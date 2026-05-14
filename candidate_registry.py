from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from trade_config import TRADE_CONFIG


logger = logging.getLogger(__name__)
DUPLICATE_POLICY_KEEP_FIRST = "KEEP_FIRST_SIGNAL_UPDATE_LAST_SEEN"
LIFECYCLE_REGISTERED = "registered"
LIFECYCLE_REFRESHED = "refreshed"
LIFECYCLE_EXPIRED = "expired"
LIFECYCLE_RECREATED_AFTER_TTL = "recreated_after_ttl"
CONDITION_COMBO_QUANT_ONLY = "QUANT_ONLY"
CONDITION_COMBO_DANTE_ONLY = "DANTE_ONLY"
CONDITION_COMBO_QUANT_AND_DANTE = "QUANT_AND_DANTE"
CONDITION_SCORE_BONUS_VALUE = 1.0
CONDITION_COMBO_META_FIELDS = (
    "primary_condition_name",
    "bonus_condition_name",
    "quant_detected",
    "dante_detected",
    "condition_combo",
    "condition_score_bonus",
    "first_condition_name",
    "last_condition_name",
    "first_condition_detected_at",
    "bonus_condition_detected_at",
    "time_between_conditions_sec",
)
LEADER_META_FIELDS = (
    "trade_value_since_capture",
    "turnover_speed_per_min",
    "volume_ratio_1m",
    "volume_ratio_5m",
    "turnover_rank_market",
    "turnover_rank_sector",
    "leader_score",
)


def _clamp_ratio(value: float, full_value: float) -> float:
    if full_value <= 0:
        return 0.0
    return max(0.0, min(float(value or 0.0) / float(full_value), 1.0))


def _rank_score(rank: int, ranked_count: int) -> float:
    rank = int(rank or 0)
    ranked_count = int(ranked_count or 0)
    if rank <= 0 or ranked_count <= 0:
        return 0.0
    if ranked_count <= 1:
        return 1.0
    return max(0.0, min(1.0, 1.0 - ((rank - 1) / max(ranked_count - 1, 1))))


def _condition_combo_score(condition_combo: str) -> float:
    combo = str(condition_combo or "").upper()
    if combo == CONDITION_COMBO_QUANT_AND_DANTE:
        return 1.0
    if combo == CONDITION_COMBO_QUANT_ONLY:
        return 0.45
    return 0.0


def calculate_leader_score(
    *,
    turnover_speed_per_min: float = 0.0,
    volume_ratio_1m: float = 0.0,
    volume_ratio_5m: float = 0.0,
    trade_value_since_capture: float = 0.0,
    turnover_rank_market: int = 0,
    ranked_count: int = 0,
    condition_combo: str = "",
    vwap_support_ok: bool = False,
    chejan_strength: float = 0.0,
    opening_phase: bool = False,
    config=TRADE_CONFIG,
) -> float:
    """Score whether a candidate is a morning turnover leader.

    Sector rank is intentionally left outside the formula until reliable sector
    grouping is available. ``turnover_rank_market`` is the current fallback.
    """

    turnover_full = float(getattr(config, "leader_score_turnover_speed_full", 200_000_000.0) or 200_000_000.0)
    trade_value_full = float(getattr(config, "leader_score_trade_value_full", 500_000_000.0) or 500_000_000.0)
    volume_ratio_full = float(getattr(config, "leader_score_volume_ratio_full", 2.0) or 2.0)
    chejan_full = float(getattr(config, "leader_score_chejan_full", 200.0) or 200.0)

    turnover_component = _clamp_ratio(float(turnover_speed_per_min or 0.0), turnover_full)
    trade_value_component = _clamp_ratio(float(trade_value_since_capture or 0.0), trade_value_full)
    volume_component = _clamp_ratio(
        float(volume_ratio_1m if opening_phase else max(volume_ratio_5m or 0.0, volume_ratio_1m or 0.0)),
        volume_ratio_full,
    )
    rank_component = _rank_score(turnover_rank_market, ranked_count)
    combo_component = _condition_combo_score(condition_combo)
    vwap_component = 1.0 if vwap_support_ok else 0.0
    chejan_component = _clamp_ratio(float(chejan_strength or 0.0), chejan_full)

    if opening_phase:
        weights = {
            "turnover": 30.0,
            "rank": 20.0,
            "trade_value": 15.0,
            "volume": 15.0,
            "combo": 10.0,
            "vwap": 5.0,
            "chejan": 5.0,
        }
    else:
        weights = {
            "turnover": 20.0,
            "rank": 10.0,
            "trade_value": 20.0,
            "volume": 15.0,
            "combo": 10.0,
            "vwap": 15.0,
            "chejan": 10.0,
        }
    score = (
        turnover_component * weights["turnover"]
        + rank_component * weights["rank"]
        + trade_value_component * weights["trade_value"]
        + volume_component * weights["volume"]
        + combo_component * weights["combo"]
        + vwap_component * weights["vwap"]
        + chejan_component * weights["chejan"]
    )
    return round(max(0.0, min(score, 100.0)), 2)


