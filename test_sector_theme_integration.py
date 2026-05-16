from __future__ import annotations

import csv
import os
import tempfile
import unittest

import entry_strategy as es
import market_state as ms
import review.loader as loader
import training_recorder
from sector_state import SectorContext
from theme_state import ThemeContext


class _Config:
    sector_gate_enforcement_enabled = False
    theme_gate_enforcement_enabled = False


class SectorThemeIntegrationTests(unittest.TestCase):
    def test_missing_context_does_not_break_first_entry(self):
        from test_entry_strategy import build_ctx

        d = es.evaluate_first_entry(build_ctx())
        self.assertIn(d.status, ("wait", "ready", "blocked"))

    def test_dry_run_sector_risk_off_keeps_decision_shape(self):
        old = es.TRADE_CONFIG
        cfg = _Config()
        es.TRADE_CONFIG = cfg
        try:
            ctx = type("Ctx", (), {
                "market_state": None,
                "market_context": ms.MarketContext(symbol="1", primary_market_regime="neutral"),
                "sector_context": SectorContext(sector_regime="risk_off", sector_gate_action="dry_run_block_all", sector_gate_reason="SECTOR_RISK_OFF"),
                "theme_context": ThemeContext(theme_regime="strong", theme_gate_action="dry_run_boost", theme_gate_reason="THEME_STRONG"),
            })()
            decision = es.EntryDecision("ready", 1.0, 1, "ready", reason_code=es.READY_AGRADE_FIRST)
            out = es._apply_entry_context_gates(decision, ctx)
            self.assertEqual(out.status, "ready")
            self.assertEqual(out.ratio, 1.0)
            self.assertEqual(out.sector_gate_action, "dry_run_block_all")
        finally:
            es.TRADE_CONFIG = old

    def test_enforcement_sector_risk_off_blocks_chase(self):
        old = es.TRADE_CONFIG
        cfg = _Config()
        cfg.sector_gate_enforcement_enabled = True
        es.TRADE_CONFIG = cfg
        try:
            ctx = type("Ctx", (), {
                "market_state": None,
                "market_context": ms.MarketContext(symbol="1", primary_market_regime="neutral"),
                "sector_context": SectorContext(sector_regime="risk_off", sector_gate_action="dry_run_block_all", sector_gate_reason="SECTOR_RISK_OFF"),
                "theme_context": None,
            })()
            decision = es.EntryDecision("ready", 1.0, 1, "ready", reason_code=es.READY_AGRADE_FIRST)
            out = es._apply_entry_context_gates(decision, ctx)
            self.assertEqual(out.status, "blocked")
            self.assertEqual(out.reason_code, es.SECTOR_THEME_GATE_SECTOR_RISK_OFF)
        finally:
            es.TRADE_CONFIG = old

    def test_market_risk_off_not_overridden_by_theme_strong(self):
        old = es.TRADE_CONFIG
        es.TRADE_CONFIG = _Config()
        try:
            ctx = type("Ctx", (), {
                "market_state": None,
                "market_context": ms.MarketContext(symbol="1", primary_market_regime="risk_off"),
                "sector_context": SectorContext(sector_regime="strong", sector_gate_action="dry_run_boost"),
                "theme_context": ThemeContext(theme_regime="strong", theme_gate_action="dry_run_boost"),
            })()
            decision = es.EntryDecision("ready", 1.0, 1, "ready", reason_code=es.READY_AGRADE_FIRST)
            out = es._apply_entry_context_gates(decision, ctx)
            self.assertEqual(out.market_gate_action, es.MARKET_ACTION_BLOCK_ALL)
            self.assertEqual(out.status, "ready")
        finally:
            es.TRADE_CONFIG = old

    def test_training_header_extends_old_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sample.csv")
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["sample_id", "market_regime"])
                writer.writeheader()
                writer.writerow({"sample_id": "1", "market_regime": "neutral"})
            training_recorder._ensure_csv_header(
                path,
                ["sample_id", "market_regime", "sector_regime", "theme_regime"],
                log_label="test",
            )
            with open(path, newline="", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            self.assertIn("sector_regime", rows[0])
            self.assertIn("theme_regime", rows[0])

    def test_review_loader_accepts_missing_new_columns(self):
        trade = loader.Trade(date="2026-05-16", code="000001")
        loader._attach_row_features(trade, {"turnover_rank_sector": "1"})
        self.assertEqual(trade.features["turnover_rank_sector"], 1.0)


if __name__ == "__main__":
    unittest.main()
