from __future__ import annotations

import os
import tempfile
import unittest

from theme_state import ThemeStateCache


class ThemeStateTests(unittest.TestCase):
    def _cache(self):
        tmp = tempfile.TemporaryDirectory()
        path = os.path.join(tmp.name, "theme_map.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write("theme_name,code,role\n")
            f.write("AI,123456,leader\n")
            f.write("AI,234567,member\n")
            f.write("Robot,123456,member\n")
            f.write("Robot,345678,leader\n")
        cache = ThemeStateCache(path)
        cache.load_theme_map()
        return tmp, cache

    def test_load_and_multiple_themes(self):
        tmp, cache = self._cache()
        self.addCleanup(tmp.cleanup)
        self.assertEqual(cache.themes_for_symbol("123456"), ["AI", "Robot"])

    def test_active_count_under_min_unknown(self):
        tmp, cache = self._cache()
        self.addCleanup(tmp.cleanup)
        snap = cache.snapshot_theme("AI", lambda code: {"return_pct": 0.02, "turnover": 10} if code == "123456" else None)
        self.assertEqual(snap.theme_regime, "unknown")
        self.assertEqual(snap.theme_gate_action, "dry_run_allow")

    def test_strong_weak_and_risk_off(self):
        tmp, cache = self._cache()
        self.addCleanup(tmp.cleanup)
        strong = cache.snapshot_theme("AI", lambda code: {"return_pct": 0.02, "turnover": 100})
        weak = cache.snapshot_theme("AI", lambda code: {"return_pct": -0.011, "turnover": 100})
        risk = cache.snapshot_theme("AI", lambda code: {"return_pct": -0.03, "turnover": 100})
        self.assertEqual(strong.theme_regime, "strong")
        self.assertEqual(strong.theme_gate_action, "dry_run_boost")
        self.assertEqual(weak.theme_regime, "weak")
        self.assertEqual(risk.theme_regime, "risk_off")
        self.assertEqual(risk.theme_gate_action, "dry_run_block_chase_only")

    def test_unknown_symbol_fallback(self):
        tmp, cache = self._cache()
        self.addCleanup(tmp.cleanup)
        ctx = cache.snapshot_for_symbol("000000", lambda code: None)
        self.assertEqual(ctx.theme_regime, "unknown")
        self.assertEqual(ctx.theme_gate_action, "dry_run_allow")


if __name__ == "__main__":
    unittest.main()
