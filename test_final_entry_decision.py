from __future__ import annotations

import sys
import types
import unittest
from unittest import mock

from final_entry_decision import (
    FINAL_REASON_PAPER_ONLY_BREAKOUT_PROBE,
    LIVE_BREAKOUT_BLOCK_REASON_CODE,
    build_final_entry_decision,
    is_breakout_probe_entry,
)
from momentum_breakout_strategy import EntryDecision, MomentumDecision
from order_guard import (
    LIVE_BREAKOUT_BLOCKED_BY,
    OrderGuard,
    RiskState,
)
from portfolio import PortfolioState
from quant_condition_strategy import QuantEntryDecision
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


def _final_from(momentum: MomentumDecision, legacy: QuantEntryDecision):
    return build_final_entry_decision(
        momentum_action=momentum.action.value,
        momentum_reason_code=momentum.reason_code,
        momentum_reason=momentum.reason,
        momentum_chase_risk_score=momentum.chase_risk_score,
        legacy_status=legacy.status,
        legacy_reason_code=legacy.reason_code,
        legacy_reason=legacy.reason,
        strategy_version="test_strategy",
        legacy_filter_enabled=True,
        entry_type=momentum.entry_type,
        position_size_multiplier=momentum.position_size_multiplier,
    )


def _legacy(status: str, reason_code: str = "LEGACY_READY") -> QuantEntryDecision:
    return QuantEntryDecision(
        status=status,
        reason="legacy {}".format(status),
        reason_code=reason_code,
        capture_price=10_000,
        current_price=9_850,
        entry_limit_price=9_850,
        stop_price=9_700,
        take_profit_price=10_050,
    )


class _LivePlaceBuyStub:
    parse_int = main.Kiwoom.parse_int
    current_open_position_risk = main.Kiwoom.current_open_position_risk
    build_position_size_plan = main.Kiwoom.build_position_size_plan
    format_position_size_plan = main.Kiwoom.format_position_size_plan
    place_buy_order = main.Kiwoom.place_buy_order
    submit_order_guarded = main.Kiwoom.submit_order_guarded

    def __init__(self):
        self.deposit = 10_000_000
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
        self.trade_log_calls = []
        self.last_order_guard_decision = None
        self.send_order_calls = 0
        self.order_guard = OrderGuard(
            TradeConfig(
                dry_run=False,
                live_trading_enabled=True,
                paper_portfolio_enabled=False,
                max_position_size=1_000_000,
                max_daily_exposure=10_000_000,
                time_policy_enabled=False,
            )
        )

    def normalize_code(self, code):
        return str(code).strip().lstrip("A")

    def get_deposit(self, force=False):
        return self.deposit

    def build_order_risk_state(self, request):
        return RiskState(
            mode="live",
            account_state_available=True,
            daily_loss_available=True,
        )

    def append_trade_log(self, *args, **kwargs):
        self.trade_log_calls.append((args, kwargs))

    def estimate_net_target_return(self, entry_price, target_price):
        return target_price / entry_price - 1 if entry_price else 0.0

    def save_best(self):
        raise AssertionError("blocked live breakout probe must not save order state")

    def save_portfolio_state(self):
        raise AssertionError("blocked live breakout probe must not save portfolio state")

    def register_realtime_stock(self, code):
        raise AssertionError("blocked live breakout probe must not register order state")

    def send_order(self, *args, **kwargs):
        self.send_order_calls += 1
        raise AssertionError("blocked live breakout probe must not call SendOrder")


def _ready_buy_prediction(**overrides):
    payload = {
        "code": "000001",
        "name": "test",
        "current_price": 10_000,
        "entry_limit_price": 10_000,
        "stop_price": 9_850,
        "take_profit_price": 10_300,
        "ratio": 1.0,
        "grade": main.QUANT_GRADE,
        "plan_source": main.QUANT_PLAN_SOURCE,
        "order_gubun": "00",
        "score": 0.9,
        "reason": "test ready",
        "reason_code": "BUY_PULLBACK_RECLAIM",
        "final_entry_allowed": True,
        "final_reason": "test final pass",
        "final_reason_code": "FINAL_BUY_READY",
        "strategy_version": "test",
        "legacy_filter_enabled": True,
        "decision_trace": {"test": True},
    }
    payload.update(overrides)
    return payload


