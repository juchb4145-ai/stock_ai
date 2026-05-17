from __future__ import annotations

import os
import tempfile
import unittest

from sector_state import SectorStateCache
from sector_theme_maps import validate_sector_map, validate_theme_map
from theme_state import ThemeStateCache
from tools.bootstrap_sector_theme_maps import main as bootstrap_main


class SectorThemeMapValidationTests(unittest.TestCase):
    def test_header_only_maps_are_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            sector = os.path.join(tmp, "sector_map.csv")
            theme = os.path.join(tmp, "theme_map.csv")
            with open(sector, "w", encoding="utf-8") as f:
                f.write("code,name,market,sector_code,sector_name,sector_index_code\n")
            with open(theme, "w", encoding="utf-8") as f:
                f.write("theme_name,code,role\n")

            sector_report = validate_sector_map(sector)
            theme_report = validate_theme_map(theme)

            self.assertTrue(sector_report.header_only)
            self.assertTrue(sector_report.empty)
            self.assertEqual(sector_report.status(), "header_only")
            self.assertTrue(theme_report.header_only)
            self.assertTrue(theme_report.empty)
            self.assertEqual(theme_report.status(), "header_only")

    def test_loaders_warn_and_keep_unknown_fallback_on_header_only_maps(self):
        with tempfile.TemporaryDirectory() as tmp:
            sector = os.path.join(tmp, "sector_map.csv")
            theme = os.path.join(tmp, "theme_map.csv")
            with open(sector, "w", encoding="utf-8") as f:
                f.write("code,name,market,sector_code,sector_name,sector_index_code\n")
            with open(theme, "w", encoding="utf-8") as f:
                f.write("theme_name,code,role\n")

            sector_cache = SectorStateCache(sector)
            theme_cache = ThemeStateCache(theme)
            with self.assertLogs("kiwoom", level="WARNING") as logs:
                sector_cache.load_sector_maps()
                theme_cache.load_theme_map()

            joined = "\n".join(logs.output)
            self.assertIn("sector_map status=header_only", joined)
            self.assertIn("theme_map status=header_only", joined)
            self.assertEqual(sector_cache.snapshot_for_symbol("005930").sector_gate_reason, "SECTOR_UNKNOWN_FALLBACK")
            self.assertEqual(theme_cache.snapshot_for_symbol("005930", lambda code: None).theme_gate_reason, "THEME_UNKNOWN_FALLBACK")

    def test_bootstrap_writes_and_validates_local_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            sector_source = os.path.join(tmp, "sector_source.json")
            theme_source = os.path.join(tmp, "theme_source.json")
            sector_out = os.path.join(tmp, "sector_map.csv")
            theme_out = os.path.join(tmp, "theme_map.csv")
            with open(sector_source, "w", encoding="utf-8") as f:
                f.write('{"101": {"sector_name": "Semiconductor", "sector_index_code": "IDX101", "members": [{"code": "A005930", "name": "Samsung", "market": "KOSPI"}]}}')
            with open(theme_source, "w", encoding="utf-8") as f:
                f.write('{"AI": [{"code": "005930", "role": "leader"}, "000660"]}')

            rc = bootstrap_main(
                [
                    "--sector-source",
                    sector_source,
                    "--theme-source",
                    theme_source,
                    "--sector-out",
                    sector_out,
                    "--theme-out",
                    theme_out,
                    "--fail-on-empty",
                ]
            )

            self.assertEqual(rc, 0)
            self.assertTrue(validate_sector_map(sector_out).ok)
            self.assertTrue(validate_theme_map(theme_out).ok)

    def test_validate_only_fail_on_empty_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            sector = os.path.join(tmp, "sector_map.csv")
            theme = os.path.join(tmp, "theme_map.csv")
            with open(sector, "w", encoding="utf-8") as f:
                f.write("code,name,market,sector_code,sector_name,sector_index_code\n")
            with open(theme, "w", encoding="utf-8") as f:
                f.write("theme_name,code,role\n")

            rc = bootstrap_main(["--validate-only", "--sector-out", sector, "--theme-out", theme, "--fail-on-empty"])

            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
