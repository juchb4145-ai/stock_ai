"""market_state 단위 테스트.

실행:
    .\\venv64\\Scripts\\python.exe -m unittest test_market_state -v
"""

from __future__ import annotations

import unittest

import market_state as ms


def _ts(minute_offset: int, second: int = 0) -> float:
    """09:00:00 KST 가정의 단순 epoch — 분 경계 계산만 정확하면 충분."""
    base = 1_700_000_000  # 임의 고정 base. 분 경계 계산은 // 60 이라 base 의 분 정렬에 무관.
    base_minute = (base // 60) * 60
    return float(base_minute + minute_offset * 60 + second)


class IndexStateTests(unittest.TestCase):
    def test_first_tick_sets_open_and_high(self):
        st = ms.IndexState()
        st.update(2_500.0, _ts(0, 5))
        self.assertEqual(st.intraday_open, 2_500.0)
        self.assertEqual(st.intraday_high, 2_500.0)
        self.assertEqual(st.intraday_low, 2_500.0)
        self.assertEqual(st.last_price, 2_500.0)
        self.assertAlmostEqual(st.pct(), 0.0)
        self.assertAlmostEqual(st.drawdown_from_high(), 0.0)

    def test_pct_and_drawdown_after_swing(self):
        st = ms.IndexState()
        st.update(2_500.0, _ts(0))
        st.update(2_525.0, _ts(0, 30))   # 일중 고
        st.update(2_490.0, _ts(1))       # 하락
        self.assertAlmostEqual(st.pct(), 2_490 / 2_500 - 1)
        self.assertAlmostEqual(st.drawdown_from_high(), 2_490 / 2_525 - 1)

    def test_minute_bar_rollover_closes_progressing_bar(self):
        st = ms.IndexState()
        st.update(2_500.0, _ts(0, 10))
        st.update(2_510.0, _ts(0, 30))
        # 분 경계 통과 → 0분봉 closed, 1분봉 시작
        st.update(2_505.0, _ts(1, 5))
        self.assertEqual(len(st.minute_bars), 1)
        bar0 = st.minute_bars[0]
        self.assertEqual(bar0.open, 2_500.0)
        self.assertEqual(bar0.high, 2_510.0)
        self.assertEqual(bar0.close, 2_510.0)
        self.assertEqual(st.cur_open, 2_505.0)
        self.assertEqual(st.cur_close, 2_505.0)

    def test_slope_3m_uses_first_open_to_last_close(self):
        st = ms.IndexState()
        # 3개의 분봉 생성: open 2500 → close 2530 (3분 누적 +1.2%)
        st.update(2_500.0, _ts(0, 0))
        st.update(2_510.0, _ts(0, 30))
        st.update(2_512.0, _ts(1, 0))   # 새 분 시작
        st.update(2_520.0, _ts(1, 30))
        st.update(2_522.0, _ts(2, 0))
        st.update(2_530.0, _ts(2, 30))
        # 진행봉(2분봉) close=2530, 첫 봉(0분) open=2500
        slope = st.slope_3m()
        self.assertIsNotNone(slope)
        self.assertAlmostEqual(slope, 2_530 / 2_500 - 1)

    def test_slope_1m_only_progressing_bar(self):
        st = ms.IndexState()
        st.update(2_500.0, _ts(0, 0))
        st.update(2_525.0, _ts(0, 45))
        slope1 = st.slope_1m()
        self.assertAlmostEqual(slope1, 2_525 / 2_500 - 1)


class ClassifyRegimeTests(unittest.TestCase):
    def _snap(self, *, pct=None, slope_3m=None, drawdown=None):
        snap = ms.MarketSnapshot(
            market_pct=pct,
            market_slope_1m=None,
            market_slope_3m=slope_3m,
            market_drawdown_from_high=drawdown,
        )
        snap.market_regime = ms.classify_regime(snap)
        return snap

    def test_unknown_when_no_data(self):
        self.assertEqual(ms.classify_regime(ms.MarketSnapshot()), ms.REGIME_UNKNOWN)

    def test_strong_when_pct_up_and_slope_nonneg(self):
        snap = self._snap(pct=0.01, slope_3m=0.005)
        self.assertEqual(snap.market_regime, ms.REGIME_STRONG)

    def test_strong_with_slope_none(self):
        # slope_3m 미수신이어도 pct >= STRONG_PCT 면 strong (보조 신호 부재 허용)
        snap = self._snap(pct=0.008)
        self.assertEqual(snap.market_regime, ms.REGIME_STRONG)

    def test_strong_demoted_to_neutral_when_slope_negative(self):
        snap = self._snap(pct=0.008, slope_3m=-0.001)
        # pct 양호하지만 최근 slope 가 음수 → strong 아닌 neutral
        self.assertEqual(snap.market_regime, ms.REGIME_NEUTRAL)

    def test_neutral_when_small_moves(self):
        snap = self._snap(pct=0.001, slope_3m=0.0)
        self.assertEqual(snap.market_regime, ms.REGIME_NEUTRAL)

    def test_weak_when_pct_below_threshold(self):
        snap = self._snap(pct=-0.006)
        self.assertEqual(snap.market_regime, ms.REGIME_WEAK)

    def test_weak_when_slope_3m_below_threshold(self):
        # pct 자체는 작지만 최근 3분 누적 slope 가 -0.5% 이하면 weak
        snap = self._snap(pct=-0.001, slope_3m=-0.006)
        self.assertEqual(snap.market_regime, ms.REGIME_WEAK)

    def test_risk_off_when_pct_deep(self):
        snap = self._snap(pct=-0.02)
        self.assertEqual(snap.market_regime, ms.REGIME_RISK_OFF)

    def test_risk_off_when_drawdown_from_high_deep(self):
        # pct 는 weak 영역이지만 일중 고점 대비 -2% 이상 빠지면 risk_off
        snap = self._snap(pct=-0.008, drawdown=-0.025)
        self.assertEqual(snap.market_regime, ms.REGIME_RISK_OFF)


class MarketStateCacheTests(unittest.TestCase):
    def test_unknown_snapshot_when_empty(self):
        cache = ms.MarketStateCache()
        snap = cache.snapshot()
        self.assertEqual(snap.market_regime, ms.REGIME_UNKNOWN)
        self.assertIsNone(snap.market_pct)

    def test_unknown_kept_when_only_kosdaq_received(self):
        # KOSPI 가 없으면 unknown — KOSDAQ 만으로 분류하지 않는다(1차 PR 정책).
        cache = ms.MarketStateCache()
        cache.update(ms.KOSDAQ_CODE, 870.0, _ts(0))
        snap = cache.snapshot()
        self.assertEqual(snap.market_regime, ms.REGIME_UNKNOWN)

    def test_snapshot_reflects_kospi_strong_day(self):
        cache = ms.MarketStateCache()
        cache.update(ms.KOSPI_CODE, 2_500.0, _ts(0))
        cache.update(ms.KOSPI_CODE, 2_530.0, _ts(2, 30))  # +1.2%
        snap = cache.snapshot()
        self.assertEqual(snap.market_regime, ms.REGIME_STRONG)
        self.assertAlmostEqual(snap.market_pct, 2_530 / 2_500 - 1)

    def test_snapshot_reflects_kospi_risk_off_day(self):
        cache = ms.MarketStateCache()
        cache.update(ms.KOSPI_CODE, 2_500.0, _ts(0))
        cache.update(ms.KOSPI_CODE, 2_460.0, _ts(2, 30))  # -1.6%
        snap = cache.snapshot()
        self.assertEqual(snap.market_regime, ms.REGIME_RISK_OFF)

    def test_unknown_index_code_ignored(self):
        cache = ms.MarketStateCache()
        cache.update("999", 100.0, _ts(0))  # 등록 안 된 코드
        # KOSPI 는 여전히 비어 있어야 함
        self.assertEqual(cache.kospi().last_price, 0.0)


class SnapshotRowDictTests(unittest.TestCase):
    def test_row_dict_keys_match_field_names(self):
        snap = ms.MarketSnapshot(
            market_pct=0.001,
            market_slope_1m=0.0001,
            market_slope_3m=0.002,
            market_drawdown_from_high=-0.001,
            market_regime=ms.REGIME_NEUTRAL,
        )
        row = snap.as_row_dict()
        self.assertEqual(set(row.keys()), set(ms.SNAPSHOT_FIELD_NAMES))
        self.assertEqual(row["market_regime"], ms.REGIME_NEUTRAL)

    def test_none_fields_become_empty_string(self):
        # numeric None 이 ``"None"`` 문자열로 흘러 들어가면 분석 시 NaN 변환이 안 됨.
        snap = ms.MarketSnapshot()
        row = snap.as_row_dict()
        self.assertEqual(row["market_pct"], "")
        self.assertEqual(row["market_slope_1m"], "")
        self.assertEqual(row["market_drawdown_from_high"], "")
        # regime 만 라벨 디폴트로 채워짐
        self.assertEqual(row["market_regime"], ms.REGIME_UNKNOWN)


if __name__ == "__main__":
    unittest.main()
