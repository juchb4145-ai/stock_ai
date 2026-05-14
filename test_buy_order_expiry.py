"""cancel_stale_buy_orders 단위 테스트.

실행:
    .\\venv64\\Scripts\\python.exe -m pytest -q test_buy_order_expiry.py
또는:
    .\\venv64\\Scripts\\python.exe test_buy_order_expiry.py

핵심 점검:
  - ctx.placed_at + ctx.expiry_seconds 가 지난 매수 주문만 취소 발사.
  - send_order 가 order_type=3 (매수 취소) + 기존 order_no 로 호출.
  - cancel_requested_at 마킹으로 같은 주문에 두 번 취소 발사하지 않음.
  - 매도/order_no 부재/sell 측 종목은 스킵.
"""

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
import main  # noqa: E402


class _StubKiwoom:
    """cancel_stale_buy_orders 만 호출 가능한 최소 Kiwoom 모방."""

    cancel_stale_buy_orders = main.Kiwoom.cancel_stale_buy_orders

    def __init__(self) -> None:
        self.pending_order_codes: set = set()
        self.pending_sell_order_codes: set = set()
        self.order_context: dict = {}
        self.guarded_order_calls: list = []
        self.trade_log_calls: list = []

    def send_order(self, *args, **kwargs):
        raise AssertionError("cancel_stale_buy_orders must use submit_order_guarded")

    def submit_order_guarded(self, request):
        self.guarded_order_calls.append(
            (
                (
                    request.rqname,
                    request.screen_no,
                    request.order_type,
                    request.code,
                    request.quantity,
                    request.price,
                    request.order_gubun,
                    request.order_no,
                ),
                {},
            )
        )
        return 0

    def append_trade_log(self, *args, **kwargs):
        self.trade_log_calls.append((args, kwargs))


class CancelStaleBuyOrdersTests(unittest.TestCase):
    def test_cancels_when_expired(self):
        kw = _StubKiwoom()
        kw.pending_order_codes = {"000001"}
        now = time.time()
        kw.order_context["000001"] = {
            "side": "buy",
            "order_no": "ORD123",
            "placed_at": now - 60,  # 60초 경과
            "expiry_seconds": 45,
            "name": "테스트",
            "entry_limit_price": 10_000,
            "take_profit_price": 10_400,
        }
        kw.cancel_stale_buy_orders()
        self.assertEqual(len(kw.guarded_order_calls), 1)
        args = kw.guarded_order_calls[0][0]
        # submit_order_guarded(OrderRequest(...)) materializes these guarded order args.
        self.assertEqual(args[0], "buy_cancel")
        self.assertEqual(args[2], 3)  # order_type=3 (매수 취소)
        self.assertEqual(args[3], "000001")
        self.assertEqual(args[7], "ORD123")
        self.assertEqual(len(kw.trade_log_calls), 1)
        self.assertGreater(kw.order_context["000001"].get("cancel_requested_at", 0), 0)

    def test_skips_when_not_expired(self):
        kw = _StubKiwoom()
        kw.pending_order_codes = {"000001"}
        now = time.time()
        kw.order_context["000001"] = {
            "side": "buy",
            "order_no": "ORD123",
            "placed_at": now - 30,  # 30초 — expiry(45) 미달
            "expiry_seconds": 45,
        }
        kw.cancel_stale_buy_orders()
        self.assertEqual(kw.guarded_order_calls, [])
        self.assertNotIn("cancel_requested_at", kw.order_context["000001"])

    def test_skips_when_no_order_no(self):
        # chejan "접수" 가 아직 안 와서 order_no 가 비어 있는 경우 — 취소 발사 불가.
        kw = _StubKiwoom()
        kw.pending_order_codes = {"000001"}
        now = time.time()
        kw.order_context["000001"] = {
            "side": "buy",
            "order_no": "",
            "placed_at": now - 60,
            "expiry_seconds": 45,
        }
        kw.cancel_stale_buy_orders()
        self.assertEqual(kw.guarded_order_calls, [])

    def test_skips_when_sell_side(self):
        kw = _StubKiwoom()
        kw.pending_order_codes = {"000001"}
        kw.pending_sell_order_codes = {"000001"}
        now = time.time()
        kw.order_context["000001"] = {
            "side": "sell",
            "order_no": "ORD123",
            "placed_at": now - 60,
            "expiry_seconds": 45,
        }
        kw.cancel_stale_buy_orders()
        self.assertEqual(kw.guarded_order_calls, [])

    def test_does_not_double_cancel(self):
        # 이미 cancel_requested_at 이 최근(10초 이내) 마킹된 주문은 다시 취소 발사 안 함.
        kw = _StubKiwoom()
        kw.pending_order_codes = {"000001"}
        now = time.time()
        kw.order_context["000001"] = {
            "side": "buy",
            "order_no": "ORD123",
            "placed_at": now - 60,
            "expiry_seconds": 45,
            "cancel_requested_at": now - 2,  # 2초 전 이미 발사
        }
        kw.cancel_stale_buy_orders()
        self.assertEqual(kw.guarded_order_calls, [])

    def test_re_cancels_after_long_silence(self):
        # 10초 이상 chejan 응답 없이 만료 점검이 또 돌면 재발사(키움이 첫 취소를 누락한 경우 대비).
        kw = _StubKiwoom()
        kw.pending_order_codes = {"000001"}
        now = time.time()
        kw.order_context["000001"] = {
            "side": "buy",
            "order_no": "ORD123",
            "placed_at": now - 120,
            "expiry_seconds": 45,
            "cancel_requested_at": now - 30,  # 30초 전 첫 발사
        }
        kw.cancel_stale_buy_orders()
        self.assertEqual(len(kw.guarded_order_calls), 1)

    def test_cancels_multiple_codes_independently(self):
        kw = _StubKiwoom()
        kw.pending_order_codes = {"000001", "000002", "000003"}
        now = time.time()
        # 000001: 만료 — 취소.
        kw.order_context["000001"] = {
            "side": "buy",
            "order_no": "ORD1",
            "placed_at": now - 60,
            "expiry_seconds": 45,
        }
        # 000002: 미만료 — 스킵.
        kw.order_context["000002"] = {
            "side": "buy",
            "order_no": "ORD2",
            "placed_at": now - 10,
            "expiry_seconds": 45,
        }
        # 000003: 만료지만 매도 — 스킵.
        kw.pending_sell_order_codes.add("000003")
        kw.order_context["000003"] = {
            "side": "sell",
            "order_no": "ORD3",
            "placed_at": now - 60,
            "expiry_seconds": 45,
        }
        kw.cancel_stale_buy_orders()
        cancelled_codes = {call[0][3] for call in kw.guarded_order_calls}
        self.assertEqual(cancelled_codes, {"000001"})


if __name__ == "__main__":
    unittest.main()
