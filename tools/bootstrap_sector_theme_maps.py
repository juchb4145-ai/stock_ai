from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sector_theme_maps import (  # noqa: E402
    SECTOR_MAP_COLUMNS,
    THEME_MAP_COLUMNS,
    load_sector_rows,
    load_theme_rows,
    normalize_code,
    validate_sector_map,
    validate_theme_map,
    write_csv_rows,
)


DEFAULT_SECTOR_MAP = os.path.join("data", "sector_map.csv")
DEFAULT_THEME_MAP = os.path.join("data", "theme_map.csv")
DEFAULT_TEMPLATE_DIR = os.path.join("reports", "sector_theme_templates")
TEMPLATE_META_COLUMNS = [
    "first_detected_at",
    "last_detected_at",
    "detected_count",
    "condition_names",
]
SECTOR_TEMPLATE_COLUMNS = SECTOR_MAP_COLUMNS + TEMPLATE_META_COLUMNS
THEME_TEMPLATE_COLUMNS = THEME_MAP_COLUMNS + ["name", "market"] + TEMPLATE_META_COLUMNS


def _print_validation(path: str, kind: str) -> bool:
    report = validate_sector_map(path) if kind == "sector" else validate_theme_map(path)
    print(report.message())
    if report.missing_columns:
        print(f"{kind}_map missing_columns={','.join(report.missing_columns)}")
    return report.ok


