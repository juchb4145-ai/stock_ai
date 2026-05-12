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


class _TimeFilterStub:
    normalize_code = main.Kiwoom.normalize_code
    parse_int = main.Kiwoom.parse_int
    realtime_daily_turnover = main.Kiwoom.realtime_daily_turnover
    realtime_turnover_rank = main.Kiwoom.realtime_turnover_rank
    evaluate_time_filter = main.Kiwoom.evaluate_time_filter

    def __init__(self, hhmmss: int) -> None:
        self.hhmmss = hhmmss
        self.realtime_ticks = {}

    def current_hhmmss(self) -> int:
        return self.hhmmss


class TimeFilterTests(unittest.TestCase):
    def test_morning_allows_even_without_turnover_threshold(self):
        kw = _TimeFilterStub(93000)

        out = kw.evaluate_time_filter("000001", current_price=10_000, accum_volume=1)

        self.assertTrue(out["ok"])
        self.assertEqual(out["phase"], "morning")
        self.assertGreater(out["weight"], 1.0)

    def test_morning_keeps_turnover_metadata_for_logs(self):
        kw = _TimeFilterStub(93000)

        out = kw.evaluate_time_filter("000001", current_price=10_000, accum_volume=500_000)

        self.assertTrue(out["ok"])
        self.assertEqual(out["phase"], "morning")
        self.assertEqual(out["daily_turnover"], 5_000_000_000)

    def test_midday_blocks_new_buys(self):
        kw = _TimeFilterStub(110000)

        out = kw.evaluate_time_filter("000001", current_price=10_000, accum_volume=5_000_000)

        self.assertFalse(out["ok"])
        self.assertEqual(out["status"], "blocked")
        self.assertEqual(out["phase"], "midday")

    def test_closing_requires_top_turnover_rank(self):
        kw = _TimeFilterStub(143000)
        for idx in range(11):
            code = f"{idx:06d}"
            kw.realtime_ticks[code] = [
                {
                    "close": 10_000,
                    "accum_volume": 2_000_000 - idx,
                }
            ]

        out = kw.evaluate_time_filter("000010", current_price=10_000, accum_volume=1_999_990)

        self.assertFalse(out["ok"])
        self.assertEqual(out["phase"], "closing")
        self.assertEqual(out["turnover_rank"], 11)


if __name__ == "__main__":
    unittest.main()
