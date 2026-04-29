"""scoring.build_dante_entry_features 단위 테스트.

Phase A 의 학습 트랙 피처 추출이 다음 케이스에서 안정적으로 동작하는지 검증한다:
  - 풍부한 데이터(5분봉/1분봉/breakout_high) 가 모두 있는 정상 케이스
  - 5분봉 캐시가 비어있는 케이스(env_upper_13/bb_upper_55 = None)
  - breakout_high == 0 인 1차 진입 시점(눌림 깊이 0 기본값)
  - 1분봉이 비어있는 케이스(neg_streak/cur_positive 0)
  - 음봉 스트리크 카운트가 양봉을 만나면 멈춰야 하는 패턴

실행:
    .\\venv64\\Scripts\\python.exe -m unittest test_dante_features -v
"""

from __future__ import annotations

import unittest

from bars import MinuteBar
import scoring


def make_bar(*, open_: int, close: int, high: int = 0, low: int = 0, ts: float = 0.0) -> MinuteBar:
    return MinuteBar(
        minute_start=int(ts // 60) * 60,
        open=open_,
        high=high or max(open_, close),
        low=low or min(open_, close),
        close=close,
        volume=100,
        received_at=ts,
    )


class BuildDanteFeaturesTests(unittest.TestCase):
    def test_full_feature_extraction(self):
        bars = [
            make_bar(open_=10_000, close=10_080, ts=1_000),  # 양봉
            make_bar(open_=10_080, close=10_050, ts=1_060),  # 음봉
            make_bar(open_=10_050, close=10_020, ts=1_120),  # 음봉
            make_bar(open_=10_020, close=10_060, ts=1_180),  # 진행봉(양봉)
        ]
        f = scoring.build_dante_entry_features(
            current_price=10_060,
            chejan_strength=125.5,
            volume_speed=1_200.0,
            spread_rate=0.0015,
            obs_elapsed_sec=42.0,
            env_upper_13=10_000,
            bb_upper_55=9_950,
            five_min_closes_count=60,
            breakout_high=10_120,
            minute_bars=bars,
        )
        self.assertAlmostEqual(f["chejan_strength"], 125.5)
        self.assertAlmostEqual(f["volume_speed"], 1_200.0)
        self.assertAlmostEqual(f["spread_rate"], 0.0015)
        self.assertAlmostEqual(f["obs_elapsed_sec"], 42.0)
        self.assertAlmostEqual(f["px_over_env13_pct"], 10_060 / 10_000 - 1)
        self.assertAlmostEqual(f["px_over_bb55_pct"], 10_060 / 9_950 - 1)
        self.assertEqual(f["five_min_closes_count"], 60.0)
        self.assertAlmostEqual(f["pullback_pct_from_high"], (10_120 - 10_060) / 10_120)
        self.assertEqual(f["neg_bars_streak"], 2.0)  # 진행봉 직전 2개 음봉
        self.assertEqual(f["cur_bar_is_positive"], 1.0)
        # 모든 피처가 정의된 헤더 그대로 채워졌는지
        self.assertEqual(set(f.keys()), set(scoring.DANTE_ENTRY_FEATURE_NAMES))

    def test_zero_when_five_min_cache_missing(self):
        bars = [
            make_bar(open_=10_000, close=10_010, ts=1_000),
            make_bar(open_=10_010, close=10_020, ts=1_060),
        ]
        f = scoring.build_dante_entry_features(
            current_price=10_020,
            chejan_strength=110.0,
            volume_speed=800.0,
            spread_rate=0.002,
            obs_elapsed_sec=30.0,
            env_upper_13=None,
            bb_upper_55=None,
            five_min_closes_count=0,
            breakout_high=10_020,
            minute_bars=bars,
        )
        self.assertEqual(f["px_over_env13_pct"], 0.0)
        self.assertEqual(f["px_over_bb55_pct"], 0.0)
        self.assertEqual(f["five_min_closes_count"], 0.0)

    def test_zero_pullback_when_breakout_high_zero(self):
        bars = [make_bar(open_=10_000, close=10_010, ts=1_000)]
        f = scoring.build_dante_entry_features(
            current_price=10_010,
            chejan_strength=120.0,
            volume_speed=900.0,
            spread_rate=0.001,
            obs_elapsed_sec=10.0,
            env_upper_13=9_900,
            bb_upper_55=9_900,
            five_min_closes_count=20,
            breakout_high=0,  # 1차 진입 직전이라 아직 트래킹 안 됨
            minute_bars=bars,
        )
        self.assertEqual(f["pullback_pct_from_high"], 0.0)

    def test_no_minute_bars(self):
        f = scoring.build_dante_entry_features(
            current_price=10_000,
            chejan_strength=110.0,
            volume_speed=600.0,
            spread_rate=0.003,
            obs_elapsed_sec=5.0,
            env_upper_13=9_900,
            bb_upper_55=9_900,
            five_min_closes_count=10,
            breakout_high=0,
            minute_bars=[],
        )
        self.assertEqual(f["neg_bars_streak"], 0.0)
        self.assertEqual(f["cur_bar_is_positive"], 0.0)

    def test_neg_streak_stops_at_first_positive(self):
        # 음봉 → 양봉 → 음봉 → 진행봉(양봉)
        bars = [
            make_bar(open_=10_100, close=10_080, ts=1_000),  # 음봉
            make_bar(open_=10_080, close=10_120, ts=1_060),  # 양봉(streak 차단)
            make_bar(open_=10_120, close=10_100, ts=1_120),  # 음봉(진행봉 직전)
            make_bar(open_=10_100, close=10_140, ts=1_180),  # 진행봉(양봉)
        ]
        f = scoring.build_dante_entry_features(
            current_price=10_140,
            chejan_strength=120.0,
            volume_speed=900.0,
            spread_rate=0.001,
            obs_elapsed_sec=20.0,
            env_upper_13=10_000,
            bb_upper_55=10_000,
            five_min_closes_count=30,
            breakout_high=10_180,
            minute_bars=bars,
        )
        # 진행봉 직전 음봉 1개 후 양봉을 만나 카운트가 멈춤 → streak == 1
        self.assertEqual(f["neg_bars_streak"], 1.0)

    def test_cur_negative_bar_marks_zero_positive(self):
        bars = [
            make_bar(open_=10_000, close=10_050, ts=1_000),
            make_bar(open_=10_050, close=10_010, ts=1_060),  # 진행봉(음봉)
        ]
        f = scoring.build_dante_entry_features(
            current_price=10_010,
            chejan_strength=110.0,
            volume_speed=800.0,
            spread_rate=0.002,
            obs_elapsed_sec=15.0,
            env_upper_13=9_900,
            bb_upper_55=9_900,
            five_min_closes_count=20,
            breakout_high=10_080,
            minute_bars=bars,
        )
        self.assertEqual(f["cur_bar_is_positive"], 0.0)

    def test_negative_inputs_are_normalized(self):
        # obs_elapsed_sec 가 음수로 들어와도 0으로 떨어져야 한다(시계 역행 방어)
        f = scoring.build_dante_entry_features(
            current_price=10_000,
            chejan_strength=0,  # 데이터 미수신
            volume_speed=0,
            spread_rate=0,
            obs_elapsed_sec=-5.0,
            env_upper_13=0,  # 0 으로 들어오는 경우 px_over=0 이 되어야 함
            bb_upper_55=0,
            five_min_closes_count=0,
            breakout_high=0,
            minute_bars=[],
        )
        self.assertEqual(f["obs_elapsed_sec"], 0.0)
        self.assertEqual(f["px_over_env13_pct"], 0.0)
        self.assertEqual(f["px_over_bb55_pct"], 0.0)

    def test_breakout_grade_a_flag(self):
        f = scoring.build_dante_entry_features(
            current_price=10_000,
            chejan_strength=130.0,
            volume_speed=900.0,
            spread_rate=0.001,
            obs_elapsed_sec=20.0,
            env_upper_13=9_900,
            bb_upper_55=9_900,
            five_min_closes_count=60,
            breakout_high=10_050,
            minute_bars=[],
            is_breakout_zero_bar=True,
            is_breakout_prev_bar=False,
        )
        self.assertEqual(f["breakout_grade_a"], 1.0)
        self.assertEqual(f["breakout_grade_b"], 0.0)

    def test_breakout_grade_b_flag(self):
        f = scoring.build_dante_entry_features(
            current_price=10_000,
            chejan_strength=130.0,
            volume_speed=900.0,
            spread_rate=0.001,
            obs_elapsed_sec=20.0,
            env_upper_13=9_900,
            bb_upper_55=9_900,
            five_min_closes_count=60,
            breakout_high=10_050,
            minute_bars=[],
            is_breakout_zero_bar=False,
            is_breakout_prev_bar=True,
        )
        self.assertEqual(f["breakout_grade_a"], 0.0)
        self.assertEqual(f["breakout_grade_b"], 1.0)

    def test_breakout_grade_b_excluded_when_also_zero(self):
        # 0봉전도 돌파했으면 'A' 가 우선이고 B 플래그는 0 이어야 한다.
        f = scoring.build_dante_entry_features(
            current_price=10_000,
            chejan_strength=130.0,
            volume_speed=900.0,
            spread_rate=0.001,
            obs_elapsed_sec=20.0,
            env_upper_13=9_900,
            bb_upper_55=9_900,
            five_min_closes_count=60,
            breakout_high=10_050,
            minute_bars=[],
            is_breakout_zero_bar=True,
            is_breakout_prev_bar=True,
        )
        self.assertEqual(f["breakout_grade_a"], 1.0)
        self.assertEqual(f["breakout_grade_b"], 0.0)

    def test_chejan_strength_trend_positive(self):
        history = [100.0, 102.0, 105.0, 110.0, 112.0, 115.0]
        f = scoring.build_dante_entry_features(
            current_price=10_000,
            chejan_strength=115.0,
            volume_speed=900.0,
            spread_rate=0.001,
            obs_elapsed_sec=20.0,
            env_upper_13=9_900,
            bb_upper_55=9_900,
            five_min_closes_count=60,
            breakout_high=10_050,
            minute_bars=[],
            chejan_strength_history=history,
        )
        # tail_mean - head_mean > 0
        self.assertGreater(f["chejan_strength_trend"], 0)

    def test_chejan_strength_trend_negative(self):
        history = [115.0, 112.0, 108.0, 104.0, 100.0, 98.0]
        f = scoring.build_dante_entry_features(
            current_price=10_000,
            chejan_strength=98.0,
            volume_speed=900.0,
            spread_rate=0.001,
            obs_elapsed_sec=20.0,
            env_upper_13=9_900,
            bb_upper_55=9_900,
            five_min_closes_count=60,
            breakout_high=10_050,
            minute_bars=[],
            chejan_strength_history=history,
        )
        self.assertLess(f["chejan_strength_trend"], 0)

    def test_upper_wick_ratio_clamped(self):
        # 음수/1 초과 입력은 0~1 범위로 캡
        f_neg = scoring.build_dante_entry_features(
            current_price=10_000, chejan_strength=130.0, volume_speed=900.0,
            spread_rate=0.001, obs_elapsed_sec=20.0,
            env_upper_13=9_900, bb_upper_55=9_900,
            five_min_closes_count=60, breakout_high=10_050,
            minute_bars=[], upper_wick_ratio=-0.5,
        )
        f_over = scoring.build_dante_entry_features(
            current_price=10_000, chejan_strength=130.0, volume_speed=900.0,
            spread_rate=0.001, obs_elapsed_sec=20.0,
            env_upper_13=9_900, bb_upper_55=9_900,
            five_min_closes_count=60, breakout_high=10_050,
            minute_bars=[], upper_wick_ratio=2.0,
        )
        self.assertEqual(f_neg["upper_wick_ratio"], 0.0)
        self.assertEqual(f_over["upper_wick_ratio"], 1.0)

    def test_open_return_pass_through(self):
        f = scoring.build_dante_entry_features(
            current_price=11_000, chejan_strength=130.0, volume_speed=900.0,
            spread_rate=0.001, obs_elapsed_sec=20.0,
            env_upper_13=9_900, bb_upper_55=9_900,
            five_min_closes_count=60, breakout_high=11_050,
            minute_bars=[], open_return=0.085,
        )
        self.assertAlmostEqual(f["open_return"], 0.085)

    def test_all_15_features_present(self):
        f = scoring.build_dante_entry_features(
            current_price=10_000, chejan_strength=130.0, volume_speed=900.0,
            spread_rate=0.001, obs_elapsed_sec=20.0,
            env_upper_13=9_900, bb_upper_55=9_900,
            five_min_closes_count=60, breakout_high=10_050,
            minute_bars=[],
        )
        # 학습 헤더와 1:1 일치 — 추가/삭제 시 train 코드도 깨져야 한다.
        self.assertEqual(set(f.keys()), set(scoring.DANTE_ENTRY_FEATURE_NAMES))
        self.assertEqual(len(f), 15)


if __name__ == "__main__":
    unittest.main()
