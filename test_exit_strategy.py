from __future__ import annotations

import time
import unittest
from typing import List

from bars import MinuteBar
from portfolio import Position
from trade_config import TradeConfig
import exit_strategy as xs


def make_bar(*, ts: float, close: int, open_: int = 0, high: int = 0, low: int = 0, volume: int = 100) -> MinuteBar:
    open_ = open_ or close
    high = high or max(open_, close)
    low = low or min(open_, close)
    return MinuteBar(
        minute_start=int(ts // 60) * 60,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        received_at=ts,
    )


def base_position(
    *,
    entry_price: int = 10_000,
    quantity: int = 40,
    partial_taken: bool = False,
    stop_price: int | None = None,
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
    pos.breakout_high = entry_price
    pos.highest_price = entry_price
    pos.entry1_time = time.time() + entry1_offset_secs
    pos.entry_time = pos.entry1_time
    return pos


def ctx(
    *,
    position: Position,
    current_price: int,
    chejan_strength: float = 120.0,
    minute_bars: List[MinuteBar] | None = None,
    now_ts: float | None = None,
    intraday_vwap: float = 0.0,
    vwap_below_since: float = 0.0,
    signal_bar_low: int = 0,
    chejan_strength_history: List[float] | None = None,
    force_exit: bool = False,
    closing_auction_emergency: bool = False,
    config: TradeConfig | None = None,
) -> xs.ExitContext:
    return xs.ExitContext(
        position=position,
        current_price=current_price,
        chejan_strength=chejan_strength,
        minute_bars=minute_bars or [],
        five_min_ind=None,
        now_ts=now_ts or time.time(),
        intraday_vwap=intraday_vwap,
        vwap_below_since=vwap_below_since,
        signal_bar_low=signal_bar_low,
        chejan_strength_history=chejan_strength_history,
        force_exit=force_exit,
        closing_auction_emergency=closing_auction_emergency,
        config=config or TradeConfig(),
    )


class StructuredExitTests(unittest.TestCase):
    def test_hard_stop_beats_profit_take(self):
        pos = base_position(stop_price=10_500)
        pos.highest_price = 10_600

        d = xs.evaluate_exit(ctx(position=pos, current_price=10_200))

        self.assertEqual(d.action, xs.ACTION_STOP_LOSS)
        self.assertEqual(d.exit_reason_code, xs.REASON_BREAK_EVEN_STOP_AFTER_1R)
        self.assertEqual(d.exit_type, xs.EXIT_TYPE_BREAK_EVEN_STOP)

    def test_fixed_hard_stop(self):
        pos = base_position(stop_price=9_000)

        d = xs.evaluate_exit(ctx(position=pos, current_price=9_850))

        self.assertEqual(d.action, xs.ACTION_STOP_LOSS)
        self.assertEqual(d.exit_reason_code, xs.REASON_HARD_STOP_FIXED_PCT)

    def test_break_even_stop_after_1r(self):
        pos = base_position(stop_price=10_000)

        d = xs.evaluate_exit(ctx(position=pos, current_price=10_000))

        self.assertEqual(d.action, xs.ACTION_STOP_LOSS)
        self.assertEqual(d.exit_type, xs.EXIT_TYPE_BREAK_EVEN_STOP)
        self.assertEqual(d.exit_reason_code, xs.REASON_BREAK_EVEN_STOP_AFTER_1R)

    def test_holds_and_marks_be_update_when_above_1r(self):
        pos = base_position(entry_price=10_000, stop_price=9_850)

        d = xs.evaluate_exit(ctx(position=pos, current_price=10_160))

        self.assertEqual(d.action, xs.ACTION_HOLD)
        self.assertTrue(d.update_stop_to_be)

    def test_structure_stop_signal_bar_low_break(self):
        pos = base_position()

        d = xs.evaluate_exit(ctx(position=pos, current_price=9_940, signal_bar_low=9_950))

        self.assertEqual(d.action, xs.ACTION_STOP_LOSS)
        self.assertEqual(d.exit_reason_code, xs.REASON_STRUCTURE_SIGNAL_BAR_LOW_BREAK)
        self.assertEqual(d.exit_type, xs.EXIT_TYPE_STRUCTURE_STOP)

    def test_structure_stop_recent_1m_low_break(self):
        pos = base_position()
        now = time.time() - 300
        bars = [
            make_bar(ts=now, close=10_050, low=10_000),
            make_bar(ts=now + 60, close=10_040, low=10_010),
            make_bar(ts=now + 120, close=10_030, low=10_020),
            make_bar(ts=now + 180, close=9_990, low=9_990),
        ]

        d = xs.evaluate_exit(ctx(position=pos, current_price=9_990, minute_bars=bars))

        self.assertEqual(d.action, xs.ACTION_STOP_LOSS)
        self.assertEqual(d.exit_reason_code, xs.REASON_STRUCTURE_RECENT_1M_LOW_BREAK)

    def test_vwap_reclaim_failed(self):
        pos = base_position()
        now = time.time()

        d = xs.evaluate_exit(
            ctx(
                position=pos,
                current_price=9_950,
                intraday_vwap=10_000,
                vwap_below_since=now - 61,
                now_ts=now,
            )
        )

        self.assertEqual(d.action, xs.ACTION_STOP_LOSS)
        self.assertEqual(d.exit_reason_code, xs.REASON_VWAP_RECLAIM_FAILED)

    def test_vwap_fast_drop(self):
        pos = base_position()

        d = xs.evaluate_exit(ctx(position=pos, current_price=9_890, intraday_vwap=10_000))

        self.assertEqual(d.action, xs.ACTION_STOP_LOSS)
        self.assertEqual(d.exit_reason_code, xs.REASON_VWAP_BREAK_FAST_DROP)

    def test_momentum_trade_strength_drop(self):
        pos = base_position()

        d = xs.evaluate_exit(
            ctx(
                position=pos,
                current_price=10_020,
                chejan_strength=80,
                chejan_strength_history=[150, 145, 80],
            )
        )

        self.assertEqual(d.action, xs.ACTION_STOP_LOSS)
        self.assertEqual(d.exit_reason_code, xs.REASON_MOMENTUM_TRADE_STRENGTH_DROP)

    def test_bearish_volume_candle(self):
        pos = base_position()
        now = time.time() - 120
        bars = [
            make_bar(ts=now, open_=10_000, close=10_020, volume=100),
            make_bar(ts=now + 60, open_=10_020, close=10_010, volume=180),
        ]

        d = xs.evaluate_exit(ctx(position=pos, current_price=10_010, minute_bars=bars))

        self.assertEqual(d.action, xs.ACTION_STOP_LOSS)
        self.assertEqual(d.exit_reason_code, xs.REASON_MOMENTUM_VOLUME_BEARISH_CANDLE)

    def test_partial_take_profit_at_2r(self):
        pos = base_position(entry_price=10_000, partial_taken=False)

        d = xs.evaluate_exit(ctx(position=pos, current_price=10_300))

        self.assertEqual(d.action, xs.ACTION_SELL_PARTIAL)
        self.assertAlmostEqual(d.qty_ratio, 0.5)
        self.assertTrue(d.mark_partial_taken)
        self.assertEqual(d.exit_reason_code, xs.REASON_TAKE_PROFIT_2R_PARTIAL)

    def test_trailing_high_pullback(self):
        pos = base_position(entry_price=10_000, partial_taken=True)
        pos.highest_price = 10_405

        d = xs.evaluate_exit(ctx(position=pos, current_price=10_300))

        self.assertEqual(d.action, xs.ACTION_TRAILING_STOP)
        self.assertEqual(d.exit_reason_code, xs.REASON_TRAILING_HIGH_PULLBACK)

    def test_time_stop_no_progress(self):
        pos = base_position(entry_price=10_000, entry1_offset_secs=-(xs.EXIT_TIME_LIMIT_SECONDS + 30))

        d = xs.evaluate_exit(ctx(position=pos, current_price=10_050))

        self.assertEqual(d.action, xs.ACTION_TIME_STOP)
        self.assertEqual(d.exit_reason_code, xs.REASON_TIME_STOP_NO_PROGRESS)

    def test_force_exit_after_1505(self):
        pos = base_position()

        d = xs.evaluate_exit(ctx(position=pos, current_price=10_050, force_exit=True))

        self.assertEqual(d.action, xs.ACTION_FORCE_EXIT)
        self.assertEqual(d.exit_reason_code, xs.REASON_FORCE_EXIT_AFTER_1505)

    def test_closing_auction_emergency_exit(self):
        pos = base_position()

        d = xs.evaluate_exit(ctx(position=pos, current_price=10_050, closing_auction_emergency=True))

        self.assertEqual(d.action, xs.ACTION_FORCE_EXIT)
        self.assertEqual(d.exit_reason_code, xs.REASON_CLOSING_AUCTION_EMERGENCY_EXIT)


if __name__ == "__main__":
    unittest.main()
