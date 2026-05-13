import csv
import tempfile
import unittest
from pathlib import Path

from momentum_breakout_strategy import EntryDecision
from momentum_replay import (
    RESULT_FIELDS,
    MomentumReplayRunner,
    load_condition_events,
    load_minute_bars,
    mock_condition_event,
    run_replay,
)
from trade_config import TradeConfig


ROOT = Path(__file__).resolve().parent
EVENTS = ROOT / "sample_data" / "momentum_condition_events.csv"
BARS = ROOT / "sample_data" / "momentum_minute_bars.csv"


class MomentumReplayTests(unittest.TestCase):
    def test_sample_replay_covers_all_decisions(self):
        events = load_condition_events(EVENTS)
        bars_by_code = load_minute_bars(BARS)
        runner = MomentumReplayRunner(config=TradeConfig())

        results = runner.run(events=events, bars_by_code=bars_by_code)
        by_code = {row.code: row for row in results}

        self.assertEqual(by_code["BUY1"].decision, EntryDecision.BUY)
        self.assertEqual(by_code["BUY1"].entry_price, 9850)
        self.assertEqual(by_code["BUY1"].stop_price, 9702)
        self.assertEqual(by_code["BUY1"].take_profit_price, 10047)
        self.assertEqual(by_code["WAIT1"].decision, EntryDecision.WAIT_PULLBACK)
        self.assertEqual(by_code["BLOCK1"].decision, EntryDecision.BLOCK_CHASE)
        self.assertEqual(by_code["REJECT1"].decision, EntryDecision.REJECT)
        self.assertGreater(by_code["BLOCK1"].chase_risk_score, 0.0)

    def test_run_replay_writes_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "momentum_replay_results.csv"

            results = run_replay(
                events_path=EVENTS,
                bars_path=BARS,
                output_path=output,
                config=TradeConfig(),
            )

            self.assertEqual(len(results), 4)
            with output.open("r", newline="", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 4)
            self.assertEqual(list(rows[0].keys()), RESULT_FIELDS)
            self.assertEqual(rows[0]["code"], "BUY1")

    def test_mock_condition_event_can_drive_replay(self):
        event = mock_condition_event(
            code="MOCK1",
            detected_at="2026-05-13 09:30:00",
            capture_price=10000,
        )

        self.assertEqual(event.code, "MOCK1")
        self.assertEqual(event.capture_price, 10000)
        self.assertGreater(event.detected_ts, 0.0)

    def test_replay_uses_default_strategy_risk_config(self):
        config = TradeConfig(
            default_stop_loss_pct=0.02,
            default_take_profit_pct=0.03,
        )
        runner = MomentumReplayRunner(config=config)

        self.assertEqual(runner.stop_loss_pct, 0.02)
        self.assertEqual(runner.take_profit_pct, 0.03)

    def test_replay_specific_config_overrides_default_risk_config(self):
        config = TradeConfig(
            default_stop_loss_pct=0.02,
            default_take_profit_pct=0.03,
            replay_stop_loss_pct=0.01,
            replay_take_profit_pct=0.04,
        )
        runner = MomentumReplayRunner(config=config)

        self.assertEqual(runner.stop_loss_pct, 0.01)
        self.assertEqual(runner.take_profit_pct, 0.04)


if __name__ == "__main__":
    unittest.main()
