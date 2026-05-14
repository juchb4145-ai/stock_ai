from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


FINAL_ENTRY_STRATEGY_VERSION = "momentum_v2_selective_relief_v1"
ENTRY_TYPE_BREAKOUT_SMALL = "BREAKOUT_SMALL"


@dataclass(frozen=True)
class FinalEntryDecision:
    allowed: bool
    status: str
    reason_code: str
    final_reason: str
    strategy_version: str
    legacy_filter_enabled: bool
    momentum_decision: str
    momentum_reason_code: str
    legacy_decision: str
    legacy_reason_code: str
    blocked_by: str = ""
    entry_type: str = ""
    position_size_multiplier: float = 0.0
    legacy_veto_applied: bool = False
    legacy_veto_ignored: bool = False
    decision_trace: Dict[str, Any] = field(default_factory=dict)


def build_final_entry_decision(
    *,
    momentum_action: str,
    momentum_reason_code: str,
    momentum_reason: str,
    momentum_chase_risk_score: Optional[float] = None,
    legacy_status: str = "",
    legacy_reason_code: str = "",
    legacy_reason: str = "",
    strategy_version: str = FINAL_ENTRY_STRATEGY_VERSION,
    legacy_filter_enabled: bool = True,
    entry_type: str = "",
    position_size_multiplier: float = 0.0,
    legacy_filter_veto_breakout_small: bool = False,
) -> FinalEntryDecision:
    momentum_action = str(momentum_action or "").upper()
    legacy_status = str(legacy_status or "").lower()
    momentum_reason_code = str(momentum_reason_code or "")
    legacy_reason_code = str(legacy_reason_code or "")
    momentum_reason = str(momentum_reason or "")
    legacy_reason = str(legacy_reason or "")
    entry_type = str(entry_type or "")
    position_size_multiplier = float(position_size_multiplier or 0.0)

    trace: Dict[str, Any] = {
        "strategy_version": strategy_version,
        "legacy_filter_enabled": bool(legacy_filter_enabled),
        "entry_type": entry_type,
        "position_size_multiplier": position_size_multiplier,
        "momentum_decision": {
            "action": momentum_action,
            "reason_code": momentum_reason_code,
            "reason": momentum_reason,
            "chase_risk_score": momentum_chase_risk_score,
        },
        "legacy_decision": {
            "status": legacy_status or "not_evaluated",
            "reason_code": legacy_reason_code,
            "reason": legacy_reason,
        },
    }

    if momentum_action != "BUY":
        status = (
            "wait"
            if momentum_action in {"WAIT_PULLBACK", "WAIT_RECLAIM_VWAP", "WAIT_DATA", "WAIT"}
            else "blocked"
        )
        reason_code = "FINAL_MOMENTUM_{}".format(momentum_reason_code or momentum_action or "NOT_BUY")
        return FinalEntryDecision(
            allowed=False,
            status=status,
            reason_code=reason_code,
            final_reason="Momentum decision is not BUY: {} {}".format(
                momentum_action,
                momentum_reason or momentum_reason_code,
            ).strip(),
            strategy_version=strategy_version,
            legacy_filter_enabled=bool(legacy_filter_enabled),
            momentum_decision=momentum_action,
            momentum_reason_code=momentum_reason_code,
            legacy_decision=legacy_status or "not_evaluated",
            legacy_reason_code=legacy_reason_code,
            blocked_by="momentum",
            entry_type=entry_type,
            position_size_multiplier=position_size_multiplier,
            decision_trace=trace,
        )

    legacy_veto_applied = bool(legacy_filter_enabled and legacy_status != "ready")
    legacy_veto_ignored = bool(
        legacy_veto_applied
        and entry_type == ENTRY_TYPE_BREAKOUT_SMALL
        and not legacy_filter_veto_breakout_small
    )
    trace["legacy_veto_applied"] = legacy_veto_applied
    trace["legacy_veto_ignored"] = legacy_veto_ignored

    if legacy_veto_applied and not legacy_veto_ignored:
        status = "blocked" if legacy_status == "blocked" else "wait"
        reason_code = "FINAL_LEGACY_VETO_{}".format(legacy_reason_code or legacy_status or "NOT_READY")
        return FinalEntryDecision(
            allowed=False,
            status=status,
            reason_code=reason_code,
            final_reason="Legacy/Dante veto: {} {}".format(
                legacy_status or "not_ready",
                legacy_reason or legacy_reason_code,
            ).strip(),
            strategy_version=strategy_version,
            legacy_filter_enabled=True,
            momentum_decision=momentum_action,
            momentum_reason_code=momentum_reason_code,
            legacy_decision=legacy_status or "not_evaluated",
            legacy_reason_code=legacy_reason_code,
            blocked_by="legacy_veto",
            entry_type=entry_type,
            position_size_multiplier=position_size_multiplier,
            legacy_veto_applied=True,
            decision_trace=trace,
        )

    return FinalEntryDecision(
        allowed=True,
        status="ready",
        reason_code="FINAL_BUY_READY",
        final_reason=(
            "Momentum BUY; legacy/Dante veto ignored for BREAKOUT_SMALL"
            if legacy_veto_ignored
            else "Momentum BUY and legacy/Dante veto filters passed"
        ),
        strategy_version=strategy_version,
        legacy_filter_enabled=bool(legacy_filter_enabled),
        momentum_decision=momentum_action,
        momentum_reason_code=momentum_reason_code,
        legacy_decision=legacy_status or "ready",
        legacy_reason_code=legacy_reason_code,
        blocked_by="",
        entry_type=entry_type,
        position_size_multiplier=position_size_multiplier,
        legacy_veto_applied=legacy_veto_applied,
        legacy_veto_ignored=legacy_veto_ignored,
        decision_trace=trace,
    )


def trace_with_order_guard(
    trace: Optional[Dict[str, Any]],
    *,
    allowed: bool,
    reason: str,
    blocked_by: str = "",
    guard_decision_id: str = "",
    mode: str = "",
) -> Dict[str, Any]:
    merged = dict(trace or {})
    merged["order_guard_decision"] = {
        "allowed": bool(allowed),
        "reason": str(reason or ""),
        "blocked_by": str(blocked_by or ""),
        "guard_decision_id": str(guard_decision_id or ""),
        "mode": str(mode or ""),
    }
    return merged
