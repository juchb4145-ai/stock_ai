from __future__ import annotations

import csv
import os
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple, Union

from candidate_registry import CONDITION_COMBO_META_FIELDS, LEADER_META_FIELDS
from trade_config import TRADE_CONFIG


CONDITION_CAPTURE_CSV = os.path.join("data", "condition_captures.csv")

CONDITION_CAPTURE_FIELDS = [
    "logged_at",
    "event",
    "source_event",
    "created_at",
    "candidate_id",
    "symbol",
    "symbol_name",
    "detected_at",
    "captured_at",
    "captured_time",
    "code",
    "name",
    "condition_name",
    *CONDITION_COMBO_META_FIELDS,
    *LEADER_META_FIELDS,
    "symbol_market",
    "sector_code",
    "sector_name",
    "sector_index_code",
    "primary_theme",
    "theme_names",
    "strategy_name",
    "condition_formula",
    "condition_formula_version",
    "condition_index",
    "event_type",
    "screen_no",
    "capture_price",
    "entry_trigger_price",
    "chejan_strength",
    "accum_volume",
    "signal_source",
    "source",
    "candidate_role",
    "time_policy_reason",
    "entry_allowed",
    "capture_allowed",
    "manage_allowed",
    "analysis_allowed",
]


def _now_strings(now: Optional[float] = None) -> Tuple[str, str]:
    ts = now if now is not None else time.time()
    local = time.localtime(ts)
    return (
        time.strftime("%Y-%m-%d %H:%M:%S", local),
        time.strftime("%H%M%S", local),
    )


@dataclass(frozen=True)
class ConditionCaptureEvent:
    event: str
    code: str
    candidate_id: str = ""
    symbol: str = ""
    symbol_name: str = ""
    name: str = ""
    condition_name: str = ""
    primary_condition_name: str = ""
    bonus_condition_name: str = ""
    quant_detected: Union[bool, str, None] = ""
    dante_detected: Union[bool, str, None] = ""
    condition_combo: str = ""
    condition_score_bonus: Union[float, str, None] = ""
    first_condition_name: str = ""
    last_condition_name: str = ""
    first_condition_detected_at: Union[float, str, None] = ""
    bonus_condition_detected_at: Union[float, str, None] = ""
    time_between_conditions_sec: Union[float, str, None] = ""
    trade_value_since_capture: Union[int, float, str, None] = ""
    turnover_speed_per_min: Union[float, str, None] = ""
    volume_ratio_1m: Union[float, str, None] = ""
    volume_ratio_5m: Union[float, str, None] = ""
    turnover_rank_market: Union[int, str, None] = ""
    turnover_rank_sector: Union[int, str, None] = ""
    leader_score: Union[float, str, None] = ""
    symbol_market: str = ""
    sector_code: str = ""
    sector_name: str = ""
    sector_index_code: str = ""
    primary_theme: str = ""
    theme_names: str = ""
    strategy_name: str = ""
    condition_formula: str = ""
    condition_formula_version: str = ""
    condition_index: Union[str, int] = ""
    event_type: str = ""
    screen_no: str = ""
    capture_price: Union[int, str, None] = ""
    entry_trigger_price: Union[int, str, None] = ""
    chejan_strength: Union[float, str, None] = ""
    accum_volume: Union[int, str, None] = ""
    signal_source: str = TRADE_CONFIG.signal_source
    source: str = "kiwoom"
    candidate_role: str = "trading"
    time_policy_reason: str = ""
    entry_allowed: Union[bool, str, None] = ""
    capture_allowed: Union[bool, str, None] = ""
    manage_allowed: Union[bool, str, None] = ""
    analysis_allowed: Union[bool, str, None] = ""
    source_event: str = ""
    logged_at: str = ""
    created_at: str = ""
    detected_at: str = ""
    captured_at: str = ""
    captured_time: str = ""

    def to_row(self) -> Dict[str, object]:
        logged_at = self.logged_at
        created_at = self.created_at
        captured_at = self.captured_at
        captured_time = self.captured_time
        if not logged_at or not created_at or not captured_at or not captured_time:
            now_at, now_time = _now_strings()
            logged_at = logged_at or now_at
            created_at = created_at or now_at
            captured_at = captured_at or now_at
            captured_time = captured_time or now_time

        return {
            "logged_at": logged_at,
            "event": self.event,
            "source_event": self.source_event or self.event,
            "created_at": created_at,
            "candidate_id": self.candidate_id,
            "symbol": self.symbol or self.code,
            "symbol_name": self.symbol_name or self.name,
            "detected_at": self.detected_at or captured_at,
            "captured_at": captured_at,
            "captured_time": captured_time,
            "code": self.code,
            "name": self.name,
            "condition_name": self.condition_name,
            "primary_condition_name": (
                self.primary_condition_name
                or getattr(TRADE_CONFIG, "primary_condition_name", TRADE_CONFIG.condition_name)
            ),
            "bonus_condition_name": (
                self.bonus_condition_name
                or getattr(TRADE_CONFIG, "bonus_condition_name", TRADE_CONFIG.legacy_condition_name)
            ),
            "quant_detected": self.quant_detected,
            "dante_detected": self.dante_detected,
            "condition_combo": self.condition_combo,
            "condition_score_bonus": self.condition_score_bonus,
            "first_condition_name": self.first_condition_name,
            "last_condition_name": self.last_condition_name,
            "first_condition_detected_at": self.first_condition_detected_at,
            "bonus_condition_detected_at": self.bonus_condition_detected_at,
            "time_between_conditions_sec": self.time_between_conditions_sec,
            "trade_value_since_capture": self.trade_value_since_capture,
            "turnover_speed_per_min": self.turnover_speed_per_min,
            "volume_ratio_1m": self.volume_ratio_1m,
            "volume_ratio_5m": self.volume_ratio_5m,
            "turnover_rank_market": self.turnover_rank_market,
            "turnover_rank_sector": self.turnover_rank_sector,
            "leader_score": self.leader_score,
            "symbol_market": self.symbol_market,
            "sector_code": self.sector_code,
            "sector_name": self.sector_name,
            "sector_index_code": self.sector_index_code,
            "primary_theme": self.primary_theme,
            "theme_names": self.theme_names,
            "strategy_name": self.strategy_name or TRADE_CONFIG.strategy_name,
            "condition_formula": self.condition_formula or TRADE_CONFIG.condition_formula,
            "condition_formula_version": (
                self.condition_formula_version or TRADE_CONFIG.condition_formula_version
            ),
            "condition_index": self.condition_index,
            "event_type": self.event_type,
            "screen_no": self.screen_no,
            "capture_price": self.capture_price,
            "entry_trigger_price": self.entry_trigger_price,
            "chejan_strength": self.chejan_strength,
            "accum_volume": self.accum_volume,
            "signal_source": self.signal_source,
            "source": self.source,
            "candidate_role": self.candidate_role,
            "time_policy_reason": self.time_policy_reason,
            "entry_allowed": self.entry_allowed,
            "capture_allowed": self.capture_allowed,
            "manage_allowed": self.manage_allowed,
            "analysis_allowed": self.analysis_allowed,
        }


