from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from condition_capture_logger import ConditionCaptureLogger, read_condition_captures
from quant_backtest import BacktestTick, QuantConditionBacktester, QuantForwardSimulator
from quant_condition_strategy import QuantConditionStrategy


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
        )
        self.assertEqual(weak.status, "wait")
        self.assertEqual(weak.reason_code, "SAFE_CHEJAN_WAIT")

        ready = self.strategy.evaluate_entry(
            capture_price=10_000,
            current_price=9_850,
            chejan_strength=100,
        )
        self.assertEqual(ready.status, "ready")
        self.assertEqual(ready.reason_code, "QUANT_PULLBACK_READY")
        self.assertGreater(ready.take_profit_price, ready.entry_limit_price)
        self.assertLess(ready.stop_price, ready.entry_limit_price)

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
                    BacktestTick("005930", 9_850, 100, "091100"),
                    BacktestTick("005930", 10_050, 120, "091500"),
                ]
            },
        )

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].code, "005930")
        self.assertGreaterEqual(trades[0].return_pct, 0.02)

    def test_forward_simulator_uses_same_rules(self):
        simulator = QuantForwardSimulator()
        simulator.on_capture("005930", 10_000)

        wait = simulator.on_tick(BacktestTick("005930", 9_900, 120, "091000"))
        self.assertEqual(wait["state"], "watching")

        entered = simulator.on_tick(BacktestTick("005930", 9_850, 100, "091100"))
        self.assertEqual(entered["state"], "entered")

        holding = simulator.on_tick(BacktestTick("005930", 10_050, 110, "091500"))
        self.assertEqual(holding["exit_action"], "sell")
        self.assertEqual(len(simulator.closed_trades), 1)


if __name__ == "__main__":
    unittest.main()
