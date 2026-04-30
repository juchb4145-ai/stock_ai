"""review.overrides 단위 테스트.

PR-A 적용기가 의존하는 핵심 안전성 보장:
  - whitelist 외 target 거부
  - allowed op 외 op 거부
  - set/increment/decrement/multiply 산술 정확
  - rule min/max 와 hard cap(whitelist) 양쪽 모두 적용 (교집합)
  - eval/exec/dynamic import 일절 미사용 (구조상 보장 — 코드 감사로 확인)

  python -m unittest test_overrides
"""

from __future__ import annotations

import unittest

from review.overrides import (
    ALLOWED_OPS,
    TARGET_WHITELIST,
    Override,
    apply_override,
    validate_override,
)


VALID_TARGET = "exit_strategy.EXIT_PARTIAL_R"  # whitelist min=1.0, max=3.5


class ValidateOverrideTest(unittest.TestCase):

    def test_unknown_target_rejected(self):
        ov = Override(target="strategy.NOT_EXIST", op="set", value=1.0)
        with self.assertRaises(ValueError):
            validate_override(ov)

    def test_unknown_op_rejected(self):
        ov = Override(target=VALID_TARGET, op="divide", by=2.0)
        with self.assertRaises(ValueError):
            validate_override(ov)

    def test_set_requires_value(self):
        ov = Override(target=VALID_TARGET, op="set")
        with self.assertRaises(ValueError):
            validate_override(ov)

    def test_increment_requires_by(self):
        ov = Override(target=VALID_TARGET, op="increment")
        with self.assertRaises(ValueError):
            validate_override(ov)

    def test_min_cannot_exceed_max(self):
        ov = Override(target=VALID_TARGET, op="set", value=2.0, min=2.0, max=1.0)
        with self.assertRaises(ValueError):
            validate_override(ov)


class ApplyOverrideArithmeticTest(unittest.TestCase):

    def test_set(self):
        ov = Override(target=VALID_TARGET, op="set", value=1.5)
        self.assertAlmostEqual(apply_override(ov, current_value=2.0), 1.5)

    def test_increment(self):
        ov = Override(target=VALID_TARGET, op="increment", by=0.3)
        self.assertAlmostEqual(apply_override(ov, current_value=2.0), 2.3)

    def test_decrement(self):
        ov = Override(target=VALID_TARGET, op="decrement", by=0.5)
        self.assertAlmostEqual(apply_override(ov, current_value=2.0), 1.5)

    def test_multiply(self):
        ov = Override(target=VALID_TARGET, op="multiply", by=0.5)
        self.assertAlmostEqual(apply_override(ov, current_value=3.0), 1.5)


class ApplyOverrideClampTest(unittest.TestCase):

    def test_rule_min_clamps(self):
        ov = Override(target=VALID_TARGET, op="decrement", by=10.0, min=1.0)
        # current=2.0 - 10.0 = -8 → rule min 1.0 → hard min 1.0
        self.assertAlmostEqual(apply_override(ov, current_value=2.0), 1.0)

    def test_rule_max_clamps(self):
        ov = Override(target=VALID_TARGET, op="increment", by=10.0, max=2.5)
        # current=2.0 + 10 = 12 → rule max 2.5 → hard max 3.5 → 결과 2.5
        self.assertAlmostEqual(apply_override(ov, current_value=2.0), 2.5)

    def test_hard_cap_clamps_when_no_rule_max(self):
        ov = Override(target=VALID_TARGET, op="increment", by=10.0)
        # rule max 없음, hard max 3.5 적용
        self.assertAlmostEqual(apply_override(ov, current_value=2.0), 3.5)

    def test_hard_cap_clamps_when_no_rule_min(self):
        ov = Override(target=VALID_TARGET, op="decrement", by=10.0)
        # rule min 없음, hard min 1.0 적용
        self.assertAlmostEqual(apply_override(ov, current_value=2.0), 1.0)

    def test_set_value_outside_hard_cap_is_rejected(self):
        """P1 #9 정책 변경: op=set 은 hard cap 밖이면 사전 거부(클램프 X).

        increment/decrement/multiply 와 달리 set 은 의도값 자체가 hard cap 을
        벗어나면 룰이 잘못 작성된 것으로 간주하고 거부한다(audit 가독성 + 안전).
        """
        ov = Override(target=VALID_TARGET, op="set", value=99.0)
        with self.assertRaises(ValueError):
            apply_override(ov, current_value=2.0)


class WhitelistShapeTest(unittest.TestCase):
    """whitelist 가 PR-A 가 기대하는 형태(<module>.<NAME>) 인지 sanity check."""

    def test_keys_have_module_and_name(self):
        for key in TARGET_WHITELIST.keys():
            self.assertIn(".", key, f"target 키는 module.NAME 형태여야 함: {key}")
            module, name = key.split(".", 1)
            self.assertTrue(name.isupper() or "_" in name,
                            f"NAME 은 모듈 상수(대문자) 권장: {key}")

    def test_each_entry_has_min_max(self):
        for key, cap in TARGET_WHITELIST.items():
            self.assertIn("min", cap, f"{key} 의 hard cap min 누락")
            self.assertIn("max", cap, f"{key} 의 hard cap max 누락")
            self.assertLessEqual(cap["min"], cap["max"],
                                 f"{key} 의 hard cap min > max")

    def test_allowed_ops_set(self):
        self.assertEqual(set(ALLOWED_OPS), {"set", "increment", "decrement", "multiply"})


class SerializationTest(unittest.TestCase):

    def test_to_dict_round_trip(self):
        ov = Override(
            target=VALID_TARGET, op="decrement", by=0.5, min=1.0, max=3.0,
            reason="테스트",
        )
        d = ov.to_dict()
        self.assertEqual(d["target"], VALID_TARGET)
        self.assertEqual(d["op"], "decrement")
        self.assertEqual(d["by"], 0.5)
        self.assertNotIn("value", d)  # decrement 는 value 비어 있어야 함

        rebuilt = Override.from_dict(d)
        self.assertEqual(rebuilt.target, ov.target)
        self.assertEqual(rebuilt.op, ov.op)
        self.assertEqual(rebuilt.by, ov.by)
        self.assertEqual(rebuilt.reason, "테스트")


if __name__ == "__main__":
    unittest.main()
