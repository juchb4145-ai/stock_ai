from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import scoring
from quant_condition_strategy import QuantConditionStrategy


@dataclass(frozen=True)
class BacktestTick:
    code: str
    price: int
    chejan_strength: float = 0.0
    at: str = ""
    market_state: str = "neutral"
    bid_price: int = 0
    ask_price: int = 0
    low_price: int = 0
    high_price: int = 0
    available_volume: int = 0

    @property
    def bid(self) -> int:
        return int(self.bid_price or self.price)

    @property
    def ask(self) -> int:
        return int(self.ask_price or self.price)

    @property
    def low(self) -> int:
        return int(self.low_price or self.price)

    @property
    def high(self) -> int:
        return int(self.high_price or self.price)


@dataclass(frozen=True)
class BacktestTrade:
    code: str
    entry_price: int
    exit_price: int
    entry_at: str
    exit_at: str
    reason: str
    return_pct: float
    gross_return_pct: float = 0.0
    fee_cost: float = 0.0
    tax_cost: float = 0.0
    quantity: int = 1
    entry_order_at: str = ""
    exit_order_at: str = ""
    entry_fill_ratio: float = 1.0


@dataclass(frozen=True)
class BacktestExecutionConfig:
    """Realistic execution knobs for condition-strategy backtests."""

    quantity: int = 1
    buy_commission_rate: float = 0.00015
    sell_commission_rate: float = 0.00015
    sell_tax_rate: float = 0.0018
    buy_slippage_pct: float = 0.0005
    sell_slippage_pct: float = 0.0005
    latency_ticks: int = 0
    max_orders_per_second: int = 5
    min_fill_ratio: float = 1.0


@dataclass
class _PendingOrder:
    code: str
    side: str
    limit_price: int
    decision_index: int
    eligible_index: int
    ordered_at: str
    reason: str = ""


def _time_to_seconds(value: str) -> Optional[int]:
    raw = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(raw) < 6:
        return None
    raw = raw[-6:]
    hour = int(raw[0:2])
    minute = int(raw[2:4])
    second = int(raw[4:6])
    return hour * 3600 + minute * 60 + second


