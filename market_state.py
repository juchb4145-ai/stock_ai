"""실시간 KOSPI/KOSDAQ 지수 상태 캐시.

목적:
    main.py 가 키움 OpenAPI 의 업종지수 실시간(real_type "업종지수") 으로 받는 KOSPI(001)/
    KOSDAQ(101) 틱을 한 곳에 모아두고, 진입 평가 시점에 ``snapshot()`` 으로 즉시 매크로
    통계를 뽑게 한다.

설계 원칙:
    - 순수 Python (PyQt 의존 없음). main.py 의 슬롯이 ``update()`` 만 호출하면 된다.
      → 단위 테스트가 64-bit/CI 어디서든 가능.
    - 절대시간(time.time()) 기반 1분 OHLC 롤링. 정각 분 경계를 넘으면 진행봉을 닫고
      최근 N=5분 deque 에 push.
    - 데이터 부재(키움 응답 지연/연결 실패) 는 상위(entry_strategy) 에서 ``regime=unknown``
      → neutral fallback 으로 안전 처리하므로, 본 모듈은 ``snapshot()`` 이 None 가능 필드를
      그대로 노출한다.

분류(``classify_regime``):
    - risk_off : KOSPI 일중 등락률 ≤ -1.5% 또는 일중 고점 대비 -2.0% 이하
    - weak     : KOSPI 일중 등락률 ≤ -0.5% 또는 최근 3분 slope ≤ -0.5%
    - strong   : KOSPI 일중 등락률 ≥ +0.5% 그리고 최근 3분 slope ≥ 0
    - neutral  : 그 외
    - unknown  : KOSPI 데이터 부재
임계는 모듈 상수로 노출(데이터 누적 후 재조정 예정).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional


# === 업종 코드 (키움 매뉴얼) ===
KOSPI_CODE = "001"
KOSDAQ_CODE = "101"

# === regime 분류 임계 (1차 PR 의 문헌 기반 초안) ===
RISK_OFF_PCT = -0.015
RISK_OFF_DRAWDOWN = -0.020
WEAK_PCT = -0.005
WEAK_SLOPE_3M = -0.005
STRONG_PCT = 0.005

# === regime 라벨 (오타 방지용 상수) ===
REGIME_STRONG = "strong"
REGIME_NEUTRAL = "neutral"
REGIME_WEAK = "weak"
REGIME_RISK_OFF = "risk_off"
REGIME_UNKNOWN = "unknown"

# === MarketSnapshot CSV 컬럼명 (training_recorder 가 그대로 import) ===
SNAPSHOT_FIELD_NAMES = (
    "market_pct",
    "market_slope_1m",
    "market_slope_3m",
    "market_drawdown_from_high",
    "market_regime",
)

# 1분 OHLC deque 의 최대 길이. slope_3m 에 3개만 쓰지만 여유 있게 5분 보관.
MINUTE_BAR_HISTORY = 5


@dataclass
class MinuteBar:
    """업종지수 1분 OHLC. open/high/low/close 만 사용."""
    minute_start: int  # 분 시작 epoch second (정각 분 경계)
    open: float
    high: float
    low: float
    close: float


@dataclass
class IndexState:
    """업종 한 종목(KOSPI 또는 KOSDAQ)의 일중 상태.

    ``intraday_high`` 는 모든 틱이 갱신할 수 있게 항상 현재가와 비교한다.
    ``minute_bars`` deque 는 닫힌 1분봉만 push 되며, 진행 중인 봉은
    ``cur_*`` 에 들어 있다.
    """
    last_price: float = 0.0
    last_ts: float = 0.0
    intraday_open: float = 0.0
    intraday_high: float = 0.0
    intraday_low: float = 0.0
    cur_minute_start: int = 0
    cur_open: float = 0.0
    cur_high: float = 0.0
    cur_low: float = 0.0
    cur_close: float = 0.0
    minute_bars: Deque[MinuteBar] = field(
        default_factory=lambda: deque(maxlen=MINUTE_BAR_HISTORY)
    )

    def update(self, price: float, ts: float) -> None:
        """한 틱 반영. 분 경계 넘으면 진행봉 닫고 새 봉 시작."""
        if price <= 0:
            return
        # 일중 고/저/시 갱신 (시가는 첫 틱이 결정)
        if self.intraday_open <= 0:
            self.intraday_open = price
        if price > self.intraday_high:
            self.intraday_high = price
        if self.intraday_low <= 0 or price < self.intraday_low:
            self.intraday_low = price

        # 1분 OHLC 롤링
        minute_start = int(ts // 60) * 60
        if self.cur_minute_start == 0:
            # 첫 틱
            self._open_new_minute(minute_start, price)
        elif minute_start != self.cur_minute_start:
            # 분 경계 통과 — 진행봉 닫고 새 봉
            self._close_current_minute()
            self._open_new_minute(minute_start, price)
        else:
            # 같은 분 내부 — 진행봉 갱신
            if price > self.cur_high:
                self.cur_high = price
            if price < self.cur_low:
                self.cur_low = price
            self.cur_close = price

        self.last_price = price
        self.last_ts = ts

    def _open_new_minute(self, minute_start: int, price: float) -> None:
        self.cur_minute_start = minute_start
        self.cur_open = price
        self.cur_high = price
        self.cur_low = price
        self.cur_close = price

    def _close_current_minute(self) -> None:
        if self.cur_minute_start == 0 or self.cur_open <= 0:
            return
        self.minute_bars.append(
            MinuteBar(
                minute_start=self.cur_minute_start,
                open=self.cur_open,
                high=self.cur_high,
                low=self.cur_low,
                close=self.cur_close,
            )
        )

    # === 통계 헬퍼 ===

    def pct(self) -> Optional[float]:
        """일중 등락률 = (last - open) / open."""
        if self.intraday_open <= 0 or self.last_price <= 0:
            return None
        return self.last_price / self.intraday_open - 1

    def slope_1m(self) -> Optional[float]:
        """진행 중 분봉의 (close - open) / open. 진행봉이 비면 None."""
        if self.cur_open <= 0 or self.cur_close <= 0:
            return None
        return self.cur_close / self.cur_open - 1

    def slope_3m(self) -> Optional[float]:
        """최근 3분봉(닫힌 + 진행) 누적 slope.

        - 닫힌 봉이 2개 이상이면 (마지막 3봉의 첫 open → 마지막 close)
        - 닫힌 봉이 부족하면 가능한 만큼 + 진행봉으로 보완
        - 데이터가 전혀 없으면 None
        """
        bars = list(self.minute_bars)
        # 닫힌 봉 + 진행봉 (open 이 있는 경우만)
        if self.cur_open > 0:
            bars.append(
                MinuteBar(
                    minute_start=self.cur_minute_start,
                    open=self.cur_open,
                    high=self.cur_high,
                    low=self.cur_low,
                    close=self.cur_close,
                )
            )
        if not bars:
            return None
        recent = bars[-3:]
        first_open = recent[0].open
        last_close = recent[-1].close
        if first_open <= 0 or last_close <= 0:
            return None
        return last_close / first_open - 1

    def drawdown_from_high(self) -> Optional[float]:
        """일중 고점 대비 (last / high - 1). 항상 ≤ 0."""
        if self.intraday_high <= 0 or self.last_price <= 0:
            return None
        return self.last_price / self.intraday_high - 1


@dataclass
class MarketSnapshot:
    """진입 평가 시점에 캡처된 KOSPI 매크로 한 줄.

    KOSDAQ 은 1차 PR 에서는 보조 신호로만(현재 분류에는 영향 없음, CSV 에는 기록 안 함)
    두고, 다음 PR 에서 KOSDAQ 가중을 추가할 여지를 남긴다.
    """
    market_pct: Optional[float] = None
    market_slope_1m: Optional[float] = None
    market_slope_3m: Optional[float] = None
    market_drawdown_from_high: Optional[float] = None
    market_regime: str = REGIME_UNKNOWN

    def as_row_dict(self) -> Dict[str, object]:
        """CSV row 에 그대로 update() 할 수 있는 dict.

        None 은 빈 문자열로 변환해 csv.DictWriter 가 ``""`` 로 기록하게 한다
        (numeric None 을 ``"None"`` 문자열로 흘리지 않기 위함).
        """
        return {
            "market_pct": "" if self.market_pct is None else self.market_pct,
            "market_slope_1m": "" if self.market_slope_1m is None else self.market_slope_1m,
            "market_slope_3m": "" if self.market_slope_3m is None else self.market_slope_3m,
            "market_drawdown_from_high":
                "" if self.market_drawdown_from_high is None else self.market_drawdown_from_high,
            "market_regime": self.market_regime or REGIME_UNKNOWN,
        }


def classify_regime(snap: MarketSnapshot) -> str:
    """KOSPI 통계로 regime 4+1분류.

    데이터가 전혀 없으면 ``unknown`` (entry_strategy 가 neutral 로 fallback).
    """
    pct = snap.market_pct
    if pct is None:
        return REGIME_UNKNOWN
    drawdown = snap.market_drawdown_from_high
    slope_3m = snap.market_slope_3m

    if pct <= RISK_OFF_PCT:
        return REGIME_RISK_OFF
    if drawdown is not None and drawdown <= RISK_OFF_DRAWDOWN:
        return REGIME_RISK_OFF
    if pct <= WEAK_PCT:
        return REGIME_WEAK
    if slope_3m is not None and slope_3m <= WEAK_SLOPE_3M:
        return REGIME_WEAK
    if pct >= STRONG_PCT and (slope_3m is None or slope_3m >= 0):
        return REGIME_STRONG
    return REGIME_NEUTRAL


class MarketStateCache:
    """KOSPI/KOSDAQ 실시간 상태 보관 + 즉시 snapshot 발급.

    main.py 의 ``_on_receive_real_data`` 가 ``update(index_code, price, ts)`` 만 부르면
    되고, ``score_opening_trade`` 는 ``snapshot()`` 을 부른다. 두 호출은 같은 GIL 하에서만
    일어나므로 별도 락은 두지 않는다(키움 OpenAPI 콜백은 메인 Qt 이벤트루프에서 직렬화됨).
    """

    def __init__(self) -> None:
        self.indices: Dict[str, IndexState] = {
            KOSPI_CODE: IndexState(),
            KOSDAQ_CODE: IndexState(),
        }

    def update(self, index_code: str, price: float, ts: float) -> None:
        """한 틱 반영. 등록된 업종(001/101) 외는 무시."""
        state = self.indices.get(index_code)
        if state is None:
            return
        state.update(price, ts)

    def kospi(self) -> IndexState:
        return self.indices[KOSPI_CODE]

    def kosdaq(self) -> IndexState:
        return self.indices[KOSDAQ_CODE]

    def snapshot(self) -> MarketSnapshot:
        """KOSPI 기준 즉시 통계 + regime 분류.

        KOSPI 데이터가 없으면 ``regime=unknown`` 이 자동 설정된다.
        """
        kospi = self.indices[KOSPI_CODE]
        snap = MarketSnapshot(
            market_pct=kospi.pct(),
            market_slope_1m=kospi.slope_1m(),
            market_slope_3m=kospi.slope_3m(),
            market_drawdown_from_high=kospi.drawdown_from_high(),
        )
        snap.market_regime = classify_regime(snap)
        return snap