class FinalEntryDecisionTests(unittest.TestCase):
    def test_final_paper_only_reason_is_breakout_probe_reason(self):
        self.assertTrue(
            is_breakout_probe_entry(
                reason_code=FINAL_REASON_PAPER_ONLY_BREAKOUT_PROBE,
            )
        )

    def test_momentum_buy_legacy_block_prevents_final_buy(self):
        momentum = MomentumDecision(
            EntryDecision.BUY,
            "momentum pass",
            "BUY_PULLBACK_CONFIRMED",
            chase_risk_score=12.0,
            entry_ratio=1.0,
        )
        final = _final_from(momentum, _legacy("blocked", "LEGACY_BLOCK_SPREAD"))

        self.assertFalse(final.allowed)
        self.assertEqual(final.status, "blocked")
        self.assertEqual(final.blocked_by, "legacy_veto")
        self.assertIn("LEGACY_BLOCK_SPREAD", final.reason_code)

    def test_legacy_ready_cannot_override_momentum_block_chase(self):
        momentum = MomentumDecision(
            EntryDecision.BLOCK_CHASE,
            "signal candle top",
            "BLOCK_SIGNAL_CANDLE_TOP",
            chase_risk_score=88.0,
        )
        final = _final_from(momentum, _legacy("ready"))

        self.assertFalse(final.allowed)
        self.assertEqual(final.status, "blocked")
        self.assertEqual(final.blocked_by, "momentum")
        self.assertIn("BLOCK_SIGNAL_CANDLE_TOP", final.reason_code)

    def test_missing_data_momentum_wait_data_blocks_even_if_legacy_ready(self):
        momentum = MomentumDecision(
            EntryDecision.WAIT_DATA,
            "missing_volume_ratio",
            "MISSING_VOLUME_RATIO",
            chase_risk_score=0.0,
            metrics={"volume_ratio": None},
        )
        final = _final_from(momentum, _legacy("ready"))

        self.assertFalse(final.allowed)
        self.assertEqual(final.status, "wait")
        self.assertEqual(final.blocked_by, "momentum")
        self.assertIn("MISSING_VOLUME_RATIO", final.reason_code)

    def test_both_pass_allows_final_buy_with_trace(self):
        momentum = MomentumDecision(
            EntryDecision.BUY,
            "pullback confirmed",
            "BUY_PULLBACK_RECLAIM",
            chase_risk_score=10.0,
            entry_ratio=1.0,
            entry_type="PULLBACK_RECLAIM",
        )
        final = _final_from(momentum, _legacy("ready"))

        self.assertTrue(final.allowed)
        self.assertEqual(final.reason_code, "FINAL_BUY_READY")
        self.assertEqual(final.decision_trace["momentum_decision"]["action"], "BUY")
        self.assertEqual(final.decision_trace["legacy_decision"]["status"], "ready")
        self.assertFalse(final.decision_trace["paper_only_breakout_probe"])

    def test_breakout_small_legacy_veto_is_not_ignored(self):
        final = build_final_entry_decision(
            momentum_action="BUY",
            momentum_reason_code="BUY_BREAKOUT_SMALL",
            momentum_reason="breakout probe",
            momentum_chase_risk_score=12.0,
            legacy_status="blocked",
            legacy_reason_code="LEGACY_BLOCK_PULLBACK",
            legacy_reason="pullback not ready",
            strategy_version="test_strategy",
            legacy_filter_enabled=True,
            entry_type="BREAKOUT_SMALL",
            position_size_multiplier=0.25,
            legacy_filter_veto_breakout_small=False,
        )

        self.assertFalse(final.allowed)
        self.assertEqual(final.blocked_by, "legacy_veto")
        self.assertFalse(final.legacy_veto_ignored)
        self.assertTrue(final.decision_trace["paper_only_breakout_probe"])
        self.assertTrue(final.decision_trace["breakout_probe_veto_ignore_removed"])

    def test_breakout_small_ready_is_marked_paper_only(self):
        final = build_final_entry_decision(
            momentum_action="BUY",
            momentum_reason_code="BUY_BREAKOUT_SMALL",
            momentum_reason="breakout probe",
            momentum_chase_risk_score=12.0,
            legacy_status="ready",
            legacy_reason_code="LEGACY_READY",
            legacy_reason="legacy ready",
            strategy_version="test_strategy",
            legacy_filter_enabled=True,
            entry_type="BREAKOUT_SMALL",
            position_size_multiplier=0.25,
        )

        self.assertTrue(final.allowed)
        self.assertEqual(final.reason_code, FINAL_REASON_PAPER_ONLY_BREAKOUT_PROBE)
        self.assertEqual(final.decision_trace["live_block_reason_code"], LIVE_BREAKOUT_BLOCK_REASON_CODE)

    def test_midday_paper_only_strategy_records_even_with_legacy_wait(self):
        final = build_final_entry_decision(
            momentum_action="BUY",
            momentum_reason_code="MIDDAY_VWAP_RECLAIM_PAPER_ONLY",
            momentum_reason="midday paper",
            legacy_status="wait",
            legacy_reason_code="SAFE_PULLBACK_SHALLOW",
            legacy_reason="wait pullback",
            entry_type="MIDDAY_VWAP_RECLAIM",
            position_size_multiplier=0.25,
        )

        self.assertTrue(final.allowed)
        self.assertEqual(final.reason_code, "FINAL_PAPER_ONLY_STRATEGY")
        self.assertTrue(final.legacy_veto_applied)
        self.assertTrue(final.decision_trace["paper_only_strategy"])
        self.assertTrue(final.decision_trace["blocked_live_breakout_probe"])

    def test_place_buy_order_logs_live_breakout_block_without_send_order(self):
        stub = _LivePlaceBuyStub()
        prediction = _ready_buy_prediction(
            reason_code="BUY_BREAKOUT_SMALL",
            momentum_reason_code="BUY_BREAKOUT_SMALL",
            final_reason_code=FINAL_REASON_PAPER_ONLY_BREAKOUT_PROBE,
            final_reason="Momentum breakout probe is paper-only",
            entry_type="BREAKOUT_SMALL",
            position_size_multiplier=0.25,
            decision_trace={
                "paper_only_breakout_probe": True,
                "blocked_live_breakout_probe": True,
            },
        )

        stub.place_buy_order("A000001", prediction, ratio=1.0, stage=2)

        self.assertEqual(stub.send_order_calls, 0)
        self.assertIsNotNone(stub.last_order_guard_decision)
        self.assertFalse(stub.last_order_guard_decision.allowed)
        self.assertEqual(stub.last_order_guard_decision.reason, LIVE_BREAKOUT_BLOCK_REASON_CODE)
        self.assertEqual(stub.last_order_guard_decision.blocked_by, LIVE_BREAKOUT_BLOCKED_BY)
        self.assertEqual(len(stub.trade_log_calls), 1)
        event_args, row = stub.trade_log_calls[0]
        self.assertEqual(event_args[0], "buy_skip")
        self.assertEqual(row["reason_code"], LIVE_BREAKOUT_BLOCK_REASON_CODE)
        self.assertEqual(row["blocked_by"], LIVE_BREAKOUT_BLOCKED_BY)
        self.assertEqual(row["plan_source"], "paper_only_breakout_probe")

    def test_place_buy_order_blocks_missing_final_entry_approval(self):
        class Stub:
            parse_int = main.Kiwoom.parse_int
            place_buy_order = main.Kiwoom.place_buy_order

            def __init__(self):
                self.trade_log_calls = []
                self.submit_calls = 0

            def normalize_code(self, code):
                return str(code).strip().lstrip("A")

            def append_trade_log(self, *args, **kwargs):
                self.trade_log_calls.append((args, kwargs))

            def submit_order_guarded(self, request):
                self.submit_calls += 1
                raise AssertionError("missing FinalEntryDecision must not reach OrderGuard")

        stub = Stub()
        prediction = {
            "name": "test",
            "current_price": 10_000,
            "reason": "legacy direct ready",
            "reason_code": "LEGACY_READY",
        }

        stub.place_buy_order("A000001", prediction, ratio=1.0, stage=2)

        self.assertEqual(stub.submit_calls, 0)
        self.assertEqual(len(stub.trade_log_calls), 1)
        self.assertEqual(stub.trade_log_calls[0][1]["reason"], "FinalEntryDecision block")

    def test_safe_second_entry_without_final_decision_does_not_order(self):
        class Stub:
            parse_int = main.Kiwoom.parse_int
            place_buy_order = main.Kiwoom.place_buy_order

            def __init__(self):
                self.trade_log_calls = []
                self.submit_calls = 0

            def normalize_code(self, code):
                return str(code).strip().lstrip("A")

            def append_trade_log(self, *args, **kwargs):
                self.trade_log_calls.append((args, kwargs))

            def submit_order_guarded(self, request):
                self.submit_calls += 1
                raise AssertionError("SAFE second entry must not bypass FinalEntryDecision")

        stub = Stub()
        prediction = {
            "name": "test",
            "current_price": 10_000,
            "capture_price": 10_200,
            "safe_pullback_entry": True,
            "grade": "SAFE",
            "status": "ready",
            "reason": "legacy safe second entry",
            "reason_code": "SAFE_SECOND_ENTRY",
            "entry_limit_price": 9_950,
            "stop_price": 9_800,
            "take_profit_price": 10_200,
        }

        stub.place_buy_order("A000001", prediction, ratio=0.5, stage=2)

        self.assertEqual(stub.submit_calls, 0)
        self.assertEqual(len(stub.trade_log_calls), 1)
        self.assertEqual(stub.trade_log_calls[0][1]["reason"], "FinalEntryDecision block")


if __name__ == "__main__":
    unittest.main()
