from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

from quant_condition_strategy import QuantConditionStrategy


@dataclass(frozen=True)
class BacktestTick:
    code: str
    price: int
    chejan_strength: float = 0.0
    at: str = ""


@dataclass(frozen=True)
class BacktestTrade:
    code: str
    entry_price: int
    exit_price: int
    entry_at: str
    exit_at: str
    reason: str
    return_pct: float


class QuantConditionBacktester:
    """Replay saved condition captures with historical ticks/minute bars."""

    def __init__(self, strategy: Optional[QuantConditionStrategy] = None):
        self.strategy = strategy or QuantConditionStrategy()

    def run(
        self,
        *,
        captures: Sequence[Dict[str, object]],
        ticks_by_code: Dict[str, Iterable[BacktestTick]],
    ) -> List[BacktestTrade]:
        trades: List[BacktestTrade] = []
        for capture in captures:
            code = str(capture.get("code", ""))
            capture_price = int(float(capture.get("capture_price") or 0))
            if not code or capture_price <= 0:
                continue

            position_entry = 0
            entry_at = ""
            for tick in ticks_by_code.get(code, []):
                if position_entry <= 0:
                    entry = self.strategy.evaluate_entry(
                        capture_price=capture_price,
                        current_price=int(tick.price),
                        chejan_strength=float(tick.chejan_strength),
                        active_positions=0,
                    )
                    if entry.status == "ready":
                        position_entry = entry.entry_limit_price
                        entry_at = tick.at
                    continue

                exit_decision = self.strategy.evaluate_exit(
                    entry_price=position_entry,
                    current_price=int(tick.price),
                )
                if exit_decision.action == "sell":
                    trades.append(
                        BacktestTrade(
                            code=code,
                            entry_price=position_entry,
                            exit_price=int(tick.price),
                            entry_at=entry_at,
                            exit_at=tick.at,
                            reason=exit_decision.reason,
                            return_pct=exit_decision.profit_pct,
                        )
                    )
                    break
        return trades


class QuantForwardSimulator:
    """Paper-trading state machine that uses the same strategy as live trading."""

    def __init__(self, strategy: Optional[QuantConditionStrategy] = None):
        self.strategy = strategy or QuantConditionStrategy()
        self.captures: Dict[str, int] = {}
        self.positions: Dict[str, int] = {}
        self.closed_trades: List[BacktestTrade] = []

    def on_capture(self, code: str, capture_price: int) -> None:
        if capture_price > 0:
            self.captures[code] = int(capture_price)

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
        entry = self.strategy.evaluate_entry(
            capture_price=capture_price,
            current_price=int(tick.price),
            chejan_strength=float(tick.chejan_strength),
            active_positions=len(self.positions),
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
