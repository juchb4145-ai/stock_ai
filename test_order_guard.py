import time
import unittest
from datetime import datetime

from order_guard import GuardDecision, OrderGuard, OrderRequest, PaperPortfolio, RiskState
from time_policy import load_timezone
from trade_config import TradeConfig


SEOUL = load_timezone("Asia/Seoul")
ALLOWED_TS = datetime(2026, 5, 13, 9, 5, 0, tzinfo=SEOUL).timestamp()
PRE_OPEN_TS = datetime(2026, 5, 13, 8, 59, 0, tzinfo=SEOUL).timestamp()
FORCE_EXIT_TS = datetime(2026, 5, 13, 15, 10, 0, tzinfo=SEOUL).timestamp()


def _buy_request(code="005930", quantity=10, final_entry_allowed=True):
    return OrderRequest(
        rqname="buy",
        screen_no="0001",
        order_type=1,
        code=code,
        quantity=quantity,
        price=10_000,
        order_gubun="00",
        side="buy",
        name="Samsung",
        current_price=10_000,
        entry_price=10_000,
        target_price=10_200,
        stop_price=9_850,
        reason="test buy",
        context={
            "final_entry_allowed": final_entry_allowed,
            "strategy_version": "test",
            "decision_trace": {"test": True},
        },
    )


def _sell_request(code="005930", quantity=10, exit_policy_allowed=True):
    return OrderRequest(
        rqname="sell",
        screen_no="0001",
        order_type=2,
        code=code,
        quantity=quantity,
        price=10_100,
        order_gubun="00",
        side="sell",
        name="Samsung",
        current_price=10_100,
        entry_price=10_000,
        reason="test exit",
        context={
            "exit_policy_allowed": exit_policy_allowed,
            "exit_policy_reason": "target_reached",
        },
    )


def _cancel_request(code="005930", order_no="12345", cancel_policy_allowed=True):
    return OrderRequest(
        rqname="buy_cancel",
        screen_no="0001",
        order_type=3,
        code=code,
        quantity=0,
        price=0,
        order_gubun="00",
        order_no=order_no,
        side="buy",
        name="삼성전자",
        reason="expired",
        context={
            "cancel_policy_allowed": cancel_policy_allowed,
            "cancel_policy_reason": "expired",
            "original_order_no": order_no,
        },
    )


