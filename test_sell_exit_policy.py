from __future__ import annotations

import time
import sys
import types
import unittest
from unittest import mock

import exit_strategy as xs
from order_guard import GuardDecision
from portfolio import PortfolioState


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
        core.QEventLoop = mock.MagicMock
        core.QObject = mock.MagicMock
        core.pyqtSignal = mock.MagicMock()
        core.__all__ = ["QTimer", "QEventLoop", "QObject", "pyqtSignal"]

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


class _SellStub:
    normalize_code = main.Kiwoom.normalize_code
    parse_int = main.Kiwoom.parse_int
    _exit_log_fields = main.Kiwoom._exit_log_fields
    _mark_exit_escalation = main.Kiwoom._mark_exit_escalation
    queue_sell_intent = main.Kiwoom.queue_sell_intent
    process_pending_sell_intents = main.Kiwoom.process_pending_sell_intents
    check_sell_unfilled_timeouts = main.Kiwoom.check_sell_unfilled_timeouts
    check_sell_signal = main.Kiwoom.check_sell_signal
    place_sell_order = main.Kiwoom.place_sell_order
    _do_place_sell_order = main.Kiwoom._do_place_sell_order

    def __init__(self, *, submit_result=0):
        self.submit_result = submit_result
        self.submitted_requests = []
        self.trade_logs = []
        self.portfolio = PortfolioState()
        pos = self.portfolio.get_or_create("005930", name="Samsung")
        pos.quantity = 10
        pos.available_quantity = 10
        pos.entry_price = 10_000
        pos.stop_price = 9_850
        pos.target_price = 10_200
        pos.entry_time = time.time() - 60
        self.position_quantities = {"005930": 10}
        self.available_quantities = {"005930": 10}
        self.cached_balance = []
        self.holding_codes = {"005930"}
        self.best = {"005930": 10_200}
        self.order_prices = {"005930": 10_000}
        self.realtime_ticks = {"005930": [{"close": 9_850, "chejan_strength": 80}]}
        self.pending_order_codes = set()
        self.pending_sell_order_codes = set()
        self.pending_sell_intents = {}
        self._selling_codes = set()
        self.order_context = {}
        self.last_sell_skip_log_at = {}
        self.entry_times = {"005930": time.time() - 60}
        self.exit_escalation_active = False
        self.exit_escalated_codes = set()
        self.last_order_guard_decision = None

    def get_code_name(self, code):
        return "Samsung"

    def _lookup_balance_quantity(self, code):
        return (
            self.position_quantities.get(code, 0),
            self.available_quantities.get(code, 0),
        )

    def update_account_status(self, force=False):
        return None

    def should_log_sell_skip(self, code):
        return True

    def gross_to_net_return(self, value):
        return value

    def append_trade_log(self, event, **kwargs):
        self.trade_logs.append((event, kwargs))

    def save_portfolio_state(self):
        return None

    def submit_order_guarded(self, request):
        self.submitted_requests.append(request)
        self.last_order_guard_decision = GuardDecision(
            True,
            False,
            True,
            "paper_allowed",
            symbol=request.code,
            mode="paper",
        )
        return self.submit_result

    def score_exit_timing(self, code, current_price):
        return {
            "action": xs.ACTION_STOP_LOSS,
            "qty_ratio": 1.0,
            "reason": "fixed hard stop",
            "exit_type": xs.EXIT_TYPE_HARD_STOP,
            "exit_reason_code": xs.REASON_HARD_STOP_FIXED_PCT,
            "stop_reason": xs.REASON_HARD_STOP_FIXED_PCT,
            "exit_policy_source": "test",
            "exit_decision_trace": {"matched_rule": xs.REASON_HARD_STOP_FIXED_PCT},
        }


class SellExitPolicyTests(unittest.TestCase):
    def test_check_sell_signal_creates_guarded_sell_request(self):
        stub = _SellStub()

        stub.check_sell_signal("005930", 9_850)

        self.assertEqual(len(stub.submitted_requests), 1)
        request = stub.submitted_requests[0]
        self.assertEqual(request.normalized_side, "sell")
        self.assertTrue(request.context["exit_policy_allowed"])
        self.assertNotIn("final_entry_allowed", request.context)
        self.assertEqual(request.context["exit_reason_code"], xs.REASON_HARD_STOP_FIXED_PCT)
        self.assertEqual(stub.trade_logs[-1][1]["exit_reason_code"], xs.REASON_HARD_STOP_FIXED_PCT)

    def test_sell_failure_queues_retry_with_exit_fields(self):
        stub = _SellStub(submit_result=-1)

        stub.place_sell_order(
            "005930",
            0,
            "03",
            "fixed hard stop",
            exit_meta={
                "exit_type": xs.EXIT_TYPE_HARD_STOP,
                "exit_reason_code": xs.REASON_HARD_STOP_FIXED_PCT,
            },
        )

        intent = stub.pending_sell_intents["005930"]
        self.assertEqual(intent["sell_retry_count"], 1)
        self.assertEqual(intent["sell_order_result"], "sell_order_failed")
        self.assertEqual(intent["exit_reason_code"], xs.REASON_HARD_STOP_FIXED_PCT)

    def test_second_retry_escalates_and_blocks_new_buys(self):
        stub = _SellStub(submit_result=-1)
        stub.pending_sell_intents["005930"] = {
            "reason": "fixed hard stop",
            "order_price": 0,
            "order_gubun": "03",
            "queued_at": time.time() - 10,
            "last_try_at": 0,
            "sell_retry_count": 1,
            "exit_type": xs.EXIT_TYPE_HARD_STOP,
            "exit_reason_code": xs.REASON_HARD_STOP_FIXED_PCT,
        }

        stub.process_pending_sell_intents()

        self.assertTrue(stub.exit_escalation_active)
        self.assertIn("005930", stub.exit_escalated_codes)
        self.assertTrue(any(event == "sell_order_escalation" for event, _ in stub.trade_logs))

    def test_unfilled_sell_timeout_escalates(self):
        stub = _SellStub()
        stub.pending_sell_order_codes.add("005930")
        stub.order_context["005930"] = {
            "submitted_at": time.time() - 20,
            "quantity": 10,
            "exit_type": xs.EXIT_TYPE_HARD_STOP,
            "exit_reason_code": xs.REASON_HARD_STOP_FIXED_PCT,
        }

        stub.check_sell_unfilled_timeouts()

        self.assertTrue(stub.exit_escalation_active)
        self.assertEqual(stub.order_context["005930"]["sell_order_result"], "sell_order_unfilled_timeout")


if __name__ == "__main__":
    unittest.main()
