from __future__ import annotations

import time
import uuid
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from time_policy import TimeDecision, TimePolicy
from trade_config import TradeConfig


logger = logging.getLogger(__name__)

LIVE_BREAKOUT_BLOCKED_BY = "live_breakout_probe_disabled"
LIVE_BREAKOUT_BLOCK_REASON_CODE = "BLOCK_LIVE_BREAKOUT_SMALL"
PAPER_ONLY_BREAKOUT_PLAN_SOURCE = "paper_only_breakout_probe"
LIVE_ANALYSIS_ONLY_BLOCKED_BY = "analysis_only_candidate"
LIVE_ANALYSIS_ONLY_REASON_CODE = "BLOCK_LIVE_ANALYSIS_ONLY_CANDIDATE"
_LIVE_BLOCKED_BREAKOUT_VALUES = {
    "BREAKOUT_SMALL",
    "BUY_BREAKOUT_SMALL",
    "READY_AGRADE_FIRST",
    "FINAL_PAPER_ONLY_BREAKOUT_PROBE",
    "FINAL_PAPER_ONLY_STRATEGY",
    "AFTERNOON_SECOND_WAVE",
    "CLOSING_STRENGTH",
    "TREND_CONTINUATION",
    "WEAK_VOLUME_RELIEF_PAPER_ONLY",
    "MIDDAY_VWAP_RECLAIM_PAPER_ONLY",
    "AFTERNOON_SECOND_WAVE_PAPER_ONLY",
    "CLOSING_STRENGTH_PAPER_ONLY",
    "TREND_CONTINUATION_PAPER_ONLY",
    "WEAK_VOLUME_RELIEF_PAPER_ONLY",
    "PAPER_ONLY_BREAKOUT_PROBE",
}


def _context_value(context: Dict[str, object], key: str) -> str:
    value = context.get(key, "")
    return str(value or "")


def is_live_breakout_probe_context(context: Dict[str, object]) -> bool:
    context = context or {}
    trace = context.get("decision_trace", {})
    if isinstance(trace, dict) and trace.get("paper_only_breakout_probe"):
        return True
    if isinstance(trace, dict) and trace.get("paper_only_strategy"):
        return True
    for key in ("entry_type", "reason_code", "momentum_reason_code", "final_reason_code"):
        if _context_value(context, key).upper() in _LIVE_BLOCKED_BREAKOUT_VALUES:
            return True
    for key in ("plan_source", "entry_plan_reason", "reason"):
        value = _context_value(context, key).lower()
        if "breakout_probe" in value or "breakout_small" in value:
            return True
    return False


def is_analysis_only_candidate_context(context: Dict[str, object]) -> bool:
    context = context or {}
    return (
        _context_value(context, "condition_combo").upper() == "DANTE_ONLY"
        or _context_value(context, "candidate_role").lower() == "analysis_only"
    )


@dataclass(frozen=True)
class OrderRequest:
    rqname: str
    screen_no: str
    order_type: int
    code: str
    quantity: int
    price: int
    order_gubun: str
    order_no: str = ""
    side: str = ""
    name: str = ""
    reason: str = ""
    current_price: int = 0
    entry_price: int = 0
    target_price: int = 0
    stop_price: int = 0
    plan_source: str = ""
    context: Dict[str, object] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    @property
    def is_cancel(self) -> bool:
        return self.order_type in (3, 4) or "cancel" in self.rqname

    @property
    def normalized_side(self) -> str:
        if self.side:
            return self.side
        if self.order_type in (1, 3):
            return "buy"
        if self.order_type in (2, 4):
            return "sell"
        return ""

    @property
    def guard_action(self) -> str:
        if self.is_cancel:
            if self.order_type == 3 or self.normalized_side == "buy":
                return "buy_cancel"
            if self.order_type == 4 or self.normalized_side == "sell":
                return "sell_cancel"
            return "cancel"
        return self.normalized_side


@dataclass(frozen=True)
class GuardDecision:
    allowed: bool
    live: bool
    paper: bool
    reason: str
    guard_decision_id: str = ""
    throttle_seconds: float = 0.0
    mode: str = ""
    blocked_by: str = ""
    symbol: str = ""
    requested_amount: int = 0
    daily_buy_count: int = 0
    daily_loss: float = 0.0
    effective_position_limit: int = 0
    effective_daily_exposure_limit: int = 0
    limit_source: str = ""
    is_reentry_blocked: bool = False
    time_decision: Dict[str, object] = field(default_factory=dict)
    time_decision_id: str = ""


