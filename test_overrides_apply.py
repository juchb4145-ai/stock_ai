"""review.overrides 응용 레이어(PR-A) 단위 테스트.

핵심 안전성 보장:
  - dry_run 모드는 절대 setattr 하지 않는다
  - commit 모드여도 confidence != high 또는 allow_auto_apply=false 면 skip
  - 변경 개수 > max_daily_rule_changes 면 초과분 skip
  - target whitelist 외, 타입 불일치, 값 동일은 모두 skip
  - fixture_hook 가 False 면 같은 batch 내 모든 setattr rollback
  - 모듈 상수가 테스트 사이에 새지 않게 setUp/tearDown 으로 복원

  python -m unittest test_overrides_apply
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from typing import Dict, List

import entry_strategy
import exit_strategy
from review import classifier as classifier_mod
from review import overrides as ov_mod


# ---------------------------------------------------------------------------
# 헬퍼: 모듈 상수 backup/restore + 후보 JSON 빌더
# ---------------------------------------------------------------------------


_TARGETS_TO_TRACK = [
    ("entry_strategy", "MAX_UPPER_WICK_RATIO", entry_strategy),
    ("entry_strategy", "OVERHEATED_OPEN_RETURN", entry_strategy),
    ("entry_strategy", "DANTE_FIRST_ENTRY_RATIO", entry_strategy),
    ("exit_strategy", "EXIT_BE_R", exit_strategy),
    ("exit_strategy", "EXIT_PARTIAL_R", exit_strategy),
    ("exit_strategy", "EXIT_PARTIAL_RATIO", exit_strategy),
]


def _snapshot() -> Dict[str, float]:
    return {f"{m}.{n}": getattr(mod, n) for (m, n, mod) in _TARGETS_TO_TRACK}


def _restore(snap: Dict[str, float]) -> None:
    for key, value in snap.items():
        m, n = key.split(".", 1)
        mod = {"entry_strategy": entry_strategy, "exit_strategy": exit_strategy}[m]
        setattr(mod, n, value)


def _make_candidate(
    rule_id: str,
    overrides: List[dict],
    *,
    confidence: str = "high",
    allow_auto_apply: bool = True,
    consistent: bool = True,
    n_largest: int = 50,
) -> dict:
    return {
        "rule_id": rule_id,
        "title": rule_id,
        "confidence": confidence,
        "allow_auto_apply": allow_auto_apply,
        "consistent_across_windows": consistent,
        "n_largest_window": n_largest,
        "auto_apply": False,
        "proposed_overrides": overrides,
    }


def _payload(candidates: List[dict], source_file: str = "synthetic.json") -> dict:
    return {"candidates": candidates}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class PreviewModeTest(unittest.TestCase):
    """preview_overrides 가 절대 setattr 하지 않는다 + skipped_reason 정확."""

    def setUp(self):
        self.snap = _snapshot()

    def tearDown(self):
        _restore(self.snap)

    def test_dry_run_skipped_reason_empty_when_valid(self):
        cand = _make_candidate("r1", [{
            "target": "exit_strategy.EXIT_PARTIAL_R",
            "op": "decrement", "by": 0.5, "reason": "test",
        }])
        result = ov_mod.preview_overrides(_payload([cand]), mode="dry_run")
        self.assertEqual(len(result), 1)
        e = result[0]
        self.assertEqual(e["validation_status"], "ok")
        self.assertEqual(e["skipped_reason"], "")
        self.assertEqual(e["applied"], False)
        # 모듈 상수는 그대로
        self.assertEqual(getattr(exit_strategy, "EXIT_PARTIAL_R"), self.snap["exit_strategy.EXIT_PARTIAL_R"])

    def test_commit_mode_skipped_when_low_confidence(self):
        cand = _make_candidate("r1", [{
            "target": "exit_strategy.EXIT_PARTIAL_R", "op": "decrement", "by": 0.5,
        }], confidence="low")
        result = ov_mod.preview_overrides(_payload([cand]), mode="commit")
        self.assertEqual(result[0]["skipped_reason"], "confidence_below_high")

    def test_commit_mode_skipped_when_not_approved(self):
        cand = _make_candidate("r1", [{
            "target": "exit_strategy.EXIT_PARTIAL_R", "op": "decrement", "by": 0.5,
        }], allow_auto_apply=False)
        result = ov_mod.preview_overrides(_payload([cand]), mode="commit")
        self.assertEqual(result[0]["skipped_reason"], "not_approved")

    def test_validation_failed_for_whitelist_miss(self):
        cand = _make_candidate("r1", [{
            "target": "strategy.NOT_EXIST", "op": "set", "value": 1.0,
        }])
        result = ov_mod.preview_overrides(_payload([cand]), mode="dry_run")
        self.assertEqual(result[0]["validation_status"], "failed")
        self.assertEqual(result[0]["skipped_reason"], "validation_failed")

    def test_no_change_when_value_matches_current(self):
        current = getattr(exit_strategy, "EXIT_PARTIAL_R")
        cand = _make_candidate("r1", [{
            "target": "exit_strategy.EXIT_PARTIAL_R", "op": "set", "value": current,
        }])
        result = ov_mod.preview_overrides(_payload([cand]), mode="dry_run")
        self.assertEqual(result[0]["skipped_reason"], "no_change")

    def test_max_daily_limit_caps_eligible(self):
        # 6개 candidate, max=2 → 4개 skip (exceeded_daily_limit)
        cands = []
        for i in range(6):
            cands.append(_make_candidate(f"r{i}", [{
                "target": "exit_strategy.EXIT_PARTIAL_R",
                "op": "increment", "by": 0.01 * (i + 1),
            }]))
        result = ov_mod.preview_overrides(_payload(cands), mode="commit",
                                          max_daily_rule_changes=2)
        skipped = [e for e in result if e["skipped_reason"] == "exceeded_daily_limit"]
        eligible = [e for e in result if not e["skipped_reason"]]
        self.assertEqual(len(eligible), 2)
        self.assertEqual(len(skipped), 4)


class CommitModeTest(unittest.TestCase):
    """commit_overrides 가 setattr 를 정확히 수행하고 dry_run 은 setattr 하지 않는다."""

    def setUp(self):
        self.snap = _snapshot()

    def tearDown(self):
        _restore(self.snap)

    def test_dry_run_never_setattrs(self):
        cand = _make_candidate("r1", [{
            "target": "exit_strategy.EXIT_PARTIAL_R", "op": "decrement", "by": 0.5,
        }])
        preview = ov_mod.preview_overrides(_payload([cand]), mode="dry_run")
        ov_mod.commit_overrides(preview, mode="dry_run")
        self.assertEqual(getattr(exit_strategy, "EXIT_PARTIAL_R"),
                         self.snap["exit_strategy.EXIT_PARTIAL_R"])

    def test_commit_setattrs_and_marks_applied(self):
        original = getattr(exit_strategy, "EXIT_PARTIAL_R")
        cand = _make_candidate("r1", [{
            "target": "exit_strategy.EXIT_PARTIAL_R", "op": "decrement", "by": 0.5,
        }])
        preview = ov_mod.preview_overrides(_payload([cand]), mode="commit")
        result = ov_mod.commit_overrides(preview, mode="commit")
        self.assertTrue(result[0]["applied"])
        self.assertEqual(getattr(exit_strategy, "EXIT_PARTIAL_R"), original - 0.5)

    def test_commit_skips_low_confidence(self):
        original = getattr(exit_strategy, "EXIT_BE_R")
        cand = _make_candidate("r1", [{
            "target": "exit_strategy.EXIT_BE_R", "op": "set", "value": 0.7,
        }], confidence="low")
        preview = ov_mod.preview_overrides(_payload([cand]), mode="commit")
        ov_mod.commit_overrides(preview, mode="commit")
        self.assertEqual(getattr(exit_strategy, "EXIT_BE_R"), original)

    def test_commit_skips_when_not_approved(self):
        original = getattr(exit_strategy, "EXIT_BE_R")
        cand = _make_candidate("r1", [{
            "target": "exit_strategy.EXIT_BE_R", "op": "set", "value": 0.7,
        }], allow_auto_apply=False)
        preview = ov_mod.preview_overrides(_payload([cand]), mode="commit")
        ov_mod.commit_overrides(preview, mode="commit")
        self.assertEqual(getattr(exit_strategy, "EXIT_BE_R"), original)


class FixtureRollbackTest(unittest.TestCase):
    """fixture_hook 가 False 면 commit 한 모든 변경이 rollback 되어야 한다."""

    def setUp(self):
        self.snap = _snapshot()

    def tearDown(self):
        _restore(self.snap)

    def test_rollback_when_hook_returns_false(self):
        original = getattr(exit_strategy, "EXIT_PARTIAL_R")
        cand = _make_candidate("r1", [{
            "target": "exit_strategy.EXIT_PARTIAL_R", "op": "decrement", "by": 0.5,
        }])
        preview = ov_mod.preview_overrides(_payload([cand]), mode="commit")
        result = ov_mod.commit_overrides(preview, mode="commit",
                                         fixture_hook=lambda: False)
        # rollback 되어 원복
        self.assertEqual(getattr(exit_strategy, "EXIT_PARTIAL_R"), original)
        self.assertFalse(result[0]["applied"])
        self.assertEqual(result[0]["skipped_reason"], "fixture_failed")

    def test_no_rollback_when_hook_returns_true(self):
        original = getattr(exit_strategy, "EXIT_PARTIAL_R")
        cand = _make_candidate("r1", [{
            "target": "exit_strategy.EXIT_PARTIAL_R", "op": "decrement", "by": 0.5,
        }])
        preview = ov_mod.preview_overrides(_payload([cand]), mode="commit")
        result = ov_mod.commit_overrides(preview, mode="commit",
                                         fixture_hook=lambda: True)
        self.assertEqual(getattr(exit_strategy, "EXIT_PARTIAL_R"), original - 0.5)
        self.assertTrue(result[0]["applied"])

    def test_hook_exception_triggers_rollback(self):
        original = getattr(exit_strategy, "EXIT_PARTIAL_R")
        cand = _make_candidate("r1", [{
            "target": "exit_strategy.EXIT_PARTIAL_R", "op": "decrement", "by": 0.5,
        }])

        def raising_hook():
            raise RuntimeError("simulated test failure")

        preview = ov_mod.preview_overrides(_payload([cand]), mode="commit")
        result = ov_mod.commit_overrides(preview, mode="commit",
                                         fixture_hook=raising_hook)
        self.assertEqual(getattr(exit_strategy, "EXIT_PARTIAL_R"), original)
        self.assertEqual(result[0]["skipped_reason"], "fixture_failed")


class LoadRuleCandidatesTest(unittest.TestCase):
    """rule_candidates_*.json 우선, 없으면 rule_overrides_*.json 으로 fallback."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ovapply_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, name: str, payload: dict) -> str:
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        return path

    def test_rolling_preferred(self):
        rolling_payload = {"candidates": [{"rule_id": "rolling_x"}]}
        self._write("rule_candidates_20260430.json", rolling_payload)
        daily_payload = {"proposed_overrides": [], "evidence": []}
        self._write("rule_overrides_2026-04-30.json", daily_payload)
        result = ov_mod.load_rule_candidates(self.tmp, "2026-04-30")
        self.assertEqual(result["schema"], "rolling_v1")
        self.assertEqual(result["candidates"][0]["rule_id"], "rolling_x")

    def test_daily_fallback_flatten(self):
        daily_payload = {
            "proposed_overrides": [
                {"target": "exit_strategy.EXIT_BE_R", "op": "set", "value": 0.7,
                 "source_rule": "break_even_cut"},
            ],
            "evidence": [{"rule": "break_even_cut", "title": "BE", "confidence": "medium"}],
        }
        self._write("rule_overrides_2026-04-30.json", daily_payload)
        result = ov_mod.load_rule_candidates(self.tmp, "2026-04-30")
        self.assertEqual(result["schema"], "daily_v1")
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["candidates"][0]["rule_id"], "break_even_cut")
        self.assertEqual(result["candidates"][0]["confidence"], "medium")
        # daily fallback 은 allow_auto_apply 가 안전 기본값(false) 이어야 함
        self.assertFalse(result["candidates"][0]["allow_auto_apply"])

    def test_missing_raises(self):
        with self.assertRaises(FileNotFoundError):
            ov_mod.load_rule_candidates(self.tmp, "2026-04-30")


