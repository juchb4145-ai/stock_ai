"""리스크 예산 기반 매수 수량 산정 테스트."""

from __future__ import annotations

import sys
import time
import types
import unittest
from unittest import mock


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
import entry_strategy  # noqa: E402
import main  # noqa: E402
from portfolio import PortfolioState, Position  # noqa: E402


class _StubKiwoom:
    parse_int = main.Kiwoom.parse_int
    estimate_position_plan_risk = main.Kiwoom.estimate_position_plan_risk
    current_open_position_risk = main.Kiwoom.current_open_position_risk
    build_position_size_plan = main.Kiwoom.build_position_size_plan
    format_position_size_plan = main.Kiwoom.format_position_size_plan
    place_buy_order = main.Kiwoom.place_buy_order

    def __init__(self, *, deposit: int = 10_000_000) -> None:
        self.deposit = deposit
        self.portfolio = PortfolioState()
        self.order_context = {}
        self.order_prices = {}
        self.entry_times = {}
        self.highest_prices = {}
        self.pending_order_codes = set()
        self.bought_codes = set()
        self.best = {}
        self.target_returns = {}
        self.dante_reentry_watchlist = {}
        self.dante_a_watchlist = {}
        self.guarded_order_calls = []
        self.trade_log_calls = []
        self.saved_best = False
        self.saved_portfolio = False
        self.registered_codes = []

    def normalize_code(self, code):
        return str(code).strip().lstrip("A")

    def get_deposit(self, force=False):
        return self.deposit

    def send_order(self, *args):
        raise AssertionError("place_buy_order must use submit_order_guarded")

    def submit_order_guarded(self, request):
        self.guarded_order_calls.append(
            (
                request.rqname,
                request.screen_no,
                request.order_type,
                request.code,
                request.quantity,
                request.price,
                request.order_gubun,
                request.order_no,
            )
        )
        return 0

    def append_trade_log(self, *args, **kwargs):
        self.trade_log_calls.append((args, kwargs))

    def estimate_net_target_return(self, entry_price, target_price):
        if entry_price <= 0:
            return 0.0
        return target_price / entry_price - 1

    def save_best(self):
        self.saved_best = True

    def save_portfolio_state(self):
        self.saved_portfolio = True

    def register_realtime_stock(self, code):
        self.registered_codes.append(code)


def _position(
    code: str,
    *,
    entry_price: int,
    stop_price: int,
    planned_quantity: int,
    quantity: int = 0,
    entry_stage: int = 2,
    pending_buy: bool = False,
) -> Position:
    pos = Position(
        code=code,
        entry_price=entry_price,
        stop_price=stop_price,
        planned_quantity=planned_quantity,
        quantity=quantity,
        entry_stage=entry_stage,
        pending_buy=pending_buy,
    )
    pos.entry_time = time.time()
    return pos


def _prediction(**overrides):
    payload = {
        "code": "000001",
        "name": "테스트",
        "current_price": 10_000,
        "entry_limit_price": 10_000,
        "stop_price": 9_850,
        "take_profit_price": 10_300,
        "ratio": 1.0,
        "grade": "B",
        "reason_code": entry_strategy.READY_BGRADE_PULLBACK,
        "reason": "테스트 진입",
        "final_entry_allowed": True,
        "final_reason": "test final pass",
        "final_reason_code": "FINAL_BUY_READY",
        "strategy_version": "test",
        "legacy_filter_enabled": True,
        "decision_trace": {"test": True},
    }
    payload.update(overrides)
    return payload


class PositionSizePlanTests(unittest.TestCase):
    def test_caps_quantity_by_per_trade_risk(self):
        kw = _StubKiwoom(deposit=10_000_000)
        plan = kw.build_position_size_plan(
            code="000001",
            deposit=10_000_000,
            entry_limit_price=10_000,
            stop_price=9_850,
        )
        self.assertEqual(plan["risk_per_share"], 150)
        self.assertEqual(plan["risk_budget"], 50_000)
        self.assertEqual(plan["risk_quantity"], 333)
        self.assertEqual(plan["planned_quantity"], 333)
        self.assertEqual(plan["reason"], "risk_capped")

    def test_uses_remaining_portfolio_risk_budget(self):
        kw = _StubKiwoom(deposit=10_000_000)
        kw.portfolio.get_or_create("111111").__dict__.update(
            _position(
                "111111",
                entry_price=10_000,
                stop_price=9_810,
                planned_quantity=1_000,
                entry_stage=1,
            ).__dict__
        )
        plan = kw.build_position_size_plan(
            code="000001",
            deposit=10_000_000,
            entry_limit_price=10_000,
            stop_price=9_900,
        )
        self.assertEqual(plan["portfolio_risk_budget"], 200_000)
        self.assertEqual(plan["used_portfolio_risk"], 190_000)
        self.assertEqual(plan["remaining_portfolio_risk"], 10_000)
        self.assertEqual(plan["planned_quantity"], 100)

    def test_rejects_when_order_cash_is_below_minimum(self):
        kw = _StubKiwoom(deposit=100_000)
        plan = kw.build_position_size_plan(
            code="000001",
            deposit=100_000,
            entry_limit_price=5_000,
            stop_price=4_900,
        )
        self.assertEqual(plan["planned_quantity"], 0)
        self.assertEqual(plan["reason"], "below_min_order_cash")


class PlaceBuyOrderSizingTests(unittest.TestCase):
    def test_lump_sum_entry_uses_risk_based_planned_quantity(self):
        kw = _StubKiwoom(deposit=10_000_000)
        kw.place_buy_order("A000001", _prediction(), ratio=1.0, stage=2)

        self.assertEqual(len(kw.guarded_order_calls), 1)
        args = kw.guarded_order_calls[0]
        self.assertEqual(args[0], "buy")
        self.assertEqual(args[3], "000001")
        self.assertEqual(args[4], 333)
        self.assertEqual(args[5], 10_000)

        ctx = kw.order_context["000001"]
        self.assertEqual(ctx["planned_quantity"], 333)
        self.assertEqual(ctx["position_sizing"], "risk_capped")
        self.assertEqual(ctx["risk_per_share"], 150)

    def test_skips_when_portfolio_risk_budget_is_exhausted(self):
        kw = _StubKiwoom(deposit=10_000_000)
        kw.portfolio.get_or_create("111111").__dict__.update(
            _position(
                "111111",
                entry_price=10_000,
                stop_price=9_800,
                planned_quantity=1_000,
                entry_stage=1,
            ).__dict__
        )

        kw.place_buy_order("A000001", _prediction(), ratio=1.0, stage=2)

        self.assertEqual(kw.guarded_order_calls, [])
        self.assertEqual(len(kw.trade_log_calls), 1)
        self.assertEqual(kw.trade_log_calls[0][1]["reason"], "리스크 예산 부족")


if __name__ == "__main__":
    unittest.main()
