from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import scoring


@dataclass(frozen=True)
class QuantStrategyConfig:
    condition_name: str = "퀀트조건식"
    entry_pullback_pct: float = 0.015
    min_chejan_strength: float = 100.0
    take_profit_pct: float = 0.020
    stop_loss_pct: float = 0.015
    max_positions: int = 3
    plan_source: str = "quant_condition_pullback"
    grade: str = "QUANT"
    order_gubun: str = "00"


@dataclass(frozen=True)
class QuantEntryDecision:
    status: str
    reason: str
    reason_code: str
    capture_price: int = 0
    current_price: int = 0
    pullback_pct: float = 0.0
    chejan_strength: float = 0.0
    entry_limit_price: int = 0
    stop_price: int = 0
    take_profit_price: int = 0
    safe_target_price: int = 0

    def to_prediction(
        self,
        *,
        code: str,
        name: str,
        config: QuantStrategyConfig,
        stage: int = 2,
        extra: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        prediction: Dict[str, object] = {
            "status": self.status,
            "code": code,
            "name": name,
            "current_price": self.current_price,
            "ratio": 1.0 if self.status == "ready" else 0.0,
            "stage": stage,
            "score": 1.0 if self.status == "ready" else 0.0,
            "grade": config.grade,
            "reason": self.reason,
            "reason_code": self.reason_code,
            "capture_price": self.capture_price,
            "safe_target_price": self.safe_target_price,
            "entry_limit_price": self.entry_limit_price,
            "stop_price": self.stop_price,
            "take_profit_price": self.take_profit_price,
            "order_gubun": config.order_gubun,
            "plan_source": config.plan_source,
            "entry_plan_reason": "퀀트조건식 포착가 -1.5% 눌림 지정가, +2% 익절/-1.5% 손절",
            "chejan_strength": self.chejan_strength,
            "pullback_pct": self.pullback_pct,
            "volume_speed": 0.0,
            "spread_rate": 0.0,
        }
        if extra:
            prediction.update(extra)
        return prediction


@dataclass(frozen=True)
class QuantExitDecision:
    action: str
    qty_ratio: float
    reason: str
    profit_pct: float


class QuantConditionStrategy:
    """Pure decision logic shared by live trading, backtests, and forward tests."""

    def __init__(self, config: Optional[QuantStrategyConfig] = None):
        self.config = config or QuantStrategyConfig()

    def trigger_price(self, capture_price: int) -> int:
        if capture_price <= 0:
            return 0
        return scoring.round_down_to_tick(
            capture_price * (1 - self.config.entry_pullback_pct)
        )

    def evaluate_entry(
        self,
        *,
        capture_price: int,
        current_price: int,
        chejan_strength: float,
        active_positions: int = 0,
    ) -> QuantEntryDecision:
        if current_price <= 0:
            return QuantEntryDecision(
                status="wait",
                reason="현재가 없음",
                reason_code="SAFE_NO_PRICE",
                capture_price=capture_price,
                current_price=current_price,
                chejan_strength=chejan_strength,
            )
        if capture_price <= 0:
            return QuantEntryDecision(
                status="wait",
                reason="포착가 저장 대기",
                reason_code="SAFE_NO_CAPTURE",
                capture_price=capture_price,
                current_price=current_price,
                chejan_strength=chejan_strength,
            )

        target_price = self.trigger_price(capture_price)
        pullback_pct = (capture_price - current_price) / capture_price
        if pullback_pct < self.config.entry_pullback_pct:
            return QuantEntryDecision(
                status="wait",
                reason="퀀트조건식 눌림 대기 {:.2%} < {:.2%} (capture={} trigger={})".format(
                    pullback_pct,
                    self.config.entry_pullback_pct,
                    capture_price,
                    target_price,
                ),
                reason_code="SAFE_PULLBACK_SHALLOW",
                capture_price=capture_price,
                current_price=current_price,
                pullback_pct=pullback_pct,
                chejan_strength=chejan_strength,
                safe_target_price=target_price,
            )
        if chejan_strength < self.config.min_chejan_strength:
            return QuantEntryDecision(
                status="wait",
                reason="퀀트조건식 체결강도 대기 {:.1f} < {:.0f} (pullback {:.2%})".format(
                    chejan_strength,
                    self.config.min_chejan_strength,
                    pullback_pct,
                ),
                reason_code="SAFE_CHEJAN_WAIT",
                capture_price=capture_price,
                current_price=current_price,
                pullback_pct=pullback_pct,
                chejan_strength=chejan_strength,
                safe_target_price=target_price,
            )
        if active_positions >= self.config.max_positions:
            return QuantEntryDecision(
                status="wait",
                reason="최대 보유 종목 {}개 도달".format(self.config.max_positions),
                reason_code="SAFE_MAX_POSITIONS",
                capture_price=capture_price,
                current_price=current_price,
                pullback_pct=pullback_pct,
                chejan_strength=chejan_strength,
                safe_target_price=target_price,
            )

        entry_limit_price = scoring.round_down_to_tick(current_price)
        stop_price = scoring.round_down_to_tick(
            entry_limit_price * (1 - self.config.stop_loss_pct)
        )
        take_profit_price = scoring.round_up_to_tick(
            entry_limit_price * (1 + self.config.take_profit_pct)
        )
        return QuantEntryDecision(
            status="ready",
            reason="포착가 대비 눌림 {:.2%} >= {:.2%} + 체결강도 {:.1f} >= {:.0f}".format(
                pullback_pct,
                self.config.entry_pullback_pct,
                chejan_strength,
                self.config.min_chejan_strength,
            ),
            reason_code="QUANT_PULLBACK_READY",
            capture_price=capture_price,
            current_price=current_price,
            pullback_pct=pullback_pct,
            chejan_strength=chejan_strength,
            entry_limit_price=entry_limit_price,
            stop_price=stop_price,
            take_profit_price=take_profit_price,
            safe_target_price=target_price,
        )

    def evaluate_exit(self, *, entry_price: int, current_price: int) -> QuantExitDecision:
        if entry_price <= 0 or current_price <= 0:
            return QuantExitDecision("hold", 0.0, "진입가/현재가 정보 부족", 0.0)

        profit_pct = current_price / entry_price - 1
        if profit_pct >= self.config.take_profit_pct:
            return QuantExitDecision(
                "sell",
                1.0,
                "퀀트조건식 익절 {:.2%} >= {:.2%}".format(
                    profit_pct, self.config.take_profit_pct
                ),
                profit_pct,
            )
        if profit_pct <= -self.config.stop_loss_pct:
            return QuantExitDecision(
                "sell",
                1.0,
                "퀀트조건식 손절 {:.2%} <= -{:.2%}".format(
                    profit_pct, self.config.stop_loss_pct
                ),
                profit_pct,
            )
        return QuantExitDecision("hold", 0.0, "퀀트조건식 청산 조건 대기", profit_pct)
