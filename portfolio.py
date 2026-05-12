"""한 종목의 보유/주문/관찰 상태를 단일 객체로 모은 Position과 그 컬렉션 PortfolioState.

main.py 의 Kiwoom 클래스가 13개 이상의 dict/set에 종목별 상태를 흩어 두던 것을
점진적으로 이쪽으로 옮긴다. 마이그레이션이 끝날 때까지는 기존 dict들과 병행 운영되며,
Kiwoom._sync_position_from_dicts 를 통해 양쪽이 동기화된다.

리팩터링 단계 (자세한 내용은 chat 의 'dataclass 통합 세부 작업' 답변 참조):
  Phase 1) portfolio.py 신규 + import + self.portfolio = PortfolioState()
  Phase 2) _discard_position 에서 portfolio.remove 동기화
  Phase 3) write 경로(채우기) parallel write — 현재 단계
  Phase 4) read 경로(조회) Position 기반으로 변환
  Phase 5) 기존 dict/set 제거

장중 크래시 복원:
  PortfolioState.save() / load() 가 디스크 영속화를 담당한다. 잔고/미체결 등
  키움에서 다시 받아올 수 있는 정보는 잃어도 되지만, 아래 필드들은 잃으면 *전략이
  망가진다* — 그래서 별도 JSON 으로 매 갱신 시점마다 atomic write 한다.

    - entry_stage          (잃으면 1차만 사놓고 2차 본진입 못함)
    - planned_quantity     (잃으면 2차 매수 수량 계산이 깨짐)
    - stop_price           (잃으면 BE 스탑이 풀려 -1R 보호 못함)
    - partial_taken        (잃으면 +2R 도달 시 또 부분익절 시도)
    - breakout_high        (잃으면 추적 고점이 0부터 다시)
    - pullback_window_deadline / entry1_time / entry2_time
    - breakout_grade       ("A"/"B" 분할 매수 분기 식별자)
    - pending_sell_intent  (잃으면 큐에 들어 있던 매도 의도가 사라짐)

  반대로 quantity / available_quantity / entry_price / pending_buy / pending_sell
  은 부팅 시 키움 잔고/미체결 TR 응답으로 덮어쓰여야 하므로 디스크 본을 무시한다.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set


_logger = logging.getLogger(__name__)


# 디스크 영속화에 포함시키는 필드들. 위 docstring 의 "잃으면 안 되는 8개" 이외에
# audit 가독성을 위해 보존해 두면 좋은 항목(name/r_unit_pct/highest_price 등)도 포함.
# quantity/available_quantity/entry_price/pending_* 같은 휘발성 필드는 의도적으로 제외.
_PERSISTED_POSITION_FIELDS = (
    "code",
    "name",
    "target_price",
    "target_return",
    "highest_price",
    "entry_time",
    "bought_today",
    "pending_sell_intent",
    "order_context",
    "entry_stage",
    "planned_quantity",
    "entry1_time",
    "entry2_time",
    "r_unit_pct",
    "stop_price",
    "partial_taken",
    "breakout_high",
    "pullback_window_deadline",
    "breakout_grade",
)

# from_persisted_dict 가 JSON 값에 적용할 타입 캐스트 카테고리. 운영 중 손으로 편집된
# JSON 또는 미래 schema 어긋남에 강건하게 만든다. 캐스트 실패 시 해당 필드만 무시.
_PERSISTED_INT_FIELDS = frozenset({
    "target_price", "highest_price",
    "entry_stage", "planned_quantity",
    "stop_price", "breakout_high",
})
_PERSISTED_FLOAT_FIELDS = frozenset({
    "target_return", "entry_time",
    "entry1_time", "entry2_time",
    "r_unit_pct", "pullback_window_deadline",
})
_PERSISTED_BOOL_FIELDS = frozenset({"bought_today", "partial_taken"})
_PERSISTED_STR_FIELDS = frozenset({"name", "breakout_grade"})


# 캐스트 실패 sentinel. None 은 정상 값(pending_sell_intent 등)이라 별도 sentinel 사용.
class _CastFailed:
    __slots__ = ()
    def __repr__(self) -> str:  # pragma: no cover (debug only)
        return "<CAST_FAILED>"


_CAST_FAILED = _CastFailed()


def _cast_persisted_value(name: str, value: Any) -> Any:
    """필드 이름에 따라 JSON 값을 강제 캐스트. 실패하면 ``_CAST_FAILED``.

    int/float 필드에 들어온 문자열("123" 등) 은 정상 캐스트로 살리되, 캐스트 자체가
    예외를 던지면 호출자가 해당 필드를 default 로 두도록 sentinel 반환.
    """
    if name in _PERSISTED_INT_FIELDS:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return _CAST_FAILED
    if name in _PERSISTED_FLOAT_FIELDS:
        try:
            return float(value)
        except (TypeError, ValueError):
            return _CAST_FAILED
    if name in _PERSISTED_BOOL_FIELDS:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes"}
        return _CAST_FAILED
    if name in _PERSISTED_STR_FIELDS:
        if value is None:
            return ""
        try:
            return str(value)
        except Exception:    # noqa: BLE001
            return _CAST_FAILED
    # 미지정 필드는 그대로 통과(하위 호환).
    return value


@dataclass
class Position:
    """단일 종목의 보유/주문/관찰 상태."""

    code: str
    name: str = ""

    # === 보유 정보 (chejan/잔고 TR 응답이 채움) ===
    quantity: int = 0
    available_quantity: int = 0
    entry_price: int = 0

    # === 목표/추적 ===
    target_price: int = 0
    target_return: float = 0.0
    highest_price: int = 0

    # === 시간 ===
    entry_time: float = 0.0

    # === 일일 플래그 ===
    bought_today: bool = False

    # === 진행 중 주문 / 의도 ===
    pending_buy: bool = False
    pending_sell: bool = False
    pending_sell_intent: Optional[dict] = None
    order_context: dict = field(default_factory=dict)

    # === 단테 분할매수/청산 상태 (1차 추격 + 2차 본진입 + R-multiple 트레일링) ===
    # entry_stage: 0 미체결, 1 1차(소량) 완료, 2 본진입 완료
    entry_stage: int = 0
    # 1차 진입 시 결정되는 총 계획 수량(1차 + 2차 합산). 0이면 미설정.
    planned_quantity: int = 0
    # 1차 체결 시각 / 2차 체결 시각
    entry1_time: float = 0.0
    entry2_time: float = 0.0
    # 1R = stop_price 와 entry_price 사이의 비율(기본 0.015)
    r_unit_pct: float = 0.0
    # 동적 스탑가. 초기 -1R, +1R 도달 시 BE 로 상향. 0이면 미설정.
    stop_price: int = 0
    # +2R 도달 시 50% 익절 완료 플래그
    partial_taken: bool = False
    # 1차 진입 후 갱신되는 고점(눌림 판정 기준)
    breakout_high: int = 0
    # 본진입 윈도우 마감 시각(epoch 초). 0 이면 윈도우 비활성.
    pullback_window_deadline: float = 0.0
    # 진입 시점 단테 등급. "A" = 0봉전 동시 돌파(추격+눌림 분할매수), "B" = 1봉전 돌파만(첫 눌림 일괄). "" = 미분류.
    breakout_grade: str = ""

    # === 편의 메서드 ===
    def is_holding(self) -> bool:
        return self.quantity > 0

    def is_pending(self) -> bool:
        return self.pending_buy or self.pending_sell

    def update_highest(self, price: int) -> None:
        if price and price > self.highest_price:
            self.highest_price = price

    def update_breakout_high(self, price: int) -> None:
        if price and price > self.breakout_high:
            self.breakout_high = price

    def profit_rate(self, current_price: int) -> float:
        if self.entry_price <= 0 or not current_price:
            return 0.0
        return current_price / self.entry_price - 1

    # === 디스크 영속화 ===

    def to_persisted_dict(self) -> Dict[str, Any]:
        """장중 크래시 복원용 직렬화. 잔고/미체결 같은 휘발성 필드는 제외."""
        return {name: getattr(self, name) for name in _PERSISTED_POSITION_FIELDS}

    @classmethod
    def from_persisted_dict(cls, payload: Dict[str, Any]) -> "Position":
        """to_persisted_dict 의 역. 알 수 없는 키는 무시(하위호환).

        손상되거나 잘못된 타입의 값은 해당 필드만 default 로 두고 진행한다(부팅 차단
        금지). 예: ``entry_stage`` 가 ``"two"`` 로 들어와도 0(default) 으로 남긴다.
        """
        code = str(payload.get("code") or "").strip()
        if not code:
            raise ValueError("from_persisted_dict: code 비어 있음")
        position = cls(code=code)
        for name in _PERSISTED_POSITION_FIELDS:
            if name == "code":
                continue
            if name not in payload:
                continue
            value = payload[name]
            if name == "pending_sell_intent":
                # None 또는 dict 만 허용 — 그 외는 무시.
                position.pending_sell_intent = (
                    dict(value) if isinstance(value, dict) else None
                )
                continue
            if name == "order_context":
                position.order_context = dict(value) if isinstance(value, dict) else {}
                continue
            cast_value = _cast_persisted_value(name, value)
            if cast_value is _CAST_FAILED:
                _logger.warning(
                    "from_persisted_dict: %s.%s 값 무시(%r) -- 타입 캐스트 실패",
                    code, name, value,
                )
                continue
            setattr(position, name, cast_value)
        return position


class PortfolioState:
    """Position 객체의 컬렉션. 일관된 종목 상태 변경 진입점을 제공한다."""

    def __init__(self) -> None:
        self._positions: Dict[str, Position] = {}

    # --- 조회 ---

    def get(self, code: str) -> Optional[Position]:
        return self._positions.get(code)

    def get_or_create(self, code: str, *, name: str = "") -> Position:
        position = self._positions.get(code)
        if position is None:
            position = Position(code=code, name=name)
            self._positions[code] = position
        elif name and not position.name:
            position.name = name
        return position

    def remove(self, code: str) -> Optional[Position]:
        return self._positions.pop(code, None)

    def has(self, code: str) -> bool:
        return code in self._positions

    def codes(self) -> Set[str]:
        return set(self._positions.keys())

    def values(self):
        return self._positions.values()

    def items(self):
        return self._positions.items()

    # --- 도메인 뷰 ---

    def holding_codes(self) -> Set[str]:
        return {code for code, p in self._positions.items() if p.is_holding()}

    def pending_order_codes(self) -> Set[str]:
        return {code for code, p in self._positions.items() if p.is_pending()}

    def pending_sell_codes(self) -> Set[str]:
        return {code for code, p in self._positions.items() if p.pending_sell}

    def bought_today_codes(self) -> Set[str]:
        return {code for code, p in self._positions.items() if p.bought_today}

    def __len__(self) -> int:
        return len(self._positions)

    def __contains__(self, code: str) -> bool:
        return code in self._positions

    # --- 디스크 영속화 ---

    def to_persisted_dict(self, *, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """전체 portfolio 를 단일 JSON-호환 dict 로 직렬화. metadata 는 top-level 에 병합."""
        payload: Dict[str, Any] = {
            "schema": "portfolio_state_v1",
            "positions": [p.to_persisted_dict() for p in self._positions.values()],
        }
        if metadata:
            for k, v in metadata.items():
                if k in {"schema", "positions"}:
                    continue
                payload[k] = v
        return payload

    def save(self, path: str, *, metadata: Optional[Dict[str, Any]] = None) -> None:
        """원자적 저장 — tmp 파일 → fsync → rename 으로 부분 쓰기를 막는다.

        ``metadata`` 는 trading_day / saved_at 같은 호출측 메타정보를 함께 보존하기 위해
        받는다. IO 실패 시 예외를 호출자에게 전파한다(상위에서 감춰지지 않게).
        """
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        tmp_path = path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(
                    self.to_persisted_dict(metadata=metadata),
                    f, ensure_ascii=False, indent=2,
                )
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
        except Exception:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass
            raise

    @classmethod
    def load(cls, path: str) -> "LoadedPortfolioState":
        """디스크에서 PortfolioState + metadata 를 복원한다.

        파일이 없거나 손상돼 있으면 빈 결과를 반환한다(부팅 차단 금지).
        손상 파일은 ``.corrupt`` 접미사로 보존해 사후 분석을 가능케 한다.
        """
        state = cls()
        metadata: Dict[str, Any] = {}
        if not os.path.exists(path):
            return LoadedPortfolioState(state=state, metadata=metadata)
        try:
            with open(path, encoding="utf-8") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            backup = path + ".corrupt"
            try:
                os.replace(path, backup)
            except OSError:
                pass
            _logger.error("portfolio_state 손상 -- %s 로 보존 후 빈 상태 시작: %s", backup, exc)
            return LoadedPortfolioState(state=state, metadata=metadata)

        if not isinstance(payload, dict):
            _logger.error("portfolio_state 형식 오류 — 빈 상태 시작")
            return LoadedPortfolioState(state=state, metadata=metadata)

        for entry in payload.get("positions") or []:
            if not isinstance(entry, dict):
                continue
            try:
                position = Position.from_persisted_dict(entry)
            except (TypeError, ValueError) as exc:
                _logger.warning("portfolio_state entry 무시: %s", exc)
                continue
            state._positions[position.code] = position
        for k, v in payload.items():
            if k in {"schema", "positions"}:
                continue
            metadata[k] = v
        return LoadedPortfolioState(state=state, metadata=metadata)


@dataclass
class LoadedPortfolioState:
    """``PortfolioState.load`` 의 반환 타입. state + 호출측 메타정보를 함께 전달한다."""
    state: "PortfolioState"
    metadata: Dict[str, Any] = field(default_factory=dict)
