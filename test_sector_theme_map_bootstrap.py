from __future__ import annotations

import csv
import os
import tempfile
import unittest

from sector_state import SectorStateCache
from sector_theme_maps import validate_sector_map, validate_theme_map
from theme_state import ThemeStateCache
from tools.bootstrap_sector_theme_maps import main as bootstrap_main
from tools.fetch_sector_theme_maps import (
    parse_master_stock_info,
    parse_theme_group_list,
    parse_upjong_code_list,
)


class SectorThemeMapValidationTests(unittest.TestCase):
    def test_fetcher_parsers_accept_kiwoom_master_outputs(self):
        groups = parse_theme_group_list("330|화장품;그린카_전기차|245;")
        self.assertEqual(groups, [("330", "화장품"), ("245", "그린카_전기차")])

        upjong = parse_upjong_code_list("001|종합(KOSPI);027|금융업;", "KOSPI")
        self.assertEqual(upjong["금융업"], "KOSPI:027")

        info = parse_master_stock_info("시장구분0|거래소;시장구분1|중형주;업종구분|금융업;")
        self.assertEqual(info["업종구분"], "금융업")

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

    def test_condition_capture_template_prefills_detected_symbols(self):
        with tempfile.TemporaryDirectory() as tmp:
            captures = os.path.join(tmp, "condition_captures.csv")
            sector_template = os.path.join(tmp, "sector_template.csv")
            theme_template = os.path.join(tmp, "theme_template.csv")
            sector_map = os.path.join(tmp, "sector_map.csv")
            theme_map = os.path.join(tmp, "theme_map.csv")
            with open(sector_map, "w", encoding="utf-8") as f:
                f.write("code,name,market,sector_code,sector_name,sector_index_code\n")
            with open(theme_map, "w", encoding="utf-8") as f:
                f.write("theme_name,code,role\n")
            with open(captures, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "detected_at",
                        "symbol",
                        "symbol_name",
                        "code",
                        "name",
                        "condition_name",
                        "symbol_market",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "detected_at": "2026-05-18 09:00:00",
                        "symbol": "A005930",
                        "symbol_name": "Samsung",
                        "condition_name": "quant",
                    }
                )
                writer.writerow(
                    {
                        "detected_at": "2026-05-18 09:01:00",
                        "code": "005930",
                        "name": "Samsung",
                        "condition_name": "dante",
                        "symbol_market": "KOSPI",
                    }
                )
                writer.writerow(
                    {
                        "detected_at": "2026-05-17 09:00:00",
                        "symbol": "000660",
                        "symbol_name": "SK Hynix",
                        "condition_name": "old",
                        "symbol_market": "KOSPI",
                    }
                )

            rc = bootstrap_main(
                [
                    "--template-from-condition-captures",
                    captures,
                    "--template-date",
                    "2026-05-18",
                    "--sector-template-out",
                    sector_template,
                    "--theme-template-out",
                    theme_template,
                    "--sector-out",
                    sector_map,
                    "--theme-out",
                    theme_map,
                    "--fail-on-empty",
                ]
            )

            self.assertEqual(rc, 0)
            with open(sector_template, newline="", encoding="utf-8-sig") as f:
                sector_rows = list(csv.DictReader(f))
            with open(theme_template, newline="", encoding="utf-8-sig") as f:
                theme_rows = list(csv.DictReader(f))
            self.assertEqual(len(sector_rows), 1)
            self.assertEqual(sector_rows[0]["code"], "005930")
            self.assertEqual(sector_rows[0]["market"], "KOSPI")
            self.assertEqual(sector_rows[0]["detected_count"], "2")
            self.assertEqual(sector_rows[0]["condition_names"], "dante;quant")
            self.assertEqual(theme_rows[0]["code"], "005930")
            self.assertEqual(theme_rows[0]["name"], "Samsung")

    def test_fail_on_invalid_source_blocks_partial_template_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            sector_source = os.path.join(tmp, "sector_template.csv")
            theme_source = os.path.join(tmp, "theme_template.csv")
            sector_out = os.path.join(tmp, "sector_map.csv")
            theme_out = os.path.join(tmp, "theme_map.csv")
            with open(sector_source, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "code",
                        "name",
                        "market",
                        "sector_code",
                        "sector_name",
                        "sector_index_code",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "code": "005930",
                        "name": "Samsung",
                        "market": "KOSPI",
                        "sector_code": "101",
                        "sector_name": "Semiconductor",
                    }
                )
                writer.writerow({"code": "000660", "name": "SK Hynix", "market": "KOSPI"})
            with open(theme_source, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["theme_name", "code", "role"])
                writer.writeheader()
                writer.writerow({"theme_name": "AI", "code": "005930", "role": "leader"})
                writer.writerow({"theme_name": "", "code": "000660", "role": "member"})

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
                    "--fail-on-invalid-source",
                ]
            )

            self.assertEqual(rc, 1)
            self.assertFalse(os.path.exists(sector_out))
            self.assertFalse(os.path.exists(theme_out))


if __name__ == "__main__":
    unittest.main()
