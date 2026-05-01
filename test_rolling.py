"""review.rolling 단위 테스트.

기존 test_*.py 와 동일한 unittest 스타일을 따른다 (pytest 없이 실행 가능).

  python -m unittest test_rolling

정적 fixture: tests/fixtures/reviews/ — 5일치 동일 패턴(README 참조).
큰 표본/일관성 시나리오는 _make_synthetic_window() 헬퍼로 임시 디렉토리에
가공해 사용한다.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import tempfile
import unittest
from typing import Dict, List

from review import rolling


FIXTURES_DIR = os.path.join("tests", "fixtures", "reviews")


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------


def _read_fixture_rows() -> List[dict]:
    """fixture 5일치 거래를 한 리스트로 합쳐 반환."""
    dates = rolling.discover_review_dates(FIXTURES_DIR)
    return rolling.load_trade_rows(FIXTURES_DIR, dates)


def _make_synthetic_window(
    out_dir: str,
    n_days: int,
    per_day_pattern: List[Dict[str, float]],
    start_date: str = "2026-04-01",
) -> List[str]:
    """fixture 패턴(per_day_pattern)을 n_days 일에 걸쳐 깔아 둔다.

    per_day_pattern: 각 거래의 entry_class/exit_class/r_multiple/mfe_r/mae_r/
        be_violation/realized_return/give_back_r/over_run_r 등 dict.
    반환: 생성된 날짜 리스트(오름차순).
    """
    os.makedirs(out_dir, exist_ok=True)
    base_y, base_m, base_d = (int(x) for x in start_date.split("-"))
    from datetime import date, timedelta
    dates: List[str] = []
    cur = date(base_y, base_m, base_d)
    for _ in range(n_days):
        d = cur.strftime("%Y-%m-%d")
        dates.append(d)
        path = os.path.join(out_dir, f"trade_review_{d}.csv")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "date", "code", "name", "entry_class", "exit_class", "grade",
                "entry_stage_max", "entry_avg_price", "exit_avg_price",
                "entry_first_time", "exit_last_time", "hold_seconds",
                "realized_return", "r_multiple",
                "mfe", "mae", "mfe_r", "mae_r",
                "return_5m", "return_10m", "return_20m",
                "give_back_r", "over_run_r", "bounce_after_stop_r",
                "be_violation", "reached_1r", "reached_2r", "hit_stop", "time_exit",
                "open_return", "upper_wick_ratio", "px_over_bb55_pct",
                "chejan_strength", "volume_speed", "spread_rate",
                "reason", "exit_reason",
            ])
            for i, row in enumerate(per_day_pattern):
                writer.writerow([
                    d, f"X{i:04d}", "synth",
                    row.get("entry_class", "breakout_chase"),
                    row.get("exit_class", "clean_exit"),
                    row.get("grade", "A"),
                    row.get("entry_stage_max", 1),
                    10000, int(10000 * (1 + (row.get("realized_return") or 0))),
                    f"{d} 09:00:00", f"{d} 09:10:00", 600,
                    row.get("realized_return", 0.0),
                    row.get("r_multiple", 0.0),
                    "", "",
                    row.get("mfe_r", 0.0), row.get("mae_r", 0.0),
                    "", "", "",
                    row.get("give_back_r", ""), row.get("over_run_r", ""), "",
                    row.get("be_violation", 0.0),
                    row.get("reached_1r", 0), 0, 0, 0,
                    row.get("open_return", 0.0),
                    row.get("upper_wick_ratio", 0.0),
                    row.get("px_over_bb55_pct", 0.0),
                    180.0, 1500.0, 0.0015,
                    "synthetic", "synthetic",
                ])
        cur = cur + timedelta(days=1)
    return dates


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class DiscoverDatesTest(unittest.TestCase):

    def test_fixture_dates_in_order(self):
        dates = rolling.discover_review_dates(FIXTURES_DIR)
        self.assertEqual(dates, [
            "2026-04-21", "2026-04-22", "2026-04-23", "2026-04-24", "2026-04-25",
        ])

    def test_select_window_returns_last_n(self):
        dates = ["2026-04-21", "2026-04-22", "2026-04-23", "2026-04-24", "2026-04-25"]
        self.assertEqual(
            rolling.select_window_dates(dates, "2026-04-25", 3),
            ["2026-04-23", "2026-04-24", "2026-04-25"],
        )

    def test_select_window_caps_at_available(self):
        dates = ["2026-04-21", "2026-04-22"]
        self.assertEqual(
            rolling.select_window_dates(dates, "2026-04-25", 10),
            dates,
        )

    def test_select_window_excludes_future_dates(self):
        dates = ["2026-04-21", "2026-04-25", "2026-04-30"]
        self.assertEqual(
            rolling.select_window_dates(dates, "2026-04-25", 5),
            ["2026-04-21", "2026-04-25"],
        )


class AggregateWindowTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rows = _read_fixture_rows()

    def test_total_rows(self):
        self.assertEqual(len(self.rows), 25)

    def test_aggregate_overall_winrate(self):
        stats = rolling.aggregate_window(5, [], self.rows)
        # 승: clean_exit 5 + late_take 5 = 10 / 25 = 0.4
        self.assertAlmostEqual(stats.overall["win_rate"], 0.4, places=4)
        self.assertEqual(stats.overall["n"], 25)

    def test_aggregate_by_entry_class(self):
        stats = rolling.aggregate_window(5, [], self.rows)
        self.assertIn("breakout_chase", stats.by_entry)
        self.assertIn("first_pullback", stats.by_entry)
        self.assertEqual(stats.by_entry["breakout_chase"]["n"], 20)
        self.assertEqual(stats.by_entry["first_pullback"]["n"], 5)

    def test_aggregate_by_exit_class_bad_stop(self):
        stats = rolling.aggregate_window(5, [], self.rows)
        bad = stats.by_exit["bad_stop"]
        self.assertEqual(bad["n"], 10)        # 일별 2건 × 5일
        self.assertEqual(bad["win_rate"], 0.0)

    def test_aggregate_combo(self):
        stats = rolling.aggregate_window(5, [], self.rows)
        self.assertIn("breakout_chase|bad_stop", stats.by_combo)
        self.assertEqual(stats.by_combo["breakout_chase|bad_stop"]["n"], 10)

    def test_window_confidence_is_medium(self):
        stats = rolling.aggregate_window(5, [], self.rows)
        # n=25 → medium (20<=n<40)
        self.assertEqual(stats.confidence, "medium")


class CandidateEvaluationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rows = _read_fixture_rows()

    def test_break_even_cut_triggered(self):
        ev = rolling._eval_be_cut(self.rows)
        self.assertIsNotNone(ev)
        # be_violation 10건 / loser 15건
        self.assertEqual(ev["n"], 10)
        self.assertEqual(ev["total"], 15)
        self.assertAlmostEqual(ev["ratio"], 10 / 15, places=4)

    def test_take_profit_faster_triggered(self):
        ev = rolling._eval_take_faster(self.rows)
        self.assertIsNotNone(ev)
        self.assertEqual(ev["n"], 5)         # late_take 5건
        self.assertEqual(ev["total"], 10)    # winners 10건

    def test_block_fake_breakout_not_triggered(self):
        self.assertIsNone(rolling._eval_block_fake(self.rows))

    def test_apply_trailing_not_triggered(self):
        self.assertIsNone(rolling._eval_trailing(self.rows))

    def test_wait_for_pullback_triggered(self):
        # A 평균 R = (-0.5 -0.7 -1.0 +1.0 평균; 일별 값) → 음수
        # B 평균 R = +1.0 (전 일자)
        ev = rolling._eval_wait_pullback(self.rows)
        self.assertIsNotNone(ev)
        self.assertLess(ev["a_avg_r"], 0)
        self.assertGreater(ev["b_avg_r"], 0)


class ConfidenceTest(unittest.TestCase):

    def test_low(self):
        self.assertEqual(rolling._confidence_for_n(0), "low")
        self.assertEqual(rolling._confidence_for_n(19), "low")

    def test_medium(self):
        self.assertEqual(rolling._confidence_for_n(20), "medium")
        self.assertEqual(rolling._confidence_for_n(39), "medium")

    def test_high(self):
        self.assertEqual(rolling._confidence_for_n(40), "high")
        self.assertEqual(rolling._confidence_for_n(120), "high")


class RunRollingFixtureTest(unittest.TestCase):
    """fixture 디렉토리를 그대로 입력으로 넣었을 때 후보가 medium 으로 잡혀야 한다."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rolling_test_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _copy_fixtures(self):
        for name in os.listdir(FIXTURES_DIR):
            if name.startswith("trade_review_") or name.startswith("rule_overrides_"):
                shutil.copy(os.path.join(FIXTURES_DIR, name), self.tmp)

    def test_fixture_pipeline(self):
        self._copy_fixtures()
        result = rolling.run_rolling(
            as_of_date="2026-04-25",
            windows=(5, 10, 20),
            reviews_dir=self.tmp,
            write=True,
        )
        self.assertEqual(result.as_of_date, "2026-04-25")
        # 5d 윈도우 전체 거래 수 = 25
        ws5 = next(s for s in result.window_stats if s.window == 5)
        self.assertEqual(ws5.n_total, 25)

        rule_ids = {c.rule_id for c in result.candidates}
        # 의도된 룰 후보: be_cut + take_faster + wait_pullback
        self.assertIn("break_even_cut", rule_ids)
        self.assertIn("take_profit_faster", rule_ids)
        self.assertIn("wait_for_pullback", rule_ids)
        self.assertNotIn("block_fake_breakout", rule_ids)
        self.assertNotIn("apply_trailing", rule_ids)

        be = next(c for c in result.candidates if c.rule_id == "break_even_cut")
        # 5/10/20 모두 같은 fixture → consistent
        self.assertTrue(be.consistent_across_windows)
        # n_window_total=25 → medium 후보
        self.assertEqual(be.confidence, "medium")
        # auto_apply 는 항상 False (PR-A 가 아니므로)
        self.assertFalse(be.auto_apply)
        # proposed_overrides 는 review.overrides.Override 인스턴스 리스트(eval 미사용)
        from review.overrides import Override, validate_override
        self.assertGreater(len(be.proposed_overrides), 0)
        for ov in be.proposed_overrides:
            self.assertIsInstance(ov, Override)
            # whitelist 통과 가능해야 함
            validate_override(ov)
            self.assertTrue(ov.target.startswith("exit_strategy."))

        # 출력 파일이 떨어져야 함
        for path in result.output_paths.values():
            self.assertTrue(os.path.exists(path))

        # candidates JSON 의 글로벌 가드 키 확인 + 직렬화된 override 가 dict 형태
        with open(result.output_paths["candidates"], encoding="utf-8") as f:
            payload = json.load(f)
        self.assertTrue(payload["auto_apply_globally_disabled"])
        for cand in payload["candidates"]:
            for ov in cand["proposed_overrides"]:
                # 절대 문자열 표현식이 아니라 dict 여야 함
                self.assertIsInstance(ov, dict)
                self.assertIn("target", ov)
                self.assertIn("op", ov)


