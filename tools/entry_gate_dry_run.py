from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from review.structured_log import iter_structured_events
from trade_config import TRADE_CONFIG


DEFAULT_OUTPUT_DIR = Path("reports") / "entry_gate"
POLICIES = {
    "pullback_0p5": 0.005,
    "pullback_0p8": 0.008,
    "pullback_1p0": 0.010,
    "pullback_1p5": 0.015,
}

CSV_FIELDS = [
    "policy",
    "symbol",
    "symbol_name",
    "raw_symbols",
    "candidate_ids",
    "condition_name",
    "candidate_role",
    "join_key",
    "join_status",
    "would_buy",
    "baseline_allowed",
    "best_timestamp",
    "last_evaluated_at",
    "capture_price",
    "current_price",
    "pullback_pct",
    "return_pct",
    "trade_strength",
    "volume_ratio",
    "spread_rate",
    "is_above_vwap",
    "one_min_reversal",
    "upper_wick_ratio",
    "time_policy_reason_code",
    "block_reason",
    "missing_momentum_reason",
]

MISSING_MOMENTUM_FIELDS = [
    "symbol",
    "symbol_name",
    "candidate_ids",
    "candidate_id_count",
    "raw_symbols",
    "condition_name",
    "candidate_role",
    "first_detected_at",
    "last_detected_at",
    "capture_price",
    "candidate_registered_at",
    "last_candidate_event",
    "last_time_policy_at",
    "last_time_policy_reason",
    "last_time_policy_source",
    "time_policy_eval_count",
    "last_evaluated_at",
    "momentum_count",
    "final_count",
    "join_key",
    "join_status",
    "missing_reason",
    "expected_next_step",
    "is_bug_or_expected",
]


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _parse_dt(value: object) -> Optional[datetime]:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def _normalize_symbol(value: object) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return ""
    if text.startswith("A") and len(text) == 7 and text[1:].isalnum():
        text = text[1:]
    if text.isdigit():
        return text.zfill(6)
    return text


def _symbol(payload: Dict[str, object]) -> str:
    return _normalize_symbol(payload.get("symbol") or payload.get("code"))


def _event_rank(payload: Dict[str, object]) -> float:
    dt = _parse_dt(
        payload.get("timestamp")
        or payload.get("current_time")
        or payload.get("_line_timestamp")
        or payload.get("logged_at")
        or payload.get("detected_at")
        or payload.get("captured_at")
    )
    return dt.timestamp() if dt else 0.0


def _event_time(payload: Dict[str, object]) -> str:
    for key in ("timestamp", "current_time", "_line_timestamp", "logged_at", "detected_at", "captured_at"):
        value = str(payload.get(key) or "").strip()
        if value:
            return value[:19].replace("T", " ")
    return ""


def _candidate_id(payload: Dict[str, object]) -> str:
    return str(payload.get("candidate_id") or "").strip()


def _split_ids(value: object) -> List[str]:
    if isinstance(value, (list, tuple, set)):
        return sorted(str(item).strip() for item in value if str(item).strip())
    text = str(value or "").strip()
    if not text:
        return []
    return [item.strip() for item in text.split(";") if item.strip()]


def load_log_events(main_log: str | Path, *, target_date: str) -> Dict[str, List[Dict[str, object]]]:
    labels = {
        "momentum_entry_decision",
        "final_entry_decision",
        "time_policy_decision",
        "candidate_registered",
        "candidate_duplicate_refresh",
        "candidate_expired",
        "candidate_lifecycle_summary",
        "would_order",
        "pre_live_order_submit",
    }
    events: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for event in iter_structured_events(main_log, labels=labels, target_date=target_date):
        payload = dict(event.payload)
        event_dt = _parse_dt(payload.get("timestamp") or payload.get("current_time"))
        if event_dt is not None and event_dt.strftime("%Y-%m-%d") != target_date:
            continue
        symbol = _symbol(payload)
        if not symbol:
            continue
        payload["_event_label"] = event.label
        payload["_log_path"] = event.path
        payload["_line_timestamp"] = event.line[:19]
        payload["_raw_symbol"] = str(payload.get("symbol") or payload.get("code") or "").strip()
        events[symbol].append(payload)
    for rows in events.values():
        rows.sort(key=_event_rank)
    return events


def _empty_candidate(symbol: str) -> Dict[str, object]:
    return {
        "symbol": symbol,
        "symbol_name": "",
        "candidate_ids": set(),
        "raw_symbols": set(),
        "condition_names": set(),
        "candidate_roles": set(),
        "time_policy_reasons": [],
        "first_detected_at": "",
        "last_detected_at": "",
        "capture_price": "",
    }