class AuditLogShapeTest(unittest.TestCase):
    """audit JSON 이 13개 필드 모두 갖추고 있어야 한다."""

    def setUp(self):
        self.snap = _snapshot()
        self.tmp = tempfile.mkdtemp(prefix="ovaudit_")

    def tearDown(self):
        _restore(self.snap)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_audit_fields_present(self):
        cand = _make_candidate("r1", [{
            "target": "exit_strategy.EXIT_PARTIAL_R", "op": "decrement", "by": 0.5,
            "reason": "테스트",
        }])
        preview = ov_mod.preview_overrides(_payload([cand]), mode="dry_run")
        path = ov_mod.write_applied_overrides_log(
            preview, date="2026-04-30", mode="dry_run",
            source_file="synthetic.json", log_dir=self.tmp,
        )
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["schema"], "applied_overrides_v1")
        entry = payload["entries"][0]
        for key in (
            "date", "mode", "source_file",
            "target", "old_value", "new_value", "op",
            "confidence", "reason",
            "validation_status", "skipped_reason", "applied",
            "rule_hash",
            "classifier_version_before", "classifier_version_after",
        ):
            self.assertIn(key, entry, f"audit field missing: {key}")
        self.assertEqual(entry["mode"], "dry_run")
        self.assertEqual(entry["applied"], False)


