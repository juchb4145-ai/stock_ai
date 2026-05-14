from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional


logger = logging.getLogger(__name__)
DUPLICATE_POLICY_KEEP_FIRST = "KEEP_FIRST_SIGNAL_UPDATE_LAST_SEEN"
LIFECYCLE_REGISTERED = "registered"
LIFECYCLE_REFRESHED = "refreshed"
LIFECYCLE_EXPIRED = "expired"
LIFECYCLE_RECREATED_AFTER_TTL = "recreated_after_ttl"


@dataclass
class Candidate:
    code: str
    candidate_id: str = ""
    name: str = ""
    condition_name: str = ""
    condition_index: str = ""
    event_type: str = "I"
    signal_source: str = "HTS_CONDITION_SEARCH"
    detected_at: float = 0.0
    first_detected_at: float = 0.0
    last_detected_at: float = 0.0
    capture_price: int = 0
    first_capture_price: int = 0
    last_capture_price: int = 0
    capture_accum_volume: int = 0
    last_accum_volume: int = 0
    volume_since_capture: int = 0
    trade_value_since_capture: int = 0
    entry_trigger_price: int = 0
    last_price: int = 0
    last_chejan_strength: float = 0.0
    tick_count: int = 0
    recent_low_price: int = 0
    min_price_after_capture: int = 0
    max_price_after_capture: int = 0
    status: str = "WATCHING"
    refresh_count: int = 0
    duplicate_policy: str = DUPLICATE_POLICY_KEEP_FIRST
    last_update_reason: str = "new_candidate"
    last_condition_name: str = ""
    last_signal_source: str = "HTS_CONDITION_SEARCH"
    meta: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self):
        if not self.candidate_id:
            self.candidate_id = uuid.uuid4().hex
        if self.first_detected_at <= 0:
            self.first_detected_at = float(self.detected_at or time.time())
        if self.detected_at <= 0:
            self.detected_at = float(self.first_detected_at)
        if self.last_detected_at <= 0:
            self.last_detected_at = float(self.first_detected_at)
        if self.first_capture_price <= 0 and self.capture_price > 0:
            self.first_capture_price = int(self.capture_price)
        if self.last_capture_price <= 0 and self.capture_price > 0:
            self.last_capture_price = int(self.capture_price)
        if self.min_price_after_capture <= 0 and self.capture_price > 0:
            self.min_price_after_capture = int(self.capture_price)
        if self.max_price_after_capture <= 0 and self.capture_price > 0:
            self.max_price_after_capture = int(self.capture_price)
        if not self.last_condition_name:
            self.last_condition_name = self.condition_name
        if not self.last_signal_source:
            self.last_signal_source = self.signal_source

    def on_tick(
        self,
        *,
        price: int,
        chejan_strength: float = 0.0,
        accum_volume: int = 0,
        volume_delta: int = 0,
        trade_value: int = 0,
        entry_trigger_price: int = 0,
    ) -> bool:
        if price <= 0:
            return False
        self.last_price = int(price)
        self.last_chejan_strength = float(chejan_strength or 0.0)
        self.tick_count += 1
        accum = int(accum_volume or 0)
        if volume_delta <= 0 and self.last_accum_volume > 0 and accum > self.last_accum_volume:
            volume_delta = accum - self.last_accum_volume
        if volume_delta > 0:
            self.volume_since_capture += int(volume_delta)
            self.trade_value_since_capture += int(trade_value or (int(volume_delta) * int(price)))
        if accum > 0:
            self.last_accum_volume = accum
        first_capture = self.capture_price <= 0
        if first_capture:
            self.capture_price = int(price)
            if self.first_capture_price <= 0:
                self.first_capture_price = int(price)
            self.last_capture_price = int(price)
            self.capture_accum_volume = accum
            self.last_accum_volume = accum
            self.entry_trigger_price = int(entry_trigger_price or 0)
            self.recent_low_price = int(price)
            self.min_price_after_capture = int(price)
            self.max_price_after_capture = int(price)
        else:
            self.recent_low_price = min(self.recent_low_price or int(price), int(price))
            self.min_price_after_capture = min(
                self.min_price_after_capture or int(price),
                int(price),
            )
            self.max_price_after_capture = max(
                self.max_price_after_capture or int(price),
                int(price),
            )
        return first_capture

    def age_seconds(self, now: Optional[float] = None) -> float:
        ts = time.time() if now is None else float(now)
        first_detected = float(self.first_detected_at or self.detected_at or ts)
        return max(0.0, ts - first_detected)

    def is_expired(self, *, now: Optional[float] = None, expiry_seconds: int = 0) -> bool:
        if expiry_seconds <= 0:
            return False
        return self.age_seconds(now) > expiry_seconds

    @property
    def strategy_name(self) -> str:
        return str(self.meta.get("strategy_name", "") or "")


