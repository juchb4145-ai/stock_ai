from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bars import MinuteBar
from condition_capture_logger import ConditionCaptureLogger, read_condition_captures
from quant_backtest import (
    BacktestExecutionConfig,
    BacktestTick,
    QuantConditionBacktester,
    QuantForwardSimulator,
)
from quant_condition_strategy import QuantConditionStrategy, QuantStrategyConfig


class QuantConditionStrategyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = QuantConditionStrategy()

    def test_entry_waits_until_pullback_and_strength_pass(self):
        shallow = self.strategy.evaluate_entry(
            capture_price=10_000,
            current_price=9_900,
            chejan_strength=120,
        )
        self.assertEqual(shallow.status, "wait")
        self.assertEqual(shallow.reason_code, "SAFE_PULLBACK_SHALLOW")

        weak = self.strategy.evaluate_entry(
            capture_price=10_000,
            current_price=9_850,
            chejan_strength=99.9,
            recent_low_price=9_820,
        )
        self.assertEqual(weak.status, "wait")
        self.assertEqual(weak.reason_code, "SAFE_CHEJAN_WAIT")

        ready = self.strategy.evaluate_entry(
            capture_price=10_000,
            current_price=9_850,
            chejan_strength=100,
            recent_low_price=9_820,
        )
        self.assertEqual(ready.status, "ready")
        self.assertEqual(ready.reason_code, "QUANT_PULLBACK_READY")
        self.assertGreater(ready.take_profit_price, ready.entry_limit_price)
        self.assertLess(ready.stop_price, ready.entry_limit_price)
        self.assertGreaterEqual(ready.rebound_pct, self.strategy.config.rebound_confirm_pct)

    def test_entry_blocks_pullback_deeper_than_three_percent(self):
        decision = self.strategy.evaluate_entry(
            capture_price=10_000,
            current_price=9_690,
            chejan_strength=130,
            recent_low_price=9_650,
        )

        self.assertEqual(decision.status, "wait")
        self.assertEqual(decision.reason_code, "SAFE_PULLBACK_TOO_DEEP")

    def test_entry_waits_for_rebound_from_recent_low(self):
        decision = self.strategy.evaluate_entry(
            capture_price=10_000,
            current_price=9_850,
            chejan_strength=130,
            recent_low_price=9_840,
        )

        self.assertEqual(decision.status, "wait")
        self.assertEqual(decision.reason_code, "SAFE_REBOUND_WAIT")

        ready = self.strategy.evaluate_entry(
            capture_price=10_000,
            current_price=9_850,
            chejan_strength=130,
            recent_low_price=9_820,
        )
        self.assertEqual(ready.status, "ready")

    def test_weak_market_raises_chejan_strength_threshold(self):
        weak = self.strategy.evaluate_entry(
            capture_price=10_000,
            current_price=9_850,
            chejan_strength=119.9,
            recent_low_price=9_820,
            market_state="weak",
        )
        self.assertEqual(weak.reason_code, "SAFE_CHEJAN_WAIT")
        self.assertEqual(weak.min_chejan_strength, 120.0)

        strong = self.strategy.evaluate_entry(
            capture_price=10_000,
            current_price=9_850,
            chejan_strength=100.0,
            recent_low_price=9_820,
            market_state="strong",
        )
        self.assertEqual(strong.status, "ready")
        self.assertEqual(strong.min_chejan_strength, 100.0)

    def test_market_strength_config_can_keep_neutral_at_110(self):
        strategy = QuantConditionStrategy(
            QuantStrategyConfig(market_min_chejan_strength={"neutral": 110.0, "weak": 120.0})
        )

        blocked = strategy.evaluate_entry(
            capture_price=10_000,
            current_price=9_850,
            chejan_strength=109.9,
            recent_low_price=9_820,
            market_state="neutral",
        )
        self.assertEqual(blocked.reason_code, "SAFE_CHEJAN_WAIT")
        self.assertEqual(blocked.min_chejan_strength, 110.0)

    def test_high_since_capture_pullback_can_pass_even_above_capture_price(self):
        decision = self.strategy.evaluate_entry(
            capture_price=10_000,
            high_since_capture=10_800,
            low_after_high=10_450,
            current_price=10_500,
            chejan_strength=125,
            recent_low_price=10_450,
            intraday_vwap=10_420,
            one_min_reversal=True,
        )

        self.assertEqual(decision.status, "ready")
        self.assertEqual(decision.reason_code, "QUANT_FIRST_PULLBACK_READY")
        self.assertAlmostEqual(decision.pullback_from_high_pct, (10_800 - 10_500) / 10_800)
        self.assertAlmostEqual(decision.rebound_from_low_pct, 10_500 / 10_450 - 1)
        self.assertTrue(decision.vwap_support_ok)
        self.assertTrue(decision.first_pullback_ready)

    def test_high_since_capture_pullback_is_shallow(self):
        decision = self.strategy.evaluate_entry(
            capture_price=10_000,
            high_since_capture=10_800,
            low_after_high=10_650,
            current_price=10_700,
            chejan_strength=125,
            recent_low_price=10_650,
            one_min_reversal=True,
        )

        self.assertEqual(decision.status, "wait")
        self.assertEqual(decision.reason_code, "SAFE_PULLBACK_FROM_HIGH_SHALLOW")

    def test_high_since_capture_pullback_too_deep(self):
        decision = self.strategy.evaluate_entry(
            capture_price=10_000,
            high_since_capture=10_800,
            low_after_high=10_360,
            current_price=10_400,
            chejan_strength=125,
            recent_low_price=10_360,
            one_min_reversal=True,
        )

        self.assertEqual(decision.status, "wait")
        self.assertEqual(decision.reason_code, "SAFE_PULLBACK_FROM_HIGH_TOO_DEEP")

    def test_high_since_capture_requires_low_after_high_and_rebound(self):
        missing_low = self.strategy.evaluate_entry(
            capture_price=10_000,
            high_since_capture=10_800,
            low_after_high=0,
            current_price=10_500,
            chejan_strength=125,
            recent_low_price=10_450,
            one_min_reversal=True,
        )
        self.assertEqual(missing_low.reason_code, "SAFE_LOW_AFTER_HIGH_MISSING")

        no_rebound = self.strategy.evaluate_entry(
            capture_price=10_000,
            high_since_capture=10_800,
            low_after_high=10_490,
            current_price=10_500,
            chejan_strength=125,
            recent_low_price=10_490,
            one_min_reversal=True,
        )
        self.assertEqual(no_rebound.reason_code, "SAFE_REBOUND_FROM_LOW_WAIT")

    def test_high_since_capture_vwap_and_strength_gates(self):
        below_vwap = self.strategy.evaluate_entry(
            capture_price=10_000,
            high_since_capture=10_800,
            low_after_high=10_450,
            current_price=10_500,
            chejan_strength=125,
            recent_low_price=10_450,
            intraday_vwap=10_600,
            one_min_reversal=True,
        )
        self.assertEqual(below_vwap.reason_code, "SAFE_VWAP_SUPPORT_WAIT")
        self.assertFalse(below_vwap.vwap_support_ok)

        weak = self.strategy.evaluate_entry(
            capture_price=10_000,
            high_since_capture=10_800,
            low_after_high=10_450,
            current_price=10_500,
            chejan_strength=99,
            recent_low_price=10_450,
            intraday_vwap=10_420,
            one_min_reversal=True,
        )
        self.assertEqual(weak.reason_code, "SAFE_CHEJAN_WAIT")

    def test_one_minute_reversal_can_confirm_with_positive_bar_or_prev_high_reclaim(self):
        positive_bar = [
            MinuteBar(0, 10_470, 10_520, 10_430, 10_500, 100, 0),
        ]
        decision = self.strategy.evaluate_entry(
            capture_price=10_000,
            high_since_capture=10_800,
            low_after_high=10_450,
            current_price=10_500,
            chejan_strength=125,
            recent_low_price=10_450,
            minute_bars=positive_bar,
        )
        self.assertEqual(decision.reason_code, "QUANT_FIRST_PULLBACK_READY")

        weak_bar = [
            MinuteBar(0, 10_520, 10_540, 10_480, 10_490, 100, 0),
        ]
        wait = self.strategy.evaluate_entry(
            capture_price=10_000,
            high_since_capture=10_800,
            low_after_high=10_450,
            current_price=10_500,
            chejan_strength=125,
            recent_low_price=10_450,
            minute_bars=weak_bar,
        )
        self.assertEqual(wait.reason_code, "SAFE_ONE_MIN_REVERSAL_WAIT")

    def test_exit_sells_all_at_profit_or_stop(self):
        profit = self.strategy.evaluate_exit(entry_price=10_000, current_price=10_200)
        self.assertEqual(profit.action, "sell")
        self.assertEqual(profit.qty_ratio, 1.0)
        self.assertIn("익절", profit.reason)

        stop = self.strategy.evaluate_exit(entry_price=10_000, current_price=9_850)
        self.assertEqual(stop.action, "sell")
        self.assertEqual(stop.qty_ratio, 1.0)
        self.assertIn("손절", stop.reason)


