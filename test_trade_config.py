import os
import unittest
from unittest import mock

from trade_config import TradeConfig, _env_bool


class TradeConfigBoolEnvTests(unittest.TestCase):
    def test_env_bool_uses_default_when_unset(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(_env_bool("KIWOOM_DRY_RUN", True))
            self.assertFalse(_env_bool("KIWOOM_DRY_RUN", False))

    def test_env_bool_accepts_true_values(self):
        for value in ("1", "true", "t", "yes", "y", "on"):
            with self.subTest(value=value):
                with mock.patch.dict(os.environ, {"KIWOOM_DRY_RUN": value}):
                    self.assertTrue(_env_bool("KIWOOM_DRY_RUN", False))

    def test_env_bool_accepts_false_values(self):
        for value in ("0", "false", "f", "no", "n", "off"):
            with self.subTest(value=value):
                with mock.patch.dict(os.environ, {"KIWOOM_DRY_RUN": value}):
                    self.assertFalse(_env_bool("KIWOOM_DRY_RUN", True))

    def test_env_bool_rejects_typo_values(self):
        for value in ("flase", "maybe", ""):
            with self.subTest(value=value):
                with mock.patch.dict(os.environ, {"KIWOOM_DRY_RUN": value}):
                    with self.assertRaises(ValueError):
                        _env_bool("KIWOOM_DRY_RUN", True)

    def test_trade_config_rejects_misspelled_dry_run(self):
        with mock.patch.dict(os.environ, {"KIWOOM_DRY_RUN": "flase"}):
            with self.assertRaises(ValueError):
                TradeConfig.from_env()

    def test_live_mode_requires_separate_confirmation_flag(self):
        with mock.patch.dict(
            os.environ,
            {
                "KIWOOM_DRY_RUN": "false",
                "KIWOOM_LIVE_TRADING_ENABLED": "true",
            },
        ):
            config = TradeConfig.from_env()

        self.assertFalse(config.dry_run)
        self.assertTrue(config.live_trading_enabled)

    def test_risk_reward_defaults_and_replay_fallbacks(self):
        config = TradeConfig()

        self.assertEqual(config.condition_name, "단테떡상이_수정")
        self.assertEqual(config.legacy_condition_name, "단테떡상이")
        self.assertEqual(config.primary_condition_name, "단테떡상이_수정")
        self.assertEqual(config.bonus_condition_name, "단테떡상이")
        self.assertEqual(config.entry_strategy_version, "quant_first_pullback_v1")
        self.assertFalse(config.allow_breakout_probe_entry)
        self.assertEqual(config.breakout_probe_entry_ratio, 0.0)
        self.assertEqual(config.cash_usage_ratio, 0.98)
        self.assertEqual(config.max_position_cash_ratio, 0.10)
        self.assertEqual(config.default_stop_loss_pct, 0.015)
        self.assertEqual(config.default_take_profit_pct, 0.020)
        self.assertEqual(config.resolved_replay_stop_loss_pct, config.default_stop_loss_pct)
        self.assertEqual(config.resolved_replay_take_profit_pct, config.default_take_profit_pct)

    def test_replay_risk_env_can_override_defaults(self):
        with mock.patch.dict(
            os.environ,
            {
                "KIWOOM_DEFAULT_STOP_LOSS_PCT": "0.02",
                "KIWOOM_DEFAULT_TAKE_PROFIT_PCT": "0.03",
                "KIWOOM_REPLAY_STOP_LOSS_PCT": "0.01",
                "KIWOOM_REPLAY_TAKE_PROFIT_PCT": "0.04",
            },
        ):
            config = TradeConfig.from_env()

        self.assertEqual(config.default_stop_loss_pct, 0.02)
        self.assertEqual(config.default_take_profit_pct, 0.03)
        self.assertEqual(config.resolved_replay_stop_loss_pct, 0.01)
        self.assertEqual(config.resolved_replay_take_profit_pct, 0.04)

    def test_time_policy_defaults_are_configured(self):
        config = TradeConfig()

        self.assertEqual(config.trading_timezone, "Asia/Seoul")
        self.assertEqual(config.candidate_capture_start, "09:00:00")
        self.assertEqual(config.candidate_capture_end, "14:50:00")
        self.assertEqual(config.entry_windows, "09:03:00-10:30:00,13:00:00-14:20:00")
        self.assertEqual(config.no_new_entry_after, "14:20:00")
        self.assertEqual(config.force_exit_start, "15:05:00")
        self.assertEqual(config.force_exit_deadline, "15:19:30")
        self.assertEqual(config.closing_auction_start, "15:20:00")
        self.assertEqual(config.closing_auction_end, "15:30:00")
        self.assertFalse(config.allow_after_hours_entry)
        self.assertFalse(config.allow_nxt_trading)

    def test_exit_policy_defaults_are_configured(self):
        config = TradeConfig()

        self.assertTrue(config.technical_stop_enabled)
        self.assertTrue(config.structure_stop_enabled)
        self.assertTrue(config.vwap_stop_enabled)
        self.assertEqual(config.vwap_reclaim_wait_sec, 60)
        self.assertEqual(config.recent_low_lookback_bars, 3)
        self.assertTrue(config.enable_r_multiple_exit)
        self.assertTrue(config.partial_take_profit_enabled)
        self.assertEqual(config.first_partial_take_profit_r, 2.0)
        self.assertEqual(config.force_exit_start, "15:05:00")
        self.assertEqual(config.force_exit_deadline, "15:19:30")
        self.assertTrue(config.allow_closing_auction_emergency_exit)
        self.assertTrue(config.block_new_buys_on_exit_escalation)
        self.assertEqual(config.max_sell_retry_count, 3)

    def test_condition_role_env_overrides_keep_legacy_compatibility(self):
        with mock.patch.dict(
            os.environ,
            {
                "KIWOOM_PRIMARY_CONDITION_NAME": "primary-new",
                "KIWOOM_BONUS_CONDITION_NAME": "bonus-new",
            },
            clear=True,
        ):
            config = TradeConfig.from_env()

        self.assertEqual(config.primary_condition_name, "primary-new")
        self.assertEqual(config.bonus_condition_name, "bonus-new")
        self.assertEqual(config.condition_name, "primary-new")
        self.assertEqual(config.legacy_condition_name, "bonus-new")

        with mock.patch.dict(
            os.environ,
            {
                "KIWOOM_CONDITION_NAME": "primary-legacy-env",
                "KIWOOM_LEGACY_CONDITION_NAME": "bonus-legacy-env",
            },
            clear=True,
        ):
            config = TradeConfig.from_env()

        self.assertEqual(config.primary_condition_name, "primary-legacy-env")
        self.assertEqual(config.bonus_condition_name, "bonus-legacy-env")
        self.assertEqual(config.condition_name, "primary-legacy-env")
        self.assertEqual(config.legacy_condition_name, "bonus-legacy-env")


if __name__ == "__main__":
    unittest.main()