def candidate_leader_priority(candidate: "Candidate") -> Tuple[int, float, int, float]:
    meta = candidate.meta or {}
    combo = str(meta.get("condition_combo", "") or "").upper()
    combo_rank = {
        CONDITION_COMBO_QUANT_AND_DANTE: 0,
        CONDITION_COMBO_QUANT_ONLY: 1,
        CONDITION_COMBO_DANTE_ONLY: 2,
    }.get(combo, 3)
    rank = int(candidate.turnover_rank_market or meta.get("turnover_rank_market", 0) or 0)
    return (
        combo_rank,
        -float(candidate.leader_score or meta.get("leader_score", 0.0) or 0.0),
        rank if rank > 0 else 999_999,
        float(candidate.first_detected_at or candidate.detected_at or 0.0),
    )


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
    turnover_speed_per_min: float = 0.0
    volume_ratio_1m: float = 0.0
    volume_ratio_5m: float = 0.0
    turnover_rank_market: int = 0
    turnover_rank_sector: int = 0
    leader_score: float = 0.0
    entry_trigger_price: int = 0
    last_price: int = 0
    last_chejan_strength: float = 0.0
    tick_count: int = 0
    recent_low_price: int = 0
    min_price_after_capture: int = 0
    max_price_after_capture: int = 0
    high_since_capture: int = 0
    low_after_high: int = 0
    pullback_from_high_pct: float = 0.0
    rebound_from_low_pct: float = 0.0
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
        if self.high_since_capture <= 0 and self.max_price_after_capture > 0:
            self.high_since_capture = int(self.max_price_after_capture)
        if not self.last_condition_name:
            self.last_condition_name = self.condition_name
        if not self.last_signal_source:
            self.last_signal_source = self.signal_source

    def _refresh_pullback_metrics(self, price: int) -> None:
        high = int(self.high_since_capture or self.max_price_after_capture or 0)
        low = int(self.low_after_high or 0)
        if high > 0 and price > 0 and high > self.capture_price:
            self.pullback_from_high_pct = max((high - int(price)) / high, 0.0)
        else:
            self.pullback_from_high_pct = 0.0
        if low > 0 and price > 0:
            self.rebound_from_low_pct = max(int(price) / low - 1, 0.0)
        else:
            self.rebound_from_low_pct = 0.0

    def update_leader_metrics(
        self,
        *,
        trade_value_since_capture: Optional[int] = None,
        turnover_speed_per_min: Optional[float] = None,
        volume_ratio_1m: Optional[float] = None,
        volume_ratio_5m: Optional[float] = None,
        turnover_rank_market: Optional[int] = None,
        turnover_rank_sector: Optional[int] = None,
        leader_score: Optional[float] = None,
    ) -> None:
        if trade_value_since_capture is not None:
            self.trade_value_since_capture = int(max(0, int(trade_value_since_capture or 0)))
        if turnover_speed_per_min is not None:
            self.turnover_speed_per_min = float(max(0.0, float(turnover_speed_per_min or 0.0)))
        if volume_ratio_1m is not None:
            self.volume_ratio_1m = float(max(0.0, float(volume_ratio_1m or 0.0)))
        if volume_ratio_5m is not None:
            self.volume_ratio_5m = float(max(0.0, float(volume_ratio_5m or 0.0)))
        if turnover_rank_market is not None:
            self.turnover_rank_market = int(max(0, int(turnover_rank_market or 0)))
        if turnover_rank_sector is not None:
            self.turnover_rank_sector = int(max(0, int(turnover_rank_sector or 0)))
        if leader_score is not None:
            self.leader_score = float(max(0.0, min(float(leader_score or 0.0), 100.0)))
        for field_name in LEADER_META_FIELDS:
            self.meta[field_name] = getattr(self, field_name)

    def on_tick(
        self,
        *,
        price: int,
        chejan_strength: float = 0.0,
        accum_volume: int = 0,
        volume_delta: int = 0,
        trade_value: int = 0,
        entry_trigger_price: int = 0,
        turnover_speed_per_min: Optional[float] = None,
        volume_ratio_1m: Optional[float] = None,
        volume_ratio_5m: Optional[float] = None,
        turnover_rank_market: Optional[int] = None,
        turnover_rank_sector: Optional[int] = None,
        leader_score: Optional[float] = None,
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
            self.high_since_capture = int(price)
            self.low_after_high = 0
        else:
            previous_high = int(self.high_since_capture or self.max_price_after_capture or self.capture_price or 0)
            self.recent_low_price = min(self.recent_low_price or int(price), int(price))
            self.min_price_after_capture = min(
                self.min_price_after_capture or int(price),
                int(price),
            )
            self.max_price_after_capture = max(
                self.max_price_after_capture or int(price),
                int(price),
            )
            self.high_since_capture = max(
                self.high_since_capture or self.max_price_after_capture or int(price),
                self.max_price_after_capture,
                int(price),
            )
            if int(price) > previous_high:
                self.low_after_high = 0
            elif self.high_since_capture > self.capture_price and int(price) < self.high_since_capture:
                self.low_after_high = min(self.low_after_high or int(price), int(price))
        self._refresh_pullback_metrics(int(price))
        self.update_leader_metrics(
            turnover_speed_per_min=turnover_speed_per_min,
            volume_ratio_1m=volume_ratio_1m,
            volume_ratio_5m=volume_ratio_5m,
            turnover_rank_market=turnover_rank_market,
            turnover_rank_sector=turnover_rank_sector,
            leader_score=leader_score,
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
        primary_condition_name: str = "",
        bonus_condition_name: str = "",
        condition_score_bonus_value: float = CONDITION_SCORE_BONUS_VALUE,
    ):
        self.signal_source = signal_source
        self.candidate_expiry_seconds = int(candidate_expiry_seconds or 0)
        self.primary_condition_name = str(
            primary_condition_name
            or getattr(TRADE_CONFIG, "primary_condition_name", "")
            or getattr(TRADE_CONFIG, "condition_name", "")
            or ""
        )
        self.bonus_condition_name = str(
            bonus_condition_name
            or getattr(TRADE_CONFIG, "bonus_condition_name", "")
            or getattr(TRADE_CONFIG, "legacy_condition_name", "")
            or ""
        )
        self.condition_score_bonus_value = float(condition_score_bonus_value or 0.0)
        self._candidates: Dict[str, Candidate] = {}

    @staticmethod
    def _normalize_condition_name(condition_name: str) -> str:
        return str(condition_name or "").strip()

    def is_primary_condition(self, condition_name: str) -> bool:
        name = self._normalize_condition_name(condition_name)
        aliases = {
            self._normalize_condition_name(self.primary_condition_name),
            self._normalize_condition_name(getattr(TRADE_CONFIG, "condition_name", "")),
        }
        aliases.discard("")
        return bool(name and name in aliases)

    def is_bonus_condition(self, condition_name: str) -> bool:
        name = self._normalize_condition_name(condition_name)
        aliases = {
            self._normalize_condition_name(self.bonus_condition_name),
            self._normalize_condition_name(getattr(TRADE_CONFIG, "legacy_condition_name", "")),
        }
        aliases.discard("")
        return bool(name and name in aliases)

    def condition_role(self, condition_name: str) -> str:
        if self.is_primary_condition(condition_name):
            return "primary"
        if self.is_bonus_condition(condition_name):
            return "bonus"
        return "unknown"

    def _apply_condition_combo_meta(
        self,
        candidate: Candidate,
        *,
        condition_name: str,
        detected_at: float,
    ) -> None:
        name = self._normalize_condition_name(condition_name)
        if not name:
            return
        is_primary = self.is_primary_condition(name)
        is_bonus = self.is_bonus_condition(name)
        if not is_primary and not is_bonus:
            candidate.meta.setdefault("primary_condition_name", self.primary_condition_name)
            candidate.meta.setdefault("bonus_condition_name", self.bonus_condition_name)
            candidate.meta.setdefault("last_condition_name", name)
            return

        meta = candidate.meta
        meta["primary_condition_name"] = self.primary_condition_name
        meta["bonus_condition_name"] = self.bonus_condition_name
        if not meta.get("first_condition_name"):
            meta["first_condition_name"] = name
        if not meta.get("first_condition_detected_at"):
            meta["first_condition_detected_at"] = float(detected_at or time.time())
        meta["last_condition_name"] = name

        if is_primary:
            meta["quant_detected"] = True
            meta.setdefault("primary_condition_detected_at", float(detected_at or time.time()))
        else:
            meta["quant_detected"] = bool(meta.get("quant_detected", False))

        if is_bonus:
            meta["dante_detected"] = True
            if not meta.get("bonus_condition_detected_at"):
                meta["bonus_condition_detected_at"] = float(detected_at or time.time())
        else:
            meta["dante_detected"] = bool(meta.get("dante_detected", False))

        quant_detected = bool(meta.get("quant_detected", False))
        dante_detected = bool(meta.get("dante_detected", False))
        if quant_detected and dante_detected:
            meta["condition_combo"] = CONDITION_COMBO_QUANT_AND_DANTE
        elif quant_detected:
            meta["condition_combo"] = CONDITION_COMBO_QUANT_ONLY
        elif dante_detected:
            meta["condition_combo"] = CONDITION_COMBO_DANTE_ONLY
        else:
            meta["condition_combo"] = ""

        first_ts = float(meta.get("first_condition_detected_at", 0.0) or 0.0)
        primary_ts = float(meta.get("primary_condition_detected_at", 0.0) or 0.0)
        bonus_ts = float(meta.get("bonus_condition_detected_at", 0.0) or 0.0)
        if quant_detected and dante_detected:
            other_ts = primary_ts if is_bonus else bonus_ts
            if other_ts > 0:
                meta["time_between_conditions_sec"] = abs(float(detected_at) - other_ts)
            elif first_ts > 0:
                meta["time_between_conditions_sec"] = abs(float(detected_at) - first_ts)
        else:
            meta["time_between_conditions_sec"] = 0.0
        meta["condition_score_bonus"] = (
            self.condition_score_bonus_value if dante_detected else 0.0
        )

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
                high_since_capture=int(capture_price or 0),
                last_condition_name=condition_name,
                last_signal_source=source,
                meta=dict(meta or {}),
            )
            self._apply_condition_combo_meta(
                candidate,
                condition_name=condition_name,
                detected_at=now,
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
            self._apply_condition_combo_meta(
                candidate,
                condition_name=condition_name,
                detected_at=now,
            )
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
            "recent_low_price": candidate.recent_low_price or None,
            "high_since_capture": candidate.high_since_capture or candidate.max_price_after_capture or None,
            "low_after_high": candidate.low_after_high or None,
            "pullback_from_high_pct": candidate.pullback_from_high_pct,
            "rebound_from_low_pct": candidate.rebound_from_low_pct,
            "trade_value_since_capture": candidate.trade_value_since_capture,
            "turnover_speed_per_min": candidate.turnover_speed_per_min,
            "volume_ratio_1m": candidate.volume_ratio_1m,
            "volume_ratio_5m": candidate.volume_ratio_5m,
            "turnover_rank_market": candidate.turnover_rank_market,
            "turnover_rank_sector": candidate.turnover_rank_sector,
            "leader_score": candidate.leader_score,
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
            *CONDITION_COMBO_META_FIELDS,
            *LEADER_META_FIELDS,
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
        high_since = int(candidate.high_since_capture or max_price or 0)
        low_after_high = int(candidate.low_after_high or 0)
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
                "recent_low_price": candidate.recent_low_price or None,
                "high_since_capture": high_since or None,
                "low_after_high": low_after_high or None,
                "pullback_from_high_pct": candidate.pullback_from_high_pct,
                "rebound_from_low_pct": candidate.rebound_from_low_pct,
                "trade_value_since_capture": candidate.trade_value_since_capture,
                "turnover_speed_per_min": candidate.turnover_speed_per_min,
                "volume_ratio_1m": candidate.volume_ratio_1m,
                "volume_ratio_5m": candidate.volume_ratio_5m,
                "turnover_rank_market": candidate.turnover_rank_market,
                "turnover_rank_sector": candidate.turnover_rank_sector,
                "leader_score": candidate.leader_score,
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
        turnover_speed_per_min: Optional[float] = None,
        volume_ratio_1m: Optional[float] = None,
        volume_ratio_5m: Optional[float] = None,
        turnover_rank_market: Optional[int] = None,
        turnover_rank_sector: Optional[int] = None,
        leader_score: Optional[float] = None,
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
            turnover_speed_per_min=turnover_speed_per_min,
            volume_ratio_1m=volume_ratio_1m,
            volume_ratio_5m=volume_ratio_5m,
            turnover_rank_market=turnover_rank_market,
            turnover_rank_sector=turnover_rank_sector,
            leader_score=leader_score,
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

    def ranked_candidates(self, *, include_analysis: bool = False) -> List[Candidate]:
        candidates = list(self._candidates.values())
        if not include_analysis:
            candidates = [
                candidate
                for candidate in candidates
                if (candidate.meta or {}).get("candidate_role") != "analysis_only"
                and (candidate.meta or {}).get("condition_combo") != CONDITION_COMBO_DANTE_ONLY
            ]
        return sorted(candidates, key=candidate_leader_priority)

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
