from __future__ import annotations

import argparse
import os
import re
import sys
import time
from typing import Dict, Iterable, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sector_theme_maps import (  # noqa: E402
    SECTOR_MAP_COLUMNS,
    THEME_MAP_COLUMNS,
    normalize_code,
    validate_sector_map,
    validate_theme_map,
    write_csv_rows,
)


DEFAULT_SECTOR_OUT = os.path.join("data", "sector_map.csv")
DEFAULT_THEME_OUT = os.path.join("data", "theme_map.csv")
CALL_INTERVAL_SECONDS = 0.02

MARKET_CODES = (("0", "KOSPI"), ("10", "KOSDAQ"))
UPJONG_MARKETS = (("0", "KOSPI"), ("1", "KOSDAQ"))

_QAPP_REF = None


def _split_records(raw: object) -> List[str]:
    return [part.strip() for part in str(raw or "").split(";") if part and part.strip()]


def _split_fields(record: str) -> List[str]:
    fields = re.split(r"[\|\^\t,]", record)
    return [field.strip() for field in fields if field and field.strip()]


def _safe_key(value: str) -> str:
    text = re.sub(r"\s+", "_", str(value or "").strip())
    text = re.sub(r"[^0-9A-Za-z가-힣_]+", "", text)
    return text or "unknown"


def parse_theme_group_list(raw: object) -> List[Tuple[str, str]]:
    """Parse Kiwoom theme groups into ``[(theme_code, theme_name), ...]``.

    Kiwoom wrappers commonly expose either ``code|name`` or ``name|code`` records.
    The parser accepts both so the CLI remains usable across OpenAPI wrappers.
    """
    groups: List[Tuple[str, str]] = []
    for record in _split_records(raw):
        fields = _split_fields(record)
        if len(fields) < 2:
            continue
        numeric = [field for field in fields if field.isdigit()]
        if numeric:
            theme_code = numeric[0]
            theme_name = next((field for field in fields if field != theme_code), "")
        else:
            theme_code, theme_name = fields[0], fields[1]
        if theme_code and theme_name:
            groups.append((theme_code, theme_name))
    return groups


def parse_upjong_code_list(raw: object, market_name: str) -> Dict[str, str]:
    """Return ``sector_name -> sector_index_code`` from KOA GetUpjongCode output."""
    mapping: Dict[str, str] = {}
    for record in _split_records(raw):
        fields = _split_fields(record)
        if len(fields) < 2:
            continue
        code = next((field for field in fields if field.isdigit()), fields[0])
        name = next((field for field in fields if field != code), "")
        if name:
            mapping.setdefault(name, f"{market_name}:{code}")
    return mapping


def parse_master_stock_info(raw: object) -> Dict[str, str]:
    """Parse ``KOA_Functions('GetMasterStockInfo', code)`` key/value output."""
    info: Dict[str, str] = {}
    for record in _split_records(raw):
        if "|" in record:
            key, value = record.split("|", 1)
        elif "^" in record:
            key, value = record.split("^", 1)
        else:
            continue
        key = key.strip()
        value = value.strip()
        if key:
            info[key] = value
    return info


def _market_codes_from_rows(rows: Iterable[Dict[str, str]]) -> Dict[str, str]:
    return {row["code"]: row.get("market", "") for row in rows if row.get("code")}


