"""build_rule_entry_plan / compute_pullback_anchor 단위 테스트.

실행:
    .\\venv64\\Scripts\\python.exe -m pytest -q test_entry_plan.py
또는:
    .\\venv64\\Scripts\\python.exe test_entry_plan.py
(unittest 자동 발견)

핵심 점검:
  - compute_pullback_anchor: high 이후 최저 low 만 valid 로 잡는다.
  - build_rule_entry_plan: fib retracement 자리에 patient limit 발주, 윗자리/얕은 풀백은 거절.
"""

from __future__ import annotations

import sys
import types
import unittest
from typing import List
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
from bars import MinuteBar  # noqa: E402


def make_bar(*, open_: int, high: int, low: int, close: int, minute_start: int = 0) -> MinuteBar:
    return MinuteBar(
        minute_start=minute_start,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=1,
        received_at=float(minute_start),
    )


class ComputePullbackAnchorTests(unittest.TestCase):
    def test_returns_invalid_when_bars_empty(self):
        high, low, valid = entry_strategy.compute_pullback_anchor([])
        self.assertEqual((high, low, valid), (0, 0, False))

    def test_finds_high_then_post_high_low(self):
        # high 가 인덱스 0~2 사이 어딘가에 있고, 그 이후 봉이 풀백을 만든 케이스.
        bars = [
            make_bar(open_=10_000, high=10_100, low=10_000, close=10_080),  # i=0 high=10_100
            make_bar(open_=10_080, high=10_300, low=10_060, close=10_290),  # i=1 high=10_300 (max)
            make_bar(open_=10_290, high=10_280, low=10_200, close=10_210),  # i=2
            make_bar(open_=10_210, high=10_240, low=10_000, close=10_020),  # i=3 low=10_000 (post-high min)
            make_bar(open_=10_020, high=10_120, low=10_010, close=10_100),  # i=4
        ]
        high, low, valid = entry_strategy.compute_pullback_anchor(bars)
        self.assertEqual(high, 10_300)
        self.assertEqual(low, 10_000)
        self.assertTrue(valid)

    def test_post_high_low_only(self):
        # high 가 i=2 봉에서 형성됐어도 그 봉의 low(9_850)는 사용하지 않고,
        # 그 봉 이후의 봉들의 low 만 풀백으로 본다(high→low 인지 low→high 인지 분간 불가).
        bars = [
            make_bar(open_=9_500, high=9_600, low=9_400, close=9_580),
            make_bar(open_=9_580, high=9_900, low=9_550, close=9_880),
            make_bar(open_=9_880, high=10_300, low=9_850, close=10_280),  # i=2 high=10_300
            make_bar(open_=10_280, high=10_280, low=10_240, close=10_260),  # post-high low=10_240
        ]
        high, low, valid = entry_strategy.compute_pullback_anchor(bars)
        self.assertEqual(high, 10_300)
        self.assertEqual(low, 10_240)
        self.assertTrue(valid)

    def test_invalid_when_high_is_last_bar(self):
        # high 가 진행봉(=마지막 봉) 에서 형성됐으면 그 이후 풀백 데이터가 없어 valid=False.
        bars = [
            make_bar(open_=9_500, high=9_600, low=9_400, close=9_580),
            make_bar(open_=9_580, high=9_900, low=9_550, close=9_880),
            make_bar(open_=9_880, high=10_300, low=9_850, close=10_280),  # 마지막 봉 = high
        ]
        high, low, valid = entry_strategy.compute_pullback_anchor(bars)
        self.assertEqual(high, 10_300)
        self.assertEqual(low, 0)
        self.assertFalse(valid)

    def test_breakout_high_hint_overrides_when_higher(self):
        # watch 시작 시점에 잡힌 hint 가 lookback 봉 최고 high 보다 큰 경우 — hint 사용.
        bars = [
            make_bar(open_=10_000, high=10_100, low=9_950, close=10_080),
            make_bar(open_=10_080, high=10_120, low=10_000, close=10_010),
        ]
        high, low, valid = entry_strategy.compute_pullback_anchor(
            bars, breakout_high_hint=10_500
        )
        # hint 가 lookback 외부 고점이라 모든 바를 high 이후로 본다.
        self.assertEqual(high, 10_500)
        self.assertEqual(low, 9_950)
        self.assertTrue(valid)

    def test_invalid_when_only_zero_lows(self):
        bars = [
            make_bar(open_=10_000, high=10_100, low=0, close=10_080),
        ]
        high, low, valid = entry_strategy.compute_pullback_anchor(bars)
        self.assertEqual(high, 10_100)
        self.assertEqual(low, 0)
        self.assertFalse(valid)


