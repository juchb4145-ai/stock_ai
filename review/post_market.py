from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sector_theme_maps import (
    load_sector_rows,
    load_theme_rows,
    validate_sector_map,
    validate_theme_map,
)

from .structured_log import iter_structured_events


CONDITION_CAPTURE_DEFAULT = Path("data") / "condition_captures.csv"
TRADE_LOG_DEFAULT = Path("data") / "trade_log.csv"
MAIN_LOG_DEFAULT = Path("data") / "main.log"
INTRADAY_DIR_DEFAULT = Path("data") / "intraday"
POST_MARKET_OUTPUT_DEFAULT = Path("reports") / "post_market"
SECTOR_MAP_DEFAULT = Path("data") / "sector_map.csv"
THEME_MAP_DEFAULT = Path("data") / "theme_map.csv"

MODE_PAPER = "paper"
MODE_LIVE = "live"
MODE_CHOICES = (MODE_PAPER, MODE_LIVE, "all")

MISSING_TEXT = "missing"
TIME_POLICY_HIGH_MFE_PAPER_MIN_MFE_PCT = 0.02

BLOCK_CHASE_REASON_CODES = {
    "block_chase_signal_candle_top",
    "block_chase_too_extended",
    "block_chase_upper_wick",
    "wait_pullback_too_extended",
    "block_chase_distance",
}
DATA_QUALITY_REASON_CODES = {
    "MISSING_CAPTURE_PRICE",
    "MISSING_VWAP",
    "MISSING_VOLUME_RATIO",
    "MISSING_TRADE_STRENGTH",
    "MISSING_DECISION_TRACE",
    "MISSING_MARKET_METRICS",
    "MISSING_PRIOR_HIGH",
    "missing_volume_ratio",
    "invalid_volume_ratio",
    "missing_turnover_speed",
    "missing_vwap",
    "missing_candle_cache",
    "missing_wick_risk",
    "missing_prior_high",
}
TIME_POLICY_REASON_CODES = {
    "TIME_POLICY_PRE_MOMENTUM_BLOCK",
    "TIME_POLICY_ENTRY_BLOCK",
    "TIME_POLICY_ANALYSIS_ONLY",
    "BLOCK_PRE_OPEN",
    "BLOCK_OPENING_STABILIZATION",
    "BLOCK_AFTER_ENTRY_CUTOFF",
    "BLOCK_CLOSING_AUCTION",
    "BLOCK_AFTER_MARKET",
    "BLOCK_NON_TRADING_DAY",
    "ALLOW_MANAGE_ONLY",
    "TOO_LATE_FOR_ENTRY_WINDOW",
}
ORDER_GUARD_REASON_CODES = {
    "missing_final_entry_decision",
    "daily_buy_limit_exceeded",
    "daily_loss_limit_exceeded",
    "duplicate_position",
    "pending_order_exists",
    "reentry_cooldown",
    "position_limit_exceeded",
    "time_policy_block",
    "missing_live_account_state",
    "daily_buy_limit",
    "daily_loss_limit",
    "position_limit",
}

OLD_CONDITION_FIELDS = [
    "logged_at",
    "event",
    "captured_at",
    "captured_time",
    "code",
    "name",
    "condition_name",
    "condition_index",
    "event_type",
    "screen_no",
    "capture_price",
    "entry_trigger_price",
    "chejan_strength",
    "accum_volume",
    "source",
]

NEW_CONDITION_FIELDS = [
    "logged_at",
    "event",
    "source_event",
    "created_at",
    "candidate_id",
    "symbol",
    "symbol_name",
    "detected_at",
    "captured_at",
    "captured_time",
    "code",
    "name",
    "condition_name",
    "strategy_name",
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
    "candidate_role",
    "time_policy_reason",
    "entry_allowed",
    "capture_allowed",
    "manage_allowed",
    "analysis_allowed",
]

MARKET_CONTEXT_REVIEW_FIELDS = [
    "symbol_market",
    "primary_index_code",
    "primary_market_regime",
    "primary_market_pct",
    "primary_market_slope_1m",
    "primary_market_slope_3m",
    "primary_market_drawdown_from_high",
    "kospi_regime",
    "kospi_pct",
    "kospi_slope_1m",
    "kospi_slope_3m",
    "kospi_drawdown_from_high",
    "kosdaq_regime",
    "kosdaq_pct",
    "kosdaq_slope_1m",
    "kosdaq_slope_3m",
    "kosdaq_drawdown_from_high",
]

SECTOR_CONTEXT_REVIEW_FIELDS = [
    "sector_code",
    "sector_name",
    "sector_index_code",
    "sector_pct",
    "sector_slope_1m",
    "sector_slope_3m",
    "sector_drawdown_from_high",
    "sector_relative_strength_vs_primary",
    "sector_ranked_count",
]

THEME_CONTEXT_REVIEW_FIELDS = [
    "primary_theme",
    "theme_names",
    "theme_member_count",
    "theme_active_count",
    "theme_rising_count",
    "theme_falling_count",
    "theme_avg_return",
    "theme_top_return",
    "theme_top_turnover",
    "theme_leader_code",
    "theme_leader_return",
]

REVIEW_CONTEXT_FIELDS = (
    MARKET_CONTEXT_REVIEW_FIELDS
    + SECTOR_CONTEXT_REVIEW_FIELDS
    + THEME_CONTEXT_REVIEW_FIELDS
)

REVIEW_COLUMNS = [
    "mode",
    "symbol",
    "symbol_name",
    "condition_name",
    "strategy_name",
    "candidate_id",
    "candidate_role",
    "source_event",
    "candidate_lifecycle",
    "recovery_watch_count",
    "recovery_watch_reasons",
    "recovery_watch_delay_seconds",
    "recovery_watch_last_at",
    "join_quality",
    "detected_at",
    "capture_price",
    "current_price",
    *REVIEW_CONTEXT_FIELDS,
    "traded",
    "final_decision",
    "final_reason",
    "blocked_by",
    "reason_code",
    "decision_trace",
    "entry_time",
    "exit_time",
    "entry_reason",
    "exit_reason",
    "exit_reason_code",
    "exit_type",
    "stop_reason",
    "exit_policy_source",
    "sell_retry_count",
    "unfilled_exit_qty",
    "sell_order_result",
    "exit_order_no",
    "exit_decision_trace",
    "entry_price",
    "exit_price",
    "realized_pnl",
    "realized_pnl_pct",
    "close_price",
    "return_to_close_pct",
    "high_after_signal",
    "low_after_signal",
    "mfe_pct",
    "mae_pct",
    "time_to_high_min",
    "time_to_low_min",
    "return_after_5m",
    "return_after_10m",
    "return_after_30m",
    "return_after_60m",
    "volume_ratio",
    "turnover_speed_per_min",
    "turnover_rank_sector",
    "trade_strength",
    "spread_rate",
    "vwap",
    "prior_high",
    "prior_high_source",
    "chase_risk_score",
    "high_distance_pct",
    "upper_wick_ratio",
    "candle_cache_available",
    "market_data_available",
    "orderbook_available",
    "one_min_reversal",
    "entry_type",
    "position_size_multiplier",
    "market_regime",
    "market_gate_action",
    "market_gate_reason",
    "sector_regime",
    "sector_gate_action",
    "sector_gate_reason",
    "theme_regime",
    "theme_gate_action",
    "theme_gate_reason",
    "time_policy_reason",
    "time_policy_source",
    "order_guard_reason",
    "missed_reason_detail",
    "block_source",
    "recoverable",
    "would_have_passed_if_time_policy_relaxed",
    "would_have_passed_if_order_guard_relaxed",
    "order_guard_rule",
    "order_guard_recoverable",
    "blocked_after_buy_ready",
    "time_bucket",
    "is_theme_leader",
    "theme_coverage_status",
    "data_quality",
    "missed_opportunity",
    "review_category",
]


@dataclass(frozen=True)
class IntradayBar:
    dt: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class ReviewCandidate:
    internal_id: str
    symbol: str
    symbol_name: str = ""
    condition_name: str = ""
    candidate_id: Optional[str] = None
    strategy_name: str = ""
    strategy_name_fallback_used: bool = False
    source_event: str = ""
    candidate_role: str = ""
    source_time_policy_reason: str = ""
    context_fields: Dict[str, object] = field(default_factory=dict)
    join_methods: List[str] = field(default_factory=list)
    lifecycle_events: List[str] = field(default_factory=list)
    detected_at: Optional[datetime] = None
    capture_price: Optional[float] = None
    source_rows: List[Dict[str, str]] = field(default_factory=list)
    candidate_events: List[Dict[str, object]] = field(default_factory=list)
    time_policy_events: List[Dict[str, object]] = field(default_factory=list)
    momentum_events: List[Dict[str, object]] = field(default_factory=list)
    final_events: List[Dict[str, object]] = field(default_factory=list)
    guard_events: List[Dict[str, object]] = field(default_factory=list)


@dataclass
class TradeSummary:
    mode: str
    symbol: str
    candidate_id: Optional[str] = None
    symbol_name: str = ""
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    quantity: Optional[int] = None
    exit_quantity: Optional[int] = None
    realized_pnl: Optional[float] = None
    realized_pnl_pct: Optional[float] = None
    entry_reason: str = ""
    exit_reason: str = ""
    exit_reason_code: str = ""
    exit_type: str = ""
    stop_reason: str = ""
    exit_policy_source: str = ""
    sell_retry_count: Optional[int] = None
    unfilled_exit_qty: Optional[int] = None
    sell_order_result: str = ""
    exit_order_no: str = ""
    exit_decision_trace: Any = None
    source: str = ""


@dataclass
class PriceFlow:
    current_price_at_signal: Optional[float] = None
    vwap_at_signal: Optional[float] = None
    prior_high_at_signal: Optional[float] = None
    volume_ratio_at_signal: Optional[float] = None
    upper_wick_ratio_at_signal: Optional[float] = None
    candle_cache_available: bool = False
    market_data_available: bool = False
    close_price: Optional[float] = None
    return_to_close_pct: Optional[float] = None
    high_after_signal: Optional[float] = None
    low_after_signal: Optional[float] = None
    mfe_pct: Optional[float] = None
    mae_pct: Optional[float] = None
    time_to_high_min: Optional[float] = None
    time_to_low_min: Optional[float] = None
    return_after_5m: Optional[float] = None
    return_after_10m: Optional[float] = None
    return_after_30m: Optional[float] = None
    return_after_60m: Optional[float] = None
    data_quality: List[str] = field(default_factory=list)


@dataclass
class ReviewRow:
    mode: str
    symbol: str
    symbol_name: str
    condition_name: str
    strategy_name: str
    candidate_id: Optional[str]
    candidate_role: str
    source_event: str
    candidate_lifecycle: str
    recovery_watch_count: int
    recovery_watch_reasons: str
    recovery_watch_delay_seconds: Optional[float]
    recovery_watch_last_at: Optional[datetime]
    join_quality: str
    detected_at: Optional[datetime]
    capture_price: Optional[float]
    current_price: Optional[float]
    context_fields: Dict[str, object]
    traded: bool
    final_decision: Optional[str]
    final_reason: str
    blocked_by: str
    reason_code: str
    decision_trace: Any
    entry_time: Optional[datetime]
    exit_time: Optional[datetime]
    entry_reason: str
    exit_reason: str
    exit_reason_code: str
    exit_type: str
    stop_reason: str
    exit_policy_source: str
    sell_retry_count: Optional[int]
    unfilled_exit_qty: Optional[int]
    sell_order_result: str
    exit_order_no: str
    exit_decision_trace: Any
    entry_price: Optional[float]
    exit_price: Optional[float]
    realized_pnl: Optional[float]
    realized_pnl_pct: Optional[float]
    close_price: Optional[float]
    return_to_close_pct: Optional[float]
    high_after_signal: Optional[float]
    low_after_signal: Optional[float]
    mfe_pct: Optional[float]
    mae_pct: Optional[float]
    time_to_high_min: Optional[float]
    time_to_low_min: Optional[float]
    return_after_5m: Optional[float]
    return_after_10m: Optional[float]
    return_after_30m: Optional[float]
    return_after_60m: Optional[float]
    volume_ratio: Optional[float]
    turnover_speed_per_min: Optional[float]
    turnover_rank_sector: Optional[float]
    trade_strength: Optional[float]
    spread_rate: Optional[float]
    vwap: Optional[float]
    prior_high: Optional[float]
    prior_high_source: str
    chase_risk_score: Optional[float]
    high_distance_pct: Optional[float]
    upper_wick_ratio: Optional[float]
    candle_cache_available: Optional[bool]
    market_data_available: Optional[bool]
    orderbook_available: Optional[bool]
    one_min_reversal: Optional[bool]
    entry_type: str
    position_size_multiplier: Optional[float]
    market_regime: str
    market_gate_action: str
    market_gate_reason: str
    sector_regime: str
    sector_gate_action: str
    sector_gate_reason: str
    theme_regime: str
    theme_gate_action: str
    theme_gate_reason: str
    time_policy_reason: str
    time_policy_source: str
    order_guard_reason: str
    missed_reason_detail: str
    block_source: str
    recoverable: bool
    would_have_passed_if_time_policy_relaxed: bool
    would_have_passed_if_order_guard_relaxed: bool
    order_guard_rule: str
    order_guard_recoverable: bool
    blocked_after_buy_ready: bool
    time_bucket: str
    is_theme_leader: bool
    theme_coverage_status: str
    data_quality: List[str]
    missed_opportunity: bool
    review_category: str

    def as_dict(self) -> Dict[str, object]:
        out = {
            "mode": self.mode,
            "symbol": self.symbol,
            "symbol_name": self.symbol_name,
            "condition_name": self.condition_name,
            "strategy_name": self.strategy_name,
            "candidate_id": self.candidate_id,
            "candidate_role": self.candidate_role,
            "source_event": self.source_event,
            "candidate_lifecycle": self.candidate_lifecycle,
            "recovery_watch_count": self.recovery_watch_count,
            "recovery_watch_reasons": self.recovery_watch_reasons,
            "recovery_watch_delay_seconds": self.recovery_watch_delay_seconds,
            "recovery_watch_last_at": _format_dt(self.recovery_watch_last_at),
            "join_quality": self.join_quality,
            "detected_at": _format_dt(self.detected_at),
            "capture_price": self.capture_price,
            "current_price": self.current_price,
            "traded": self.traded,
            "final_decision": self.final_decision,
            "final_reason": self.final_reason,
            "blocked_by": self.blocked_by,
            "reason_code": self.reason_code,
            "decision_trace": self.decision_trace,
            "entry_time": _format_dt(self.entry_time),
            "exit_time": _format_dt(self.exit_time),
            "entry_reason": self.entry_reason,
            "exit_reason": self.exit_reason,
            "exit_reason_code": self.exit_reason_code,
            "exit_type": self.exit_type,
            "stop_reason": self.stop_reason,
            "exit_policy_source": self.exit_policy_source,
            "sell_retry_count": self.sell_retry_count,
            "unfilled_exit_qty": self.unfilled_exit_qty,
            "sell_order_result": self.sell_order_result,
            "exit_order_no": self.exit_order_no,
            "exit_decision_trace": self.exit_decision_trace,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "realized_pnl": self.realized_pnl,
            "realized_pnl_pct": self.realized_pnl_pct,
            "close_price": self.close_price,
            "return_to_close_pct": self.return_to_close_pct,
            "high_after_signal": self.high_after_signal,
            "low_after_signal": self.low_after_signal,
            "mfe_pct": self.mfe_pct,
            "mae_pct": self.mae_pct,
            "time_to_high_min": self.time_to_high_min,
            "time_to_low_min": self.time_to_low_min,
            "return_after_5m": self.return_after_5m,
            "return_after_10m": self.return_after_10m,
            "return_after_30m": self.return_after_30m,
            "return_after_60m": self.return_after_60m,
            "volume_ratio": self.volume_ratio,
            "turnover_speed_per_min": self.turnover_speed_per_min,
            "turnover_rank_sector": self.turnover_rank_sector,
            "trade_strength": self.trade_strength,
            "spread_rate": self.spread_rate,
            "vwap": self.vwap,
            "prior_high": self.prior_high,
            "prior_high_source": self.prior_high_source,
            "chase_risk_score": self.chase_risk_score,
            "high_distance_pct": self.high_distance_pct,
            "upper_wick_ratio": self.upper_wick_ratio,
            "candle_cache_available": self.candle_cache_available,
            "market_data_available": self.market_data_available,
            "orderbook_available": self.orderbook_available,
            "one_min_reversal": self.one_min_reversal,
            "entry_type": self.entry_type,
            "position_size_multiplier": self.position_size_multiplier,
            "market_regime": self.market_regime,
            "market_gate_action": self.market_gate_action,
            "market_gate_reason": self.market_gate_reason,
            "sector_regime": self.sector_regime,
            "sector_gate_action": self.sector_gate_action,
            "sector_gate_reason": self.sector_gate_reason,
            "theme_regime": self.theme_regime,
            "theme_gate_action": self.theme_gate_action,
            "theme_gate_reason": self.theme_gate_reason,
            "time_policy_reason": self.time_policy_reason,
            "time_policy_source": self.time_policy_source,
            "order_guard_reason": self.order_guard_reason,
            "missed_reason_detail": self.missed_reason_detail,
            "block_source": self.block_source,
            "recoverable": self.recoverable,
            "would_have_passed_if_time_policy_relaxed": self.would_have_passed_if_time_policy_relaxed,
            "would_have_passed_if_order_guard_relaxed": self.would_have_passed_if_order_guard_relaxed,
            "order_guard_rule": self.order_guard_rule,
            "order_guard_recoverable": self.order_guard_recoverable,
            "blocked_after_buy_ready": self.blocked_after_buy_ready,
            "time_bucket": self.time_bucket,
            "is_theme_leader": self.is_theme_leader,
            "theme_coverage_status": self.theme_coverage_status,
            "data_quality": list(self.data_quality),
            "missed_opportunity": self.missed_opportunity,
            "review_category": self.review_category,
        }
        for field_name in REVIEW_CONTEXT_FIELDS:
            out[field_name] = self.context_fields.get(field_name, "")
        return out


@dataclass
class ReviewPaths:
    csv: Path
    markdown: Path
    json: Optional[Path] = None
    extra_csv: Dict[str, Path] = field(default_factory=dict)


@dataclass
class ReviewResult:
    mode: str
    date: str
    rows: List[ReviewRow]
    paths: Optional[ReviewPaths] = None
    data_source_status: Dict[str, Dict[str, object]] = field(default_factory=dict)


@dataclass
class StaticReviewContext:
    sector_by_symbol: Dict[str, Dict[str, str]] = field(default_factory=dict)
    themes_by_symbol: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)
    theme_member_counts: Dict[str, int] = field(default_factory=dict)


