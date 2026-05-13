from __future__ import annotations

import json
import logging
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Sequence

from bars import MinuteBar
from candidate_registry import Candidate
from time_policy import TimeDecision, TimePolicy
from trade_config import TRADE_CONFIG, TradeConfig


logger = logging.getLogger(__name__)


class EntryDecision(str, Enum):
    BUY = "BUY"
    WAIT_PULLBACK = "WAIT_PULLBACK"
    WAIT_DATA = "WAIT_DATA"
    BLOCK_CHASE = "BLOCK_CHASE"
    REJECT = "REJECT"


@dataclass(frozen=True)
class MomentumDecision:
    action: EntryDecision
    reason: str
    reason_code: str
    chase_risk_score: float = 0.0
    entry_ratio: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class MomentumContext:
    candidate: Candidate
    current_price: int
    chejan_strength: float
    spread_rate: Optional[float] = None
    volume_ratio: Optional[float] = None
    turnover_speed_per_min: Optional[float] = None
    intraday_vwap: Optional[float] = None
    minute_bars: Sequence[MinuteBar] = ()
    prior_high: Optional[int] = None
    prior_low: Optional[int] = None
    short_ma: Optional[float] = None
    high_since_capture: int = 0
    upper_wick_ratio: Optional[float] = None
    signal_candle_range_pct: Optional[float] = None
    position_in_signal_candle_pct: Optional[float] = None
    recent_low_to_current_pct: Optional[float] = None
    tick_count: int = 0
    now_ts: float = 0.0


