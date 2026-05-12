"""AI 후보는 즉시 매수 승격하지 않고 감시 후 룰 ready 에서만 통과한다."""

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
        "status": "wait",
        "stage": 2,
        "ratio": 0.0,
        "code": "000001",
        "name": "테스트",
        "current_price": 10_000,
        "grade": "",
        "reason": "거래속도 부족",
        "reason_code": entry_strategy.GATE_VOLUME_SPEED,
        "model_name": "DanteLightGBM",
        "model_score": 0.76,
        "model_action": "shadow_allow",
        "model_target": "good_trade",
        "model_threshold": 0.52,
        "market_gate_action": entry_strategy.MARKET_ACTION_ALLOW,
    }
    payload.update(overrides)
    return payload


class _AiWatchStub:
    parse_float = main.Kiwoom.parse_float
    normalize_code = main.Kiwoom.normalize_code
    dante_hard_blocks_ai_candidate = main.Kiwoom.dante_hard_blocks_ai_candidate
    dante_allows_ai_candidate_watch = main.Kiwoom.dante_allows_ai_candidate_watch
    cleanup_ai_candidate_watchlist = main.Kiwoom.cleanup_ai_candidate_watchlist
    start_ai_candidate_watch = main.Kiwoom.start_ai_candidate_watch
    should_continue_ai_candidate_watch = main.Kiwoom.should_continue_ai_candidate_watch
    maybe_promote_ai_candidate = main.Kiwoom.maybe_promote_ai_candidate

    def __init__(self) -> None:
        self.ai_candidate_watchlist = {}
        self.pending_condition_codes = []
        self.portfolio = PortfolioState()

    def requeue_condition_stock(self, code):
        code = self.normalize_code(code)
        if code not in self.pending_condition_codes:
            self.pending_condition_codes.append(code)

    def current_hhmmss(self):
        return 100000


class AiCandidateWatchTests(unittest.TestCase):
    def setUp(self):
        patches = [
            mock.patch.object(main, "MODEL_ASSIST_ONLY", False),
            mock.patch.object(main, "AI_CANDIDATE_PROMOTION_ENABLED", True),
            mock.patch.object(main, "AI_CANDIDATE_WATCH_ENABLED", True),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_high_score_wait_registers_watch_without_ready_promotion(self):
        kw = _AiWatchStub()

        out = kw.maybe_promote_ai_candidate(_prediction())

        self.assertEqual(out["status"], "wait")
        self.assertEqual(out["ratio"], 0.0)
        self.assertIn("000001", kw.ai_candidate_watchlist)
        self.assertIn("000001", kw.pending_condition_codes)
        self.assertIn("AI 후보 감시", out["reason"])

    def test_ready_after_watch_passes_existing_ready_path(self):
        kw = _AiWatchStub()
        kw.ai_candidate_watchlist["000001"] = {
            "started_at": time.time() - 60,
            "deadline": time.time() + 600,
            "last_recheck_at": time.time() - 60,
            "best_model_score": 0.77,
            "reason_code": entry_strategy.GATE_VOLUME_SPEED,
        }

        out = kw.maybe_promote_ai_candidate(
            _prediction(
                status="ready",
                ratio=1.0,
                grade="B",
                reason="B급 첫 눌림",
                reason_code=entry_strategy.READY_BGRADE_PULLBACK,
            )
        )

        self.assertEqual(out["status"], "ready")
        self.assertEqual(out["ratio"], 1.0)
        self.assertNotIn("000001", kw.ai_candidate_watchlist)
        self.assertIn("AI 감시 후 룰 ready", out["reason"])

    def test_hard_block_does_not_register_watch(self):
        kw = _AiWatchStub()

        out = kw.maybe_promote_ai_candidate(
            _prediction(reason_code=entry_strategy.GATE_SPREAD)
        )

        self.assertEqual(out["status"], "wait")
        self.assertNotIn("000001", kw.ai_candidate_watchlist)
        self.assertEqual(out["ai_candidate_block_reason"], entry_strategy.GATE_SPREAD)

    def test_deep_pullback_registers_watch_without_buying_immediately(self):
        kw = _AiWatchStub()

        out = kw.maybe_promote_ai_candidate(
            _prediction(reason_code=entry_strategy.GATE_BGRADE_PULLBACK_DEEP)
        )

        self.assertEqual(out["status"], "wait")
        self.assertEqual(out["ratio"], 0.0)
        self.assertIn("000001", kw.ai_candidate_watchlist)
        self.assertIn("000001", kw.pending_condition_codes)

    def test_vwap_lost_registers_watch_for_recovery(self):
        kw = _AiWatchStub()

        out = kw.maybe_promote_ai_candidate(
            _prediction(status="blocked", reason_code=entry_strategy.GATE_STAGE2_VWAP_LOST)
        )

        self.assertEqual(out["status"], "wait")
        self.assertEqual(out["ratio"], 0.0)
        self.assertIn("000001", kw.ai_candidate_watchlist)
        self.assertIn("000001", kw.pending_condition_codes)

    def test_drawdown_cap_remains_hard_blocked(self):
        kw = _AiWatchStub()

        out = kw.maybe_promote_ai_candidate(
            _prediction(status="blocked", reason_code=entry_strategy.GATE_BGRADE_DRAWDOWN)
        )

        self.assertEqual(out["status"], "blocked")
        self.assertNotIn("000001", kw.ai_candidate_watchlist)
        self.assertEqual(out["ai_candidate_block_reason"], entry_strategy.GATE_BGRADE_DRAWDOWN)


if __name__ == "__main__":
    unittest.main()
