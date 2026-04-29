"""exit_strategy 단위 테스트.

R-multiple 손절/BE/+2R 부분익절, 부분익절 후 추세 이탈, 시간 손절을
모두 표 형태로 커버한다.

실행:
    .\\venv64\\Scripts\\python.exe -m unittest test_exit_strategy -v
"""

from __future__ import annotations

import time
import unittest
from typing import List

from bars import FiveMinIndicators, MinuteBar
from portfolio import Position
import exit_strategy as xs


def make_bar(*, ts: float, close: int, open_: int = 0, high: int = 0, low: int = 0) -> MinuteBar:
    open_ = open_ or close
    high = high or max(open_, close)
    low = low or min(open_, close)
    return MinuteBar(
        minute_start=int(ts // 60) * 60,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=100,
        received_at=ts,
    )


def base_position(
    *,
    entry_price: int = 10_000,
    quantity: int = 40,
    partial_taken: bool = False,
    stop_price: int | None = None,
    breakout_high: int | None = None,
    entry1_offset_secs: float = -120.0,
) -> Position:
    pos = Position(
        code="000001",
        entry_stage=2,
        entry_price=entry_price,
        quantity=quantity,
        planned_quantity=quantity,
        r_unit_pct=xs.R_UNIT_PCT,
        partial_taken=partial_taken,
    )
    pos.stop_price = stop_price if stop_price is not None else int(entry_price * (1 - xs.R_UNIT_PCT))
    pos.breakout_high = breakout_high if breakout_high is not None else entry_price
    pos.entry1_time = time.time() + entry1_offset_secs
    pos.entry_time = pos.entry1_time
    return pos


def ctx(
    *,
    position: Position,
    current_price: int,
    chejan_strength: float = 120.0,
    minute_bars: List[MinuteBar] | None = None,
    five_min_ind: FiveMinIndicators | None = None,
    now_ts: float | None = None,
) -> xs.ExitContext:
    return xs.ExitContext(
        position=position,
        current_price=current_price,
        chejan_strength=chejan_strength,
        minute_bars=minute_bars or [],
        five_min_ind=five_min_ind,
        now_ts=now_ts or time.time(),
    )


class StopLossTests(unittest.TestCase):
    def test_sells_when_price_at_or_below_stop(self):
        pos = base_position(stop_price=9_850)
        d = xs.evaluate_exit(ctx(position=pos, current_price=9_850))
        self.assertEqual(d.action, "sell")
        self.assertIn("손절", d.reason)

    def test_holds_when_price_above_stop(self):
        pos = base_position(stop_price=9_850)
        d = xs.evaluate_exit(ctx(position=pos, current_price=10_000))
        self.assertEqual(d.action, "hold")


class BreakEvenTests(unittest.TestCase):
    def test_marks_be_update_when_above_1r(self):
        pos = base_position(entry_price=10_000)  # stop = 9_850
        # +1.6% 수익 → r ≈ 1.07 → BE 트리거
        d = xs.evaluate_exit(ctx(position=pos, current_price=10_160))
        self.assertEqual(d.action, "hold")
        self.assertTrue(d.update_stop_to_be)

    def test_does_not_update_be_below_1r(self):
        pos = base_position(entry_price=10_000)
        # +0.5% 수익 → BE 트리거 안 됨
        d = xs.evaluate_exit(ctx(position=pos, current_price=10_050))
        self.assertEqual(d.action, "hold")
        self.assertFalse(d.update_stop_to_be)


class PartialExitTests(unittest.TestCase):
    def test_triggers_partial_at_2r(self):
        pos = base_position(entry_price=10_000, partial_taken=False)
        # +3.0% 수익 → r=2.0 → 부분 익절 트리거
        d = xs.evaluate_exit(ctx(position=pos, current_price=10_300))
        self.assertEqual(d.action, "partial_sell")
        self.assertAlmostEqual(d.qty_ratio, xs.EXIT_PARTIAL_RATIO)
        self.assertTrue(d.mark_partial_taken)
        # 동시에 BE 스탑 이동도 함께 표시
        self.assertTrue(d.update_stop_to_be)

    def test_does_not_repeat_partial_after_taken(self):
        pos = base_position(entry_price=10_000, partial_taken=True)
        d = xs.evaluate_exit(ctx(position=pos, current_price=10_300))
        # 이미 부분 익절을 한 번 했으므로 partial_sell 액션이 다시 나오면 안 됨
        self.assertNotEqual(d.action, "partial_sell")


class TrendExitTests(unittest.TestCase):
    def _bars_with_5ma_below(self, *, current: int) -> List[MinuteBar]:
        ts = time.time() - 60 * 6
        # 종가가 점점 떨어지는 봉 5개 → 5MA가 현재가보다 높게 형성
        closes = [10_400, 10_380, 10_350, 10_330, 10_310]
        bars = []
        for c in closes:
            bars.append(make_bar(ts=ts, close=c))
            ts += 60
        # 현재 진행봉 (current 가격)
        bars.append(make_bar(ts=ts, close=current))
        return bars

    def test_sells_remainder_on_5ma_break_after_partial(self):
        pos = base_position(entry_price=10_000, partial_taken=True)
        bars = self._bars_with_5ma_below(current=10_290)
        d = xs.evaluate_exit(ctx(position=pos, current_price=10_290, minute_bars=bars))
        self.assertEqual(d.action, "sell")
        self.assertIn("MA", d.reason)

    def test_does_not_apply_5ma_exit_before_partial(self):
        pos = base_position(entry_price=10_000, partial_taken=False)
        bars = self._bars_with_5ma_below(current=10_290)
        # +2.9% 수익(<2R) 인 부분익절 전 상태에서 5MA 이탈만으로는 청산하지 않는다.
        # 단, 본 케이스는 현재가 10_290 → r ≈ 1.93 < 2 이므로 partial 트리거도 안 된다.
        d = xs.evaluate_exit(ctx(position=pos, current_price=10_290, minute_bars=bars))
        self.assertEqual(d.action, "hold")

    def test_sells_remainder_on_chejan_strength_collapse_after_partial(self):
        pos = base_position(entry_price=10_000, partial_taken=True)
        d = xs.evaluate_exit(
            ctx(position=pos, current_price=10_300, chejan_strength=50.0)
        )
        self.assertEqual(d.action, "sell")
        self.assertIn("체결강도", d.reason)

    def test_sells_remainder_on_5min_envelope_break_after_partial(self):
        pos = base_position(entry_price=10_000, partial_taken=True)
        ind = FiveMinIndicators(
            bb_upper_45_2=11_000,
            bb_upper_55_2=11_200,
            env_upper_13_25=10_500,
            env_upper_22_25=10_700,
            last_close=10_300,
            closes_count=60,
        )
        d = xs.evaluate_exit(
            ctx(position=pos, current_price=10_300, five_min_ind=ind)
        )
        self.assertEqual(d.action, "sell")
        self.assertIn("Env(13)", d.reason)


class TimeExitTests(unittest.TestCase):
    def test_sells_after_25min_when_below_1r(self):
        pos = base_position(entry_price=10_000, entry1_offset_secs=-(xs.EXIT_TIME_LIMIT_SECONDS + 30))
        d = xs.evaluate_exit(ctx(position=pos, current_price=10_050))
        self.assertEqual(d.action, "sell")
        self.assertIn("시간 손절", d.reason)

    def test_holds_when_above_1r_even_after_long_hold(self):
        pos = base_position(entry_price=10_000, entry1_offset_secs=-(xs.EXIT_TIME_LIMIT_SECONDS + 30))
        # +1.6% (>1R) 이면 시간 손절 트리거 안 됨
        d = xs.evaluate_exit(ctx(position=pos, current_price=10_160))
        self.assertEqual(d.action, "hold")


if __name__ == "__main__":
    unittest.main()
