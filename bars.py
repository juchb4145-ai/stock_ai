"""1분봉 집계 + 5분봉 BB/Envelope 캐시.

- MinuteBarAggregator: main.py 의 실시간 틱 수신 콜백에서 push 를 호출해
  종목별 1분봉 OHLCV 시퀀스를 누적한다. 분(minute)이 바뀌면 직전 봉이
  자동으로 finalize 되고 새 봉이 시작된다.

- FiveMinIndicatorCache: opt10080(분봉, 시간단위=5) TR 응답으로 종가 시퀀스를
  push 받아 BB(45,2)/BB(55,2)/Envelope(13,2.5)/Envelope(22,2.5) 의 상한선만
  계산해 캐시한다. 단테조건식과 동일한 (period, std_mult/pct) 설정.

설계 의도:
  - 순수 stdlib(statistics/math)만 사용 → 32비트 venv 에서도 그대로 동작.
  - 1분봉/5분봉의 IO(TR 호출) 책임은 main.py 의 Kiwoom 객체가 진다.
    이 모듈은 데이터 구조 + 지표 계산 + 도메인 view 만 노출한다.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional


# 기본 파라미터(단테조건식과 동일)
BB_SETUPS = ((45, 2.0), (55, 2.0))
ENVELOPE_SETUPS = ((13, 2.5), (22, 2.5))


@dataclass
class MinuteBar:
    """단일 1분봉 OHLCV.

    minute_start: 봉 시작 시각(epoch 초, 1분 단위로 정렬)
    """

    minute_start: int
    open: int
    high: int
    low: int
    close: int
    volume: int
    received_at: float


class MinuteBarAggregator:
    """종목별 실시간 틱을 1분봉 OHLCV 시퀀스로 집계한다.

    틱 수신 콜백에서 push 호출 → 분 경계가 바뀌면 직전 봉이 finalize 되고
    새 봉이 시작된다. all_bars(code) 는 [완성봉..., 진행봉] 순서로 반환한다.
    """

    def __init__(self, max_bars: int = 60) -> None:
        self.max_bars = max_bars
        self._bars: Dict[str, Deque[MinuteBar]] = defaultdict(
            lambda: deque(maxlen=max_bars)
        )
        # accum_volume 은 일중 누적이므로 1분 단위 거래량은 차분으로 계산.
        self._prev_accum_volume: Dict[str, int] = {}

    def push(
        self,
        code: str,
        *,
        received_at: float,
        close: int,
        high: int,
        low: int,
        open_: int,
        accum_volume: int,
    ) -> None:
        if not code or close <= 0 or received_at <= 0:
            return
        minute_start = int(received_at // 60) * 60
        bars = self._bars[code]
        prev_accum = self._prev_accum_volume.get(code)
        if prev_accum is None:
            prev_accum = accum_volume
        delta_volume = max(int(accum_volume) - int(prev_accum), 0)
        self._prev_accum_volume[code] = int(accum_volume)

        if not bars or bars[-1].minute_start != minute_start:
            new_bar = MinuteBar(
                minute_start=minute_start,
                open=int(open_) if open_ > 0 else int(close),
                high=int(high) if high > 0 else int(close),
                low=int(low) if low > 0 else int(close),
                close=int(close),
                volume=delta_volume,
                received_at=received_at,
            )
            bars.append(new_bar)
            return

        cur = bars[-1]
        cur.close = int(close)
        if high and high > cur.high:
            cur.high = int(high)
        if low > 0 and (cur.low <= 0 or low < cur.low):
            cur.low = int(low)
        cur.volume += delta_volume
        cur.received_at = received_at

    def all_bars(self, code: str) -> List[MinuteBar]:
        bars = self._bars.get(code)
        return list(bars) if bars else []

    def closed_bars(self, code: str) -> List[MinuteBar]:
        """완성된(직전) 1분봉 리스트(가장 오래된 것이 인덱스 0)."""
        bars = self._bars.get(code)
        if not bars or len(bars) < 2:
            return []
        return list(bars)[:-1]

    def current_bar(self, code: str) -> Optional[MinuteBar]:
        bars = self._bars.get(code)
        return bars[-1] if bars else None

    def discard(self, code: str) -> None:
        self._bars.pop(code, None)
        self._prev_accum_volume.pop(code, None)

    # --- 도메인 view ---

    def recent_high_since(self, code: str, since_ts: float) -> int:
        """since_ts 이후 갱신된 1분봉(현재봉 포함)들의 최고가."""
        bars = self.all_bars(code)
        highs = [b.high for b in bars if b.received_at >= since_ts and b.high > 0]
        return max(highs) if highs else 0

    def sma_close(self, code: str, period: int) -> Optional[float]:
        """완성봉 + 진행봉을 합쳐 마지막 period 봉의 종가 SMA. 봉 부족 시 None."""
        bars = self.all_bars(code)
        if len(bars) < period:
            return None
        closes = [b.close for b in bars[-period:]]
        return sum(closes) / period


# === 5분봉 지표 ===


def _bb_upper(closes: List[float], period: int, std_mult: float) -> Optional[float]:
    if len(closes) < period:
        return None
    window = closes[-period:]
    mean = sum(window) / period
    if period < 2:
        return mean
    variance = sum((x - mean) ** 2 for x in window) / period
    std = math.sqrt(variance)
    return mean + std_mult * std


def _envelope_upper(closes: List[float], period: int, pct: float) -> Optional[float]:
    """Envelope 상한선 = SMA(period) * (1 + pct/100). 단테조건식의 (period, pct) = (13,2.5)/(22,2.5)."""
    if len(closes) < period:
        return None
    window = closes[-period:]
    mean = sum(window) / period
    return mean * (1 + pct / 100.0)


@dataclass
class FiveMinIndicators:
    """단일 종목의 5분봉 BB/Envelope 상한선 + OHLC 스냅샷.

    *_now 는 진행봉(0봉전)을 포함한 종가 시퀀스로 계산한 상한선,
    *_prev 는 진행봉을 제외한 종가 시퀀스로 계산한 상한선이다.
    cur_/prev_/pre_prev_ OHLC 는 영웅문 분봉 TR(opt10080) 응답에서 추출한
    원시 봉 정보이며 진행봉 close 는 호출측이 실시간 마지막 틱으로 덮어쓴다.
    """

    bb_upper_45_2: Optional[float] = None
    bb_upper_55_2: Optional[float] = None
    env_upper_13_25: Optional[float] = None
    env_upper_22_25: Optional[float] = None
    bb_upper_45_2_prev: Optional[float] = None
    bb_upper_55_2_prev: Optional[float] = None
    env_upper_13_25_prev: Optional[float] = None
    env_upper_22_25_prev: Optional[float] = None
    last_close: Optional[float] = None
    closes_count: int = 0
    updated_at: float = 0.0
    cur_open: Optional[float] = None
    cur_high: Optional[float] = None
    cur_low: Optional[float] = None
    prev_open: Optional[float] = None
    prev_high: Optional[float] = None
    prev_low: Optional[float] = None
    prev_close: Optional[float] = None
    pre_prev_close: Optional[float] = None

    def trend_up(self, current_price: float) -> bool:
        """현재가가 5분봉 추세 위에 있는지(Envelope(13) 상단 또는 BB(55) 상단 위)."""
        if current_price <= 0:
            return False
        env = self.env_upper_13_25
        bb = self.bb_upper_55_2
        if env is not None and current_price >= env:
            return True
        if bb is not None and current_price >= bb:
            return True
        return False

    def is_breakout_zero_bar(self) -> bool:
        """0봉전(진행봉) 동시 돌파 — A급 신호.

        조건: 진행봉 close 가 현재 시점의 4개 상한선(BB45/BB55/Env13/Env22) 모두 위 +
        직전 완성봉 close 가 그 직전 시점의 4개 상한선 중 적어도 하나 아래(=처음 돌파).
        """
        cur = self.last_close
        if cur is None:
            return False
        cur_uppers = (
            self.bb_upper_45_2,
            self.bb_upper_55_2,
            self.env_upper_13_25,
            self.env_upper_22_25,
        )
        for upper in cur_uppers:
            if upper is None or cur < upper:
                return False
        prev = self.prev_close
        if prev is None:
            return True
        prev_uppers = [
            u
            for u in (
                self.bb_upper_45_2_prev,
                self.bb_upper_55_2_prev,
                self.env_upper_13_25_prev,
                self.env_upper_22_25_prev,
            )
            if u is not None
        ]
        if not prev_uppers:
            return True
        # 직전 봉이 4개 상단 중 적어도 하나라도 아래였다면 진행봉이 새로 뚫은 것으로 본다.
        return any(prev < u for u in prev_uppers)

    def is_breakout_prev_bar(self) -> bool:
        """1봉전(직전 완성봉) 동시 돌파 — B급 신호.

        조건: 직전 완성봉 close 가 그 시점의 4개 상한선 모두 위 +
        그 직전 봉(pre_prev) close 가 같은 상한선 중 적어도 하나 아래.
        """
        prev = self.prev_close
        if prev is None:
            return False
        prev_uppers = (
            self.bb_upper_45_2_prev,
            self.bb_upper_55_2_prev,
            self.env_upper_13_25_prev,
            self.env_upper_22_25_prev,
        )
        for upper in prev_uppers:
            if upper is None or prev < upper:
                return False
        pp = self.pre_prev_close
        if pp is None:
            return True
        return any(pp < u for u in prev_uppers if u is not None)

    def upper_wick_ratio_zero_bar(self) -> float:
        """진행봉의 윗꼬리 비율 = (high - close) / (high - low). 0~1.

        값이 클수록 진행봉이 위에서 강하게 밀린 형태(가짜 돌파 가능성).
        high == low 이거나 데이터 없으면 0.0 반환.
        """
        if self.cur_high is None or self.cur_low is None or self.last_close is None:
            return 0.0
        if self.cur_high <= self.cur_low:
            return 0.0
        wick = (self.cur_high - self.last_close) / (self.cur_high - self.cur_low)
        return max(0.0, min(1.0, wick))


class FiveMinIndicatorCache:
    """5분봉 종가 시퀀스 + BB/Envelope 상한선 캐시.

    main.py 가 opt10080(시간단위=5) TR 응답으로 update(code, closes) 를 호출한다.
    TR 빈도 제한(초 5회) 때문에 needs_refresh 로 갱신 주기를 조절한다.
    """

    DEFAULT_REFRESH_SECONDS = 60.0

    def __init__(self) -> None:
        self._closes: Dict[str, List[float]] = {}
        self._indicators: Dict[str, FiveMinIndicators] = {}
        self._last_request_at: Dict[str, float] = {}

    def update(self, code: str, closes: List[float]) -> FiveMinIndicators:
        """closes 만으로 지표 갱신(OHLC 미반영). 호환을 위해 남겨둔다.

        새 코드는 update_bars 를 호출하여 진행봉/직전봉 OHLC + 1봉전 시점 상한선까지
        모두 채워둔다. update 만 호출하면 is_breakout_*/upper_wick_ratio_* 는 0/False 로 동작한다.
        """
        cleaned = [float(c) for c in closes if c]
        self._closes[code] = cleaned
        ind = FiveMinIndicators(
            bb_upper_45_2=_bb_upper(cleaned, 45, 2.0),
            bb_upper_55_2=_bb_upper(cleaned, 55, 2.0),
            env_upper_13_25=_envelope_upper(cleaned, 13, 2.5),
            env_upper_22_25=_envelope_upper(cleaned, 22, 2.5),
            last_close=cleaned[-1] if cleaned else None,
            closes_count=len(cleaned),
            updated_at=time.time(),
        )
        self._indicators[code] = ind
        return ind

    def update_bars(self, code: str, bars):
        """OHLCV 튜플 시퀀스(과거→최신, 마지막 = 진행봉)로 지표를 갱신한다.

        bars 의 각 항목은 (open, high, low, close, volume) 튜플(또는 동일 인덱싱 가능 객체).
        진행봉 close 는 호출측이 미리 실시간 마지막 틱 close 로 덮어쓰는 것을 권장한다.
        """
        if not bars:
            ind = FiveMinIndicators(updated_at=time.time())
            self._indicators[code] = ind
            self._closes[code] = []
            return ind

        closes = [float(b[3]) for b in bars if b and len(b) >= 4 and b[3]]
        if not closes:
            ind = FiveMinIndicators(updated_at=time.time())
            self._indicators[code] = ind
            self._closes[code] = []
            return ind
        self._closes[code] = closes

        cur = bars[-1]
        cur_o = float(cur[0]) if len(cur) > 0 and cur[0] else None
        cur_h = float(cur[1]) if len(cur) > 1 and cur[1] else None
        cur_l = float(cur[2]) if len(cur) > 2 and cur[2] else None

        prev_o = prev_h = prev_l = prev_c = None
        if len(bars) >= 2:
            prev = bars[-2]
            prev_o = float(prev[0]) if len(prev) > 0 and prev[0] else None
            prev_h = float(prev[1]) if len(prev) > 1 and prev[1] else None
            prev_l = float(prev[2]) if len(prev) > 2 and prev[2] else None
            prev_c = float(prev[3]) if len(prev) > 3 and prev[3] else None

        pre_prev_c = None
        if len(bars) >= 3:
            pp = bars[-3]
            pre_prev_c = float(pp[3]) if len(pp) > 3 and pp[3] else None

        closes_excluding_cur = closes[:-1]

        ind = FiveMinIndicators(
            bb_upper_45_2=_bb_upper(closes, 45, 2.0),
            bb_upper_55_2=_bb_upper(closes, 55, 2.0),
            env_upper_13_25=_envelope_upper(closes, 13, 2.5),
            env_upper_22_25=_envelope_upper(closes, 22, 2.5),
            bb_upper_45_2_prev=_bb_upper(closes_excluding_cur, 45, 2.0),
            bb_upper_55_2_prev=_bb_upper(closes_excluding_cur, 55, 2.0),
            env_upper_13_25_prev=_envelope_upper(closes_excluding_cur, 13, 2.5),
            env_upper_22_25_prev=_envelope_upper(closes_excluding_cur, 22, 2.5),
            last_close=closes[-1],
            closes_count=len(closes),
            updated_at=time.time(),
            cur_open=cur_o,
            cur_high=cur_h,
            cur_low=cur_l,
            prev_open=prev_o,
            prev_high=prev_h,
            prev_low=prev_l,
            prev_close=prev_c,
            pre_prev_close=pre_prev_c,
        )
        self._indicators[code] = ind
        return ind

    def get(self, code: str) -> Optional[FiveMinIndicators]:
        return self._indicators.get(code)

    def discard(self, code: str) -> None:
        self._closes.pop(code, None)
        self._indicators.pop(code, None)
        self._last_request_at.pop(code, None)

    def needs_refresh(
        self, code: str, *, refresh_seconds: float = DEFAULT_REFRESH_SECONDS
    ) -> bool:
        last = self._last_request_at.get(code, 0.0)
        return (time.time() - last) >= refresh_seconds

    def mark_refreshed(self, code: str) -> None:
        self._last_request_at[code] = time.time()
