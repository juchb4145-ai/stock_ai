from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional


logger = logging.getLogger(__name__)
DUPLICATE_POLICY_KEEP_FIRST = "KEEP_FIRST_SIGNAL_UPDATE_LAST_SEEN"


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
        else:
            self.recent_low_price = min(self.recent_low_price or int(price), int(price))
        return first_capture

    def age_seconds(self, now: Optional[float] = None) -> float:
        ts = time.time() if now is None else float(now)
        first_detected = float(self.first_detected_at or self.detected_at or ts)
        return max(0.0, ts - first_detected)

    def is_expired(self, *, now: Optional[float] = None, expiry_seconds: int = 0) -> bool:
        if expiry_seconds <= 0:
            return False
        return self.age_seconds(now) > expiry_seconds


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
        if candidate is not None and ttl > 0 and candidate.is_expired(now=now, expiry_seconds=ttl):
            logger.info(
                "[candidate_recreated_after_ttl] %s",
                json.dumps(
                    {
                        "event": "candidate_recreated_after_ttl",
                        "symbol": code,
                        "old_candidate_id": candidate.candidate_id,
                        "candidate_age_sec": candidate.age_seconds(now),
                        "ttl_seconds": ttl,
                        "reason": "same_symbol_after_ttl",
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            )
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
                last_condition_name=condition_name,
                last_signal_source=source,
                meta=dict(meta or {}),
            )
            self._candidates[code] = candidate
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
            self._log_duplicate_refresh(candidate, now)
        return candidate

    def _log_duplicate_refresh(self, candidate: Candidate, now: float) -> None:
        logger.info(
            "[candidate_duplicate_refresh] %s",
            json.dumps(
                {
                    "event": "candidate_duplicate_refresh",
                    "symbol": candidate.code,
                    "candidate_id": candidate.candidate_id,
                    "first_detected_at": candidate.first_detected_at,
                    "last_detected_at": candidate.last_detected_at,
                    "first_capture_price": candidate.first_capture_price or None,
                    "last_capture_price": candidate.last_capture_price or None,
                    "refresh_count": candidate.refresh_count,
                    "candidate_age_sec": candidate.age_seconds(now),
                    "duplicate_policy": candidate.duplicate_policy,
                    "reason": "same_symbol_within_ttl",
                    "condition_name": candidate.condition_name,
                    "last_condition_name": candidate.last_condition_name,
                    "strategy_name": candidate.meta.get("strategy_name", ""),
                    "last_signal_source": candidate.last_signal_source,
                },
                ensure_ascii=False,
                sort_keys=True,
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

    def remove(self, code: str) -> Optional[Candidate]:
        return self._candidates.pop(code, None)

    def codes(self):
        return set(self._candidates.keys())

    def expire(self, *, now: Optional[float] = None, expiry_seconds: int = 0):
        expired = []
        for code, candidate in list(self._candidates.items()):
            if candidate.is_expired(now=now, expiry_seconds=expiry_seconds):
                expired.append(self._candidates.pop(code))
        return expired