class HighConfidenceConsistentTest(unittest.TestCase):
    """40건 이상 + 5/10/20 모두 트리거 → high 후보 시나리오."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rolling_test_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_high_confidence_when_consistent(self):
        # 일별 5건, 20일치 = 100건. 일별 패턴은 fixture 와 동일하게 깔되,
        # be_violation 비율과 loser 패턴이 강해야 break_even_cut 이 매번 트리거됨.
        per_day = [
            {"entry_class": "breakout_chase", "exit_class": "bad_stop",
             "r_multiple": -0.5, "mfe_r": 1.5, "mae_r": -1.0,
             "be_violation": 1.0, "reached_1r": 1, "realized_return": -0.0075},
            {"entry_class": "breakout_chase", "exit_class": "bad_stop",
             "r_multiple": -0.7, "mfe_r": 2.0, "mae_r": -1.0,
             "be_violation": 1.0, "reached_1r": 1, "realized_return": -0.0105},
            {"entry_class": "breakout_chase", "exit_class": "good_stop",
             "r_multiple": -1.0, "mfe_r": 0.3, "mae_r": -1.0,
             "be_violation": 0.0, "reached_1r": 0, "realized_return": -0.015},
            {"entry_class": "breakout_chase", "exit_class": "clean_exit",
             "r_multiple": 1.0, "mfe_r": 1.5, "mae_r": -0.3,
             "be_violation": 0.0, "reached_1r": 1, "realized_return": 0.015},
            {"entry_class": "first_pullback", "exit_class": "late_take",
             "r_multiple": 1.0, "mfe_r": 3.0, "mae_r": -0.5,
             "be_violation": 0.0, "reached_1r": 1, "realized_return": 0.015,
             "give_back_r": 2.0, "over_run_r": 1.5},
        ]
        dates = _make_synthetic_window(self.tmp, n_days=20, per_day_pattern=per_day)
        as_of = dates[-1]

        result = rolling.run_rolling(
            as_of_date=as_of,
            windows=(5, 10, 20),
            reviews_dir=self.tmp,
            write=False,
        )
        # 20d 윈도우 전체 거래수 = 100 → high 후보 가능
        ws20 = next(s for s in result.window_stats if s.window == 20)
        self.assertEqual(ws20.n_total, 100)
        self.assertEqual(ws20.confidence, "high")

        be = next(c for c in result.candidates if c.rule_id == "break_even_cut")
        self.assertTrue(be.consistent_across_windows)
        self.assertEqual(be.confidence, "high")
        # 자동 적용은 항상 막혀야 함
        self.assertFalse(be.auto_apply)
        self.assertIn("PR-A", be.reason_no_apply)


class HighDowngradedToMediumTest(unittest.TestCase):
    """40건 이상이지만 일관성이 깨지면 medium 으로 강등된다."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rolling_test_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_downgrade_when_only_largest_window_triggers(self):
        # 첫 5일은 bad_stop 거의 없게(트리거 X), 이후 15일은 강하게 트리거.
        # 5d 윈도우는 트리거 안 함, 10d/20d 만 트리거 → consistent=False → medium 강등.
        clean = [
            {"entry_class": "breakout_chase", "exit_class": "clean_exit",
             "r_multiple": 1.0, "mfe_r": 1.2, "mae_r": -0.2,
             "be_violation": 0.0, "reached_1r": 1, "realized_return": 0.015},
        ] * 5
        bad = [
            {"entry_class": "breakout_chase", "exit_class": "bad_stop",
             "r_multiple": -0.7, "mfe_r": 2.0, "mae_r": -1.0,
             "be_violation": 1.0, "reached_1r": 1, "realized_return": -0.0105},
        ] * 5

        # day1~15: bad 패턴, day16~20: clean 패턴
        # → 5d 윈도우(day16~20) 는 loser 0건 → 트리거 X
        # → 10d 윈도우(day11~20) 는 loser 25건 중 25개 be → 트리거
        # → 20d 윈도우(day1~20) 도 트리거
        from datetime import date, timedelta
        os.makedirs(self.tmp, exist_ok=True)
        cur = date(2026, 4, 1)
        for i in range(20):
            d = cur.strftime("%Y-%m-%d")
            pattern = bad if i < 15 else clean
            _write_one_day(self.tmp, d, pattern)
            cur += timedelta(days=1)

        result = rolling.run_rolling(
            as_of_date=cur.strftime("%Y-%m-%d"),
            windows=(5, 10, 20),
            reviews_dir=self.tmp,
            write=False,
        )
        be = next((c for c in result.candidates if c.rule_id == "break_even_cut"), None)
        self.assertIsNotNone(be)
        self.assertFalse(be.consistent_across_windows)
        # 20d N=100 → high 자격이지만, consistent=False 라 medium 으로 강등
        self.assertEqual(be.confidence, "medium")


