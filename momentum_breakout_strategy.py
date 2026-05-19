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
from time_policy import TimeDecision, TimePolicy, parse_clock
from trade_config import TRADE_CONFIG, TradeConfig


logger = logging.getLogger(__name__)

ENTRY_TYPE_BREAKOUT_SMALL = "BREAKOUT_SMALL"
ENTRY_TYPE_PULLBACK_RECLAIM = "PULLBACK_RECLAIM"
ENTRY_TYPE_OPENING_RECOVERY_PROBE = "OPENING_RECOVERY_PROBE"
ENTRY_TYPE_MIDDAY_VWAP_RECLAIM = "MIDDAY_VWAP_RECLAIM"
ENTRY_TYPE_AFTERNOON_SECOND_WAVE = "AFTERNOON_SECOND_WAVE"
ENTRY_TYPE_CLOSING_STRENGTH = "CLOSING_STRENGTH"
ENTRY_TYPE_TREND_CONTINUATION = "TREND_CONTINUATION"
ENTRY_TYPE_WEAK_VOLUME_RELIEF = "WEAK_VOLUME_RELIEF_PAPER_ONLY"


class EntryDecision(str, Enum):
    BUY = "BUY"
    WAIT_PULLBACK = "WAIT_PULLBACK"
    WAIT_RECLAIM_VWAP = "WAIT_RECLAIM_VWAP"
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
    entry_type: str = ""
    position_size_multiplier: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class MomentumContext:
    candidate: Candidate
    current_price: int
    chejan_strength: float
    spread_rate: Optional[float] = None
    volume_ratio: Optional[float] = None
    turnover_speed_per_min: Optional[float] = None
    trade_value_since_capture: int = 0
    volume_ratio_1m: Optional[float] = None
    volume_ratio_5m: Optional[float] = None
    turnover_rank_market: int = 0
    turnover_rank_sector: int = 0
    leader_score: float = 0.0
    intraday_vwap: Optional[float] = None
    minute_bars: Sequence[MinuteBar] = ()
    prior_high: Optional[int] = None
    prior_low: Optional[int] = None
    short_ma: Optional[float] = None
    realtime_day_high: int = 0
    rolling_high_since_capture: int = 0
    high_since_capture: int = 0
    low_after_high: int = 0
    pullback_from_high_pct: float = 0.0
    rebound_from_low_pct: float = 0.0
    one_min_reversal: Optional[bool] = None
    upper_wick_ratio: Optional[float] = None
    signal_candle_range_pct: Optional[float] = None
    position_in_signal_candle_pct: Optional[float] = None
    recent_low_to_current_pct: Optional[float] = None
    tick_count: int = 0
    now_ts: float = 0.0
    was_below_vwap: bool = False
    short_reclaim_high: int = 0
    sector_context: Optional[object] = None
    theme_context: Optional[object] = None


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

    def analysis_snapshot(
        self,
        ctx: MomentumContext,
        *,
        reason_code: str,
        reason_detail: str,
        blocked_by: str = "time_policy",
    ) -> MomentumDecision:
        """Emit a non-orderable momentum snapshot for analysis-only candidates."""
        age = ctx.candidate.age_seconds(ctx.now_ts or time.time())
        metrics = self._metrics(ctx, age)
        metrics["analysis_only"] = 1.0
        metrics["analysis_snapshot"] = 1.0
        metrics["orderable"] = 0.0
        metrics["blocked_by"] = blocked_by
        metrics["time_policy_reason_code"] = str(reason_code or "")
        decision = MomentumDecision(
            EntryDecision.REJECT,
            reason_detail,
            str(reason_code or "ANALYSIS_ONLY"),
            chase_risk_score=metrics.get("chase_risk_score", 0.0),
            entry_type="ANALYSIS_ONLY",
            metrics=metrics,
        )
        self._log_decision(ctx, decision)
        return decision

    def _evaluate(self, ctx: MomentumContext) -> MomentumDecision:
        c = ctx.candidate
        now_ts = ctx.now_ts or time.time()
        age = c.age_seconds(now_ts)
        metrics = self._metrics(ctx, age)
        metrics["paper_strategy_type"] = self.time_policy.paper_strategy_type(now=now_ts)
        late_a_grade_candidate = self._late_a_grade_candidate(ctx, metrics)
        min_observation_sec = self._min_observation_seconds(late_a_grade_candidate)
        metrics["min_observation_sec"] = float(min_observation_sec)
        metrics["late_a_grade_candidate"] = 1.0 if late_a_grade_candidate else 0.0
        deferred_time_policy_block: Optional[MomentumDecision] = None

        if bool(self.config.time_policy_enabled):
            time_decision = self.time_policy.evaluate_entry(
                now=now_ts,
                log=False,
                context={
                    "symbol": c.code,
                    "candidate_id": getattr(c, "candidate_id", ""),
                    "strategy_name": self.config.strategy_name,
                    "late_a_grade_candidate": late_a_grade_candidate,
                    "entry_type": ENTRY_TYPE_BREAKOUT_SMALL if late_a_grade_candidate else "",
                    "candidate_grade": "A" if late_a_grade_candidate else "",
                },
            )
            metrics["time_decision_id"] = getattr(time_decision, "time_decision_id", "")
            metrics["time_policy_reason_code"] = time_decision.reason_code
            metrics["time_policy_config_version"] = time_decision.config_version
            if not time_decision.allowed:
                paper_window_type = self.time_policy.paper_strategy_type(now=now_ts)
                metrics["paper_strategy_type"] = paper_window_type
                if not paper_window_type:
                    return self._time_policy_block(time_decision, metrics)
                deferred_time_policy_block = self._time_policy_block(time_decision, metrics)
            cutoff_block = self._entry_cutoff_block(ctx, metrics, age, min_observation_sec)
            if cutoff_block is not None:
                paper_window_type = self.time_policy.paper_strategy_type(now=now_ts)
                metrics["paper_strategy_type"] = paper_window_type
                if not paper_window_type:
                    return cutoff_block
                deferred_time_policy_block = cutoff_block

        if c.is_expired(now=now_ts, expiry_seconds=self.config.candidate_expiry_seconds):
            if deferred_time_policy_block is not None:
                return deferred_time_policy_block
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
        if age < min_observation_sec:
            return MomentumDecision(
                EntryDecision.WAIT_PULLBACK,
                "candidate observation age {:.0f}/{}s".format(
                    age, min_observation_sec
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

        leader_decision = self._leader_score_decision(ctx, metrics)
        if leader_decision is not None:
            return leader_decision

        spread_rate = float(ctx.spread_rate or 0.0)
        volume_ratio = float(ctx.volume_ratio or 0.0)
        turnover_speed = float(ctx.turnover_speed_per_min or 0.0)
        upper_wick_ratio = float(ctx.upper_wick_ratio or 0.0)
        intraday_vwap = float(ctx.intraday_vwap or 0.0)
        bullish_reversal = self._bullish_reversal(ctx.minute_bars)
        paper_decision = self._paper_strategy_decision(ctx, metrics, bullish_reversal)
        if paper_decision is not None:
            return paper_decision
        if deferred_time_policy_block is not None:
            return deferred_time_policy_block
        if metrics.get("time_policy_reason_code") == "ALLOW_MIDDAY_ENTRY":
            return MomentumDecision(
                EntryDecision.WAIT_RECLAIM_VWAP,
                "midday live entry is limited to VWAP reclaim setup",
                "WAIT_MIDDAY_VWAP_RECLAIM",
                chase_risk_score=metrics["chase_risk_score"],
                entry_type=ENTRY_TYPE_MIDDAY_VWAP_RECLAIM,
                metrics=metrics,
            )

        if spread_rate < 0 or spread_rate > self.config.max_spread_pct:
            if not self._conditional_spread_relief(ctx, metrics, bullish_reversal):
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
            return self._below_vwap_decision(ctx, metrics)
        reclaim_decision = self._vwap_reclaim_confirmation(ctx, metrics, bullish_reversal)
        if reclaim_decision is not None:
            return reclaim_decision
        flow_decision = self._flow_gate_decision(ctx, metrics)
        if flow_decision is not None:
            return flow_decision
        if (
            metrics["chase_distance_pct"] > self.config.max_chase_distance_pct
            and not bool(metrics.get("first_pullback_ready", 0.0))
        ):
            trend_decision = self._trend_continuation_decision(ctx, metrics)
            if trend_decision is not None:
                return trend_decision
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

        if (
            metrics["chase_risk_score"] > self.config.max_chase_risk_score
            and not bool(metrics.get("first_pullback_ready", 0.0))
        ):
            return MomentumDecision(
                EntryDecision.BLOCK_CHASE,
                "chase risk score {:.1f} > {:.1f}".format(
                    metrics["chase_risk_score"], self.config.max_chase_risk_score
                ),
                "BLOCK_CHASE_SCORE",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )

        pullback_pct = metrics["pullback_pct"]
        if self._breakout_small_ready(ctx, metrics, bullish_reversal):
            probe_metrics = dict(metrics)
            probe_metrics["paper_only_breakout_probe"] = 1.0
            probe_metrics["orderable_live"] = 0.0
            ratio = self._entry_size_multiplier(
                metrics,
                self._breakout_probe_entry_ratio(),
            )
            return MomentumDecision(
                EntryDecision.BUY,
                "breakout small entry strength={:.1f} volume_ratio={:.2f}".format(
                    ctx.chejan_strength, volume_ratio
                ),
                "BUY_BREAKOUT_SMALL",
                chase_risk_score=probe_metrics["chase_risk_score"],
                entry_ratio=ratio,
                entry_type=ENTRY_TYPE_BREAKOUT_SMALL,
                position_size_multiplier=ratio,
                metrics=probe_metrics,
            )

        effective_pullback_pct = float(metrics.get("effective_pullback_entry_pct", self.config.pullback_entry_pct))
        if pullback_pct >= effective_pullback_pct:
            reclaim_high = int(ctx.short_reclaim_high or 0)
            if ctx.was_below_vwap and reclaim_high > 0 and ctx.current_price < reclaim_high:
                return MomentumDecision(
                    EntryDecision.WAIT_RECLAIM_VWAP,
                    "waiting for short reclaim high current={} high={}".format(
                        ctx.current_price,
                        reclaim_high,
                    ),
                    "REJECT_RECLAIM_FAILED",
                    chase_risk_score=metrics["chase_risk_score"],
                    entry_type=ENTRY_TYPE_PULLBACK_RECLAIM,
                    metrics=metrics,
                )
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
                "BUY_PULLBACK_RECLAIM",
                chase_risk_score=metrics["chase_risk_score"],
                entry_ratio=self._entry_size_multiplier(metrics, 1.0),
                entry_type=ENTRY_TYPE_PULLBACK_RECLAIM,
                position_size_multiplier=self._entry_size_multiplier(metrics, 1.0),
                metrics=metrics,
            )

        if (
            self.config.allow_breakout_probe_entry
            and ctx.current_price >= c.capture_price
            and bullish_reversal
            and metrics["chase_risk_score"] <= self.config.max_chase_risk_score * 0.7
        ):
            probe_metrics = dict(metrics)
            probe_metrics["paper_only_breakout_probe"] = 1.0
            probe_metrics["orderable_live"] = 0.0
            ratio = self._entry_size_multiplier(
                probe_metrics,
                self._breakout_probe_entry_ratio(),
            )
            return MomentumDecision(
                EntryDecision.BUY,
                "breakout continuation probe strength={:.1f} volume_ratio={:.2f}".format(
                    ctx.chejan_strength, volume_ratio
                ),
                "BUY_BREAKOUT_SMALL",
                chase_risk_score=probe_metrics["chase_risk_score"],
                entry_ratio=ratio,
                entry_type=ENTRY_TYPE_BREAKOUT_SMALL,
                position_size_multiplier=ratio,
                metrics=probe_metrics,
            )

        return MomentumDecision(
            EntryDecision.WAIT_PULLBACK,
            "waiting for first pullback pullback={:.2%} < {:.2%}".format(
                pullback_pct, effective_pullback_pct
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

    def _below_vwap_decision(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
    ) -> MomentumDecision:
        spread_rate = float(ctx.spread_rate or 0.0)
        recent_rebound = float(metrics.get("recent_low_to_current_pct", 0.0) or 0.0)
        orderbook_available = not self._missing_number(ctx.spread_rate)
        strong_reclaim_flow = (
            ctx.chejan_strength >= float(getattr(self.config, "vwap_reclaim_wait_trade_strength", 180.0) or 180.0)
            and recent_rebound >= float(getattr(self.config, "vwap_reclaim_min_rebound_pct", 0.003) or 0.003)
            and spread_rate <= self.config.max_spread_pct
            and orderbook_available
        )
        blocked_metrics = dict(metrics or {})
        blocked_metrics["was_below_vwap"] = 1.0
        blocked_metrics["vwap_reclaim_candidate"] = 1.0 if strong_reclaim_flow else 0.0
        blocked_metrics["orderbook_available"] = 1.0 if orderbook_available else 0.0
        if strong_reclaim_flow:
            return MomentumDecision(
                EntryDecision.WAIT_RECLAIM_VWAP,
                "below VWAP but flow is strong; wait for reclaim current={} vwap={:.0f}".format(
                    ctx.current_price,
                    float(ctx.intraday_vwap or 0.0),
                ),
                "WAIT_RECLAIM_VWAP",
                chase_risk_score=blocked_metrics.get("chase_risk_score", 0.0),
                entry_type=ENTRY_TYPE_PULLBACK_RECLAIM,
                metrics=blocked_metrics,
            )
        return MomentumDecision(
            EntryDecision.REJECT,
            "below VWAP with weak reclaim flow current={} vwap={:.0f} strength={:.1f}".format(
                ctx.current_price,
                float(ctx.intraday_vwap or 0.0),
                ctx.chejan_strength,
            ),
            "BLOCK_BELOW_VWAP_WEAK_FLOW",
            chase_risk_score=blocked_metrics.get("chase_risk_score", 0.0),
            metrics=blocked_metrics,
        )

    def _conditional_spread_relief(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
        bullish_reversal: bool,
    ) -> bool:
        metrics["spread_gate_relaxed"] = 0.0
        if not bool(getattr(self.config, "conditional_spread_relief_enabled", False)):
            return False
        if ctx.was_below_vwap:
            return False
        spread_rate = float(ctx.spread_rate or 0.0)
        max_conditional = float(
            getattr(self.config, "max_conditional_spread_pct", self.config.max_spread_pct)
            or self.config.max_spread_pct
        )
        if spread_rate <= self.config.max_spread_pct or spread_rate > max_conditional:
            return False
        if ctx.chejan_strength < float(
            getattr(self.config, "conditional_spread_min_trade_strength", 0.0) or 0.0
        ):
            return False
        if float(ctx.volume_ratio or 0.0) < float(
            getattr(self.config, "conditional_spread_min_volume_ratio", 0.0) or 0.0
        ):
            return False
        if metrics.get("pullback_pct", 0.0) < float(
            metrics.get("effective_pullback_entry_pct", self.config.pullback_entry_pct)
        ):
            return False
        if metrics.get("recent_low_to_current_pct", 0.0) < float(
            getattr(self.config, "conditional_spread_min_rebound_pct", 0.0) or 0.0
        ):
            return False
        if self.config.require_one_min_reversal and not bullish_reversal:
            return False

        metrics["spread_gate_relaxed"] = 1.0
        metrics["spread_gate_max_pct"] = max_conditional
        metrics["spread_position_size_multiplier"] = float(
            getattr(self.config, "conditional_spread_position_size_multiplier", 0.25)
            or 0.25
        )
        return True

    def _vwap_reclaim_confirmation(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
        bullish_reversal: bool,
    ) -> Optional[MomentumDecision]:
        if not self.config.require_vwap_filter or not ctx.was_below_vwap:
            return None
        if self._missing_number(ctx.intraday_vwap) or float(ctx.intraday_vwap or 0.0) <= 0:
            return None
        vwap = float(ctx.intraday_vwap or 0.0)
        buffer_pct = max(
            0.0,
            float(getattr(self.config, "vwap_reclaim_confirm_buffer_pct", 0.0) or 0.0),
        )
        reclaim_price = vwap * (1.0 + buffer_pct)
        blocked_metrics = dict(metrics or {})
        blocked_metrics["vwap_reclaim_price"] = reclaim_price
        blocked_metrics["vwap_reclaim_confirmed"] = 0.0
        if ctx.current_price < reclaim_price:
            return MomentumDecision(
                EntryDecision.WAIT_RECLAIM_VWAP,
                "waiting for VWAP reclaim confirmation current={} reclaim={:.0f}".format(
                    ctx.current_price,
                    reclaim_price,
                ),
                "WAIT_RECLAIM_VWAP",
                chase_risk_score=blocked_metrics.get("chase_risk_score", 0.0),
                entry_type=ENTRY_TYPE_PULLBACK_RECLAIM,
                metrics=blocked_metrics,
            )
        if self.config.require_one_min_reversal and not bullish_reversal:
            return MomentumDecision(
                EntryDecision.WAIT_RECLAIM_VWAP,
                "waiting for bullish one-minute reversal after VWAP reclaim",
                "WAIT_RECLAIM_VWAP",
                chase_risk_score=blocked_metrics.get("chase_risk_score", 0.0),
                entry_type=ENTRY_TYPE_PULLBACK_RECLAIM,
                metrics=blocked_metrics,
            )
        metrics["vwap_reclaim_price"] = reclaim_price
        metrics["vwap_reclaim_confirmed"] = 1.0
        return None

    def _flow_gate_decision(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
    ) -> Optional[MomentumDecision]:
        volume_ratio = float(ctx.volume_ratio or 0.0)
        turnover_speed = float(ctx.turnover_speed_per_min or 0.0)
        min_turnover = float(self.config.min_turnover_speed_per_min or 0.0)
        strong_strength = float(
            getattr(self.config, "strong_trade_strength_for_volume_relief", 300.0) or 300.0
        )
        mid_strength = float(
            getattr(self.config, "vwap_reclaim_buy_trade_strength", 150.0) or 150.0
        )
        if ctx.chejan_strength >= strong_strength:
            min_volume = float(
                getattr(self.config, "strong_trade_strength_min_volume_ratio", 0.3) or 0.3
            )
            require_both = False
            score_bucket = "strong_strength_volume_relief"
        elif ctx.chejan_strength >= mid_strength:
            min_volume = float(
                getattr(self.config, "vwap_reclaim_min_volume_ratio", 0.8) or 0.8
            )
            require_both = False
            score_bucket = "mid_strength_volume_or_turnover"
        else:
            min_volume = float(self.config.min_volume_ratio or 0.0)
            require_both = bool(self.config.require_turnover_speed)
            score_bucket = "baseline_and"

        volume_ok = (not self.config.require_volume_ratio) or volume_ratio >= min_volume
        turnover_ok = (
            (not self.config.require_turnover_speed)
            or min_turnover <= 0
            or turnover_speed >= min_turnover
        )
        if require_both:
            flow_ok = volume_ok and turnover_ok
        else:
            flow_ok = volume_ok or turnover_ok

        metrics["flow_score_bucket"] = score_bucket
        metrics["volume_gate_min_ratio"] = min_volume
        metrics["volume_gate_relaxed_by_strength"] = 1.0 if min_volume < self.config.min_volume_ratio else 0.0
        metrics["turnover_gate_min_per_min"] = min_turnover
        metrics["flow_gate_volume_ok"] = 1.0 if volume_ok else 0.0
        metrics["flow_gate_turnover_ok"] = 1.0 if turnover_ok else 0.0
        metrics["flow_gate_ok"] = 1.0 if flow_ok else 0.0

        if flow_ok:
            return None
        if bool(metrics.get("first_pullback_ready", 0.0)):
            metrics["flow_score_bucket"] = "first_pullback_leader_turnover_relief"
            metrics["flow_gate_ok"] = 1.0
            metrics["volume_gate_relaxed_by_first_pullback"] = 1.0
            return None
        if self._weak_volume_partial_entry_relief(
            ctx,
            metrics,
            volume_ok=volume_ok,
            turnover_ok=turnover_ok,
        ):
            if metrics.get("weak_volume_paper_only", 0.0) > 0.0:
                ratio = float(metrics.get("weak_volume_position_size_multiplier", 0.25) or 0.25)
                return self._paper_buy(
                    ctx,
                    metrics,
                    reason="weak volume relief paper-only",
                    reason_code="WEAK_VOLUME_RELIEF_PAPER_ONLY",
                    entry_type=ENTRY_TYPE_WEAK_VOLUME_RELIEF,
                    ratio=ratio,
                )
            return None
        if not volume_ok:
            return MomentumDecision(
                EntryDecision.REJECT,
                "weak_volume_ratio {:.2f} < {:.2f} bucket={}".format(
                    volume_ratio,
                    min_volume,
                    score_bucket,
                ),
                "WEAK_VOLUME_RATIO",
                chase_risk_score=metrics["chase_risk_score"],
                metrics=metrics,
            )
        return MomentumDecision(
            EntryDecision.REJECT,
            "weak_turnover_speed {:.0f} < {:.0f} bucket={}".format(
                turnover_speed,
                min_turnover,
                score_bucket,
            ),
            "WEAK_TURNOVER_SPEED",
            chase_risk_score=metrics["chase_risk_score"],
            metrics=metrics,
        )

    def _weak_volume_partial_entry_relief(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
        *,
        volume_ok: bool,
        turnover_ok: bool,
    ) -> bool:
        metrics["weak_volume_partial_relief"] = 0.0
        if volume_ok or not bool(getattr(self.config, "weak_volume_partial_entry_enabled", False)):
            return False
        if ctx.chejan_strength < float(
            getattr(self.config, "weak_volume_partial_min_trade_strength", 0.0) or 0.0
        ):
            return False
        if (
            float(ctx.spread_rate or 0.0) > self.config.max_spread_pct
            and metrics.get("spread_gate_relaxed", 0.0) <= 0.0
        ):
            return False
        volume_ratio = float(ctx.volume_ratio or 0.0)
        min_partial_volume = float(
            getattr(self.config, "weak_volume_partial_min_volume_ratio", 0.0) or 0.0
        )
        if volume_ratio < min_partial_volume and not turnover_ok:
            return False
        if metrics.get("pullback_pct", 0.0) < float(
            metrics.get("effective_pullback_entry_pct", self.config.pullback_entry_pct)
        ):
            return False
        relaxed_paper_only = False
        if metrics.get("recent_low_to_current_pct", 0.0) < float(
            getattr(self.config, "weak_volume_partial_min_rebound_pct", 0.0) or 0.0
        ):
            relaxed_paper_only = (
                float(ctx.chejan_strength or 0.0) >= 130.0
                and float(ctx.turnover_speed_per_min or 0.0) >= 300_000_000.0
                and bool(metrics.get("vwap_support_ok", 0.0))
                and float(ctx.spread_rate or 0.0) <= self.config.max_spread_pct
                and self._after_clock(ctx.now_ts, "09:30:00")
            )
            if not relaxed_paper_only:
                return False

        metrics["flow_score_bucket"] = "weak_volume_partial_pullback"
        metrics["flow_gate_ok"] = 1.0
        metrics["weak_volume_partial_relief"] = 1.0
        metrics["weak_volume_paper_only"] = 1.0 if relaxed_paper_only else 0.0
        metrics["weak_volume_partial_min_ratio"] = min_partial_volume
        metrics["weak_volume_position_size_multiplier"] = float(
            getattr(self.config, "weak_volume_partial_position_size_multiplier", 0.25)
            or 0.25
        )
        return True

    def _after_clock(self, now: float, clock_text: str) -> bool:
        local_dt = self.time_policy._coerce_datetime(now or time.time())
        return local_dt.time().replace(tzinfo=None) >= parse_clock(clock_text)

    @staticmethod
    def _entry_size_multiplier(metrics: Dict[str, float], default: float) -> float:
        multiplier = float(default or 0.0)
        for key in (
            "weak_volume_position_size_multiplier",
            "spread_position_size_multiplier",
        ):
            value = metrics.get(key)
            if value is None:
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if number > 0:
                multiplier = min(multiplier, number)
        return multiplier

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
        if bool(metrics.get("first_pullback_ready", 0.0)):
            metrics["hard_chase_relaxed_by_first_pullback"] = 1.0
            return None

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

    def _paper_strategy_decision(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
        bullish_reversal: bool,
    ) -> Optional[MomentumDecision]:
        strategy_type = str(metrics.get("paper_strategy_type") or "")
        if not strategy_type:
            return None
        if strategy_type == ENTRY_TYPE_OPENING_RECOVERY_PROBE:
            return self._opening_recovery_probe_decision(ctx, metrics, bullish_reversal)
        if strategy_type == ENTRY_TYPE_MIDDAY_VWAP_RECLAIM:
            return self._midday_vwap_reclaim_decision(ctx, metrics, bullish_reversal)
        if strategy_type == ENTRY_TYPE_AFTERNOON_SECOND_WAVE:
            return self._afternoon_second_wave_decision(ctx, metrics, bullish_reversal)
        if strategy_type == "CLOSING_STRENGTH":
            return self._closing_strength_decision(ctx, metrics, bullish_reversal)
        return None

    def _paper_buy(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
        *,
        reason: str,
        reason_code: str,
        entry_type: str,
        ratio: float = 0.25,
    ) -> MomentumDecision:
        paper_metrics = dict(metrics)
        paper_metrics["paper_only_strategy"] = 1.0
        paper_metrics["orderable_live"] = 0.0
        paper_metrics["strategy_type"] = entry_type
        return MomentumDecision(
            EntryDecision.BUY,
            reason,
            reason_code,
            chase_risk_score=paper_metrics.get("chase_risk_score", 0.0),
            entry_ratio=ratio,
            entry_type=entry_type,
            position_size_multiplier=ratio,
            metrics=paper_metrics,
        )

    def _opening_recovery_probe_decision(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
        bullish_reversal: bool,
    ) -> Optional[MomentumDecision]:
        vwap = float(ctx.intraday_vwap or 0.0)
        turnover_ok = float(ctx.turnover_speed_per_min or 0.0) >= 300_000_000.0
        volume_reaccel = float(ctx.volume_ratio_1m or 0.0) >= float(ctx.volume_ratio_5m or 0.0)
        near_capture = (
            ctx.current_price / ctx.candidate.capture_price - 1.0
            if ctx.candidate.capture_price > 0
            else 0.0
        )
        if (
            bool(getattr(self.config, "time_policy_high_mfe_paper_enabled", True))
            and vwap > 0
            and ctx.current_price >= vwap
            and bullish_reversal
            and -0.015 <= near_capture <= 0.040
            and float(ctx.chejan_strength or 0.0) >= 130.0
            and float(ctx.spread_rate or 0.0) <= self.config.max_spread_pct
            and (float(ctx.volume_ratio or 0.0) >= self.config.min_volume_ratio or turnover_ok or volume_reaccel)
        ):
            paper_metrics = dict(metrics)
            paper_metrics["time_policy_high_mfe_paper_candidate"] = 1.0
            return self._paper_buy(
                ctx,
                paper_metrics,
                reason="opening recovery probe paper-only",
                reason_code="OPENING_RECOVERY_PROBE_PAPER_ONLY",
                entry_type=ENTRY_TYPE_OPENING_RECOVERY_PROBE,
                ratio=0.15,
            )
        return None

    def _live_strategy_buy(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
        *,
        reason: str,
        reason_code: str,
        entry_type: str,
        ratio: float,
    ) -> MomentumDecision:
        live_metrics = dict(metrics)
        live_metrics["paper_only_strategy"] = 0.0
        live_metrics["orderable_live"] = 1.0
        live_metrics["strategy_type"] = entry_type
        return MomentumDecision(
            EntryDecision.BUY,
            reason,
            reason_code,
            chase_risk_score=live_metrics.get("chase_risk_score", 0.0),
            entry_ratio=ratio,
            entry_type=entry_type,
            position_size_multiplier=ratio,
            metrics=live_metrics,
        )

    def _midday_vwap_reclaim_decision(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
        bullish_reversal: bool,
    ) -> Optional[MomentumDecision]:
        vwap = float(ctx.intraday_vwap or 0.0)
        turnover_ok = float(ctx.turnover_speed_per_min or 0.0) >= 300_000_000.0
        volume_reaccel = float(ctx.volume_ratio_1m or 0.0) >= float(ctx.volume_ratio_5m or 0.0)
        pulled_back = 0.003 <= float(metrics.get("observed_pullback_from_high_pct", 0.0)) <= 0.06
        if (
            vwap > 0
            and ctx.current_price >= vwap
            and bullish_reversal
            and float(ctx.chejan_strength or 0.0) >= 120.0
            and float(ctx.spread_rate or 0.0) <= self.config.max_spread_pct
            and pulled_back
            and (float(ctx.volume_ratio or 0.0) >= self.config.min_volume_ratio or turnover_ok or volume_reaccel)
        ):
            ratio = max(float(getattr(self.config, "midday_live_entry_ratio", 0.25) or 0.0), 0.0)
            if bool(getattr(self.config, "midday_live_entry_enabled", True)) and ratio > 0:
                return self._live_strategy_buy(
                    ctx,
                    metrics,
                    reason="midday VWAP reclaim live",
                    reason_code="MIDDAY_VWAP_RECLAIM_LIVE",
                    entry_type=ENTRY_TYPE_MIDDAY_VWAP_RECLAIM,
                    ratio=ratio,
                )
            return self._paper_buy(
                ctx,
                metrics,
                reason="midday VWAP reclaim paper-only",
                reason_code="MIDDAY_VWAP_RECLAIM_PAPER_ONLY",
                entry_type=ENTRY_TYPE_MIDDAY_VWAP_RECLAIM,
                ratio=0.25,
            )
        return None

    def _afternoon_second_wave_decision(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
        bullish_reversal: bool,
    ) -> Optional[MomentumDecision]:
        vwap = float(ctx.intraday_vwap or 0.0)
        prior_high = float(metrics.get("prior_high") or 0.0)
        room_to_high = prior_high / float(ctx.current_price or 1) - 1.0 if prior_high > 0 and ctx.current_price > 0 else 0.0
        pullback = float(metrics.get("observed_pullback_from_high_pct", 0.0))
        turnover_ok = float(ctx.turnover_speed_per_min or 0.0) >= 300_000_000.0
        short_ma_ok = self._missing_number(ctx.short_ma) or float(ctx.short_ma or 0.0) <= 0 or ctx.current_price > float(ctx.short_ma or 0.0)
        if (
            vwap > 0
            and ctx.current_price > vwap
            and short_ma_ok
            and 0.01 <= pullback <= 0.06
            and turnover_ok
            and float(ctx.chejan_strength or 0.0) >= 110.0
            and float(ctx.chejan_strength or 0.0) <= 300.0
            and float(ctx.spread_rate or 0.0) <= self.config.max_spread_pct
            and room_to_high >= 0.015
            and bullish_reversal
        ):
            paper_metrics = dict(metrics)
            paper_metrics["stop_policy"] = "VWAP_LOST_OR_PREV_PULLBACK_LOW"
            paper_metrics["take_profit_policy"] = "FIRST_0P8_TO_1P2"
            return self._paper_buy(
                ctx,
                paper_metrics,
                reason="afternoon second wave paper-only",
                reason_code="AFTERNOON_SECOND_WAVE_PAPER_ONLY",
                entry_type=ENTRY_TYPE_AFTERNOON_SECOND_WAVE,
                ratio=0.25,
            )
        return None

    def _closing_strength_decision(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
        bullish_reversal: bool,
    ) -> Optional[MomentumDecision]:
        if (
            float(ctx.intraday_vwap or 0.0) > 0
            and ctx.current_price > float(ctx.intraday_vwap or 0.0)
            and float(ctx.chejan_strength or 0.0) >= 150.0
            and float(ctx.spread_rate or 0.0) <= self.config.max_spread_pct
            and bullish_reversal
        ):
            return self._paper_buy(
                ctx,
                metrics,
                reason="closing strength paper-only",
                reason_code="CLOSING_STRENGTH_PAPER_ONLY",
                entry_type=ENTRY_TYPE_CLOSING_STRENGTH,
                ratio=0.15,
            )
        return None

    def _trend_continuation_decision(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
    ) -> Optional[MomentumDecision]:
        if (
            float(metrics.get("chase_distance_pct", 0.0)) > 0.04
            and float(ctx.chejan_strength or 0.0) >= 150.0
            and float(ctx.intraday_vwap or 0.0) > 0
            and ctx.current_price > float(ctx.intraday_vwap or 0.0)
            and float(ctx.upper_wick_ratio or 0.0) <= 0.25
            and self._bullish_reversal(ctx.minute_bars)
        ):
            return self._paper_buy(
                ctx,
                metrics,
                reason="trend continuation chase candidate paper-only",
                reason_code="TREND_CONTINUATION_PAPER_ONLY",
                entry_type=ENTRY_TYPE_TREND_CONTINUATION,
                ratio=0.15,
            )
        return None

    def _metrics(self, ctx: MomentumContext, age: float) -> Dict[str, float]:
        c = ctx.candidate
        prior_high, prior_high_source = self._prior_high_with_source(ctx)
        prior_low = self._prior_low(ctx)
        observed_pullback_from_high_pct = (
            max((int(ctx.high_since_capture or 0) - ctx.current_price) / int(ctx.high_since_capture or 0), 0.0)
            if int(ctx.high_since_capture or 0) > 0 and ctx.current_price > 0
            else 0.0
        )
        capture_pullback_pct = (
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
        volume_ratio_1m = (
            float(ctx.volume_ratio_1m)
            if not self._missing_number(ctx.volume_ratio_1m)
            else 0.0
        )
        volume_ratio_5m = (
            float(ctx.volume_ratio_5m)
            if not self._missing_number(ctx.volume_ratio_5m)
            else volume_ratio
        )
        turnover_speed = (
            float(ctx.turnover_speed_per_min)
            if not self._missing_number(ctx.turnover_speed_per_min)
            else 0.0
        )
        is_above_vwap = (
            1.0
            if self._missing_number(ctx.intraday_vwap)
            or float(ctx.intraday_vwap or 0.0) <= 0
            or ctx.current_price >= float(ctx.intraday_vwap or 0.0)
            else 0.0
        )
        adaptive_pullback_pct = self._adaptive_pullback_pct(ctx)
        effective_pullback_pct = float(self.config.pullback_entry_pct)
        if bool(getattr(self.config, "adaptive_pullback_enabled", False)) and adaptive_pullback_pct > 0:
            effective_pullback_pct = min(effective_pullback_pct, adaptive_pullback_pct)
        strategy_pullback_basis = (
            int(ctx.high_since_capture or 0)
            if int(ctx.high_since_capture or 0) > int(c.capture_price or 0)
            else int(c.capture_price or 0)
        )
        pullback_pct = (
            observed_pullback_from_high_pct
            if strategy_pullback_basis == int(ctx.high_since_capture or 0)
            and int(ctx.high_since_capture or 0) > int(c.capture_price or 0)
            else capture_pullback_pct
        )
        entry_pullback_eligible = (
            pullback_pct >= effective_pullback_pct
            and pullback_pct <= float(getattr(self.config, "max_pullback_pct", 1.0) or 1.0)
        )
        vwap_support_ok = bool(
            self._missing_number(ctx.intraday_vwap)
            or float(ctx.intraday_vwap or 0.0) <= 0
            or ctx.current_price >= float(ctx.intraday_vwap or 0.0)
        )
        first_pullback_quality = bool(
            entry_pullback_eligible
            and observed_pullback_from_high_pct >= effective_pullback_pct
            and int(ctx.low_after_high or 0) > 0
            and float(ctx.rebound_from_low_pct or 0.0) >= float(getattr(self.config, "rebound_confirm_pct", 0.0) or 0.0)
            and vwap_support_ok
            and float(ctx.leader_score or 0.0) >= 70.0
            and turnover_speed >= 300_000_000.0
            and float(ctx.chejan_strength or 0.0) >= 100.0
        )
        pullback_dry_run = self._pullback_dry_run(c.capture_price, pullback_pct)

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
        if prior_high_source not in {"candle"}:
            risk += 8.0 if prior_high_source in {"rolling_since_capture", "realtime_day_high"} else 14.0

        condition_meta = c.meta or {}
        condition_score_bonus = float(condition_meta.get("condition_score_bonus", 0.0) or 0.0)
        return {
            "age_seconds": age,
            "primary_condition_name": condition_meta.get("primary_condition_name", ""),
            "bonus_condition_name": condition_meta.get("bonus_condition_name", ""),
            "quant_detected": 1.0 if bool(condition_meta.get("quant_detected", False)) else 0.0,
            "dante_detected": 1.0 if bool(condition_meta.get("dante_detected", False)) else 0.0,
            "condition_combo": condition_meta.get("condition_combo", ""),
            "condition_score_bonus": condition_score_bonus,
            "first_condition_name": condition_meta.get("first_condition_name", ""),
            "last_condition_name": condition_meta.get("last_condition_name", ""),
            "first_condition_detected_at": condition_meta.get("first_condition_detected_at", ""),
            "bonus_condition_detected_at": condition_meta.get("bonus_condition_detected_at", ""),
            "time_between_conditions_sec": condition_meta.get("time_between_conditions_sec", ""),
            "pullback_pct": pullback_pct,
            "capture_pullback_pct": capture_pullback_pct,
            "observed_pullback_from_high_pct": observed_pullback_from_high_pct,
            "pullback_from_high_pct": observed_pullback_from_high_pct,
            "strategy_pullback_basis": float(strategy_pullback_basis),
            "entry_pullback_eligible": 1.0 if entry_pullback_eligible else 0.0,
            "first_pullback_ready": 1.0 if first_pullback_quality else 0.0,
            "first_pullback_quality_relief": 1.0 if first_pullback_quality else 0.0,
            "chase_distance_pct": max(capture_chase_pct, prior_high_chase_pct),
            "capture_chase_pct": capture_chase_pct,
            "prior_high_chase_pct": prior_high_chase_pct,
            "prior_high": float(prior_high),
            "prior_high_source": prior_high_source,
            "prior_low": float(prior_low),
            "spread_rate": spread_rate,
            "volume_ratio": volume_ratio,
            "volume_ratio_1m": volume_ratio_1m,
            "volume_ratio_5m": volume_ratio_5m,
            "turnover_speed_per_min": turnover_speed,
            "trade_value_since_capture": float(ctx.trade_value_since_capture or 0),
            "turnover_rank_market": float(ctx.turnover_rank_market or 0),
            "turnover_rank_sector": float(ctx.turnover_rank_sector or 0),
            "leader_score": float(ctx.leader_score or 0.0),
            "sector_regime": getattr(ctx.sector_context, "sector_regime", "") if ctx.sector_context is not None else "",
            "sector_gate_action": getattr(ctx.sector_context, "sector_gate_action", "") if ctx.sector_context is not None else "",
            "theme_regime": getattr(ctx.theme_context, "theme_regime", "") if ctx.theme_context is not None else "",
            "theme_gate_action": getattr(ctx.theme_context, "theme_gate_action", "") if ctx.theme_context is not None else "",
            "is_above_vwap": is_above_vwap,
            "vwap_support_ok": 1.0 if vwap_support_ok else 0.0,
            "upper_wick_ratio": upper_wick_ratio,
            "signal_candle_range_pct": signal_candle_range_pct,
            "position_in_signal_candle_pct": position_in_signal_candle_pct,
            "recent_low_to_current_pct": recent_low_to_current_pct,
            "extension_from_vwap_pct": extension_from_vwap_pct,
            "extension_from_short_ma_pct": extension_from_short_ma_pct,
            "chase_risk_score": min(risk, 100.0),
            "adaptive_pullback_entry_pct": adaptive_pullback_pct,
            "effective_pullback_entry_pct": effective_pullback_pct,
            "pullback_dry_run": pullback_dry_run,
            "was_below_vwap": 1.0 if ctx.was_below_vwap else 0.0,
            "short_reclaim_high": float(ctx.short_reclaim_high or 0),
            "prior_high_fallback_used": 0.0 if prior_high_source == "candle" else 1.0,
        }

    @staticmethod
    def _hhmmss_value(value: str, default: int) -> int:
        digits = "".join(ch for ch in str(value or "") if ch.isdigit())
        if not digits:
            return default
        try:
            return int(digits[:6].ljust(6, "0"))
        except ValueError:
            return default

    def _leader_phase(self, now_ts: float) -> str:
        local = time.localtime(now_ts or time.time())
        hhmmss = local.tm_hour * 10000 + local.tm_min * 100 + local.tm_sec
        start = self._hhmmss_value(getattr(self.config, "opening_leader_start", ""), 90300)
        end = self._hhmmss_value(getattr(self.config, "opening_leader_end", ""), 93000)
        return "opening" if start <= hhmmss <= end else "post_opening"

    def _leader_score_threshold(
        self,
        now_ts: float,
        *,
        condition_combo: str = "",
        first_pullback_ready: bool = False,
    ) -> float:
        phase = self._leader_phase(now_ts)
        if phase == "opening":
            combo = str(condition_combo or "").upper()
            if combo == "QUANT_AND_DANTE":
                threshold = float(
                    getattr(
                        self.config,
                        "opening_quant_and_dante_min_leader_score",
                        60.0,
                    )
                    or 0.0
                )
            elif combo == "QUANT_ONLY":
                threshold = float(
                    getattr(
                        self.config,
                        "opening_quant_only_min_leader_score",
                        65.0,
                    )
                    or 0.0
                )
            else:
                threshold = float(
                    getattr(
                        self.config,
                        "opening_min_leader_score",
                        getattr(self.config, "min_leader_score", 60.0),
                    )
                    or 0.0
                )
        else:
            threshold = float(
                getattr(
                    self.config,
                    "post_opening_min_leader_score",
                    getattr(self.config, "min_leader_score", 60.0),
                )
                or 0.0
            )
        if first_pullback_ready and threshold > 0:
            threshold = max(
                0.0,
                threshold
                - float(
                    getattr(self.config, "first_pullback_leader_score_relief", 7.0)
                    or 0.0
                ),
            )
        return threshold

    def _leader_score_decision(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
    ) -> Optional[MomentumDecision]:
        if not bool(getattr(self.config, "leader_score_enabled", True)):
            return None
        phase = self._leader_phase(ctx.now_ts or time.time())
        base_threshold = self._leader_score_threshold(
            ctx.now_ts or time.time(),
            condition_combo=str(metrics.get("condition_combo", "") or ""),
            first_pullback_ready=False,
        )
        threshold = self._leader_score_threshold(
            ctx.now_ts or time.time(),
            condition_combo=str(metrics.get("condition_combo", "") or ""),
            first_pullback_ready=bool(metrics.get("first_pullback_ready", 0.0)),
        )
        score = float(ctx.leader_score or metrics.get("leader_score", 0.0) or 0.0)
        metrics["leader_score_phase"] = phase
        metrics["leader_score_base_min"] = base_threshold
        metrics["leader_score_min"] = threshold
        metrics["leader_score_relief"] = max(base_threshold - threshold, 0.0)
        if threshold <= 0:
            return None
        if score <= 0:
            return MomentumDecision(
                EntryDecision.WAIT_DATA,
                "leader score missing",
                "WAIT_LEADER_SCORE",
                chase_risk_score=metrics.get("chase_risk_score", 0.0),
                metrics=metrics,
            )
        if score < threshold:
            if phase == "opening":
                action = EntryDecision.WAIT_PULLBACK
                reason_code = "WAIT_LEADER_SCORE"
                reason = "leader score wait {:.1f} < {:.1f}".format(score, threshold)
            else:
                if self._post_opening_weak_leader_context_relief(
                    ctx,
                    metrics,
                    score=score,
                    threshold=threshold,
                ):
                    return None
                action = EntryDecision.BLOCK_CHASE
                reason_code = "BLOCK_WEAK_LEADER"
                reason = "leader score weak {:.1f} < {:.1f}".format(score, threshold)
            return MomentumDecision(
                action,
                reason,
                reason_code,
                chase_risk_score=metrics.get("chase_risk_score", 0.0),
                metrics=metrics,
            )
        return None

    def _post_opening_weak_leader_context_relief(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
        *,
        score: float,
        threshold: float,
    ) -> bool:
        relief = float(
            getattr(self.config, "post_opening_weak_leader_context_relief", 0.0)
            or 0.0
        )
        if relief <= 0 or threshold - score > relief:
            return False
        min_score = float(
            getattr(self.config, "post_opening_weak_leader_min_score", threshold)
            or threshold
        )
        if score < min_score:
            return False
        metrics["leader_score_context_relief_checked"] = 1.0

        one_min_reversal = (
            bool(ctx.one_min_reversal)
            if ctx.one_min_reversal is not None
            else self._bullish_reversal(ctx.minute_bars)
        )
        if not one_min_reversal:
            metrics["leader_score_context_relief"] = 0.0
            return False
        if float(ctx.spread_rate or 0.0) > float(self.config.max_spread_pct or 0.0):
            metrics["leader_score_context_relief"] = 0.0
            return False

        vwap_support_ok = bool(metrics.get("vwap_support_ok", 0.0))
        upper_wick_ok = float(ctx.upper_wick_ratio or 0.0) <= float(
            self.config.max_upper_wick_ratio or 0.0
        )
        reclaim_strength = float(
            getattr(
                self.config,
                "vwap_reclaim_buy_trade_strength",
                self.config.min_trade_strength,
            )
            or self.config.min_trade_strength
        )
        vwap_reclaim_context = (
            vwap_support_ok
            and upper_wick_ok
            and float(ctx.chejan_strength or 0.0) >= reclaim_strength
        )

        min_turnover = float(
            getattr(self.config, "post_opening_weak_leader_min_turnover_speed", 0.0)
            or 0.0
        )
        min_strength = float(
            getattr(self.config, "post_opening_weak_leader_min_trade_strength", 0.0)
            or 0.0
        )
        pullback_dry_run = metrics.get("pullback_dry_run", {}) or {}
        dry_run_1pct = False
        if isinstance(pullback_dry_run, dict):
            dry_run_1pct = bool((pullback_dry_run.get("0.0100") or {}).get("passes"))
        pullback_context = (
            dry_run_1pct
            and float(ctx.turnover_speed_per_min or 0.0) >= min_turnover
            and float(ctx.chejan_strength or 0.0) >= min_strength
        )

        allowed = bool(vwap_reclaim_context or pullback_context)
        metrics["leader_score_context_relief"] = 1.0 if allowed else 0.0
        if allowed:
            metrics["leader_score_context_min"] = min_score
            metrics["leader_score_context_relief_points"] = threshold - score
        return allowed

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

    def _entry_cutoff_block(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
        age: float,
        min_observation_sec: float,
    ) -> Optional[MomentumDecision]:
        if not bool(getattr(self.config, "entry_cutoff_guard_enabled", True)):
            return None
        deadline = self.time_policy.entry_window_deadline(
            now=ctx.now_ts or time.time(),
            context={
                "late_a_grade_candidate": bool(metrics.get("late_a_grade_candidate")),
                "entry_type": ENTRY_TYPE_BREAKOUT_SMALL
                if bool(metrics.get("late_a_grade_candidate"))
                else "",
                "candidate_grade": "A" if bool(metrics.get("late_a_grade_candidate")) else "",
            },
        )
        if deadline is None:
            return None
        remaining_observation = max(float(min_observation_sec or 0.0) - float(age or 0.0), 0.0)
        now_ts = float(ctx.now_ts or time.time())
        if now_ts + remaining_observation <= deadline.timestamp():
            return None
        blocked_metrics = dict(metrics or {})
        blocked_metrics["entry_cutoff_ts"] = deadline.timestamp()
        blocked_metrics["remaining_observation_sec"] = remaining_observation
        return MomentumDecision(
            EntryDecision.REJECT,
            "too late for entry window remaining_observation={:.1f}s cutoff={}".format(
                remaining_observation,
                deadline.isoformat(),
            ),
            "TOO_LATE_FOR_ENTRY_WINDOW",
            chase_risk_score=blocked_metrics.get("chase_risk_score", 0.0),
            metrics=blocked_metrics,
        )

    def _min_observation_seconds(self, late_a_grade_candidate: bool) -> float:
        if late_a_grade_candidate:
            return float(
                getattr(
                    self.config,
                    "min_candidate_age_a_grade_seconds",
                    self.config.min_candidate_age_seconds,
                )
                or self.config.min_candidate_age_seconds
            )
        return float(self.config.min_candidate_age_seconds)

    def _late_a_grade_candidate(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
    ) -> bool:
        if not bool(getattr(self.config, "allow_late_a_grade_entry", False)):
            return False
        return self._breakout_small_ready(ctx, metrics, self._bullish_reversal(ctx.minute_bars))

    def _breakout_probe_entry_ratio(self) -> float:
        return max(float(getattr(self.config, "breakout_probe_entry_ratio", 0.0) or 0.0), 0.0)

    def _breakout_small_ready(
        self,
        ctx: MomentumContext,
        metrics: Dict[str, float],
        bullish_reversal: bool,
    ) -> bool:
        if not bool(self.config.allow_breakout_probe_entry):
            return False
        c = ctx.candidate
        if ctx.current_price <= 0 or c.capture_price <= 0:
            return False
        if ctx.current_price < c.capture_price:
            return False
        if self.config.require_one_min_reversal and not bullish_reversal:
            return False
        if metrics.get("chase_risk_score", 100.0) > self.config.max_chase_risk_score * 0.7:
            return False
        if self.config.require_vwap_filter and metrics.get("is_above_vwap", 1.0) <= 0:
            return False
        if (
            metrics.get("spread_rate", 1.0) > self.config.max_spread_pct
            and metrics.get("spread_gate_relaxed", 0.0) <= 0.0
        ):
            return False
        if metrics.get("upper_wick_ratio", 1.0) > self.config.max_upper_wick_ratio:
            return False
        return True

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
            "primary_condition_name": metrics.get("primary_condition_name"),
            "bonus_condition_name": metrics.get("bonus_condition_name"),
            "quant_detected": bool(metrics.get("quant_detected", 0.0)),
            "dante_detected": bool(metrics.get("dante_detected", 0.0)),
            "condition_combo": metrics.get("condition_combo"),
            "condition_score_bonus": self._optional_number(metrics.get("condition_score_bonus")),
            "first_condition_name": metrics.get("first_condition_name"),
            "last_condition_name": metrics.get("last_condition_name"),
            "first_condition_detected_at": metrics.get("first_condition_detected_at"),
            "bonus_condition_detected_at": metrics.get("bonus_condition_detected_at"),
            "time_between_conditions_sec": self._optional_number(
                metrics.get("time_between_conditions_sec")
            ),
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
            "prior_high_source": metrics.get("prior_high_source"),
            "upper_wick_ratio": self._optional_number(ctx.upper_wick_ratio),
            "was_below_vwap": bool(metrics.get("was_below_vwap") or ctx.was_below_vwap),
            "short_reclaim_high": self._positive_optional_number(metrics.get("short_reclaim_high")),
            "vwap_reclaim_candidate": bool(metrics.get("vwap_reclaim_candidate", 0.0)),
            "pullback_pct": self._optional_number(metrics.get("pullback_pct")),
            "capture_pullback_pct": self._optional_number(metrics.get("capture_pullback_pct")),
            "pullback_from_high_pct": self._optional_number(metrics.get("pullback_from_high_pct")),
            "observed_pullback_from_high_pct": self._optional_number(
                metrics.get("observed_pullback_from_high_pct")
            ),
            "strategy_pullback_basis": self._positive_optional_number(
                metrics.get("strategy_pullback_basis")
            ),
            "entry_pullback_eligible": bool(metrics.get("entry_pullback_eligible", 0.0)),
            "first_pullback_ready": bool(metrics.get("first_pullback_ready", 0.0)),
            "effective_pullback_entry_pct": self._optional_number(metrics.get("effective_pullback_entry_pct")),
            "adaptive_pullback_entry_pct": self._optional_number(metrics.get("adaptive_pullback_entry_pct")),
            "pullback_dry_run": metrics.get("pullback_dry_run"),
            "candle_cache_available": bool(ctx.minute_bars),
            "orderbook_available": not self._missing_number(ctx.spread_rate),
            "market_data_available": self._market_data_available(ctx, metrics),
            "is_above_vwap": None if vwap is None or current_price <= 0 else current_price >= vwap,
            "one_min_reversal": one_min_reversal,
            "recent_low_to_current_pct": self._optional_number(ctx.recent_low_to_current_pct),
            "extension_from_vwap_pct": self._optional_number(metrics.get("extension_from_vwap_pct")),
            "extension_from_short_ma_pct": self._optional_number(metrics.get("extension_from_short_ma_pct")),
            "entry_type": self._entry_type(decision),
            "strategy_type": metrics.get("strategy_type") or decision.entry_type,
            "paper_only_strategy": bool(metrics.get("paper_only_strategy", 0.0)),
            "orderable_live": False if metrics.get("orderable_live", 1.0) <= 0.0 else True,
            "position_size_multiplier": self._optional_number(decision.position_size_multiplier),
            "flow_score_bucket": metrics.get("flow_score_bucket"),
            "flow_gate_ok": self._optional_number(metrics.get("flow_gate_ok")),
            "volume_gate_min_ratio": self._optional_number(metrics.get("volume_gate_min_ratio")),
            "weak_volume_partial_relief": bool(metrics.get("weak_volume_partial_relief", 0.0)),
            "weak_volume_partial_min_ratio": self._optional_number(
                metrics.get("weak_volume_partial_min_ratio")
            ),
            "spread_gate_relaxed": bool(metrics.get("spread_gate_relaxed", 0.0)),
            "spread_gate_max_pct": self._optional_number(metrics.get("spread_gate_max_pct")),
            "vwap_reclaim_price": self._positive_optional_number(metrics.get("vwap_reclaim_price")),
            "vwap_reclaim_confirmed": self._optional_number(metrics.get("vwap_reclaim_confirmed")),
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
        if decision.entry_type:
            return decision.entry_type
        if decision.reason_code in {"BUY_PULLBACK_CONFIRMED", "BUY_PULLBACK_RECLAIM"}:
            return ENTRY_TYPE_PULLBACK_RECLAIM
        if decision.reason_code in {"BUY_BREAKOUT_PROBE", "BUY_BREAKOUT_SMALL"}:
            return ENTRY_TYPE_BREAKOUT_SMALL
        return None

    @staticmethod
    def _blocked_by(decision: MomentumDecision) -> Optional[str]:
        if decision.action in {
            EntryDecision.BLOCK_CHASE,
            EntryDecision.REJECT,
            EntryDecision.WAIT_DATA,
            EntryDecision.WAIT_RECLAIM_VWAP,
        }:
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

    def _prior_high_with_source(self, ctx: MomentumContext):
        if ctx.prior_high is not None and ctx.prior_high > 0:
            return int(ctx.prior_high), "candle"
        bars = list(ctx.minute_bars or [])
        if self.config.exclude_current_bar_from_high_distance and bars:
            bars = bars[:-1]
        if self.config.high_distance_lookback_bars > 0:
            bars = bars[-self.config.high_distance_lookback_bars :]
        highs = [int(getattr(bar, "high", 0) or 0) for bar in bars]
        highs = [value for value in highs if value > 0]
        if highs:
            return max(highs), "candle"
        rolling_high = int(ctx.rolling_high_since_capture or ctx.high_since_capture or 0)
        if rolling_high > 0:
            return rolling_high, "rolling_since_capture"
        if int(ctx.realtime_day_high or 0) > 0:
            return int(ctx.realtime_day_high), "realtime_day_high"
        first_capture = int(getattr(ctx.candidate, "first_capture_price", 0) or ctx.candidate.capture_price or 0)
        if first_capture > 0:
            return first_capture, "first_capture_price"
        if ctx.current_price > 0:
            return int(ctx.current_price), "current_price_fallback"
        return 0, "missing"

    def _prior_high(self, ctx: MomentumContext) -> int:
        return self._prior_high_with_source(ctx)[0]

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
        if lows:
            return min(lows)
        if int(getattr(ctx.candidate, "recent_low_price", 0) or 0) > 0:
            return int(getattr(ctx.candidate, "recent_low_price", 0) or 0)
        return int(ctx.current_price or 0)

    def _adaptive_pullback_pct(self, ctx: MomentumContext) -> float:
        bars = list(ctx.minute_bars or [])[-5:]
        ranges = []
        for bar in bars:
            close = float(getattr(bar, "close", 0) or 0)
            high = float(getattr(bar, "high", 0) or 0)
            low = float(getattr(bar, "low", 0) or 0)
            if close > 0 and high > low:
                ranges.append((high - low) / close)
        if not ranges:
            return 0.0
        raw = (
            sum(ranges) / len(ranges)
            * float(getattr(self.config, "adaptive_pullback_volatility_multiplier", 0.5) or 0.5)
        )
        lo = float(getattr(self.config, "adaptive_pullback_min_pct", 0.005) or 0.005)
        hi = float(getattr(self.config, "adaptive_pullback_max_pct", 0.015) or 0.015)
        return max(lo, min(raw, hi))

    def _pullback_dry_run(self, capture_price: int, pullback_pct: float) -> Dict[str, object]:
        levels = []
        for item in str(getattr(self.config, "pullback_dry_run_levels", "") or "").split(","):
            text = item.strip()
            if not text:
                continue
            try:
                value = float(text)
            except ValueError:
                continue
            if value > 0:
                levels.append(value)
        if not levels:
            levels = [0.005, 0.008, 0.010, 0.015]
        out: Dict[str, object] = {}
        for level in levels:
            key = "{:.4f}".format(level)
            out[key] = {
                "passes": bool(pullback_pct >= level),
                "trigger_price": int(capture_price * (1.0 - level)) if capture_price > 0 else None,
            }
        return out

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