class CandidateRegistry:
    def __init__(
        self,
        *,
        signal_source: str = "HTS_CONDITION_SEARCH",
        candidate_expiry_seconds: int = 0,
    ):
        self.signal_source = signal_source
        self.candidate_expiry_seconds = int(candidate_expiry_seconds or 0)
        self._candidates: Dict[str, Candidate] = {}

    def register_detection(
        self,
        *,
        code: str,
        name: str = "",
        condition_name: str = "",
        condition_index: str = "",
        event_type: str = "I",
        detected_at: Optional[float] = None,
        capture_price: int = 0,
        capture_accum_volume: int = 0,
        signal_source: str = "",
        expiry_seconds: Optional[int] = None,
        meta: Optional[Dict[str, object]] = None,
    ) -> Candidate:
        candidate = self._candidates.get(code)
        now = time.time() if detected_at is None else float(detected_at)
        source = signal_source or self.signal_source
        ttl = self.candidate_expiry_seconds if expiry_seconds is None else int(expiry_seconds or 0)
        old_candidate = None
        if candidate is not None and ttl > 0 and candidate.is_expired(now=now, expiry_seconds=ttl):
            old_candidate = candidate
            self._candidates.pop(code, None)
            candidate = None
        if candidate is None:
            candidate = Candidate(
                code=code,
                name=name,
                condition_name=condition_name,
                condition_index=str(condition_index or ""),
                event_type=event_type or "I",
                signal_source=source,
                detected_at=now,
                first_detected_at=now,
                last_detected_at=now,
                capture_price=int(capture_price or 0),
                first_capture_price=int(capture_price or 0),
                last_capture_price=int(capture_price or 0),
                capture_accum_volume=int(capture_accum_volume or 0),
                recent_low_price=int(capture_price or 0),
                min_price_after_capture=int(capture_price or 0),
                max_price_after_capture=int(capture_price or 0),
                last_condition_name=condition_name,
                last_signal_source=source,
                meta=dict(meta or {}),
            )
            self._candidates[code] = candidate
            if old_candidate is not None:
                self._log_recreated_after_ttl(old_candidate, candidate, now, ttl)
            else:
                self._log_registered(candidate, now, ttl)
        else:
            candidate.name = name or candidate.name
            if not candidate.condition_name:
                candidate.condition_name = condition_name
            candidate.last_detected_at = now
            candidate.last_condition_name = condition_name or candidate.last_condition_name
            candidate.last_signal_source = source
            candidate.condition_index = str(condition_index or candidate.condition_index)
            candidate.event_type = event_type or candidate.event_type
            candidate.refresh_count += 1
            candidate.last_update_reason = "same_symbol_within_ttl"
            last_capture = int(capture_price or 0)
            if last_capture > 0:
                if candidate.first_capture_price <= 0:
                    candidate.first_capture_price = last_capture
                    if candidate.capture_price <= 0:
                        candidate.capture_price = last_capture
                candidate.last_capture_price = last_capture
            if capture_accum_volume:
                candidate.meta["last_capture_accum_volume"] = int(capture_accum_volume or 0)
            if meta:
                candidate.meta.update(meta)
            self._log_duplicate_refresh(candidate, now, ttl)
        return candidate

    def _base_log_payload(
        self,
        candidate: Candidate,
        now: float,
        ttl: int,
        *,
        event: str,
        lifecycle_state: str,
        extra: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        payload = {
            "event": event,
            "candidate_id": candidate.candidate_id,
            "symbol": candidate.code,
            "symbol_name": candidate.name,
            "condition_name": candidate.condition_name,
            "strategy_name": candidate.strategy_name,
            "signal_source": candidate.signal_source,
            "first_detected_at": candidate.first_detected_at,
            "last_detected_at": candidate.last_detected_at,
            "first_capture_price": candidate.first_capture_price or None,
            "last_capture_price": candidate.last_capture_price or None,
            "capture_price": candidate.capture_price or None,
            "min_price_after_capture": candidate.min_price_after_capture or None,
            "max_price_after_capture": candidate.max_price_after_capture or None,
            "refresh_count": candidate.refresh_count,
            "candidate_age_sec": candidate.age_seconds(now),
            "ttl_sec": int(ttl or 0),
            "duplicate_policy": candidate.duplicate_policy,
            "lifecycle_state": lifecycle_state,
            "last_condition_name": candidate.last_condition_name,
            "last_signal_source": candidate.last_signal_source,
        }
        for key in (
            "candidate_role",
            "time_policy_reason",
            "entry_allowed",
            "capture_allowed",
            "manage_allowed",
            "analysis_allowed",
        ):
            if key in candidate.meta:
                payload[key] = candidate.meta.get(key)
        if extra:
            payload.update(extra)
        return payload

    def _lifecycle_summary_payload(
        self,
        candidate: Candidate,
        now: float,
        ttl: int,
        *,
        final_block_reason: str = "",
    ) -> Dict[str, object]:
        capture = int(candidate.capture_price or candidate.first_capture_price or 0)
        min_price = int(candidate.min_price_after_capture or candidate.recent_low_price or 0)
        max_price = int(candidate.max_price_after_capture or candidate.last_price or 0)
        max_pullback_pct = (
            (capture - min_price) / capture
            if capture > 0 and min_price > 0 and min_price < capture
            else 0.0
        )
        max_return_pct = (
            max_price / capture - 1
            if capture > 0 and max_price > 0
            else 0.0
        )
        meta = candidate.meta or {}
        return self._base_log_payload(
            candidate,
            now,
            ttl,
            event="candidate_lifecycle_summary",
            lifecycle_state=LIFECYCLE_EXPIRED,
            extra={
                "first_detected_at": candidate.first_detected_at,
                "last_detected_at": candidate.last_detected_at,
                "capture_price": capture or None,
                "min_price_after_capture": min_price or None,
                "max_price_after_capture": max_price or None,
                "max_pullback_pct": max_pullback_pct,
                "max_return_pct": max_return_pct,
                "time_policy_block_count": int(meta.get("time_policy_block_count", 0) or 0),
                "missing_data_count": int(meta.get("missing_data_count", 0) or 0),
                "final_block_reason": final_block_reason
                or str(meta.get("final_block_reason", "") or ""),
                "would_buy_under_relaxed_rules": bool(
                    meta.get("would_buy_under_relaxed_rules", False)
                ),
            },
        )

    def _log_payload(self, label: str, payload: Dict[str, object]) -> None:
        logger.info(
            "[%s] %s",
            label,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        )

    def _log_registered(self, candidate: Candidate, now: float, ttl: int) -> None:
        self._log_payload(
            "candidate_registered",
            self._base_log_payload(
                candidate,
                now,
                ttl,
                event="candidate_registered",
                lifecycle_state=LIFECYCLE_REGISTERED,
                extra={"reason": "new_candidate"},
            ),
        )

    def _log_duplicate_refresh(self, candidate: Candidate, now: float, ttl: int) -> None:
        self._log_payload(
            "candidate_duplicate_refresh",
            self._base_log_payload(
                candidate,
                now,
                ttl,
                event="candidate_duplicate_refresh",
                lifecycle_state=LIFECYCLE_REFRESHED,
                extra={"reason": "same_symbol_within_ttl"},
            ),
        )

    def _log_expired(self, candidate: Candidate, now: float, ttl: int) -> None:
        self._log_payload(
            "candidate_expired",
            self._base_log_payload(
                candidate,
                now,
                ttl,
                event="candidate_expired",
                lifecycle_state=LIFECYCLE_EXPIRED,
                extra={"reason": "candidate_ttl_expired"},
            ),
        )
        self._log_payload(
            "candidate_lifecycle_summary",
            self._lifecycle_summary_payload(candidate, now, ttl),
        )

    def _log_recreated_after_ttl(
        self,
        old_candidate: Candidate,
        new_candidate: Candidate,
        now: float,
        ttl: int,
    ) -> None:
        self._log_payload(
            "candidate_recreated_after_ttl",
            self._base_log_payload(
                new_candidate,
                now,
                ttl,
                event="candidate_recreated_after_ttl",
                lifecycle_state=LIFECYCLE_RECREATED_AFTER_TTL,
                extra={
                    "old_candidate_id": old_candidate.candidate_id,
                    "old_first_detected_at": old_candidate.first_detected_at,
                    "old_last_detected_at": old_candidate.last_detected_at,
                    "old_candidate_age_sec": old_candidate.age_seconds(now),
                    "reason": "same_symbol_after_ttl",
                },
            ),
        )

    def get(self, code: str) -> Optional[Candidate]:
        return self._candidates.get(code)

    def on_tick(
        self,
        code: str,
        *,
        price: int,
        chejan_strength: float = 0.0,
        accum_volume: int = 0,
        volume_delta: int = 0,
        trade_value: int = 0,
        entry_trigger_price: int = 0,
    ) -> bool:
        candidate = self._candidates.get(code)
        if candidate is None:
            return False
        return candidate.on_tick(
            price=price,
            chejan_strength=chejan_strength,
            accum_volume=accum_volume,
            volume_delta=volume_delta,
            trade_value=trade_value,
            entry_trigger_price=entry_trigger_price,
        )

    def record_gate_result(
        self,
        code: str,
        *,
        reason_code: str = "",
        blocked_by: str = "",
        would_buy_under_relaxed_rules: bool = False,
    ) -> None:
        candidate = self._candidates.get(code)
        if candidate is None:
            return
        reason = str(reason_code or "").strip()
        blocked = str(blocked_by or "").strip().lower()
        if reason:
            candidate.meta["final_block_reason"] = reason
        reason_l = reason.lower()
        if "time" in blocked or "time_policy" in blocked or reason in {
            "ALLOW_MANAGE_ONLY",
            "BLOCK_AFTER_ENTRY_CUTOFF",
            "TOO_LATE_FOR_ENTRY_WINDOW",
        }:
            candidate.meta["time_policy_block_count"] = int(
                candidate.meta.get("time_policy_block_count", 0) or 0
            ) + 1
        if "missing" in reason_l or "invalid" in reason_l:
            candidate.meta["missing_data_count"] = int(
                candidate.meta.get("missing_data_count", 0) or 0
            ) + 1
        if would_buy_under_relaxed_rules:
            candidate.meta["would_buy_under_relaxed_rules"] = True

    def remove(self, code: str) -> Optional[Candidate]:
        return self._candidates.pop(code, None)

    def codes(self):
        return set(self._candidates.keys())

    def expire(self, *, now: Optional[float] = None, expiry_seconds: int = 0):
        expired = []
        for code, candidate in list(self._candidates.items()):
            if candidate.is_expired(now=now, expiry_seconds=expiry_seconds):
                expired_candidate = self._candidates.pop(code)
                expired.append(expired_candidate)
                self._log_expired(
                    expired_candidate,
                    time.time() if now is None else float(now),
                    int(expiry_seconds or self.candidate_expiry_seconds or 0),
                )
        return expired
