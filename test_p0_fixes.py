"""P0 코드리뷰 수정 사항 회귀 방지 테스트.

각 P0 항목이 의도대로 동작하고, 향후 누군가 되돌리지 못하게 잠근다.

  python -m unittest test_p0_fixes
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import entry_strategy
import exit_strategy
from review import classifier as classifier_mod
from review import intraday as intraday_mod
from review import overrides as ov_mod


# ---------------------------------------------------------------------------
# 공통 헬퍼
# ---------------------------------------------------------------------------


_SNAPSHOT_TARGETS = [
    ("entry_strategy", "MAX_UPPER_WICK_RATIO", entry_strategy),
    ("entry_strategy", "DANTE_FIRST_ENTRY_RATIO", entry_strategy),
    ("exit_strategy", "EXIT_BE_R", exit_strategy),
    ("exit_strategy", "EXIT_PARTIAL_R", exit_strategy),
    ("exit_strategy", "EXIT_PARTIAL_RATIO", exit_strategy),
]


def _snapshot() -> Dict[str, float]:
    return {f"{m}.{n}": getattr(mod, n) for (m, n, mod) in _SNAPSHOT_TARGETS}


def _restore(snap: Dict[str, float]) -> None:
    for key, value in snap.items():
        m, n = key.split(".", 1)
        mod = {"entry_strategy": entry_strategy, "exit_strategy": exit_strategy}[m]
        setattr(mod, n, value)


def _make_candidate(
    overrides: List[dict],
    *,
    rule_id: str = "test_rule",
    confidence: str = "high",
    allow_auto_apply: bool = True,
) -> dict:
    return {
        "rule_id": rule_id,
        "title": rule_id,
        "confidence": confidence,
        "allow_auto_apply": allow_auto_apply,
        "consistent_across_windows": True,
        "n_largest_window": 50,
        "auto_apply": False,
        "proposed_overrides": overrides,
    }


# ---------------------------------------------------------------------------
# P0 #5 — dry_run 에서도 일일 한도 적용 (운영자 예측 가능성)
# ---------------------------------------------------------------------------


class P0_5_DryRunDailyLimitTest(unittest.TestCase):

    def setUp(self):
        self.snap = _snapshot()

    def tearDown(self):
        _restore(self.snap)

    def test_dry_run_also_marks_exceeded_limit(self):
        # 6개 후보 + 한도 2 → 4개가 exceeded_daily_limit 마킹되어야 함
        cands = [
            _make_candidate([{
                "target": "exit_strategy.EXIT_PARTIAL_R", "op": "increment",
                "by": 0.01 * (i + 1),
            }], rule_id=f"r{i}")
            for i in range(6)
        ]
        result = ov_mod.preview_overrides(
            {"candidates": cands}, mode="dry_run", max_daily_rule_changes=2,
        )
        skipped = [e for e in result if e["skipped_reason"] == "exceeded_daily_limit"]
        eligible = [e for e in result if not e["skipped_reason"]]
        self.assertEqual(len(eligible), 2)
        self.assertEqual(len(skipped), 4)

    def test_dry_run_and_commit_have_same_limit_behavior(self):
        cands = [
            _make_candidate([{
                "target": "exit_strategy.EXIT_PARTIAL_R", "op": "increment",
                "by": 0.05 * (i + 1),
            }], rule_id=f"r{i}")
            for i in range(5)
        ]
        # 같은 후보를 두 모드로 평가했을 때 한도 적용 결과(eligible 수)가 같아야 함
        dry = ov_mod.preview_overrides(
            {"candidates": cands}, mode="dry_run", max_daily_rule_changes=3,
        )
        com = ov_mod.preview_overrides(
            {"candidates": cands}, mode="commit", max_daily_rule_changes=3,
        )
        dry_eligible = sum(1 for e in dry if not e["skipped_reason"])
        com_eligible = sum(1 for e in com if not e["skipped_reason"])
        self.assertEqual(dry_eligible, com_eligible)


# ---------------------------------------------------------------------------
# P0 #4 — commit_overrides 에서 confidence/approval 재검증 (2단계 방어)
# ---------------------------------------------------------------------------


class P0_4_CommitDoubleGateTest(unittest.TestCase):

    def setUp(self):
        self.snap = _snapshot()

    def tearDown(self):
        _restore(self.snap)

    def test_commit_blocks_low_confidence_even_if_preview_state_says_ok(self):
        """preview entry 가 외부에서 조작되어 skipped_reason='' 이지만 confidence=low 일 때.

        commit_overrides 가 함수 차원에서 한 번 더 차단해야 한다.
        """
        original = getattr(exit_strategy, "EXIT_BE_R")
        # 강제로 commit 가능 상태처럼 만들기 (외부 오용 시뮬레이션)
        forged_entry = {
            "target": "exit_strategy.EXIT_BE_R",
            "op": "decrement",
            "old_value": original,
            "new_value": original - 0.3,
            "confidence": "low",         # ← low 임에도 불구하고
            "allow_auto_apply": True,
            "validation_status": "ok",
            "skipped_reason": "",         # ← 비어 있음
            "applied": False,
            "rule_hash": "x",
            "source_rule": "forged",
            "classifier_version_before": "v2",
            "classifier_version_after": "v2",
        }
        result = ov_mod.commit_overrides([forged_entry], mode="commit")
        self.assertFalse(result[0]["applied"])
        self.assertEqual(result[0]["skipped_reason"], "confidence_below_high")
        self.assertEqual(getattr(exit_strategy, "EXIT_BE_R"), original)

    def test_commit_blocks_not_approved(self):
        original = getattr(exit_strategy, "EXIT_BE_R")
        forged_entry = {
            "target": "exit_strategy.EXIT_BE_R",
            "op": "decrement",
            "old_value": original,
            "new_value": original - 0.3,
            "confidence": "high",
            "allow_auto_apply": False,    # ← 승인 없음
            "validation_status": "ok",
            "skipped_reason": "",
            "applied": False,
            "rule_hash": "x",
            "source_rule": "forged",
            "classifier_version_before": "v2",
            "classifier_version_after": "v2",
        }
        result = ov_mod.commit_overrides([forged_entry], mode="commit")
        self.assertFalse(result[0]["applied"])
        self.assertEqual(result[0]["skipped_reason"], "not_approved")
        self.assertEqual(getattr(exit_strategy, "EXIT_BE_R"), original)

    def test_commit_passes_when_both_gates_ok(self):
        original = getattr(exit_strategy, "EXIT_BE_R")
        cand = _make_candidate([{
            "target": "exit_strategy.EXIT_BE_R", "op": "decrement", "by": 0.3,
        }])
        preview = ov_mod.preview_overrides({"candidates": [cand]}, mode="commit")
        result = ov_mod.commit_overrides(preview, mode="commit")
        self.assertTrue(result[0]["applied"])
        self.assertAlmostEqual(getattr(exit_strategy, "EXIT_BE_R"), original - 0.3)


# ---------------------------------------------------------------------------
# P0 #2 — _ret_after 의 window 길이 엄격화 (거짓 0% 메트릭 방지)
# ---------------------------------------------------------------------------


class P0_2_RetAfterStrictWindowTest(unittest.TestCase):

    def _bars(self, count: int):
        # 09:00 부터 1분 단위로 count 개. 가격은 +1 씩 증가.
        return [
            intraday_mod.Bar(
                dt=datetime(2026, 4, 30, 9, i, 0),
                open=10000 + i, high=10005 + i, low=9995 + i,
                close=10000 + i, volume=1000,
            )
            for i in range(count)
        ]

    def test_short_window_returns_none_not_zero(self):
        # 진입봉(09:00) + 후행 1봉(09:01) 만 있으니 return_3m 은 None 이어야 함
        bars = self._bars(2)
        out = intraday_mod.compute_intraday_metrics(
            datetime(2026, 4, 30, 9, 0, 30), entry_price=10000.0, bars=bars,
        )
        self.assertIsNone(out["return_3m"])
        self.assertIsNone(out["max_profit_3m"])
        self.assertIsNone(out["max_drawdown_3m"])

    def test_exact_window_returns_value(self):
        # 진입봉 + 후행 3봉 = 총 4개 → return_3m 산출
        bars = self._bars(4)
        out = intraday_mod.compute_intraday_metrics(
            datetime(2026, 4, 30, 9, 0, 30), entry_price=10000.0, bars=bars,
        )
        self.assertIsNotNone(out["return_3m"])
        # close at 09:03 = 10003 → return = 0.0003
        self.assertAlmostEqual(out["return_3m"], 0.0003, places=6)


# ---------------------------------------------------------------------------
# P0 #1 — _bar_at_or_after 가 분 시작/종료 형식 모두 지원
# ---------------------------------------------------------------------------


class P0_1_BarMatchingBothTimeFormatsTest(unittest.TestCase):

    def test_minute_start_format(self):
        # bar.dt 가 분 시작(09:06:00 = 09:06~09:07 봉) 형식
        bars = [
            intraday_mod.Bar(
                dt=datetime(2026, 4, 30, 9, m, 0),
                open=100, high=100, low=100, close=100, volume=1,
            )
            for m in range(0, 10)
        ]
        idx = intraday_mod._bar_at_or_after(bars, datetime(2026, 4, 30, 9, 6, 50))
        self.assertEqual(idx, 6)

    def test_minute_end_format(self):
        # bar.dt 가 분 종료 형식 (09:01:00 = 09:00:00~09:01:00 봉) — 분 시작 형식
        # 으로 매칭되는 봉이 *없는* 상황을 만들어 분 종료 매칭이 발동하는지 본다.
        bars = [
            intraday_mod.Bar(
                dt=datetime(2026, 4, 30, 9, m, 0),
                open=100, high=100, low=100, close=100, volume=1,
            )
            for m in range(1, 11)   # 09:01, 09:02, ..., 09:10
        ]
        # 진입 09:00:50 → minute_start=09:00:00(없음), minute_end=09:01:00(=bars[0])
        idx = intraday_mod._bar_at_or_after(bars, datetime(2026, 4, 30, 9, 0, 50))
        self.assertEqual(idx, 0)
        self.assertEqual(bars[idx].dt, datetime(2026, 4, 30, 9, 1, 0))


# ---------------------------------------------------------------------------
# P0 #3 — entry_stage_max=0 거래 폴백 (1분봉 있으면 breakout_chase)
# ---------------------------------------------------------------------------


class P0_3_StageZeroFallbackTest(unittest.TestCase):
    """dante 매칭 실패해서 grade='' / entry_stage_max=0 인 거래의 폴백 정책."""

    def _make_trade(self, *, metric_source: Optional[str] = None):
        from review.loader import Trade
        t = Trade(date="2026-04-30", code="999999", name="test")
        t.grade = ""
        t.entry_stage_max = 0
        t.entry_qty = 1
        t.entry_notional = 10000
        t.exit_qty = 1
        t.exit_notional = 10100
        t.entry_first_time = datetime(2026, 4, 30, 9, 10, 0)
        t.exit_last_time = datetime(2026, 4, 30, 9, 30, 0)
        t.realized_return = 0.01
        t.metrics["mfe_r"] = 1.0
        t.metrics["mae_r"] = -0.3
        if metric_source is not None:
            t.metrics["metric_source"] = metric_source
        return t

    def test_with_intraday_falls_back_to_breakout_chase(self):
        trade = self._make_trade(metric_source="kiwoom_1m_csv")
        result = classifier_mod._classify_entry(trade)
        self.assertEqual(result, "breakout_chase")

    def test_without_intraday_stays_unclassified(self):
        trade = self._make_trade(metric_source=None)
        result = classifier_mod._classify_entry(trade)
        self.assertEqual(result, "unclassified")

    def test_fallback_5m_does_not_fall_back(self):
        # fallback 메트릭만 있으면 1분봉이 없는 셈이라 unclassified 유지
        trade = self._make_trade(metric_source="fallback_5m_approx")
        result = classifier_mod._classify_entry(trade)
        self.assertEqual(result, "unclassified")


# ---------------------------------------------------------------------------
# P0 #6 — apply_overrides.py 가 fixture_hook 을 자동 부착 (구조 검증)
# ---------------------------------------------------------------------------


class P0_6_CliFixtureHookDefaultTest(unittest.TestCase):

    def test_apply_overrides_module_has_fixture_hook_helpers(self):
        """apply_overrides.py 가 _make_fixture_hook 함수와 DEFAULT_FIXTURE_TESTS 상수를 export 한다."""
        import apply_overrides
        self.assertTrue(hasattr(apply_overrides, "_make_fixture_hook"))
        self.assertTrue(hasattr(apply_overrides, "DEFAULT_FIXTURE_TESTS"))
        self.assertEqual(apply_overrides.DEFAULT_FIXTURE_TESTS, "test_classifier")

    def test_no_fixture_test_flag_in_argparse(self):
        import apply_overrides
        ns = apply_overrides._parse_args(["2026-04-30", "--commit", "--no-fixture-test"])
        self.assertTrue(ns.no_fixture_test)
        self.assertTrue(ns.commit)


# ---------------------------------------------------------------------------
# P0 #7 — fetch_minute_bars.py 의 페이지 정렬 명시 (구조 검증)
# ---------------------------------------------------------------------------


class P0_7_FetchPageSortIsExplicitTest(unittest.TestCase):
    """fetch 가 매 페이지 응답 후 self.rows 를 명시적으로 정렬한다."""

    def test_fetch_default_max_pages(self):
        import inspect
        import fetch_minute_bars
        sig = inspect.signature(fetch_minute_bars._KiwoomMinuteFetcher.fetch)
        # max_pages 기본값이 8 로 늘어났는지 확인 (페이지 부족 방지)
        self.assertEqual(sig.parameters["max_pages"].default, 8)

    def test_source_contains_explicit_sort(self):
        with open(os.path.join("fetch_minute_bars.py"), encoding="utf-8") as f:
            src = f.read()
        # 페이지 응답 후 명시적 정렬이 들어 있는지 (문자열 검사)
        self.assertIn("self.rows.sort", src)


if __name__ == "__main__":
    unittest.main()