def _write_one_day(out_dir: str, date_str: str, rows: list) -> None:
    """단일 날짜 trade_review CSV 작성 헬퍼."""
    path = os.path.join(out_dir, f"trade_review_{date_str}.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "date", "code", "name", "entry_class", "exit_class", "grade",
            "entry_stage_max", "entry_avg_price", "exit_avg_price",
            "entry_first_time", "exit_last_time", "hold_seconds",
            "realized_return", "r_multiple",
            "mfe", "mae", "mfe_r", "mae_r",
            "return_5m", "return_10m", "return_20m",
            "give_back_r", "over_run_r", "bounce_after_stop_r",
            "be_violation", "reached_1r", "reached_2r", "hit_stop", "time_exit",
            "open_return", "upper_wick_ratio", "px_over_bb55_pct",
            "chejan_strength", "volume_speed", "spread_rate",
            "reason", "exit_reason",
        ])
        for i, row in enumerate(rows):
            writer.writerow([
                date_str, f"Y{i:04d}", "synth",
                row.get("entry_class", "breakout_chase"),
                row.get("exit_class", "clean_exit"),
                "A", 1, 10000,
                int(10000 * (1 + (row.get("realized_return") or 0))),
                f"{date_str} 09:00:00", f"{date_str} 09:10:00", 600,
                row.get("realized_return", 0.0),
                row.get("r_multiple", 0.0),
                "", "",
                row.get("mfe_r", 0.0), row.get("mae_r", 0.0),
                "", "", "",
                "", "", "",
                row.get("be_violation", 0.0),
                row.get("reached_1r", 0), 0, 0, 0,
                row.get("open_return", 0.0),
                row.get("upper_wick_ratio", 0.0),
                row.get("px_over_bb55_pct", 0.0),
                180.0, 1500.0, 0.0015,
                "synthetic", "synthetic",
            ])


