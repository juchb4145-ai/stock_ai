from __future__ import annotations

import argparse
import os
import sys
from typing import List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sector_theme_maps import (  # noqa: E402
    SECTOR_MAP_COLUMNS,
    THEME_MAP_COLUMNS,
    load_sector_rows,
    load_theme_rows,
    validate_sector_map,
    validate_theme_map,
    write_csv_rows,
)


DEFAULT_SECTOR_MAP = os.path.join("data", "sector_map.csv")
DEFAULT_THEME_MAP = os.path.join("data", "theme_map.csv")


def _print_validation(path: str, kind: str) -> bool:
    report = validate_sector_map(path) if kind == "sector" else validate_theme_map(path)
    print(report.message())
    if report.missing_columns:
        print(f"{kind}_map missing_columns={','.join(report.missing_columns)}")
    return report.ok


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Bootstrap or validate sector/theme maps. Kiwoom network/COM fetch is intentionally "
            "not performed here; export Kiwoom/local data to the documented CSV/JSON shape first."
        )
    )
    parser.add_argument("--sector-source", help="Input CSV/JSON with code,name,market,sector_code,sector_name,sector_index_code")
    parser.add_argument("--theme-source", help="Input CSV/JSON with theme_name,code,role or {theme:[codes...]}")
    parser.add_argument("--sector-out", default=DEFAULT_SECTOR_MAP)
    parser.add_argument("--theme-out", default=DEFAULT_THEME_MAP)
    parser.add_argument("--validate-only", action="store_true", help="Only validate output paths; do not write")
    parser.add_argument("--fail-on-empty", action="store_true", help="Exit non-zero if a map is missing/header-only/no-valid-rows")
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.validate_only:
        sector_ok = _print_validation(args.sector_out, "sector")
        theme_ok = _print_validation(args.theme_out, "theme")
        return 1 if args.fail_on_empty and not (sector_ok and theme_ok) else 0

    wrote_any = False
    if args.sector_source:
        rows = load_sector_rows(args.sector_source)
        count = write_csv_rows(args.sector_out, SECTOR_MAP_COLUMNS, rows)
        print(f"wrote sector_map path={args.sector_out} rows={count} source={args.sector_source}")
        wrote_any = True
    if args.theme_source:
        rows = load_theme_rows(args.theme_source)
        count = write_csv_rows(args.theme_out, THEME_MAP_COLUMNS, rows)
        print(f"wrote theme_map path={args.theme_out} rows={count} source={args.theme_source}")
        wrote_any = True

    if not wrote_any:
        print("nothing to write: pass --sector-source and/or --theme-source, or use --validate-only")
        return 2

    sector_ok = _print_validation(args.sector_out, "sector")
    theme_ok = _print_validation(args.theme_out, "theme")
    return 1 if args.fail_on_empty and not (sector_ok and theme_ok) else 0


if __name__ == "__main__":
    raise SystemExit(main())
