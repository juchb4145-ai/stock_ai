from __future__ import annotations

import os
import tempfile
import unittest

import market_state as ms
from sector_state import SectorStateCache


def _ts(minute: int) -> float:
    return 1_700_000_000.0 + minute * 60


class SectorStateTests(unittest.TestCase):
    def test_missing_map_unknown_fallback(self):
        cache = SectorStateCache("missing_sector_map.csv")
        cache.load_sector_maps()
        ctx = cache.snapshot_for_symbol("005930")
        self.assertEqual(ctx.sector_regime, "unknown")
        self.assertEqual(ctx.sector_gate_action, "dry_run_allow")
        self.assertEqual(ctx.sector_gate_reason, "SECTOR_UNKNOWN_FALLBACK")

    def test_mapping_snapshot_update_and_relative_strength(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sector_map.csv")
            with open(path, "w", encoding="utf-8") as f:
                f.write("code,name,market,sector_code,sector_name,sector_index_code\n")
                f.write("123456,예시,KOSDAQ,201,반도체,201\n")
            cache = SectorStateCache(path)
            cache.load_sector_maps()
            self.assertEqual(cache.resolve_symbol_sector("A123456")["sector_code"], "201")
            cache.register_sector_index_if_needed("201")
            cache.update("201", 100.0, _ts(0))
            cache.update("201", 102.0, _ts(1))
            market_ctx = ms.MarketContext(
                symbol="123456",
                symbol_market="KOSDAQ",
                primary_market_regime="neutral",
                primary_market_pct=0.005,
            )
            ctx = cache.snapshot_for_symbol("123456", "KOSDAQ", market_ctx)
            self.assertEqual(ctx.sector_regime, "strong")
            self.assertAlmostEqual(ctx.sector_relative_strength_vs_primary, 0.015)
            self.assertEqual(ctx.sector_gate_action, "dry_run_boost")

    def test_weak_and_risk_off_gate_actions(self):
        cache = SectorStateCache()
        weak = cache._with_gate(type("S", (), {"sector_regime": "weak"})())
        risk = cache._with_gate(type("S", (), {"sector_regime": "risk_off"})())
        self.assertEqual(weak.sector_gate_action, "dry_run_block_chase_only")
        self.assertEqual(risk.sector_gate_action, "dry_run_block_all")


if __name__ == "__main__":
    unittest.main()
