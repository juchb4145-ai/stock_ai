from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest import mock

from final_entry_decision import FINAL_REASON_PAPER_ONLY_BREAKOUT_PROBE
from order_guard import (
    LIVE_ANALYSIS_ONLY_BLOCKED_BY,
    LIVE_ANALYSIS_ONLY_REASON_CODE,
    LIVE_BREAKOUT_BLOCKED_BY,
    LIVE_BREAKOUT_BLOCK_REASON_CODE,
    OrderGuard,
    OrderRequest,
    PaperPortfolio,
    RiskState,
)
from time_policy import TimeDecision
from trade_config import TradeConfig


def _ensure_external_stubs() -> None:
    if "PyQt5" not in sys.modules:
        qax = types.ModuleType("PyQt5.QAxContainer")
        qax.QAxWidget = mock.MagicMock
        qax.__all__ = ["QAxWidget"]

        widgets = types.ModuleType("PyQt5.QtWidgets")
        widgets.QApplication = mock.MagicMock
        widgets.QWidget = mock.MagicMock
        widgets.__all__ = ["QApplication", "QWidget"]

        core = types.ModuleType("PyQt5.QtCore")
        core.QTimer = mock.MagicMock
        core.QObject = mock.MagicMock
        core.pyqtSignal = mock.MagicMock()
        core.__all__ = ["QTimer", "QObject", "pyqtSignal"]

        pyqt5 = types.ModuleType("PyQt5")
        pyqt5.QAxContainer = qax
        pyqt5.QtWidgets = widgets
        pyqt5.QtCore = core

        sys.modules["PyQt5"] = pyqt5
        sys.modules["PyQt5.QAxContainer"] = qax
        sys.modules["PyQt5.QtWidgets"] = widgets
        sys.modules["PyQt5.QtCore"] = core

    if "pandas" not in sys.modules:
        sys.modules["pandas"] = mock.MagicMock()


_ensure_external_stubs()
import main  # noqa: E402


def _buy_request(**overrides):
    payload = {
        "rqname": "buy",
        "screen_no": "0001",
        "order_type": 1,
        "code": "005930",
        "quantity": 1,
        "price": 10_000,
        "order_gubun": "00",
        "side": "buy",
        "name": "Samsung",
        "reason": "test buy",
        "current_price": 10_000,
        "entry_price": 10_000,
        "context": {
            "final_entry_allowed": True,
            "strategy_version": "test",
            "decision_trace": {"test": True},
        },
    }
    payload.update(overrides)
    return OrderRequest(**payload)


