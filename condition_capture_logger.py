from __future__ import annotations

import csv
import os
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple, Union

from trade_config import TRADE_CONFIG


CONDITION_CAPTURE_CSV = os.path.join("data", "condition_captures.csv")

CONDITION_CAPTURE_FIELDS = [
    "logged_at",
    "event",
    "detected_at",
    "captured_at",
    "captured_time",
    "code",
    "name",
    "condition_name",
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
    name: str = ""
    condition_name: str = ""
    condition_formula: str = ""
    condition_formula_version: str = ""
    condition_index: Union[str, int] = ""
    event_type: str = ""
    screen_no: str = ""
    capture_price: int = 0
    entry_trigger_price: int = 0
    chejan_strength: float = 0.0
    accum_volume: int = 0
    signal_source: str = TRADE_CONFIG.signal_source
    source: str = "kiwoom"
    logged_at: str = ""
    detected_at: str = ""
    captured_at: str = ""
    captured_time: str = ""

    def to_row(self) -> Dict[str, object]:
        logged_at = self.logged_at
        captured_at = self.captured_at
        captured_time = self.captured_time
        if not logged_at or not captured_at or not captured_time:
            now_at, now_time = _now_strings()
            logged_at = logged_at or now_at
            captured_at = captured_at or now_at
            captured_time = captured_time or now_time

        return {
            "logged_at": logged_at,
            "event": self.event,
            "detected_at": self.detected_at or captured_at,
            "captured_at": captured_at,
            "captured_time": captured_time,
            "code": self.code,
            "name": self.name,
            "condition_name": self.condition_name,
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
        }


class ConditionCaptureLogger:
    """Append-only CSV logger for condition detections and first capture prices."""

    def __init__(self, path: str = CONDITION_CAPTURE_CSV):
        self.path = path

    def append(self, event: ConditionCaptureEvent) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        file_exists = os.path.exists(self.path) and os.path.getsize(self.path) > 0
        with open(self.path, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CONDITION_CAPTURE_FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(event.to_row())

    def append_detection(
        self,
        *,
        code: str,
        name: str = "",
        condition_name: str = "",
        condition_index: Union[str, int] = "",
        event_type: str = "",
        screen_no: str = "",
    ) -> None:
        self.append(
            ConditionCaptureEvent(
                event="condition_detected",
                code=code,
                name=name,
                condition_name=condition_name,
                condition_index=condition_index,
                event_type=event_type,
                screen_no=screen_no,
            )
        )

    def append_capture_price(
        self,
        *,
        code: str,
        name: str = "",
        condition_name: str = "",
        condition_index: Union[str, int] = "",
        event_type: str = "",
        screen_no: str = "",
        capture_price: int = 0,
        entry_trigger_price: int = 0,
        chejan_strength: float = 0.0,
        accum_volume: int = 0,
    ) -> None:
        self.append(
            ConditionCaptureEvent(
                event="capture_price",
                code=code,
                name=name,
                condition_name=condition_name,
                condition_index=condition_index,
                event_type=event_type,
                screen_no=screen_no,
                capture_price=capture_price,
                entry_trigger_price=entry_trigger_price,
                chejan_strength=chejan_strength,
                accum_volume=accum_volume,
            )
        )


def read_condition_captures(path: str = CONDITION_CAPTURE_CSV) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def capture_price_events(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    return [row for row in rows if row.get("event") == "capture_price"]
