"""A급 watch 만료 decision 이 로그/Shadow 샘플 경로로 전달되는지 검증."""

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


class _MinuteAggregator:
    def all_bars(self, code):
        return []


class _MarketState:
    def snapshot(self):
        return None


class _StubKiwoom:
    score_opening_trade = main.Kiwoom.score_opening_trade
    parse_int = main.Kiwoom.parse_int

    def __init__(self) -> None:
        now = time.time()
        self.realtime_ticks = {
            "005930": [
                {
                    "received_at": now - 60,
                    "signed_at": "100000",
                    "close": 10_000,
                    "high": 10_050,
                    "open": 9_900,
                    "low": 9_880,
                    "ask": 10_005,
                    "bid": 9_995,
                    "accum_volume": 100_000,
                    "chejan_strength": 115.0,
                },
                {
                    "received_at": now,
                    "signed_at": "100100",
                    "close": 10_000,
                    "high": 10_080,
                    "open": 9_900,
                    "low": 9_880,
                    "ask": 10_005,
                    "bid": 9_995,
                    "accum_volume": 160_000,
                    "chejan_strength": 115.0,
                },
            ]
        }
        self.condition_registered_at = {"005930": now - 120}
        self.portfolio = {}
        self.five_min_cache = {}
        self.minute_aggregator = _MinuteAggregator()
        self.market_state = _MarketState()
        self.dante_a_watchlist = {
            "005930": {
                "started_at": now - entry_strategy.PULLBACK_WINDOW_MAX_SECONDS - 5,
                "deadline": now - 1,
                "breakout_high": 10_100,
            }
        }
        self.shadow_samples = []

    def normalize_code(self, code):
        return code.strip().lstrip("A")

    def current_hhmmss(self):
        return 100000

    def refresh_five_min_indicators(self, code):
        return None

    def get_code_name(self, code):
        return "삼성전자"

    def register_dante_shadow_sample(self, **kwargs):
        self.shadow_samples.append(kwargs)

    def register_dante_training_sample(self, **kwargs):
        raise AssertionError("expired watch must not be registered as ready training")

    def requeue_condition_stock(self, code):
        raise AssertionError("expired watch should be blocked, not requeued")


class AWatchExpiryTests(unittest.TestCase):
    def test_expired_watch_is_evaluated_before_removal_for_shadow_sample(self):
        kw = _StubKiwoom()

        with mock.patch("entry_strategy.evaluate_first_entry") as evaluate_first_entry:
            prediction = kw.score_opening_trade("A005930")

        evaluate_first_entry.assert_not_called()
        self.assertEqual(prediction["status"], "blocked")
        self.assertEqual(prediction["stage"], 2)
        self.assertEqual(prediction["reason_code"], entry_strategy.GATE_STAGE2_WINDOW_EXPIRED)
        self.assertIn("A-watch window expired", prediction["reason"])
        self.assertNotIn("005930", kw.dante_a_watchlist)
        self.assertEqual(len(kw.shadow_samples), 1)
        self.assertEqual(
            kw.shadow_samples[0]["decision"].reason_code,
            entry_strategy.GATE_STAGE2_WINDOW_EXPIRED,
        )


if __name__ == "__main__":
    unittest.main()