def collect_data_source_status(
    *,
    sector_map_path: str | Path = SECTOR_MAP_DEFAULT,
    theme_map_path: str | Path = THEME_MAP_DEFAULT,
) -> Dict[str, Dict[str, object]]:
    statuses: Dict[str, Dict[str, object]] = {}
    validators = (
        ("sector_map", sector_map_path, validate_sector_map),
        ("theme_map", theme_map_path, validate_theme_map),
    )
    for source_name, path, validator in validators:
        try:
            report = validator(str(path))
            statuses[source_name] = {
                "status": report.status(),
                "path": report.path,
                "exists": report.exists,
                "data_rows": report.data_rows,
                "valid_rows": report.valid_rows,
                "invalid_rows": report.invalid_rows,
                "missing_columns": list(report.missing_columns),
                "ok": report.ok,
            }
        except Exception as exc:
            statuses[source_name] = {
                "status": "error",
                "path": str(path),
                "exists": Path(path).exists(),
                "data_rows": 0,
                "valid_rows": 0,
                "invalid_rows": 0,
                "missing_columns": [],
                "ok": False,
                "error": str(exc),
            }
    return statuses


def load_static_review_context(
    sector_map_path: str | Path = SECTOR_MAP_DEFAULT,
    theme_map_path: str | Path = THEME_MAP_DEFAULT,
) -> StaticReviewContext:
    """Load static sector/theme identity maps for post-market row enrichment.

    This deliberately enriches identity fields only. Regime/action/reason fields
    come from live structured logs and are not recomputed here.
    """
    context = StaticReviewContext()
    if validate_sector_map(str(sector_map_path)).ok:
        try:
            for row in load_sector_rows(str(sector_map_path)):
                symbol = _normalize_symbol(row.get("code"))
                if not symbol:
                    continue
                context.sector_by_symbol[symbol] = {
                    "sector_code": str(row.get("sector_code") or "").strip(),
                    "sector_name": _clean_static_label(row.get("sector_name")),
                    "sector_index_code": str(row.get("sector_index_code") or "").strip(),
                }
        except Exception:
            context.sector_by_symbol.clear()
    if validate_theme_map(str(theme_map_path)).ok:
        try:
            for row in load_theme_rows(str(theme_map_path)):
                symbol = _normalize_symbol(row.get("code"))
                theme_name = _clean_static_label(row.get("theme_name"))
                if not symbol or not theme_name:
                    continue
                item = {
                    "theme_name": theme_name,
                    "code": symbol,
                    "role": str(row.get("role") or "member").strip() or "member",
                }
                context.themes_by_symbol.setdefault(symbol, []).append(item)
                context.theme_member_counts[theme_name] = context.theme_member_counts.get(theme_name, 0) + 1
        except Exception:
            context.themes_by_symbol.clear()
            context.theme_member_counts.clear()
    return context


def static_context_for_symbol(symbol: str, static_context: StaticReviewContext) -> Dict[str, object]:
    normalized = _normalize_symbol(symbol)
    out: Dict[str, object] = {}
    sector = static_context.sector_by_symbol.get(normalized)
    if sector:
        out.update({key: value for key, value in sector.items() if str(value or "").strip()})
    themes = static_context.themes_by_symbol.get(normalized, [])
    if themes:
        theme_names = [theme["theme_name"] for theme in themes if theme.get("theme_name")]
        primary = next((theme for theme in themes if str(theme.get("role") or "").lower() == "leader"), themes[0])
        primary_theme = str(primary.get("theme_name") or "").strip()
        if theme_names:
            out["theme_names"] = ";".join(theme_names)
        if primary_theme:
            out["primary_theme"] = primary_theme
            out["theme_member_count"] = static_context.theme_member_counts.get(primary_theme, len(themes))
            if str(primary.get("role") or "").lower() == "leader":
                out["theme_leader_code"] = normalized
    return out


def merge_missing_context_fields(existing: Dict[str, object], static_fields: Dict[str, object]) -> Dict[str, object]:
    merged = dict(existing or {})
    for key, value in (static_fields or {}).items():
        if _is_missing_context_value(key, merged.get(key)):
            merged[key] = value
    return merged


def _clean_static_label(value: object) -> str:
    return str(value or "").strip().rstrip("|").strip()


def _is_missing_context_value(key: str, value: object) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    if not text:
        return True
    if key == "theme_member_count" and text in {"0", "0.0"}:
        return True
    return False


def _normalize_symbol(value: object) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return ""
    if text.startswith("A") and len(text) == 7 and text[1:].isalnum():
        text = text[1:]
    if text.isdigit():
        return text.zfill(6)
    return text


def _parse_float(value: object) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_int(value: object) -> Optional[int]:
    number = _parse_float(value)
    if number is None:
        return None
    return int(number)


def _parse_jsonish(value: object) -> Any:
    if isinstance(value, (dict, list)):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return text


def _apply_exit_fields(trade: TradeSummary, row: Dict[str, str]) -> None:
    trade.exit_reason_code = str(row.get("exit_reason_code") or row.get("reason_code") or "")
    trade.exit_type = str(row.get("exit_type") or "")
    trade.stop_reason = str(row.get("stop_reason") or "")
    trade.exit_policy_source = str(row.get("exit_policy_source") or "")
    trade.sell_retry_count = _parse_int(row.get("sell_retry_count"))
    trade.unfilled_exit_qty = _parse_int(row.get("unfilled_exit_qty"))
    trade.sell_order_result = str(row.get("sell_order_result") or row.get("order_result") or row.get("order_status") or "")
    trade.exit_order_no = str(row.get("exit_order_no") or row.get("order_no") or "")
    trade.exit_decision_trace = _parse_jsonish(row.get("exit_decision_trace"))


def _parse_datetime(value: object, *, target_date: str = "") -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, (int, float)):
        if float(value) <= 0:
            return None
        return datetime.fromtimestamp(float(value))
    text = str(value).strip()
    if not text:
        return None
    number = _parse_float(text)
    if number is not None and text.replace(".", "", 1).isdigit() and number > 1_000_000:
        return datetime.fromtimestamp(number)
    cleaned = text.replace("T", " ")
    if "+" in cleaned:
        cleaned = cleaned.split("+", 1)[0]
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y%m%d%H%M%S",
        "%H%M%S",
        "%H:%M:%S",
    ):
        try:
            parsed = datetime.strptime(cleaned[:19], fmt)
        except ValueError:
            continue
        if parsed.year == 1900 and target_date:
            day = datetime.strptime(target_date, "%Y-%m-%d")
            parsed = parsed.replace(year=day.year, month=day.month, day=day.day)
        return parsed
    return None