class ConditionCaptureLogger:
    """Append-only CSV logger for condition detections and first capture prices."""

    def __init__(self, path: str = CONDITION_CAPTURE_CSV):
        self.path = path

    def _ensure_schema(self) -> bool:
        if not os.path.exists(self.path) or os.path.getsize(self.path) <= 0:
            return False
        with open(self.path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            existing_fields = reader.fieldnames or []
            if existing_fields == CONDITION_CAPTURE_FIELDS:
                return True
            rows = list(reader)
        backup_path = "{}.bak_{}".format(self.path, time.strftime("%Y%m%d%H%M%S"))
        os.replace(self.path, backup_path)
        with open(self.path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CONDITION_CAPTURE_FIELDS)
            writer.writeheader()
            for old_row in rows:
                row = {field: old_row.get(field, "") for field in CONDITION_CAPTURE_FIELDS}
                row["source_event"] = row.get("source_event") or old_row.get("event", "")
                row["created_at"] = row.get("created_at") or old_row.get("logged_at", "")
                row["symbol"] = row.get("symbol") or old_row.get("code", "")
                row["symbol_name"] = row.get("symbol_name") or old_row.get("name", "")
                row["strategy_name"] = row.get("strategy_name") or TRADE_CONFIG.strategy_name
                writer.writerow(row)
        return True

    def append(self, event: ConditionCaptureEvent) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        file_exists = self._ensure_schema()
        with open(self.path, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CONDITION_CAPTURE_FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(event.to_row())

    def append_detection(
        self,
        *,
        code: str,
        candidate_id: str = "",
        name: str = "",
        condition_name: str = "",
        strategy_name: str = "",
        condition_index: Union[str, int] = "",
        event_type: str = "",
        screen_no: str = "",
        signal_source: str = "",
        detected_at: str = "",
        candidate_role: str = "trading",
        time_policy_reason: str = "",
        entry_allowed: Union[bool, str, None] = "",
        capture_allowed: Union[bool, str, None] = "",
        manage_allowed: Union[bool, str, None] = "",
        analysis_allowed: Union[bool, str, None] = "",
        condition_meta: Optional[Dict[str, object]] = None,
    ) -> None:
        condition_meta = dict(condition_meta or {})
        self.append(
            ConditionCaptureEvent(
                event="condition_detected",
                code=code,
                candidate_id=candidate_id,
                name=name,
                condition_name=condition_name,
                strategy_name=strategy_name,
                condition_index=condition_index,
                event_type=event_type,
                screen_no=screen_no,
                signal_source=signal_source or TRADE_CONFIG.signal_source,
                detected_at=detected_at,
                candidate_role=candidate_role,
                time_policy_reason=time_policy_reason,
                entry_allowed=entry_allowed,
                capture_allowed=capture_allowed,
                manage_allowed=manage_allowed,
                analysis_allowed=analysis_allowed,
                **{
                    key: condition_meta.get(key, "")
                    for key in (
                        *CONDITION_COMBO_META_FIELDS,
                        *LEADER_META_FIELDS,
                        "symbol_market",
                        "sector_code",
                        "sector_name",
                        "sector_index_code",
                        "primary_theme",
                        "theme_names",
                    )
                },
            )
        )

    def append_capture_price(
        self,
        *,
        code: str,
        candidate_id: str = "",
        name: str = "",
        condition_name: str = "",
        strategy_name: str = "",
        condition_index: Union[str, int] = "",
        event_type: str = "",
        screen_no: str = "",
        capture_price: int = 0,
        entry_trigger_price: int = 0,
        chejan_strength: float = 0.0,
        accum_volume: int = 0,
        signal_source: str = "",
        detected_at: str = "",
        candidate_role: str = "trading",
        time_policy_reason: str = "",
        entry_allowed: Union[bool, str, None] = "",
        capture_allowed: Union[bool, str, None] = "",
        manage_allowed: Union[bool, str, None] = "",
        analysis_allowed: Union[bool, str, None] = "",
        condition_meta: Optional[Dict[str, object]] = None,
    ) -> None:
        condition_meta = dict(condition_meta or {})
        self.append(
            ConditionCaptureEvent(
                event="capture_price",
                code=code,
                candidate_id=candidate_id,
                name=name,
                condition_name=condition_name,
                strategy_name=strategy_name,
                condition_index=condition_index,
                event_type=event_type,
                screen_no=screen_no,
                capture_price=capture_price,
                entry_trigger_price=entry_trigger_price,
                chejan_strength=chejan_strength,
                accum_volume=accum_volume,
                signal_source=signal_source or TRADE_CONFIG.signal_source,
                detected_at=detected_at,
                candidate_role=candidate_role,
                time_policy_reason=time_policy_reason,
                entry_allowed=entry_allowed,
                capture_allowed=capture_allowed,
                manage_allowed=manage_allowed,
                analysis_allowed=analysis_allowed,
                **{
                    key: condition_meta.get(key, "")
                    for key in (
                        *CONDITION_COMBO_META_FIELDS,
                        *LEADER_META_FIELDS,
                        "symbol_market",
                        "sector_code",
                        "sector_name",
                        "sector_index_code",
                        "primary_theme",
                        "theme_names",
                    )
                },
            )
        )


def read_condition_captures(path: str = CONDITION_CAPTURE_CSV) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for field in (
            *CONDITION_COMBO_META_FIELDS,
            *LEADER_META_FIELDS,
            "symbol_market",
            "sector_code",
            "sector_name",
            "sector_index_code",
            "primary_theme",
            "theme_names",
        ):
            row.setdefault(field, "")
        if not row.get("primary_condition_name"):
            row["primary_condition_name"] = getattr(
                TRADE_CONFIG,
                "primary_condition_name",
                TRADE_CONFIG.condition_name,
            )
        if not row.get("bonus_condition_name"):
            row["bonus_condition_name"] = getattr(
                TRADE_CONFIG,
                "bonus_condition_name",
                TRADE_CONFIG.legacy_condition_name,
            )
    return rows


def capture_price_events(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    return [row for row in rows if row.get("event") == "capture_price"]
