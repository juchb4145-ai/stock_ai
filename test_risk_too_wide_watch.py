"""손절폭 과대 후보 재감시 테스트."""

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
from portfolio import PortfolioState  # noqa: E402


def _prediction(**overrides):
    payload = {
        "status": "ready",
        "stage": 2,
        "ratio": 1.0,
        "code": "000001",
        "name": "테스트",
        "current_price": 10_000,
        "grade": "B",
        "reason_code": entry_strategy.READY_BGRADE_PULLBACK,
        "model_name": "DanteLightGBM",
        "model_score": 0.75,
        "model_action": "shadow_allow",
        "model_target": "reached_1r",
        "model_threshold": 0.58,
        "market_gate_action": entry_strategy.MARKET_ACTION_ALLOW,
    }
    payload.update(overrides)
    return payload


def _plan(**overrides):
    payload = {
        "entry_limit_price": 10_000,
        "stop_price": 9_700,
        "take_profit_price": 10_600,
        "model_name": "DanteLightGBM",
        "model_score": 0.75,
        "model_action": "shadow_allow",
        "model_target": "reached_1r",
        "model_threshold": 0.58,
    }
    payload.update(overrides)
    return payload


class _WatchStub:
    parse_int = main.Kiwoom.parse_int
    parse_float = main.Kiwoom.parse_float
    is_risk_too_wide_plan_rejection = main.Kiwoom.is_risk_too_wide_plan_rejection
    _plan_risk_pct = main.Kiwoom._plan_risk_pct
    cleanup_risk_too_wide_watchlist = main.Kiwoom.cleanup_risk_too_wide_watchlist
    qualifies_risk_too_wide_watch = main.Kiwoom.qualifies_risk_too_wide_watch
    start_risk_too_wide_watch = main.Kiwoom.start_risk_too_wide_watch
    should_continue_risk_too_wide_watch = main.Kiwoom.should_continue_risk_too_wide_watch
    validate_entry_plan = main.Kiwoom.validate_entry_plan
    handle_condition_stock = main.Kiwoom.handle_condition_stock

    def __init__(self) -> None:
        self.risk_too_wide_watchlist = {}
        self.pending_condition_codes = []
        self.no_tick_codes = set()
        self.realtime_registered_codes = {"000001"}
        self.portfolio = PortfolioState()
        self.prediction = _prediction()
        self.plan = _plan(stop_price=9_850, take_profit_price=10_300)
        self.placed_orders = []
        self.trade_logs = []

    def normalize_code(self, code):
        return str(code).strip().lstrip("A")

    def requeue_condition_stock(self, code):
        code = self.normalize_code(code)
        if code not in self.pending_condition_codes:
            self.pending_condition_codes.append(code)

    def current_hhmmss(self):
        return 100000

    def register_realtime_stock(self, code):
        self.realtime_registered_codes.add(self.normalize_code(code))

    def predict_stock(self, code):
        return dict(self.prediction)

    def update_account_status(self):
        return None

    def should_skip_buy(self, code, *, stage=1, grade=""):
        return False

    def request_dante_entry_plan(self, code, prediction):
        return dict(self.plan)

    def place_buy_order(self, code, prediction, *, ratio, stage):
        self.placed_orders.append((self.normalize_code(code), dict(prediction), ratio, stage))

    def append_trade_log(self, *args, **kwargs):
        self.trade_logs.append((args, kwargs))


class RiskTooWideWatchTests(unittest.TestCase):
    def test_registers_high_score_risk_too_wide_candidate(self):
        kw = _WatchStub()
        ok = kw.start_risk_too_wide_watch(
            "A000001",
            _prediction(model_score=0.76, reason_code=entry_strategy.GATE_NO_BREAKOUT),
            _plan(),
            "손절폭 과대 3.00%",
        )

        self.assertTrue(ok)
        self.assertIn("000001", kw.risk_too_wide_watchlist)
        self.assertIn("000001", kw.pending_condition_codes)
        self.assertAlmostEqual(kw.risk_too_wide_watchlist["000001"]["risk_pct"], 0.03)

    def test_does_not_register_low_score_non_ready_candidate(self):
        kw = _WatchStub()
        ok = kw.start_risk_too_wide_watch(
            "A000001",
            _prediction(model_score=0.55, reason_code=entry_strategy.GATE_NO_BREAKOUT),
            _plan(model_score=0.55),
            "손절폭 과대 3.00%",
        )

        self.assertFalse(ok)
        self.assertNotIn("000001", kw.risk_too_wide_watchlist)

    def test_defers_recheck_until_interval(self):
        kw = _WatchStub()
        now = time.time()
        kw.risk_too_wide_watchlist["000001"] = {
            "deadline": now + 600,
            "last_recheck_at": now,
            "best_risk_pct": 0.03,
        }

        self.assertFalse(kw.should_continue_risk_too_wide_watch("000001"))
        self.assertIn("000001", kw.pending_condition_codes)

    def test_expired_watch_is_removed(self):
        kw = _WatchStub()
        kw.risk_too_wide_watchlist["000001"] = {
            "deadline": time.time() - 1,
            "last_recheck_at": time.time() - 60,
            "best_risk_pct": 0.03,
        }

        self.assertFalse(kw.should_continue_risk_too_wide_watch("000001"))
        self.assertNotIn("000001", kw.risk_too_wide_watchlist)

    def test_holding_position_removes_watch(self):
        kw = _WatchStub()
        kw.risk_too_wide_watchlist["000001"] = {
            "deadline": time.time() + 600,
            "last_recheck_at": time.time() - 60,
            "best_risk_pct": 0.03,
        }
        pos = kw.portfolio.get_or_create("000001")
        pos.quantity = 10

        self.assertFalse(kw.should_continue_risk_too_wide_watch("000001"))
        self.assertNotIn("000001", kw.risk_too_wide_watchlist)

    def test_recheck_with_valid_plan_enters_existing_buy_path(self):
        kw = _WatchStub()
        kw.risk_too_wide_watchlist["000001"] = {
            "deadline": time.time() + 600,
            "last_recheck_at": time.time() - main.RISK_TOO_WIDE_RECHECK_INTERVAL_SECONDS - 1,
            "best_risk_pct": 0.03,
        }

        kw.handle_condition_stock("A000001")

        self.assertEqual(len(kw.placed_orders), 1)
        self.assertNotIn("000001", kw.risk_too_wide_watchlist)
        _code, prediction, _ratio, _stage = kw.placed_orders[0]
        self.assertEqual(prediction["entry_limit_price"], 10_000)
        self.assertEqual(prediction["stop_price"], 9_850)


if __name__ == "__main__":
    unittest.main()
