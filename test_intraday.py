"""review.intraday 단위 테스트.

  python -m unittest test_intraday

fixture: tests/fixtures/intraday/20260430/050890.csv
  진입 09:06:50 / 진입가 16761 기준 의도된 메트릭은 README 참조.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from review import intraday


FIXTURE_DIR = os.path.join("tests", "fixtures", "intraday")
TARGET_DATE = "2026-04-30"
CODE_WITH_BARS = "050890"


# ---------------------------------------------------------------------------
# 테스트 전용 가짜 Trade. 실제 Trade 는 portfolio/exit_strategy 등 의존이 있어
# 여기서는 attach_intraday_metrics 가 사용하는 속성만 갖춘 dataclass 로 대체.
# ---------------------------------------------------------------------------


@dataclass
class FakeTrade:
    code: str
    entry_first_time: Optional[datetime]
    entry_avg_price: float
    return_5m: Optional[float] = None
    max_return_25m: Optional[float] = None
    min_return_25m: Optional[float] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    features: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class LoadMinuteBarsTest(unittest.TestCase):

    def test_fixture_load(self):
        bars = intraday.load_minute_bars(TARGET_DATE, CODE_WITH_BARS, FIXTURE_DIR)
        self.assertEqual(len(bars), 15)
        self.assertEqual(bars[0].dt, datetime(2026, 4, 30, 9, 0, 0))
        self.assertEqual(bars[-1].dt, datetime(2026, 4, 30, 9, 14, 0))
        # 시간 오름차순
        for i in range(1, len(bars)):
            self.assertLess(bars[i - 1].dt, bars[i].dt)

    def test_missing_file_returns_empty(self):
        self.assertEqual(
            intraday.load_minute_bars(TARGET_DATE, "999999", FIXTURE_DIR),
            [],
        )


class ComputeIntradayMetricsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bars = intraday.load_minute_bars(TARGET_DATE, CODE_WITH_BARS, FIXTURE_DIR)
        cls.entry_time = datetime(2026, 4, 30, 9, 6, 50)
        cls.entry_price = 16761

    def setUp(self):
        self.metrics = intraday.compute_intraday_metrics(
            self.entry_time, self.entry_price, self.bars,
        )

    def test_return_1m(self):
        # close at 09:07 = 16850
        expected = (16850 - 16761) / 16761
        self.assertAlmostEqual(self.metrics["return_1m"], expected, places=6)

    def test_return_3m(self):
        # close at 09:09 = 17050
        expected = (17050 - 16761) / 16761
        self.assertAlmostEqual(self.metrics["return_3m"], expected, places=6)

    def test_return_5m_intraday(self):
        # close at 09:11 = 17280
        expected = (17280 - 16761) / 16761
        self.assertAlmostEqual(self.metrics["return_5m_intraday"], expected, places=6)

    def test_max_profit_3m(self):
        # high at 09:09 = 17080
        expected = (17080 - 16761) / 16761
        self.assertAlmostEqual(self.metrics["max_profit_3m"], expected, places=6)

    def test_max_drawdown_3m(self):
        # min low across 09:06~09:09 = 16690 (09:06)
        expected = (16690 - 16761) / 16761
        self.assertAlmostEqual(self.metrics["max_drawdown_3m"], expected, places=6)

    def test_buy_price_to_1m_low_pct(self):
        # min low across 09:06~09:07 = 16690
        expected = (16690 - 16761) / 16761
        self.assertAlmostEqual(self.metrics["buy_price_to_1m_low_pct"], expected, places=6)

    def test_breakout_candle_body_pct(self):
        # 09:06: open 16700, close 16780, high 16820, low 16690
        body = abs(16780 - 16700)
        rng = 16820 - 16690
        self.assertAlmostEqual(self.metrics["breakout_candle_body_pct"], body / rng, places=6)

    def test_upper_wick_pct(self):
        body_top = max(16700, 16780)
        rng = 16820 - 16690
        self.assertAlmostEqual(self.metrics["upper_wick_pct"], (16820 - body_top) / rng, places=6)

    def test_volume_ratio_1m(self):
        # entry bar volume = 12000, prev 5 bars (09:01~09:05) avg = (4500+4200+4800+5100+5500)/5 = 4820
        avg = (4500 + 4200 + 4800 + 5100 + 5500) / 5
        self.assertAlmostEqual(self.metrics["volume_ratio_1m"], 12000 / avg, places=6)

    def test_prior_3m_return_pct(self):
        # prev_close_3m = close at 09:03 = 16600
        expected = (16761 - 16600) / 16600
        self.assertAlmostEqual(self.metrics["prior_3m_return_pct"], expected, places=6)

    def test_session_high_at_entry_bar(self):
        # 09:06 의 high 16820 가 09:00~09:06 중 최대 → entry_bar 자체가 session_high
        self.assertEqual(self.metrics["entry_after_peak_sec"], 50.0)
        self.assertEqual(self.metrics["entry_near_session_high"], 1.0)

    def test_high_to_entry_drop_pct(self):
        expected = (16820 - 16761) / 16820
        self.assertAlmostEqual(self.metrics["high_to_entry_drop_pct"], expected, places=6)

    def test_entry_vs_vwap_pct_is_positive(self):
        # 진입가가 누적 VWAP 보다 높아야 함(모든 봉 평균보다 16761 가 위)
        self.assertGreater(self.metrics["entry_vs_vwap_pct"], 0)

    def test_empty_bars_returns_empty_dict(self):
        self.assertEqual(
            intraday.compute_intraday_metrics(self.entry_time, self.entry_price, []),
            {},
        )


class AttachIntradayMetricsTest(unittest.TestCase):
    """파이프라인: 1분봉 있는 종목 + 없는 종목 + 5분봉 라벨도 없는 종목."""

    def test_with_intraday_path(self):
        trade = FakeTrade(
            code=CODE_WITH_BARS,
            entry_first_time=datetime(2026, 4, 30, 9, 6, 50),
            entry_avg_price=16761,
            return_5m=0.02, max_return_25m=0.067, min_return_25m=-0.012,
        )
        summary = intraday.attach_intraday_metrics(
            [trade], target_date=TARGET_DATE, intraday_dir=FIXTURE_DIR,
        )
        self.assertEqual(summary["with_intraday"], [CODE_WITH_BARS])
        self.assertEqual(trade.metrics["metric_source"], "kiwoom_1m_csv")
        self.assertIn("return_1m", trade.metrics)
        self.assertIn("breakout_candle_body_pct", trade.features)
        self.assertIn("entry_near_session_high", trade.features)

    def test_fallback_path_uses_5m_labels(self):
        trade = FakeTrade(
            code="999999",
            entry_first_time=datetime(2026, 4, 30, 9, 30, 0),
            entry_avg_price=10000,
            return_5m=0.005, max_return_25m=0.04, min_return_25m=-0.02,
        )
        summary = intraday.attach_intraday_metrics(
            [trade], target_date=TARGET_DATE, intraday_dir=FIXTURE_DIR,
        )
        self.assertEqual(summary["fallback"], ["999999"])
        self.assertEqual(trade.metrics["metric_source"], "fallback_5m_approx")
        self.assertEqual(trade.metrics["return_5m_intraday"], 0.005)
        self.assertEqual(trade.metrics["max_profit_5m"], 0.04)
        self.assertIsNone(trade.metrics.get("return_1m"))   # 1분봉 정보 없음

    def test_missing_path_when_no_labels(self):
        trade = FakeTrade(
            code="888888",
            entry_first_time=datetime(2026, 4, 30, 10, 0, 0),
            entry_avg_price=5000,
            return_5m=None, max_return_25m=None, min_return_25m=None,
        )
        summary = intraday.attach_intraday_metrics(
            [trade], target_date=TARGET_DATE, intraday_dir=FIXTURE_DIR,
        )
        self.assertEqual(summary["missing"], ["888888"])
        self.assertEqual(trade.metrics["metric_source"], "missing")

    def test_no_entry_time_marked_missing(self):
        trade = FakeTrade(code="000000", entry_first_time=None, entry_avg_price=0)
        summary = intraday.attach_intraday_metrics(
            [trade], target_date=TARGET_DATE, intraday_dir=FIXTURE_DIR,
        )
        self.assertEqual(summary["missing"], ["000000"])
        self.assertEqual(trade.metrics["metric_source"], "missing")


class WriteCsvAndLoadRoundTripTest(unittest.TestCase):
    """fetch_minute_bars.write_intraday_csv 가 만들어내는 형식과 호환 확인."""

    def test_round_trip(self):
        from fetch_minute_bars import write_intraday_csv

        rows = [
            {"datetime": "2026-04-30 10:00:00", "open": 100, "high": 105,
             "low": 99, "close": 103, "volume": 500},
            {"datetime": "2026-04-30 10:01:00", "open": 103, "high": 108,
             "low": 102, "close": 107, "volume": 600},
        ]
        tmp = tempfile.mkdtemp(prefix="intraday_test_")
        try:
            path = os.path.join(tmp, "20260430", "111111.csv")
            n = write_intraday_csv(path, rows)
            self.assertEqual(n, 2)
            bars = intraday.load_minute_bars("2026-04-30", "111111", tmp)
            self.assertEqual(len(bars), 2)
            self.assertEqual(bars[0].close, 103.0)
            self.assertEqual(bars[1].volume, 600.0)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
