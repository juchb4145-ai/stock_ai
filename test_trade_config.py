import ast
import importlib
import os
from pathlib import Path
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
        self.assertTrue(config.leader_score_enabled)
        self.assertEqual(config.min_leader_score, 60.0)
        self.assertEqual(config.opening_min_leader_score, 65.0)
        self.assertEqual(config.opening_quant_and_dante_min_leader_score, 60.0)
        self.assertEqual(config.opening_quant_only_min_leader_score, 65.0)
        self.assertEqual(config.first_pullback_leader_score_relief, 7.0)
        self.assertEqual(config.post_opening_min_leader_score, 60.0)
        self.assertEqual(config.opening_leader_start, "09:00:00")
        self.assertEqual(config.opening_leader_end, "09:30:00")
        self.assertEqual(config.leader_score_turnover_speed_full, 200_000_000.0)
        self.assertEqual(config.leader_score_trade_value_full, 500_000_000.0)
        self.assertEqual(config.leader_score_volume_ratio_full, 2.0)
        self.assertEqual(config.leader_score_chejan_full, 200.0)
        self.assertEqual(config.cash_usage_ratio, 0.98)
        self.assertEqual(config.max_position_cash_ratio, 0.10)
        self.assertEqual(config.max_daily_exposure_ratio, 0.30)
        self.assertEqual(config.max_position_size, 0)
        self.assertEqual(config.max_daily_exposure, 0)
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
        self.assertEqual(config.midday_paper_window, "10:30:00-13:00:00")
        self.assertTrue(config.midday_live_entry_enabled)
        self.assertEqual(config.midday_live_entry_ratio, 0.25)
        self.assertEqual(config.afternoon_entry_window, "13:00:00-14:20:00")
        self.assertEqual(config.closing_paper_window, "14:20:00-14:50:00")
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

    def test_leader_score_env_overrides_are_loaded(self):
        with mock.patch.dict(
            os.environ,
            {
                "KIWOOM_LEADER_SCORE_ENABLED": "false",
                "KIWOOM_MIN_LEADER_SCORE": "55",
                "KIWOOM_OPENING_MIN_LEADER_SCORE": "75",
                "KIWOOM_OPENING_QUANT_AND_DANTE_MIN_LEADER_SCORE": "61",
                "KIWOOM_OPENING_QUANT_ONLY_MIN_LEADER_SCORE": "66",
                "KIWOOM_FIRST_PULLBACK_LEADER_SCORE_RELIEF": "8",
                "KIWOOM_POST_OPENING_MIN_LEADER_SCORE": "62",
                "KIWOOM_OPENING_LEADER_START": "09:04:00",
                "KIWOOM_OPENING_LEADER_END": "09:25:00",
                "KIWOOM_LEADER_SCORE_TURNOVER_SPEED_FULL": "300000000",
                "KIWOOM_LEADER_SCORE_TRADE_VALUE_FULL": "700000000",
                "KIWOOM_LEADER_SCORE_VOLUME_RATIO_FULL": "3.5",
                "KIWOOM_LEADER_SCORE_CHEJAN_FULL": "240",
            },
            clear=True,
        ):
            config = TradeConfig.from_env()

        self.assertFalse(config.leader_score_enabled)
        self.assertEqual(config.min_leader_score, 55.0)
        self.assertEqual(config.opening_min_leader_score, 75.0)
        self.assertEqual(config.opening_quant_and_dante_min_leader_score, 61.0)
        self.assertEqual(config.opening_quant_only_min_leader_score, 66.0)
        self.assertEqual(config.first_pullback_leader_score_relief, 8.0)
        self.assertEqual(config.post_opening_min_leader_score, 62.0)
        self.assertEqual(config.opening_leader_start, "09:04:00")
        self.assertEqual(config.opening_leader_end, "09:25:00")
        self.assertEqual(config.leader_score_turnover_speed_full, 300_000_000.0)
        self.assertEqual(config.leader_score_trade_value_full, 700_000_000.0)
        self.assertEqual(config.leader_score_volume_ratio_full, 3.5)
        self.assertEqual(config.leader_score_chejan_full, 240.0)

    def test_first_pullback_modules_import_cleanly(self):
        for module_name in (
            "trade_config",
            "quant_condition_strategy",
            "momentum_breakout_strategy",
            "candidate_registry",
            "final_entry_decision",
            "order_guard",
        ):
            with self.subTest(module=module_name):
                importlib.import_module(module_name)

    def test_direct_trade_config_references_exist(self):
        root = Path(__file__).resolve().parent
        config_tree = ast.parse((root / "trade_config.py").read_text(encoding="utf-8"))
        trade_config_fields = set()
        for node in ast.walk(config_tree):
            if isinstance(node, ast.ClassDef) and node.name == "TradeConfig":
                for stmt in node.body:
                    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                        trade_config_fields.add(stmt.target.id)
                break

        target_files = (
            "quant_condition_strategy.py",
            "momentum_breakout_strategy.py",
            "candidate_registry.py",
            "final_entry_decision.py",
            "order_guard.py",
            "main.py",
        )
        missing = {}
        for filename in target_files:
            tree = ast.parse((root / filename).read_text(encoding="utf-8"))
            refs = {
                node.attr
                for node in ast.walk(tree)
                if isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "TRADE_CONFIG"
            }
            missing[filename] = sorted(refs - trade_config_fields)

        self.assertEqual({k: v for k, v in missing.items() if v}, {})


if __name__ == "__main__":
    unittest.main()