class LoadAndApplyMainHookTest(unittest.TestCase):
    """전체 파이프라인 main hook 동작 — dry_run 은 setattr 안 하고 audit JSON 만 떨어진다."""

    def setUp(self):
        self.snap = _snapshot()
        self.tmp = tempfile.mkdtemp(prefix="ovapply_main_")

    def tearDown(self):
        _restore(self.snap)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_rolling_json(self, allow: bool = False, confidence: str = "high"):
        payload = {
            "candidates": [{
                "rule_id": "break_even_cut",
                "title": "test",
                "confidence": confidence,
                "allow_auto_apply": allow,
                "consistent_across_windows": True,
                "n_largest_window": 50,
                "auto_apply": False,
                "proposed_overrides": [{
                    "target": "exit_strategy.EXIT_BE_R", "op": "decrement",
                    "by": 0.3, "min": 0.5, "reason": "test",
                }],
            }],
        }
        path = os.path.join(self.tmp, "rule_candidates_20260430.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f)

    def test_dry_run_default_does_not_setattr(self):
        original = getattr(exit_strategy, "EXIT_BE_R")
        self._make_rolling_json(allow=True, confidence="high")
        result = ov_mod.load_and_apply_overrides(
            "2026-04-30", mode="dry_run",
            source_dir=self.tmp, log_dir=self.tmp,
        )
        self.assertEqual(getattr(exit_strategy, "EXIT_BE_R"), original)
        self.assertEqual(result["mode"], "dry_run")
        self.assertEqual(result["applied_count"], 0)
        self.assertTrue(os.path.exists(result["audit_log_path"]))

    def test_commit_with_high_and_approval_setattrs(self):
        original = getattr(exit_strategy, "EXIT_BE_R")
        self._make_rolling_json(allow=True, confidence="high")
        result = ov_mod.load_and_apply_overrides(
            "2026-04-30", mode="commit",
            source_dir=self.tmp, log_dir=self.tmp,
        )
        self.assertEqual(result["applied_count"], 1)
        self.assertEqual(getattr(exit_strategy, "EXIT_BE_R"), original - 0.3)

    def test_commit_skipped_when_not_approved(self):
        original = getattr(exit_strategy, "EXIT_BE_R")
        self._make_rolling_json(allow=False, confidence="high")
        result = ov_mod.load_and_apply_overrides(
            "2026-04-30", mode="commit",
            source_dir=self.tmp, log_dir=self.tmp,
        )
        self.assertEqual(result["applied_count"], 0)
        self.assertEqual(getattr(exit_strategy, "EXIT_BE_R"), original)
        # entry 의 skipped_reason 확인
        skipped = [e for e in result["entries"] if e["skipped_reason"]][0]
        self.assertEqual(skipped["skipped_reason"], "not_approved")

    def test_commit_with_failing_fixture_hook_rolls_back(self):
        original = getattr(exit_strategy, "EXIT_BE_R")
        self._make_rolling_json(allow=True, confidence="high")
        result = ov_mod.load_and_apply_overrides(
            "2026-04-30", mode="commit",
            source_dir=self.tmp, log_dir=self.tmp,
            fixture_hook=lambda: False,
        )
        self.assertEqual(getattr(exit_strategy, "EXIT_BE_R"), original)
        # entries 의 applied=false, skipped_reason=fixture_failed
        applied_entries = [e for e in result["entries"] if e["applied"]]
        self.assertEqual(len(applied_entries), 0)
        self.assertEqual(result["entries"][0]["skipped_reason"], "fixture_failed")


class RuleHashStabilityTest(unittest.TestCase):

    def test_same_input_same_hash(self):
        a = ov_mod._rule_hash("r1", {"target": "x", "op": "set", "value": 1.0})
        b = ov_mod._rule_hash("r1", {"target": "x", "op": "set", "value": 1.0})
        self.assertEqual(a, b)

    def test_different_input_different_hash(self):
        a = ov_mod._rule_hash("r1", {"target": "x", "op": "set", "value": 1.0})
        b = ov_mod._rule_hash("r2", {"target": "x", "op": "set", "value": 1.0})
        self.assertNotEqual(a, b)


class StaticImportPolicyTest(unittest.TestCase):
    """동적 import 금지: review/overrides.py 가 importlib 등을 사용하지 않는지 코드 감사."""

    def test_no_dynamic_import_or_eval(self):
        path = os.path.join("review", "overrides.py")
        with open(path, encoding="utf-8") as f:
            src = f.read()
        for forbidden in ("importlib.import_module", "__import__(", "eval(", "exec("):
            self.assertNotIn(forbidden, src,
                             f"review/overrides.py 에서 금지 토큰 발견: {forbidden}")


if __name__ == "__main__":
    unittest.main()
