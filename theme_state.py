from __future__ import annotations

import csv
import json
import logging
import os
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from sector_theme_maps import MapValidation, validate_theme_map
from market_state import REGIME_NEUTRAL, REGIME_RISK_OFF, REGIME_STRONG, REGIME_UNKNOWN, REGIME_WEAK


logger = logging.getLogger("kiwoom")

THEME_ACTION_ALLOW = "dry_run_allow"
THEME_ACTION_BOOST = "dry_run_boost"
THEME_ACTION_REDUCE_CHASE = "dry_run_reduce_chase"
THEME_ACTION_BLOCK_CHASE_ONLY = "dry_run_block_chase_only"

THEME_FIELDS = [
    "primary_theme",
    "theme_names",
    "theme_regime",
    "theme_member_count",
    "theme_active_count",
    "theme_rising_count",
    "theme_falling_count",
    "theme_avg_return",
    "theme_top_return",
    "theme_top_turnover",
    "theme_leader_code",
    "theme_leader_return",
    "theme_gate_action",
    "theme_gate_reason",
]


@dataclass
class ThemeSnapshot:
    theme_name: str = ""
    theme_regime: str = REGIME_UNKNOWN
    theme_member_count: int = 0
    theme_active_count: int = 0
    theme_rising_count: int = 0
    theme_falling_count: int = 0
    theme_avg_return: Optional[float] = None
    theme_top_return: Optional[float] = None
    theme_top_turnover: int = 0
    theme_leader_code: str = ""
    theme_leader_return: Optional[float] = None
    theme_gate_action: str = THEME_ACTION_ALLOW
    theme_gate_reason: str = ""


@dataclass
class ThemeContext:
    symbol: str = ""
    primary_theme: str = ""
    theme_names: str = ""
    theme_regime: str = REGIME_UNKNOWN
    theme_member_count: int = 0
    theme_active_count: int = 0
    theme_rising_count: int = 0
    theme_falling_count: int = 0
    theme_avg_return: Optional[float] = None
    theme_top_return: Optional[float] = None
    theme_top_turnover: int = 0
    theme_leader_code: str = ""
    theme_leader_return: Optional[float] = None
    theme_gate_action: str = THEME_ACTION_ALLOW
    theme_gate_reason: str = ""

    def as_log_dict(self) -> Dict[str, object]:
        return as_log_dict(self)


