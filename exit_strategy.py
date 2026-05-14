"""Structured exit policy for intraday positions.

This module is intentionally pure: it does not submit, cancel, or retry orders.
Callers own Position mutations and order routing through OrderGuard.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from bars import FiveMinIndicators, MinuteBar
from portfolio import Position
from trade_config import TRADE_CONFIG


ACTION_HOLD = "HOLD"
ACTION_SELL_PARTIAL = "SELL_PARTIAL"
ACTION_SELL_ALL = "SELL_ALL"
ACTION_STOP_LOSS = "STOP_LOSS"
ACTION_TRAILING_STOP = "TRAILING_STOP"
ACTION_TIME_STOP = "TIME_STOP"
ACTION_FORCE_EXIT = "FORCE_EXIT"

EXIT_TYPE_HARD_STOP = "hard_stop"
EXIT_TYPE_STRUCTURE_STOP = "structure_stop"
EXIT_TYPE_VWAP_STOP = "vwap_stop"
EXIT_TYPE_MOMENTUM_WEAKNESS_STOP = "momentum_weakness_stop"
EXIT_TYPE_PROFIT_TAKE = "profit_take"
EXIT_TYPE_PARTIAL_PROFIT_TAKE = "partial_profit_take"
EXIT_TYPE_TRAILING_STOP = "trailing_stop"
EXIT_TYPE_BREAK_EVEN_STOP = "break_even_stop"
EXIT_TYPE_TIME_STOP = "time_stop"
EXIT_TYPE_FORCE_EXIT = "force_exit"
EXIT_TYPE_CLOSING_AUCTION_EMERGENCY_EXIT = "closing_auction_emergency_exit"
EXIT_TYPE_UNKNOWN = "unknown"

REASON_HARD_STOP_FIXED_PCT = "hard_stop_fixed_pct"
REASON_HARD_STOP_POSITION_STOP_PRICE = "hard_stop_position_stop_price"
REASON_STRUCTURE_SIGNAL_BAR_LOW_BREAK = "structure_stop_signal_bar_low_break"
REASON_STRUCTURE_RECENT_1M_LOW_BREAK = "structure_stop_recent_1m_low_break"
REASON_VWAP_RECLAIM_FAILED = "vwap_reclaim_failed"
REASON_VWAP_BREAK_FAST_DROP = "vwap_break_fast_drop"
REASON_MOMENTUM_TRADE_STRENGTH_DROP = "momentum_trade_strength_drop"
REASON_MOMENTUM_VOLUME_BEARISH_CANDLE = "momentum_volume_bearish_candle"
REASON_ORDERBOOK_SELL_PRESSURE = "orderbook_sell_pressure"
REASON_TAKE_PROFIT_FIXED_PCT = "take_profit_fixed_pct"
REASON_TAKE_PROFIT_1R = "take_profit_1r"
REASON_TAKE_PROFIT_2R_PARTIAL = "take_profit_2r_partial"
REASON_TRAILING_HIGH_PULLBACK = "trailing_high_pullback"
REASON_BREAK_EVEN_STOP_AFTER_1R = "break_even_stop_after_1r"
REASON_TIME_STOP_NO_PROGRESS = "time_stop_no_progress"
REASON_FORCE_EXIT_AFTER_1505 = "force_exit_after_1505"
REASON_FORCE_EXIT_DEADLINE = "force_exit_deadline"
REASON_CLOSING_AUCTION_EMERGENCY_EXIT = "closing_auction_emergency_exit"

R_UNIT_PCT = 0.015
EXIT_BE_R = 1.0
EXIT_PARTIAL_R = 2.0
EXIT_PARTIAL_RATIO = 0.5
TRAIL_HIGHEST_GIVEBACK_R = 0.7
EXIT_TIME_LIMIT_SECONDS = 25 * 60
EXIT_MIN_CHEJAN_STRENGTH = 80.0
EXIT_MA_PERIOD = 5
ENV_BREAK_BUFFER_PCT = 0.001
FIXED_TAKE_PROFIT_PCT = 0.020
FIXED_STOP_LOSS_PCT = 0.015
FIVE_MIN_MA_EXIT_PERIOD = 20
FIVE_MIN_MA_BREAK_BUFFER_PCT = 0.001


@dataclass
class ExitDecision:
    action: str
    qty_ratio: float = 0.0
    reason: str = ""
    update_stop_to_be: bool = False
    mark_partial_taken: bool = False
    exit_type: str = EXIT_TYPE_UNKNOWN
    exit_reason_code: str = ""
    reason_detail: str = ""
    priority: int = 99
    symbol: str = ""
    position_id: str = ""
    qty_to_sell: int = 0
    entry_price: int = 0
    current_price: int = 0
    stop_price: int = 0
    take_profit_price: int = 0
    trailing_stop_price: int = 0
    high_since_entry: int = 0
    low_since_entry: int = 0
    pnl_pct: float = 0.0
    mfe_pct: float = 0.0
    mae_pct: float = 0.0
    holding_minutes: float = 0.0
    exit_policy_source: str = "exit_strategy.evaluate_exit"
    decision_trace: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_exit(self) -> bool:
        return self.action in {
            ACTION_SELL_PARTIAL,
            ACTION_SELL_ALL,
            ACTION_STOP_LOSS,
            ACTION_TRAILING_STOP,
            ACTION_TIME_STOP,
            ACTION_FORCE_EXIT,
        }

    @property
    def is_partial(self) -> bool:
        return self.action == ACTION_SELL_PARTIAL

    def as_log_fields(self) -> Dict[str, Any]:
        return {
            "exit_type": self.exit_type,
            "exit_reason_code": self.exit_reason_code,
            "stop_reason": self.exit_reason_code if self.action in {ACTION_STOP_LOSS, ACTION_TRAILING_STOP, ACTION_TIME_STOP, ACTION_FORCE_EXIT} else "",
            "exit_policy_source": self.exit_policy_source,
            "exit_decision_trace": dict(self.decision_trace),
        }


@dataclass
class ExitContext:
    position: Position
    current_price: int
    chejan_strength: float
    minute_bars: List[MinuteBar]
    five_min_ind: Optional[FiveMinIndicators]
    now_ts: float
    symbol: str = ""
    position_id: str = ""
    intraday_vwap: float = 0.0
    vwap_below_since: float = 0.0
    signal_bar_low: int = 0
    chejan_strength_history: Optional[List[float]] = None
    orderbook_sell_pressure: bool = False
    force_exit: bool = False
    force_exit_deadline: bool = False
    closing_auction_emergency: bool = False
    config: Any = None


def evaluate_exit(ctx: ExitContext) -> ExitDecision:
    pos = ctx.position
    cur = int(ctx.current_price or 0)
    config = ctx.config or TRADE_CONFIG
    if pos.entry_price <= 0 or cur <= 0:
        return _hold(ctx, "missing_entry_or_current_price")

    entry = int(pos.entry_price)
    profit_rate = cur / entry - 1
    r_unit = float(pos.r_unit_pct if pos.r_unit_pct > 0 else R_UNIT_PCT)
    r = profit_rate / r_unit if r_unit > 0 else 0.0
    high = int(max(pos.highest_price or 0, cur, entry))
    low = _low_since_entry(ctx, cur, entry)
    mfe_pct = high / entry - 1 if entry > 0 else 0.0
    mae_pct = low / entry - 1 if entry > 0 else 0.0
    holding_minutes = _holding_minutes(pos, ctx.now_ts)
    update_stop = r >= _cfg(config, "move_stop_to_break_even_at_r", EXIT_BE_R) and pos.stop_price < entry

    trace = {
        "r": round(r, 4),
        "r_unit_pct": r_unit,
        "profit_rate": profit_rate,
        "high_since_entry": high,
        "low_since_entry": low,
        "intraday_vwap": float(ctx.intraday_vwap or 0.0),
        "chejan_strength": float(ctx.chejan_strength or 0.0),
        "holding_minutes": holding_minutes,
        "partial_taken": bool(pos.partial_taken),
        "force_exit": bool(ctx.force_exit),
        "force_exit_deadline": bool(ctx.force_exit_deadline),
        "closing_auction_emergency": bool(ctx.closing_auction_emergency),
    }

    def decision(
        *,
        action: str,
        exit_type: str,
        reason_code: str,
        detail: str,
        priority: int,
        qty_ratio: float = 1.0,
        mark_partial_taken: bool = False,
        trailing_stop_price: int = 0,
    ) -> ExitDecision:
        qty_to_sell = _qty_to_sell(pos, qty_ratio)
        return ExitDecision(
            action=action,
            qty_ratio=float(qty_ratio),
            reason=detail,
            update_stop_to_be=bool(update_stop),
            mark_partial_taken=bool(mark_partial_taken),
            exit_type=exit_type,
            exit_reason_code=reason_code,
            reason_detail=detail,
            priority=priority,
            symbol=ctx.symbol or getattr(pos, "code", ""),
            position_id=ctx.position_id or str(getattr(pos, "candidate_id", "") or ""),
            qty_to_sell=qty_to_sell,
            entry_price=entry,
            current_price=cur,
            stop_price=int(pos.stop_price or 0),
            take_profit_price=int(pos.target_price or 0),
            trailing_stop_price=int(trailing_stop_price or 0),
            high_since_entry=high,
            low_since_entry=low,
            pnl_pct=profit_rate,
            mfe_pct=mfe_pct,
            mae_pct=mae_pct,
            holding_minutes=holding_minutes,
            decision_trace={**trace, "matched_rule": reason_code, "priority": priority},
        )

    if ctx.closing_auction_emergency:
        return decision(
            action=ACTION_FORCE_EXIT,
            exit_type=EXIT_TYPE_CLOSING_AUCTION_EMERGENCY_EXIT,
            reason_code=REASON_CLOSING_AUCTION_EMERGENCY_EXIT,
            detail="closing auction emergency exit",
            priority=1,
        )

    fixed_stop_pct = float(_cfg(config, "fixed_stop_loss_pct", FIXED_STOP_LOSS_PCT) or FIXED_STOP_LOSS_PCT)
    if profit_rate <= -abs(fixed_stop_pct):
        return decision(
            action=ACTION_STOP_LOSS,
            exit_type=EXIT_TYPE_HARD_STOP,
            reason_code=REASON_HARD_STOP_FIXED_PCT,
            detail="fixed hard stop reached ({:.2%})".format(profit_rate),
            priority=2,
        )

    if pos.stop_price > 0 and cur <= pos.stop_price:
        reason_code = REASON_HARD_STOP_POSITION_STOP_PRICE
        exit_type = EXIT_TYPE_HARD_STOP
        if pos.stop_price >= entry:
            reason_code = REASON_BREAK_EVEN_STOP_AFTER_1R
            exit_type = EXIT_TYPE_BREAK_EVEN_STOP
        return decision(
            action=ACTION_STOP_LOSS,
            exit_type=exit_type,
            reason_code=reason_code,
            detail="position stop reached (stop {}, pnl {:.2%})".format(pos.stop_price, profit_rate),
            priority=2,
        )

    if _cfg_bool(config, "technical_stop_enabled", True) and _cfg_bool(config, "structure_stop_enabled", True):
        signal_low = _signal_bar_low(ctx)
        if signal_low > 0 and cur < signal_low:
            return decision(
                action=ACTION_STOP_LOSS,
                exit_type=EXIT_TYPE_STRUCTURE_STOP,
                reason_code=REASON_STRUCTURE_SIGNAL_BAR_LOW_BREAK,
                detail="signal bar low break ({} < {})".format(cur, signal_low),
                priority=3,
            )
        recent_low = _recent_swing_low(ctx, config)
        if recent_low > 0 and cur < recent_low:
            return decision(
                action=ACTION_STOP_LOSS,
                exit_type=EXIT_TYPE_STRUCTURE_STOP,
                reason_code=REASON_STRUCTURE_RECENT_1M_LOW_BREAK,
                detail="recent 1m swing low break ({} < {})".format(cur, recent_low),
                priority=3,
            )

    if _cfg_bool(config, "technical_stop_enabled", True) and _cfg_bool(config, "vwap_stop_enabled", True):
        vwap = float(ctx.intraday_vwap or 0.0)
        if vwap > 0 and cur < vwap:
            fast_drop_pct = float(_cfg(config, "vwap_fast_drop_pct", 0.01) or 0.01)
            if (vwap - cur) / vwap >= fast_drop_pct:
                return decision(
                    action=ACTION_STOP_LOSS,
                    exit_type=EXIT_TYPE_VWAP_STOP,
                    reason_code=REASON_VWAP_BREAK_FAST_DROP,
                    detail="fast VWAP break ({:.2%} below VWAP)".format((vwap - cur) / vwap),
                    priority=4,
                )
            wait_sec = float(_cfg(config, "vwap_reclaim_wait_sec", 60) or 60)
            if ctx.vwap_below_since > 0 and ctx.now_ts - ctx.vwap_below_since >= wait_sec:
                return decision(
                    action=ACTION_STOP_LOSS,
                    exit_type=EXIT_TYPE_VWAP_STOP,
                    reason_code=REASON_VWAP_RECLAIM_FAILED,
                    detail="VWAP reclaim failed for {:.0f}s".format(ctx.now_ts - ctx.vwap_below_since),
                    priority=4,
                )

    if _cfg_bool(config, "technical_stop_enabled", True):
        if _trade_strength_drop(ctx, config):
            return decision(
                action=ACTION_STOP_LOSS,
                exit_type=EXIT_TYPE_MOMENTUM_WEAKNESS_STOP,
                reason_code=REASON_MOMENTUM_TRADE_STRENGTH_DROP,
                detail="trade strength drop",
                priority=4,
            )
        if _bearish_volume_candle(ctx, config):
            return decision(
                action=ACTION_STOP_LOSS,
                exit_type=EXIT_TYPE_MOMENTUM_WEAKNESS_STOP,
                reason_code=REASON_MOMENTUM_VOLUME_BEARISH_CANDLE,
                detail="bearish candle with elevated volume",
                priority=4,
            )
        if _cfg_bool(config, "orderbook_sell_pressure_enabled", False) and ctx.orderbook_sell_pressure:
            return decision(
                action=ACTION_STOP_LOSS,
                exit_type=EXIT_TYPE_MOMENTUM_WEAKNESS_STOP,
                reason_code=REASON_ORDERBOOK_SELL_PRESSURE,
                detail="orderbook sell pressure",
                priority=4,
            )

    if ctx.force_exit or ctx.force_exit_deadline:
        return decision(
            action=ACTION_FORCE_EXIT,
            exit_type=EXIT_TYPE_FORCE_EXIT,
            reason_code=REASON_FORCE_EXIT_DEADLINE if ctx.force_exit_deadline else REASON_FORCE_EXIT_AFTER_1505,
            detail="force exit window",
            priority=5,
        )

    trailing_start = float(_cfg(config, "trailing_start_profit_pct", 0.015) or 0.015)
    trailing_pullback = float(_cfg(config, "trailing_pullback_pct", 0.008) or 0.008)
    trailing_stop_price = int(high * (1 - trailing_pullback)) if high > 0 else 0
    if high > cur and (profit_rate >= trailing_start or pos.partial_taken):
        pullback = high / cur - 1
        r_unit_abs = entry * r_unit
        giveback_r = (high - cur) / r_unit_abs if r_unit_abs > 0 else 0.0
        if pullback >= trailing_pullback or (pos.partial_taken and giveback_r >= TRAIL_HIGHEST_GIVEBACK_R):
            return decision(
                action=ACTION_TRAILING_STOP,
                exit_type=EXIT_TYPE_TRAILING_STOP,
                reason_code=REASON_TRAILING_HIGH_PULLBACK,
                detail="high pullback trailing stop (pullback {:.2%}, giveback {:.2f}R)".format(pullback, giveback_r),
                priority=6,
                trailing_stop_price=trailing_stop_price,
            )

    if _cfg_bool(config, "partial_take_profit_enabled", True) and r >= float(_cfg(config, "first_partial_take_profit_r", EXIT_PARTIAL_R) or EXIT_PARTIAL_R) and not pos.partial_taken:
        return decision(
            action=ACTION_SELL_PARTIAL,
            exit_type=EXIT_TYPE_PARTIAL_PROFIT_TAKE,
            reason_code=REASON_TAKE_PROFIT_2R_PARTIAL,
            detail="partial take profit at {:.2f}R ({:.2%})".format(r, profit_rate),
            priority=7,
            qty_ratio=float(_cfg(config, "first_partial_take_profit_ratio", EXIT_PARTIAL_RATIO) or EXIT_PARTIAL_RATIO),
            mark_partial_taken=True,
        )

    fixed_take_profit = float(_cfg(config, "fixed_take_profit_pct", FIXED_TAKE_PROFIT_PCT) or FIXED_TAKE_PROFIT_PCT)
    fixed_take_profit_allowed = (
        _cfg_bool(config, "fixed_take_profit_as_fallback", True)
        and profit_rate >= fixed_take_profit
        and (pos.partial_taken or not _cfg_bool(config, "partial_take_profit_enabled", True))
    )
    if fixed_take_profit_allowed:
        return decision(
            action=ACTION_SELL_ALL,
            exit_type=EXIT_TYPE_PROFIT_TAKE,
            reason_code=REASON_TAKE_PROFIT_FIXED_PCT,
            detail="fixed take profit reached ({:.2%})".format(profit_rate),
            priority=7,
        )

    if _cfg_bool(config, "enable_r_multiple_exit", True) and update_stop:
        trace["stop_update_reason_code"] = REASON_TAKE_PROFIT_1R

    time_limit = int(_cfg(config, "time_stop_seconds", EXIT_TIME_LIMIT_SECONDS) or EXIT_TIME_LIMIT_SECONDS)
    if holding_minutes * 60 >= time_limit and r < float(_cfg(config, "move_stop_to_break_even_at_r", EXIT_BE_R) or EXIT_BE_R):
        return decision(
            action=ACTION_TIME_STOP,
            exit_type=EXIT_TYPE_TIME_STOP,
            reason_code=REASON_TIME_STOP_NO_PROGRESS,
            detail="time stop no progress ({:.0f}s, {:.2f}R)".format(holding_minutes * 60, r),
            priority=8,
        )

    return ExitDecision(
        action=ACTION_HOLD,
        qty_ratio=0.0,
        reason="hold (R={:.2f}, pnl {:.2%}{})".format(r, profit_rate, ", move stop to BE" if update_stop else ""),
        update_stop_to_be=bool(update_stop),
        symbol=ctx.symbol or getattr(pos, "code", ""),
        position_id=ctx.position_id or str(getattr(pos, "candidate_id", "") or ""),
        entry_price=entry,
        current_price=cur,
        stop_price=int(pos.stop_price or 0),
        take_profit_price=int(pos.target_price or 0),
        high_since_entry=high,
        low_since_entry=low,
        pnl_pct=profit_rate,
        mfe_pct=mfe_pct,
        mae_pct=mae_pct,
        holding_minutes=holding_minutes,
        decision_trace={**trace, "matched_rule": "hold"},
    )


def _hold(ctx: ExitContext, reason: str) -> ExitDecision:
    return ExitDecision(
        action=ACTION_HOLD,
        qty_ratio=0.0,
        reason=reason,
        symbol=ctx.symbol or getattr(ctx.position, "code", ""),
        current_price=int(ctx.current_price or 0),
        decision_trace={"matched_rule": "hold", "reason": reason},
    )


def _cfg(config: Any, name: str, default: Any) -> Any:
    return getattr(config, name, default)


def _cfg_bool(config: Any, name: str, default: bool) -> bool:
    return bool(getattr(config, name, default))


def _holding_minutes(pos: Position, now_ts: float) -> float:
    entry_anchor = float(pos.entry1_time or pos.entry_time or now_ts)
    return max(float(now_ts) - entry_anchor, 0.0) / 60.0


def _low_since_entry(ctx: ExitContext, cur: int, entry: int) -> int:
    lows = [int(bar.low) for bar in ctx.minute_bars if getattr(bar, "low", 0)]
    lows.extend([cur, entry])
    return min(lows) if lows else min(cur, entry)


def _qty_to_sell(pos: Position, qty_ratio: float) -> int:
    quantity = max(int(getattr(pos, "quantity", 0) or 0), 0)
    if quantity <= 0:
        return 0
    return min(max(int(quantity * float(qty_ratio or 0.0)), 1), quantity)


def _signal_bar_low(ctx: ExitContext) -> int:
    if int(ctx.signal_bar_low or 0) > 0:
        return int(ctx.signal_bar_low)
    position_low = int(getattr(ctx.position, "order_context", {}).get("signal_bar_low", 0) or 0)
    return position_low


def _recent_swing_low(ctx: ExitContext, config: Any) -> int:
    lookback = int(_cfg(config, "recent_low_lookback_bars", 3) or 3)
    if lookback <= 0 or len(ctx.minute_bars) < lookback + 1:
        return 0
    previous = ctx.minute_bars[-(lookback + 1):-1]
    lows = [int(bar.low) for bar in previous if getattr(bar, "low", 0)]
    return min(lows) if lows else 0


def _trade_strength_drop(ctx: ExitContext, config: Any) -> bool:
    history = ctx.chejan_strength_history or []
    current = float(ctx.chejan_strength or 0.0)
    if len(history) < 2 or current <= 0:
        return False
    baseline = max(float(value or 0.0) for value in history[:-1])
    if baseline <= 0:
        return False
    drop_pct = float(_cfg(config, "trade_strength_drop_pct", 30.0) or 30.0) / 100.0
    return current <= baseline * (1 - drop_pct)


def _bearish_volume_candle(ctx: ExitContext, config: Any) -> bool:
    if len(ctx.minute_bars) < 2:
        return False
    last = ctx.minute_bars[-1]
    previous = ctx.minute_bars[-2]
    if int(last.close or 0) >= int(last.open or 0):
        return False
    prev_volume = float(previous.volume or 0.0)
    if prev_volume <= 0:
        return False
    ratio_pct = float(last.volume or 0.0) / prev_volume * 100.0
    return ratio_pct >= float(_cfg(config, "bearish_volume_ratio_min", 150.0) or 150.0)