def _merge_candidate_row(candidate: Dict[str, object], row: Dict[str, object]) -> None:
    symbol = _normalize_symbol(row.get("symbol") or row.get("code"))
    if not symbol:
        return
    candidate["symbol"] = symbol
    name = str(row.get("symbol_name") or row.get("name") or "").strip()
    if name and not candidate.get("symbol_name"):
        candidate["symbol_name"] = name
    candidate_id = str(row.get("candidate_id") or "").strip()
    if candidate_id:
        candidate["candidate_ids"].add(candidate_id)
    raw_symbol = str(row.get("symbol") or row.get("code") or "").strip()
    if raw_symbol:
        candidate["raw_symbols"].add(raw_symbol)
    condition_name = str(row.get("condition_name") or "").strip()
    if condition_name:
        candidate["condition_names"].add(condition_name)
    role = str(row.get("candidate_role") or "").strip()
    if role:
        candidate["candidate_roles"].add(role)
    policy_reason = str(row.get("time_policy_reason") or "").strip()
    if policy_reason:
        candidate["time_policy_reasons"].append(policy_reason)

    detected_at = str(row.get("detected_at") or row.get("logged_at") or "").strip()
    if detected_at:
        first = str(candidate.get("first_detected_at") or "")
        last = str(candidate.get("last_detected_at") or "")
        if not first or detected_at < first:
            candidate["first_detected_at"] = detected_at
        if not last or detected_at > last:
            candidate["last_detected_at"] = detected_at

    capture = row.get("capture_price")
    if str(capture or "").strip() and not str(candidate.get("capture_price") or "").strip():
        candidate["capture_price"] = capture


def load_condition_candidates(
    condition_captures: str | Path,
    *,
    target_date: str,
) -> Dict[str, Dict[str, object]]:
    rows = load_condition_capture_rows(condition_captures, target_date=target_date)
    candidates: Dict[str, Dict[str, object]] = {}
    for row in rows:
        if row.get("event") not in {"condition_detected", "capture_price"}:
            continue
        symbol = _normalize_symbol(row.get("symbol") or row.get("code"))
        if not symbol:
            continue
        candidate = candidates.setdefault(symbol, _empty_candidate(symbol))
        _merge_candidate_row(candidate, row)
    return candidates


def load_condition_capture_rows(
    condition_captures: str | Path,
    *,
    target_date: str,
) -> List[Dict[str, object]]:
    path = Path(condition_captures)
    if not path.exists():
        return []
    rows: List[Dict[str, object]] = []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_date = (
                str(row.get("logged_at") or "")
                or str(row.get("detected_at") or "")
                or str(row.get("captured_at") or "")
            )
            if target_date and target_date not in row_date:
                continue
            rows.append(dict(row))
    return rows


def _candidate_to_row(candidate: Dict[str, object]) -> Dict[str, object]:
    roles = sorted(candidate.get("candidate_roles") or [])
    role = "trading" if "trading" in roles else (roles[0] if roles else "")
    return {
        "symbol": candidate.get("symbol") or "",
        "symbol_name": candidate.get("symbol_name") or "",
        "candidate_ids": ";".join(sorted(candidate.get("candidate_ids") or [])),
        "raw_symbols": ";".join(sorted(candidate.get("raw_symbols") or [])),
        "condition_name": ";".join(sorted(candidate.get("condition_names") or [])),
        "candidate_role": role,
        "first_detected_at": candidate.get("first_detected_at") or "",
        "last_detected_at": candidate.get("last_detected_at") or "",
        "capture_price": candidate.get("capture_price") or "",
    }


def candidates_from_events(events: Dict[str, List[Dict[str, object]]]) -> Dict[str, Dict[str, object]]:
    candidates: Dict[str, Dict[str, object]] = {}
    for symbol, rows in events.items():
        candidate = candidates.setdefault(symbol, _empty_candidate(symbol))
        for row in rows:
            _merge_candidate_row(candidate, row)
            if not candidate.get("first_detected_at"):
                candidate["first_detected_at"] = _event_time(row)
            candidate["last_detected_at"] = _event_time(row) or candidate.get("last_detected_at", "")
    return candidates


def _events_by_candidate_id(events: Dict[str, List[Dict[str, object]]]) -> Dict[str, List[Dict[str, object]]]:
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for rows in events.values():
        for row in rows:
            candidate_id = _candidate_id(row)
            if candidate_id:
                grouped[candidate_id].append(row)
    for rows in grouped.values():
        rows.sort(key=_event_rank)
    return grouped