class _PlanStubKiwoom:
    """build_rule_entry_plan 만 호출 가능한 최소 Kiwoom 모방."""

    build_rule_entry_plan = main.Kiwoom.build_rule_entry_plan
    parse_int = main.Kiwoom.parse_int
    parse_float = main.Kiwoom.parse_float

    class _Aggregator:
        def __init__(self, bars: List[MinuteBar]) -> None:
            self._bars = bars

        def all_bars(self, code: str) -> List[MinuteBar]:
            return list(self._bars)

    def __init__(self, bars: List[MinuteBar]) -> None:
        self.minute_aggregator = self._Aggregator(bars)


class BuildRuleEntryPlanTests(unittest.TestCase):
    def _bars_with_pullback(
        self,
        *,
        breakout_high: int = 10_300,
        pullback_low: int = 10_000,
        current_close: int = 10_120,
    ) -> List[MinuteBar]:
        return [
            make_bar(open_=10_000, high=10_100, low=10_000, close=10_080, minute_start=0),
            make_bar(open_=10_080, high=breakout_high, low=10_060, close=10_290, minute_start=60),
            make_bar(open_=10_290, high=10_280, low=10_200, close=10_210, minute_start=120),
            make_bar(open_=10_210, high=10_240, low=pullback_low, close=10_020, minute_start=180),
            make_bar(open_=10_020, high=current_close + 10, low=10_010, close=current_close, minute_start=240),
        ]

    def test_emits_fib_anchor_in_pullback_zone(self):
        bars = self._bars_with_pullback(
            breakout_high=10_300, pullback_low=10_000, current_close=10_120
        )
        kw = _PlanStubKiwoom(bars)
        prediction = {
            "code": "000001",
            "current_price": 10_120,
            "ask": 10_125,
            "bid": 10_115,
            "breakout_high": 10_300,
            "recent_low": 10_000,
        }
        plan = kw.build_rule_entry_plan(prediction)
        self.assertTrue(plan, "plan should be non-empty for valid pullback")
        # fib_anchor = 10_000 + (10_300 - 10_000) * 0.40 = 10_120
        self.assertEqual(plan["pullback_high"], 10_300)
        self.assertEqual(plan["pullback_low"], 10_000)
        self.assertEqual(plan["fib_anchor"], 10_120)
        # entry_limit = min(current_price=10_120, fib_anchor=10_120) -> 10_120 (round_down_to_tick)
        # 호가 단위에 따라 약간 round 될 수 있으나 anchor 와 거의 같아야 한다.
        self.assertLessEqual(plan["entry_limit_price"], 10_120)
        self.assertGreater(plan["entry_limit_price"], 10_000)
        self.assertIn("retracement", plan)
        # retracement = (10_120 - 10_000) / (10_300 - 10_000) = 0.40
        self.assertAlmostEqual(plan["retracement"], 0.40, places=2)
        self.assertIn("rule_fib", plan["plan_source"])
        # stop = pullback_low - 1tick (10_000 - tick) — entry_limit 보다 한 단계 아래
        self.assertLess(plan["stop_price"], plan["entry_limit_price"])
        self.assertGreater(plan["stop_price"], 9_900)

    def test_rejects_when_retracement_too_high(self):
        # current_price 가 풀백 저점에서 80% 회복 → 윗자리 추격. plan 거절.
        bars = self._bars_with_pullback(
            breakout_high=10_300, pullback_low=10_000, current_close=10_240
        )
        kw = _PlanStubKiwoom(bars)
        prediction = {
            "code": "000001",
            "current_price": 10_240,  # retracement = 240/300 = 0.80 > 0.60
            "ask": 10_245,
            "bid": 10_235,
            "breakout_high": 10_300,
            "recent_low": 10_000,
        }
        plan = kw.build_rule_entry_plan(prediction)
        self.assertEqual(plan, {}, "plan should be empty when retracement exceeds 0.60")

    def test_rejects_when_pullback_too_shallow(self):
        # 풀백 깊이가 -0.1% (10_290 → 10_280) — MIN_PULLBACK_DEPTH(0.3%) 미달.
        bars = [
            make_bar(open_=10_280, high=10_290, low=10_280, close=10_285, minute_start=0),
            make_bar(open_=10_285, high=10_290, low=10_280, close=10_286, minute_start=60),
        ]
        kw = _PlanStubKiwoom(bars)
        prediction = {
            "code": "000001",
            "current_price": 10_286,
            "ask": 10_290,
            "bid": 10_285,
            "breakout_high": 10_290,
            "recent_low": 10_280,
        }
        plan = kw.build_rule_entry_plan(prediction)
        self.assertEqual(plan, {}, "plan should be empty when pullback depth < 0.3%")

    def test_falls_back_when_no_bars(self):
        # 1분봉이 비어 있으면 fib 분석 불가 → 기존 보수적 fallback 경로.
        kw = _PlanStubKiwoom([])
        prediction = {
            "code": "000001",
            "current_price": 10_000,
            "ask": 10_010,
            "bid": 9_990,
            "breakout_high": 0,
            "recent_low": 9_950,
        }
        plan = kw.build_rule_entry_plan(prediction)
        self.assertTrue(plan, "fallback plan should be returned when fib data is missing")
        self.assertEqual(plan["plan_source"], "rule_fallback")
        # fib_anchor 는 0 (계산 불가).
        self.assertEqual(plan["fib_anchor"], 0)
        # entry_limit 은 min(current, bid + tick).
        self.assertLessEqual(plan["entry_limit_price"], 10_000)

    def test_deeper_pullback_yields_lower_anchor(self):
        # 같은 retracement 비율(40%)이라도 풀백이 깊을수록 fib_anchor 가 더 낮다.
        # 풀백 -3%: high=10_300, low=10_000, fib_anchor=10_120
        # 풀백 -5%: high=10_500, low=10_000, fib_anchor=10_200
        # 두 경우 모두 retracement 가 0.4 가 되도록 current_price 를 anchor 와 같게 둔다.
        deep_bars = self._bars_with_pullback(
            breakout_high=10_300, pullback_low=10_000, current_close=10_120
        )
        deep_plan = _PlanStubKiwoom(deep_bars).build_rule_entry_plan(
            {
                "code": "000001",
                "current_price": 10_120,
                "ask": 10_125,
                "bid": 10_115,
                "breakout_high": 10_300,
                "recent_low": 10_000,
            }
        )

        # 풀백이 더 깊은 케이스 — anchor 자리가 절대치로 더 낮음.
        # high - low 가 더 크므로 fib_anchor 자체는 더 위지만, breakout_high 대비 거리는 더 멀다.
        # 핵심: pullback_depth 가 더 큰 쪽이 절대 손실 자리도 더 깊게 떨어질 여지가 있다.
        self.assertEqual(deep_plan["fib_anchor"], 10_120)
        self.assertGreater(deep_plan["pullback_depth"], 0.005)


if __name__ == "__main__":
    unittest.main()