def _write_day_with_classifier(out_dir: str, date_str: str, rows: List[Dict[str, object]]) -> None:
    """classifier_version 컬럼을 명시한 단일 날짜 trade_review CSV 작성 헬퍼."""
    path = os.path.join(out_dir, f"trade_review_{date_str}.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "date", "code", "name", "entry_class", "exit_class", "classifier_version",
            "grade", "entry_stage_max", "entry_avg_price", "exit_avg_price",
            "entry_first_time", "exit_last_time", "hold_seconds",
            "realized_return", "r_multiple",
            "mfe", "mae", "mfe_r", "mae_r",
            "return_5m", "return_10m", "return_20m",
            "give_back_r", "over_run_r", "bounce_after_stop_r",
            "be_violation", "reached_1r", "reached_2r", "hit_stop", "time_exit",
            "open_return", "upper_wick_ratio", "px_over_bb55_pct",
            "chejan_strength", "volume_speed", "spread_rate",
            "reason", "exit_reason",
        ])
        for i, row in enumerate(rows):
            writer.writerow([
                date_str, f"Z{i:04d}", "synth",
                row.get("entry_class", "breakout_chase"),
                row.get("exit_class", "clean_exit"),
                row.get("classifier_version", "v2"),
                "A", 1, 10000,
                int(10000 * (1 + (row.get("realized_return") or 0))),
                f"{date_str} 09:00:00", f"{date_str} 09:10:00", 600,
                row.get("realized_return", 0.0),
                row.get("r_multiple", 0.0),
                "", "",
                row.get("mfe_r", 0.0), row.get("mae_r", 0.0),
                "", "", "",
                "", "", "",
                row.get("be_violation", 0.0),
                row.get("reached_1r", 0), 0, 0, 0,
                row.get("open_return", 0.0),
                row.get("upper_wick_ratio", 0.0),
                row.get("px_over_bb55_pct", 0.0),
                180.0, 1500.0, 0.0015,
                "synthetic", "synthetic",
            ])