def _matched_rows(
    candidate: Dict[str, object],
    events: Dict[str, List[Dict[str, object]]],
    events_by_candidate: Dict[str, List[Dict[str, object]]],
) -> tuple[List[Dict[str, object]], str, str]:
    candidate_ids = _split_ids(candidate.get("candidate_ids"))
    by_id: List[Dict[str, object]] = []
    for candidate_id in candidate_ids:
        by_id.extend(events_by_candidate.get(candidate_id, []))
    by_id.sort(key=_event_rank)
    symbol = str(candidate.get("symbol") or "")
    by_symbol = list(events.get(symbol, []))
    if by_id:
        candidate_id_set = set(candidate_ids)
        context_rows = [
            row
            for row in by_symbol
            if not _candidate_id(row) or _candidate_id(row) in candidate_id_set
        ]
        merged = list({id(row): row for row in [*by_id, *context_rows]}.values())
        merged.sort(key=_event_rank)
        return merged, ";".join(candidate_ids), "candidate_id"
    if by_symbol:
        legacy_rows = [row for row in by_symbol if not _candidate_id(row)]
        if legacy_rows:
            status = "symbol_fallback" if candidate_ids else "symbol"
            return legacy_rows, symbol, status
    return [], ";".join(candidate_ids) or symbol, "missing"