@dataclass(frozen=True)
class LiveOrderToken:
    token_id: str
    guard_decision_id: str
    request_id: str
    symbol: str
    side: str
    guard_action: str
    rqname: str
    order_type: int
    quantity: int
    price: int
    order_gubun: str
    order_no: str
    created_at: float
    expires_at: float


@dataclass(frozen=True)
class RiskLimits:
    trading_enabled: bool
    live_trading_enabled: bool
    dry_run: bool
    max_daily_buy_count: int
    max_daily_loss: int
    max_position_size: int
    max_daily_exposure: int
    cash_usage_ratio: float
    max_position_cash_ratio: float
    max_daily_exposure_ratio: float
    reentry_cooldown_seconds: int
    max_orders_per_second: int

    @classmethod
    def from_config(cls, config: TradeConfig) -> "RiskLimits":
        return cls(
            trading_enabled=bool(config.trading_enabled),
            live_trading_enabled=bool(config.live_trading_enabled),
            dry_run=bool(config.dry_run),
            max_daily_buy_count=int(config.max_daily_buy_count),
            max_daily_loss=int(config.max_daily_loss),
            max_position_size=int(config.max_position_size),
            max_daily_exposure=int(config.max_daily_exposure),
            cash_usage_ratio=float(config.cash_usage_ratio),
            max_position_cash_ratio=float(config.max_position_cash_ratio),
            max_daily_exposure_ratio=float(config.max_daily_exposure_ratio),
            reentry_cooldown_seconds=int(config.reentry_cooldown_seconds),
            max_orders_per_second=int(config.max_orders_per_second),
        )


@dataclass(frozen=True)
class RiskState:
    mode: str
    account_state_available: bool = True
    daily_loss_available: bool = True
    daily_buy_count: int = 0
    daily_loss: float = 0.0
    daily_exposure: int = 0
    account_cash: int = 0
    open_positions: Set[str] = field(default_factory=set)
    pending_orders: Set[str] = field(default_factory=set)
    pending_order_ids: Set[str] = field(default_factory=set)
    last_exit_at: Dict[str, float] = field(default_factory=dict)


@dataclass
class PaperPosition:
    code: str
    name: str = ""
    quantity: int = 0
    entry_price: int = 0
    stop_price: int = 0
    target_price: int = 0
    opened_at: float = 0.0
    highest_price: int = 0
    plan_source: str = ""
    reason: str = ""

    def profit_rate(self, current_price: int) -> float:
        if self.entry_price <= 0 or current_price <= 0:
            return 0.0
        return current_price / self.entry_price - 1