def _validate_source_before_write(path: str, kind: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        rows = load_sector_rows(path) if kind == "sector" else load_theme_rows(path)
        status = "ok" if rows else "no_valid_rows"
        print(f"{kind}_source status={status} path={path} valid_rows={len(rows)}")
        return bool(rows)
    report = validate_sector_map(path) if kind == "sector" else validate_theme_map(path)
    print(
        f"{kind}_source status={report.status()} path={report.path} "
        f"data_rows={report.data_rows} valid_rows={report.valid_rows} invalid_rows={report.invalid_rows}"
    )
    if report.missing_columns:
        print(f"{kind}_source missing_columns={','.join(report.missing_columns)}")
    if report.invalid_rows:
        print(f"{kind}_source invalid_rows={report.invalid_rows}")
    return report.ok and report.invalid_rows == 0


def _default_template_path(kind: str, target_date: str | None) -> str:
    prefix = target_date.replace("-", "") if target_date else "all"
    return os.path.join(DEFAULT_TEMPLATE_DIR, f"{prefix}_{kind}_map_template.csv")


def _row_matches_date(row: Dict[str, str], target_date: str | None) -> bool:
    if not target_date:
        return True
    for key in ("detected_at", "created_at", "captured_at", "logged_at"):
        value = str(row.get(key, "") or "").strip()
        if value.startswith(target_date):
            return True
    return False


def _condition_capture_time(row: Dict[str, str]) -> str:
    for key in ("detected_at", "created_at", "captured_at", "logged_at"):
        value = str(row.get(key, "") or "").strip()
        if value:
            return value
    return ""


def _read_condition_capture_symbols(path: str, target_date: str | None = None) -> List[Dict[str, object]]:
    symbols: Dict[str, Dict[str, object]] = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if not _row_matches_date(row, target_date):
                continue
            code = normalize_code(row.get("symbol") or row.get("code"))
            if not code:
                continue
            detected_at = _condition_capture_time(row)
            record = symbols.setdefault(
                code,
                {
                    "code": code,
                    "name": "",
                    "market": "",
                    "first_detected_at": detected_at,
                    "last_detected_at": detected_at,
                    "detected_count": 0,
                    "condition_names": set(),
                },
            )
            name = str(row.get("symbol_name") or row.get("name") or "").strip()
            market = str(row.get("symbol_market") or row.get("market") or "").strip()
            condition_name = str(row.get("condition_name") or row.get("primary_condition_name") or "").strip()
            if name and not record["name"]:
                record["name"] = name
            if market and not record["market"]:
                record["market"] = market
            if detected_at:
                first = str(record.get("first_detected_at") or "")
                last = str(record.get("last_detected_at") or "")
                record["first_detected_at"] = min(first, detected_at) if first else detected_at
                record["last_detected_at"] = max(last, detected_at) if last else detected_at
            record["detected_count"] = int(record["detected_count"]) + 1
            if condition_name:
                record["condition_names"].add(condition_name)
    out: List[Dict[str, object]] = []
    for record in symbols.values():
        conditions = sorted(record.pop("condition_names"))
        record["condition_names"] = ";".join(conditions)
        out.append(record)
    return sorted(out, key=lambda item: str(item.get("code", "")))


def _existing_sector_rows(path: str) -> Dict[str, Dict[str, str]]:
    try:
        return {row["code"]: row for row in load_sector_rows(path)}
    except (FileNotFoundError, ValueError):
        return {}


def _existing_theme_rows(path: str) -> Dict[str, List[Dict[str, str]]]:
    out: Dict[str, List[Dict[str, str]]] = {}
    try:
        rows = load_theme_rows(path)
    except (FileNotFoundError, ValueError):
        return out
    for row in rows:
        out.setdefault(row["code"], []).append(row)
    return out


def write_condition_capture_templates(
    *,
    condition_capture_path: str,
    target_date: str | None,
    sector_template_out: str,
    theme_template_out: str,
    existing_sector_map: str,
    existing_theme_map: str,
) -> Dict[str, int]:
    symbols = _read_condition_capture_symbols(condition_capture_path, target_date)
    existing_sectors = _existing_sector_rows(existing_sector_map)
    existing_themes = _existing_theme_rows(existing_theme_map)
    sector_rows = []
    theme_rows = []
    known_market_count = 0
    for symbol in symbols:
        code = str(symbol.get("code") or "")
        existing_sector = existing_sectors.get(code, {})
        market = str(existing_sector.get("market") or symbol.get("market") or "")
        if market:
            known_market_count += 1
        sector_rows.append(
            {
                **symbol,
                "market": market,
                "sector_code": existing_sector.get("sector_code", ""),
                "sector_name": existing_sector.get("sector_name", ""),
                "sector_index_code": existing_sector.get("sector_index_code", ""),
            }
        )
        themes = existing_themes.get(code) or [{"theme_name": "", "code": code, "role": ""}]
        for theme in themes:
            theme_rows.append(
                {
                    "theme_name": theme.get("theme_name", ""),
                    "code": code,
                    "role": theme.get("role", ""),
                    "name": symbol.get("name", ""),
                    "market": market,
                    "first_detected_at": symbol.get("first_detected_at", ""),
                    "last_detected_at": symbol.get("last_detected_at", ""),
                    "detected_count": symbol.get("detected_count", 0),
                    "condition_names": symbol.get("condition_names", ""),
                }
            )
    sector_count = write_csv_rows(sector_template_out, SECTOR_TEMPLATE_COLUMNS, sector_rows)
    theme_count = write_csv_rows(theme_template_out, THEME_TEMPLATE_COLUMNS, theme_rows)
    return {
        "symbols": len(symbols),
        "known_market": known_market_count,
        "missing_market": len(symbols) - known_market_count,
        "sector_rows": sector_count,
        "theme_rows": theme_count,
    }


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
    parser.add_argument("--template-from-condition-captures", help="Write fill-in templates from condition_captures.csv")
    parser.add_argument("--template-date", help="Only include symbols detected on YYYY-MM-DD when writing templates")
    parser.add_argument("--sector-template-out", help="Output path for sector fill-in template")
    parser.add_argument("--theme-template-out", help="Output path for theme fill-in template")
    parser.add_argument(
        "--fail-on-invalid-source",
        action="store_true",
        help="Before writing output maps, fail if a CSV source has missing columns, no valid rows, or invalid rows.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.validate_only:
        sector_ok = _print_validation(args.sector_out, "sector")
        theme_ok = _print_validation(args.theme_out, "theme")
        return 1 if args.fail_on_empty and not (sector_ok and theme_ok) else 0

    if args.template_from_condition_captures:
        sector_template_out = args.sector_template_out or _default_template_path("sector", args.template_date)
        theme_template_out = args.theme_template_out or _default_template_path("theme", args.template_date)
        stats = write_condition_capture_templates(
            condition_capture_path=args.template_from_condition_captures,
            target_date=args.template_date,
            sector_template_out=sector_template_out,
            theme_template_out=theme_template_out,
            existing_sector_map=args.sector_out,
            existing_theme_map=args.theme_out,
        )
        print(
            "wrote sector/theme templates "
            f"symbols={stats['symbols']} known_market={stats['known_market']} "
            f"missing_market={stats['missing_market']}"
        )
        print(f"  sector_template: {sector_template_out} rows={stats['sector_rows']}")
        print(f"  theme_template: {theme_template_out} rows={stats['theme_rows']}")
        return 1 if args.fail_on_empty and stats["symbols"] == 0 else 0

    if args.fail_on_invalid_source:
        source_ok = True
        if args.sector_source:
            source_ok = _validate_source_before_write(args.sector_source, "sector") and source_ok
        if args.theme_source:
            source_ok = _validate_source_before_write(args.theme_source, "theme") and source_ok
        if not source_ok:
            return 1

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
