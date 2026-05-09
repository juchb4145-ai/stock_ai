"""dante_hard_blocks_ai_candidate — Tier A 데이터 위생 코드 차단 테스트."""

from __future__ import annotations

import sys
import types
import unittest
from unittest import mock


def _ensure_external_stubs() -> None:
    if "PyQt5" not in sys.modules:
        qax = types.ModuleType("PyQt5.QAxContainer")
        qax.QAxWidget = mock.MagicMock
        widgets = types.ModuleType("PyQt5.QtWidgets")
        widgets.QApplication = mock.MagicMock
        widgets.QWidget = mock.MagicMock
        core = types.ModuleType("PyQt5.QtCore")
        core.QTimer = mock.MagicMock
        core.QObject = mock.MagicMock
        core.pyqtSignal = mock.MagicMock()
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

import entry_strategy as es  # noqa: E402
import main  # noqa: E402


class _StubKiwoom:
    dante_hard_blocks_ai_candidate = main.Kiwoom.dante_hard_blocks_ai_candidate


class DanteHardBlocksTests(unittest.TestCase):
    def _predict(self, reason_code: str, market_gate_action: str = ""):
        return {
            "status": "wait",
            "reason_code": reason_code,
            "market_gate_action": market_gate_action,
        }

    def test_tier_a_blocks(self):
        kw = _StubKiwoom()
        for rc in (
            es.GATE_TICKS_INSUFFICIENT,
            es.GATE_OBSERVATION_SHORT,
            es.GATE_FIVEMIN_CACHE,
        ):
            blocked, msg = kw.dante_hard_blocks_ai_candidate(self._predict(rc))
            self.assertTrue(blocked, "expected hard block for %s" % rc)
            self.assertEqual(msg, rc)

    def test_risk_off_blocks(self):
        kw = _StubKiwoom()
        blocked, msg = kw.dante_hard_blocks_ai_candidate(
            self._predict(
                es.GATE_NO_BREAKOUT,
                market_gate_action=es.MARKET_ACTION_BLOCK_ALL,
            )
        )
        self.assertTrue(blocked)
        self.assertEqual(msg, "market risk_off")

    def test_no_breakout_not_blocked(self):
        kw = _StubKiwoom()
        blocked, _msg = kw.dante_hard_blocks_ai_candidate(
            self._predict(es.GATE_NO_BREAKOUT)
        )
        self.assertFalse(blocked)


if __name__ == "__main__":
    unittest.main()