def _latest_final(rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    finals = [row for row in rows if row.get("_event_label") == "final_entry_decision"]
    return finals[-1] if finals else {}


def _best_momentum(rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    momentums = [row for row in rows if row.get("_event_label") == "momentum_entry_decision"]
    if not momentums:
        return {}
    return max(
        momentums,
        key=lambda row: (
            _as_float(row.get("pullback_pct")),
            _as_float(row.get("trade_strength")),
            _event_rank(row),
        ),
    )


def _last_eval_time(rows: Sequence[Dict[str, object]]) -> str:
    evals = [
        row
        for row in rows
        if row.get("_event_label") in {"momentum_entry_decision", "final_entry_decision"}
    ]
    if not evals:
        return ""
    return _event_time(evals[-1])


def _last_event(rows: Sequence[Dict[str, object]], label: str) -> Dict[str, object]:
    matches = [row for row in rows if row.get("_event_label") == label]
    return matches[-1] if matches else {}


def _time_policy_rows(rows: Sequence[Dict[str, object]], *, source: str = "") -> List[Dict[str, object]]:
    policies = [row for row in rows if row.get("_event_label") == "time_policy_decision"]
    if source:
        policies = [row for row in policies if str(row.get("source") or "") == source]
    return policies


def _last_time_policy(rows: Sequence[Dict[str, object]], *, prefer_eval_filter: bool = False) -> Dict[str, object]:
    if prefer_eval_filter:
        eval_policies = _time_policy_rows(rows, source="evaluate_time_filter")
        if eval_policies:
            return eval_policies[-1]
    return _last_event(rows, "time_policy_decision")


def _missing_momentum_reason(candidate: Dict[str, object], rows: Sequence[Dict[str, object]]) -> str:
    momentums = [row for row in rows if row.get("_event_label") == "momentum_entry_decision"]
    if momentums:
        return ""
    finals = [row for row in rows if row.get("_event_label") == "final_entry_decision"]
    if finals:
        return "final_logged_without_momentum_log"
    registered = [row for row in rows if row.get("_event_label") == "candidate_registered"]
    last_policy = _last_time_policy(rows, prefer_eval_filter=bool(registered))
    last_policy_reason = str(last_policy.get("reason_code") or "")
    last_policy_source = str(last_policy.get("source") or "")
    if not registered:
        candidate_role = str(candidate.get("candidate_role") or "")
        if candidate_role == "analysis_only":
            return "analysis_only_not_registered"
        if last_policy_reason:
            return f"not_registered_time_policy_{last_policy_reason}"
        return "not_registered_or_no_log_event"
    if last_policy_reason and last_policy_reason not in {"ALLOW_ENTRY", "ALLOW_CANDIDATE_CAPTURE"}:
        if last_policy_source == "evaluate_time_filter":
            return f"evaluation_loop_time_policy_pre_momentum_{last_policy_reason}"
        return f"time_policy_block_{last_policy_reason}"
    if not str(candidate.get("capture_price") or "").strip():
        return "registered_waiting_capture_price_or_first_tick"
    return "registered_but_no_momentum_event"


def _missing_expected(reason: str) -> tuple[str, str]:
    if reason == "analysis_only_not_registered":
        return "analysis_only_sample; no live entry", "expected_policy"
    if reason.startswith("evaluation_loop_time_policy_pre_momentum_"):
        return "emit analysis momentum snapshot; keep entry blocked", "expected_policy_missing_snapshot"
    if reason.startswith("time_policy_block_") or reason.startswith("not_registered_time_policy_"):
        return "keep as time policy block; no order", "expected_policy"
    if reason == "registered_waiting_capture_price_or_first_tick":
        return "wait for first realtime tick/capture_price", "expected_data_wait"
    if reason == "registered_but_no_momentum_event":
        return "inspect eval loop scheduling/log emission", "needs_investigation"
    if reason == "final_logged_without_momentum_log":
        return "fix decision trace join/log ordering", "bug"
    return "inspect candidate lifecycle", "needs_investigation"


def _has_rebound(momentum: Dict[str, object], min_rebound: float) -> bool:
    return _as_float(momentum.get("recent_low_to_current_pct")) >= float(min_rebound or 0.0)


def _conditional_spread_relief(momentum: Dict[str, object]) -> bool:
    if not bool(getattr(TRADE_CONFIG, "conditional_spread_relief_enabled", False)):
        return False
    spread = _as_float(momentum.get("spread_rate"))
    if spread <= TRADE_CONFIG.max_spread_pct:
        return True
    if spread > float(getattr(TRADE_CONFIG, "max_conditional_spread_pct", TRADE_CONFIG.max_spread_pct)):
        return False
    if _as_bool(momentum.get("was_below_vwap"), default=False):
        return False
    if _as_float(momentum.get("trade_strength")) < float(
        getattr(TRADE_CONFIG, "conditional_spread_min_trade_strength", 0.0) or 0.0
    ):
        return False
    if _as_float(momentum.get("volume_ratio")) < float(
        getattr(TRADE_CONFIG, "conditional_spread_min_volume_ratio", 0.0) or 0.0
    ):
        return False
    if not _has_rebound(
        momentum,
        float(getattr(TRADE_CONFIG, "conditional_spread_min_rebound_pct", 0.0) or 0.0),
    ):
        return False
    if not _as_bool(momentum.get("one_min_reversal"), default=True):
        return False
    return True


def _weak_volume_relief(momentum: Dict[str, object], *, threshold: float) -> bool:
    if not bool(getattr(TRADE_CONFIG, "weak_volume_partial_entry_enabled", False)):
        return False
    if _as_float(momentum.get("trade_strength")) < float(
        getattr(TRADE_CONFIG, "weak_volume_partial_min_trade_strength", 0.0) or 0.0
    ):
        return False
    if (
        _as_float(momentum.get("spread_rate")) > TRADE_CONFIG.max_spread_pct
        and not _conditional_spread_relief(momentum)
    ):
        return False
    min_partial_volume = float(
        getattr(TRADE_CONFIG, "weak_volume_partial_min_volume_ratio", 0.0) or 0.0
    )
    turnover_ok = (
        not bool(getattr(TRADE_CONFIG, "require_turnover_speed", True))
        or _as_float(momentum.get("turnover_speed_per_min")) >= TRADE_CONFIG.min_turnover_speed_per_min
    )
    if _as_float(momentum.get("volume_ratio")) < min_partial_volume and not turnover_ok:
        return False
    if _as_float(momentum.get("pullback_pct")) < threshold:
        return False
    if not _has_rebound(
        momentum,
        float(getattr(TRADE_CONFIG, "weak_volume_partial_min_rebound_pct", 0.0) or 0.0),
    ):
        return False
    return True


def _base_block_reason(momentum: Dict[str, object], *, threshold: float, breakout: bool = False) -> str:
    time_reason = str(momentum.get("time_policy_reason_code") or "")
    if time_reason and time_reason not in {"ALLOW_ENTRY", "ALLOW_LATE_A_GRADE_ENTRY"}:
        return time_reason
    if _as_float(momentum.get("trade_strength")) < 100.0:
        return "trade_strength_lt_100"
    if not _as_bool(momentum.get("is_above_vwap"), default=True):
        if (
            _as_float(momentum.get("trade_strength"))
            >= float(getattr(TRADE_CONFIG, "vwap_reclaim_wait_trade_strength", 180.0) or 180.0)
            and _as_float(momentum.get("spread_rate")) <= TRADE_CONFIG.max_spread_pct
        ):
            return "WAIT_RECLAIM_VWAP"
        return "BLOCK_BELOW_VWAP_WEAK_FLOW"
    if _as_bool(momentum.get("was_below_vwap"), default=False):
        vwap = _as_float(momentum.get("vwap"))
        current = _as_float(momentum.get("current_price"))
        reclaim_price = vwap * (
            1.0 + float(getattr(TRADE_CONFIG, "vwap_reclaim_confirm_buffer_pct", 0.0) or 0.0)
        )
        if vwap > 0 and current < reclaim_price:
            return "WAIT_RECLAIM_VWAP"
        if not _as_bool(momentum.get("one_min_reversal"), default=True):
            return "WAIT_RECLAIM_VWAP"
    if _as_float(momentum.get("spread_rate")) > TRADE_CONFIG.max_spread_pct and not _conditional_spread_relief(momentum):
        return "spread_too_wide"
    if _as_float(momentum.get("upper_wick_ratio")) > 0.30:
        return "upper_wick_too_large"
    if not _as_bool(momentum.get("one_min_reversal"), default=True):
        return "missing_one_min_reversal"
    if _as_float(momentum.get("volume_ratio")) < TRADE_CONFIG.min_volume_ratio and (
        breakout
        or not _weak_volume_relief(
            momentum,
            threshold=threshold,
        )
    ):
        return "volume_ratio_lt_1p2"
    if breakout:
        capture = _as_float(momentum.get("capture_price"))
        current = _as_float(momentum.get("current_price"))
        if capture <= 0 or current < capture:
            return "not_breakout_above_capture"
        return ""
    if _as_float(momentum.get("pullback_pct")) < threshold:
        return "pullback_shallow"
    return ""


def _row_for_policy(
    policy: str,
    candidate: Dict[str, object],
    rows: Sequence[Dict[str, object]],
    *,
    threshold: float = 0.0,
    breakout: bool = False,
    join_key: str = "",
    join_status: str = "",
) -> Dict[str, object]:
    symbol = str(candidate.get("symbol") or "")
    momentum = _best_momentum(rows)
    final = _latest_final(rows)
    missing_reason = _missing_momentum_reason(candidate, rows)
    reason = _base_block_reason(momentum, threshold=threshold, breakout=breakout) if momentum else "missing_momentum_log"
    baseline_allowed = bool(final.get("allowed") is True)
    capture = _as_float(momentum.get("capture_price"))
    if capture <= 0:
        capture = _as_float(candidate.get("capture_price"))
    current = _as_float(momentum.get("current_price"))
    return {
        "policy": policy,
        "symbol": symbol,
        "symbol_name": momentum.get("symbol_name") or final.get("symbol_name") or candidate.get("symbol_name") or "",
        "raw_symbols": candidate.get("raw_symbols") or "",
        "candidate_ids": candidate.get("candidate_ids") or "",
        "condition_name": momentum.get("condition_name") or final.get("condition_name") or candidate.get("condition_name") or "",
        "candidate_role": candidate.get("candidate_role") or "",
        "join_key": join_key,
        "join_status": join_status,
        "would_buy": not bool(reason),
        "baseline_allowed": baseline_allowed,
        "best_timestamp": momentum.get("timestamp") or final.get("timestamp") or "",
        "last_evaluated_at": _last_eval_time(rows),
        "capture_price": int(capture) if capture > 0 else "",
        "current_price": int(current) if current > 0 else "",
        "pullback_pct": _as_float(momentum.get("pullback_pct")),
        "return_pct": (current / capture - 1.0) if capture > 0 and current > 0 else "",
        "trade_strength": _as_float(momentum.get("trade_strength")),
        "volume_ratio": _as_float(momentum.get("volume_ratio")),
        "spread_rate": _as_float(momentum.get("spread_rate")),
        "is_above_vwap": momentum.get("is_above_vwap"),
        "one_min_reversal": momentum.get("one_min_reversal"),
        "upper_wick_ratio": _as_float(momentum.get("upper_wick_ratio")),
        "time_policy_reason_code": momentum.get("time_policy_reason_code") or "",
        "block_reason": reason,
        "missing_momentum_reason": missing_reason,
    }


def build_rows(
    events: Dict[str, List[Dict[str, object]]],
    candidates: Dict[str, Dict[str, object]],
) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    events_by_candidate = _events_by_candidate_id(events)
    for symbol, raw_candidate in sorted(candidates.items()):
        candidate = _candidate_to_row(raw_candidate)
        candidate["symbol"] = symbol
        rows, join_key, join_status = _matched_rows(candidate, events, events_by_candidate)
        for policy, threshold in POLICIES.items():
            out.append(
                _row_for_policy(
                    policy,
                    candidate,
                    rows,
                    threshold=threshold,
                    join_key=join_key,
                    join_status=join_status,
                )
            )
        out.append(
            _row_for_policy(
                "breakout_small",
                candidate,
                rows,
                breakout=True,
                join_key=join_key,
                join_status=join_status,
            )
        )
    return out


def build_funnel(
    *,
    raw_condition_rows: Sequence[Dict[str, object]],
    events: Dict[str, List[Dict[str, object]]],
    candidates: Dict[str, Dict[str, object]],
    rows: Sequence[Dict[str, object]],
) -> Dict[str, int]:
    condition_detected = [
        row for row in raw_condition_rows if str(row.get("event") or "") == "condition_detected"
    ]
    symbol_rows = rows[:: max(len(POLICIES) + 1, 1)]
    policy_rows = list(rows)
    registered = set()
    momentum_evaluated = set()
    final_decision = set()
    actually_ordered = set()
    for symbol, event_rows in events.items():
        for event in event_rows:
            label = event.get("_event_label")
            cid = _candidate_id(event) or symbol
            if label == "candidate_registered":
                registered.add(cid)
            elif label == "momentum_entry_decision":
                momentum_evaluated.add(cid)
            elif label == "final_entry_decision":
                final_decision.add(cid)
            elif label in {"would_order", "pre_live_order_submit"}:
                side = str(event.get("side") or "").lower()
                if side in {"", "buy"}:
                    actually_ordered.add(cid)
    analysis_only = [
        row
        for row in condition_detected
        if str(row.get("candidate_role") or "") == "analysis_only"
    ]
    baseline_symbols = {
        str(row.get("symbol") or "")
        for row in symbol_rows
        if row.get("baseline_allowed") is True
    }
    relaxed_symbols = {
        str(row.get("symbol") or "")
        for row in policy_rows
        if row.get("would_buy") is True
    }
    return {
        "raw_condition_detected_count": len(condition_detected),
        "registered_candidate_count": len(registered),
        "analysis_only_count": len(analysis_only),
        "momentum_evaluated_count": len(momentum_evaluated),
        "final_entry_decision_count": len(final_decision),
        "baseline_would_buy_count": len(baseline_symbols),
        "relaxed_would_buy_count": len(relaxed_symbols),
        "actually_ordered_count": len(actually_ordered),
        "unique_symbol_count": len(candidates),
        "policy_row_count": len(policy_rows),
    }


def write_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def build_missing_momentum_rows(
    events: Dict[str, List[Dict[str, object]]],
    candidates: Dict[str, Dict[str, object]],
) -> List[Dict[str, object]]:
    events_by_candidate = _events_by_candidate_id(events)
    out: List[Dict[str, object]] = []
    for symbol, raw_candidate in sorted(candidates.items()):
        candidate = _candidate_to_row(raw_candidate)
        candidate["symbol"] = symbol
        rows, join_key, join_status = _matched_rows(candidate, events, events_by_candidate)
        momentum_count = sum(1 for row in rows if row.get("_event_label") == "momentum_entry_decision")
        if momentum_count:
            continue
        final_count = sum(1 for row in rows if row.get("_event_label") == "final_entry_decision")
        registered = [row for row in rows if row.get("_event_label") == "candidate_registered"]
        policy_rows = _time_policy_rows(rows)
        last_policy = _last_time_policy(rows, prefer_eval_filter=bool(registered))
        candidate_events = [
            row
            for row in rows
            if row.get("_event_label")
            in {"candidate_registered", "candidate_duplicate_refresh", "candidate_expired", "candidate_lifecycle_summary"}
        ]
        candidate_ids = _split_ids(candidate.get("candidate_ids"))
        missing_reason = _missing_momentum_reason(candidate, rows)
        expected_next_step, is_bug_or_expected = _missing_expected(missing_reason)
        out.append(
            {
                "symbol": symbol,
                "symbol_name": candidate.get("symbol_name") or "",
                "candidate_ids": ";".join(candidate_ids),
                "candidate_id_count": len(candidate_ids),
                "raw_symbols": candidate.get("raw_symbols") or "",
                "condition_name": candidate.get("condition_name") or "",
                "candidate_role": candidate.get("candidate_role") or "",
                "first_detected_at": candidate.get("first_detected_at") or "",
                "last_detected_at": candidate.get("last_detected_at") or "",
                "capture_price": candidate.get("capture_price") or "",
                "candidate_registered_at": _event_time(registered[0]) if registered else "",
                "last_candidate_event": str(candidate_events[-1].get("_event_label") or "") if candidate_events else "",
                "last_time_policy_at": _event_time(last_policy),
                "last_time_policy_reason": last_policy.get("reason_code") or "",
                "last_time_policy_source": last_policy.get("source") or "",
                "time_policy_eval_count": len(policy_rows),
                "last_evaluated_at": _last_eval_time(rows),
                "momentum_count": momentum_count,
                "final_count": final_count,
                "join_key": join_key,
                "join_status": join_status,
                "missing_reason": missing_reason,
                "expected_next_step": expected_next_step,
                "is_bug_or_expected": is_bug_or_expected,
            }
        )
    return out


def write_missing_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=MISSING_MOMENTUM_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in MISSING_MOMENTUM_FIELDS})