class OrderGuardTests(unittest.TestCase):
    def test_buy_requires_final_entry_decision(self):
        config = TradeConfig(dry_run=True, paper_portfolio_enabled=True)
        guard = OrderGuard(config)

        decision = guard.validate(_buy_request(final_entry_allowed=False), now=ALLOWED_TS)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "missing_final_entry_decision")
        self.assertEqual(decision.blocked_by, "final_entry_decision")

    def test_dry_run_routes_to_paper_without_live_order(self):
        config = TradeConfig(dry_run=True, paper_portfolio_enabled=True)
        paper = PaperPortfolio(initial_cash=1_000_000)
        guard = OrderGuard(config, paper)

        decision = guard.validate(_buy_request(), now=ALLOWED_TS)
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.live)
        self.assertTrue(decision.paper)

        paper.apply_buy(_buy_request(), fill_price=10_000)
        self.assertTrue(paper.has_open_position("005930"))

    def test_paper_blocks_duplicate_position(self):
        config = TradeConfig(dry_run=True, paper_portfolio_enabled=True)
        paper = PaperPortfolio(initial_cash=1_000_000)
        guard = OrderGuard(config, paper)
        paper.apply_buy(_buy_request(), fill_price=10_000)

        decision = guard.validate(_buy_request(), now=ALLOWED_TS)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "position_already_open")

    def test_live_mode_throttles_after_five_orders_in_one_second(self):
        config = TradeConfig(
            dry_run=False,
            live_trading_enabled=True,
            paper_portfolio_enabled=False,
            max_orders_per_second=5,
        )
        guard = OrderGuard(config)
        for offset in range(5):
            guard.record_sent(now=ALLOWED_TS + offset * 0.01)

        decision = guard.validate(
            _buy_request(code="000001"),
            now=ALLOWED_TS + 0.20,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
            ),
        )

        self.assertTrue(decision.allowed)
        self.assertTrue(decision.live)
        self.assertGreater(decision.throttle_seconds, 0)

    def test_blocks_position_size_over_config_limit(self):
        config = TradeConfig(
            dry_run=False,
            live_trading_enabled=True,
            paper_portfolio_enabled=False,
            max_position_size=50_000,
        )
        guard = OrderGuard(config)

        decision = guard.validate(
            _buy_request(quantity=10),
            now=ALLOWED_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
            ),
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "max_position_size_exceeded")

    def test_paper_blocks_reentry_during_cooldown(self):
        config = TradeConfig(
            dry_run=True,
            paper_portfolio_enabled=True,
            reentry_cooldown_seconds=3600,
        )
        paper = PaperPortfolio(initial_cash=1_000_000)
        guard = OrderGuard(config, paper)
        request = _buy_request(quantity=10)
        paper.apply_buy(request, fill_price=10_000)
        paper.apply_sell(
            request.__class__(
                rqname="sell",
                screen_no="0001",
                order_type=2,
                code="005930",
                quantity=10,
                price=10_100,
                order_gubun="03",
                side="sell",
                current_price=10_100,
            ),
            fill_price=10_100,
        )

        decision = guard.validate(_buy_request(), now=ALLOWED_TS)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "reentry_cooldown")

    def test_dry_run_blocks_daily_buy_limit(self):
        config = TradeConfig(dry_run=True, paper_portfolio_enabled=True, max_daily_buy_count=1)
        guard = OrderGuard(config)

        decision = guard.validate(
            _buy_request(),
            now=ALLOWED_TS,
            risk_state=RiskState(mode="paper", daily_buy_count=1),
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "daily_buy_limit")

    def test_live_blocks_daily_buy_limit(self):
        config = TradeConfig(
            dry_run=False,
            live_trading_enabled=True,
            max_daily_buy_count=1,
        )
        guard = OrderGuard(config)

        decision = guard.validate(
            _buy_request(),
            now=ALLOWED_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
                daily_buy_count=1,
            ),
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "daily_buy_limit")

    def test_live_blocks_reentry_cooldown(self):
        config = TradeConfig(
            dry_run=False,
            live_trading_enabled=True,
            reentry_cooldown_seconds=3600,
        )
        guard = OrderGuard(config)

        decision = guard.validate(
            _buy_request(),
            now=1_000.0,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
                last_exit_at={"005930": 900.0},
            ),
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "reentry_cooldown")
        self.assertTrue(decision.is_reentry_blocked)

    def test_live_blocks_daily_loss_limit(self):
        config = TradeConfig(
            dry_run=False,
            live_trading_enabled=True,
            max_daily_loss=100_000,
        )
        guard = OrderGuard(config)

        decision = guard.validate(
            _buy_request(),
            now=ALLOWED_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
                daily_loss=-100_000,
            ),
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "daily_loss_limit")

    def test_live_blocks_missing_account_state(self):
        config = TradeConfig(dry_run=False, live_trading_enabled=True)
        guard = OrderGuard(config)

        decision = guard.validate(_buy_request(), now=ALLOWED_TS)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "missing_live_account_state")

    def test_live_requires_second_confirmation_flag(self):
        config = TradeConfig(dry_run=False, live_trading_enabled=False)
        guard = OrderGuard(config)

        decision = guard.validate(
            _buy_request(),
            now=ALLOWED_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
            ),
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "live_trading_not_enabled")

    def test_live_blocks_duplicate_position_and_pending_order(self):
        config = TradeConfig(dry_run=False, live_trading_enabled=True)
        guard = OrderGuard(config)

        duplicate_position = guard.validate(
            _buy_request(),
            now=ALLOWED_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
                open_positions={"005930"},
            ),
        )
        duplicate_pending = guard.validate(
            _buy_request(),
            now=ALLOWED_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
                pending_orders={"005930"},
            ),
        )

        self.assertFalse(duplicate_position.allowed)
        self.assertEqual(duplicate_position.reason, "position_already_open")
        self.assertFalse(duplicate_pending.allowed)
        self.assertEqual(duplicate_pending.reason, "duplicate_pending_order")

    def test_live_blocks_daily_exposure_limit(self):
        config = TradeConfig(
            dry_run=False,
            live_trading_enabled=True,
            max_daily_exposure=150_000,
        )
        guard = OrderGuard(config)

        decision = guard.validate(
            _buy_request(quantity=10),
            now=ALLOWED_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
                daily_exposure=100_000,
            ),
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "daily_exposure_limit")

    def test_time_policy_blocks_live_buy(self):
        config = TradeConfig(dry_run=False, live_trading_enabled=True)
        guard = OrderGuard(config)

        decision = guard.validate(
            _buy_request(),
            now=PRE_OPEN_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
            ),
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.blocked_by, "time_policy")
        self.assertEqual(decision.reason, "block_pre_open")
        self.assertEqual(decision.time_decision["reason_code"], "BLOCK_PRE_OPEN")

    def test_dry_run_still_logs_time_policy_block(self):
        config = TradeConfig(dry_run=True, paper_portfolio_enabled=True)
        guard = OrderGuard(config)

        with self.assertLogs(level="INFO") as logs:
            decision = guard.validate(_buy_request(), now=PRE_OPEN_TS)

        self.assertFalse(decision.allowed)
        joined = "\n".join(logs.output)
        self.assertIn("order_blocked_by_time_policy", joined)
        self.assertIn("time_decision_id", joined)

    def test_live_token_is_one_time_and_bound_to_request(self):
        config = TradeConfig(
            dry_run=False,
            live_trading_enabled=True,
            time_policy_enabled=False,
        )
        guard = OrderGuard(config)
        request = _buy_request()
        decision = guard.validate(
            request,
            now=ALLOWED_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
            ),
        )
        token = guard.issue_live_order_token(request, decision, now=ALLOWED_TS)

        ok, reason = guard.consume_live_order_token(
            token.token_id,
            rqname=request.rqname,
            order_type=request.order_type,
            code=request.code,
            quantity=request.quantity,
            price=request.price,
            order_gubun=request.order_gubun,
            order_no=request.order_no,
            request_id=request.request_id,
            now=ALLOWED_TS + 1,
        )
        self.assertTrue(ok, reason)

        ok, reason = guard.consume_live_order_token(
            token.token_id,
            rqname=request.rqname,
            order_type=request.order_type,
            code=request.code,
            quantity=request.quantity,
            price=request.price,
            order_gubun=request.order_gubun,
            order_no=request.order_no,
            request_id=request.request_id,
            now=ALLOWED_TS + 2,
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "invalid_or_reused_guard_token")

    def test_live_token_expires(self):
        config = TradeConfig(
            dry_run=False,
            live_trading_enabled=True,
            time_policy_enabled=False,
            live_order_token_ttl_seconds=0.1,
        )
        guard = OrderGuard(config)
        request = _buy_request()
        decision = GuardDecision(True, True, False, "live_allowed")
        token = guard.issue_live_order_token(request, decision, now=ALLOWED_TS)

        ok, reason = guard.consume_live_order_token(
            token.token_id,
            rqname=request.rqname,
            order_type=request.order_type,
            code=request.code,
            quantity=request.quantity,
            price=request.price,
            order_gubun=request.order_gubun,
            request_id=request.request_id,
            now=ALLOWED_TS + 1,
        )

        self.assertFalse(ok)
        self.assertEqual(reason, "expired_guard_token")

    def test_buy_token_cannot_submit_sell_or_cancel(self):
        config = TradeConfig(dry_run=False, live_trading_enabled=True, time_policy_enabled=False)
        guard = OrderGuard(config)
        request = _buy_request()
        decision = GuardDecision(True, True, False, "live_allowed")
        token = guard.issue_live_order_token(request, decision, now=ALLOWED_TS)

        ok, reason = guard.consume_live_order_token(
            token.token_id,
            rqname="sell",
            order_type=2,
            code=request.code,
            quantity=request.quantity,
            price=request.price,
            order_gubun=request.order_gubun,
            request_id=request.request_id,
            now=ALLOWED_TS + 1,
        )

        self.assertFalse(ok)
        self.assertIn("guard_token_request_mismatch", reason)

    def test_sell_requires_exit_policy_and_open_position(self):
        config = TradeConfig(dry_run=False, live_trading_enabled=True, time_policy_enabled=False)
        guard = OrderGuard(config)

        no_exit_policy = guard.validate(
            _sell_request(exit_policy_allowed=False),
            now=ALLOWED_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
                open_positions={"005930"},
            ),
        )
        no_position = guard.validate(
            _sell_request(),
            now=ALLOWED_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
            ),
        )

        self.assertFalse(no_exit_policy.allowed)
        self.assertEqual(no_exit_policy.reason, "missing_exit_policy_decision")
        self.assertFalse(no_position.allowed)
        self.assertEqual(no_position.reason, "missing_sell_position")

    def test_sell_does_not_require_final_entry_decision(self):
        config = TradeConfig(dry_run=False, live_trading_enabled=True, time_policy_enabled=False)
        guard = OrderGuard(config)

        decision = guard.validate(
            _sell_request(),
            now=ALLOWED_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
                open_positions={"005930"},
            ),
        )

        self.assertTrue(decision.allowed)

    def test_exit_escalation_blocks_new_buys(self):
        config = TradeConfig(dry_run=True, paper_portfolio_enabled=True)
        guard = OrderGuard(config)
        request = _buy_request()
        request.context["exit_escalation_active"] = True

        decision = guard.validate(request, now=ALLOWED_TS)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "exit_escalation_active")
        self.assertEqual(decision.blocked_by, "exit_escalation")

    def test_stop_sell_allowed_during_no_buy_force_exit_window(self):
        config = TradeConfig(dry_run=False, live_trading_enabled=True)
        guard = OrderGuard(config)

        buy_decision = guard.validate(
            _buy_request(),
            now=FORCE_EXIT_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
            ),
        )
        sell_decision = guard.validate(
            _sell_request(),
            now=FORCE_EXIT_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
                open_positions={"005930"},
            ),
        )

        self.assertFalse(buy_decision.allowed)
        self.assertEqual(buy_decision.blocked_by, "time_policy")
        self.assertTrue(sell_decision.allowed)
        self.assertEqual(sell_decision.time_decision["reason_code"], "FORCE_EXIT_WINDOW")

    def test_cancel_requires_cancel_policy_and_original_order_state(self):
        config = TradeConfig(dry_run=False, live_trading_enabled=True, time_policy_enabled=False)
        guard = OrderGuard(config)

        no_policy = guard.validate(
            _cancel_request(cancel_policy_allowed=False),
            now=ALLOWED_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
                pending_orders={"005930"},
                pending_order_ids={"12345"},
            ),
        )
        no_order_state = guard.validate(
            _cancel_request(order_no="99999"),
            now=ALLOWED_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
                pending_orders={"005930"},
                pending_order_ids={"12345"},
            ),
        )
        allowed = guard.validate(
            _cancel_request(),
            now=ALLOWED_TS,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
                pending_orders={"005930"},
                pending_order_ids={"12345"},
            ),
        )

        self.assertFalse(no_policy.allowed)
        self.assertEqual(no_policy.reason, "missing_cancel_policy_decision")
        self.assertFalse(no_order_state.allowed)
        self.assertEqual(no_order_state.reason, "original_order_not_pending")
        self.assertTrue(allowed.allowed)


if __name__ == "__main__":
    unittest.main()