class ThemeStateCache:
    def __init__(self, map_path: str = "data/theme_map.csv", min_active_symbols: int = 2) -> None:
        self.map_path = map_path
        self.min_active_symbols = int(min_active_symbols or 2)
        self.symbol_themes: Dict[str, List[Dict[str, str]]] = {}
        self.theme_members: Dict[str, List[Dict[str, str]]] = {}
        self.map_validation: Optional[MapValidation] = None

    @staticmethod
    def normalize_code(code: str) -> str:
        return str(code or "").strip().lstrip("A").zfill(6)[-6:]

    def load_theme_map(self) -> None:
        self.symbol_themes.clear()
        self.theme_members.clear()
        self.map_validation = validate_theme_map(self.map_path)
        if not self.map_validation.ok:
            logger.warning("[theme] %s - theme unknown fallback", self.map_validation.message())
            return
        if not os.path.exists(self.map_path):
            logger.info("[theme] theme map 없음 - theme unknown fallback")
            return
        ext = os.path.splitext(self.map_path)[1].lower()
        rows: List[Dict[str, str]] = []
        if ext == ".csv":
            with open(self.map_path, newline="", encoding="utf-8-sig") as f:
                rows = [dict(row) for row in csv.DictReader(f)]
        elif ext == ".json":
            with open(self.map_path, encoding="utf-8-sig") as f:
                payload = json.load(f)
            rows = self._rows_from_json(payload)
        elif ext in (".yml", ".yaml"):
            try:
                import yaml  # type: ignore
            except ImportError:
                logger.warning("[theme] PyYAML 없음 - yml theme map 스킵")
                return
            with open(self.map_path, encoding="utf-8-sig") as f:
                rows = self._rows_from_json(yaml.safe_load(f) or {})
        for row in rows:
            theme_name = str(row.get("theme_name", "") or row.get("theme", "") or "").strip()
            code = self.normalize_code(row.get("code", ""))
            if not theme_name or not code:
                continue
            item = {"theme_name": theme_name, "code": code, "role": str(row.get("role", "") or "member")}
            self.symbol_themes.setdefault(code, []).append(item)
            self.theme_members.setdefault(theme_name, []).append(item)

    def _rows_from_json(self, payload) -> List[Dict[str, str]]:
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

    def themes_for_symbol(self, code: str) -> List[str]:
        return [item["theme_name"] for item in self.symbol_themes.get(self.normalize_code(code), [])]

    def snapshot_theme(self, theme_name: str, realtime_lookup: Callable[[str], Optional[Dict[str, object]]]) -> ThemeSnapshot:
        members = self.theme_members.get(str(theme_name or ""), [])
        returns: List[float] = []
        top_turnover = 0
        leader_code = ""
        leader_return: Optional[float] = None
        for item in members:
            data = realtime_lookup(item["code"]) if realtime_lookup else None
            if not data:
                continue
            ret = data.get("return_pct")
            if ret is None:
                continue
            ret_f = float(ret)
            returns.append(ret_f)
            turnover = int(data.get("turnover", 0) or 0)
            if turnover > top_turnover:
                top_turnover = turnover
                leader_code = item["code"]
                leader_return = ret_f
        active = len(returns)
        rising = len([v for v in returns if v > 0])
        falling = len([v for v in returns if v < 0])
        avg_return = (sum(returns) / active) if active else None
        top_return = max(returns) if returns else None
        regime = REGIME_UNKNOWN
        if active >= self.min_active_symbols and avg_return is not None:
            rising_ratio = rising / active if active else 0.0
            falling_ratio = falling / active if active else 0.0
            if avg_return <= -0.02 and falling_ratio >= 0.7:
                regime = REGIME_RISK_OFF
            elif avg_return >= 0.01 and rising_ratio >= 0.6:
                regime = REGIME_STRONG
            elif avg_return <= -0.01 and rising_ratio <= 0.3:
                regime = REGIME_WEAK
            else:
                regime = REGIME_NEUTRAL
        return self._with_gate(
            ThemeSnapshot(
                theme_name=theme_name,
                theme_regime=regime,
                theme_member_count=len(members),
                theme_active_count=active,
                theme_rising_count=rising,
                theme_falling_count=falling,
                theme_avg_return=avg_return,
                theme_top_return=top_return,
                theme_top_turnover=top_turnover,
                theme_leader_code=leader_code,
                theme_leader_return=leader_return,
            )
        )

    def snapshot_for_symbol(self, code: str, realtime_lookup: Callable[[str], Optional[Dict[str, object]]]) -> ThemeContext:
        normalized = self.normalize_code(code)
        themes = self.themes_for_symbol(normalized)
        if not themes:
            return ThemeContext(
                symbol=normalized,
                theme_gate_action=THEME_ACTION_ALLOW,
                theme_gate_reason="THEME_UNKNOWN_FALLBACK",
            )
        snapshots = [self.snapshot_theme(theme, realtime_lookup) for theme in themes]
        primary = sorted(
            snapshots,
            key=lambda s: (
                s.theme_regime == REGIME_STRONG,
                s.theme_active_count,
                s.theme_avg_return if s.theme_avg_return is not None else -999.0,
            ),
            reverse=True,
        )[0]
        return ThemeContext(
            symbol=normalized,
            primary_theme=primary.theme_name,
            theme_names=";".join(themes),
            theme_regime=primary.theme_regime,
            theme_member_count=primary.theme_member_count,
            theme_active_count=primary.theme_active_count,
            theme_rising_count=primary.theme_rising_count,
            theme_falling_count=primary.theme_falling_count,
            theme_avg_return=primary.theme_avg_return,
            theme_top_return=primary.theme_top_return,
            theme_top_turnover=primary.theme_top_turnover,
            theme_leader_code=primary.theme_leader_code,
            theme_leader_return=primary.theme_leader_return,
            theme_gate_action=primary.theme_gate_action,
            theme_gate_reason=primary.theme_gate_reason,
        )

    @staticmethod
    def _with_gate(snapshot: ThemeSnapshot) -> ThemeSnapshot:
        if snapshot.theme_regime == REGIME_STRONG:
            snapshot.theme_gate_action = THEME_ACTION_BOOST
            snapshot.theme_gate_reason = "THEME_STRONG"
        elif snapshot.theme_regime == REGIME_NEUTRAL:
            snapshot.theme_gate_action = THEME_ACTION_ALLOW
            snapshot.theme_gate_reason = ""
        elif snapshot.theme_regime == REGIME_WEAK:
            snapshot.theme_gate_action = THEME_ACTION_REDUCE_CHASE
            snapshot.theme_gate_reason = "THEME_WEAK"
        elif snapshot.theme_regime == REGIME_RISK_OFF:
            snapshot.theme_gate_action = THEME_ACTION_BLOCK_CHASE_ONLY
            snapshot.theme_gate_reason = "THEME_RISK_OFF"
        else:
            snapshot.theme_regime = REGIME_UNKNOWN
            snapshot.theme_gate_action = THEME_ACTION_ALLOW
            snapshot.theme_gate_reason = "THEME_UNKNOWN_FALLBACK"
        return snapshot

    def as_log_dict(self, context: ThemeContext) -> Dict[str, object]:
        return as_log_dict(context)


def as_log_dict(context: ThemeContext) -> Dict[str, object]:
    if context is None:
        context = ThemeContext()
    out = {}
    for field in THEME_FIELDS:
        value = getattr(context, field, "")
        out[field] = "" if value is None else value
    return out
