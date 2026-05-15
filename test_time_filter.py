from __future__ import annotations

import unittest
from datetime import datetime

from time_policy import (
    ALLOW_ENTRY,
    ALLOW_MANAGE_ONLY,
    BLOCK_AFTER_ENTRY_CUTOFF,
    BLOCK_CLOSING_AUCTION,
    BLOCK_NON_TRADING_DAY,
    BLOCK_OPENING_STABILIZATION,
    BLOCK_PRE_OPEN,
    CLOSING_AUCTION_EMERGENCY_EXIT,
    FORCE_EXIT_WINDOW,
    TimePolicy,
    load_timezone,
)
from trade_config import TradeConfig


SEOUL = load_timezone("Asia/Seoul")


def _at(clock: str, *, day: str = "2026-05-13") -> datetime:
    hour, minute, second = [int(part) for part in clock.split(":")]
    year, month, month_day = [int(part) for part in day.split("-")]
    return datetime(year, month, month_day, hour, minute, second, tzinfo=SEOUL)


class TimePolicyTests(unittest.TestCase):
    def test_blocks_before_regular_open(self):
        decision = TimePolicy(TradeConfig()).evaluate_entry(now=_at("08:59:00"))

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, BLOCK_PRE_OPEN)

    def test_blocks_opening_stabilization_period(self):
        decision = TimePolicy(TradeConfig()).evaluate_entry(now=_at("09:01:00"))

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, BLOCK_OPENING_STABILIZATION)
        self.assertIn("09:03:00", decision.next_allowed_time)

    def test_allows_main_entry_window(self):
        decision = TimePolicy(TradeConfig()).evaluate_entry(now=_at("09:05:00"))

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, ALLOW_ENTRY)

    def test_midday_entry_depends_on_configured_windows_and_defaults_to_block(self):
        decision = TimePolicy(TradeConfig()).evaluate_entry(now=_at("10:45:00"))

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, ALLOW_MANAGE_ONLY)
        self.assertIn("13:00:00", decision.next_allowed_time)
        self.assertEqual(
            TimePolicy(TradeConfig()).paper_strategy_type(now=_at("10:45:00")),
            "MIDDAY_VWAP_RECLAIM",
        )

    def test_allows_secondary_entry_window(self):
        decision = TimePolicy(TradeConfig()).evaluate_entry(now=_at("13:30:00"))

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, ALLOW_ENTRY)
        self.assertEqual(
            TimePolicy(TradeConfig()).paper_strategy_type(now=_at("13:30:00")),
            "AFTERNOON_SECOND_WAVE",
        )

    def test_blocks_after_new_entry_cutoff(self):
        decision = TimePolicy(TradeConfig()).evaluate_entry(now=_at("14:25:00"))

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, BLOCK_AFTER_ENTRY_CUTOFF)
        self.assertEqual(
            TimePolicy(TradeConfig()).paper_strategy_type(now=_at("14:25:00")),
            "CLOSING_STRENGTH",
        )

    def test_force_exit_window_allows_management_only(self):
        policy = TimePolicy(TradeConfig())
        entry = policy.evaluate_entry(now=_at("15:10:00"))
        manage = policy.evaluate_manage(now=_at("15:10:00"))

        self.assertFalse(entry.allowed)
        self.assertEqual(entry.action, FORCE_EXIT_WINDOW)
        self.assertTrue(manage.allowed)
        self.assertEqual(manage.action, FORCE_EXIT_WINDOW)

    def test_blocks_entry_during_closing_auction(self):
        decision = TimePolicy(TradeConfig()).evaluate_entry(now=_at("15:22:00"))

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, BLOCK_CLOSING_AUCTION)

    def test_closing_auction_manage_is_emergency_policy_only(self):
        decision = TimePolicy(TradeConfig()).evaluate_manage(now=_at("15:22:00"))

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, CLOSING_AUCTION_EMERGENCY_EXIT)
        self.assertEqual(decision.reason_code, CLOSING_AUCTION_EMERGENCY_EXIT)

    def test_closing_auction_manage_can_be_disabled_by_config(self):
        config = TradeConfig(allow_closing_auction_emergency_exit=False)
        decision = TimePolicy(config).evaluate_manage(now=_at("15:22:00"))

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, BLOCK_CLOSING_AUCTION)

    def test_configured_weekday_holiday_is_non_trading_day(self):
        config = TradeConfig(krx_holidays="2026-05-13")
        decision = TimePolicy(config).evaluate_entry(now=_at("09:05:00"))

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason_code, BLOCK_NON_TRADING_DAY)

    def test_candidate_capture_window_is_separate_from_entry_window(self):
        policy = TimePolicy(TradeConfig())

        capture = policy.evaluate_candidate_capture(now=_at("14:25:00"))
        entry = policy.evaluate_entry(now=_at("14:25:00"))

        self.assertTrue(capture.allowed)
        self.assertFalse(entry.allowed)
        self.assertEqual(entry.reason_code, BLOCK_AFTER_ENTRY_CUTOFF)


if __name__ == "__main__":
    unittest.main()
