"""bars.py — MinuteBarAggregator(VWAP) + FiveMinIndicatorCache(ATR) 단위 테스트.

W1 보강의 데이터 소스가 되는 두 인디케이터를 직접 검증한다:
    - MinuteBarAggregator.intraday_vwap() : 일중 거래량 가중 평균가
    - MinuteBarAggregator.pullback_low_after_high() : 직전 고점 이후 저점
    - FiveMinIndicators.atr_pct           : 5분봉 ATR(14) / last_close
"""

from __future__ import annotations

import unittest

from bars import (
    ATR_PERIOD_DEFAULT,
    FiveMinIndicatorCache,
    MinuteBarAggregator,
)


def _push(agg: MinuteBarAggregator, *, code: str, ts: float, price: int, accum: int) -> None:
    agg.push(
        code,
        received_at=ts,
        close=price,
        high=price,
        low=price,
        open_=price,
        accum_volume=accum,
    )


class IntradayVwapTests(unittest.TestCase):
    def test_no_data_returns_zero(self):
        agg = MinuteBarAggregator()
        self.assertEqual(agg.intraday_vwap("000001"), 0.0)

    def test_single_push_no_delta_volume_returns_zero(self):
        # 첫 push 의 prev_accum 은 accum 자체로 초기화 → delta_volume == 0
        agg = MinuteBarAggregator()
        _push(agg, code="000001", ts=60.0, price=10_000, accum=1_000)
        self.assertEqual(agg.intraday_vwap("000001"), 0.0)

    def test_weighted_average_across_multiple_pushes(self):
        agg = MinuteBarAggregator()
        # 첫 push: prev_accum 초기화(volume 0)
        _push(agg, code="000001", ts=60.0, price=10_000, accum=0)
        # 가격 10_000 × 100주
        _push(agg, code="000001", ts=61.0, price=10_000, accum=100)
        # 가격 11_000 × 200주
        _push(agg, code="000001", ts=62.0, price=11_000, accum=300)
        # VWAP = (10_000×100 + 11_000×200) / 300 = 3_200_000 / 300 = 10_666.67
        self.assertAlmostEqual(agg.intraday_vwap("000001"), 3_200_000 / 300, places=2)

    def test_isolated_per_code(self):
        agg = MinuteBarAggregator()
        _push(agg, code="A", ts=60.0, price=10_000, accum=0)
        _push(agg, code="A", ts=61.0, price=10_000, accum=100)
        _push(agg, code="B", ts=60.0, price=20_000, accum=0)
        _push(agg, code="B", ts=61.0, price=20_000, accum=100)
        self.assertAlmostEqual(agg.intraday_vwap("A"), 10_000.0, places=2)
        self.assertAlmostEqual(agg.intraday_vwap("B"), 20_000.0, places=2)

    def test_discard_clears_vwap(self):
        agg = MinuteBarAggregator()
        _push(agg, code="000001", ts=60.0, price=10_000, accum=0)
        _push(agg, code="000001", ts=61.0, price=10_000, accum=100)
        self.assertGreater(agg.intraday_vwap("000001"), 0.0)
        agg.discard("000001")
        self.assertEqual(agg.intraday_vwap("000001"), 0.0)


class PullbackLowAfterHighTests(unittest.TestCase):
    def test_no_bars_returns_zero(self):
        agg = MinuteBarAggregator()
        self.assertEqual(agg.pullback_low_after_high("000001"), 0)

    def test_finds_lowest_after_highest(self):
        agg = MinuteBarAggregator()
        # 봉1: high=10_300, 봉2(현재): low=10_100  → 풀백 저점 10_100
        # 분 경계를 명확히 가르기 위해 ts=60(분0), ts=120(분1) 등
        agg.push("000001", received_at=60, close=10_280, high=10_300, low=10_000, open_=10_000, accum_volume=0)
        agg.push("000001", received_at=120, close=10_200, high=10_290, low=10_100, open_=10_280, accum_volume=100)
        self.assertEqual(agg.pullback_low_after_high("000001"), 10_100)

    def test_returns_zero_when_high_at_last_bar(self):
        # 최고가가 가장 마지막 봉이면 "after high" 가 비어 있음 → 0
        agg = MinuteBarAggregator()
        agg.push("000001", received_at=60, close=10_100, high=10_100, low=10_000, open_=10_000, accum_volume=0)
        agg.push("000001", received_at=120, close=10_300, high=10_300, low=10_200, open_=10_100, accum_volume=100)
        self.assertEqual(agg.pullback_low_after_high("000001"), 0)


class FiveMinAtrTests(unittest.TestCase):
    def test_no_bars_atr_none(self):
        cache = FiveMinIndicatorCache()
        ind = cache.update_bars("000001", [])
        self.assertIsNone(ind.atr_pct)

    def test_too_few_bars_atr_none(self):
        cache = FiveMinIndicatorCache()
        bars = [(10_000, 10_100, 9_900, 10_050, 1_000)] * 5
        ind = cache.update_bars("000001", bars)
        self.assertIsNone(ind.atr_pct)

    def test_constant_bars_atr_around_band_width(self):
        # 모든 봉이 high-low = 200, 종가 일정 → True Range 가 모두 200, last_close=10_050
        cache = FiveMinIndicatorCache()
        bars = [(10_000, 10_100, 9_900, 10_050, 1_000) for _ in range(ATR_PERIOD_DEFAULT + 2)]
        ind = cache.update_bars("000001", bars)
        self.assertIsNotNone(ind.atr_pct)
        # ATR ≈ 200 / 10_050 ≈ 0.0199
        self.assertAlmostEqual(ind.atr_pct, 200 / 10_050, places=4)

    def test_high_volatility_bars_have_higher_atr(self):
        cache = FiveMinIndicatorCache()
        low_vol = [(10_000, 10_050, 9_950, 10_010, 1_000) for _ in range(ATR_PERIOD_DEFAULT + 2)]
        high_vol = [(10_000, 10_400, 9_600, 10_050, 1_000) for _ in range(ATR_PERIOD_DEFAULT + 2)]
        ind_low = cache.update_bars("LOW", low_vol)
        ind_high = cache.update_bars("HIGH", high_vol)
        self.assertGreater(ind_high.atr_pct, ind_low.atr_pct * 5)

    def test_atr_handles_zero_close_gracefully(self):
        # 봉 일부에 0 close 가 섞여도 None 안 떨어짐(스킵 후 가능하면 계산)
        cache = FiveMinIndicatorCache()
        bars = [(10_000, 10_100, 9_900, 10_050, 1_000) for _ in range(ATR_PERIOD_DEFAULT + 2)]
        bars[3] = (0, 0, 0, 0, 0)  # 더러운 봉 한 개
        ind = cache.update_bars("000001", bars)
        # 더러운 봉은 close=0 으로 update_bars 의 closes 필터에 걸려 제외됨.
        # ATR 자체는 _atr_pct 에서 prev_close 갱신 안 되는 봉이므로 전체 trs 가 부족할 수 있다.
        # 어떤 경우든 예외 없이 None 또는 양수.
        if ind.atr_pct is not None:
            self.assertGreater(ind.atr_pct, 0.0)


if __name__ == "__main__":
    unittest.main()