class PaperPortfolio:
    def __init__(self, *, initial_cash: int = 10_000_000, daily_loss_limit_pct: float = 0.03):
        self.initial_cash = int(initial_cash)
        self.cash = int(initial_cash)
        self.daily_loss_limit_pct = float(daily_loss_limit_pct)
        self.positions: Dict[str, PaperPosition] = {}
        self.closed_trades: List[Dict[str, object]] = []
        self.last_exit_at: Dict[str, float] = {}
        self.daily_buy_count = 0
        self.realized_pnl = 0
        self.daily_buy_amount = 0

    def has_open_position(self, code: str) -> bool:
        position = self.positions.get(code)
        return bool(position and position.quantity > 0)

    def can_buy(
        self,
        code: str,
        *,
        max_daily_buy_count: int,
        reentry_cooldown_seconds: int = 0,
    ) -> GuardDecision:
        if self.has_open_position(code):
            return GuardDecision(False, False, True, "paper_position_already_open")
        if self.daily_buy_count >= max_daily_buy_count:
            return GuardDecision(False, False, True, "paper_daily_buy_limit")
        if self.realized_pnl <= -self.initial_cash * self.daily_loss_limit_pct:
            return GuardDecision(False, False, True, "paper_daily_loss_limit")
        last_exit = float(self.last_exit_at.get(code, 0.0) or 0.0)
        if reentry_cooldown_seconds > 0 and last_exit > 0:
            elapsed = time.time() - last_exit
            if elapsed < reentry_cooldown_seconds:
                return GuardDecision(False, False, True, "paper_reentry_cooldown")
        return GuardDecision(True, False, True, "paper_allowed")

    def apply_buy(self, request: OrderRequest, *, fill_price: int) -> None:
        quantity = max(int(request.quantity), 0)
        if quantity <= 0 or fill_price <= 0:
            return
        self.positions[request.code] = PaperPosition(
            code=request.code,
            name=request.name,
            quantity=quantity,
            entry_price=fill_price,
            stop_price=int(request.stop_price or 0),
            target_price=int(request.target_price or 0),
            opened_at=time.time(),
            highest_price=fill_price,
            plan_source=request.plan_source,
            reason=request.reason,
        )
        self.cash -= quantity * fill_price
        self.daily_buy_count += 1
        self.daily_buy_amount += quantity * fill_price

    def apply_sell(self, request: OrderRequest, *, fill_price: int) -> Optional[Dict[str, object]]:
        position = self.positions.get(request.code)
        if position is None or position.quantity <= 0 or fill_price <= 0:
            return None
        quantity = min(max(int(request.quantity or position.quantity), 1), position.quantity)
        pnl = (fill_price - position.entry_price) * quantity
        self.realized_pnl += pnl
        self.cash += quantity * fill_price
        position.quantity -= quantity
        trade = {
            "code": request.code,
            "name": position.name,
            "quantity": quantity,
            "entry_price": position.entry_price,
            "exit_price": fill_price,
            "profit_rate": fill_price / position.entry_price - 1 if position.entry_price else 0.0,
            "pnl": pnl,
            "reason": request.reason,
            "closed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.closed_trades.append(trade)
        if position.quantity <= 0:
            self.positions.pop(request.code, None)
            self.last_exit_at[request.code] = time.time()
        return trade

    def update_highest(self, code: str, price: int) -> None:
        position = self.positions.get(code)
        if position is not None and price > position.highest_price:
            position.highest_price = price

    def to_risk_state(
        self,
        *,
        pending_orders: Optional[Set[str]] = None,
        pending_order_ids: Optional[Set[str]] = None,
    ) -> RiskState:
        return RiskState(
            mode="paper",
            account_state_available=True,
            daily_loss_available=True,
            daily_buy_count=int(self.daily_buy_count),
            daily_loss=float(min(self.realized_pnl, 0)),
            daily_exposure=int(self.daily_buy_amount),
            account_cash=int(self.cash + self.daily_buy_amount),
            open_positions={code for code, pos in self.positions.items() if pos.quantity > 0},
            pending_orders=set(pending_orders or set()),
            pending_order_ids=set(pending_order_ids or set()),
            last_exit_at=dict(self.last_exit_at),
        )


class OrderGuard:
    def __init__(
        self,
        config: TradeConfig,
        paper_portfolio: Optional[PaperPortfolio] = None,
        time_policy: Optional[TimePolicy] = None,
    ):
        self.config = config
        self.limits = RiskLimits.from_config(config)
        self.paper_portfolio = paper_portfolio
        self.time_policy = time_policy or TimePolicy(config)
        self._sent_at: List[float] = []
        self._live_tokens: Dict[str, LiveOrderToken] = {}

    def _throttle_seconds(self, now: float) -> float:
        window_start = now - 1.0
        self._sent_at = [ts for ts in self._sent_at if ts > window_start]
        if len(self._sent_at) < max(1, int(self.limits.max_orders_per_second)):
            return 0.0
        oldest = min(self._sent_at)
        return max(0.0, oldest + 1.0 - now)

    def record_sent(self, now: Optional[float] = None) -> None:
        self._sent_at.append(time.time() if now is None else float(now))

    def _token_ttl_seconds(self) -> float:
        return max(float(getattr(self.config, "live_order_token_ttl_seconds", 5.0) or 0.0), 0.001)

    @staticmethod
    def _incoming_guard_action(rqname: str, order_type: int) -> str:
        if int(order_type) == 1:
            return "buy"
        if int(order_type) == 2:
            return "sell"
        if int(order_type) == 3:
            return "buy_cancel"
        if int(order_type) == 4:
            return "sell_cancel"
        if "cancel" in str(rqname or "").lower():
            return "cancel"
        return ""

    @staticmethod
    def _incoming_side(order_type: int) -> str:
        if int(order_type) in (1, 3):
            return "buy"
        if int(order_type) in (2, 4):
            return "sell"
        return ""

    def purge_expired_live_tokens(self, now: Optional[float] = None) -> None:
        now_ts = time.time() if now is None else float(now)
        expired = [
            token_id
            for token_id, token in self._live_tokens.items()
            if token.expires_at <= now_ts
        ]
        for token_id in expired:
            self._live_tokens.pop(token_id, None)

    def issue_live_order_token(
        self,
        request: OrderRequest,
        decision: GuardDecision,
        *,
        now: Optional[float] = None,
    ) -> LiveOrderToken:
        now_ts = time.time() if now is None else float(now)
        self.purge_expired_live_tokens(now_ts)
        token = LiveOrderToken(
            token_id=uuid.uuid4().hex,
            guard_decision_id=decision.guard_decision_id,
            request_id=request.request_id,
            symbol=request.code,
            side=request.normalized_side,
            guard_action=request.guard_action,
            rqname=request.rqname,
            order_type=int(request.order_type),
            quantity=int(request.quantity),
            price=int(request.price),
            order_gubun=str(request.order_gubun),
            order_no=str(request.order_no or ""),
            created_at=now_ts,
            expires_at=now_ts + self._token_ttl_seconds(),
        )
        self._live_tokens[token.token_id] = token
        return token

    def consume_live_order_token(
        self,
        token_id: str,
        *,
        rqname: str,
        order_type: int,
        code: str,
        quantity: int,
        price: int,
        order_gubun: str,
        order_no: str = "",
        request_id: str = "",
        now: Optional[float] = None,
    ) -> Tuple[bool, str]:
        now_ts = time.time() if now is None else float(now)
        if not token_id:
            return False, "missing_guard_token"
        token = self._live_tokens.pop(str(token_id), None)
        if token is None:
            return False, "invalid_or_reused_guard_token"
        if token.expires_at <= now_ts:
            return False, "expired_guard_token"
        incoming_action = self._incoming_guard_action(rqname, int(order_type))
        incoming_side = self._incoming_side(int(order_type))
        expected = {
            "request_id": token.request_id,
            "symbol": token.symbol,
            "side": token.side,
            "guard_action": token.guard_action,
            "rqname": token.rqname,
            "order_type": token.order_type,
            "quantity": token.quantity,
            "price": token.price,
            "order_gubun": token.order_gubun,
            "order_no": token.order_no,
        }
        actual = {
            "request_id": str(request_id or ""),
            "symbol": str(code or ""),
            "side": incoming_side,
            "guard_action": incoming_action,
            "rqname": str(rqname or ""),
            "order_type": int(order_type),
            "quantity": int(quantity),
            "price": int(price),
            "order_gubun": str(order_gubun),
            "order_no": str(order_no or ""),
        }
        mismatched = [key for key, value in expected.items() if actual.get(key) != value]
        if mismatched:
            return False, "guard_token_request_mismatch:{}".format(",".join(sorted(mismatched)))
        return True, "guard_token_consumed"

    def _default_risk_state(self) -> RiskState:
        if self.limits.dry_run:
            if self.paper_portfolio is not None:
                return self.paper_portfolio.to_risk_state()
            return RiskState(mode="paper")
        return RiskState(
            mode="live",
            account_state_available=False,
            daily_loss_available=False,
        )

    def _effective_position_limit(self, risk_state: RiskState) -> tuple[int, str]:
        if self.limits.max_position_size > 0:
            return int(self.limits.max_position_size), "absolute_config"
        account_cash = int(risk_state.account_cash or 0)
        if account_cash <= 0:
            return 0, ""
        limit = int(
            account_cash
            * max(float(self.limits.max_position_cash_ratio or 0.0), 0.0)
            * max(float(self.limits.cash_usage_ratio or 0.0), 0.0)
        )
        return max(limit, 0), "dynamic_deposit_ratio" if limit > 0 else ""

    def _effective_daily_exposure_limit(self, risk_state: RiskState) -> tuple[int, str]:
        if self.limits.max_daily_exposure > 0:
            return int(self.limits.max_daily_exposure), "absolute_config"
        account_cash = int(risk_state.account_cash or 0)
        if account_cash <= 0:
            return 0, ""
        limit = int(
            account_cash
            * max(float(self.limits.max_daily_exposure_ratio or 0.0), 0.0)
        )
        return max(limit, 0), "dynamic_deposit_ratio" if limit > 0 else ""

    def _decision(
        self,
        *,
        allowed: bool,
        mode: str,
        reason: str,
        request: OrderRequest,
        risk_state: RiskState,
        requested_amount: int = 0,
        blocked_by: str = "",
        throttle_seconds: float = 0.0,
        is_reentry_blocked: bool = False,
        time_decision: Optional[TimeDecision] = None,
        effective_position_limit: int = 0,
        effective_daily_exposure_limit: int = 0,
        limit_source: str = "",
    ) -> GuardDecision:
        return GuardDecision(
            allowed=allowed,
            live=bool(allowed and mode == "live"),
            paper=bool(mode == "paper" and self.config.paper_portfolio_enabled),
            reason=reason,
            guard_decision_id=uuid.uuid4().hex,
            throttle_seconds=throttle_seconds,
            mode=mode,
            blocked_by=blocked_by or ("" if allowed else reason),
            symbol=request.code,
            requested_amount=int(requested_amount),
            daily_buy_count=int(risk_state.daily_buy_count),
            daily_loss=float(risk_state.daily_loss),
            effective_position_limit=int(effective_position_limit or 0),
            effective_daily_exposure_limit=int(effective_daily_exposure_limit or 0),
            limit_source=str(limit_source or ""),
            is_reentry_blocked=is_reentry_blocked,
            time_decision=time_decision.to_dict() if time_decision is not None else {},
            time_decision_id=(
                getattr(time_decision, "time_decision_id", "")
                if time_decision is not None
                else ""
            ),
        )

    def _log_order_blocked_by_time_policy(
        self,
        request: OrderRequest,
        decision: TimeDecision,
        *,
        mode: str,
        requested_amount: int,
    ) -> None:
        payload = {
            "event": "order_blocked_by_time_policy",
            "symbol": request.code,
            "side": request.normalized_side,
            "rqname": request.rqname,
            "mode": mode,
            "requested_amount": int(requested_amount),
        }
        payload.update(decision.to_dict())
        logger.info(
            "[order_blocked_by_time_policy] %s",
            json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
        )

    def validate(
        self,
        request: OrderRequest,
        *,
        now: Optional[float] = None,
        risk_state: Optional[RiskState] = None,
    ) -> GuardDecision:
        risk_state = risk_state or self._default_risk_state()
        mode = "paper" if self.limits.dry_run else "live"
        risk_state = RiskState(
            mode=mode,
            account_state_available=bool(risk_state.account_state_available),
            daily_loss_available=bool(risk_state.daily_loss_available),
            daily_buy_count=int(risk_state.daily_buy_count),
            daily_loss=float(risk_state.daily_loss),
            daily_exposure=int(risk_state.daily_exposure),
            account_cash=int(risk_state.account_cash),
            open_positions=set(risk_state.open_positions),
            pending_orders=set(risk_state.pending_orders),
            pending_order_ids=set(risk_state.pending_order_ids),
            last_exit_at=dict(risk_state.last_exit_at),
        )

        if not request.code:
            return self._decision(
                allowed=False,
                mode=mode,
                reason="missing_code",
                request=request,
                risk_state=risk_state,
                blocked_by="request_validation",
            )
        if request.normalized_side not in {"buy", "sell"}:
            return self._decision(
                allowed=False,
                mode=mode,
                reason="unknown_side",
                request=request,
                risk_state=risk_state,
                blocked_by="request_validation",
            )
        if not self.limits.trading_enabled:
            return self._decision(
                allowed=False,
                mode=mode,
                reason="trading_disabled",
                request=request,
                risk_state=risk_state,
                blocked_by="kill_switch",
            )
        if mode == "live" and not self.limits.live_trading_enabled:
            return self._decision(
                allowed=False,
                mode=mode,
                reason="live_trading_not_enabled",
                request=request,
                risk_state=risk_state,
                blocked_by="live_confirmation",
            )
        if mode == "live" and (
            not risk_state.account_state_available
            or not risk_state.daily_loss_available
        ):
            return self._decision(
                allowed=False,
                mode=mode,
                reason="missing_live_account_state",
                request=request,
                risk_state=risk_state,
                blocked_by="account_state",
            )

        basis_price = int(request.current_price or request.price or request.entry_price or 0)
        requested_amount = max(basis_price, 0) * max(int(request.quantity or 0), 0)
        effective_position_limit, position_limit_source = self._effective_position_limit(risk_state)
        effective_daily_exposure_limit, daily_exposure_limit_source = (
            self._effective_daily_exposure_limit(risk_state)
        )
        limit_source = (
            "absolute_config"
            if "absolute_config" in {position_limit_source, daily_exposure_limit_source}
            else "dynamic_deposit_ratio"
            if "dynamic_deposit_ratio" in {position_limit_source, daily_exposure_limit_source}
            else ""
        )
        limit_decision_kwargs = {
            "effective_position_limit": effective_position_limit,
            "effective_daily_exposure_limit": effective_daily_exposure_limit,
            "limit_source": limit_source,
        }
        if not request.is_cancel:
            if request.quantity <= 0:
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="non_positive_quantity",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="request_validation",
                    **limit_decision_kwargs,
                )
            if basis_price <= 0 or requested_amount <= 0:
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="non_positive_order_amount",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="request_validation",
                    **limit_decision_kwargs,
                )
            if request.order_gubun != "03" and int(request.price or 0) <= 0:
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="invalid_limit_price",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="price_validation",
                    **limit_decision_kwargs,
                )
            if int(request.current_price or 0) < 0 or int(request.price or 0) < 0:
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="invalid_price",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="price_validation",
                    **limit_decision_kwargs,
                )
            if request.code in risk_state.pending_orders:
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="duplicate_pending_order",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="duplicate_order",
                    **limit_decision_kwargs,
                )
        else:
            if (
                bool(getattr(self.config, "require_cancel_policy_for_cancel", True))
                and request.context.get("cancel_policy_allowed") is not True
            ):
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="missing_cancel_policy_decision",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="cancel_policy",
                )
            if not str(request.order_no or ""):
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="missing_original_order",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="cancel_policy",
                )
            if not risk_state.pending_order_ids:
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="missing_pending_order_state",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="cancel_policy",
                )
            if str(request.order_no) not in risk_state.pending_order_ids:
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="original_order_not_pending",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="cancel_policy",
                )
            if risk_state.pending_orders and request.code not in risk_state.pending_orders:
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="original_symbol_not_pending",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="cancel_policy",
                )

        time_decision: Optional[TimeDecision] = None
        if bool(self.config.time_policy_enabled) and not request.is_cancel:
            time_decision = self.time_policy.evaluate_order(
                side=request.normalized_side,
                now=now,
                log=False,
                context={
                    "symbol": request.code,
                    "side": request.normalized_side,
                    "rqname": request.rqname,
                    "mode": mode,
                },
            )
            if not time_decision.allowed:
                if (
                    mode == "paper"
                    and request.normalized_side == "buy"
                    and is_live_breakout_probe_context(request.context)
                    and self.time_policy.paper_strategy_allowed(now=now)
                ):
                    pass
                else:
                    self._log_order_blocked_by_time_policy(
                        request,
                        time_decision,
                        mode=mode,
                        requested_amount=requested_amount,
                    )
                    return self._decision(
                        allowed=False,
                        mode=mode,
                        reason=time_decision.reason_code.lower(),
                        request=request,
                        risk_state=risk_state,
                        requested_amount=requested_amount,
                        blocked_by="time_policy",
                        time_decision=time_decision,
                    )
            if (
                mode == "live"
                and request.normalized_side == "buy"
                and getattr(time_decision, "action", "") == "ALLOW_MIDDAY_ENTRY"
                and (
                    _context_value(request.context, "entry_type").upper() != "MIDDAY_VWAP_RECLAIM"
                    or _context_value(request.context, "reason_code").upper() != "MIDDAY_VWAP_RECLAIM_LIVE"
                )
            ):
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="midday_entry_strategy_not_allowed",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="time_policy",
                    time_decision=time_decision,
                    **limit_decision_kwargs,
                )

        if request.normalized_side == "buy" and not request.is_cancel:
            if (
                bool(getattr(self.config, "block_new_buys_on_exit_escalation", True))
                and request.context.get("exit_escalation_active") is True
            ):
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="exit_escalation_active",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="exit_escalation",
                    time_decision=time_decision,
                    **limit_decision_kwargs,
                )
            if request.context.get("final_entry_allowed") is not True:
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="missing_final_entry_decision",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="final_entry_decision",
                    time_decision=time_decision,
                    **limit_decision_kwargs,
                )
            if mode == "live" and is_analysis_only_candidate_context(request.context):
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason=LIVE_ANALYSIS_ONLY_REASON_CODE,
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by=LIVE_ANALYSIS_ONLY_BLOCKED_BY,
                    time_decision=time_decision,
                    **limit_decision_kwargs,
                )
            if mode == "live" and is_live_breakout_probe_context(request.context):
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason=LIVE_BREAKOUT_BLOCK_REASON_CODE,
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by=LIVE_BREAKOUT_BLOCKED_BY,
                    time_decision=time_decision,
                    **limit_decision_kwargs,
                )
            if request.code in risk_state.open_positions:
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="position_already_open",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="duplicate_position",
                    time_decision=time_decision,
                    **limit_decision_kwargs,
                )
            if (
                effective_position_limit > 0
                and requested_amount > effective_position_limit
            ):
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="max_position_size_exceeded",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="position_limit",
                    time_decision=time_decision,
                    **limit_decision_kwargs,
                )
            if (
                self.limits.max_daily_buy_count > 0
                and risk_state.daily_buy_count >= self.limits.max_daily_buy_count
            ):
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="daily_buy_limit",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="daily_buy_limit",
                    time_decision=time_decision,
                    **limit_decision_kwargs,
                )
            if (
                self.limits.max_daily_loss > 0
                and float(risk_state.daily_loss) <= -float(self.limits.max_daily_loss)
            ):
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="daily_loss_limit",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="daily_loss_limit",
                    time_decision=time_decision,
                    **limit_decision_kwargs,
                )
            if (
                effective_daily_exposure_limit > 0
                and risk_state.daily_exposure + requested_amount > effective_daily_exposure_limit
            ):
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="daily_exposure_limit",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="daily_exposure_limit",
                    time_decision=time_decision,
                    **limit_decision_kwargs,
                )
            last_exit = float(risk_state.last_exit_at.get(request.code, 0.0) or 0.0)
            if self.limits.reentry_cooldown_seconds > 0 and last_exit > 0:
                elapsed = (time.time() if now is None else float(now)) - last_exit
                if elapsed < self.limits.reentry_cooldown_seconds:
                    return self._decision(
                        allowed=False,
                        mode=mode,
                        reason="reentry_cooldown",
                        request=request,
                        risk_state=risk_state,
                        requested_amount=requested_amount,
                        blocked_by="reentry_cooldown",
                        is_reentry_blocked=True,
                        time_decision=time_decision,
                        **limit_decision_kwargs,
                    )

        if request.normalized_side == "sell" and not request.is_cancel:
            if (
                bool(getattr(self.config, "require_exit_policy_for_sell", True))
                and request.context.get("exit_policy_allowed") is not True
            ):
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="missing_exit_policy_decision",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="exit_policy",
                    time_decision=time_decision,
                )
            if request.code not in risk_state.open_positions:
                return self._decision(
                    allowed=False,
                    mode=mode,
                    reason="missing_sell_position",
                    request=request,
                    risk_state=risk_state,
                    requested_amount=requested_amount,
                    blocked_by="position_state",
                    time_decision=time_decision,
                )

        if mode == "paper":
            reason = "paper_allowed" if self.config.paper_portfolio_enabled else "dry_run_would_order"
            return self._decision(
                allowed=True,
                mode=mode,
                reason=reason,
                request=request,
                risk_state=risk_state,
                requested_amount=requested_amount,
                time_decision=time_decision,
                **limit_decision_kwargs,
            )

        delay = self._throttle_seconds(time.time() if now is None else float(now))
        return self._decision(
            allowed=True,
            mode=mode,
            reason="live_allowed",
            request=request,
            risk_state=risk_state,
            requested_amount=requested_amount,
            throttle_seconds=delay,
            time_decision=time_decision,
            **limit_decision_kwargs,
        )