class OrderSafetyTests(unittest.TestCase):
    def test_main_risk_defaults_are_loaded_from_trade_config(self):
        self.assertEqual(main.BUY_CASH_BUFFER_RATE, main.TRADE_CONFIG.cash_usage_ratio)
        self.assertEqual(main.SAFE_PULLBACK_CASH_RATE, main.TRADE_CONFIG.max_position_cash_ratio)
        self.assertEqual(main.SAFE_PULLBACK_STOP_LOSS_PCT, main.TRADE_CONFIG.default_stop_loss_pct)
        self.assertEqual(main.SAFE_PULLBACK_TAKE_PROFIT_PCT, main.TRADE_CONFIG.default_take_profit_pct)

    def test_direct_send_order_is_blocked_before_dynamic_call(self):
        class Stub:
            _order_guard_live_call = False
            account_updated_at = 0
            deposit_updated_at = 0
            dynamic_call_count = 0

            def wait_for_order_slot(self):
                raise AssertionError("wait_for_order_slot must not be called")

            def dynamicCall(self, *args):
                self.dynamic_call_count += 1
                raise AssertionError("SendOrder dynamicCall must not be called")

        stub = Stub()

        result = main.Kiwoom.send_order(
            stub,
            "buy",
            "0001",
            1,
            "005930",
            1,
            10_000,
            "00",
        )

        self.assertEqual(result, -9901)
        self.assertEqual(stub.dynamic_call_count, 0)

    def test_direct_send_order_requires_matching_guard_request(self):
        class Stub:
            _order_guard_live_call = "guard-token"
            _order_guard_live_request = ("buy", "005930", 1, 2, 10_000, "00")
            account_updated_at = 0
            deposit_updated_at = 0
            dynamic_call_count = 0

            def wait_for_order_slot(self):
                raise AssertionError("wait_for_order_slot must not be called")

            def dynamicCall(self, *args):
                self.dynamic_call_count += 1
                raise AssertionError("SendOrder dynamicCall must not be called")

        stub = Stub()

        result = main.Kiwoom.send_order(
            stub,
            "buy",
            "0001",
            1,
            "005930",
            1,
            10_000,
            "00",
        )

        self.assertEqual(result, -9901)
        self.assertEqual(stub.dynamic_call_count, 0)

    def test_send_order_consumes_one_time_guard_token_before_dynamic_call(self):
        request = _buy_request()
        guard = OrderGuard(
            TradeConfig(
                dry_run=False,
                live_trading_enabled=True,
                paper_portfolio_enabled=False,
                time_policy_enabled=False,
            )
        )
        decision = guard.validate(
            request,
            risk_state=RiskState(
                mode="live",
                account_state_available=True,
                daily_loss_available=True,
            ),
        )
        token = guard.issue_live_order_token(request, decision)

        class Stub:
            order_guard = guard
            account_number = "12345678"
            account_updated_at = 0
            deposit_updated_at = 0
            dynamic_call_count = 0

            def wait_for_order_slot(self):
                return None

            def dynamicCall(self, *args):
                self.dynamic_call_count += 1
                return 0

        stub = Stub()

        result = main.Kiwoom.send_order(
            stub,
            request.rqname,
            request.screen_no,
            request.order_type,
            request.code,
            request.quantity,
            request.price,
            request.order_gubun,
            request.order_no,
            guard_token=token.token_id,
            request_id=request.request_id,
        )
        reused = main.Kiwoom.send_order(
            stub,
            request.rqname,
            request.screen_no,
            request.order_type,
            request.code,
            request.quantity,
            request.price,
            request.order_gubun,
            request.order_no,
            guard_token=token.token_id,
            request_id=request.request_id,
        )

        self.assertEqual(result, 0)
        self.assertEqual(reused, -9901)
        self.assertEqual(stub.dynamic_call_count, 1)

    def test_submit_order_guarded_without_guard_fails_closed(self):
        class Stub:
            last_order_guard_decision = None

            def send_order(self, *args, **kwargs):
                raise AssertionError("send_order must not be called without OrderGuard")

        request = OrderRequest(
            rqname="buy",
            screen_no="0001",
            order_type=1,
            code="005930",
            quantity=1,
            price=10_000,
            order_gubun="00",
            side="buy",
            current_price=10_000,
        )

        result = main.Kiwoom.submit_order_guarded(Stub(), request)

        self.assertEqual(result, -9904)

    def test_dry_run_would_order_does_not_call_send_order(self):
        request = _buy_request()

        class Stub:
            order_guard = OrderGuard(
                TradeConfig(
                    dry_run=True,
                    paper_portfolio_enabled=False,
                    time_policy_enabled=False,
                )
            )
            last_order_guard_decision = None

            def build_order_risk_state(self, request):
                return RiskState(mode="paper")

            def parse_int(self, value):
                return int(value or 0)

            def send_order(self, *args, **kwargs):
                raise AssertionError("dry-run must not call send_order")

        result = main.Kiwoom.submit_order_guarded(Stub(), request)

        self.assertEqual(result, 0)

    def test_final_allowed_dry_run_applies_paper_fill_without_send_order(self):
        request = _buy_request()
        paper = PaperPortfolio(initial_cash=1_000_000)

        class Stub:
            paper_portfolio = paper
            order_guard = OrderGuard(
                TradeConfig(
                    dry_run=True,
                    paper_portfolio_enabled=True,
                    time_policy_enabled=False,
                ),
                paper,
            )
            last_order_guard_decision = None

            def build_order_risk_state(self, request):
                return paper.to_risk_state()

            def parse_int(self, value):
                return int(value or 0)

            def send_order(self, *args, **kwargs):
                raise AssertionError("dry-run paper fill must not call send_order")

        result = main.Kiwoom.submit_order_guarded(Stub(), request)

        self.assertEqual(result, 0)
        self.assertTrue(paper.has_open_position("005930"))

    def test_live_guard_reject_does_not_call_send_order(self):
        request = _buy_request()

        class Stub:
            order_guard = OrderGuard(
                TradeConfig(
                    dry_run=False,
                    live_trading_enabled=True,
                    max_daily_buy_count=1,
                    time_policy_enabled=False,
                )
            )
            last_order_guard_decision = None

            def build_order_risk_state(self, request):
                return RiskState(
                    mode="live",
                    account_state_available=True,
                    daily_loss_available=True,
                    daily_buy_count=1,
                )

            def send_order(self, *args, **kwargs):
                raise AssertionError("rejected live order must not call send_order")

        stub = Stub()
        result = main.Kiwoom.submit_order_guarded(stub, request)

        self.assertEqual(result, -9902)
        self.assertFalse(stub.last_order_guard_decision.allowed)

    def test_live_breakout_small_reject_does_not_call_send_order(self):
        request = _buy_request(
            context={
                "final_entry_allowed": True,
                "strategy_version": "test",
                "decision_trace": {"paper_only_breakout_probe": True},
                "reason_code": "BUY_BREAKOUT_SMALL",
                "momentum_reason_code": "BUY_BREAKOUT_SMALL",
                "final_reason_code": FINAL_REASON_PAPER_ONLY_BREAKOUT_PROBE,
                "entry_type": "BREAKOUT_SMALL",
            }
        )

        class Stub:
            order_guard = OrderGuard(
                TradeConfig(
                    dry_run=False,
                    live_trading_enabled=True,
                    paper_portfolio_enabled=False,
                    time_policy_enabled=False,
                )
            )
            last_order_guard_decision = None
            send_order_calls = 0

            def build_order_risk_state(self, request):
                return RiskState(
                    mode="live",
                    account_state_available=True,
                    daily_loss_available=True,
                )

            def send_order(self, *args, **kwargs):
                self.send_order_calls += 1
                raise AssertionError("live breakout probe must not call send_order")

        stub = Stub()
        result = main.Kiwoom.submit_order_guarded(stub, request)

        self.assertEqual(result, -9902)
        self.assertEqual(stub.send_order_calls, 0)
        self.assertFalse(stub.last_order_guard_decision.allowed)
        self.assertEqual(stub.last_order_guard_decision.reason, LIVE_BREAKOUT_BLOCK_REASON_CODE)
        self.assertEqual(stub.last_order_guard_decision.blocked_by, LIVE_BREAKOUT_BLOCKED_BY)

    def test_dante_only_live_reject_does_not_call_send_order(self):
        request = _buy_request(
            context={
                "final_entry_allowed": True,
                "strategy_version": "test",
                "decision_trace": {"test": True},
                "reason_code": "BUY_PULLBACK_RECLAIM",
                "momentum_reason_code": "BUY_PULLBACK_RECLAIM",
                "entry_type": "PULLBACK_RECLAIM",
                "condition_combo": "DANTE_ONLY",
                "candidate_role": "analysis_only",
            }
        )

        class Stub:
            order_guard = OrderGuard(
                TradeConfig(
                    dry_run=False,
                    live_trading_enabled=True,
                    paper_portfolio_enabled=False,
                    time_policy_enabled=False,
                )
            )
            last_order_guard_decision = None
            send_order_calls = 0

            def build_order_risk_state(self, request):
                return RiskState(
                    mode="live",
                    account_state_available=True,
                    daily_loss_available=True,
                )

            def send_order(self, *args, **kwargs):
                self.send_order_calls += 1
                raise AssertionError("DANTE_ONLY analysis candidate must not call send_order")

        stub = Stub()
        result = main.Kiwoom.submit_order_guarded(stub, request)

        self.assertEqual(result, -9902)
        self.assertEqual(stub.send_order_calls, 0)
        self.assertFalse(stub.last_order_guard_decision.allowed)
        self.assertEqual(stub.last_order_guard_decision.reason, LIVE_ANALYSIS_ONLY_REASON_CODE)
        self.assertEqual(stub.last_order_guard_decision.blocked_by, LIVE_ANALYSIS_ONLY_BLOCKED_BY)

    def test_dry_run_breakout_probe_stays_paper_even_with_live_flag(self):
        request = _buy_request(
            context={
                "final_entry_allowed": True,
                "strategy_version": "test",
                "decision_trace": {"paper_only_breakout_probe": True},
                "reason_code": FINAL_REASON_PAPER_ONLY_BREAKOUT_PROBE,
                "momentum_reason_code": "BUY_BREAKOUT_SMALL",
                "entry_type": "BREAKOUT_SMALL",
            }
        )
        paper = PaperPortfolio(initial_cash=1_000_000)

        class Stub:
            order_guard = OrderGuard(
                TradeConfig(
                    dry_run=True,
                    live_trading_enabled=True,
                    paper_portfolio_enabled=True,
                    time_policy_enabled=False,
                ),
                paper,
            )
            paper_portfolio = paper
            last_order_guard_decision = None
            send_order_calls = 0

            def build_order_risk_state(self, request):
                return paper.to_risk_state()

            def parse_int(self, value):
                return int(value or 0)

            def send_order(self, *args, **kwargs):
                self.send_order_calls += 1
                raise AssertionError("dry_run breakout probe must not call live send_order")

        stub = Stub()
        result = main.Kiwoom.submit_order_guarded(stub, request)

        self.assertEqual(result, 0)
        self.assertEqual(stub.send_order_calls, 0)
        self.assertTrue(stub.last_order_guard_decision.allowed)
        self.assertFalse(stub.last_order_guard_decision.live)
        self.assertTrue(stub.last_order_guard_decision.paper)

    def test_live_time_policy_reject_does_not_call_send_order(self):
        request = _buy_request(
            context={
                "final_entry_allowed": True,
                "strategy_version": "test",
                "decision_trace": {"momentum": "BUY"},
                "entry_decision": "BUY",
            }
        )

        class BlockingTimePolicy:
            def evaluate_order(self, *, side, now=None, log=False, context=None):
                return TimeDecision(
                    allowed=False,
                    action="BLOCK_PRE_OPEN",
                    reason_code="BLOCK_PRE_OPEN",
                    current_time="2026-05-13T08:59:00+09:00",
                    session="pre_open",
                    next_allowed_time="2026-05-13T09:03:00+09:00",
                    config_version="test",
                )

        class Stub:
            order_guard = OrderGuard(
                TradeConfig(
                    dry_run=False,
                    live_trading_enabled=True,
                    paper_portfolio_enabled=False,
                    max_position_size=1_000_000,
                    max_daily_exposure=10_000_000,
                ),
                time_policy=BlockingTimePolicy(),
            )
            last_order_guard_decision = None

            def build_order_risk_state(self, request):
                return RiskState(
                    mode="live",
                    account_state_available=True,
                    daily_loss_available=True,
                )

            def send_order(self, *args, **kwargs):
                raise AssertionError("time policy block must not call live send_order")

            def log_entry_decision_trace(self, request, decision, risk_state):
                return None

        stub = Stub()
        result = main.Kiwoom.submit_order_guarded(stub, request)

        self.assertEqual(result, -9902)
        self.assertFalse(stub.last_order_guard_decision.allowed)
        self.assertEqual(stub.last_order_guard_decision.blocked_by, "time_policy")

    def test_live_allowed_logs_preflight_before_send_order(self):
        request = _buy_request(
            context={
                "final_entry_allowed": True,
                "strategy_version": "test",
                "decision_trace": {"test": True},
                "entry_decision": "BUY",
                "chase_risk_score": 12.5,
                "momentum_metrics": {"age_seconds": 90, "chase_risk_score": 12.5},
            }
        )
        events = []

        class Stub:
            order_guard = OrderGuard(
                TradeConfig(
                    dry_run=False,
                    live_trading_enabled=True,
                    paper_portfolio_enabled=False,
                    max_position_size=1_000_000,
                    max_daily_exposure=10_000_000,
                    time_policy_enabled=False,
                )
            )
            last_order_guard_decision = None

            def build_order_risk_state(self, request):
                return RiskState(
                    mode="live",
                    account_state_available=True,
                    daily_loss_available=True,
                )

            def log_pre_live_order_submit(self, request, decision, risk_state, **kwargs):
                events.append(("pre_live_order_submit", kwargs.get("guard_token_id", "")))

            def send_order(
                self,
                rqname,
                screen_no,
                order_type,
                code,
                qty,
                price,
                order_gubun,
                order_no="",
                *,
                guard_token="",
                request_id="",
            ):
                events.append(("send_order", guard_token))
                ok, reason = self.order_guard.consume_live_order_token(
                    guard_token,
                    rqname=rqname,
                    order_type=order_type,
                    code=code,
                    quantity=qty,
                    price=price,
                    order_gubun=order_gubun,
                    order_no=order_no,
                    request_id=request_id,
                )
                if not ok:
                    raise AssertionError("live send_order did not receive a valid guard token: {}".format(reason))
                return 0

        stub = Stub()
        result = main.Kiwoom.submit_order_guarded(stub, request)

        self.assertEqual(result, 0)
        self.assertEqual([event[0] for event in events], ["pre_live_order_submit", "send_order"])
        self.assertTrue(events[0][1])
        self.assertEqual(events[0][1], events[1][1])

    def test_main_has_no_direct_send_order_call_outside_guarded_submit(self):
        import ast

        tree = ast.parse(Path(__file__).with_name("main.py").read_text(encoding="utf-8"))
        offenders = []
        parents = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (
                isinstance(func, ast.Attribute)
                and func.attr == "send_order"
                and isinstance(func.value, ast.Name)
                and func.value.id == "self"
            ):
                continue
            cursor = node
            function_name = ""
            while cursor in parents:
                cursor = parents[cursor]
                if isinstance(cursor, ast.FunctionDef):
                    function_name = cursor.name
                    break
            if function_name != "submit_order_guarded":
                offenders.append((function_name, node.lineno))

        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
