from __future__ import annotations

import sys
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
import main  # noqa: E402
from candidate_registry import (  # noqa: E402
    CONDITION_COMBO_DANTE_ONLY,
    CONDITION_COMBO_QUANT_AND_DANTE,
    CONDITION_COMBO_QUANT_ONLY,
    CandidateRegistry,
)


class _Decision:
    def __init__(
        self,
        *,
        allowed: bool = True,
        capture_allowed: bool = True,
        entry_allowed: bool = True,
        role: str = "trading",
        reason_code: str = "ALLOW_CANDIDATE_CAPTURE",
    ) -> None:
        self.allowed = allowed
        self.action = reason_code
        self.reason_code = reason_code
        self.current_time = "2026-05-15T09:10:00+09:00"
        self.session = "regular_market"
        self.next_allowed_time = None
        self.config_version = "test"
        self.entry_allowed = entry_allowed
        self.capture_allowed = capture_allowed
        self.manage_allowed = True
        self.analysis_allowed = True
        self.candidate_role = role


class _TimePolicy:
    def evaluate_trading_candidate_capture(self, **kwargs):
        return _Decision(role="trading")

    def evaluate_candidate_capture(self, **kwargs):
        return _Decision(role="analysis_only")


class _CaptureLogger:
    def __init__(self) -> None:
        self.detections = []
        self.captures = []

    def append_detection(self, **kwargs):
        self.detections.append(kwargs)

    def append_capture_price(self, **kwargs):
        self.captures.append(kwargs)


class _StubKiwoom:
    normalize_code = main.Kiwoom.normalize_code
    _condition_event_meta = main.Kiwoom._condition_event_meta
    _condition_log_meta = main.Kiwoom._condition_log_meta
    register_condition_detected_stock = main.Kiwoom.register_condition_detected_stock
    handle_condition_stock = main.Kiwoom.handle_condition_stock

    def __init__(self) -> None:
        self.time_policy = _TimePolicy()
        self.candidate_registry = CandidateRegistry(
            signal_source=main.TRADE_CONFIG.signal_source,
            candidate_expiry_seconds=main.TRADE_CONFIG.candidate_expiry_seconds,
            primary_condition_name=main.PRIMARY_CONDITION_NAME,
            bonus_condition_name=main.BONUS_CONDITION_NAME,
        )
        self.condition_capture_logger = _CaptureLogger()
        self.monitoring_dict = {}
        self.realtime_registered_codes = set()
        self.realtime_code_screens = {}
        self.condition_registered_at = {}
        self.pending_condition_codes = []
        self.last_signal_at = {}
        self.no_tick_codes = set()
        self.predict_called = False

    def get_code_name(self, code):
        return "테스트종목"

    def ensure_monitoring_stock(self, code):
        code = self.normalize_code(code)
        return self.monitoring_dict.setdefault(code, {"condition_name": main.CONDITION_NAME})

    def register_realtime_stock(self, code):
        code = self.normalize_code(code)
        self.realtime_registered_codes.add(code)
        self.realtime_code_screens[code] = "0160"

    def enqueue_condition_stock(self, code, condition_name="", event_type="I"):
        code = self.normalize_code(code)
        if code not in self.pending_condition_codes:
            self.pending_condition_codes.append(code)

    def predict_stock(self, code):
        self.predict_called = True
        raise AssertionError("analysis-only DANTE_ONLY candidate must not be predicted")


class ConditionRoleFlowTests(unittest.TestCase):
    def test_primary_condition_creates_quant_only_trading_candidate(self):
        kw = _StubKiwoom()

        kw.register_condition_detected_stock("A005930", main.PRIMARY_CONDITION_NAME, "I")

        candidate = kw.candidate_registry.get("005930")
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.meta["condition_combo"], CONDITION_COMBO_QUANT_ONLY)
        self.assertTrue(candidate.meta["quant_detected"])
        self.assertFalse(candidate.meta["dante_detected"])
        self.assertEqual(candidate.meta["candidate_role"], "trading")
        self.assertIn("005930", kw.monitoring_dict)
        self.assertIn("005930", kw.pending_condition_codes)
        self.assertIn("005930", kw.realtime_registered_codes)
        self.assertEqual(
            kw.condition_capture_logger.detections[-1]["condition_meta"]["condition_combo"],
            CONDITION_COMBO_QUANT_ONLY,
        )

    def test_bonus_after_primary_updates_to_quant_and_dante(self):
        kw = _StubKiwoom()
        kw.register_condition_detected_stock("005930", main.PRIMARY_CONDITION_NAME, "I")
        candidate_id = kw.candidate_registry.get("005930").candidate_id

        kw.register_condition_detected_stock("005930", main.BONUS_CONDITION_NAME, "I")

        candidate = kw.candidate_registry.get("005930")
        self.assertEqual(candidate.candidate_id, candidate_id)
        self.assertEqual(candidate.refresh_count, 1)
        self.assertEqual(candidate.meta["condition_combo"], CONDITION_COMBO_QUANT_AND_DANTE)
        self.assertTrue(candidate.meta["quant_detected"])
        self.assertTrue(candidate.meta["dante_detected"])
        self.assertEqual(kw.monitoring_dict["005930"]["condition_name"], main.PRIMARY_CONDITION_NAME)
        self.assertEqual(kw.monitoring_dict["005930"]["last_condition_name"], main.BONUS_CONDITION_NAME)
        self.assertEqual(
            kw.condition_capture_logger.detections[-1]["condition_meta"]["condition_combo"],
            CONDITION_COMBO_QUANT_AND_DANTE,
        )

    def test_bonus_only_is_analysis_candidate_and_never_live_buy(self):
        kw = _StubKiwoom()

        kw.register_condition_detected_stock("005930", main.BONUS_CONDITION_NAME, "I")

        candidate = kw.candidate_registry.get("005930")
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.meta["condition_combo"], CONDITION_COMBO_DANTE_ONLY)
        self.assertEqual(candidate.meta["candidate_role"], "analysis_only")
        self.assertNotIn("005930", kw.monitoring_dict)
        self.assertNotIn("005930", kw.pending_condition_codes)
        self.assertIn("005930", kw.realtime_registered_codes)
        self.assertEqual(
            kw.condition_capture_logger.detections[-1]["condition_meta"]["condition_combo"],
            CONDITION_COMBO_DANTE_ONLY,
        )

        kw.pending_condition_codes.append("005930")
        kw.handle_condition_stock("005930")
        self.assertFalse(kw.predict_called)


if __name__ == "__main__":
    unittest.main()