def _pct(value: object) -> str:
    number = _as_float(value, default=float("nan"))
    if number != number:
        return ""
    return "{:+.2f}%".format(number * 100.0)


def write_markdown(
    path: Path,
    rows: Sequence[Dict[str, object]],
    *,
    target_date: str,
    missing_momentum_rows: Sequence[Dict[str, object]] = (),
    funnel: Optional[Dict[str, int]] = None,
) -> None:
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["policy"])].append(row)
    baseline_buys = {
        row["symbol"]
        for row in rows
        if row.get("baseline_allowed") is True
    }
    lines = [f"# {target_date} Entry Gate Dry Run", ""]
    lines.append("## Baseline")
    lines.append(f"- baseline_allowed_buy_symbols: {len(baseline_buys)}")
    lines.append("")
    if funnel:
        lines.append("## Daily Buy Gate Funnel")
        lines.append("| metric | value |")
        lines.append("|---|---:|")
        for key in [
            "raw_condition_detected_count",
            "registered_candidate_count",
            "analysis_only_count",
            "momentum_evaluated_count",
            "final_entry_decision_count",
            "baseline_would_buy_count",
            "relaxed_would_buy_count",
            "actually_ordered_count",
            "unique_symbol_count",
            "policy_row_count",
        ]:
            lines.append(f"| {key} | {int(funnel.get(key, 0))} |")
        lines.append("")
    lines.append("## Policy Comparison")
    lines.append("| policy | candidate_unique_symbols | would_buy_unique_symbols | blocked_unique_symbols | policy_rows | top_block_reason |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for policy, members in grouped.items():
        would = [row for row in members if row.get("would_buy") is True]
        blocked = [row for row in members if row.get("would_buy") is not True]
        counter = Counter(str(row.get("block_reason") or "") for row in blocked)
        top_reason = counter.most_common(1)[0][0] if counter else ""
        lines.append(
            "| {policy} | {candidates} | {would} | {blocked} | {rows} | {top_reason} |".format(
                policy=policy,
                candidates=len({row.get("symbol") for row in members}),
                would=len({row.get("symbol") for row in would}),
                blocked=len({row.get("symbol") for row in blocked}),
                rows=len(members),
                top_reason=top_reason,
            )
        )
    lines.append("")
    lines.append("## Reason Counts by Policy Row")
    reason_counter = Counter(str(row.get("block_reason") or "would_buy") for row in rows)
    lines.append("| reason | count |")
    lines.append("|---|---:|")
    for reason, count in reason_counter.most_common():
        lines.append(f"| {reason or 'would_buy'} | {count} |")
    lines.append("")
    lines.append("## Reason Counts by Unique Symbol")
    unique_reason: Dict[str, set[str]] = defaultdict(set)
    for row in rows:
        unique_reason[str(row.get("block_reason") or "would_buy")].add(str(row.get("symbol") or ""))
    lines.append("| reason | unique_symbols |")
    lines.append("|---|---:|")
    for reason, symbols in sorted(unique_reason.items(), key=lambda item: (-len(item[1]), item[0])):
        lines.append(f"| {reason or 'would_buy'} | {len(symbols)} |")
    lines.append("")
    lines.append("## Missing Momentum Log")
    if missing_momentum_rows:
        missing_counter = Counter(str(row.get("missing_reason") or "unknown") for row in missing_momentum_rows)
        lines.append(f"- symbols_without_momentum_entry_decision: {len(missing_momentum_rows)}")
        lines.append("")
        lines.append("| missing_reason | symbols |")
        lines.append("|---|---:|")
        for reason, count in missing_counter.most_common():
            lines.append(f"| {reason} | {count} |")
        lines.append("")
        lines.append("| symbol | name | detected_at | candidate_ids | registered_at | last_time_policy | last_eval | join | reason | expected_next_step | bug_or_expected |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for row in missing_momentum_rows:
            policy = str(row.get("last_time_policy_reason") or "")
            policy_at = str(row.get("last_time_policy_at") or "")
            policy_cell = f"{policy}@{policy_at}" if policy or policy_at else ""
            lines.append(
                "| {symbol} | {name} | {detected} | {candidate_ids} | {registered} | {policy} | {last_eval} | {join_status} | {reason} | {expected} | {bug} |".format(
                    symbol=row.get("symbol") or "",
                    name=str(row.get("symbol_name") or "").replace("|", "/"),
                    detected=row.get("first_detected_at") or "",
                    candidate_ids=str(row.get("candidate_ids") or "").replace("|", "/"),
                    registered=row.get("candidate_registered_at") or "",
                    policy=policy_cell,
                    last_eval=row.get("last_evaluated_at") or "",
                    join_status=row.get("join_status") or "",
                    reason=row.get("missing_reason") or "",
                    expected=str(row.get("expected_next_step") or "").replace("|", "/"),
                    bug=row.get("is_bug_or_expected") or "",
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Join Key Notes")
    symbol_rows = rows[:: max(len(POLICIES) + 1, 1)]
    join_counter = Counter(str(row.get("join_status") or "unknown") for row in symbol_rows)
    lines.append("| join_status | symbols |")
    lines.append("|---|---:|")
    for status, count in join_counter.most_common():
        lines.append(f"| {status} | {count} |")
    raw_variant_count = 0
    a_prefix_count = 0
    alnum_symbols: List[str] = []
    for row in symbol_rows:
        raws = [item for item in str(row.get("raw_symbols") or "").split(";") if item]
        if len(set(raws)) > 1:
            raw_variant_count += 1
        if any(item.upper().startswith("A") and len(item) == 7 for item in raws):
            a_prefix_count += 1
        symbol = str(row.get("symbol") or "")
        if any(ch.isalpha() for ch in symbol):
            alnum_symbols.append(symbol)
    lines.append("")
    lines.append(f"- raw_symbol_variant_symbols: {raw_variant_count}")
    lines.append(f"- raw_A_prefix_symbols: {a_prefix_count}")
    lines.append(
        "- alphanumeric_symbols: {}".format(
            ", ".join(sorted(alnum_symbols)) if alnum_symbols else "none"
        )
    )
    lines.append("")
    lines.append("## Would Buy Comparison")
    lines.append("| policy | unique_symbol_count | policy_row_count | would_buy_unique_symbols | would_buy_policy_rows |")
    lines.append("|---|---:|---:|---:|---:|")
    for policy, members in grouped.items():
        would = [row for row in members if row.get("would_buy") is True]
        lines.append(
            f"| {policy} | {len({row.get('symbol') for row in members})} | {len(members)} | {len({row.get('symbol') for row in would})} | {len(would)} |"
        )
    lines.append("")
    lines.append("## Reconciliation")
    if funnel:
        lines.append(
            "- raw_condition_detected_count={} and unique_symbol_count={} are different denominators. Post-market keeps raw detections; entry-gate dry-run evaluates unique symbols and expands policy rows.".format(
                funnel.get("raw_condition_detected_count", 0),
                funnel.get("unique_symbol_count", 0),
            )
        )
        lines.append(
            "- policy_row_count={} equals unique symbols multiplied by the policy set. Compare would_buy_unique_symbols before comparing to post-market raw rows.".format(
                funnel.get("policy_row_count", 0)
            )
        )
    lines.append("- post-market relaxed pullback counts are pullback-threshold signals, not full buy-gate approvals. This dry-run keeps VWAP, volume, spread, wick, time-policy and final-entry blocks in the same row.")
    lines.append("")
    lines.append("## Candidate Detail")
    lines.append("| policy | symbol | name | would_buy | block_reason | missing_reason | pullback | return | strength | volume_ratio | time_policy | join |")
    lines.append("|---|---|---|---|---|---|---:|---:|---:|---:|---|---|")
    for row in sorted(rows, key=lambda item: (str(item["policy"]), str(item["symbol"]))):
        lines.append(
            "| {policy} | {symbol} | {name} | {would} | {reason} | {missing} | {pullback} | {ret} | {strength:.1f} | {volume:.2f} | {time} | {join} |".format(
                policy=row["policy"],
                symbol=row["symbol"],
                name=str(row.get("symbol_name") or "").replace("|", "/"),
                would="Y" if row.get("would_buy") is True else "N",
                reason=row.get("block_reason") or "",
                missing=row.get("missing_momentum_reason") or "",
                pullback=_pct(row.get("pullback_pct")),
                ret=_pct(row.get("return_pct")),
                strength=_as_float(row.get("trade_strength")),
                volume=_as_float(row.get("volume_ratio")),
                time=row.get("time_policy_reason_code") or "",
                join=row.get("join_status") or "",
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(
    *,
    main_log: str | Path,
    target_date: str,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    condition_captures: str | Path = Path("data") / "condition_captures.csv",
) -> Dict[str, Path]:
    events = load_log_events(main_log, target_date=target_date)
    raw_condition_rows = load_condition_capture_rows(condition_captures, target_date=target_date)
    candidates = load_condition_candidates(condition_captures, target_date=target_date)
    if not candidates:
        candidates = candidates_from_events(events)
    rows = build_rows(events, candidates)
    missing_rows = build_missing_momentum_rows(events, candidates)
    funnel = build_funnel(
        raw_condition_rows=raw_condition_rows,
        events=events,
        candidates=candidates,
        rows=rows,
    )
    yyyymmdd = target_date.replace("-", "")
    out_dir = Path(output_dir)
    csv_path = out_dir / f"{yyyymmdd}_entry_gate_dry_run.csv"
    md_path = out_dir / f"{yyyymmdd}_entry_gate_dry_run.md"
    missing_csv_path = out_dir / f"{yyyymmdd}_missing_momentum_log.csv"
    write_csv(csv_path, rows)
    write_missing_csv(missing_csv_path, missing_rows)
    write_markdown(
        md_path,
        rows,
        target_date=target_date,
        missing_momentum_rows=missing_rows,
        funnel=funnel,
    )
    return {"csv": csv_path, "markdown": md_path, "missing_momentum_csv": missing_csv_path}


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay entry-gate relaxations from main.log* only.")
    parser.add_argument("--date", required=True, help="Target date in YYYY-MM-DD format.")
    parser.add_argument("--main-log", default="data/main.log")
    parser.add_argument("--condition-captures", default="data/condition_captures.csv")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    paths = run(
        main_log=args.main_log,
        target_date=args.date,
        output_dir=args.output,
        condition_captures=args.condition_captures,
    )
    print(f"csv: {paths['csv']}")
    print(f"md: {paths['markdown']}")
    print(f"missing_momentum_csv: {paths['missing_momentum_csv']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