class ClassifierVersionFilteringTest(unittest.TestCase):
    """v1 fallback 거래가 후보 평가에 영향 안 주고 by_classifier_version 통계만 갱신해야 한다."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rolling_test_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_v1_rows_excluded_from_candidates(self):
        # v1 row 만으로 가짜돌파 30%+ 발생해도 후보가 안 떠야 한다.
        # block_fake_breakout 트리거 임계: fake_breakout_ratio >= 0.30 + 가짜돌파 n>=2.
        v1_rows = (
            [{"entry_class": "fake_breakout", "exit_class": "good_stop",
              "r_multiple": -1.0, "mfe_r": 0.2, "mae_r": -1.0,
              "realized_return": -0.015, "classifier_version": "v1"}] * 5
            + [{"entry_class": "breakout_chase", "exit_class": "clean_exit",
                "r_multiple": 1.0, "mfe_r": 1.5, "mae_r": -0.2,
                "realized_return": 0.015, "classifier_version": "v1"}] * 10
        )
        _write_day_with_classifier(self.tmp, "2026-04-25", v1_rows)
        result = rolling.run_rolling(
            as_of_date="2026-04-25",
            windows=(5,),
            reviews_dir=self.tmp,
            write=False,
        )
        # v1 만 들어 있으므로 후보 평가 대상 = 0 → 어떤 rule_id 도 트리거 안 됨
        self.assertEqual(len(result.candidates), 0)
        ws = result.window_stats[0]
        self.assertEqual(ws.n_total, 15)
        self.assertEqual(ws.n_candidate, 0)
        self.assertIn("v1", ws.by_classifier)
        self.assertEqual(ws.by_classifier["v1"]["n"], 15)
        self.assertNotIn("v2", ws.by_classifier)

    def test_v2_rows_drive_candidates_v1_only_in_stats(self):
        # 같은 날에 v2 가짜돌파 5건(트리거) + v1 정상 거래 50건(잡음).
        # 후보는 v2 만으로 평가되어야 트리거 + confidence=low (v2 n=15 미만 보장 위해 적게).
        v2_rows = (
            [{"entry_class": "fake_breakout", "exit_class": "good_stop",
              "r_multiple": -1.0, "mfe_r": 0.2, "mae_r": -1.0,
              "realized_return": -0.015, "classifier_version": "v2"}] * 5
            + [{"entry_class": "breakout_chase", "exit_class": "clean_exit",
                "r_multiple": 1.0, "mfe_r": 1.2, "mae_r": -0.2,
                "realized_return": 0.015, "classifier_version": "v2"}] * 10
        )
        v1_rows = (
            [{"entry_class": "breakout_chase", "exit_class": "clean_exit",
              "r_multiple": 1.0, "mfe_r": 1.5, "mae_r": -0.2,
              "realized_return": 0.015, "classifier_version": "v1"}] * 50
        )
        _write_day_with_classifier(self.tmp, "2026-04-25", v2_rows + v1_rows)
        result = rolling.run_rolling(
            as_of_date="2026-04-25",
            windows=(5,),
            reviews_dir=self.tmp,
            write=False,
        )
        ws = result.window_stats[0]
        self.assertEqual(ws.n_total, 65)
        self.assertEqual(ws.n_candidate, 15)
        self.assertEqual(ws.confidence, "low")  # v2 n=15 < 20
        # by_classifier_version 통계에는 v1/v2 양쪽 노출
        self.assertEqual(ws.by_classifier["v2"]["n"], 15)
        self.assertEqual(ws.by_classifier["v1"]["n"], 50)
        # 후보는 v2 표본만으로 트리거 — block_fake_breakout 가 잡혀야 함
        rule_ids = {c.rule_id for c in result.candidates}
        self.assertIn("block_fake_breakout", rule_ids)

    def test_blank_classifier_version_treated_as_v2(self):
        # 빈 문자열은 default v2 로 취급되어 후보 평가에 들어간다(legacy fixture 호환).
        rows = [
            {"entry_class": "fake_breakout", "exit_class": "good_stop",
             "r_multiple": -1.0, "mfe_r": 0.2, "mae_r": -1.0,
             "realized_return": -0.015, "classifier_version": ""},
        ] * 5 + [
            {"entry_class": "breakout_chase", "exit_class": "clean_exit",
             "r_multiple": 1.0, "mfe_r": 1.2, "mae_r": -0.2,
             "realized_return": 0.015, "classifier_version": ""},
        ] * 10
        _write_day_with_classifier(self.tmp, "2026-04-25", rows)
        result = rolling.run_rolling(
            as_of_date="2026-04-25",
            windows=(5,),
            reviews_dir=self.tmp,
            write=False,
        )
        ws = result.window_stats[0]
        self.assertEqual(ws.n_candidate, 15)  # 빈 값이 v2 로 카운트
        self.assertIn("v2", ws.by_classifier)


if __name__ == "__main__":
    unittest.main()
