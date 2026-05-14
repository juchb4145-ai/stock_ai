from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    true_values = {"1", "true", "t", "yes", "y", "on"}
    false_values = {"0", "false", "f", "no", "n", "off"}
    if normalized in true_values:
        return True
    if normalized in false_values:
        return False
    raise ValueError(
        "{} must be an explicit boolean value ({}/{}), got {!r}".format(
            name,
            ", ".join(sorted(true_values)),
            ", ".join(sorted(false_values)),
            value,
        )
    )


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _env_optional_float(name: str, default: Optional[float]) -> Optional[float]:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _env_str(name: str, default: str) -> str:
    value = os.environ.get(name)
    if value is None:
        return default
    return str(value).strip()


DEFAULT_CONDITION_FORMULA = """((A and B) or (C and D) or (E and F) or (G and H)) and I and J and N and O and T"""
DEFAULT_ENTRY_STRATEGY_VERSION = "momentum_v2_selective_relief_v1"


@dataclass(frozen=True)
class TradeConfig:
    strategy_name: str = "퀀트조건식"
    condition_name: str = "단테떡상이_수정"
    legacy_condition_name: str = "단테떡상이_수정"
    condition_formula: str = DEFAULT_CONDITION_FORMULA
    condition_formula_version: str = "quant_condition_formula_v2"
    signal_source: str = "HTS_CONDITION_SEARCH"
    risk_reward_profile_name: str = "quant_pullback_1p5_stop_2p0_target"
    entry_strategy_version: str = DEFAULT_ENTRY_STRATEGY_VERSION

    dry_run: bool = True
    live_trading_enabled: bool = False
    trading_enabled: bool = True
    paper_portfolio_enabled: bool = True
    paper_initial_cash: int = 10_000_000
    paper_daily_loss_limit_pct: float = 0.03

    candidate_expiry_seconds: int = 30 * 60
    min_candidate_age_seconds: int = 30
    min_candidate_age_a_grade_seconds: int = 8
    min_candidate_ticks: int = 5
    entry_cutoff_guard_enabled: bool = True
    trading_candidate_capture_requires_entry_window: bool = True
    allow_late_a_grade_entry: bool = False
    late_a_grade_entry_start: str = "10:30:00"
    late_a_grade_entry_end: str = "10:45:00"
    late_a_grade_position_size_multiplier: float = 0.25
    cash_usage_ratio: float = 0.98
    max_position_cash_ratio: float = 0.10
    default_stop_loss_pct: float = 0.015
    default_take_profit_pct: float = 0.020
    replay_stop_loss_pct: Optional[float] = None
    replay_take_profit_pct: Optional[float] = None
    pullback_entry_pct: float = 0.015
    pullback_dry_run_levels: str = "0.005,0.008,0.010,0.015"
    adaptive_pullback_enabled: bool = False
    adaptive_pullback_min_pct: float = 0.005
    adaptive_pullback_max_pct: float = 0.015
    adaptive_pullback_volatility_multiplier: float = 0.5
    max_pullback_pct: float = 0.030
    rebound_confirm_pct: float = 0.003
    min_trade_strength: float = 100.0
    weak_market_min_trade_strength: float = 120.0
    require_volume_ratio: bool = True
    min_volume_ratio: float = 1.2
    weak_volume_partial_entry_enabled: bool = True
    weak_volume_partial_min_trade_strength: float = 110.0
    weak_volume_partial_min_volume_ratio: float = 0.03
    weak_volume_partial_min_rebound_pct: float = 0.003
    weak_volume_partial_position_size_multiplier: float = 0.25
    vwap_reclaim_wait_trade_strength: float = 180.0
    vwap_reclaim_buy_trade_strength: float = 150.0
    vwap_reclaim_min_rebound_pct: float = 0.003
    vwap_reclaim_min_volume_ratio: float = 0.8
    vwap_reclaim_confirm_buffer_pct: float = 0.001
    strong_trade_strength_for_volume_relief: float = 300.0
    strong_trade_strength_min_volume_ratio: float = 0.3
    require_turnover_speed: bool = True
    min_turnover_speed_per_min: float = 50_000_000.0
    reject_missing_market_data: bool = True
    max_chase_distance_pct: float = 0.04
    max_chase_risk_score: float = 60.0
    max_spread_pct: float = 0.006
    conditional_spread_relief_enabled: bool = True
    max_conditional_spread_pct: float = 0.007
    conditional_spread_min_trade_strength: float = 110.0
    conditional_spread_min_volume_ratio: float = 0.15
    conditional_spread_min_rebound_pct: float = 0.003
    conditional_spread_position_size_multiplier: float = 0.25
    max_upper_wick_ratio: float = 0.30
    require_vwap_filter: bool = True
    require_one_min_reversal: bool = True
    require_candle_cache_for_buy: bool = True
    max_extension_from_vwap_pct: float = 0.03
    max_extension_from_short_ma_pct: float = 0.03
    max_signal_candle_range_pct: float = 0.04
    max_position_in_signal_candle_pct: float = 0.90
    max_recent_low_to_current_pct: float = 0.05
    min_pullback_after_signal_pct: float = 0.003
    high_distance_lookback_bars: int = 5
    exclude_current_bar_from_high_distance: bool = True
    allow_breakout_probe_entry: bool = True
    breakout_probe_entry_ratio: float = 0.25
    legacy_filter_enabled: bool = True
    legacy_filter_veto_breakout_small: bool = False

    max_positions: int = 3
    max_daily_buy_count: int = 20
    max_daily_loss: int = 300_000
    max_daily_exposure: int = 3_000_000
    min_order_cash: int = 50_000
    max_position_size: int = 1_000_000
    reentry_cooldown_seconds: int = 6 * 60 * 60
    order_request_interval_seconds: float = 0.25
    max_orders_per_second: int = 5
    live_order_token_ttl_seconds: float = 5.0
    require_exit_policy_for_sell: bool = True
    require_cancel_policy_for_cancel: bool = True
    technical_stop_enabled: bool = True
    structure_stop_enabled: bool = True
    vwap_stop_enabled: bool = True
    vwap_reclaim_wait_sec: int = 60
    vwap_fast_drop_pct: float = 0.010
    recent_low_lookback_bars: int = 3
    trade_strength_drop_pct: float = 30.0
    bearish_volume_ratio_min: float = 150.0
    orderbook_sell_pressure_enabled: bool = False
    orderbook_sell_pressure_ratio: float = 2.0
    hard_stop_has_highest_priority: bool = True
    enable_r_multiple_exit: bool = True
    move_stop_to_break_even_at_r: float = 1.0
    partial_take_profit_enabled: bool = True
    first_partial_take_profit_r: float = 2.0
    first_partial_take_profit_ratio: float = 0.5
    trailing_start_profit_pct: float = 0.015
    trailing_pullback_pct: float = 0.008
    fixed_take_profit_pct: float = 0.020
    fixed_stop_loss_pct: float = 0.015
    fixed_take_profit_as_fallback: bool = True
    time_stop_seconds: int = 25 * 60
    max_sell_retry_count: int = 3
    sell_retry_interval_sec: int = 3
    sell_unfilled_timeout_sec: int = 10
    cancel_replace_on_retry: bool = True
    escalate_after_retry_count: int = 2
    block_new_buys_on_exit_escalation: bool = True
    allow_closing_auction_emergency_exit: bool = True
    allow_new_buy_after_closing_auction: bool = False
    stop_sell_allowed_during_no_buy_window: bool = True
    time_policy_enabled: bool = True
    time_policy_config_version: str = "krx_regular_v1"
    trading_timezone: str = "Asia/Seoul"
    krx_regular_open: str = "09:00:00"
    krx_regular_close: str = "15:30:00"
    candidate_capture_start: str = "09:00:00"
    candidate_capture_end: str = "14:50:00"
    entry_windows: str = "09:03:00-10:30:00,13:00:00-14:20:00"
    no_new_entry_after: str = "14:20:00"
    force_exit_start: str = "15:05:00"
    force_exit_deadline: str = "15:19:30"
    closing_auction_start: str = "15:20:00"
    closing_auction_end: str = "15:30:00"
    allow_after_hours_entry: bool = False
    allow_nxt_trading: bool = False
    krx_holidays: str = ""

    @property
    def resolved_replay_stop_loss_pct(self) -> float:
        if self.replay_stop_loss_pct is not None:
            return float(self.replay_stop_loss_pct)
        return float(self.default_stop_loss_pct)

    @property
    def resolved_replay_take_profit_pct(self) -> float:
        if self.replay_take_profit_pct is not None:
            return float(self.replay_take_profit_pct)
        return float(self.default_take_profit_pct)

    @classmethod
    def from_env(cls) -> "TradeConfig":
        return cls(
            strategy_name=os.environ.get("KIWOOM_STRATEGY_NAME", cls.strategy_name),
            condition_name=os.environ.get("KIWOOM_CONDITION_NAME", cls.condition_name),
            legacy_condition_name=os.environ.get(
                "KIWOOM_LEGACY_CONDITION_NAME", cls.legacy_condition_name
            ),
            condition_formula=os.environ.get(
                "KIWOOM_CONDITION_FORMULA", cls.condition_formula
            ),
            condition_formula_version=os.environ.get(
                "KIWOOM_CONDITION_FORMULA_VERSION",
                cls.condition_formula_version,
            ),
            signal_source=os.environ.get("KIWOOM_SIGNAL_SOURCE", cls.signal_source),
            risk_reward_profile_name=os.environ.get(
                "KIWOOM_RISK_REWARD_PROFILE_NAME",
                cls.risk_reward_profile_name,
            ),
            entry_strategy_version=os.environ.get(
                "KIWOOM_ENTRY_STRATEGY_VERSION",
                cls.entry_strategy_version,
            ),
            dry_run=_env_bool("KIWOOM_DRY_RUN", cls.dry_run),
            live_trading_enabled=_env_bool(
                "KIWOOM_LIVE_TRADING_ENABLED",
                cls.live_trading_enabled,
            ),
            trading_enabled=_env_bool(
                "KIWOOM_TRADING_ENABLED",
                cls.trading_enabled,
            ),
            paper_portfolio_enabled=_env_bool(
                "KIWOOM_PAPER_PORTFOLIO_ENABLED",
                cls.paper_portfolio_enabled,
            ),
            paper_initial_cash=_env_int(
                "KIWOOM_PAPER_INITIAL_CASH",
                cls.paper_initial_cash,
            ),
            paper_daily_loss_limit_pct=_env_float(
                "KIWOOM_PAPER_DAILY_LOSS_LIMIT_PCT",
                cls.paper_daily_loss_limit_pct,
            ),
            candidate_expiry_seconds=_env_int(
                "KIWOOM_CANDIDATE_EXPIRY_SECONDS",
                cls.candidate_expiry_seconds,
            ),
            min_candidate_age_seconds=_env_int(
                "KIWOOM_MIN_CANDIDATE_AGE_SECONDS",
                cls.min_candidate_age_seconds,
            ),
            min_candidate_age_a_grade_seconds=_env_int(
                "KIWOOM_MIN_CANDIDATE_AGE_A_GRADE_SECONDS",
                cls.min_candidate_age_a_grade_seconds,
            ),
            min_candidate_ticks=_env_int(
                "KIWOOM_MIN_CANDIDATE_TICKS",
                cls.min_candidate_ticks,
            ),
            entry_cutoff_guard_enabled=_env_bool(
                "KIWOOM_ENTRY_CUTOFF_GUARD_ENABLED",
                cls.entry_cutoff_guard_enabled,
            ),
            trading_candidate_capture_requires_entry_window=_env_bool(
                "KIWOOM_TRADING_CANDIDATE_CAPTURE_REQUIRES_ENTRY_WINDOW",
                cls.trading_candidate_capture_requires_entry_window,
            ),
            allow_late_a_grade_entry=_env_bool(
                "KIWOOM_ALLOW_LATE_A_GRADE_ENTRY",
                cls.allow_late_a_grade_entry,
            ),
            late_a_grade_entry_start=_env_str(
                "KIWOOM_LATE_A_GRADE_ENTRY_START",
                cls.late_a_grade_entry_start,
            ),
            late_a_grade_entry_end=_env_str(
                "KIWOOM_LATE_A_GRADE_ENTRY_END",
                cls.late_a_grade_entry_end,
            ),
            late_a_grade_position_size_multiplier=_env_float(
                "KIWOOM_LATE_A_GRADE_POSITION_SIZE_MULTIPLIER",
                cls.late_a_grade_position_size_multiplier,
            ),
            cash_usage_ratio=_env_float(
                "KIWOOM_CASH_USAGE_RATIO",
                cls.cash_usage_ratio,
            ),
            max_position_cash_ratio=_env_float(
                "KIWOOM_MAX_POSITION_CASH_RATIO",
                cls.max_position_cash_ratio,
            ),
            default_stop_loss_pct=_env_float(
                "KIWOOM_DEFAULT_STOP_LOSS_PCT",
                cls.default_stop_loss_pct,
            ),
            default_take_profit_pct=_env_float(
                "KIWOOM_DEFAULT_TAKE_PROFIT_PCT",
                cls.default_take_profit_pct,
            ),
            replay_stop_loss_pct=_env_optional_float(
                "KIWOOM_REPLAY_STOP_LOSS_PCT",
                cls.replay_stop_loss_pct,
            ),
            replay_take_profit_pct=_env_optional_float(
                "KIWOOM_REPLAY_TAKE_PROFIT_PCT",
                cls.replay_take_profit_pct,
            ),
            pullback_entry_pct=_env_float(
                "KIWOOM_PULLBACK_ENTRY_PCT",
                cls.pullback_entry_pct,
            ),
            pullback_dry_run_levels=_env_str(
                "KIWOOM_PULLBACK_DRY_RUN_LEVELS",
                cls.pullback_dry_run_levels,
            ),
            adaptive_pullback_enabled=_env_bool(
                "KIWOOM_ADAPTIVE_PULLBACK_ENABLED",
                cls.adaptive_pullback_enabled,
            ),
            adaptive_pullback_min_pct=_env_float(
                "KIWOOM_ADAPTIVE_PULLBACK_MIN_PCT",
                cls.adaptive_pullback_min_pct,
            ),
            adaptive_pullback_max_pct=_env_float(
                "KIWOOM_ADAPTIVE_PULLBACK_MAX_PCT",
                cls.adaptive_pullback_max_pct,
            ),
            adaptive_pullback_volatility_multiplier=_env_float(
                "KIWOOM_ADAPTIVE_PULLBACK_VOLATILITY_MULTIPLIER",
                cls.adaptive_pullback_volatility_multiplier,
            ),
            max_pullback_pct=_env_float(
                "KIWOOM_MAX_PULLBACK_PCT",
                cls.max_pullback_pct,
            ),
            rebound_confirm_pct=_env_float(
                "KIWOOM_REBOUND_CONFIRM_PCT",
                cls.rebound_confirm_pct,
            ),
            min_trade_strength=_env_float(
                "KIWOOM_MIN_TRADE_STRENGTH",
                cls.min_trade_strength,
            ),
            weak_market_min_trade_strength=_env_float(
                "KIWOOM_WEAK_MARKET_MIN_TRADE_STRENGTH",
                cls.weak_market_min_trade_strength,
            ),
            require_volume_ratio=_env_bool(
                "KIWOOM_REQUIRE_VOLUME_RATIO",
                cls.require_volume_ratio,
            ),
            min_volume_ratio=_env_float(
                "KIWOOM_MIN_VOLUME_RATIO",
                cls.min_volume_ratio,
            ),
            weak_volume_partial_entry_enabled=_env_bool(
                "KIWOOM_WEAK_VOLUME_PARTIAL_ENTRY_ENABLED",
                cls.weak_volume_partial_entry_enabled,
            ),
            weak_volume_partial_min_trade_strength=_env_float(
                "KIWOOM_WEAK_VOLUME_PARTIAL_MIN_TRADE_STRENGTH",
                cls.weak_volume_partial_min_trade_strength,
            ),
            weak_volume_partial_min_volume_ratio=_env_float(
                "KIWOOM_WEAK_VOLUME_PARTIAL_MIN_VOLUME_RATIO",
                cls.weak_volume_partial_min_volume_ratio,
            ),
            weak_volume_partial_min_rebound_pct=_env_float(
                "KIWOOM_WEAK_VOLUME_PARTIAL_MIN_REBOUND_PCT",
                cls.weak_volume_partial_min_rebound_pct,
            ),
            weak_volume_partial_position_size_multiplier=_env_float(
                "KIWOOM_WEAK_VOLUME_PARTIAL_POSITION_SIZE_MULTIPLIER",
                cls.weak_volume_partial_position_size_multiplier,
            ),
            vwap_reclaim_wait_trade_strength=_env_float(
                "KIWOOM_VWAP_RECLAIM_WAIT_TRADE_STRENGTH",
                cls.vwap_reclaim_wait_trade_strength,
            ),
            vwap_reclaim_buy_trade_strength=_env_float(
                "KIWOOM_VWAP_RECLAIM_BUY_TRADE_STRENGTH",
                cls.vwap_reclaim_buy_trade_strength,
            ),
            vwap_reclaim_min_rebound_pct=_env_float(
                "KIWOOM_VWAP_RECLAIM_MIN_REBOUND_PCT",
                cls.vwap_reclaim_min_rebound_pct,
            ),
            vwap_reclaim_min_volume_ratio=_env_float(
                "KIWOOM_VWAP_RECLAIM_MIN_VOLUME_RATIO",
                cls.vwap_reclaim_min_volume_ratio,
            ),
            vwap_reclaim_confirm_buffer_pct=_env_float(
                "KIWOOM_VWAP_RECLAIM_CONFIRM_BUFFER_PCT",
                cls.vwap_reclaim_confirm_buffer_pct,
            ),
            strong_trade_strength_for_volume_relief=_env_float(
                "KIWOOM_STRONG_TRADE_STRENGTH_FOR_VOLUME_RELIEF",
                cls.strong_trade_strength_for_volume_relief,
            ),
            strong_trade_strength_min_volume_ratio=_env_float(
                "KIWOOM_STRONG_TRADE_STRENGTH_MIN_VOLUME_RATIO",
                cls.strong_trade_strength_min_volume_ratio,
            ),
            require_turnover_speed=_env_bool(
                "KIWOOM_REQUIRE_TURNOVER_SPEED",
                cls.require_turnover_speed,
            ),
            min_turnover_speed_per_min=_env_float(
                "KIWOOM_MIN_TURNOVER_SPEED_PER_MIN",
                cls.min_turnover_speed_per_min,
            ),
            reject_missing_market_data=_env_bool(
                "KIWOOM_REJECT_MISSING_MARKET_DATA",
                cls.reject_missing_market_data,
            ),
            max_chase_distance_pct=_env_float(
                "KIWOOM_MAX_CHASE_DISTANCE_PCT",
                cls.max_chase_distance_pct,
            ),
            max_chase_risk_score=_env_float(
                "KIWOOM_MAX_CHASE_RISK_SCORE",
                cls.max_chase_risk_score,
            ),
            max_spread_pct=_env_float(
                "KIWOOM_MAX_SPREAD_PCT",
                cls.max_spread_pct,
            ),
            conditional_spread_relief_enabled=_env_bool(
                "KIWOOM_CONDITIONAL_SPREAD_RELIEF_ENABLED",
                cls.conditional_spread_relief_enabled,
            ),
            max_conditional_spread_pct=_env_float(
                "KIWOOM_MAX_CONDITIONAL_SPREAD_PCT",
                cls.max_conditional_spread_pct,
            ),
            conditional_spread_min_trade_strength=_env_float(
                "KIWOOM_CONDITIONAL_SPREAD_MIN_TRADE_STRENGTH",
                cls.conditional_spread_min_trade_strength,
            ),
            conditional_spread_min_volume_ratio=_env_float(
                "KIWOOM_CONDITIONAL_SPREAD_MIN_VOLUME_RATIO",
                cls.conditional_spread_min_volume_ratio,
            ),
            conditional_spread_min_rebound_pct=_env_float(
                "KIWOOM_CONDITIONAL_SPREAD_MIN_REBOUND_PCT",
                cls.conditional_spread_min_rebound_pct,
            ),
            conditional_spread_position_size_multiplier=_env_float(
                "KIWOOM_CONDITIONAL_SPREAD_POSITION_SIZE_MULTIPLIER",
                cls.conditional_spread_position_size_multiplier,
            ),
            max_upper_wick_ratio=_env_float(
                "KIWOOM_MAX_UPPER_WICK_RATIO",
                cls.max_upper_wick_ratio,
            ),
            require_vwap_filter=_env_bool(
                "KIWOOM_REQUIRE_VWAP_FILTER",
                cls.require_vwap_filter,
            ),
            require_one_min_reversal=_env_bool(
                "KIWOOM_REQUIRE_ONE_MIN_REVERSAL",
                cls.require_one_min_reversal,
            ),
            require_candle_cache_for_buy=_env_bool(
                "KIWOOM_REQUIRE_CANDLE_CACHE_FOR_BUY",
                cls.require_candle_cache_for_buy,
            ),
            max_extension_from_vwap_pct=_env_float(
                "KIWOOM_MAX_EXTENSION_FROM_VWAP_PCT",
                cls.max_extension_from_vwap_pct,
            ),
            max_extension_from_short_ma_pct=_env_float(
                "KIWOOM_MAX_EXTENSION_FROM_SHORT_MA_PCT",
                cls.max_extension_from_short_ma_pct,
            ),
            max_signal_candle_range_pct=_env_float(
                "KIWOOM_MAX_SIGNAL_CANDLE_RANGE_PCT",
                cls.max_signal_candle_range_pct,
            ),
            max_position_in_signal_candle_pct=_env_float(
                "KIWOOM_MAX_POSITION_IN_SIGNAL_CANDLE_PCT",
                cls.max_position_in_signal_candle_pct,
            ),
            max_recent_low_to_current_pct=_env_float(
                "KIWOOM_MAX_RECENT_LOW_TO_CURRENT_PCT",
                cls.max_recent_low_to_current_pct,
            ),
            min_pullback_after_signal_pct=_env_float(
                "KIWOOM_MIN_PULLBACK_AFTER_SIGNAL_PCT",
                cls.min_pullback_after_signal_pct,
            ),
            high_distance_lookback_bars=_env_int(
                "KIWOOM_HIGH_DISTANCE_LOOKBACK_BARS",
                cls.high_distance_lookback_bars,
            ),
            exclude_current_bar_from_high_distance=_env_bool(
                "KIWOOM_EXCLUDE_CURRENT_BAR_FROM_HIGH_DISTANCE",
                cls.exclude_current_bar_from_high_distance,
            ),
            allow_breakout_probe_entry=_env_bool(
                "KIWOOM_ALLOW_BREAKOUT_PROBE_ENTRY",
                cls.allow_breakout_probe_entry,
            ),
            breakout_probe_entry_ratio=_env_float(
                "KIWOOM_BREAKOUT_PROBE_ENTRY_RATIO",
                cls.breakout_probe_entry_ratio,
            ),
            legacy_filter_enabled=_env_bool(
                "KIWOOM_LEGACY_FILTER_ENABLED",
                cls.legacy_filter_enabled,
            ),
            legacy_filter_veto_breakout_small=_env_bool(
                "KIWOOM_LEGACY_FILTER_VETO_BREAKOUT_SMALL",
                cls.legacy_filter_veto_breakout_small,
            ),
            max_positions=_env_int("KIWOOM_MAX_POSITIONS", cls.max_positions),
            max_daily_buy_count=_env_int(
                "KIWOOM_MAX_DAILY_BUY_COUNT",
                cls.max_daily_buy_count,
            ),
            max_daily_loss=_env_int(
                "KIWOOM_MAX_DAILY_LOSS",
                cls.max_daily_loss,
            ),
            max_daily_exposure=_env_int(
                "KIWOOM_MAX_DAILY_EXPOSURE",
                cls.max_daily_exposure,
            ),
            min_order_cash=_env_int("KIWOOM_MIN_ORDER_CASH", cls.min_order_cash),
            max_position_size=_env_int(
                "KIWOOM_MAX_POSITION_SIZE",
                cls.max_position_size,
            ),
            reentry_cooldown_seconds=_env_int(
                "KIWOOM_REENTRY_COOLDOWN_SECONDS",
                cls.reentry_cooldown_seconds,
            ),
            order_request_interval_seconds=_env_float(
                "KIWOOM_ORDER_REQUEST_INTERVAL_SECONDS",
                cls.order_request_interval_seconds,
            ),
            max_orders_per_second=_env_int(
                "KIWOOM_MAX_ORDERS_PER_SECOND",
                cls.max_orders_per_second,
            ),
            live_order_token_ttl_seconds=_env_float(
                "KIWOOM_LIVE_ORDER_TOKEN_TTL_SECONDS",
                cls.live_order_token_ttl_seconds,
            ),
            require_exit_policy_for_sell=_env_bool(
                "KIWOOM_REQUIRE_EXIT_POLICY_FOR_SELL",
                cls.require_exit_policy_for_sell,
            ),
            require_cancel_policy_for_cancel=_env_bool(
                "KIWOOM_REQUIRE_CANCEL_POLICY_FOR_CANCEL",
                cls.require_cancel_policy_for_cancel,
            ),
            technical_stop_enabled=_env_bool(
                "KIWOOM_TECHNICAL_STOP_ENABLED",
                cls.technical_stop_enabled,
            ),
            structure_stop_enabled=_env_bool(
                "KIWOOM_STRUCTURE_STOP_ENABLED",
                cls.structure_stop_enabled,
            ),
            vwap_stop_enabled=_env_bool(
                "KIWOOM_VWAP_STOP_ENABLED",
                cls.vwap_stop_enabled,
            ),
            vwap_reclaim_wait_sec=_env_int(
                "KIWOOM_VWAP_RECLAIM_WAIT_SEC",
                cls.vwap_reclaim_wait_sec,
            ),
            vwap_fast_drop_pct=_env_float(
                "KIWOOM_VWAP_FAST_DROP_PCT",
                cls.vwap_fast_drop_pct,
            ),
            recent_low_lookback_bars=_env_int(
                "KIWOOM_RECENT_LOW_LOOKBACK_BARS",
                cls.recent_low_lookback_bars,
            ),
            trade_strength_drop_pct=_env_float(
                "KIWOOM_TRADE_STRENGTH_DROP_PCT",
                cls.trade_strength_drop_pct,
            ),
            bearish_volume_ratio_min=_env_float(
                "KIWOOM_BEARISH_VOLUME_RATIO_MIN",
                cls.bearish_volume_ratio_min,
            ),
            orderbook_sell_pressure_enabled=_env_bool(
                "KIWOOM_ORDERBOOK_SELL_PRESSURE_ENABLED",
                cls.orderbook_sell_pressure_enabled,
            ),
            orderbook_sell_pressure_ratio=_env_float(
                "KIWOOM_ORDERBOOK_SELL_PRESSURE_RATIO",
                cls.orderbook_sell_pressure_ratio,
            ),
            hard_stop_has_highest_priority=_env_bool(
                "KIWOOM_HARD_STOP_HAS_HIGHEST_PRIORITY",
                cls.hard_stop_has_highest_priority,
            ),
            enable_r_multiple_exit=_env_bool(
                "KIWOOM_ENABLE_R_MULTIPLE_EXIT",
                cls.enable_r_multiple_exit,
            ),
            move_stop_to_break_even_at_r=_env_float(
                "KIWOOM_MOVE_STOP_TO_BREAK_EVEN_AT_R",
                cls.move_stop_to_break_even_at_r,
            ),
            partial_take_profit_enabled=_env_bool(
                "KIWOOM_PARTIAL_TAKE_PROFIT_ENABLED",
                cls.partial_take_profit_enabled,
            ),
            first_partial_take_profit_r=_env_float(
                "KIWOOM_FIRST_PARTIAL_TAKE_PROFIT_R",
                cls.first_partial_take_profit_r,
            ),
            first_partial_take_profit_ratio=_env_float(
                "KIWOOM_FIRST_PARTIAL_TAKE_PROFIT_RATIO",
                cls.first_partial_take_profit_ratio,
            ),
            trailing_start_profit_pct=_env_float(
                "KIWOOM_TRAILING_START_PROFIT_PCT",
                cls.trailing_start_profit_pct,
            ),
            trailing_pullback_pct=_env_float(
                "KIWOOM_TRAILING_PULLBACK_PCT",
                cls.trailing_pullback_pct,
            ),
            fixed_take_profit_pct=_env_float(
                "KIWOOM_FIXED_TAKE_PROFIT_PCT",
                cls.fixed_take_profit_pct,
            ),
            fixed_stop_loss_pct=_env_float(
                "KIWOOM_FIXED_STOP_LOSS_PCT",
                cls.fixed_stop_loss_pct,
            ),
            fixed_take_profit_as_fallback=_env_bool(
                "KIWOOM_FIXED_TAKE_PROFIT_AS_FALLBACK",
                cls.fixed_take_profit_as_fallback,
            ),
            time_stop_seconds=_env_int(
                "KIWOOM_TIME_STOP_SECONDS",
                cls.time_stop_seconds,
            ),
            max_sell_retry_count=_env_int(
                "KIWOOM_MAX_SELL_RETRY_COUNT",
                cls.max_sell_retry_count,
            ),
            sell_retry_interval_sec=_env_int(
                "KIWOOM_SELL_RETRY_INTERVAL_SEC",
                cls.sell_retry_interval_sec,
            ),
            sell_unfilled_timeout_sec=_env_int(
                "KIWOOM_SELL_UNFILLED_TIMEOUT_SEC",
                cls.sell_unfilled_timeout_sec,
            ),
            cancel_replace_on_retry=_env_bool(
                "KIWOOM_CANCEL_REPLACE_ON_RETRY",
                cls.cancel_replace_on_retry,
            ),
            escalate_after_retry_count=_env_int(
                "KIWOOM_ESCALATE_AFTER_RETRY_COUNT",
                cls.escalate_after_retry_count,
            ),
            block_new_buys_on_exit_escalation=_env_bool(
                "KIWOOM_BLOCK_NEW_BUYS_ON_EXIT_ESCALATION",
                cls.block_new_buys_on_exit_escalation,
            ),
            allow_closing_auction_emergency_exit=_env_bool(
                "KIWOOM_ALLOW_CLOSING_AUCTION_EMERGENCY_EXIT",
                cls.allow_closing_auction_emergency_exit,
            ),
            allow_new_buy_after_closing_auction=_env_bool(
                "KIWOOM_ALLOW_NEW_BUY_AFTER_CLOSING_AUCTION",
                cls.allow_new_buy_after_closing_auction,
            ),
            stop_sell_allowed_during_no_buy_window=_env_bool(
                "KIWOOM_STOP_SELL_ALLOWED_DURING_NO_BUY_WINDOW",
                cls.stop_sell_allowed_during_no_buy_window,
            ),
            time_policy_enabled=_env_bool(
                "KIWOOM_TIME_POLICY_ENABLED",
                cls.time_policy_enabled,
            ),
            time_policy_config_version=_env_str(
                "KIWOOM_TIME_POLICY_CONFIG_VERSION",
                cls.time_policy_config_version,
            ),
            trading_timezone=_env_str(
                "KIWOOM_TRADING_TIMEZONE",
                cls.trading_timezone,
            ),
            krx_regular_open=_env_str(
                "KIWOOM_KRX_REGULAR_OPEN",
                cls.krx_regular_open,
            ),
            krx_regular_close=_env_str(
                "KIWOOM_KRX_REGULAR_CLOSE",
                cls.krx_regular_close,
            ),
            candidate_capture_start=_env_str(
                "KIWOOM_CANDIDATE_CAPTURE_START",
                cls.candidate_capture_start,
            ),
            candidate_capture_end=_env_str(
                "KIWOOM_CANDIDATE_CAPTURE_END",
                cls.candidate_capture_end,
            ),
            entry_windows=_env_str(
                "KIWOOM_ENTRY_WINDOWS",
                cls.entry_windows,
            ),
            no_new_entry_after=_env_str(
                "KIWOOM_NO_NEW_ENTRY_AFTER",
                cls.no_new_entry_after,
            ),
            force_exit_start=_env_str(
                "KIWOOM_FORCE_EXIT_START",
                cls.force_exit_start,
            ),
            force_exit_deadline=_env_str(
                "KIWOOM_FORCE_EXIT_DEADLINE",
                cls.force_exit_deadline,
            ),
            closing_auction_start=_env_str(
                "KIWOOM_CLOSING_AUCTION_START",
                cls.closing_auction_start,
            ),
            closing_auction_end=_env_str(
                "KIWOOM_CLOSING_AUCTION_END",
                cls.closing_auction_end,
            ),
            allow_after_hours_entry=_env_bool(
                "KIWOOM_ALLOW_AFTER_HOURS_ENTRY",
                cls.allow_after_hours_entry,
            ),
            allow_nxt_trading=_env_bool(
                "KIWOOM_ALLOW_NXT_TRADING",
                cls.allow_nxt_trading,
            ),
            krx_holidays=_env_str("KIWOOM_KRX_HOLIDAYS", cls.krx_holidays),
        )


TRADE_CONFIG = TradeConfig.from_env()
