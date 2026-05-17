from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence


SECTOR_MAP_COLUMNS = ["code", "name", "market", "sector_code", "sector_name", "sector_index_code"]
THEME_MAP_COLUMNS = ["theme_name", "code", "role"]


@dataclass(frozen=True)
class MapValidation:
    path: str
    kind: str
    exists: bool
    header: List[str]
    data_rows: int
    valid_rows: int
    missing_columns: List[str]
    invalid_rows: int = 0

    @property
    def header_only(self) -> bool:
        return self.exists and self.data_rows == 0

    @property
    def empty(self) -> bool:
        return (not self.exists) or self.header_only or self.valid_rows == 0

    @property
    def ok(self) -> bool:
        return self.exists and not self.missing_columns and self.valid_rows > 0

    def status(self) -> str:
        if not self.exists:
            return "missing"
        if self.missing_columns:
            return "missing_columns"
        if self.header_only:
            return "header_only"
        if self.valid_rows == 0:
            return "no_valid_rows"
        if self.invalid_rows:
            return "partial"
        return "ok"

    def message(self) -> str:
        return (
            f"{self.kind}_map status={self.status()} path={self.path} "
            f"data_rows={self.data_rows} valid_rows={self.valid_rows} invalid_rows={self.invalid_rows}"
        )


def normalize_code(code: object) -> str:
    text = str(code or "").strip().lstrip("A")
    return text.zfill(6)[-6:] if text else ""


def validate_sector_map(path: str) -> MapValidation:
    return _validate_csv_map(path, "sector", SECTOR_MAP_COLUMNS, ["code", "sector_code"])


def validate_theme_map(path: str) -> MapValidation:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        exists = os.path.exists(path)
        rows = load_theme_rows(path) if exists else []
        return MapValidation(
            path=path,
            kind="theme",
            exists=exists,
            header=THEME_MAP_COLUMNS if rows else [],
            data_rows=len(rows),
            valid_rows=len(rows),
            missing_columns=[] if exists else list(THEME_MAP_COLUMNS),
            invalid_rows=0,
        )
    return _validate_csv_map(path, "theme", THEME_MAP_COLUMNS, ["theme_name", "code"])


def read_csv_rows(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv_rows(path: str, columns: Sequence[str], rows: Iterable[Dict[str, object]]) -> int:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    count = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in columns})
            count += 1
    return count


def load_sector_rows(path: str) -> List[Dict[str, str]]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        rows = read_csv_rows(path)
    elif ext == ".json":
        with open(path, encoding="utf-8-sig") as f:
            rows = sector_rows_from_json(json.load(f))
    else:
        raise ValueError(f"unsupported sector map extension: {ext or '<none>'}")
    out: List[Dict[str, str]] = []
    for row in rows:
        code = normalize_code(row.get("code", ""))
        sector_code = str(row.get("sector_code", "") or "").strip()
        if not code or not sector_code:
            continue
        out.append(
            {
                "code": code,
                "name": str(row.get("name", "") or "").strip(),
                "market": str(row.get("market", "") or "unknown").strip() or "unknown",
                "sector_code": sector_code,
                "sector_name": str(row.get("sector_name", "") or "").strip(),
                "sector_index_code": str(row.get("sector_index_code", "") or "").strip(),
            }
        )
    return out


def sector_rows_from_json(payload) -> List[Dict[str, str]]:
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    rows: List[Dict[str, str]] = []
    if isinstance(payload, dict):
        for sector_code, members in payload.items():
            sector_name = ""
            sector_index_code = ""
            if isinstance(members, dict):
                sector_name = str(members.get("sector_name", "") or members.get("name", "") or "")
                sector_index_code = str(members.get("sector_index_code", "") or "")
                members = members.get("members", [])
            for item in members or []:
                if isinstance(item, str):
                    rows.append(
                        {
                            "code": item,
                            "sector_code": str(sector_code),
                            "sector_name": sector_name,
                            "sector_index_code": sector_index_code,
                        }
                    )
                elif isinstance(item, dict):
                    row = dict(item)
                    row.setdefault("sector_code", str(sector_code))
                    row.setdefault("sector_name", sector_name)
                    row.setdefault("sector_index_code", sector_index_code)
                    rows.append(row)
    return rows


def load_theme_rows(path: str) -> List[Dict[str, str]]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        rows = read_csv_rows(path)
    elif ext == ".json":
        with open(path, encoding="utf-8-sig") as f:
            rows = theme_rows_from_json(json.load(f))
    else:
        raise ValueError(f"unsupported theme map extension: {ext or '<none>'}")
    out: List[Dict[str, str]] = []
    for row in rows:
        theme_name = str(row.get("theme_name", "") or row.get("theme", "") or "").strip()
        code = normalize_code(row.get("code", ""))
        if not theme_name or not code:
            continue
        out.append({"theme_name": theme_name, "code": code, "role": str(row.get("role", "") or "member").strip() or "member"})
    return out


def theme_rows_from_json(payload) -> List[Dict[str, str]]:
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    rows: List[Dict[str, str]] = []
    if isinstance(payload, dict):
        for theme_name, members in payload.items():
            if isinstance(members, dict):
                members = members.get("members", [])
            for item in members or []:
                if isinstance(item, str):
                    rows.append({"theme_name": str(theme_name), "code": item, "role": "member"})
                elif isinstance(item, dict):
                    row = dict(item)
                    row.setdefault("theme_name", str(theme_name))
                    rows.append(row)
    return rows


def _validate_csv_map(
    path: str,
    kind: str,
    required_columns: Sequence[str],
    required_value_columns: Sequence[str],
) -> MapValidation:
    if not os.path.exists(path):
        return MapValidation(path, kind, False, [], 0, 0, list(required_columns))
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        missing = [column for column in required_columns if column not in header]
        data_rows = 0
        valid_rows = 0
        for row in reader:
            data_rows += 1
            if all(str(row.get(column, "") or "").strip() for column in required_value_columns):
                valid_rows += 1
    return MapValidation(
        path=path,
        kind=kind,
        exists=True,
        header=header,
        data_rows=data_rows,
        valid_rows=valid_rows,
        missing_columns=missing,
        invalid_rows=max(0, data_rows - valid_rows),
    )
