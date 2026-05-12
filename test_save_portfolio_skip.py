"""save_portfolio_state 의 빈 portfolio skip 동작 테스트.

main.Kiwoom.save_portfolio_state 가 보유/주문 종목 0 일 때 디스크 IO 를 건너뛰는지
검증한다. 1.5초 주기로 호출되는 check_open_positions 에서 무의미한 fsync 가 누적되지
않도록 하는 polish.

PyQt5/pandas 의존을 sys.modules stub 으로 우회한 뒤 unbound 메서드만 호출한다
(test_shadow_training 과 동일 패턴).
"""

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
from portfolio import PortfolioState  # noqa: E402


class _StubKiwoom:
    save_portfolio_state = main.Kiwoom.save_portfolio_state

    def __init__(self):
        self.portfolio = PortfolioState()
        self.trading_day = "2026-04-30"


class SavePortfolioSkipTests(unittest.TestCase):
    def test_empty_portfolio_skips_disk_write(self):
        kw = _StubKiwoom()
        with mock.patch.object(PortfolioState, "save") as mocked_save:
            kw.save_portfolio_state()
            mocked_save.assert_not_called()

    def test_non_empty_portfolio_writes_to_disk(self):
        kw = _StubKiwoom()
        kw.portfolio.get_or_create("005930", name="삼성전자")
        with mock.patch.object(PortfolioState, "save") as mocked_save:
            kw.save_portfolio_state()
            mocked_save.assert_called_once()
            # path 인자가 PORTFOLIO_STATE_PATH 인지 확인
            args, kwargs = mocked_save.call_args
            self.assertEqual(args[0], main.PORTFOLIO_STATE_PATH)
            # metadata 가 trading_day 를 포함해야 함
            self.assertIn("trading_day", kwargs.get("metadata", {}))
            self.assertEqual(kwargs["metadata"]["trading_day"], "2026-04-30")

    def test_save_failure_logged_not_raised(self):
        kw = _StubKiwoom()
        kw.portfolio.get_or_create("005930", name="삼성전자")
        with mock.patch.object(PortfolioState, "save", side_effect=OSError("disk full")):
            # 예외가 호출자로 전파되면 안 됨 -- best-effort 동작
            kw.save_portfolio_state()


if __name__ == "__main__":
    unittest.main()