class MomentumBreakoutStrategy:
    """Second-pass gate for HTS condition-search candidates.

    HTS condition search only discovers candidates. Missing risk data must not
    be interpreted as zero risk; when required market data is unavailable, this
    gate waits instead of opening BUY.
    """

    def __init__(
        self,
        config: TradeConfig = TRADE_CONFIG,
        time_policy: Optional[TimePolicy] = None,
    ):
        self.config = config
        self.time_policy = time_policy or TimePolicy(config)

    def evaluate(self, ctx: MomentumContext) -> MomentumDecision:
        decision = self._evaluate(ctx)
        self._log_decision(ctx, decision)
        return decision

    def _evaluate(self, ctx: MomentumContext) -> MomentumDecision:
        c = ctx.candidate
        now_ts = ctx.now_ts or time.time()
        age = c.age_seconds(now_ts)
        metrics = self._metrics(ctx, age)

        if bool(self.config.time_policy_enabled):
            time_decision = self.time_policy.evaluate_entry(
                now=now_ts,
                log=False,
                context={
                    "symbol": c.code,
                    "candidate_id": getattr(c, "candidate_id", ""),
                    "strategy_name": self.config.strategy_name,
                },
            )
            metrics["time_decision_id"] = getattr(time_decision, "time_decision_id", "")
            metrics["time_policy_reason_code"] = time_decision.reason_code
            metrics["time_policy_config_version"] = time_decision.config_version
            if not time_decision.allowed:
                return self._time_policy_block(time_decision, metrics)

        if c.is_expired(now=now_ts, expiry_seconds=self.config.candidate_expiry_seconds):
            return MomentumDecision(
                EntryDecision.REJECT,
                "candidate expired age={:.0f}s limit={}s".format(
                    age, self.config.candidate_expiry_seconds
                ),
                "CANDIDATE_EXPIRED",
                metrics=metrics,
            )
        if ctx.current_price <= 0 or c.capture_price <= 0:
            return MomentumDecision(
                EntryDecision.WAIT_PULLBACK,
                "waiting for current/capture price",
                "WAIT_PRICE_CAPTURE",
                metrics=metrics,
            )
        if age < self.config.min_candidate_age_seconds:
            return MomentumDecision(
                EntryDecision.WAIT_PULLBACK,
                "candidate observation age {:.0f}/{}s".format(
                    age, self.config.min_candidate_age_seconds
                ),
                "WAIT_MIN_AGE",
                metrics=metrics,
            )
        if ctx.tick_count < self.config.min_candidate_ticks:
            return MomentumDecision(
                EntryDecision.WAIT_PULLBACK,
                "realtime tick count {}/{}".format(
                    ctx.tick_count, self.config.min_candidate_ticks
                ),
                "WAIT_MIN_TICKS",
                metrics=metrics,
            )

        data_decision = self._missing_or_invalid_market_data(ctx, metrics)
        if data_decision is not None:
            return data_decision

        spread_rate = float(ctx.spread_rate or 0.0)
        volume_ratio = float(ctx.volume_ratio or 0.0)
        turnover_speed = float(ctx.turnover_speed_per_min or 0.0)
        upper_wick_ratio = float(ctx.upper_wick_ratio or 0.0)
        intraday_vwap = float(ctx.intraday_vwap or 0.0)

        if spread_rate < 0 or spread_rate > self.config.max_spread_pct:
            return MomentumDecision(
                EntryDecision.REJECT,
                "spread too wide {:.2%} > {:.2%}".format(
                    spread_rate, self.config.max_spread_pct
                ),
                "REJECT_SPREAD",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )
        if ctx.chejan_strength < self.config.min_trade_strength:
            return MomentumDecision(
                EntryDecision.REJECT,
                "trade strength weak {:.1f} < {:.1f}".format(
                    ctx.chejan_strength, self.config.min_trade_strength
                ),
                "REJECT_TRADE_STRENGTH",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )
        if (
            self.config.require_vwap_filter
            and intraday_vwap > 0
            and ctx.current_price < intraday_vwap
        ):
            return MomentumDecision(
                EntryDecision.REJECT,
                "VWAP recovery failed current={} vwap={:.0f}".format(
                    ctx.current_price, intraday_vwap
                ),
                "REJECT_VWAP_LOST",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )
        if volume_ratio < self.config.min_volume_ratio:
            return MomentumDecision(
                EntryDecision.REJECT,
                "weak_volume_ratio {:.2f} < {:.2f}".format(
                    volume_ratio, self.config.min_volume_ratio
                ),
                "WEAK_VOLUME_RATIO",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )
        if turnover_speed < self.config.min_turnover_speed_per_min:
            return MomentumDecision(
                EntryDecision.REJECT,
                "weak_turnover_speed {:.0f} < {:.0f}".format(
                    turnover_speed, self.config.min_turnover_speed_per_min
                ),
                "WEAK_TURNOVER_SPEED",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )
        if metrics["chase_distance_pct"] > self.config.max_chase_distance_pct:
            return MomentumDecision(
                EntryDecision.BLOCK_CHASE,
                "chase distance too high {:.2%} > {:.2%}".format(
                    metrics["chase_distance_pct"],
                    self.config.max_chase_distance_pct,
                ),
                "BLOCK_CHASE_DISTANCE",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )
        if upper_wick_ratio > self.config.max_upper_wick_ratio:
            return MomentumDecision(
                EntryDecision.BLOCK_CHASE,
                "upper wick pressure {:.0%} > {:.0%}".format(
                    upper_wick_ratio, self.config.max_upper_wick_ratio
                ),
                "BLOCK_UPPER_WICK",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )

        hard_chase = self._hard_chase_block(ctx, metrics)
        if hard_chase is not None:
            return hard_chase

        if metrics["chase_risk_score"] > self.config.max_chase_risk_score:
            return MomentumDecision(
                EntryDecision.BLOCK_CHASE,
                "chase risk score {:.1f} > {:.1f}".format(
                    metrics["chase_risk_score"], self.config.max_chase_risk_score
                ),
                "BLOCK_CHASE_SCORE",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )

        bullish_reversal = self._bullish_reversal(ctx.minute_bars)
        pullback_pct = metrics["pullback_pct"]
        if pullback_pct >= self.config.pullback_entry_pct:
            if self.config.require_one_min_reversal and not bullish_reversal:
                return MomentumDecision(
                    EntryDecision.WAIT_PULLBACK,
                    "waiting for bullish one-minute reversal",
                    "WAIT_ONE_MIN_REVERSAL",
                    chase_risk_score=metrics["chase_risk_score"],
                    metrics=metrics,
                )
            return MomentumDecision(
                EntryDecision.BUY,
                "pullback entry confirmed pullback={:.2%} strength={:.1f} volume_ratio={:.2f}".format(
                    pullback_pct, ctx.chejan_strength, volume_ratio
                ),
                "BUY_PULLBACK_CONFIRMED",
                chase_risk_score=metrics["chase_risk_score"],
                entry_ratio=1.0,
                metrics=metrics,
            )

        if (
            self.config.allow_breakout_probe_entry
            and ctx.current_price >= c.capture_price
            and bullish_reversal
            and metrics["chase_risk_score"] <= self.config.max_chase_risk_score * 0.7
        ):
            return MomentumDecision(
                EntryDecision.BUY,
                "breakout continuation probe strength={:.1f} volume_ratio={:.2f}".format(
                    ctx.chejan_strength, volume_ratio
                ),
                "BUY_BREAKOUT_PROBE",
                chase_risk_score=metrics["chase_risk_score"],
                entry_ratio=self.config.breakout_probe_entry_ratio,
                metrics=metrics,
            )

        return MomentumDecision(
            EntryDecision.WAIT_PULLBACK,
            "waiting for first pullback pullback={:.2%} < {:.2%}".format(
                pullback_pct, self.config.pullback_entry_pct
            ),
            "WAIT_PULLBACK",
            chase_risk_score=metrics["chase_risk_score"],
            metrics=metrics,
        )

    def _missing_or_invalid_market_data(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
    ) -> Optional[MomentumDecision]:
        if not self.config.reject_missing_market_data:
            return None

        if self.config.require_volume_ratio:
            volume_ratio = ctx.volume_ratio
            if self._missing_number(volume_ratio):
                return self._wait_data("missing_volume_ratio", "MISSING_VOLUME_RATIO", metrics)
            if float(volume_ratio) <= 0:
                return self._wait_data("invalid_volume_ratio", "INVALID_VOLUME_RATIO", metrics)

        if self.config.require_turnover_speed:
            turnover_speed = ctx.turnover_speed_per_min
            if self._missing_number(turnover_speed):
                return self._wait_data("missing_turnover_speed", "MISSING_TURNOVER_SPEED", metrics)
            if float(turnover_speed) <= 0:
                return self._wait_data("invalid_turnover_speed", "INVALID_TURNOVER_SPEED", metrics)

        if self._missing_number(ctx.spread_rate):
            return self._wait_data("missing_spread_rate", "MISSING_SPREAD_RATE", metrics)
        if float(ctx.spread_rate or 0.0) < 0:
            return self._wait_data("invalid_spread_rate", "INVALID_SPREAD_RATE", metrics)
        if self.config.require_candle_cache_for_buy and not ctx.minute_bars:
            return self._wait_data("missing_candle_cache", "MISSING_CANDLE_CACHE", metrics)
        if self.config.require_candle_cache_for_buy and self._missing_number(ctx.upper_wick_ratio):
            return self._wait_data("missing_wick_risk", "MISSING_WICK_RISK", metrics)
        if self.config.require_vwap_filter and self._missing_number(ctx.intraday_vwap):
            return self._wait_data("missing_vwap", "MISSING_VWAP", metrics)
        if self.config.require_candle_cache_for_buy and metrics.get("prior_high", 0.0) <= 0:
            return self._wait_data("missing_prior_high", "MISSING_PRIOR_HIGH", metrics)
        if self.config.require_candle_cache_for_buy and metrics.get("prior_low", 0.0) <= 0:
            return self._wait_data("missing_prior_low", "MISSING_PRIOR_LOW", metrics)
        if self.config.require_candle_cache_for_buy and self._missing_number(ctx.short_ma):
            return self._wait_data("missing_short_ma", "MISSING_SHORT_MA", metrics)
        if self.config.require_candle_cache_for_buy and self._missing_number(ctx.signal_candle_range_pct):
            return self._wait_data(
                "missing_signal_candle_range",
                "MISSING_SIGNAL_CANDLE_RANGE",
                metrics,
            )
        if self.config.require_candle_cache_for_buy and self._missing_number(ctx.position_in_signal_candle_pct):
            return self._wait_data(
                "missing_signal_candle_position",
                "MISSING_SIGNAL_CANDLE_POSITION",
                metrics,
            )
        return None

    def _hard_chase_block(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
    ) -> Optional[MomentumDecision]:
        candle_range = metrics.get("signal_candle_range_pct", 0.0)
        candle_pos = metrics.get("position_in_signal_candle_pct", 0.0)
        recent_low_to_current = metrics.get("recent_low_to_current_pct", 0.0)
        vwap_extension = metrics.get("extension_from_vwap_pct", 0.0)
        short_ma_extension = metrics.get("extension_from_short_ma_pct", 0.0)
        pullback_pct = metrics.get("pullback_pct", 0.0)

        if candle_range > self.config.max_signal_candle_range_pct:
            return MomentumDecision(
                EntryDecision.BLOCK_CHASE,
                "signal candle range too large {:.2%} > {:.2%}".format(
                    candle_range, self.config.max_signal_candle_range_pct
                ),
                "BLOCK_SIGNAL_CANDLE_RANGE",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )
        if (
            candle_pos >= self.config.max_position_in_signal_candle_pct
            and pullback_pct < self.config.min_pullback_after_signal_pct
        ):
            return MomentumDecision(
                EntryDecision.BLOCK_CHASE,
                "signal candle top chase position={:.0%} pullback={:.2%}".format(
                    candle_pos, pullback_pct
                ),
                "BLOCK_SIGNAL_CANDLE_TOP",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )
        if recent_low_to_current > self.config.max_recent_low_to_current_pct:
            return MomentumDecision(
                EntryDecision.BLOCK_CHASE,
                "recent low extension too high {:.2%} > {:.2%}".format(
                    recent_low_to_current, self.config.max_recent_low_to_current_pct
                ),
                "BLOCK_RECENT_LOW_EXTENSION",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )
        if vwap_extension > self.config.max_extension_from_vwap_pct:
            return MomentumDecision(
                EntryDecision.BLOCK_CHASE,
                "VWAP extension too high {:.2%} > {:.2%}".format(
                    vwap_extension, self.config.max_extension_from_vwap_pct
                ),
                "BLOCK_VWAP_EXTENSION",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )
        if short_ma_extension > self.config.max_extension_from_short_ma_pct:
            return MomentumDecision(
                EntryDecision.BLOCK_CHASE,
                "short MA extension too high {:.2%} > {:.2%}".format(
                    short_ma_extension, self.config.max_extension_from_short_ma_pct
                ),
                "BLOCK_SHORT_MA_EXTENSION",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )
        return None

    def _metrics(self, ctx: MomentumContext, age: float) -> Dict[str, float]:
        c = ctx.candidate
        prior_high = self._prior_high(ctx)
        prior_low = self._prior_low(ctx)
        pullback_pct = (
            (c.capture_price - ctx.current_price) / c.capture_price
            if c.capture_price > 0
            else 0.0
        )
        capture_chase_pct = (
            ctx.current_price / c.capture_price - 1
            if c.capture_price > 0 and ctx.current_price > c.capture_price
            else 0.0
        )
        prior_high_chase_pct = (
            ctx.current_price / prior_high - 1
            if prior_high > 0 and ctx.current_price > prior_high
            else 0.0
        )
        recent_low_to_current_pct = (
            float(ctx.recent_low_to_current_pct)
            if not self._missing_number(ctx.recent_low_to_current_pct)
            else (
                ctx.current_price / prior_low - 1
                if prior_low > 0 and ctx.current_price > prior_low
                else 0.0
            )
        )
        extension_from_vwap_pct = (
            ctx.current_price / float(ctx.intraday_vwap) - 1
            if not self._missing_number(ctx.intraday_vwap)
            and float(ctx.intraday_vwap) > 0
            and ctx.current_price > float(ctx.intraday_vwap)
            else 0.0
        )
        extension_from_short_ma_pct = (
            ctx.current_price / float(ctx.short_ma) - 1
            if not self._missing_number(ctx.short_ma)
            and float(ctx.short_ma) > 0
            and ctx.current_price > float(ctx.short_ma)
            else 0.0
        )
        signal_candle_range_pct = (
            float(ctx.signal_candle_range_pct)
            if not self._missing_number(ctx.signal_candle_range_pct)
            else 0.0
        )
        position_in_signal_candle_pct = (
            float(ctx.position_in_signal_candle_pct)
            if not self._missing_number(ctx.position_in_signal_candle_pct)
            else 0.0
        )
        upper_wick_ratio = (
            float(ctx.upper_wick_ratio)
            if not self._missing_number(ctx.upper_wick_ratio)
            else 0.0
        )
        spread_rate = (
            float(ctx.spread_rate)
            if not self._missing_number(ctx.spread_rate)
            else 0.0
        )
        volume_ratio = (
            float(ctx.volume_ratio)
            if not self._missing_number(ctx.volume_ratio)
            else 0.0
        )
        turnover_speed = (
            float(ctx.turnover_speed_per_min)
            if not self._missing_number(ctx.turnover_speed_per_min)
            else 0.0
        )

        risk = 0.0
        if self.config.max_spread_pct > 0:
            risk += min(max(spread_rate, 0.0) / self.config.max_spread_pct, 2.0) * 20.0
        if self.config.max_chase_distance_pct > 0:
            risk += min(max(capture_chase_pct, prior_high_chase_pct) / self.config.max_chase_distance_pct, 2.0) * 35.0
        if self.config.max_upper_wick_ratio > 0:
            risk += min(max(upper_wick_ratio, 0.0) / self.config.max_upper_wick_ratio, 2.0) * 25.0
        if self.config.require_vwap_filter and not self._missing_number(ctx.intraday_vwap):
            vwap = float(ctx.intraday_vwap or 0.0)
            if vwap > 0 and ctx.current_price < vwap:
                risk += 30.0
        if self.config.require_one_min_reversal and not self._bullish_reversal(ctx.minute_bars):
            risk += 15.0
        if signal_candle_range_pct > self.config.max_signal_candle_range_pct:
            risk += 20.0
        if position_in_signal_candle_pct > self.config.max_position_in_signal_candle_pct:
            risk += 15.0
        if recent_low_to_current_pct > self.config.max_recent_low_to_current_pct:
            risk += 20.0

        return {
            "age_seconds": age,
            "pullback_pct": pullback_pct,
            "chase_distance_pct": max(capture_chase_pct, prior_high_chase_pct),
            "capture_chase_pct": capture_chase_pct,
            "prior_high_chase_pct": prior_high_chase_pct,
            "prior_high": float(prior_high),
            "prior_low": float(prior_low),
            "spread_rate": spread_rate,
            "volume_ratio": volume_ratio,
            "turnover_speed_per_min": turnover_speed,
            "upper_wick_ratio": upper_wick_ratio,
            "signal_candle_range_pct": signal_candle_range_pct,
            "position_in_signal_candle_pct": position_in_signal_candle_pct,
            "recent_low_to_current_pct": recent_low_to_current_pct,
            "extension_from_vwap_pct": extension_from_vwap_pct,
            "extension_from_short_ma_pct": extension_from_short_ma_pct,
            "chase_risk_score": min(risk, 100.0),
        }

    @staticmethod
    def _wait_data(
        reason: str,
        reason_code: str,
        metrics: Dict[str, float],
    ) -> MomentumDecision:
        return MomentumDecision(
            EntryDecision.WAIT_DATA,
            reason,
            reason_code,
            chase_risk_score=metrics.get("chase_risk_score", 0.0),
            metrics=metrics,
        )

    @staticmethod
    def _time_policy_block(
        decision: TimeDecision,
        metrics: Dict[str, float],
    ) -> MomentumDecision:
        blocked_metrics = dict(metrics or {})
        blocked_metrics["time_policy_allowed"] = 0.0
        blocked_metrics["time_decision_id"] = getattr(decision, "time_decision_id", "")
        blocked_metrics["time_policy_reason_code"] = decision.reason_code
        blocked_metrics["time_policy_config_version"] = decision.config_version
        wait_codes = {
            "BLOCK_PRE_OPEN",
            "BLOCK_OPENING_STABILIZATION",
            "ALLOW_MANAGE_ONLY",
        }
        action = (
            EntryDecision.WAIT_PULLBACK
            if decision.reason_code in wait_codes and decision.next_allowed_time
            else EntryDecision.REJECT
        )
        return MomentumDecision(
            action,
            "time policy blocked entry action={} session={} next={}".format(
                decision.action,
                decision.session,
                decision.next_allowed_time or "",
            ),
            decision.reason_code,
            chase_risk_score=blocked_metrics.get("chase_risk_score", 0.0),
            metrics=blocked_metrics,
        )

    def _log_decision(self, ctx: MomentumContext, decision: MomentumDecision) -> None:
        c = ctx.candidate
        metrics = decision.metrics or {}
        vwap = self._optional_number(ctx.intraday_vwap)
        current_price = int(ctx.current_price or 0)
        one_min_reversal = self._bullish_reversal(ctx.minute_bars)
        event = {
            "event": "momentum_entry_decision",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": c.code,
            "symbol_name": c.name,
            "candidate_id": getattr(c, "candidate_id", ""),
            "condition_name": c.condition_name,
            "strategy_name": self.config.strategy_name,
            "decision": decision.action.value,
            "reason_code": decision.reason_code.lower(),
            "reason_detail": decision.reason,
            "chase_risk_score": self._optional_number(decision.chase_risk_score),
            "volume_ratio": self._optional_number(ctx.volume_ratio),
            "turnover_speed_per_min": self._optional_number(ctx.turnover_speed_per_min),
            "trade_strength": self._optional_number(ctx.chejan_strength),
            "spread_rate": self._optional_number(ctx.spread_rate),
            "vwap": vwap,
            "current_price": current_price or None,
            "capture_price": int(c.capture_price or 0) or None,
            "first_capture_price": int(getattr(c, "first_capture_price", 0) or c.capture_price or 0) or None,
            "last_capture_price": int(getattr(c, "last_capture_price", 0) or c.capture_price or 0) or None,
            "candidate_age_sec": self._optional_number(metrics.get("age_seconds")),
            "high_distance_pct": self._optional_number(metrics.get("chase_distance_pct")),
            "prior_high": self._positive_optional_number(metrics.get("prior_high")),
            "upper_wick_ratio": self._optional_number(ctx.upper_wick_ratio),
            "pullback_pct": self._optional_number(metrics.get("pullback_pct")),
            "candle_cache_available": bool(ctx.minute_bars),
            "orderbook_available": not self._missing_number(ctx.spread_rate),
            "market_data_available": self._market_data_available(ctx, metrics),
            "is_above_vwap": None if vwap is None or current_price <= 0 else current_price >= vwap,
            "one_min_reversal": one_min_reversal,
            "recent_low_to_current_pct": self._optional_number(ctx.recent_low_to_current_pct),
            "extension_from_vwap_pct": self._optional_number(metrics.get("extension_from_vwap_pct")),
            "extension_from_short_ma_pct": self._optional_number(metrics.get("extension_from_short_ma_pct")),
            "entry_type": self._entry_type(decision),
            "blocked_by": self._blocked_by(decision),
            "time_decision_id": metrics.get("time_decision_id"),
            "time_policy_reason_code": metrics.get("time_policy_reason_code"),
            "time_policy_config_version": metrics.get("time_policy_config_version"),
        }
        logger.info(
            "[momentum_entry_decision] %s",
            json.dumps(event, ensure_ascii=False, sort_keys=True, default=str),
        )

    @staticmethod
    def _entry_type(decision: MomentumDecision) -> Optional[str]:
        if decision.reason_code == "BUY_PULLBACK_CONFIRMED":
            return "pullback"
        if decision.reason_code == "BUY_BREAKOUT_PROBE":
            return "breakout_probe"
        return None

    @staticmethod
    def _blocked_by(decision: MomentumDecision) -> Optional[str]:
        if decision.action in {EntryDecision.BLOCK_CHASE, EntryDecision.REJECT, EntryDecision.WAIT_DATA}:
            return decision.reason_code.lower()
        return None

    def _market_data_available(self, ctx: MomentumContext, metrics: Dict[str, float]) -> bool:
        if self.config.require_volume_ratio and (
            self._missing_number(ctx.volume_ratio) or float(ctx.volume_ratio or 0.0) <= 0
        ):
            return False
        if self.config.require_turnover_speed and (
            self._missing_number(ctx.turnover_speed_per_min)
            or float(ctx.turnover_speed_per_min or 0.0) <= 0
        ):
            return False
        if self._missing_number(ctx.spread_rate) or float(ctx.spread_rate or 0.0) < 0:
            return False
        if self.config.require_vwap_filter and (
            self._missing_number(ctx.intraday_vwap) or float(ctx.intraday_vwap or 0.0) <= 0
        ):
            return False
        if self.config.require_candle_cache_for_buy:
            if not ctx.minute_bars or self._missing_number(ctx.upper_wick_ratio):
                return False
            if metrics.get("prior_high", 0.0) <= 0 or metrics.get("prior_low", 0.0) <= 0:
                return False
            if self._missing_number(ctx.short_ma):
                return False
            if self._missing_number(ctx.signal_candle_range_pct):
                return False
            if self._missing_number(ctx.position_in_signal_candle_pct):
                return False
        return True

    @classmethod
    def _optional_number(cls, value: Optional[float]) -> Optional[float]:
        if cls._missing_number(value):
            return None
        return float(value)

    @classmethod
    def _positive_optional_number(cls, value: Optional[float]) -> Optional[float]:
        number = cls._optional_number(value)
        if number is None or number <= 0:
            return None
        return number

    @staticmethod
    def _missing_number(value: Optional[float]) -> bool:
        if value is None:
            return True
        try:
            return bool(math.isnan(float(value)))
        except (TypeError, ValueError):
            return True

    def _prior_high(self, ctx: MomentumContext) -> int:
        if ctx.prior_high is not None and ctx.prior_high > 0:
            return int(ctx.prior_high)
        bars = list(ctx.minute_bars or [])
        if self.config.exclude_current_bar_from_high_distance and bars:
            bars = bars[:-1]
        if self.config.high_distance_lookback_bars > 0:
            bars = bars[-self.config.high_distance_lookback_bars :]
        highs = [int(getattr(bar, "high", 0) or 0) for bar in bars]
        highs = [value for value in highs if value > 0]
        return max(highs) if highs else 0

    def _prior_low(self, ctx: MomentumContext) -> int:
        if ctx.prior_low is not None and ctx.prior_low > 0:
            return int(ctx.prior_low)
        bars = list(ctx.minute_bars or [])
        if self.config.exclude_current_bar_from_high_distance and bars:
            bars = bars[:-1]
        if self.config.high_distance_lookback_bars > 0:
            bars = bars[-self.config.high_distance_lookback_bars :]
        lows = [int(getattr(bar, "low", 0) or 0) for bar in bars]
        lows = [value for value in lows if value > 0]
        return min(lows) if lows else 0

    @staticmethod
    def _bullish_reversal(minute_bars: Sequence[MinuteBar]) -> bool:
        if not minute_bars:
            return False
        cur = minute_bars[-1]
        if getattr(cur, "close", 0) <= getattr(cur, "open", 0):
            return False
        if len(minute_bars) == 1:
            return True
        prev = minute_bars[-2]
        return (
            getattr(prev, "close", 0) < getattr(prev, "open", 0)
            or getattr(cur, "close", 0) >= getattr(prev, "high", 0)
            or getattr(cur, "low", 0) >= getattr(prev, "low", 0)
        )