def _format_dt(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _date_matches(value: Optional[datetime], target_date: str) -> bool:
    return value is not None and value.strftime("%Y-%m-%d") == target_date


def _safe_pct(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator - 1.0


def _condition_row_from_values(header: Sequence[str], values: Sequence[str]) -> Dict[str, str]:
    if len(values) >= len(NEW_CONDITION_FIELDS) and (
        "detected_at" not in header or len(values) > len(header)
    ):
        fields = NEW_CONDITION_FIELDS
    elif "detected_at" in header:
        fields = list(header)
    else:
        fields = OLD_CONDITION_FIELDS
    row = {field: "" for field in NEW_CONDITION_FIELDS}
    for idx, field in enumerate(fields):
        if idx < len(values):
            row[field] = values[idx]
    if not row.get("detected_at"):
        row["detected_at"] = row.get("captured_at", "")
    return row


def read_condition_rows(path: str | Path = CONDITION_CAPTURE_DEFAULT) -> List[Dict[str, str]]:
    capture_path = Path(path)
    if not capture_path.exists():
        return []
    rows: List[Dict[str, str]] = []
    with capture_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return []
        for values in reader:
            if not values:
                continue
            rows.append(_condition_row_from_values(header, values))
    return rows


def _context_fields_from_mapping(mapping: Dict[str, object]) -> Dict[str, object]:
    fields: Dict[str, object] = {}
    for key in REVIEW_CONTEXT_FIELDS:
        value = mapping.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            fields[key] = value
    return fields


def _merge_context_fields(*sources: Dict[str, object]) -> Dict[str, object]:
    merged: Dict[str, object] = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key, value in _context_fields_from_mapping(source).items():
            merged[key] = value
    return merged


def load_condition_candidates(
    *,
    target_date: str,
    path: str | Path = CONDITION_CAPTURE_DEFAULT,
) -> List[ReviewCandidate]:
    rows = read_condition_rows(path)
    candidates: List[ReviewCandidate] = []
    by_symbol: Dict[str, List[ReviewCandidate]] = defaultdict(list)
    sequence = 0

    for row in rows:
        event = str(row.get("event", "")).strip()
        symbol = _normalize_symbol(row.get("symbol") or row.get("code"))
        if not symbol:
            continue
        symbol_name = str(row.get("symbol_name") or row.get("name") or "")
        candidate_id = str(row.get("candidate_id") or "") or None
        raw_strategy_name = str(row.get("strategy_name") or "").strip()
        fallback_strategy_name = str(row.get("signal_source") or "").strip()
        strategy_name = raw_strategy_name or fallback_strategy_name
        strategy_name_fallback_used = not raw_strategy_name and bool(fallback_strategy_name)
        source_event = str(row.get("source_event") or event or "")
        candidate_role = str(row.get("candidate_role") or "").strip()
        source_time_policy_reason = str(row.get("time_policy_reason") or "").strip()
        detected_at = _parse_datetime(
            row.get("detected_at") or row.get("captured_at"),
            target_date=target_date,
        )
        if not _date_matches(detected_at, target_date):
            continue
        if event == "condition_detected":
            sequence += 1
            candidate = ReviewCandidate(
                internal_id=f"{target_date}:{sequence}:{symbol}",
                symbol=symbol,
                symbol_name=symbol_name,
                condition_name=str(row.get("condition_name", "") or ""),
                candidate_id=candidate_id,
                strategy_name=strategy_name,
                strategy_name_fallback_used=strategy_name_fallback_used,
                source_event=source_event,
                candidate_role=candidate_role,
                source_time_policy_reason=source_time_policy_reason,
                context_fields=_context_fields_from_mapping(row),
                detected_at=detected_at,
                capture_price=_parse_float(row.get("capture_price")),
                source_rows=[row],
            )
            if candidate.capture_price is not None and candidate.capture_price <= 0:
                candidate.capture_price = None
            candidates.append(candidate)
            by_symbol[symbol].append(candidate)
            continue
        if event != "capture_price":
            continue

        capture_price = _parse_float(row.get("capture_price"))
        target = None
        if candidate_id:
            target = next(
                (candidate for candidate in by_symbol.get(symbol, []) if candidate.candidate_id == candidate_id),
                None,
            )
        if target is None:
            target = _find_capture_target(by_symbol.get(symbol, []), row, detected_at)
        if target is None:
            sequence += 1
            target = ReviewCandidate(
                internal_id=f"{target_date}:{sequence}:{symbol}",
                symbol=symbol,
                symbol_name=symbol_name,
                condition_name=str(row.get("condition_name", "") or ""),
                candidate_id=candidate_id,
                strategy_name=strategy_name,
                strategy_name_fallback_used=strategy_name_fallback_used,
                source_event=source_event,
                candidate_role=candidate_role,
                source_time_policy_reason=source_time_policy_reason,
                context_fields=_context_fields_from_mapping(row),
                detected_at=detected_at,
                source_rows=[],
            )
            candidates.append(target)
            by_symbol[symbol].append(target)
        target.source_rows.append(row)
        if not target.symbol_name:
            target.symbol_name = symbol_name
        if not target.condition_name:
            target.condition_name = str(row.get("condition_name", "") or "")
        if not target.strategy_name:
            target.strategy_name = strategy_name
            target.strategy_name_fallback_used = strategy_name_fallback_used
        elif strategy_name_fallback_used:
            target.strategy_name_fallback_used = True
        if not target.source_event:
            target.source_event = source_event
        if not target.candidate_role:
            target.candidate_role = candidate_role
        if not target.source_time_policy_reason:
            target.source_time_policy_reason = source_time_policy_reason
        target.context_fields = _merge_context_fields(
            target.context_fields,
            _context_fields_from_mapping(row),
        )
        if target.capture_price is None and capture_price and capture_price > 0:
            target.capture_price = capture_price
        if target.candidate_id is None:
            target.candidate_id = candidate_id
    return candidates


def _find_capture_target(
    candidates: Sequence[ReviewCandidate],
    row: Dict[str, str],
    capture_time: Optional[datetime],
) -> Optional[ReviewCandidate]:
    condition_name = str(row.get("condition_name") or "")
    pending = [
        c
        for c in candidates
        if c.capture_price is None
        and (not condition_name or not c.condition_name or c.condition_name == condition_name)
    ]
    if pending:
        return min(
            pending,
            key=lambda c: abs(((c.detected_at or capture_time or datetime.min) - (capture_time or c.detected_at or datetime.min)).total_seconds()),
        )
    same_condition = [
        c
        for c in candidates
        if not condition_name or not c.condition_name or c.condition_name == condition_name
    ]
    if not same_condition:
        return None
    if capture_time is None:
        return same_condition[-1]
    before = [c for c in same_condition if c.detected_at and c.detected_at <= capture_time]
    return before[-1] if before else same_condition[-1]


def attach_structured_logs(
    candidates: Sequence[ReviewCandidate],
    *,
    target_date: str,
    main_log: str | Path = MAIN_LOG_DEFAULT,
) -> None:
    labels = {
        "momentum_entry_decision",
        "final_entry_decision",
        "entry_decision_trace",
        "would_order",
        "pre_live_order_submit",
        "order_blocked_by_time_policy",
        "candidate_duplicate_refresh",
        "candidate_registered",
        "candidate_expired",
        "candidate_lifecycle_summary",
        "candidate_recreated_after_ttl",
        "recovery_watch_queued",
        "time_policy_decision",
    }
    by_candidate_id: Dict[str, List[ReviewCandidate]] = defaultdict(list)
    for candidate in candidates:
        if candidate.candidate_id:
            by_candidate_id[candidate.candidate_id].append(candidate)
    by_symbol: Dict[str, List[ReviewCandidate]] = defaultdict(list)
    for candidate in candidates:
        by_symbol[candidate.symbol].append(candidate)
    for values in by_symbol.values():
        values.sort(key=lambda c: c.detected_at or datetime.min)

    for event in iter_structured_events(main_log, labels=labels, target_date=target_date):
        payload = dict(event.payload)
        event_date_ref = _parse_datetime(
            payload.get("timestamp") or payload.get("current_time"),
            target_date=target_date,
        )
        if event_date_ref is not None and not _date_matches(event_date_ref, target_date):
            continue
        symbol = _normalize_symbol(payload.get("symbol") or payload.get("code"))
        if not symbol:
            continue
        targets: List[ReviewCandidate] = []
        candidate_id = str(payload.get("candidate_id") or "").strip()
        join_method = ""
        if candidate_id:
            targets = list(by_candidate_id.get(candidate_id, []))
            if targets:
                join_method = "exact_candidate_id"
        if not targets:
            event_dt = _parse_datetime(
                payload.get("timestamp") or payload.get("current_time"),
                target_date=target_date,
            )
            detected_ref = _parse_datetime(payload.get("detected_at"), target_date=target_date)
            symbol_candidates = by_symbol.get(symbol, [])
            if candidate_id:
                symbol_candidates = [
                    candidate for candidate in symbol_candidates if not candidate.candidate_id
                ]
            target = _find_event_target(symbol_candidates, event_dt, detected_ref)
            if target is not None:
                if candidate_id:
                    join_method = "partial_match"
                elif event_dt is None and detected_ref is None:
                    join_method = "fallback_symbol_only"
                else:
                    join_method = "fallback_symbol_time"
                targets = [target]
        if not targets:
            continue
        payload["_event_label"] = event.label
        payload["_log_path"] = event.path
        for target in targets:
            _attach_structured_payload(target, payload, event.label, join_method)


def attach_trade_log_events(
    candidates: Sequence[ReviewCandidate],
    *,
    target_date: str,
    trade_log_path: str | Path = TRADE_LOG_DEFAULT,
) -> None:
    trade_path = Path(trade_log_path)
    if not trade_path.exists():
        return
    with trade_path.open("r", newline="", encoding="utf-8-sig") as f:
        rows = [
            dict(row)
            for row in csv.DictReader(f)
            if str(row.get("logged_at", "")).startswith(target_date)
            and str(row.get("event", "")) == "buy_skip"
        ]
    if not rows:
        return
    by_candidate_id: Dict[str, List[ReviewCandidate]] = defaultdict(list)
    by_symbol: Dict[str, List[ReviewCandidate]] = defaultdict(list)
    for candidate in candidates:
        if candidate.candidate_id:
            by_candidate_id[candidate.candidate_id].append(candidate)
        by_symbol[candidate.symbol].append(candidate)
    for values in by_symbol.values():
        values.sort(key=lambda c: c.detected_at or datetime.min)

    for row in rows:
        symbol = _normalize_symbol(row.get("code") or row.get("symbol"))
        if not symbol:
            continue
        payload: Dict[str, object] = dict(row)
        payload["timestamp"] = row.get("logged_at", "")
        payload["_event_label"] = "buy_skip"
        payload["_log_path"] = str(trade_path)
        candidate_id = str(row.get("candidate_id") or "").strip()
        targets: List[ReviewCandidate] = []
        join_method = ""
        if candidate_id:
            targets = list(by_candidate_id.get(candidate_id, []))
            if targets:
                join_method = "exact_candidate_id"
        if not targets:
            event_dt = _parse_datetime(row.get("logged_at"), target_date=target_date)
            target = _find_event_target(by_symbol.get(symbol, []), event_dt, None)
            if target is not None:
                targets = [target]
                join_method = "fallback_symbol_time" if event_dt else "fallback_symbol_only"
        for target in targets:
            _attach_structured_payload(target, payload, "buy_skip", join_method)


def _attach_structured_payload(
    target: ReviewCandidate,
    payload: Dict[str, object],
    label: str,
    join_method: str,
) -> None:
    event_payload = dict(payload)
    if join_method:
        target.join_methods.append(join_method)
    _hydrate_candidate_from_payload(target, event_payload, label)
    if label == "time_policy_decision":
        target.time_policy_events.append(event_payload)
    elif label == "momentum_entry_decision":
        target.momentum_events.append(event_payload)
    elif label == "final_entry_decision":
        target.final_events.append(event_payload)
    elif label == "recovery_watch_queued":
        target.lifecycle_events.append("recovery_watch_queued")
        target.candidate_events.append(event_payload)
    elif label.startswith("candidate_"):
        lifecycle_state = str(event_payload.get("lifecycle_state") or label).strip()
        target.lifecycle_events.append(lifecycle_state or label)
        target.candidate_events.append(event_payload)
    else:
        target.guard_events.append(event_payload)


def _hydrate_candidate_from_payload(
    target: ReviewCandidate,
    payload: Dict[str, object],
    label: str,
) -> None:
    if target.candidate_id is None:
        target.candidate_id = str(payload.get("candidate_id") or "") or None
    if not target.symbol_name:
        target.symbol_name = str(payload.get("symbol_name") or payload.get("name") or "")
    if not target.condition_name:
        target.condition_name = str(payload.get("condition_name") or "")
    strategy_name = str(payload.get("strategy_name") or "").strip()
    if strategy_name and not target.strategy_name:
        target.strategy_name = strategy_name
    candidate_role = str(payload.get("candidate_role") or "").strip()
    if candidate_role and not target.candidate_role:
        target.candidate_role = candidate_role
    target.context_fields = _merge_context_fields(
        target.context_fields,
        _context_fields_from_mapping(payload),
    )
    if not target.source_time_policy_reason:
        if label == "time_policy_decision":
            target.source_time_policy_reason = str(payload.get("reason_code") or "").strip()
        else:
            target.source_time_policy_reason = str(payload.get("time_policy_reason") or "").strip()
    if target.detected_at is None:
        target.detected_at = _parse_datetime(
            payload.get("first_detected_at")
            or payload.get("detected_at")
            or payload.get("timestamp"),
        )
    if target.capture_price is None or target.capture_price <= 0:
        for key in (
            "capture_price",
            "first_capture_price",
            "last_capture_price",
            "current_price",
        ):
            value = _parse_float(payload.get(key))
            if value is not None and value > 0:
                target.capture_price = value
                break


def _find_event_target(
    candidates: Sequence[ReviewCandidate],
    event_dt: Optional[datetime],
    detected_ref: Optional[datetime],
) -> Optional[ReviewCandidate]:
    if not candidates:
        return None
    ref = detected_ref or event_dt
    if ref is None:
        return candidates[-1]
    closest = min(
        candidates,
        key=lambda c: abs(((c.detected_at or ref) - ref).total_seconds()),
    )
    if detected_ref is not None:
        return closest
    before = [c for c in candidates if c.detected_at and c.detected_at <= ref]
    if before:
        return before[-1]
    return closest


def load_trades(
    *,
    target_date: str,
    mode: str,
    path: str | Path = TRADE_LOG_DEFAULT,
) -> List[TradeSummary]:
    trade_path = Path(path)
    if not trade_path.exists():
        return []
    with trade_path.open("r", newline="", encoding="utf-8-sig") as f:
        rows = [row for row in csv.DictReader(f) if str(row.get("logged_at", "")).startswith(target_date)]
    if mode == MODE_PAPER:
        return _load_paper_trades(rows)
    if mode == MODE_LIVE:
        return _load_live_trades(rows)
    raise ValueError(f"unsupported mode: {mode}")


def _load_paper_trades(rows: Sequence[Dict[str, str]]) -> List[TradeSummary]:
    trades: List[TradeSummary] = []
    open_by_symbol: Dict[str, TradeSummary] = {}
    for row in rows:
        if str(row.get("event", "")) != "would_order":
            continue
        side = str(row.get("side", "")).lower()
        symbol = _normalize_symbol(row.get("code"))
        if not symbol:
            continue
        logged_at = _parse_datetime(row.get("logged_at"))
        price = (
            _parse_float(row.get("executed_price"))
            or _parse_float(row.get("current_price"))
            or _parse_float(row.get("entry_price"))
            or _parse_float(row.get("order_price"))
        )
        if side == "buy":
            trade = TradeSummary(
                mode=MODE_PAPER,
                symbol=symbol,
                candidate_id=str(row.get("candidate_id") or "") or None,
                symbol_name=str(row.get("name") or ""),
                entry_time=logged_at,
                entry_price=price,
                quantity=_parse_int(row.get("quantity")),
                entry_reason=str(row.get("reason") or row.get("message") or ""),
                source="trade_log:would_order",
            )
            trades.append(trade)
            open_by_symbol[symbol] = trade
        elif side == "sell":
            trade = open_by_symbol.get(symbol)
            if trade is None:
                trade = TradeSummary(
                    mode=MODE_PAPER,
                    symbol=symbol,
                    candidate_id=str(row.get("candidate_id") or "") or None,
                    symbol_name=str(row.get("name") or ""),
                    source="trade_log:would_order",
                )
                trades.append(trade)
            trade.exit_time = logged_at
            trade.exit_price = price
            trade.exit_quantity = _parse_int(row.get("quantity"))
            trade.exit_reason = str(row.get("reason") or row.get("message") or "")
            _apply_exit_fields(trade, row)
            pct = _parse_float(row.get("profit_rate"))
            trade.realized_pnl_pct = pct
            _finalize_trade_pnl(trade)
            open_by_symbol.pop(symbol, None)
    return trades


def _load_live_trades(rows: Sequence[Dict[str, str]]) -> List[TradeSummary]:
    trades: List[TradeSummary] = []
    open_by_symbol: Dict[str, TradeSummary] = {}
    seen_fills = set()
    for row in rows:
        if str(row.get("event", "")) != "chejan":
            continue
        symbol = _normalize_symbol(row.get("code"))
        side = str(row.get("side", "")).lower()
        qty = _parse_int(row.get("executed_quantity"))
        price = _parse_float(row.get("executed_price"))
        if not symbol or side not in {"buy", "sell"} or not qty or not price:
            continue
        logged_at = _parse_datetime(row.get("logged_at"))
        dedup_key = (
            symbol,
            side,
            row.get("order_no", ""),
            row.get("logged_at", ""),
            qty,
            price,
        )
        if dedup_key in seen_fills:
            continue
        seen_fills.add(dedup_key)
        if side == "buy":
            trade = open_by_symbol.get(symbol)
            if trade is None:
                trade = TradeSummary(
                    mode=MODE_LIVE,
                    symbol=symbol,
                    candidate_id=str(row.get("candidate_id") or "") or None,
                    symbol_name=str(row.get("name") or ""),
                    entry_time=logged_at,
                    entry_price=price,
                    quantity=qty,
                    entry_reason=str(row.get("reason") or ""),
                    source="trade_log:chejan",
                )
                trades.append(trade)
                open_by_symbol[symbol] = trade
            else:
                old_qty = trade.quantity or 0
                new_qty = old_qty + qty
                if trade.entry_price is not None and new_qty > 0:
                    trade.entry_price = (trade.entry_price * old_qty + price * qty) / new_qty
                else:
                    trade.entry_price = price
                trade.quantity = new_qty
                if trade.entry_time is None or (logged_at and logged_at < trade.entry_time):
                    trade.entry_time = logged_at
        else:
            trade = open_by_symbol.get(symbol)
            if trade is None:
                trade = TradeSummary(
                    mode=MODE_LIVE,
                    symbol=symbol,
                    candidate_id=str(row.get("candidate_id") or "") or None,
                    symbol_name=str(row.get("name") or ""),
                    source="trade_log:chejan",
                )
                trades.append(trade)
            trade.exit_time = logged_at
            old_exit_qty = trade.exit_quantity or 0
            new_exit_qty = old_exit_qty + qty
            if trade.exit_price is not None and new_exit_qty > 0:
                trade.exit_price = (trade.exit_price * old_exit_qty + price * qty) / new_exit_qty
            else:
                trade.exit_price = price
            trade.exit_quantity = new_exit_qty
            trade.exit_reason = str(row.get("reason") or "")
            _apply_exit_fields(trade, row)
            pct = _parse_float(row.get("profit_rate"))
            if pct is not None:
                trade.realized_pnl_pct = pct
            _finalize_trade_pnl(trade)
            if trade.quantity and trade.exit_quantity and trade.exit_quantity >= trade.quantity:
                open_by_symbol.pop(symbol, None)
    return trades


def _finalize_trade_pnl(trade: TradeSummary) -> None:
    if trade.entry_price is None or trade.exit_price is None or trade.entry_price <= 0:
        return
    if trade.realized_pnl_pct is None:
        trade.realized_pnl_pct = trade.exit_price / trade.entry_price - 1.0
    qty = trade.exit_quantity or trade.quantity
    if qty:
        trade.realized_pnl = (trade.exit_price - trade.entry_price) * qty


def load_intraday_bars(
    *,
    target_date: str,
    symbol: str,
    intraday_dir: str | Path = INTRADAY_DIR_DEFAULT,
    timeframe: str = "1m",
) -> List[IntradayBar]:
    path = Path(intraday_dir) / target_date.replace("-", "") / f"{symbol}.csv"
    if not path.exists():
        return []
    bars: List[IntradayBar] = []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            dt = _parse_datetime(row.get("datetime") or row.get("at") or row.get("timestamp"))
            if dt is None:
                continue
            try:
                bar = IntradayBar(
                    dt=dt,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row.get("volume", 0) or 0),
                )
            except (KeyError, ValueError):
                continue
            bars.append(bar)
    bars.sort(key=lambda b: b.dt)
    if timeframe == "5m":
        return aggregate_bars(bars, minutes=5)
    return bars


def aggregate_bars(bars: Sequence[IntradayBar], *, minutes: int) -> List[IntradayBar]:
    grouped: Dict[datetime, List[IntradayBar]] = defaultdict(list)
    for bar in bars:
        bucket_minute = (bar.dt.minute // minutes) * minutes
        bucket = bar.dt.replace(minute=bucket_minute, second=0, microsecond=0)
        grouped[bucket].append(bar)
    out: List[IntradayBar] = []
    for bucket in sorted(grouped):
        items = sorted(grouped[bucket], key=lambda b: b.dt)
        out.append(
            IntradayBar(
                dt=bucket,
                open=items[0].open,
                high=max(b.high for b in items),
                low=min(b.low for b in items),
                close=items[-1].close,
                volume=sum(b.volume for b in items),
            )
        )
    return out


def compute_price_flow(
    *,
    detected_at: Optional[datetime],
    capture_price: Optional[float],
    bars: Sequence[IntradayBar],
) -> PriceFlow:
    flow = PriceFlow()
    if detected_at is None:
        flow.data_quality.append("missing_detected_at")
        return flow
    if not bars:
        flow.data_quality.append("missing_minute_bars")
        if capture_price is None or capture_price <= 0:
            flow.data_quality.append("missing_capture_price")
        return flow
    start = detected_at.replace(second=0, microsecond=0)
    after = [bar for bar in bars if bar.dt >= start]
    if not after:
        flow.data_quality.append("missing_bars_after_signal")
        if capture_price is None or capture_price <= 0:
            flow.data_quality.append("missing_capture_price")
        return flow
    flow.candle_cache_available = True
    flow.market_data_available = True
    signal_bar = after[0]
    flow.current_price_at_signal = signal_bar.close
    prior_bars = [bar for bar in bars if bar.dt < signal_bar.dt]
    lookback_prior = prior_bars[-5:]
    if lookback_prior:
        flow.prior_high_at_signal = max(bar.high for bar in lookback_prior)
        avg_volume = mean([bar.volume for bar in lookback_prior if bar.volume > 0] or [0.0])
        if avg_volume > 0 and signal_bar.volume > 0:
            flow.volume_ratio_at_signal = signal_bar.volume / avg_volume
    through_signal = [bar for bar in bars if bar.dt <= signal_bar.dt and bar.volume > 0]
    signal_volume = sum(bar.volume for bar in through_signal)
    if signal_volume > 0:
        flow.vwap_at_signal = sum(
            ((bar.high + bar.low + bar.close) / 3.0) * bar.volume
            for bar in through_signal
        ) / signal_volume
    if signal_bar.high > signal_bar.low:
        flow.upper_wick_ratio_at_signal = max(
            0.0,
            min(1.0, (signal_bar.high - signal_bar.close) / (signal_bar.high - signal_bar.low)),
        )
    if capture_price is None or capture_price <= 0:
        flow.data_quality.append("missing_capture_price")
        return flow
    high_bar = max(after, key=lambda b: b.high)
    low_bar = min(after, key=lambda b: b.low)
    close_price = after[-1].close
    flow.close_price = close_price
    flow.return_to_close_pct = _safe_pct(close_price, capture_price)
    flow.high_after_signal = high_bar.high
    flow.low_after_signal = low_bar.low
    flow.mfe_pct = _safe_pct(high_bar.high, capture_price)
    flow.mae_pct = _safe_pct(low_bar.low, capture_price)
    flow.time_to_high_min = max(0.0, (high_bar.dt - start).total_seconds() / 60.0)
    flow.time_to_low_min = max(0.0, (low_bar.dt - start).total_seconds() / 60.0)
    for minutes in (5, 10, 30, 60):
        value = _return_after(after, start + timedelta(minutes=minutes), capture_price)
        setattr(flow, f"return_after_{minutes}m", value)
    return flow


def _return_after(
    bars: Sequence[IntradayBar],
    target_time: datetime,
    capture_price: float,
) -> Optional[float]:
    for bar in bars:
        if bar.dt >= target_time:
            return _safe_pct(bar.close, capture_price)
    return None


def run_post_market_review(
    *,
    target_date: str,
    mode: str,
    output_dir: str | Path = POST_MARKET_OUTPUT_DEFAULT,
    condition_capture_path: str | Path = CONDITION_CAPTURE_DEFAULT,
    trade_log_path: str | Path = TRADE_LOG_DEFAULT,
    main_log_path: str | Path = MAIN_LOG_DEFAULT,
    intraday_dir: str | Path = INTRADAY_DIR_DEFAULT,
    sector_map_path: str | Path = SECTOR_MAP_DEFAULT,
    theme_map_path: str | Path = THEME_MAP_DEFAULT,
    min_missed_opportunity_pct: float = 0.05,
    timeframe: str = "1m",
    write_json: bool = False,
) -> ReviewResult:
    if mode not in {MODE_PAPER, MODE_LIVE}:
        raise ValueError("run_post_market_review expects paper or live mode")
    candidates = load_condition_candidates(target_date=target_date, path=condition_capture_path)
    attach_structured_logs(candidates, target_date=target_date, main_log=main_log_path)
    attach_trade_log_events(candidates, target_date=target_date, trade_log_path=trade_log_path)
    static_context = load_static_review_context(
        sector_map_path=sector_map_path,
        theme_map_path=theme_map_path,
    )
    for candidate in candidates:
        candidate.context_fields = merge_missing_context_fields(
            candidate.context_fields,
            static_context_for_symbol(candidate.symbol, static_context),
        )
    trades = load_trades(target_date=target_date, mode=mode, path=trade_log_path)
    trades_by_candidate = match_trades_to_candidates(candidates, trades)
    bars_cache: Dict[str, List[IntradayBar]] = {}
    rows: List[ReviewRow] = []
    for candidate in candidates:
        if candidate.symbol not in bars_cache:
            bars_cache[candidate.symbol] = load_intraday_bars(
                target_date=target_date,
                symbol=candidate.symbol,
                intraday_dir=intraday_dir,
                timeframe=timeframe,
            )
        flow = compute_price_flow(
            detected_at=candidate.detected_at,
            capture_price=candidate.capture_price,
            bars=bars_cache[candidate.symbol],
        )
        trade = trades_by_candidate.get(candidate.internal_id)
        rows.append(
            build_review_row(
                candidate=candidate,
                trade=trade,
                flow=flow,
                mode=mode,
                min_missed_opportunity_pct=min_missed_opportunity_pct,
            )
        )
    result = ReviewResult(
        mode=mode,
        date=target_date,
        rows=rows,
        data_source_status=collect_data_source_status(
            sector_map_path=sector_map_path,
            theme_map_path=theme_map_path,
        ),
    )
    paths = write_review_outputs(
        result,
        output_dir=output_dir,
        write_json=write_json,
    )
    result.paths = paths
    return result


def match_trades_to_candidates(
    candidates: Sequence[ReviewCandidate],
    trades: Sequence[TradeSummary],
) -> Dict[str, TradeSummary]:
    by_candidate_id: Dict[str, List[ReviewCandidate]] = defaultdict(list)
    for candidate in candidates:
        if candidate.candidate_id:
            by_candidate_id[candidate.candidate_id].append(candidate)
    by_symbol: Dict[str, List[ReviewCandidate]] = defaultdict(list)
    for candidate in candidates:
        by_symbol[candidate.symbol].append(candidate)
    for values in by_symbol.values():
        values.sort(key=lambda c: c.detected_at or datetime.min)
    for values in by_candidate_id.values():
        values.sort(key=lambda c: c.detected_at or datetime.min)

    out: Dict[str, TradeSummary] = {}
    for trade in trades:
        if trade.candidate_id:
            id_choices = by_candidate_id.get(trade.candidate_id, [])
            if id_choices:
                target_by_id = _find_event_target(
                    id_choices,
                    trade.entry_time or trade.exit_time,
                    None,
                )
                if target_by_id is not None:
                    target_by_id.join_methods.append("exact_candidate_id")
                    out[target_by_id.internal_id] = trade
                continue
        choices = by_symbol.get(trade.symbol, [])
        if not choices:
            continue
        ref = trade.entry_time or trade.exit_time
        if ref is None:
            target = choices[-1]
        else:
            before = [c for c in choices if c.detected_at and c.detected_at <= ref]
            target = before[-1] if before else min(
                choices,
                key=lambda c: abs(((c.detected_at or ref) - ref).total_seconds()),
            )
        if ref is None:
            target.join_methods.append("fallback_symbol_only")
        else:
            target.join_methods.append("fallback_symbol_time")
        out[target.internal_id] = trade
    return out


def build_review_row(
    *,
    candidate: ReviewCandidate,
    trade: Optional[TradeSummary],
    flow: PriceFlow,
    mode: str,
    min_missed_opportunity_pct: float,
) -> ReviewRow:
    final = _representative_final_event(candidate.final_events)
    momentum = _matching_momentum_event(candidate.momentum_events, final) if final else _latest_event(candidate.momentum_events)
    guard = _latest_event(candidate.guard_events)
    derived_metrics = _derived_metrics_from_flow(flow)
    metrics_source = momentum or derived_metrics
    context_fields = _merge_context_fields(candidate.context_fields, momentum, final, guard)
    recovery_events = _recovery_watch_events(candidate)
    latest_recovery = recovery_events[-1] if recovery_events else {}
    recovery_reasons = sorted(
        {
            str(event.get("reason_code") or "").strip()
            for event in recovery_events
            if str(event.get("reason_code") or "").strip()
        }
    )
    time_policy_event = _latest_time_policy_event(
        candidate,
        prefer_eval_filter=not bool(momentum),
    )
    time_policy_source = str(time_policy_event.get("source") or "").strip()
    time_policy_event_reason = str(time_policy_event.get("reason_code") or "").strip()
    source_time_policy_reason = str(candidate.source_time_policy_reason or "").strip()
    reason_code = _first_text(
        final.get("reason_code") if final else None,
        metrics_source.get("reason_code"),
        guard.get("reason_code") if guard else None,
        guard.get("guard_reason") if guard else None,
    )
    allowed_time_policy_reasons = {
        "ALLOW_ENTRY",
        "ALLOW_LATE_A_GRADE_ENTRY",
        "ALLOW_CANDIDATE_CAPTURE",
        "TIME_POLICY_DISABLED",
    }
    if not reason_code and not momentum:
        if (
            time_policy_source == "evaluate_time_filter"
            and time_policy_event_reason
            and time_policy_event_reason not in allowed_time_policy_reasons
        ):
            reason_code = "TIME_POLICY_PRE_MOMENTUM_BLOCK"
        elif str(candidate.candidate_role or "") == "analysis_only":
            reason_code = "TIME_POLICY_ANALYSIS_ONLY"
    final_decision = _final_decision_text(final, momentum)
    final_reason = _first_text(
        final.get("final_reason") if final else None,
        metrics_source.get("reason_detail"),
        guard.get("entry_reason") if guard else None,
    )
    if not final_reason and reason_code == "TIME_POLICY_PRE_MOMENTUM_BLOCK":
        final_reason = "Momentum evaluation skipped before strategy gate by TimePolicy {}".format(
            time_policy_event_reason or source_time_policy_reason
        ).strip()
    elif not final_reason and reason_code == "TIME_POLICY_ANALYSIS_ONLY":
        final_reason = "Analysis-only condition capture by TimePolicy {}".format(
            source_time_policy_reason or time_policy_event_reason
        ).strip()
    blocked_by = _first_text(
        final.get("blocked_by") if final else None,
        metrics_source.get("blocked_by"),
        guard.get("blocked_by") if guard else None,
    )
    if not blocked_by and reason_code.startswith("TIME_POLICY_"):
        blocked_by = "time_policy"
    time_policy_reason = _first_text(
        metrics_source.get("time_policy_reason_code"),
        time_policy_event_reason,
        source_time_policy_reason,
        guard.get("reason_code") if guard and guard.get("_event_label") == "order_blocked_by_time_policy" else None,
    )
    order_guard_reason = _first_text(
        guard.get("guard_reason") if guard else None,
        guard.get("reason_code") if guard else None,
        guard.get("reason") if guard else None,
    )
    decision_trace = _build_decision_trace(candidate, momentum=momentum, final=final, guard=guard)
    data_quality = list(flow.data_quality)
    if final and candidate.final_events and final is not _latest_event(candidate.final_events):
        data_quality.append("FINAL_READY_SUPERSEDED_BY_LATER_EVENT")
    if candidate.capture_price is None or candidate.capture_price <= 0:
        data_quality.append("MISSING_CAPTURE_PRICE")
    if candidate.strategy_name_fallback_used:
        data_quality.append("strategy_name_fallback_used")
    if metrics_source:
        if metrics_source.get("market_data_available") is False:
            data_quality.append("MISSING_MARKET_METRICS")
            data_quality.append("market_data_unavailable")
        if metrics_source.get("candle_cache_available") is False:
            data_quality.append("MISSING_CANDLE_CACHE")
        metric_checks = [
            ("vwap", "MISSING_VWAP"),
            ("volume_ratio", "MISSING_VOLUME_RATIO"),
            ("trade_strength", "MISSING_TRADE_STRENGTH"),
            ("spread_rate", "MISSING_SPREAD_RATE"),
            ("upper_wick_ratio", "MISSING_UPPER_WICK_RATIO"),
        ]
        for key, flag in metric_checks:
            if metrics_source.get(key) in {None, ""}:
                data_quality.append(flag)
        if metrics_source.get("prior_high") in {None, ""} and str(metrics_source.get("prior_high_source") or "") == "missing":
            data_quality.append("MISSING_PRIOR_HIGH")
    else:
        data_quality.append("MISSING_MARKET_METRICS")
    if not decision_trace:
        data_quality.append("MISSING_DECISION_TRACE")
    if flow.mfe_pct is None or flow.mae_pct is None:
        data_quality.append("MISSING_MFE_MAE")
    for value in (reason_code, final_reason, blocked_by):
        normalized = str(value or "").lower()
        if "missing" in normalized or "invalid" in normalized:
            data_quality.append(normalized.split()[0].upper())

    entry_price = trade.entry_price if trade else None
    exit_price = trade.exit_price if trade else None
    entry_time = trade.entry_time if trade else None
    exit_time = trade.exit_time if trade else None
    entry_reason = trade.entry_reason if trade else ""
    exit_reason = trade.exit_reason if trade else ""
    exit_reason_code = trade.exit_reason_code if trade else ""
    exit_type = trade.exit_type if trade else ""
    stop_reason = trade.stop_reason if trade else ""
    exit_policy_source = trade.exit_policy_source if trade else ""
    sell_retry_count = trade.sell_retry_count if trade else None
    unfilled_exit_qty = trade.unfilled_exit_qty if trade else None
    sell_order_result = trade.sell_order_result if trade else ""
    exit_order_no = trade.exit_order_no if trade else ""
    exit_decision_trace = trade.exit_decision_trace if trade else None
    realized_pnl = trade.realized_pnl if trade else None
    realized_pnl_pct = trade.realized_pnl_pct if trade else None
    traded = trade is not None and trade.entry_price is not None
    if trade is not None:
        if trade.entry_time is None or trade.entry_price is None:
            data_quality.append("missing_entry_fill")
        if trade.exit_time is None or trade.exit_price is None:
            data_quality.append("missing_exit_fill")
    if data_quality:
        data_quality.append("partial_data")
    canonical_quality = {
        "missing_capture_price": "MISSING_CAPTURE_PRICE",
        "missing_market_metrics": "MISSING_MARKET_METRICS",
        "missing_decision_trace": "MISSING_DECISION_TRACE",
        "missing_mfe_mae": "MISSING_MFE_MAE",
        "missing_minute_bars": "MISSING_MARKET_METRICS",
        "missing_bars_after_signal": "MISSING_MARKET_METRICS",
        "missing_detected_at": "MISSING_MARKET_METRICS",
        "missing_candle_cache": "MISSING_CANDLE_CACHE",
        "missing_prior_high": "MISSING_PRIOR_HIGH",
        "missing_vwap": "MISSING_VWAP",
        "missing_volume_ratio": "MISSING_VOLUME_RATIO",
        "missing_trade_strength": "MISSING_TRADE_STRENGTH",
    }
    data_quality = sorted(
        set(
            canonical_quality.get(str(x).strip().lower(), str(x).strip())
            for x in data_quality
            if str(x).strip()
        )
    )

    missed = bool(
        not traded
        and flow.mfe_pct is not None
        and flow.mfe_pct >= min_missed_opportunity_pct
    )
    category = classify_review_category(
        traded=traded,
        realized_pnl_pct=realized_pnl_pct,
        entry_price=entry_price,
        close_price=flow.close_price,
        reason_code=reason_code,
        blocked_by=blocked_by,
        final_decision=final_decision,
        time_policy_reason=time_policy_reason,
        order_guard_reason=order_guard_reason,
        data_quality=data_quality,
        mfe_pct=flow.mfe_pct,
        min_missed_opportunity_pct=min_missed_opportunity_pct,
        missed_opportunity=missed,
    )
    block_source = _block_source_for_row(
        review_category=category,
        blocked_by=blocked_by,
        reason_code=reason_code,
        time_policy_reason=time_policy_reason,
        order_guard_reason=order_guard_reason,
        data_quality=data_quality,
    )
    order_guard_rule = _normalize_order_guard_rule(order_guard_reason or blocked_by or reason_code)
    blocked_after_buy_ready = bool(
        not traded
        and block_source == "order_guard"
        and (
            str(final_decision or "").upper() == "BUY"
            or str(reason_code or "").upper() == "FINAL_BUY_READY"
        )
    )
    would_pass_time_relaxed = _would_have_passed_if_time_policy_relaxed(
        category=category,
        missed=missed,
        flow=flow,
        data_quality=data_quality,
    )
    would_pass_guard_relaxed = _would_have_passed_if_order_guard_relaxed(
        category=category,
        missed=missed,
        blocked_after_buy_ready=blocked_after_buy_ready,
        flow=flow,
        data_quality=data_quality,
    )
    recoverable = bool(would_pass_time_relaxed or would_pass_guard_relaxed or category in {"MISSED_OPPORTUNITY", "BAD_BLOCK_CHASE"})
    order_guard_recoverable = bool(would_pass_guard_relaxed and order_guard_rule not in {"daily_loss_limit", "missing_live_account_state"})
    theme_leader_code = str(context_fields.get("theme_leader_code") or "").strip()
    return ReviewRow(
        mode=mode,
        symbol=candidate.symbol,
        symbol_name=candidate.symbol_name,
        condition_name=candidate.condition_name,
        strategy_name=candidate.strategy_name,
        candidate_id=candidate.candidate_id,
        candidate_role=candidate.candidate_role,
        source_event=candidate.source_event,
        candidate_lifecycle=_candidate_lifecycle_text(candidate),
        recovery_watch_count=len(recovery_events),
        recovery_watch_reasons=";".join(recovery_reasons),
        recovery_watch_delay_seconds=_as_float(latest_recovery.get("delay_seconds")) if latest_recovery else None,
        recovery_watch_last_at=_event_timestamp(latest_recovery) if latest_recovery else None,
        join_quality=_join_quality_text(candidate),
        detected_at=candidate.detected_at,
        capture_price=candidate.capture_price,
        current_price=_as_float(metrics_source.get("current_price")),
        context_fields=context_fields,
        traded=traded,
        final_decision=final_decision,
        final_reason=final_reason,
        blocked_by=blocked_by,
        reason_code=reason_code,
        decision_trace=decision_trace,
        entry_time=entry_time,
        exit_time=exit_time,
        entry_reason=entry_reason,
        exit_reason=exit_reason,
        exit_reason_code=exit_reason_code,
        exit_type=exit_type,
        stop_reason=stop_reason,
        exit_policy_source=exit_policy_source,
        sell_retry_count=sell_retry_count,
        unfilled_exit_qty=unfilled_exit_qty,
        sell_order_result=sell_order_result,
        exit_order_no=exit_order_no,
        exit_decision_trace=exit_decision_trace,
        entry_price=entry_price,
        exit_price=exit_price,
        realized_pnl=realized_pnl,
        realized_pnl_pct=realized_pnl_pct,
        close_price=flow.close_price,
        return_to_close_pct=flow.return_to_close_pct,
        high_after_signal=flow.high_after_signal,
        low_after_signal=flow.low_after_signal,
        mfe_pct=flow.mfe_pct,
        mae_pct=flow.mae_pct,
        time_to_high_min=flow.time_to_high_min,
        time_to_low_min=flow.time_to_low_min,
        return_after_5m=flow.return_after_5m,
        return_after_10m=flow.return_after_10m,
        return_after_30m=flow.return_after_30m,
        return_after_60m=flow.return_after_60m,
        volume_ratio=_as_float(metrics_source.get("volume_ratio")),
        turnover_speed_per_min=_as_float(metrics_source.get("turnover_speed_per_min")),
        turnover_rank_sector=_as_float(
            _first_text(
                final.get("turnover_rank_sector") if final else None,
                momentum.get("turnover_rank_sector") if momentum else None,
                metrics_source.get("turnover_rank_sector"),
            )
        ),
        trade_strength=_as_float(metrics_source.get("trade_strength")),
        spread_rate=_as_float(metrics_source.get("spread_rate")),
        vwap=_as_float(metrics_source.get("vwap")),
        prior_high=_as_float(metrics_source.get("prior_high")),
        prior_high_source=str(metrics_source.get("prior_high_source") or ""),
        chase_risk_score=_as_float(metrics_source.get("chase_risk_score")),
        high_distance_pct=_as_float(metrics_source.get("high_distance_pct")),
        upper_wick_ratio=_as_float(metrics_source.get("upper_wick_ratio")),
        candle_cache_available=_as_bool(metrics_source.get("candle_cache_available")),
        market_data_available=_as_bool(metrics_source.get("market_data_available")),
        orderbook_available=_as_bool(metrics_source.get("orderbook_available")),
        one_min_reversal=_as_bool(metrics_source.get("one_min_reversal")),
        entry_type=str(metrics_source.get("entry_type") or ""),
        position_size_multiplier=_as_float(metrics_source.get("position_size_multiplier")),
        market_regime=_first_text(
            final.get("market_regime") if final else None,
            momentum.get("market_regime") if momentum else None,
            context_fields.get("primary_market_regime"),
        ),
        market_gate_action=_first_text(final.get("market_gate_action") if final else None, momentum.get("market_gate_action") if momentum else None),
        market_gate_reason=_first_text(final.get("market_gate_reason") if final else None, momentum.get("market_gate_reason") if momentum else None),
        sector_regime=_first_text(final.get("sector_regime") if final else None, momentum.get("sector_regime") if momentum else None),
        sector_gate_action=_first_text(final.get("sector_gate_action") if final else None, momentum.get("sector_gate_action") if momentum else None),
        sector_gate_reason=_first_text(final.get("sector_gate_reason") if final else None, momentum.get("sector_gate_reason") if momentum else None),
        theme_regime=_first_text(final.get("theme_regime") if final else None, momentum.get("theme_regime") if momentum else None),
        theme_gate_action=_first_text(final.get("theme_gate_action") if final else None, momentum.get("theme_gate_action") if momentum else None),
        theme_gate_reason=_first_text(final.get("theme_gate_reason") if final else None, momentum.get("theme_gate_reason") if momentum else None),
        time_policy_reason=time_policy_reason,
        time_policy_source=time_policy_source,
        order_guard_reason=order_guard_reason,
        missed_reason_detail=_missed_reason_detail(
            review_category=category,
            block_source=block_source,
            reason_code=reason_code,
            final_reason=final_reason,
            time_policy_reason=time_policy_reason,
            order_guard_rule=order_guard_rule,
            data_quality=data_quality,
            missed=missed,
        ),
        block_source=block_source,
        recoverable=recoverable,
        would_have_passed_if_time_policy_relaxed=would_pass_time_relaxed,
        would_have_passed_if_order_guard_relaxed=would_pass_guard_relaxed,
        order_guard_rule=order_guard_rule,
        order_guard_recoverable=order_guard_recoverable,
        blocked_after_buy_ready=blocked_after_buy_ready,
        time_bucket=_time_bucket_label(candidate.detected_at),
        is_theme_leader=bool(theme_leader_code and _normalize_symbol(theme_leader_code) == _normalize_symbol(candidate.symbol)),
        theme_coverage_status=_theme_coverage_status(context_fields),
        data_quality=data_quality,
        missed_opportunity=missed,
        review_category=category,
    )


def _derived_metrics_from_flow(flow: PriceFlow) -> Dict[str, object]:
    if not flow.market_data_available:
        return {}
    return {
        "market_data_available": True,
        "candle_cache_available": flow.candle_cache_available,
        "current_price": flow.current_price_at_signal,
        "vwap": flow.vwap_at_signal,
        "prior_high": flow.prior_high_at_signal,
        "prior_high_source": "post_market_intraday",
        "volume_ratio": flow.volume_ratio_at_signal,
        "turnover_rank_sector": None,
        "upper_wick_ratio": flow.upper_wick_ratio_at_signal,
        "trade_strength": None,
        "spread_rate": None,
        "turnover_speed_per_min": None,
        "orderbook_available": None,
        "one_min_reversal": None,
        "entry_type": "",
        "position_size_multiplier": None,
    }


def _block_source_for_row(
    *,
    review_category: str,
    blocked_by: str,
    reason_code: str,
    time_policy_reason: str,
    order_guard_reason: str,
    data_quality: Sequence[str],
) -> str:
    if review_category == "TIME_POLICY_BLOCK":
        return "time_policy"
    if review_category == "ORDER_GUARD_BLOCK":
        return "order_guard"
    if review_category == "DATA_QUALITY_BLOCK":
        return "data_quality"
    if review_category in {"GOOD_BLOCK_CHASE", "BAD_BLOCK_CHASE"}:
        return "strategy_chase_block"
    if review_category == "MISSED_OPPORTUNITY":
        return "strategy_reject"
    haystack = " ".join(
        str(value or "").lower()
        for value in (blocked_by, reason_code, time_policy_reason, order_guard_reason, " ".join(data_quality))
    )
    if "time_policy" in haystack or "block_after" in haystack or "block_pre" in haystack:
        return "time_policy"
    if "order_guard" in haystack or order_guard_reason:
        return "order_guard"
    if "missing" in haystack or "invalid" in haystack or "data" in haystack:
        return "data_quality"
    return ""


def _normalize_order_guard_rule(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    aliases = {
        "daily_buy_limit_exceeded": "daily_buy_limit",
        "daily_loss_limit_exceeded": "daily_loss_limit",
        "position_limit_exceeded": "position_limit",
        "duplicate_position": "duplicate_position",
        "pending_order_exists": "pending_order",
        "missing_final_entry_decision": "missing_final_entry_decision",
        "should_skip_buy_missing_first_position_for_stage2": "missing_first_position_for_stage2",
        "missing_live_account_state": "missing_live_account_state",
        "time_policy_block": "time_policy",
    }
    for source, normalized in aliases.items():
        if source in text:
            return normalized
    if "cooldown" in text:
        return "reentry_cooldown"
    if "duplicate" in text:
        return "duplicate_position"
    if "pending" in text:
        return "pending_order"
    if "position" in text:
        return "position_limit"
    if "daily_buy" in text:
        return "daily_buy_limit"
    if "daily_loss" in text:
        return "daily_loss_limit"
    return text[:80]


def _has_hard_data_gap(data_quality: Sequence[str]) -> bool:
    hard_flags = {
        "MISSING_CAPTURE_PRICE",
        "MISSING_MARKET_METRICS",
        "MISSING_MFE_MAE",
    }
    return any(str(flag or "").strip() in hard_flags for flag in data_quality)


def _would_have_passed_if_time_policy_relaxed(
    *,
    category: str,
    missed: bool,
    flow: PriceFlow,
    data_quality: Sequence[str],
) -> bool:
    return bool(
        category == "TIME_POLICY_BLOCK"
        and missed
        and flow.mfe_pct is not None
        and not _has_hard_data_gap(data_quality)
    )


def _would_have_passed_if_order_guard_relaxed(
    *,
    category: str,
    missed: bool,
    blocked_after_buy_ready: bool,
    flow: PriceFlow,
    data_quality: Sequence[str],
) -> bool:
    return bool(
        category == "ORDER_GUARD_BLOCK"
        and missed
        and blocked_after_buy_ready
        and flow.mfe_pct is not None
        and not _has_hard_data_gap(data_quality)
    )


def _missed_reason_detail(
    *,
    review_category: str,
    block_source: str,
    reason_code: str,
    final_reason: str,
    time_policy_reason: str,
    order_guard_rule: str,
    data_quality: Sequence[str],
    missed: bool,
) -> str:
    if not missed and review_category not in {"TIME_POLICY_BLOCK", "ORDER_GUARD_BLOCK", "DATA_QUALITY_BLOCK"}:
        return ""
    if block_source == "time_policy":
        return time_policy_reason or reason_code or "time_policy_block"
    if block_source == "order_guard":
        return order_guard_rule or reason_code or "order_guard_block"
    if block_source == "data_quality":
        return ";".join(data_quality) or reason_code or "data_quality_block"
    if review_category in {"MISSED_OPPORTUNITY", "BAD_BLOCK_CHASE"}:
        return reason_code or final_reason or review_category
    return reason_code or final_reason or review_category


def _time_bucket_label(value: Optional[datetime]) -> str:
    if value is None:
        return ""
    current = value.time()
    buckets = [
        ("09:00~09:30", "09:00:00", "09:30:00"),
        ("09:30~10:30", "09:30:00", "10:30:00"),
        ("10:30~13:00", "10:30:00", "13:00:00"),
        ("13:00~14:20", "13:00:00", "14:20:00"),
        ("14:20~close", "14:20:00", "23:59:59"),
    ]
    for label, start_text, end_text in buckets:
        start = datetime.strptime(start_text, "%H:%M:%S").time()
        end = datetime.strptime(end_text, "%H:%M:%S").time()
        if start <= current < end:
            return label
    return "outside_regular_session"


def _theme_coverage_status(context_fields: Dict[str, object]) -> str:
    names = str(context_fields.get("theme_names") or "").strip()
    primary = str(context_fields.get("primary_theme") or "").strip()
    if names and primary:
        return "mapped"
    if names:
        return "theme_names_only"
    return "blank"


def _latest_event(events: Sequence[Dict[str, object]]) -> Dict[str, object]:
    if not events:
        return {}
    return _sort_events_by_timestamp(events)[-1]


def _event_timestamp(event: Dict[str, object]) -> Optional[datetime]:
    return _parse_datetime(
        event.get("timestamp")
        or event.get("current_time")
        or event.get("logged_at")
        or event.get("detected_at")
    )


def _sort_events_by_timestamp(events: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    return sorted(
        events,
        key=lambda event: (_event_timestamp(event) or datetime.min, str(event.get("_log_path") or "")),
    )


def _is_allowed_final_event(event: Dict[str, object]) -> bool:
    status = str(event.get("status") or "").strip().lower()
    reason_code = str(event.get("reason_code") or "").strip().upper()
    return event.get("allowed") is True or status == "ready" or reason_code == "FINAL_BUY_READY"


def _representative_final_event(events: Sequence[Dict[str, object]]) -> Dict[str, object]:
    if not events:
        return {}
    ordered = _sort_events_by_timestamp(events)
    allowed = [event for event in ordered if _is_allowed_final_event(event)]
    if allowed:
        return allowed[-1]
    return ordered[-1]


def _matching_momentum_event(
    events: Sequence[Dict[str, object]],
    final: Dict[str, object],
) -> Dict[str, object]:
    if not events:
        return {}
    if not final:
        return _latest_event(events)
    ordered = _sort_events_by_timestamp(events)
    final_ts = _event_timestamp(final)
    if final_ts is None:
        return ordered[-1]
    exact = [event for event in ordered if _event_timestamp(event) == final_ts]
    if exact:
        return exact[-1]
    before = [
        event
        for event in ordered
        if (_event_timestamp(event) or datetime.min) <= final_ts
    ]
    if before:
        return before[-1]
    return min(
        ordered,
        key=lambda event: abs(((_event_timestamp(event) or final_ts) - final_ts).total_seconds()),
    )


def _latest_time_policy_event(
    candidate: ReviewCandidate,
    *,
    prefer_eval_filter: bool = False,
) -> Dict[str, object]:
    events = list(candidate.time_policy_events or [])
    if prefer_eval_filter:
        eval_events = [
            event
            for event in events
            if str(event.get("source") or "") == "evaluate_time_filter"
        ]
        if eval_events:
            return eval_events[-1]
    return events[-1] if events else {}


def _build_decision_trace(
    candidate: ReviewCandidate,
    *,
    momentum: Dict[str, object],
    final: Dict[str, object],
    guard: Dict[str, object],
) -> Any:
    trace: Any = None
    for event in [*candidate.final_events, *candidate.guard_events]:
        for key in ("decision_trace", "trace_with_order_guard"):
            value = event.get(key)
            if isinstance(value, (dict, list)):
                trace = _json_safe(value)
    if trace is None:
        trace = {}
    if not isinstance(trace, dict):
        return trace

    if final:
        trace.setdefault("momentum_decision", final.get("momentum_decision"))
        trace.setdefault("legacy_decision", final.get("legacy_decision"))
        trace.setdefault("final_reason", final.get("final_reason"))
        trace.setdefault("strategy_version", final.get("strategy_version"))
        trace.setdefault("blocked_by", final.get("blocked_by"))
        trace.setdefault("reason_code", final.get("reason_code"))
        trace.setdefault("pullback_dry_run", final.get("pullback_dry_run"))
        trace.setdefault("prior_high_source", final.get("prior_high_source"))
        for key in (
            "market_regime",
            "market_gate_action",
            "market_gate_reason",
            "sector_regime",
            "sector_gate_action",
            "sector_gate_reason",
            "theme_regime",
            "theme_gate_action",
            "theme_gate_reason",
            "turnover_rank_sector",
            *REVIEW_CONTEXT_FIELDS,
        ):
            if key in final:
                trace.setdefault(key, final.get(key))
        if "order_guard_decision" in final:
            trace.setdefault("order_guard_decision", final.get("order_guard_decision"))
    if momentum:
        trace.setdefault("momentum_decision", momentum.get("decision"))
        trace.setdefault("reason_code", momentum.get("reason_code"))
        trace.setdefault("pullback_pct", momentum.get("pullback_pct"))
        trace.setdefault("pullback_dry_run", momentum.get("pullback_dry_run"))
        for key in (
            "market_regime",
            "market_gate_action",
            "market_gate_reason",
            "sector_regime",
            "sector_gate_action",
            "sector_gate_reason",
            "theme_regime",
            "theme_gate_action",
            "theme_gate_reason",
            "turnover_rank_sector",
            *REVIEW_CONTEXT_FIELDS,
        ):
            if key in momentum:
                trace.setdefault(key, momentum.get(key))
    if guard:
        if "order_guard_decision" not in trace:
            trace["order_guard_decision"] = {
                "allowed": guard.get("guard_allowed", guard.get("allowed")),
                "reason": guard.get("guard_reason") or guard.get("reason"),
                "blocked_by": guard.get("blocked_by"),
            }
        trace.setdefault("blocked_by", guard.get("blocked_by"))
    return _json_safe(trace)


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return _format_dt(value)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


def _join_quality_text(candidate: ReviewCandidate) -> str:
    if candidate.join_methods:
        return ";".join(sorted(set(candidate.join_methods)))
    return "missing_join"


def _candidate_lifecycle_text(candidate: ReviewCandidate) -> str:
    if candidate.lifecycle_events:
        return ";".join(sorted(set(candidate.lifecycle_events)))
    return MISSING_TEXT


def _recovery_watch_events(candidate: ReviewCandidate) -> List[Dict[str, object]]:
    return _sort_events_by_timestamp(
        [
            event
            for event in candidate.candidate_events
            if str(event.get("_event_label") or event.get("event") or "") == "recovery_watch_queued"
        ]
    )


def _first_text(*values: object) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _row_field_value(row: ReviewRow, field: str) -> object:
    if hasattr(row, field):
        return getattr(row, field)
    return row.context_fields.get(field, "")


def _row_candidate_key(row: ReviewRow) -> str:
    return row.candidate_id or "{}:{}".format(row.symbol, _format_dt(row.detected_at) or "")


def _is_buy_allowed_row(row: ReviewRow) -> bool:
    if row.traded:
        return True
    decision = str(row.final_decision or "").strip().upper()
    reason_code = str(row.reason_code or "").strip().upper()
    if decision in {"BUY", "READY"} or reason_code == "FINAL_BUY_READY":
        return True
    trace = row.decision_trace if isinstance(row.decision_trace, dict) else {}
    trace_reason = str(trace.get("reason_code") or "").strip().upper()
    trace_status = str(trace.get("status") or "").strip().upper()
    return trace_reason == "FINAL_BUY_READY" or trace_status == "READY"


def _as_float(value: object) -> Optional[float]:
    return _parse_float(value)


def _as_bool(value: object) -> Optional[bool]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def _final_decision_text(
    final: Dict[str, object],
    momentum: Dict[str, object],
) -> Optional[str]:
    if final:
        if final.get("allowed") is True:
            return "BUY"
        status = str(final.get("status") or "").strip()
        return status.upper() if status else "BLOCKED"
    if momentum:
        decision = str(momentum.get("decision") or "").strip()
        return decision or None
    return None


def classify_review_category(
    *,
    traded: bool,
    realized_pnl_pct: Optional[float],
    entry_price: Optional[float],
    close_price: Optional[float],
    reason_code: str,
    blocked_by: str,
    final_decision: Optional[str],
    time_policy_reason: str,
    order_guard_reason: str,
    data_quality: Sequence[str],
    mfe_pct: Optional[float],
    min_missed_opportunity_pct: float,
    missed_opportunity: bool,
) -> str:
    if traded:
        pnl_pct = realized_pnl_pct
        if pnl_pct is None and entry_price and close_price:
            pnl_pct = close_price / entry_price - 1.0
        return "TRADED_WIN" if pnl_pct is not None and pnl_pct > 0 else "TRADED_LOSS"

    reason_l = reason_code.lower()
    blocked_l = blocked_by.lower()
    final_l = str(final_decision or "").lower()
    time_l = time_policy_reason.lower()
    guard_l = order_guard_reason.lower()
    data_l = " ".join(data_quality).lower()

    if (
        reason_l.startswith("time_policy_")
        or "time_policy" in blocked_l
        or "block_after" in time_l
        or "block_pre" in time_l
        or "force_exit" in time_l
        or "allow_manage_only" in time_l
    ):
        return "TIME_POLICY_BLOCK"

    strategy_data_block = (
        "missing" in reason_l
        or "invalid" in reason_l
        or "data" in final_l
        or "market_data_unavailable" in data_l
        or "missing_candle_cache" in data_l
        or "missing_capture_price" in data_l
        or "missing_minute_bars" in data_l
        or "missing_market_metrics" in data_l and "missing_decision_trace" not in data_l
    )
    if strategy_data_block:
        return "DATA_QUALITY_BLOCK"
    if guard_l or "order_guard" in blocked_l or blocked_l in {
        "daily_buy_limit",
        "daily_loss_limit",
        "position_limit",
        "reentry_cooldown",
        "final_entry_decision",
    }:
        return "ORDER_GUARD_BLOCK"
    if "block_chase" in reason_l or reason_l.startswith("block_"):
        if mfe_pct is not None and mfe_pct >= min_missed_opportunity_pct:
            return "BAD_BLOCK_CHASE"
        return "GOOD_BLOCK_CHASE"
    if "wait_pullback" in reason_l or final_l == "wait_pullback":
        return "WAIT_PULLBACK_NO_ENTRY"
    if missed_opportunity:
        return "MISSED_OPPORTUNITY"
    data_block_flags = {
        "missing_minute_bars",
        "missing_bars_after_signal",
        "missing_capture_price",
        "missing_detected_at",
        "missing_mfe_mae",
        "missing_market_metrics",
        "market_data_unavailable",
        "missing_candle_cache",
    }
    if any(flag in data_block_flags for flag in data_quality):
        return "DATA_QUALITY_BLOCK"
    return "GOOD_REJECT"


def write_review_outputs(
    result: ReviewResult,
    *,
    output_dir: str | Path = POST_MARKET_OUTPUT_DEFAULT,
    write_json: bool = False,
) -> ReviewPaths:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    yyyymmdd = result.date.replace("-", "")
    prefix = f"{yyyymmdd}_{result.mode}"
    csv_path = out_dir / f"{prefix}_condition_review.csv"
    md_path = out_dir / f"{prefix}_summary.md"
    json_path = out_dir / f"{prefix}_condition_review.json" if write_json else None
    write_review_csv(result.rows, csv_path)
    write_markdown_summary(result, md_path)
    if json_path is not None:
        write_review_json(result.rows, json_path)
    extra_csv = write_priority_review_reports(result.rows, out_dir, prefix)
    return ReviewPaths(csv=csv_path, markdown=md_path, json=json_path, extra_csv=extra_csv)


def write_review_csv(rows: Sequence[ReviewRow], path: str | Path) -> None:
    with Path(path).open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        for row in rows:
            row_dict = row.as_dict()
            writer.writerow({key: _csv_value(key, row_dict.get(key)) for key in REVIEW_COLUMNS})


def write_review_json(rows: Sequence[ReviewRow], path: str | Path) -> None:
    payload = [row.as_dict() for row in rows]
    with Path(path).open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


PRIORITY_REPORT_COLUMNS = [
    "symbol",
    "symbol_name",
    "detected_at",
    "review_category",
    "missed_opportunity",
    "mfe_pct",
    "mae_pct",
    "return_to_close_pct",
    "time_to_high_min",
    "final_decision",
    "reason_code",
    "block_source",
    "missed_reason_detail",
    "recoverable",
    "would_have_passed_if_time_policy_relaxed",
    "would_have_passed_if_order_guard_relaxed",
    "blocked_after_buy_ready",
    "order_guard_rule",
    "order_guard_recoverable",
    "time_bucket",
    "sector_name",
    "primary_theme",
    "theme_names",
]


def write_priority_review_reports(
    rows: Sequence[ReviewRow],
    output_dir: str | Path,
    prefix: str,
) -> Dict[str, Path]:
    out_dir = Path(output_dir)
    reports = {
        "top_missed_by_mfe": _unique_best_rows(sorted(
            [row for row in rows if not row.traded and row.missed_opportunity],
            key=lambda row: _sort_metric(row.mfe_pct),
            reverse=True,
        )),
        "top_blocked_by_order_guard": _unique_best_rows(sorted(
            [row for row in rows if row.review_category == "ORDER_GUARD_BLOCK" or row.block_source == "order_guard"],
            key=lambda row: _sort_metric(row.mfe_pct),
            reverse=True,
        )),
        "top_blocked_by_time_policy": _unique_best_rows(sorted(
            [row for row in rows if row.review_category == "TIME_POLICY_BLOCK" or row.block_source == "time_policy"],
            key=lambda row: _sort_metric(row.mfe_pct),
            reverse=True,
        )),
    }
    paths: Dict[str, Path] = {}
    for name, members in reports.items():
        path = out_dir / f"{prefix}_{name}.csv"
        _write_priority_report_csv(members, path)
        paths[name] = path

    sector_theme_path = out_dir / f"{prefix}_sector_theme_missed_summary.csv"
    _write_sector_theme_missed_summary_csv(rows, sector_theme_path)
    paths["sector_theme_missed_summary"] = sector_theme_path

    time_policy_path = out_dir / f"{prefix}_time_policy_what_if.csv"
    _write_time_policy_what_if_csv(rows, time_policy_path)
    paths["time_policy_what_if"] = time_policy_path

    return paths


def _write_priority_report_csv(rows: Sequence[ReviewRow], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=PRIORITY_REPORT_COLUMNS)
        writer.writeheader()
        for row in rows:
            data = row.as_dict()
            writer.writerow({key: _csv_value(key, data.get(key)) for key in PRIORITY_REPORT_COLUMNS})


def _unique_best_rows(rows: Sequence[ReviewRow]) -> List[ReviewRow]:
    best: Dict[str, ReviewRow] = {}
    for row in rows:
        current = best.get(row.symbol)
        if current is None or _sort_metric(row.mfe_pct) > _sort_metric(current.mfe_pct):
            best[row.symbol] = row
    return sorted(best.values(), key=lambda row: _sort_metric(row.mfe_pct), reverse=True)


def _write_sector_theme_missed_summary_csv(rows: Sequence[ReviewRow], path: Path) -> None:
    fieldnames = [
        "dimension",
        "name",
        "row_count",
        "unique_symbol_count",
        "missed_count",
        "order_guard_block_count",
        "time_policy_block_count",
        "good_reject_count",
        "avg_mfe_pct",
        "max_mfe_pct",
        "theme_blank_count",
    ]
    grouped: Dict[Tuple[str, str], List[ReviewRow]] = defaultdict(list)
    for row in rows:
        sector_name = str(row.context_fields.get("sector_name") or "").strip() or "(blank)"
        grouped[("sector", sector_name)].append(row)
        theme_names = [
            name.strip()
            for name in str(row.context_fields.get("theme_names") or "").split(";")
            if name.strip()
        ]
        if not theme_names:
            grouped[("theme", "(blank)")].append(row)
        else:
            for theme_name in theme_names:
                grouped[("theme", theme_name)].append(row)

    summary_rows: List[Dict[str, object]] = []
    for (dimension, name), members in grouped.items():
        mfe_values = [row.mfe_pct for row in members if row.mfe_pct is not None]
        summary_rows.append(
            {
                "dimension": dimension,
                "name": name,
                "row_count": len(members),
                "unique_symbol_count": len({row.symbol for row in members}),
                "missed_count": sum(1 for row in members if row.missed_opportunity),
                "order_guard_block_count": sum(1 for row in members if row.review_category == "ORDER_GUARD_BLOCK"),
                "time_policy_block_count": sum(1 for row in members if row.review_category == "TIME_POLICY_BLOCK"),
                "good_reject_count": sum(1 for row in members if row.review_category in {"GOOD_REJECT", "GOOD_BLOCK_CHASE"}),
                "avg_mfe_pct": _mean([row.mfe_pct for row in members]),
                "max_mfe_pct": max(mfe_values) if mfe_values else None,
                "theme_blank_count": sum(1 for row in members if row.theme_coverage_status == "blank"),
            }
        )
    summary_rows.sort(key=lambda item: (-int(item["missed_count"]), -float(item["max_mfe_pct"] or -999), str(item["dimension"]), str(item["name"])))
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in summary_rows:
            writer.writerow({key: _csv_value(key, item.get(key)) for key in fieldnames})


def _write_time_policy_what_if_csv(rows: Sequence[ReviewRow], path: Path) -> None:
    fieldnames = [
        "relaxation",
        "paper_strategy_type",
        "candidate_count",
        "unique_symbol_count",
        "missed_count",
        "avg_mfe_pct",
        "max_mfe_pct",
        "avg_close_return_pct",
        "max_close_return_pct",
        "top_symbol",
        "top_symbol_mfe_pct",
    ]
    time_rows = [row for row in rows if row.review_category == "TIME_POLICY_BLOCK" or row.block_source == "time_policy"]
    recoverable_rows = [row for row in time_rows if _time_policy_paper_validation_candidate(row)]
    scenarios = [
        ("current_time_policy_blocks", "", time_rows),
        ("recoverable_time_policy_blocks", "", recoverable_rows),
        ("recoverable_time_policy_blocks_unique", "", _unique_best_rows(recoverable_rows)),
        ("09:00~09:30_only", "OPENING_RECOVERY_PROBE", [row for row in time_rows if row.time_bucket == "09:00~09:30" and row.missed_opportunity]),
        ("10:30~13:00_only", "MIDDAY_VWAP_RECLAIM", [row for row in time_rows if row.time_bucket == "10:30~13:00" and row.missed_opportunity]),
        ("14:20~close_only", "CLOSING_STRENGTH", [row for row in time_rows if row.time_bucket == "14:20~close" and row.missed_opportunity]),
    ]
    by_strategy: Dict[str, List[ReviewRow]] = defaultdict(list)
    for row in recoverable_rows:
        strategy_type = _time_policy_paper_strategy_type(row)
        if strategy_type:
            by_strategy[strategy_type].append(row)
    for strategy_type, members in sorted(by_strategy.items()):
        scenarios.append((f"recoverable_strategy_{strategy_type}", strategy_type, _unique_best_rows(members)))
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for name, strategy_type, members in scenarios:
            top = max(members, key=lambda row: _sort_metric(row.mfe_pct)) if members else None
            mfe_values = [row.mfe_pct for row in members if row.mfe_pct is not None]
            close_values = [row.return_to_close_pct for row in members if row.return_to_close_pct is not None]
            writer.writerow(
                {
                    "relaxation": name,
                    "paper_strategy_type": strategy_type,
                    "candidate_count": len(members),
                    "unique_symbol_count": len({row.symbol for row in members}),
                    "missed_count": sum(1 for row in members if row.missed_opportunity),
                    "avg_mfe_pct": _mean([row.mfe_pct for row in members]),
                    "max_mfe_pct": max(mfe_values) if mfe_values else None,
                    "avg_close_return_pct": _mean([row.return_to_close_pct for row in members]),
                    "max_close_return_pct": max(close_values) if close_values else None,
                    "top_symbol": top.symbol if top else "",
                    "top_symbol_mfe_pct": top.mfe_pct if top else None,
                }
            )


def _csv_value(key: str, value: object) -> object:
    if value is None:
        return ""
    if key == "data_quality":
        if isinstance(value, list):
            return ";".join(str(v) for v in value if v) if value else "ok"
        return str(value or "ok")
    if key == "decision_trace" and isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if isinstance(value, float):
        return "" if value != value else value
    return value


def write_markdown_summary(result: ReviewResult, path: str | Path) -> None:
    rows = list(result.rows)
    traded = [r for r in rows if r.traded]
    non_traded = [r for r in rows if not r.traded]
    wins = [r for r in traded if r.review_category == "TRADED_WIN"]
    realized = [r.realized_pnl for r in traded if r.realized_pnl is not None]
    category_counter = Counter(r.review_category for r in rows)
    lines: List[str] = []
    lines.append(f"# {result.date} Post-Market Condition Review ({result.mode})")
    lines.append("")
    lines.append("## Daily Summary")
    lines.append(f"- total detected: {len(rows)}")
    lines.append(f"- traded: {len(traded)}")
    lines.append(f"- non-traded: {len(non_traded)}")
    lines.append(f"- TRADED_WIN: {category_counter.get('TRADED_WIN', 0)}")
    lines.append(f"- TRADED_LOSS: {category_counter.get('TRADED_LOSS', 0)}")
    lines.append(f"- MISSED_OPPORTUNITY: {category_counter.get('MISSED_OPPORTUNITY', 0)}")
    lines.append(f"- GOOD_REJECT: {category_counter.get('GOOD_REJECT', 0)}")
    lines.append(f"- DATA_QUALITY_BLOCK: {category_counter.get('DATA_QUALITY_BLOCK', 0)}")
    lines.append(f"- TIME_POLICY_BLOCK: {category_counter.get('TIME_POLICY_BLOCK', 0)}")
    lines.append(f"- ORDER_GUARD_BLOCK: {category_counter.get('ORDER_GUARD_BLOCK', 0)}")
    lines.append(f"- win rate: {_fmt_pct(len(wins) / len(traded) if traded else None, signed=False)}")
    lines.append(f"- realized pnl: {_fmt_number(sum(realized) if realized else None)}")
    lines.append(f"- mode: {result.mode}")
    lines.append(f"- generated_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Data Source Status")
    lines.extend(_data_source_status_lines(result))
    lines.append("")
    lines.append("## Daily Buy Gate Funnel")
    lines.extend(_daily_buy_gate_funnel_lines(rows))
    lines.append("")
    lines.append("## Market/Sector/Theme Gates")
    lines.extend(_market_sector_theme_gate_lines(rows))
    lines.append("")
    lines.append("## Reason Counts by Unique Symbol")
    lines.extend(_reason_counts_unique_lines(non_traded))
    lines.append("")
    lines.append("## Recovery Watch")
    lines.extend(_recovery_watch_lines(rows))
    lines.append("")
    lines.append("## Trade Results")
    lines.extend(_trade_table(traded))
    lines.append("")
    lines.append("## Exit Type Performance")
    lines.extend(_exit_performance_lines(traded))
    lines.append("")
    lines.append("## Non-Traded Review")
    lines.extend(_non_traded_table(non_traded))
    lines.append("")
    lines.append("## Missed Opportunities")
    missed_rows = [r for r in non_traded if r.missed_opportunity or r.review_category in {"MISSED_OPPORTUNITY", "BAD_BLOCK_CHASE"}]
    lines.extend(_non_traded_table(sorted(missed_rows, key=lambda r: r.mfe_pct or -999, reverse=True), limit=15))
    lines.append("")
    lines.append("## Top Missed Opportunities")
    lines.extend(_top_missed_opportunity_lines(rows))
    lines.append("")
    lines.append("## Most Expensive Blocks")
    lines.extend(_most_expensive_block_lines(rows))
    lines.append("")
    lines.append("## OrderGuard Review Candidates")
    lines.extend(_order_guard_review_candidate_lines(rows))
    lines.append("")
    lines.append("## TimePolicy Review Candidates")
    lines.extend(_time_policy_review_candidate_lines(rows))
    lines.append("")
    lines.append("## TimePolicy Paper Validation Candidates")
    lines.extend(_time_policy_paper_validation_lines(rows))
    lines.append("")
    lines.append("## Sector/Theme Concentration")
    lines.extend(_sector_theme_concentration_lines(rows))
    lines.append("")
    lines.append("## Recommended Next Parameter Checks")
    lines.extend(_recommended_parameter_check_lines(rows))
    lines.append("")
    lines.append("## Good Rejects")
    good_rows = [r for r in non_traded if r.review_category in {"GOOD_REJECT", "GOOD_BLOCK_CHASE"}]
    lines.extend(_non_traded_table(good_rows, limit=15))
    lines.append("")
    lines.append("## Block Chase Review")
    lines.extend(_block_chase_lines(rows))
    lines.append("")
    lines.append("## Data Quality Blocks")
    lines.extend(_data_quality_block_lines(rows))
    lines.append("")
    lines.append("## Missing Decision Trace Detail")
    lines.extend(_missing_decision_trace_lines(rows))
    lines.append("")
    lines.append("## Data Quality High MFE")
    lines.extend(_data_quality_high_mfe_lines(rows))
    lines.append("")
    lines.append("## Time Policy Blocks")
    lines.extend(_time_policy_block_lines(rows))
    lines.append("")
    lines.append("## OrderGuard Blocks")
    lines.extend(_order_guard_block_lines(rows))
    lines.append("")
    lines.append("## Reason Code Ranking")
    lines.extend(_reason_code_ranking_lines(non_traded))
    lines.append("")
    lines.append("## Relaxed Pullback Dry Run")
    lines.extend(_relaxed_pullback_lines(rows))
    lines.append("")
    lines.append("## Would Buy Comparison")
    lines.extend(_would_buy_comparison_lines(rows))
    lines.append("")
    lines.append("## Weak Volume Ratio MFE")
    lines.extend(_weak_volume_ratio_mfe_lines(rows))
    lines.append("")
    lines.append("## Reconciliation")
    lines.extend(_reconciliation_lines(rows))
    lines.append("")
    lines.append("## Time Bucket Analysis")
    lines.extend(_time_bucket_lines(rows))
    lines.append("")
    lines.append("## Paper Strategy Performance")
    lines.extend(_paper_strategy_performance_lines(rows))
    lines.append("")
    lines.append("## Parameter Tuning Hints")
    lines.extend(_hint_lines(rows))
    lines.append("")
    lines.append("## Next Action Checklist")
    lines.extend(_next_action_checklist_lines())
    lines.append("")
    lines.append("---")
    lines.append("Generated from files only. This review does not connect to live trading.")
    with Path(path).open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _data_source_status_lines(result: ReviewResult) -> List[str]:
    statuses = result.data_source_status or {}
    if not statuses:
        return ["- data source validation was not collected."]
    lines = [
        "| source | status | path | data_rows | valid_rows | invalid_rows | missing_columns |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    has_unusable_map = False
    for source_name, status in sorted(statuses.items()):
        status_value = str(status.get("status") or "unknown")
        ok = bool(status.get("ok"))
        if source_name in {"sector_map", "theme_map"} and not ok:
            has_unusable_map = True
        missing_columns = status.get("missing_columns") or []
        if isinstance(missing_columns, list):
            missing_text = ",".join(str(item) for item in missing_columns if item) or "ok"
        else:
            missing_text = str(missing_columns or "ok")
        lines.append(
            "| {source} | {status} | {path} | {data_rows} | {valid_rows} | {invalid_rows} | {missing_columns} |".format(
                source=source_name,
                status=status_value,
                path=_short(str(status.get("path") or "")),
                data_rows=status.get("data_rows", 0),
                valid_rows=status.get("valid_rows", 0),
                invalid_rows=status.get("invalid_rows", 0),
                missing_columns=missing_text,
            )
        )
    if has_unusable_map:
        lines.append("")
        lines.append("- sector/theme maps are not fully usable; sector/theme gate fields may be unknown or fallback-only.")
    return lines


def _daily_buy_gate_funnel_lines(rows: Sequence[ReviewRow]) -> List[str]:
    unique_symbols = {row.symbol for row in rows if row.symbol}
    registered_ids = {
        row.candidate_id
        for row in rows
        if row.candidate_id and row.candidate_role != "analysis_only"
    }
    analysis_only = [row for row in rows if row.candidate_role == "analysis_only"]
    momentum_evaluated = [
        row
        for row in rows
        if row.final_decision
        or (isinstance(row.decision_trace, dict) and row.decision_trace.get("momentum_decision"))
    ]
    final_emitted = [row for row in rows if row.final_decision]
    baseline_buy = [row for row in rows if _is_buy_allowed_row(row)]
    relaxed_signal = _pullback_signal_rows(rows, 0.005)
    ordered = [row for row in rows if row.entry_time is not None or row.traded]
    metrics = [
        ("raw_detected", len(rows)),
        ("unique_detected_symbols", len(unique_symbols)),
        ("registered_candidates", len(registered_ids)),
        ("analysis_only_candidates", len(analysis_only)),
        ("momentum_evaluated", len(momentum_evaluated)),
        ("final_decision_emitted", len(final_emitted)),
        ("baseline_buy_allowed", len(baseline_buy)),
        ("baseline_buy_allowed_unique_candidates", len({_row_candidate_key(row) for row in baseline_buy})),
        ("relaxed_pullback_signal_rows", len(relaxed_signal)),
        ("order_attempted", len(ordered)),
        ("order_filled", len([row for row in ordered if row.traded])),
        ("policy_row_count", len(rows)),
    ]
    lines = ["| metric | value |", "|---|---:|"]
    for name, value in metrics:
        lines.append(f"| {name} | {value} |")
    return lines


def _market_sector_theme_gate_lines(rows: Sequence[ReviewRow]) -> List[str]:
    fields = [
        *MARKET_CONTEXT_REVIEW_FIELDS,
        "market_regime",
        "market_gate_action",
        "market_gate_reason",
        *SECTOR_CONTEXT_REVIEW_FIELDS,
        "sector_regime",
        "sector_gate_action",
        "sector_gate_reason",
        *THEME_CONTEXT_REVIEW_FIELDS,
        "theme_regime",
        "theme_gate_action",
        "theme_gate_reason",
    ]
    has_gate_data = any(
        str(_row_field_value(row, field) or "").strip()
        for row in rows
        for field in fields
    )
    lines = [
        "| field | value | row_count | unique_symbol_count | missed_count | avg_mfe_pct |",
        "|---|---|---:|---:|---:|---:|",
    ]
    if not has_gate_data:
        lines.append("| gate_payload | missing | 0 | 0 | 0 | missing |")
        lines.append("")
        lines.append("- no structured market/sector/theme gate fields found in matched logs.")
        return lines
    for field in fields:
        grouped: Dict[str, List[ReviewRow]] = defaultdict(list)
        for row in rows:
            value = str(_row_field_value(row, field) or "").strip()
            if value:
                grouped[value].append(row)
        for value, members in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
            lines.append(
                "| {field} | {value} | {rows} | {symbols} | {missed} | {mfe} |".format(
                    field=field,
                    value=_short(value),
                    rows=len(members),
                    symbols=len({row.symbol for row in members}),
                    missed=sum(1 for row in members if row.missed_opportunity),
                    mfe=_fmt_pct(_mean([row.mfe_pct for row in members])),
                )
            )
    return lines


def _reason_counts_unique_lines(rows: Sequence[ReviewRow]) -> List[str]:
    grouped: Dict[str, List[ReviewRow]] = defaultdict(list)
    for row in rows:
        grouped[_display_reason(row)].append(row)
    if not grouped:
        return ["- none"]
    lines = [
        "| reason | row_count | unique_symbol_count | avg_mfe_pct | missed_count |",
        "|---|---:|---:|---:|---:|",
    ]
    for reason, members in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        lines.append(
            "| {reason} | {rows} | {symbols} | {mfe} | {missed} |".format(
                reason=_short(reason),
                rows=len(members),
                symbols=len({row.symbol for row in members}),
                mfe=_fmt_pct(_mean([row.mfe_pct for row in members])),
                missed=sum(1 for row in members if row.missed_opportunity),
            )
        )
    return lines


def _recovery_watch_lines(rows: Sequence[ReviewRow]) -> List[str]:
    watched = [row for row in rows if int(row.recovery_watch_count or 0) > 0]
    if not watched:
        return ["- none"]
    unique_candidates = {_row_candidate_key(row) for row in watched}
    unique_symbols = {row.symbol for row in watched if row.symbol}
    missed = [row for row in watched if row.missed_opportunity]
    lines = [
        f"- recovery_watch_rows: {len(watched)}",
        f"- recovery_watch_unique_candidates: {len(unique_candidates)}",
        f"- recovery_watch_unique_symbols: {len(unique_symbols)}",
        f"- recovery_watch_missed_count: {len(missed)}",
        f"- recovery_watch_avg_mfe_pct: {_fmt_pct(_mean([row.mfe_pct for row in watched]))}",
        "",
        "| reason | row_count | unique_symbol_count | missed_count | avg_mfe_pct |",
        "|---|---:|---:|---:|---:|",
    ]
    grouped: Dict[str, List[ReviewRow]] = defaultdict(list)
    for row in watched:
        reasons = [
            reason
            for reason in str(row.recovery_watch_reasons or row.reason_code or "").split(";")
            if reason
        ]
        if not reasons:
            reasons = [MISSING_TEXT]
        for reason in reasons:
            grouped[reason].append(row)
    for reason, members in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        lines.append(
            "| {reason} | {rows} | {symbols} | {missed} | {mfe} |".format(
                reason=_short(reason),
                rows=len(members),
                symbols=len({row.symbol for row in members if row.symbol}),
                missed=sum(1 for row in members if row.missed_opportunity),
                mfe=_fmt_pct(_mean([row.mfe_pct for row in members])),
            )
        )
    lines.extend(
        [
            "",
            "| symbol | name | detected_at | reason_code | recovery_reason | delay_sec | MFE | MAE | category |",
            "|---|---|---|---|---|---:|---:|---:|---|",
        ]
    )
    for row in sorted(watched, key=lambda item: _sort_metric(item.mfe_pct), reverse=True)[:20]:
        lines.append(
            "| {symbol} | {name} | {detected_at} | {reason} | {watch_reason} | {delay} | {mfe} | {mae} | {category} |".format(
                symbol=row.symbol,
                name=_short(row.symbol_name, 30),
                detected_at=_format_dt(row.detected_at) or MISSING_TEXT,
                reason=_short(row.reason_code),
                watch_reason=_short(row.recovery_watch_reasons or MISSING_TEXT),
                delay=_fmt_number(row.recovery_watch_delay_seconds),
                mfe=_fmt_pct(row.mfe_pct),
                mae=_fmt_pct(row.mae_pct),
                category=row.review_category,
            )
        )
    return lines


def _missing_decision_trace_lines(rows: Sequence[ReviewRow]) -> List[str]:
    members = [
        row
        for row in rows
        if "MISSING_DECISION_TRACE" in row.data_quality
        or str(row.reason_code or "").startswith("TIME_POLICY_")
    ]
    if not members:
        return ["- none"]
    lines = [
        "| symbol | name | detected_at | candidate_id | role | reason_code | time_policy | source | stage | data_quality |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in sorted(members, key=lambda item: (item.detected_at or datetime.min, item.symbol))[:50]:
        if str(row.reason_code or "").startswith("TIME_POLICY_"):
            stage = "time_policy_pre_momentum" if row.reason_code == "TIME_POLICY_PRE_MOMENTUM_BLOCK" else "analysis_only"
        elif row.final_decision:
            stage = "final_decision_without_trace"
        else:
            stage = "market_metrics_missing"
        lines.append(
            "| {symbol} | {name} | {detected_at} | {candidate_id} | {role} | {reason} | {policy} | {source} | {stage} | {dq} |".format(
                symbol=row.symbol,
                name=_short(row.symbol_name, 30),
                detected_at=_format_dt(row.detected_at) or MISSING_TEXT,
                candidate_id=row.candidate_id or "",
                role=row.candidate_role or "",
                reason=_short(_display_reason(row)),
                policy=_short(row.time_policy_reason),
                source=_short(row.time_policy_source),
                stage=stage,
                dq=_short(";".join(row.data_quality), 80),
            )
        )
    return lines


def _data_quality_high_mfe_lines(rows: Sequence[ReviewRow]) -> List[str]:
    members = [
        row
        for row in rows
        if row.review_category == "DATA_QUALITY_BLOCK"
        and row.mfe_pct is not None
        and row.mfe_pct == row.mfe_pct
    ]
    if not members:
        return ["- none"]
    lines = [
        "| symbol | name | detected_at | reason | MFE | MAE | data_quality |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for row in sorted(members, key=lambda item: _sort_metric(item.mfe_pct), reverse=True)[:20]:
        lines.append(
            "| {symbol} | {name} | {detected_at} | {reason} | {mfe} | {mae} | {dq} |".format(
                symbol=row.symbol,
                name=_short(row.symbol_name, 30),
                detected_at=_format_dt(row.detected_at) or MISSING_TEXT,
                reason=_short(_display_reason(row)),
                mfe=_fmt_pct(row.mfe_pct),
                mae=_fmt_pct(row.mae_pct),
                dq=_short(";".join(row.data_quality), 100),
            )
        )
    return lines


def _would_buy_comparison_lines(rows: Sequence[ReviewRow]) -> List[str]:
    policies = [
        ("baseline", [row for row in rows if _is_buy_allowed_row(row)]),
        ("pullback_0p5_signal", _pullback_signal_rows(rows, 0.005)),
        ("pullback_0p8_signal", _pullback_signal_rows(rows, 0.008)),
        ("pullback_1p0_signal", _pullback_signal_rows(rows, 0.010)),
        ("pullback_1p5_signal", _pullback_signal_rows(rows, 0.015)),
        ("breakout_small_trace", [row for row in rows if _trace_entry_type(row) == "BREAKOUT_SMALL"]),
        ("pullback_reclaim_vwap", [
            row
            for row in rows
            if _display_reason(row) in {"WAIT_RECLAIM_VWAP", "BUY_PULLBACK_RECLAIM", "FINAL_MOMENTUM_WAIT_RECLAIM_VWAP"}
            or _trace_entry_type(row) == "PULLBACK_RECLAIM"
        ]),
    ]
    lines = [
        "| policy | row_count | unique_symbol_count | traded_count | top_reason |",
        "|---|---:|---:|---:|---|",
    ]
    for name, members in policies:
        counter = Counter(_display_reason(row) for row in members if not row.traded)
        top_reason = counter.most_common(1)[0][0] if counter else ""
        lines.append(
            f"| {name} | {len(members)} | {len({row.symbol for row in members})} | {sum(1 for row in members if row.traded)} | {_short(top_reason)} |"
        )
    lines.append("")
    lines.append("- pullback_*_signal is a relaxed pullback signal count, not a full buy-gate pass count.")
    return lines


def _weak_volume_ratio_mfe_lines(rows: Sequence[ReviewRow]) -> List[str]:
    members = [
        row
        for row in rows
        if "weak_volume_ratio" in _display_reason(row).lower()
    ]
    if not members:
        return ["- none"]
    good = sum(1 for row in members if row.review_category in {"GOOD_REJECT", "GOOD_BLOCK_CHASE"})
    missed = sum(1 for row in members if row.missed_opportunity)
    lines = [
        f"- weak_volume_ratio_good_reject_count: {good}",
        f"- weak_volume_ratio_missed_opportunity_count: {missed}",
        "",
        "| symbol | name | reason | MFE | MAE | volume_ratio | trade_strength |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in sorted(members, key=lambda item: _sort_metric(item.mfe_pct), reverse=True)[:20]:
        lines.append(
            "| {symbol} | {name} | {reason} | {mfe} | {mae} | {volume} | {strength} |".format(
                symbol=row.symbol,
                name=_short(row.symbol_name, 30),
                reason=_short(_display_reason(row)),
                mfe=_fmt_pct(row.mfe_pct),
                mae=_fmt_pct(row.mae_pct),
                volume=_fmt_number(row.volume_ratio),
                strength=_fmt_number(row.trade_strength),
            )
        )
    return lines


def _reconciliation_lines(rows: Sequence[ReviewRow]) -> List[str]:
    raw_rows = len(rows)
    unique_symbols = len({row.symbol for row in rows if row.symbol})
    candidate_ids = len({row.candidate_id for row in rows if row.candidate_id})
    relaxed_05 = len(_pullback_signal_rows(rows, 0.005))
    baseline = sum(1 for row in rows if _is_buy_allowed_row(row))
    return [
        f"- post_market raw detected rows: {raw_rows}",
        f"- post_market unique symbols: {unique_symbols}",
        f"- post_market unique candidate_ids: {candidate_ids}",
        f"- baseline full-gate buy/order rows: {baseline}",
        f"- relaxed pullback 0.5% signal rows: {relaxed_05}",
        "- entry_gate_dry_run groups condition captures by symbol and then expands policy rows, while post_market keeps raw condition detections. Compare unique_symbol_count with raw_detected before tuning.",
        "- previous relaxed pullback would_buy_count meant pullback-threshold signal only. It is now reported as signal rows to avoid implying that VWAP, volume, time policy, and order guard also passed.",
    ]


def _trade_table(rows: Sequence[ReviewRow], *, limit: int = 30) -> List[str]:
    if not rows:
        return ["- no traded candidates"]
    lines = [
        "| symbol | name | entry_time | exit_time | entry_price | exit_price | pnl % | exit_type | exit_reason_code | category | entry_reason | exit_reason | strategy_name |",
        "|---|---|---|---|---:|---:|---:|---|---|---|---|---|---|",
    ]
    for row in rows[:limit]:
        lines.append(
            "| {symbol} | {name} | {entry_time} | {exit_time} | {entry} | {exit} | {pct} | {exit_type} | {exit_code} | {cat} | {entry_reason} | {exit_reason} | {strategy} |".format(
                symbol=row.symbol,
                name=row.symbol_name or "",
                entry_time=_format_dt(row.entry_time) or MISSING_TEXT,
                exit_time=_format_dt(row.exit_time) or MISSING_TEXT,
                cat=row.review_category,
                entry=_fmt_number(row.entry_price),
                exit=_fmt_number(row.exit_price),
                pct=_fmt_pct(row.realized_pnl_pct),
                exit_type=_short(row.exit_type),
                exit_code=_short(row.exit_reason_code),
                entry_reason=_short(row.entry_reason or row.final_reason or row.reason_code),
                exit_reason=_short(row.exit_reason),
                strategy=_short(row.strategy_name),
            )
        )
    return lines


def _exit_performance_lines(rows: Sequence[ReviewRow]) -> List[str]:
    traded = [row for row in rows if row.traded]
    if not traded:
        return ["- no traded candidates"]
    lines = [
        "| group | key | count | avg_pnl_pct | win_rate | sell_order_failed | stop_order_escalation |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    buckets = {
        "hard_stop": {"hard_stop", "break_even_stop"},
        "technical_stop": {"structure_stop", "vwap_stop", "momentum_weakness_stop"},
        "trailing_stop": {"trailing_stop"},
        "time_stop": {"time_stop"},
        "force_exit": {"force_exit", "closing_auction_emergency_exit"},
    }
    for label, types in buckets.items():
        members = [row for row in traded if row.exit_type in types]
        lines.append(_exit_perf_row(label, label, members))
    by_type: Dict[str, List[ReviewRow]] = defaultdict(list)
    by_reason: Dict[str, List[ReviewRow]] = defaultdict(list)
    for row in traded:
        by_type[row.exit_type or MISSING_TEXT].append(row)
        by_reason[row.exit_reason_code or MISSING_TEXT].append(row)
    for key, members in sorted(by_type.items()):
        lines.append(_exit_perf_row("exit_type", key, members))
    for key, members in sorted(by_reason.items()):
        lines.append(_exit_perf_row("exit_reason_code", key, members))
    failed = sum(1 for row in traded if str(row.sell_order_result or "").lower() == "sell_order_failed" or row.exit_reason_code == "sell_order_failed")
    escalated = sum(1 for row in traded if row.exit_reason_code == "stop_order_escalation")
    lines.append("")
    lines.append(f"- sell_order_failed count: {failed}")
    lines.append(f"- stop_order_escalation count: {escalated}")
    return lines


def _exit_perf_row(group: str, key: str, members: Sequence[ReviewRow]) -> str:
    count = len(members)
    pnl_values = [row.realized_pnl_pct for row in members]
    avg = _mean(pnl_values)
    wins = sum(1 for row in members if row.realized_pnl_pct is not None and row.realized_pnl_pct > 0)
    failed = sum(1 for row in members if str(row.sell_order_result or "").lower() == "sell_order_failed" or row.exit_reason_code == "sell_order_failed")
    escalated = sum(1 for row in members if row.exit_reason_code == "stop_order_escalation")
    win_rate = wins / count if count else None
    return "| {group} | {key} | {count} | {avg} | {win_rate} | {failed} | {escalated} |".format(
        group=group,
        key=_short(key),
        count=count,
        avg=_fmt_pct(avg),
        win_rate=_fmt_pct(win_rate, signed=False),
        failed=failed,
        escalated=escalated,
    )


def _non_traded_table(rows: Sequence[ReviewRow], *, limit: int = 30) -> List[str]:
    if not rows:
        return ["- none"]
    lines = [
        "| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |",
        "|---|---|---|---:|---|---|---|---:|---:|---|",
    ]
    for row in rows[:limit]:
        lines.append(
            "| {symbol} | {name} | {detected_at} | {capture_price} | {decision} | {final_reason} | {reason} | {mfe} | {mae} | {cat} |".format(
                symbol=row.symbol,
                name=row.symbol_name or "",
                detected_at=_format_dt(row.detected_at) or MISSING_TEXT,
                capture_price=_fmt_number(row.capture_price),
                decision=_short(row.final_decision),
                final_reason=_short(row.final_reason),
                cat=row.review_category,
                reason=_short(_display_reason(row)),
                mfe=_fmt_pct(row.mfe_pct),
                mae=_fmt_pct(row.mae_pct),
            )
        )
    return lines


def _display_reason(row: ReviewRow) -> str:
    return row.reason_code or row.blocked_by or row.final_reason or MISSING_TEXT


def _time_bucket_lines(rows: Sequence[ReviewRow]) -> List[str]:
    buckets = [
        ("09:00~09:30", "09:00:00", "09:30:00"),
        ("09:30~10:30", "09:30:00", "10:30:00"),
        ("10:30~13:00", "10:30:00", "13:00:00"),
        ("13:00~14:20", "13:00:00", "14:20:00"),
        ("14:20 이후", "14:20:00", "23:59:59"),
    ]
    lines = ["| bucket | detected | traded | missed | avg MFE |", "|---|---:|---:|---:|---:|"]
    for label, start_text, end_text in buckets:
        start = datetime.strptime(start_text, "%H:%M:%S").time()
        end = datetime.strptime(end_text, "%H:%M:%S").time()
        members = [
            r for r in rows
            if r.detected_at is not None and start <= r.detected_at.time() < end
        ]
        traded = sum(1 for r in members if r.traded)
        missed = sum(1 for r in members if r.missed_opportunity)
        avg_mfe = _mean([r.mfe_pct for r in members])
        lines.append(f"| {label} | {len(members)} | {traded} | {missed} | {_fmt_pct(avg_mfe)} |")
    return lines


def _focus_lines(rows: Sequence[ReviewRow]) -> List[str]:
    groups = [
        ("TimePolicy blocks", lambda r: r.review_category == "TIME_POLICY_BLOCK"),
        ("BLOCK_CHASE blocks", lambda r: r.review_category in {"GOOD_BLOCK_CHASE", "BAD_BLOCK_CHASE"}),
        ("DATA_QUALITY_BLOCK rows", lambda r: r.review_category == "DATA_QUALITY_BLOCK"),
    ]
    lines: List[str] = []
    for title, pred in groups:
        members = [r for r in rows if pred(r)]
        lines.append(f"### {title}")
        if not members:
            lines.append("- none")
            continue
        for row in sorted(members, key=lambda r: r.mfe_pct or -999, reverse=True)[:10]:
            lines.append(
                f"- {row.symbol} {row.symbol_name}: {row.review_category}, reason={_display_reason(row)}, MFE={_fmt_pct(row.mfe_pct)}, close={_fmt_pct(row.return_to_close_pct)}"
            )
    return lines


def _data_quality_lines(rows: Sequence[ReviewRow]) -> List[str]:
    flagged = [r for r in rows if r.data_quality]
    if not flagged:
        return ["- no missing data flags"]
    counter = Counter(flag for row in flagged for flag in row.data_quality)
    lines = [f"- rows with data quality flags: {len(flagged)}"]
    for flag, count in counter.most_common():
        members = [r for r in flagged if flag in r.data_quality]
        lines.append(
            f"- {flag}: {count}, avg MFE {_fmt_pct(_mean([r.mfe_pct for r in members]))}"
        )
    return lines


def _hint_lines(rows: Sequence[ReviewRow]) -> List[str]:
    hints: List[str] = []
    data_rows = [r for r in rows if r.review_category == "DATA_QUALITY_BLOCK"]
    if data_rows and any((r.mfe_pct or 0) >= 0.02 for r in data_rows):
        hints.append("- DATA_QUALITY_BLOCK rows include high MFE. Check collection for missing volume/VWAP/candle cache before changing entry rules.")
    chase_rows = [r for r in rows if r.review_category in {"GOOD_BLOCK_CHASE", "BAD_BLOCK_CHASE"}]
    if chase_rows:
        good = sum(1 for r in chase_rows if r.review_category == "GOOD_BLOCK_CHASE")
        bad = sum(1 for r in chase_rows if r.review_category == "BAD_BLOCK_CHASE")
        if good >= bad:
            hints.append("- BLOCK_CHASE mostly avoided weak follow-through. Keep the chase block until more samples disagree.")
        else:
            hints.append("- BLOCK_CHASE has repeated upside misses. Review chase distance and wick thresholds manually.")
    time_rows = [r for r in rows if r.review_category == "TIME_POLICY_BLOCK"]
    if time_rows and any((r.mfe_pct or 0) >= 0.02 for r in time_rows):
        hints.append("- TimePolicy blocked rows later moved strongly. Review entry windows manually, especially recurring time buckets.")
    if not hints:
        hints.append("- No tuning hint crossed the simple review thresholds. Keep collecting samples.")
    return hints


def _short(text: object, limit: int = 80) -> str:
    value = str(text or MISSING_TEXT).replace("|", "/").replace("\n", " ")
    return value if len(value) <= limit else value[: limit - 3] + "..."


def _fmt_number(value: Optional[float]) -> str:
    if value is None:
        return MISSING_TEXT
    if abs(value - int(value)) < 1e-9:
        return str(int(value))
    return f"{value:.4f}"


def _fmt_pct(value: Optional[float], *, signed: bool = True) -> str:
    if value is None:
        return MISSING_TEXT
    sign = "+" if signed else ""
    return f"{value * 100:{sign}.2f}%"


def _mean(values: Iterable[Optional[float]]) -> Optional[float]:
    clean = [value for value in values if value is not None and value == value]
    return mean(clean) if clean else None


def _time_bucket_lines(rows: Sequence[ReviewRow]) -> List[str]:
    buckets = [
        ("09:00~09:30", "09:00:00", "09:30:00"),
        ("09:30~10:30", "09:30:00", "10:30:00"),
        ("10:30~13:00", "10:30:00", "13:00:00"),
        ("13:00~14:20", "13:00:00", "14:20:00"),
        ("14:20 이후", "14:20:00", "23:59:59"),
    ]
    lines = [
        "| time_bucket | capture_count | strategy_candidate_count | paper_only_count | traded_count | non_traded_count | missed_opportunity_count | good_reject_count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, start_text, end_text in buckets:
        start = datetime.strptime(start_text, "%H:%M:%S").time()
        end = datetime.strptime(end_text, "%H:%M:%S").time()
        members = [
            row for row in rows
            if row.detected_at is not None and start <= row.detected_at.time() < end
        ]
        traded_count = sum(1 for row in members if row.traded)
        strategy_count = sum(1 for row in members if _paper_strategy_key(row))
        paper_count = sum(1 for row in members if _is_paper_only_candidate(row))
        missed_count = sum(1 for row in members if row.missed_opportunity)
        good_count = sum(1 for row in members if row.review_category in {"GOOD_REJECT", "GOOD_BLOCK_CHASE"})
        mfe_stats = _metric_stats([row.mfe_pct for row in members])
        mae_stats = _metric_stats([row.mae_pct for row in members])
        lines.append(
            f"| {label} | {len(members)} | {strategy_count} | {paper_count} | {traded_count} | {len(members) - traded_count} | {missed_count} | {good_count} | {_fmt_pct(mfe_stats['avg'])} | {_fmt_pct(mae_stats['avg'])} | {mfe_stats['n']} | {mae_stats['n']} |"
        )
    return lines


PAPER_STRATEGY_ENTRY_TYPES = {
    "OPENING_RECOVERY_PROBE",
    "MIDDAY_VWAP_RECLAIM",
    "AFTERNOON_SECOND_WAVE",
    "CLOSING_STRENGTH",
    "TREND_CONTINUATION",
    "WEAK_VOLUME_RELIEF_PAPER_ONLY",
}


def _paper_strategy_key(row: ReviewRow) -> str:
    entry_type = str(row.entry_type or "").upper()
    reason_code = str(row.reason_code or "").upper()
    if entry_type in PAPER_STRATEGY_ENTRY_TYPES:
        return entry_type
    for key in PAPER_STRATEGY_ENTRY_TYPES:
        if key in reason_code:
            return key
    return ""


def _time_policy_paper_strategy_type(row: ReviewRow) -> str:
    key = _paper_strategy_key(row)
    if key:
        return key
    if row.time_bucket == "09:00~09:30":
        return "OPENING_RECOVERY_PROBE"
    if row.time_bucket == "10:30~13:00":
        return "MIDDAY_VWAP_RECLAIM"
    if row.time_bucket == "13:00~14:20":
        return "AFTERNOON_SECOND_WAVE"
    if row.time_bucket == "14:20~close":
        return "CLOSING_STRENGTH"
    return ""


def _is_paper_only_candidate(row: ReviewRow) -> bool:
    if _paper_strategy_key(row):
        return True
    trace = row.decision_trace if isinstance(row.decision_trace, dict) else {}
    return bool(trace.get("paper_only_strategy") or trace.get("paper_only_breakout_probe"))


def _paper_strategy_performance_lines(rows: Sequence[ReviewRow]) -> List[str]:
    by_strategy: Dict[str, List[ReviewRow]] = defaultdict(list)
    for row in rows:
        key = _paper_strategy_key(row)
        if key:
            by_strategy[key].append(row)
    if not by_strategy:
        return ["No paper-only strategy candidates."]
    lines = [
        "| strategy_type | candidate_count | paper_only_count | traded_count | missed_count | good_reject_count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for strategy_type in sorted(by_strategy):
        members = by_strategy[strategy_type]
        mfe_stats = _metric_stats([row.mfe_pct for row in members])
        mae_stats = _metric_stats([row.mae_pct for row in members])
        lines.append(
            "| {strategy} | {count} | {paper} | {traded} | {missed} | {good} | {mfe} | {mae} | {n_mfe} | {n_mae} |".format(
                strategy=strategy_type,
                count=len(members),
                paper=sum(1 for row in members if _is_paper_only_candidate(row)),
                traded=sum(1 for row in members if row.traded),
                missed=sum(1 for row in members if row.missed_opportunity),
                good=sum(1 for row in members if row.review_category in {"GOOD_REJECT", "GOOD_BLOCK_CHASE"}),
                mfe=_fmt_pct(mfe_stats["avg"]),
                mae=_fmt_pct(mae_stats["avg"]),
                n_mfe=mfe_stats["n"],
                n_mae=mae_stats["n"],
            )
        )
    return lines


def _top_missed_opportunity_lines(rows: Sequence[ReviewRow]) -> List[str]:
    members = [row for row in rows if not row.traded and row.missed_opportunity]
    return _priority_candidate_table(members, limit=15)


def _most_expensive_block_lines(rows: Sequence[ReviewRow]) -> List[str]:
    members = [
        row for row in rows
        if not row.traded
        and row.block_source in {"time_policy", "order_guard", "data_quality", "strategy_chase_block"}
        and row.mfe_pct is not None
    ]
    return _priority_candidate_table(members, limit=15)


def _order_guard_review_candidate_lines(rows: Sequence[ReviewRow]) -> List[str]:
    members = [
        row for row in rows
        if row.review_category == "ORDER_GUARD_BLOCK"
        or row.block_source == "order_guard"
        or row.blocked_after_buy_ready
    ]
    lines = _priority_candidate_table(members, limit=15)
    recoverable = sum(1 for row in members if row.order_guard_recoverable)
    ready = sum(1 for row in members if row.blocked_after_buy_ready)
    lines.append("")
    lines.append(f"- blocked_after_buy_ready: {ready}")
    lines.append(f"- order_guard_recoverable: {recoverable}")
    return lines


def _time_policy_review_candidate_lines(rows: Sequence[ReviewRow]) -> List[str]:
    members = [
        row for row in rows
        if row.review_category == "TIME_POLICY_BLOCK"
        or row.block_source == "time_policy"
    ]
    lines = _priority_candidate_table(members, limit=15)
    bucket_counter = Counter(row.time_bucket or "(blank)" for row in members if row.missed_opportunity)
    if bucket_counter:
        lines.append("")
        lines.append("| time_bucket | missed_count |")
        lines.append("|---|---:|")
        for bucket, count in bucket_counter.most_common():
            lines.append(f"| {bucket} | {count} |")
    return lines


def _time_policy_paper_validation_lines(rows: Sequence[ReviewRow]) -> List[str]:
    members = _unique_best_rows(
        [
            row for row in rows
            if _time_policy_paper_validation_candidate(row)
            and _time_policy_paper_strategy_type(row)
        ]
    )
    if not members:
        return ["- none"]
    lines = [
        "- paper-only validation list; this is not a live entry relaxation.",
        "",
        "| symbol | name | time_bucket | paper_strategy_type | reason | MFE | close return | sector | theme |",
        "|---|---|---|---|---|---:|---:|---|---|",
    ]
    for row in members[:15]:
        lines.append(
            "| {symbol} | {name} | {bucket} | {strategy} | {reason} | {mfe} | {close} | {sector} | {theme} |".format(
                symbol=row.symbol,
                name=_short(row.symbol_name or "", 24),
                bucket=row.time_bucket or "",
                strategy=_time_policy_paper_strategy_type(row),
                reason=_short(row.missed_reason_detail or _display_reason(row), 56),
                mfe=_fmt_pct(row.mfe_pct),
                close=_fmt_pct(row.return_to_close_pct),
                sector=_short(row.context_fields.get("sector_name") or "", 32),
                theme=_short(row.context_fields.get("primary_theme") or row.context_fields.get("theme_names") or "", 32),
            )
        )
    return lines


def _time_policy_paper_validation_candidate(row: ReviewRow) -> bool:
    if row.review_category != "TIME_POLICY_BLOCK" and row.block_source != "time_policy":
        return False
    if row.mfe_pct is None or row.mfe_pct < TIME_POLICY_HIGH_MFE_PAPER_MIN_MFE_PCT:
        return False
    hard_flags = {"MISSING_CAPTURE_PRICE", "MISSING_MARKET_METRICS", "MISSING_MFE_MAE"}
    return not any(flag in hard_flags for flag in row.data_quality)


def _sector_theme_concentration_lines(rows: Sequence[ReviewRow]) -> List[str]:
    lines: List[str] = []
    for title, getter in (
        ("sector_name", lambda row: [str(row.context_fields.get("sector_name") or "").strip() or "(blank)"]),
        (
            "theme_names",
            lambda row: [
                name.strip()
                for name in str(row.context_fields.get("theme_names") or "").split(";")
                if name.strip()
            ] or ["(blank)"],
        ),
    ):
        grouped: Dict[str, List[ReviewRow]] = defaultdict(list)
        for row in rows:
            for key in getter(row):
                grouped[key].append(row)
        ranked = sorted(
            grouped.items(),
            key=lambda item: (
                -sum(1 for row in item[1] if row.missed_opportunity),
                -_sort_metric(max((row.mfe_pct for row in item[1] if row.mfe_pct is not None), default=None)),
                item[0],
            ),
        )[:10]
        lines.append(f"### {title}")
        lines.append("| name | rows | unique_symbols | missed | order_guard | time_policy | avg_MFE | max_MFE |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for name, members in ranked:
            mfe_values = [row.mfe_pct for row in members if row.mfe_pct is not None]
            lines.append(
                "| {name} | {rows} | {symbols} | {missed} | {guard} | {time} | {avg_mfe} | {max_mfe} |".format(
                    name=_short(name, 60),
                    rows=len(members),
                    symbols=len({row.symbol for row in members}),
                    missed=sum(1 for row in members if row.missed_opportunity),
                    guard=sum(1 for row in members if row.review_category == "ORDER_GUARD_BLOCK"),
                    time=sum(1 for row in members if row.review_category == "TIME_POLICY_BLOCK"),
                    avg_mfe=_fmt_pct(_mean([row.mfe_pct for row in members])),
                    max_mfe=_fmt_pct(max(mfe_values) if mfe_values else None),
                )
            )
        lines.append("")
    return lines[:-1] if lines and lines[-1] == "" else lines


def _recommended_parameter_check_lines(rows: Sequence[ReviewRow]) -> List[str]:
    lines: List[str] = []
    guard_ready = [row for row in rows if row.blocked_after_buy_ready and row.missed_opportunity]
    time_recoverable = [row for row in rows if row.would_have_passed_if_time_policy_relaxed]
    data_high = [
        row for row in rows
        if row.review_category == "DATA_QUALITY_BLOCK"
        and row.mfe_pct is not None
        and row.mfe_pct >= 0.02
    ]
    theme_blank_missed = [row for row in rows if row.missed_opportunity and row.theme_coverage_status == "blank"]
    if guard_ready:
        lines.append(f"- OrderGuard: review {len(guard_ready)} BUY-ready blocked rows before changing strategy thresholds.")
    if time_recoverable:
        top_bucket = Counter(row.time_bucket for row in time_recoverable).most_common(1)[0][0]
        lines.append(f"- TimePolicy: simulate a narrower relaxation around {top_bucket}; {len(time_recoverable)} recoverable rows qualify.")
    if data_high:
        lines.append(f"- Data quality: fix collection gaps for {len(data_high)} high-MFE rows before tuning entries.")
    if theme_blank_missed:
        lines.append(f"- Theme map: {len(theme_blank_missed)} missed rows still have blank theme coverage; improve the map before theme gating.")
    if not lines:
        lines.append("- No parameter check crossed the review thresholds. Keep collecting comparable samples.")
    return lines


def _priority_candidate_table(rows: Sequence[ReviewRow], *, limit: int = 15) -> List[str]:
    if not rows:
        return ["- none"]
    lines = [
        "| symbol | name | category | MFE | close | block_source | detail | sector | theme |",
        "|---|---|---|---:|---:|---|---|---|---|",
    ]
    for row in _unique_best_rows(rows)[:limit]:
        lines.append(
            "| {symbol} | {name} | {category} | {mfe} | {close} | {source} | {detail} | {sector} | {theme} |".format(
                symbol=row.symbol,
                name=_short(row.symbol_name or "", 24),
                category=row.review_category,
                mfe=_fmt_pct(row.mfe_pct),
                close=_fmt_pct(row.return_to_close_pct),
                source=row.block_source or "",
                detail=_short(row.missed_reason_detail or _display_reason(row), 60),
                sector=_short(row.context_fields.get("sector_name") or "", 32),
                theme=_short(row.context_fields.get("primary_theme") or row.context_fields.get("theme_names") or "", 32),
            )
        )
    return lines


def _block_chase_lines(rows: Sequence[ReviewRow]) -> List[str]:
    members = [
        row for row in rows
        if row.review_category in {"GOOD_BLOCK_CHASE", "BAD_BLOCK_CHASE"}
        or _matches_reason(row, BLOCK_CHASE_REASON_CODES)
    ]
    return _focus_table(members, include_data_quality=False)


def _data_quality_block_lines(rows: Sequence[ReviewRow]) -> List[str]:
    members = [
        row for row in rows
        if row.review_category == "DATA_QUALITY_BLOCK"
        or _matches_reason(row, DATA_QUALITY_REASON_CODES)
        or any(flag in DATA_QUALITY_REASON_CODES for flag in row.data_quality)
    ]
    lines = _focus_table(members, include_data_quality=True)
    if members:
        counter = Counter(flag for row in members for flag in row.data_quality)
        if counter:
            lines.append("")
            lines.append("| data_quality | count | avg_mfe_pct | n_mfe | missing_mfe |")
            lines.append("|---|---:|---:|---:|---:|")
            for flag, count in counter.most_common():
                flagged_rows = [row for row in members if flag in row.data_quality]
                stats = _metric_stats([row.mfe_pct for row in flagged_rows])
                lines.append(
                    f"| {flag} | {count} | {_fmt_pct(stats['avg'])} | {stats['n']} | {stats['missing']} |"
                )
    return lines


def _time_policy_block_lines(rows: Sequence[ReviewRow]) -> List[str]:
    members = [
        row for row in rows
        if row.review_category == "TIME_POLICY_BLOCK"
        or _matches_reason(row, TIME_POLICY_REASON_CODES)
    ]
    return _focus_table(members, include_data_quality=False)


def _order_guard_block_lines(rows: Sequence[ReviewRow]) -> List[str]:
    members = [
        row for row in rows
        if row.review_category == "ORDER_GUARD_BLOCK"
        or _matches_reason(row, ORDER_GUARD_REASON_CODES)
    ]
    return _focus_table(members, include_data_quality=False)


def _focus_table(
    rows: Sequence[ReviewRow],
    *,
    include_data_quality: bool,
    limit: int = 20,
) -> List[str]:
    if not rows:
        return ["- none"]
    if include_data_quality:
        lines = [
            "| symbol | name | category | reason_code | MFE | MAE | close return | data_quality |",
            "|---|---|---|---|---:|---:|---:|---|",
        ]
    else:
        lines = [
            "| symbol | name | category | reason_code | MFE | MAE | close return |",
            "|---|---|---|---|---:|---:|---:|",
        ]
    for row in sorted(rows, key=lambda item: _sort_metric(item.mfe_pct), reverse=True)[:limit]:
        values = [
            row.symbol,
            row.symbol_name or "",
            row.review_category,
            _short(_display_reason(row)),
            _fmt_pct(row.mfe_pct),
            _fmt_pct(row.mae_pct),
            _fmt_pct(row.return_to_close_pct),
        ]
        if include_data_quality:
            values.append(_short(";".join(row.data_quality) or "ok"))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def _reason_code_ranking_lines(rows: Sequence[ReviewRow]) -> List[str]:
    stats = _reason_code_stats(rows)
    if not stats:
        return ["- no block reasons"]
    lines = [
        "| reason_code | count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae | missing_mfe | missing_mae | missed_opportunity_count | missed_opportunity_rate | good_reject_count | good_reject_rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in stats:
        lines.append(
            "| {reason} | {count} | {avg_mfe} | {avg_mae} | {n_mfe} | {n_mae} | {missing_mfe} | {missing_mae} | {missed_count} | {missed_rate} | {good_count} | {good_rate} |".format(
                reason=item["reason_code"],
                count=item["count"],
                avg_mfe=_fmt_pct(item["avg_mfe_pct"]),
                avg_mae=_fmt_pct(item["avg_mae_pct"]),
                n_mfe=item["n_mfe"],
                n_mae=item["n_mae"],
                missing_mfe=item["missing_mfe"],
                missing_mae=item["missing_mae"],
                missed_count=item["missed_opportunity_count"],
                missed_rate=_fmt_pct(item["missed_opportunity_rate"], signed=False),
                good_count=item["good_reject_count"],
                good_rate=_fmt_pct(item["good_reject_rate"], signed=False),
            )
        )
    return lines


def _relaxed_pullback_lines(rows: Sequence[ReviewRow]) -> List[str]:
    thresholds = [0.005, 0.008, 0.010, 0.015]
    lines = [
        "| policy | candidate_rows | unique_symbols | pullback_signal_rows | non_traded_signal_rows | top_signal_block_reason |",
        "|---|---:|---:|---:|---:|---|",
    ]
    if not rows:
        return ["- no rows"]
    for threshold in thresholds:
        eligible = _pullback_signal_rows(rows, threshold)
        blocked = [row for row in eligible if not row.traded]
        counter = Counter(_display_reason(row) for row in blocked)
        top_reason = counter.most_common(1)[0][0] if counter else ""
        lines.append(
            "| pullback >= {pct:.1f}% | {candidates} | {symbols} | {signals} | {blocked} | {reason} |".format(
                pct=threshold * 100,
                candidates=len(rows),
                symbols=len({row.symbol for row in eligible}),
                signals=len(eligible),
                blocked=len(blocked),
                reason=_short(top_reason),
            )
        )
    lines.append("")
    lines.append("- pullback_signal_rows only means the relaxed pullback threshold passed; it is not a full buy-gate allowed count.")
    return lines


def _hint_lines(rows: Sequence[ReviewRow]) -> List[str]:
    hints: List[str] = []
    data_rows = [row for row in rows if row.review_category == "DATA_QUALITY_BLOCK"]
    if _has_high_mfe(data_rows, 0.02):
        hints.append("- DATA_QUALITY_BLOCK rows include high MFE. Check collection for missing volume/VWAP/candle cache before changing entry rules.")
    chase_rows = [row for row in rows if row.review_category in {"GOOD_BLOCK_CHASE", "BAD_BLOCK_CHASE"}]
    if chase_rows:
        good = sum(1 for row in chase_rows if row.review_category == "GOOD_BLOCK_CHASE")
        bad = sum(1 for row in chase_rows if row.review_category == "BAD_BLOCK_CHASE")
        if good >= bad:
            hints.append("- BLOCK_CHASE mostly avoided weak follow-through. Keep the chase block until more samples disagree.")
        else:
            hints.append("- BLOCK_CHASE has repeated upside misses. Review chase distance and wick thresholds manually.")
    time_rows = [row for row in rows if row.review_category == "TIME_POLICY_BLOCK"]
    if _has_high_mfe(time_rows, 0.02):
        hints.append("- TimePolicy blocked rows later moved strongly. Review entry windows manually, especially recurring time buckets.")
    loss_counter = Counter(_display_reason(row) for row in rows if row.review_category == "TRADED_LOSS")
    if loss_counter:
        reason, count = loss_counter.most_common(1)[0]
        if count >= 2:
            hints.append(f"- TRADED_LOSS is clustered in {reason}. Review this entry type manually before changing config.")
    if not hints:
        hints.append("- No tuning hint crossed the simple review thresholds. Keep collecting samples.")
    return hints


def _next_action_checklist_lines() -> List[str]:
    return [
        "- [ ] Review top 5 MISSED_OPPORTUNITY rows.",
        "- [ ] Check high-MFE DATA_QUALITY_BLOCK rows before tuning strategy parameters.",
        "- [ ] Verify whether BLOCK_CHASE actually prevented weak follow-through.",
        "- [ ] Review TIME_POLICY_BLOCK rows that rallied after the block.",
        "- [ ] Inspect TRADED_LOSS reason_code clustering.",
        "- [ ] Record config candidates only; do not change config immediately.",
    ]


def _reason_code_stats(rows: Sequence[ReviewRow]) -> List[Dict[str, object]]:
    grouped: Dict[str, List[ReviewRow]] = defaultdict(list)
    for row in rows:
        grouped[_display_reason(row)].append(row)
    out: List[Dict[str, object]] = []
    for reason, members in grouped.items():
        count = len(members)
        mfe_stats = _metric_stats([row.mfe_pct for row in members])
        mae_stats = _metric_stats([row.mae_pct for row in members])
        missed_count = sum(1 for row in members if row.missed_opportunity)
        good_count = sum(1 for row in members if row.review_category in {"GOOD_REJECT", "GOOD_BLOCK_CHASE"})
        out.append(
            {
                "reason_code": reason,
                "count": count,
                "avg_mfe_pct": mfe_stats["avg"],
                "avg_mae_pct": mae_stats["avg"],
                "n_mfe": mfe_stats["n"],
                "n_mae": mae_stats["n"],
                "missing_mfe": mfe_stats["missing"],
                "missing_mae": mae_stats["missing"],
                "missed_opportunity_count": missed_count,
                "missed_opportunity_rate": missed_count / count if count else None,
                "good_reject_count": good_count,
                "good_reject_rate": good_count / count if count else None,
            }
        )
    out.sort(key=lambda item: (-int(item["count"]), str(item["reason_code"])))
    return out


def _trace_entry_type(row: ReviewRow) -> str:
    trace = row.decision_trace if isinstance(row.decision_trace, dict) else {}
    value = ""
    if isinstance(trace, dict):
        value = str(trace.get("entry_type") or "").strip()
        if not value:
            momentum = trace.get("momentum_decision")
            if isinstance(momentum, dict):
                value = str(momentum.get("entry_type") or "").strip()
    return value


def _pullback_signal_rows(rows: Sequence[ReviewRow], threshold: float) -> List[ReviewRow]:
    out: List[ReviewRow] = []
    for row in rows:
        pullback = None
        trace = row.decision_trace if isinstance(row.decision_trace, dict) else {}
        if isinstance(trace, dict):
            dry = trace.get("pullback_dry_run")
            if isinstance(dry, dict):
                item = dry.get("{:.4f}".format(threshold))
                if isinstance(item, dict) and bool(item.get("passes")):
                    pullback = threshold
            if pullback is None:
                pullback = _parse_float(trace.get("pullback_pct"))
        if pullback is None:
            pullback = 0.0
        if pullback >= threshold:
            out.append(row)
    return out


def _metric_stats(values: Iterable[Optional[float]]) -> Dict[str, object]:
    all_values = list(values)
    clean = [value for value in all_values if value is not None and value == value]
    return {
        "avg": mean(clean) if clean else None,
        "n": len(clean),
        "missing": len(all_values) - len(clean),
    }


def _matches_reason(row: ReviewRow, reason_codes: Sequence[str]) -> bool:
    haystacks = {
        _display_reason(row),
        row.reason_code,
        row.final_reason,
        row.blocked_by,
        row.time_policy_reason,
        row.order_guard_reason,
    }
    lower = {str(value or "").lower() for value in haystacks}
    upper = {str(value or "").upper() for value in haystacks}
    return any(code.lower() in lower or code.upper() in upper for code in reason_codes)


def _has_high_mfe(rows: Sequence[ReviewRow], threshold: float) -> bool:
    return any(row.mfe_pct is not None and row.mfe_pct == row.mfe_pct and row.mfe_pct >= threshold for row in rows)


def _sort_metric(value: Optional[float]) -> float:
    return value if value is not None and value == value else -999.0
