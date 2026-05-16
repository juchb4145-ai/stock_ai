from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Dict, Optional, Sequence

import scoring
from trade_config import TRADE_CONFIG


@dataclass(frozen=True)
class QuantStrategyConfig:
    condition_name: str = TRADE_CONFIG.strategy_name
    entry_pullback_pct: float = TRADE_CONFIG.pullback_entry_pct
    max_pullback_pct: float = TRADE_CONFIG.max_pullback_pct
    rebound_confirm_pct: float = TRADE_CONFIG.rebound_confirm_pct
    min_high_since_capture_pct: float = TRADE_CONFIG.min_pullback_after_signal_pct
    vwap_reclaim_buffer_pct: float = TRADE_CONFIG.vwap_reclaim_confirm_buffer_pct
    min_chejan_strength: float = TRADE_CONFIG.min_trade_strength
    min_leader_score: float = TRADE_CONFIG.min_leader_score
    leader_score_enabled: bool = TRADE_CONFIG.leader_score_enabled
    opening_min_leader_score: float = TRADE_CONFIG.opening_min_leader_score
    opening_quant_and_dante_min_leader_score: float = TRADE_CONFIG.opening_quant_and_dante_min_leader_score
    opening_quant_only_min_leader_score: float = TRADE_CONFIG.opening_quant_only_min_leader_score
    first_pullback_leader_score_relief: float = TRADE_CONFIG.first_pullback_leader_score_relief
    opening_leader_start: str = TRADE_CONFIG.opening_leader_start
    opening_leader_end: str = TRADE_CONFIG.opening_leader_end
    market_min_chejan_strength: Dict[str, float] = field(
        default_factory=lambda: {"weak": TRADE_CONFIG.weak_market_min_trade_strength}
    )
    take_profit_pct: float = 0.020
    stop_loss_pct: float = 0.015
    max_positions: int = TRADE_CONFIG.max_positions
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
    min_chejan_strength: float = 0.0
    market_state: str = "neutral"
    recent_low_price: int = 0
    rebound_pct: float = 0.0
    high_since_capture: int = 0
    low_after_high: int = 0
    pullback_from_high_pct: float = 0.0
    observed_pullback_from_high_pct: float = 0.0
    strategy_pullback_basis: int = 0
    entry_pullback_eligible: bool = False
    rebound_from_low_pct: float = 0.0
    intraday_vwap: float = 0.0
    vwap_support_ok: bool = True
    first_pullback_ready: bool = False
    leader_score: float = 0.0
    min_leader_score: float = 0.0
    entry_limit_price: int = 0
    stop_price: int = 0
    take_profit_price: int = 0
    safe_target_price: int = 0
    sector_regime: str = ""
    sector_gate_action: str = ""
    sector_gate_reason: str = ""
    theme_regime: str = ""
    theme_gate_action: str = ""
    theme_gate_reason: str = ""

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
            "entry_plan_reason": "quant first-pullback limit entry",
            "chejan_strength": self.chejan_strength,
            "min_chejan_strength": self.min_chejan_strength,
            "market_state": self.market_state,
            "pullback_pct": self.pullback_pct,
            "recent_low_price": self.recent_low_price,
            "rebound_pct": self.rebound_pct,
            "high_since_capture": self.high_since_capture,
            "low_after_high": self.low_after_high,
            "pullback_from_high_pct": self.pullback_from_high_pct,
            "observed_pullback_from_high_pct": self.observed_pullback_from_high_pct,
            "strategy_pullback_basis": self.strategy_pullback_basis,
            "entry_pullback_eligible": self.entry_pullback_eligible,
            "rebound_from_low_pct": self.rebound_from_low_pct,
            "intraday_vwap": self.intraday_vwap,
            "vwap_support_ok": self.vwap_support_ok,
            "first_pullback_ready": self.first_pullback_ready,
            "leader_score": self.leader_score,
            "min_leader_score": self.min_leader_score,
            "volume_speed": 0.0,
            "spread_rate": 0.0,
            "sector_regime": self.sector_regime,
            "sector_gate_action": self.sector_gate_action,
            "sector_gate_reason": self.sector_gate_reason,
            "theme_regime": self.theme_regime,
            "theme_gate_action": self.theme_gate_action,
            "theme_gate_reason": self.theme_gate_reason,
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

    def sector_theme_quality_adjustment(self, sector_context=None, theme_context=None) -> float:
        return 0.0

    def trigger_price(self, capture_price: int) -> int:
        if capture_price <= 0:
            return 0
        return scoring.round_down_to_tick(
            capture_price * (1 - self.config.entry_pullback_pct)
        )

    def min_chejan_strength_for_market(self, market_state: str = "neutral") -> float:
        state = (market_state or "neutral").lower()
        return float(
            self.config.market_min_chejan_strength.get(
                state, self.config.min_chejan_strength
            )
        )

    @staticmethod
    def _hhmmss_value(value: str, default: int) -> int:
        digits = "".join(ch for ch in str(value or "") if ch.isdigit())
        if not digits:
            return default
        try:
            return int(digits[:6].ljust(6, "0"))
        except ValueError:
            return default

    def leader_score_threshold(
        self,
        *,
        condition_combo: str = "",
        first_pullback_ready: bool = False,
        now_ts: Optional[float] = None,
    ) -> float:
        local = time.localtime(time.time() if now_ts is None else float(now_ts))
        hhmmss = local.tm_hour * 10000 + local.tm_min * 100 + local.tm_sec
        start = self._hhmmss_value(self.config.opening_leader_start, 90000)
        end = self._hhmmss_value(self.config.opening_leader_end, 93000)
        if start <= hhmmss <= end:
            combo = str(condition_combo or "").upper()
            if combo == "QUANT_AND_DANTE":
                threshold = float(self.config.opening_quant_and_dante_min_leader_score or 0.0)
            elif combo == "QUANT_ONLY":
                threshold = float(self.config.opening_quant_only_min_leader_score or 0.0)
            else:
                threshold = float(self.config.opening_min_leader_score or self.config.min_leader_score or 0.0)
        else:
            threshold = float(self.config.min_leader_score or 0.0)
        if first_pullback_ready and threshold > 0:
            threshold = max(0.0, threshold - float(self.config.first_pullback_leader_score_relief or 0.0))
        return threshold

    @staticmethod
    def _one_min_reversal_ok(
        *,
        current_price: int,
        minute_bars: Optional[Sequence[Any]],
        one_min_reversal: Optional[bool],
    ) -> bool:
        if one_min_reversal is not None:
            return bool(one_min_reversal)
        bars = list(minute_bars or [])
        if not bars:
            return True
        cur = bars[-1]
        cur_open = int(getattr(cur, "open", 0) or 0)
        cur_close = int(current_price or getattr(cur, "close", 0) or 0)
        if cur_open > 0 and cur_close > cur_open:
            return True
        if len(bars) >= 2:
            prev_high = int(getattr(bars[-2], "high", 0) or 0)
            if prev_high > 0 and cur_close >= prev_high:
                return True
        return False

    def evaluate_entry(
        self,
        *,
        capture_price: int,
        current_price: int,
        chejan_strength: float,
        active_positions: int = 0,
        recent_low_price: int = 0,
        market_state: str = "neutral",
        high_since_capture: int = 0,
        low_after_high: int = 0,
        intraday_vwap: Optional[float] = None,
        was_below_vwap: bool = False,
        minute_bars: Optional[Sequence[Any]] = None,
        one_min_reversal: Optional[bool] = None,
        leader_score: Optional[float] = None,
        condition_combo: str = "",
        now_ts: Optional[float] = None,
        market_context: Optional[Any] = None,
        sector_context: Optional[Any] = None,
        theme_context: Optional[Any] = None,
    ) -> QuantEntryDecision:
        if market_context is not None:
            market_state = (
                getattr(market_context, "primary_market_regime", None)
                or market_state
                or "neutral"
            )
            if market_state == "unknown":
                market_state = "neutral"
        min_chejan_strength = self.min_chejan_strength_for_market(market_state)
        min_leader_score = self.leader_score_threshold(
            condition_combo=condition_combo,
            first_pullback_ready=False,
            now_ts=now_ts,
        )
        normalized_leader_score = (
            float(leader_score or 0.0) if leader_score is not None else 0.0
        )
        high_since_capture = int(high_since_capture or 0)
        low_after_high = int(low_after_high or 0)
        intraday_vwap_value = float(intraday_vwap or 0.0)
        normalized_recent_low = recent_low_price if recent_low_price > 0 else current_price
        rebound_pct = (
            current_price / normalized_recent_low - 1
            if normalized_recent_low > 0 and current_price > 0
            else 0.0
        )
        observed_pullback_from_high_pct = (
            max((high_since_capture - current_price) / high_since_capture, 0.0)
            if high_since_capture > 0 and current_price > 0
            else 0.0
        )
        strategy_pullback_basis_default = 0
        entry_pullback_eligible_default = False
        sector_regime = getattr(sector_context, "sector_regime", "") if sector_context is not None else ""
        theme_regime = getattr(theme_context, "theme_regime", "") if theme_context is not None else ""

        def decision(
            *,
            status: str,
            reason: str,
            reason_code: str,
            pullback_pct: float = 0.0,
            rebound_from_low_pct: float = 0.0,
            vwap_support_ok: bool = True,
            first_pullback_ready: bool = False,
            entry_limit_price: int = 0,
            stop_price: int = 0,
            take_profit_price: int = 0,
            safe_target_price: int = 0,
            strategy_pullback_basis: int = 0,
            entry_pullback_eligible: Optional[bool] = None,
        ) -> QuantEntryDecision:
            return QuantEntryDecision(
                status=status,
                reason=reason,
                reason_code=reason_code,
                capture_price=capture_price,
                current_price=current_price,
                pullback_pct=pullback_pct,
                chejan_strength=chejan_strength,
                min_chejan_strength=min_chejan_strength,
                market_state=market_state,
                recent_low_price=normalized_recent_low,
                rebound_pct=rebound_pct,
                high_since_capture=high_since_capture,
                low_after_high=low_after_high,
                pullback_from_high_pct=observed_pullback_from_high_pct,
                observed_pullback_from_high_pct=observed_pullback_from_high_pct,
                strategy_pullback_basis=int(
                    strategy_pullback_basis or strategy_pullback_basis_default or 0
                ),
                entry_pullback_eligible=(
                    bool(entry_pullback_eligible)
                    if entry_pullback_eligible is not None
                    else bool(entry_pullback_eligible_default)
                ),
                rebound_from_low_pct=rebound_from_low_pct,
                intraday_vwap=intraday_vwap_value,
                vwap_support_ok=vwap_support_ok,
                first_pullback_ready=first_pullback_ready,
                leader_score=normalized_leader_score,
                min_leader_score=min_leader_score,
                entry_limit_price=entry_limit_price,
                stop_price=stop_price,
                take_profit_price=take_profit_price,
                safe_target_price=safe_target_price,
                sector_regime=sector_regime,
                sector_gate_action=getattr(sector_context, "sector_gate_action", "") if sector_context is not None else "",
                sector_gate_reason=getattr(sector_context, "sector_gate_reason", "") if sector_context is not None else "",
                theme_regime=theme_regime,
                theme_gate_action=getattr(theme_context, "theme_gate_action", "") if theme_context is not None else "",
                theme_gate_reason=getattr(theme_context, "theme_gate_reason", "") if theme_context is not None else "",
            )

        if current_price <= 0:
            return decision(
                status="wait",
                reason="current price missing",
                reason_code="SAFE_NO_PRICE",
            )
        if capture_price <= 0:
            return decision(
                status="wait",
                reason="capture price missing",
                reason_code="SAFE_NO_CAPTURE",
            )
        high_extension_pct = (
            high_since_capture / capture_price - 1
            if high_since_capture > capture_price
            else 0.0
        )
        use_high_basis = False
        if high_since_capture > capture_price:
            if high_extension_pct < self.config.min_high_since_capture_pct:
                return decision(
                    status="wait",
                    reason=(
                        "high since capture not extended enough {:.2%} < {:.2%}"
                    ).format(
                        high_extension_pct,
                        self.config.min_high_since_capture_pct,
                    ),
                    reason_code="SAFE_NO_HIGH_SINCE_CAPTURE",
                    safe_target_price=self.trigger_price(capture_price),
                )
            use_high_basis = True

        pullback_basis = high_since_capture if use_high_basis else capture_price
        strategy_pullback_basis_default = pullback_basis
        target_price = scoring.round_down_to_tick(
            pullback_basis * (1 - self.config.entry_pullback_pct)
        )
        pullback_pct = (pullback_basis - current_price) / pullback_basis
        entry_pullback_eligible_default = (
            pullback_pct >= self.config.entry_pullback_pct
            and pullback_pct <= self.config.max_pullback_pct
        )

        shallow_code = (
            "SAFE_PULLBACK_FROM_HIGH_SHALLOW"
            if use_high_basis
            else "SAFE_PULLBACK_SHALLOW"
        )
        deep_code = (
            "SAFE_PULLBACK_FROM_HIGH_TOO_DEEP"
            if use_high_basis
            else "SAFE_PULLBACK_TOO_DEEP"
        )
        if pullback_pct < self.config.entry_pullback_pct:
            return decision(
                status="wait",
                reason="pullback shallow {:.2%} < {:.2%}".format(
                    pullback_pct,
                    self.config.entry_pullback_pct,
                ),
                reason_code=shallow_code,
                pullback_pct=pullback_pct,
                safe_target_price=target_price,
            )
        if pullback_pct > self.config.max_pullback_pct:
            return decision(
                status="wait",
                reason="pullback too deep {:.2%} > {:.2%}".format(
                    pullback_pct,
                    self.config.max_pullback_pct,
                ),
                reason_code=deep_code,
                pullback_pct=pullback_pct,
                safe_target_price=target_price,
            )

        if use_high_basis:
            if low_after_high <= 0 or low_after_high >= high_since_capture:
                return decision(
                    status="wait",
                    reason="low after high missing",
                    reason_code="SAFE_LOW_AFTER_HIGH_MISSING",
                    pullback_pct=pullback_pct,
                    safe_target_price=target_price,
                )
            effective_low = min(low_after_high, current_price)
            rebound_from_low_pct = (
                current_price / effective_low - 1 if effective_low > 0 else 0.0
            )
        else:
            effective_low = normalized_recent_low
            rebound_from_low_pct = rebound_pct

        rebound_check_pct = rebound_from_low_pct if use_high_basis else rebound_pct
        rebound_code = (
            "SAFE_REBOUND_FROM_LOW_WAIT" if use_high_basis else "SAFE_REBOUND_WAIT"
        )
        if rebound_check_pct < self.config.rebound_confirm_pct:
            return decision(
                status="wait",
                reason="rebound wait {:.2%} < {:.2%}".format(
                    rebound_check_pct,
                    self.config.rebound_confirm_pct,
                ),
                reason_code=rebound_code,
                pullback_pct=pullback_pct,
                rebound_from_low_pct=rebound_from_low_pct,
                safe_target_price=target_price,
            )
        if chejan_strength < min_chejan_strength:
            return decision(
                status="wait",
                reason="trade strength wait {:.1f} < {:.0f}".format(
                    chejan_strength,
                    min_chejan_strength,
                ),
                reason_code="SAFE_CHEJAN_WAIT",
                pullback_pct=pullback_pct,
                rebound_from_low_pct=rebound_from_low_pct,
                safe_target_price=target_price,
            )

        vwap_support_ok = True
        if intraday_vwap_value > 0:
            vwap_line = intraday_vwap_value
            if was_below_vwap:
                vwap_line *= 1 + max(float(self.config.vwap_reclaim_buffer_pct or 0.0), 0.0)
            vwap_support_ok = current_price >= vwap_line
        if not vwap_support_ok:
            return decision(
                status="wait",
                reason="VWAP support/reclaim wait current={} vwap={:.2f}".format(
                    current_price,
                    intraday_vwap_value,
                ),
                reason_code="SAFE_VWAP_SUPPORT_WAIT",
                pullback_pct=pullback_pct,
                rebound_from_low_pct=rebound_from_low_pct,
                vwap_support_ok=False,
                safe_target_price=target_price,
            )

        if not self._one_min_reversal_ok(
            current_price=current_price,
            minute_bars=minute_bars,
            one_min_reversal=one_min_reversal,
        ):
            return decision(
                status="wait",
                reason="one-minute reversal confirmation wait",
                reason_code="SAFE_ONE_MIN_REVERSAL_WAIT",
                pullback_pct=pullback_pct,
                rebound_from_low_pct=rebound_from_low_pct,
                vwap_support_ok=vwap_support_ok,
                safe_target_price=target_price,
            )

        min_leader_score = self.leader_score_threshold(
            condition_combo=condition_combo,
            first_pullback_ready=True,
            now_ts=now_ts,
        )
        if (
            leader_score is not None
            and bool(getattr(self.config, "leader_score_enabled", True))
            and normalized_leader_score < min_leader_score
        ):
            return decision(
                status="wait",
                reason="leader score wait {:.1f} < {:.1f}".format(
                    normalized_leader_score,
                    min_leader_score,
                ),
                reason_code="WAIT_LEADER_SCORE",
                pullback_pct=pullback_pct,
                rebound_from_low_pct=rebound_from_low_pct,
                vwap_support_ok=vwap_support_ok,
                safe_target_price=target_price,
            )

        if active_positions >= self.config.max_positions:
            return decision(
                status="wait",
                reason="max positions reached {}".format(self.config.max_positions),
                reason_code="SAFE_MAX_POSITIONS",
                pullback_pct=pullback_pct,
                rebound_from_low_pct=rebound_from_low_pct,
                vwap_support_ok=vwap_support_ok,
                safe_target_price=target_price,
            )

        entry_limit_price = scoring.round_down_to_tick(current_price)
        stop_price = scoring.round_down_to_tick(
            entry_limit_price * (1 - self.config.stop_loss_pct)
        )
        take_profit_price = scoring.round_up_to_tick(
            entry_limit_price * (1 + self.config.take_profit_pct)
        )
        ready_code = "QUANT_FIRST_PULLBACK_READY" if use_high_basis else "QUANT_PULLBACK_READY"
        return decision(
            status="ready",
            reason=(
                "first pullback ready {:.2%} >= {:.2%}; rebound {:.2%}; strength {:.1f} >= {:.0f}"
            ).format(
                pullback_pct,
                self.config.entry_pullback_pct,
                rebound_check_pct,
                chejan_strength,
                min_chejan_strength,
            ),
            reason_code=ready_code,
            pullback_pct=pullback_pct,
            rebound_from_low_pct=rebound_from_low_pct,
            vwap_support_ok=vwap_support_ok,
            first_pullback_ready=True,
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