class ConditionCaptureLoggerTests(unittest.TestCase):
    def test_appends_detection_and_capture_price_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "captures.csv"
            logger = ConditionCaptureLogger(str(path))

            logger.append_detection(
                code="005930",
                name="삼성전자",
                condition_name="퀀트조건식",
                condition_index=1,
                event_type="I",
                screen_no="0150",
            )
            logger.append_capture_price(
                code="005930",
                name="삼성전자",
                condition_name="퀀트조건식",
                condition_index=1,
                event_type="I",
                screen_no="0160",
                capture_price=10_000,
                entry_trigger_price=9_850,
                chejan_strength=101.2,
                accum_volume=12345,
            )

            rows = read_condition_captures(str(path))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["event"], "condition_detected")
            self.assertEqual(rows[1]["event"], "capture_price")
            self.assertEqual(rows[1]["capture_price"], "10000")


class QuantBacktestTests(unittest.TestCase):
    def test_replays_capture_to_closed_trade(self):
        backtester = QuantConditionBacktester()
        trades = backtester.run(
            captures=[{"code": "005930", "capture_price": 10_000}],
            ticks_by_code={
                "005930": [
                    BacktestTick("005930", 9_900, 110, "091000"),
                    BacktestTick("005930", 9_700, 120, "091100"),
                    BacktestTick("005930", 9_730, 120, "091200"),
                    BacktestTick("005930", 9_960, 120, "091500"),
                ]
            },
        )

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].code, "005930")
        self.assertGreaterEqual(trades[0].gross_return_pct, 0.02)
        self.assertLess(trades[0].return_pct, trades[0].gross_return_pct)
        self.assertGreater(trades[0].fee_cost + trades[0].tax_cost, 0)

    def test_backtest_waits_for_limit_fill_after_latency(self):
        backtester = QuantConditionBacktester(
            execution=BacktestExecutionConfig(
                buy_slippage_pct=0.0,
                sell_slippage_pct=0.0,
                latency_ticks=1,
            )
        )
        trades = backtester.run(
            captures=[{"code": "005930", "capture_price": 10_000}],
            ticks_by_code={
                "005930": [
                    BacktestTick("005930", 9_730, 130, "091200", low_price=9_730),
                    BacktestTick("005930", 9_760, 130, "091201", low_price=9_750),
                    BacktestTick("005930", 9_730, 130, "091202", low_price=9_720),
                    BacktestTick("005930", 9_930, 130, "091500"),
                ]
            },
        )

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].entry_at, "091202")

    def test_backtest_blocks_partial_fill_below_min_ratio(self):
        backtester = QuantConditionBacktester(
            execution=BacktestExecutionConfig(
                quantity=10,
                min_fill_ratio=1.0,
                buy_slippage_pct=0.0,
                sell_slippage_pct=0.0,
            )
        )
        trades = backtester.run(
            captures=[{"code": "005930", "capture_price": 10_000}],
            ticks_by_code={
                "005930": [
                    BacktestTick(
                        "005930",
                        9_730,
                        130,
                        "091200",
                        low_price=9_720,
                        available_volume=3,
                    ),
                    BacktestTick("005930", 9_930, 130, "091500"),
                ]
            },
        )

        self.assertEqual(trades, [])

    def test_backtest_uses_bid_ask_and_order_rate_limit(self):
        captures = [
            {"code": f"00000{i}", "capture_price": 10_000}
            for i in range(6)
        ]
        ticks_by_code = {
            str(capture["code"]): [
                BacktestTick(
                    str(capture["code"]),
                    9_700,
                    130,
                    "091159",
                    bid_price=9_690,
                    ask_price=9_700,
                    low_price=9_690,
                ),
                BacktestTick(
                    str(capture["code"]),
                    9_730,
                    130,
                    "091200",
                    bid_price=9_720,
                    ask_price=9_730,
                    low_price=9_720,
                ),
                BacktestTick(
                    str(capture["code"]),
                    9_960,
                    130,
                    "091500",
                    bid_price=9_950,
                    ask_price=9_960,
                ),
            ]
            for capture in captures
        }
        backtester = QuantConditionBacktester(
            execution=BacktestExecutionConfig(
                buy_slippage_pct=0.0,
                sell_slippage_pct=0.0,
                max_orders_per_second=5,
            )
        )

        trades = backtester.run(captures=captures, ticks_by_code=ticks_by_code)

        self.assertEqual(len(trades), 6)
        self.assertEqual(trades[0].entry_price, 9_730)
        self.assertEqual(trades[0].exit_price, 9_950)
        self.assertEqual(trades[5].entry_order_at, "091201")

    def test_forward_simulator_uses_same_rules(self):
        simulator = QuantForwardSimulator()
        simulator.on_capture("005930", 10_000)

        wait = simulator.on_tick(BacktestTick("005930", 9_900, 120, "091000"))
        self.assertEqual(wait["state"], "watching")

        rebound_wait = simulator.on_tick(BacktestTick("005930", 9_820, 120, "091100"))
        self.assertEqual(rebound_wait["reason_code"], "SAFE_REBOUND_WAIT")

        entered = simulator.on_tick(BacktestTick("005930", 9_850, 120, "091200"))
        self.assertEqual(entered["state"], "entered")

        holding = simulator.on_tick(BacktestTick("005930", 10_050, 110, "091500"))
        self.assertEqual(holding["exit_action"], "sell")
        self.assertEqual(len(simulator.closed_trades), 1)


if __name__ == "__main__":
    unittest.main()