class KiwoomSectorThemeFetcher:
    def __init__(self):
        from PyQt5.QAxContainer import QAxWidget  # noqa: WPS433
        from PyQt5.QtCore import QEventLoop

        self.widget = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.login_loop = QEventLoop()
        self.last_call_at = 0.0
        self.widget.OnEventConnect.connect(self._on_event_connect)

    def login(self) -> None:
        self.widget.dynamicCall("CommConnect()")
        self.login_loop.exec_()

    def _on_event_connect(self, err_code):
        if err_code != 0:
            print(f"[fetch_sector_theme_maps] Kiwoom login failed: {err_code}", file=sys.stderr)
        self.login_loop.exit()

    def _throttle(self) -> None:
        elapsed = time.time() - self.last_call_at
        if elapsed < CALL_INTERVAL_SECONDS:
            time.sleep(CALL_INTERVAL_SECONDS - elapsed)
        self.last_call_at = time.time()

    def call(self, signature: str, *args):
        self._throttle()
        return self.widget.dynamicCall(signature, *args)

    def koa(self, function_name: str, argument: str):
        return self.call("KOA_Functions(QString, QString)", function_name, argument)

    def listed_codes(self) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        seen: set[str] = set()
        for market_code, market_name in MARKET_CODES:
            raw = self.call("GetCodeListByMarket(QString)", market_code)
            for code in _split_records(raw):
                normalized = normalize_code(code)
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)
                name = str(self.call("GetMasterCodeName(QString)", normalized) or "").strip()
                rows.append({"code": normalized, "name": name, "market": market_name})
        return rows

    def upjong_index_by_name(self) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        for upjong_market, market_name in UPJONG_MARKETS:
            raw = self.koa("GetUpjongCode", upjong_market)
            mapping.update(parse_upjong_code_list(raw, market_name))
        return mapping

    def sector_rows(self) -> List[Dict[str, str]]:
        listed = self.listed_codes()
        upjong = self.upjong_index_by_name()
        rows: List[Dict[str, str]] = []
        for item in listed:
            raw_info = self.koa("GetMasterStockInfo", item["code"])
            info = parse_master_stock_info(raw_info)
            sector_name = info.get("업종구분", "") or info.get("업종", "") or "unknown"
            sector_code = _safe_key(sector_name)
            sector_index_code = upjong.get(sector_name, f"{item['market']}:{sector_code}")
            rows.append(
                {
                    "code": item["code"],
                    "name": item["name"],
                    "market": item["market"],
                    "sector_code": sector_code,
                    "sector_name": sector_name,
                    "sector_index_code": sector_index_code,
                }
            )
        return rows

    def theme_rows(self, market_by_code: Dict[str, str] | None = None) -> List[Dict[str, str]]:
        market_by_code = market_by_code or {}
        groups = parse_theme_group_list(self.call("GetThemeGroupList(int)", 1))
        rows: List[Dict[str, str]] = []
        seen: set[Tuple[str, str]] = set()
        for theme_code, theme_name in groups:
            raw_codes = self.call("GetThemeGroupCode(QString)", theme_code)
            codes = [normalize_code(code) for code in _split_records(raw_codes)]
            codes = [code for code in codes if code]
            for index, code in enumerate(codes):
                key = (theme_name, code)
                if key in seen:
                    continue
                seen.add(key)
                role = "leader" if index == 0 else "member"
                rows.append({"theme_name": theme_name, "code": code, "role": role})
        return rows


def fetch_maps() -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    global _QAPP_REF
    from PyQt5.QtWidgets import QApplication  # noqa: WPS433

    app = QApplication.instance() or QApplication(sys.argv)
    _QAPP_REF = app
    fetcher = KiwoomSectorThemeFetcher()
    fetcher.login()
    sector_rows = fetcher.sector_rows()
    theme_rows = fetcher.theme_rows(_market_codes_from_rows(sector_rows))
    return sector_rows, theme_rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch sector/theme maps from Kiwoom OpenAPI. This tool never calls order APIs."
    )
    parser.add_argument("--sector-out", default=DEFAULT_SECTOR_OUT)
    parser.add_argument("--theme-out", default=DEFAULT_THEME_OUT)
    parser.add_argument("--sector-only", action="store_true", help="Write only sector_map.csv")
    parser.add_argument("--theme-only", action="store_true", help="Write only theme_map.csv")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and print counts without writing files")
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.sector_only and args.theme_only:
        print("--sector-only and --theme-only cannot be used together", file=sys.stderr)
        return 2

    sector_rows, theme_rows = fetch_maps()
    if args.sector_only:
        theme_rows = []
    if args.theme_only:
        sector_rows = []

    print(f"fetched sector_rows={len(sector_rows)} theme_rows={len(theme_rows)}")
    if args.dry_run:
        return 0

    if not args.theme_only:
        write_csv_rows(args.sector_out, SECTOR_MAP_COLUMNS, sector_rows)
        print(validate_sector_map(args.sector_out).message())
    if not args.sector_only:
        write_csv_rows(args.theme_out, THEME_MAP_COLUMNS, theme_rows)
        print(validate_theme_map(args.theme_out).message())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
