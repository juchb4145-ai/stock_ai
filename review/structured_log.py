from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional, Sequence


DEFAULT_MAIN_LOG = Path("data") / "main.log"

_LOG_JSON_RE = re.compile(r"\[(?P<label>[A-Za-z0-9_]+)\]\s+(?P<payload>\{.*\})\s*$")


@dataclass(frozen=True)
class StructuredLogEvent:
    label: str
    payload: Dict[str, object]
    line: str
    path: str = ""


def candidate_log_paths(path: str | Path = DEFAULT_MAIN_LOG) -> Sequence[Path]:
    base = Path(path)
    if base.is_dir():
        paths = sorted(base.glob("main.log*"))
    else:
        paths = sorted(base.parent.glob(base.name + "*"))
    return [p for p in paths if p.is_file()]


def parse_structured_log_line(line: str) -> Optional[StructuredLogEvent]:
    match = _LOG_JSON_RE.search(line.rstrip())
    if not match:
        return None
    try:
        payload = json.loads(match.group("payload"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return StructuredLogEvent(
        label=match.group("label"),
        payload=payload,
        line=line.rstrip("\n"),
    )


def iter_structured_events(
    path: str | Path = DEFAULT_MAIN_LOG,
    *,
    labels: Optional[Iterable[str]] = None,
    target_date: str = "",
) -> Iterator[StructuredLogEvent]:
    wanted = set(labels or [])
    for log_path in candidate_log_paths(path):
        try:
            with log_path.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if target_date and target_date not in line:
                        continue
                    event = parse_structured_log_line(line)
                    if event is None:
                        continue
                    if wanted and event.label not in wanted:
                        continue
                    yield StructuredLogEvent(
                        label=event.label,
                        payload=event.payload,
                        line=event.line,
                        path=str(log_path),
                    )
        except OSError:
            continue