def _seconds_to_time(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hour = seconds // 3600
    minute = (seconds % 3600) // 60
    second = seconds % 60
    return f"{hour:02d}{minute:02d}{second:02d}"


class _OrderRateLimiter:
    def __init__(self, max_orders_per_second: int):
        self.max_orders_per_second = max(1, int(max_orders_per_second or 1))
        self.sent_seconds: List[int] = []

    def schedule(self, requested_at: str) -> str:
        requested_second = _time_to_seconds(requested_at)
        if requested_second is None:
            return requested_at

        scheduled = requested_second
        while True:
            same_second = sum(1 for value in self.sent_seconds if value == scheduled)
            if same_second < self.max_orders_per_second:
                self.sent_seconds.append(scheduled)
                return _seconds_to_time(scheduled)
            scheduled += 1


def _round_buy(price: float) -> int:
    return scoring.round_up_to_tick(price)


def _round_sell(price: float) -> int:
    return scoring.round_down_to_tick(price)


class QuantConditionBacktester:
    """Replay saved condition captures with historical ticks/minute bars."""

    def __init__(
        self,
        strategy: Optional[QuantConditionStrategy] = None,
        execution: Optional[BacktestExecutionConfig] = None,
    ):
        self.strategy = strategy or QuantConditionStrategy()
        self.execution = execution or BacktestExecutionConfig()

    def _buy_fill(self, order: _PendingOrder, tick: BacktestTick) -> Tuple[int, float]:
        if tick.low > order.limit_price:
            return 0, 0.0
        quantity = max(1, int(self.execution.quantity))
        if tick.available_volume > 0:
            filled = min(quantity, int(tick.available_volume))
        else:
            filled = quantity
        fill_ratio = filled / quantity
        if fill_ratio < self.execution.min_fill_ratio:
            return 0, fill_ratio
        raw_price = min(order.limit_price, tick.ask)
        fill_price = _round_buy(raw_price * (1 + self.execution.buy_slippage_pct))
        return fill_price, fill_ratio

    def _sell_fill(self, tick: BacktestTick) -> int:
        raw_price = min(int(tick.price), tick.bid)
        return _round_sell(raw_price * (1 - self.execution.sell_slippage_pct))

    def _net_return(
        self,
        *,
        entry_price: int,
        exit_price: int,
        quantity: int,
    ) -> Tuple[float, float, float, float]:
        buy_amount = entry_price * quantity
        sell_amount = exit_price * quantity
        fee_cost = (
            buy_amount * self.execution.buy_commission_rate
            + sell_amount * self.execution.sell_commission_rate
        )
        tax_cost = sell_amount * self.execution.sell_tax_rate
        gross_return_pct = exit_price / entry_price - 1 if entry_price > 0 else 0.0
        net_profit = sell_amount - buy_amount - fee_cost - tax_cost
        net_return_pct = net_profit / buy_amount if buy_amount > 0 else 0.0
        return net_return_pct, gross_return_pct, fee_cost, tax_cost

    def run(
        self,
        *,
        captures: Sequence[Dict[str, object]],
        ticks_by_code: Dict[str, Iterable[BacktestTick]],
    ) -> List[BacktestTrade]:
        trades: List[BacktestTrade] = []
        limiter = _OrderRateLimiter(self.execution.max_orders_per_second)
        for capture in captures:
            code = str(capture.get("code", ""))
            capture_price = int(float(capture.get("capture_price") or 0))
            if not code or capture_price <= 0:
                continue

            position_entry = 0
            entry_at = ""
            entry_order_at = ""
            entry_fill_ratio = 0.0
            pending_order: Optional[_PendingOrder] = None
            recent_low_price = capture_price
            ticks = list(ticks_by_code.get(code, []))
            for index, tick in enumerate(ticks):
                recent_low_price = min(recent_low_price, int(tick.price))
                if position_entry <= 0:
                    if (
                        pending_order is not None
                        and pending_order.side == "buy"
                        and index >= pending_order.eligible_index
                    ):
                        fill_price, fill_ratio = self._buy_fill(pending_order, tick)
                        if fill_price > 0:
                            position_entry = fill_price
                            entry_at = tick.at
                            entry_order_at = pending_order.ordered_at
                            entry_fill_ratio = fill_ratio
                            pending_order = None
                        continue
                    if pending_order is not None:
                        continue

                    entry = self.strategy.evaluate_entry(
                        capture_price=capture_price,
                        current_price=int(tick.price),
                        chejan_strength=float(tick.chejan_strength),
                        active_positions=0,
                        recent_low_price=recent_low_price,
                        market_state=tick.market_state,
                    )
                    if entry.status == "ready":
                        ordered_at = limiter.schedule(tick.at)
                        pending_order = _PendingOrder(
                            code=code,
                            side="buy",
                            limit_price=entry.entry_limit_price,
                            decision_index=index,
                            eligible_index=index + max(0, self.execution.latency_ticks),
                            ordered_at=ordered_at,
                            reason=entry.reason,
                        )
                        if pending_order.eligible_index <= index:
                            fill_price, fill_ratio = self._buy_fill(pending_order, tick)
                            if fill_price > 0:
                                position_entry = fill_price
                                entry_at = tick.at
                                entry_order_at = pending_order.ordered_at
                                entry_fill_ratio = fill_ratio
                                pending_order = None
                    continue

                exit_decision = self.strategy.evaluate_exit(
                    entry_price=position_entry,
                    current_price=int(tick.price),
                )
                if exit_decision.action == "sell":
                    ordered_at = limiter.schedule(tick.at)
                    eligible_index = index + max(0, self.execution.latency_ticks)
                    fill_tick = ticks[eligible_index] if eligible_index < len(ticks) else tick
                    exit_price = self._sell_fill(fill_tick)
                    quantity = max(1, int(self.execution.quantity))
                    net_return_pct, gross_return_pct, fee_cost, tax_cost = self._net_return(
                        entry_price=position_entry,
                        exit_price=exit_price,
                        quantity=quantity,
                    )
                    trades.append(
                        BacktestTrade(
                            code=code,
                            entry_price=position_entry,
                            exit_price=exit_price,
                            entry_at=entry_at,
                            exit_at=fill_tick.at,
                            reason=exit_decision.reason,
                            return_pct=net_return_pct,
                            gross_return_pct=gross_return_pct,
                            fee_cost=fee_cost,
                            tax_cost=tax_cost,
                            quantity=quantity,
                            entry_order_at=entry_order_at,
                            exit_order_at=ordered_at,
                            entry_fill_ratio=entry_fill_ratio,
                        )
                    )
                    break
        return trades


class QuantForwardSimulator:
    """Paper-trading state machine that uses the same strategy as live trading."""

    def __init__(self, strategy: Optional[QuantConditionStrategy] = None):
        self.strategy = strategy or QuantConditionStrategy()
        self.captures: Dict[str, int] = {}
        self.recent_lows: Dict[str, int] = {}
        self.positions: Dict[str, int] = {}
        self.closed_trades: List[BacktestTrade] = []

    def on_capture(self, code: str, capture_price: int) -> None:
        if capture_price > 0:
            self.captures[code] = int(capture_price)
            self.recent_lows[code] = int(capture_price)

    def on_tick(self, tick: BacktestTick) -> Dict[str, object]:
        if tick.code in self.positions:
            entry_price = self.positions[tick.code]
            exit_decision = self.strategy.evaluate_exit(
                entry_price=entry_price,
                current_price=int(tick.price),
            )
            if exit_decision.action == "sell":
                self.closed_trades.append(
                    BacktestTrade(
                        code=tick.code,
                        entry_price=entry_price,
                        exit_price=int(tick.price),
                        entry_at="",
                        exit_at=tick.at,
                        reason=exit_decision.reason,
                        return_pct=exit_decision.profit_pct,
                    )
                )
                self.positions.pop(tick.code, None)
            return {
                "code": tick.code,
                "state": "holding",
                "exit_action": exit_decision.action,
                "reason": exit_decision.reason,
            }

        capture_price = self.captures.get(tick.code, 0)
        if capture_price > 0:
            self.recent_lows[tick.code] = min(
                self.recent_lows.get(tick.code, capture_price),
                int(tick.price),
            )
        entry = self.strategy.evaluate_entry(
            capture_price=capture_price,
            current_price=int(tick.price),
            chejan_strength=float(tick.chejan_strength),
            active_positions=len(self.positions),
            recent_low_price=self.recent_lows.get(tick.code, 0),
            market_state=tick.market_state,
        )
        if entry.status == "ready":
            self.positions[tick.code] = entry.entry_limit_price
            return {
                "code": tick.code,
                "state": "entered",
                "entry_price": entry.entry_limit_price,
                "reason": entry.reason,
            }
        return {
            "code": tick.code,
            "state": "watching",
            "reason": entry.reason,
            "reason_code": entry.reason_code,
        }
