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
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Set


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
