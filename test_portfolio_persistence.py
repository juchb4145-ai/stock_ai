"""portfolio.py 의 디스크 영속화(save/load) 라운드트립 테스트.

장중 크래시 후 재시작했을 때 entry_stage / stop_price / planned_quantity 같은
전략 필드가 디스크에서 정확히 복원되는지 검증한다. 또 손상된 JSON 을 만나도
부팅이 막히지 않는다는 점도 함께 검증한다.

실행:
    python -m unittest test_portfolio_persistence -v
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from portfolio import LoadedPortfolioState, Position, PortfolioState


def _make_full_position() -> Position:
    """전략 필드가 모두 채워진 Position 생성."""
    return Position(
        code="005930",
        name="삼성전자",
        quantity=10,
        available_quantity=10,
        entry_price=70_000,
        target_price=71_500,
        target_return=0.018,
        highest_price=71_200,
        entry_time=1_700_000_000.5,
        bought_today=True,
        pending_buy=False,
        pending_sell=False,
        pending_sell_intent={"reason": "+1R 시간손절", "order_price": 0, "order_gubun": "03"},
        order_context={"side": "buy", "name": "삼성전자"},
        entry_stage=2,
        planned_quantity=10,
        entry1_time=1_700_000_000.0,
        entry2_time=1_700_000_120.0,
        r_unit_pct=0.015,
        stop_price=70_000,
        partial_taken=True,
        breakout_high=71_500,
        pullback_window_deadline=1_700_000_500.0,
        breakout_grade="A",
    )


class PositionSerializationTests(unittest.TestCase):
    def test_round_trip_preserves_strategy_fields(self):
        original = _make_full_position()
        restored = Position.from_persisted_dict(original.to_persisted_dict())

        # 잃으면 안 되는 핵심 전략 필드 — 모두 같아야 함
        for field in (
            "code", "name", "entry_stage", "planned_quantity",
            "stop_price", "partial_taken", "breakout_high", "breakout_grade",
            "entry1_time", "entry2_time", "r_unit_pct",
            "pullback_window_deadline",
            "target_price", "target_return", "highest_price",
            "entry_time", "bought_today",
        ):
            self.assertEqual(
                getattr(restored, field), getattr(original, field),
                f"{field} 가 복원되지 않음",
            )

    def test_volatile_fields_are_not_persisted(self):
        original = _make_full_position()
        original.quantity = 99  # 임의의 잔고 값
        original.available_quantity = 99
        original.pending_buy = True
        original.pending_sell = True
        payload = original.to_persisted_dict()

        # 잔고/미체결 필드는 직렬화에 포함되지 않아야 함 (잔고 TR 응답이 진리)
        self.assertNotIn("quantity", payload)
        self.assertNotIn("available_quantity", payload)
        self.assertNotIn("entry_price", payload)
        self.assertNotIn("pending_buy", payload)
        self.assertNotIn("pending_sell", payload)

        restored = Position.from_persisted_dict(payload)
        self.assertEqual(restored.quantity, 0)
        self.assertEqual(restored.available_quantity, 0)
        self.assertFalse(restored.pending_buy)
        self.assertFalse(restored.pending_sell)

    def test_pending_sell_intent_round_trip(self):
        original = _make_full_position()
        restored = Position.from_persisted_dict(original.to_persisted_dict())
        self.assertEqual(restored.pending_sell_intent, original.pending_sell_intent)

    def test_missing_code_raises(self):
        with self.assertRaises(ValueError):
            Position.from_persisted_dict({"name": "이름만 있음"})


class PositionTypeCastTests(unittest.TestCase):
    """JSON 의 잘못된 타입을 만나도 무시하고 default 를 유지해야 한다.

    손으로 편집된 portfolio_state.json 또는 미래 schema 어긋남에 강건한지 검증.
    """

    def test_int_field_string_castable(self):
        # "70000" 같이 숫자형 문자열은 캐스트 성공해 정상 적용.
        p = Position.from_persisted_dict({
            "code": "005930",
            "entry_stage": "2",
            "stop_price": "70000",
            "planned_quantity": "10",
        })
        self.assertEqual(p.entry_stage, 2)
        self.assertEqual(p.stop_price, 70_000)
        self.assertEqual(p.planned_quantity, 10)

    def test_int_field_garbage_falls_back_to_default(self):
        # "two" 같은 비숫자는 캐스트 실패 → default(0) 유지. setattr 가 일어나지 않음.
        p = Position.from_persisted_dict({
            "code": "005930",
            "entry_stage": "two",
            "stop_price": "garbage",
        })
        self.assertEqual(p.entry_stage, 0)
        self.assertEqual(p.stop_price, 0)

    def test_float_field_int_castable(self):
        p = Position.from_persisted_dict({
            "code": "005930",
            "r_unit_pct": 0.018,
            "entry_time": 1700000000,  # int → float
        })
        self.assertEqual(p.r_unit_pct, 0.018)
        self.assertEqual(p.entry_time, 1_700_000_000.0)

    def test_bool_field_handles_str_int_bool(self):
        p_true = Position.from_persisted_dict({
            "code": "A", "bought_today": True, "partial_taken": "true",
        })
        p_int = Position.from_persisted_dict({
            "code": "B", "bought_today": 1, "partial_taken": 0,
        })
        p_str = Position.from_persisted_dict({
            "code": "C", "bought_today": "yes", "partial_taken": "no",
        })
        self.assertTrue(p_true.bought_today)
        self.assertTrue(p_true.partial_taken)
        self.assertTrue(p_int.bought_today)
        self.assertFalse(p_int.partial_taken)
        self.assertTrue(p_str.bought_today)
        self.assertFalse(p_str.partial_taken)

    def test_str_field_none_becomes_empty_string(self):
        p = Position.from_persisted_dict({
            "code": "005930",
            "name": None,
            "breakout_grade": None,
        })
        self.assertEqual(p.name, "")
        self.assertEqual(p.breakout_grade, "")

    def test_pending_sell_intent_non_dict_becomes_none(self):
        p = Position.from_persisted_dict({
            "code": "005930",
            "pending_sell_intent": "garbage",
        })
        self.assertIsNone(p.pending_sell_intent)

    def test_pending_sell_intent_explicit_null(self):
        p = Position.from_persisted_dict({
            "code": "005930",
            "pending_sell_intent": None,
        })
        self.assertIsNone(p.pending_sell_intent)

    def test_corrupt_field_does_not_block_other_fields(self):
        # entry_stage 가 망가져도 stop_price 같은 다른 필드는 정상 복원.
        p = Position.from_persisted_dict({
            "code": "005930",
            "name": "삼성전자",
            "entry_stage": "two",        # 캐스트 실패 → default 0
            "stop_price": 70_000,        # 정상
            "breakout_grade": "A",
        })
        self.assertEqual(p.entry_stage, 0)
        self.assertEqual(p.stop_price, 70_000)
        self.assertEqual(p.breakout_grade, "A")
        self.assertEqual(p.name, "삼성전자")


class PortfolioStateSaveLoadTests(unittest.TestCase):
    def test_round_trip_with_metadata(self):
        ps = PortfolioState()
        ps.get_or_create("000660", name="SK하이닉스")
        # 풀 데이터 Position 은 다른 code 로 추가해야 충돌 없음 — 005930 = 삼성전자
        full = _make_full_position()
        ps._positions[full.code] = full  # noqa: SLF001  (테스트용 직접 주입)

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "portfolio_state.json")
            ps.save(path, metadata={"trading_day": "2026-04-30", "saved_at": 1234.5})

            self.assertTrue(os.path.exists(path))
            self.assertFalse(os.path.exists(path + ".tmp"))

            loaded: LoadedPortfolioState = PortfolioState.load(path)

        self.assertEqual(len(loaded.state), 2)
        self.assertEqual(loaded.metadata["trading_day"], "2026-04-30")
        self.assertEqual(loaded.metadata["saved_at"], 1234.5)
        # 전략 필드가 그대로 복원
        restored_full = loaded.state.get("005930")
        self.assertIsNotNone(restored_full)
        self.assertEqual(restored_full.entry_stage, 2)
        self.assertEqual(restored_full.stop_price, 70_000)
        self.assertEqual(restored_full.partial_taken, True)
        self.assertEqual(restored_full.breakout_grade, "A")

    def test_load_missing_file_returns_empty_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "no_such.json")
            loaded = PortfolioState.load(path)
            self.assertEqual(len(loaded.state), 0)
            self.assertEqual(loaded.metadata, {})

    def test_load_corrupt_file_preserves_backup_and_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "portfolio_state.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("{not valid json")
            loaded = PortfolioState.load(path)

            self.assertEqual(len(loaded.state), 0)
            self.assertTrue(os.path.exists(path + ".corrupt"))
            self.assertFalse(os.path.exists(path))

    def test_load_unknown_keys_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "portfolio_state.json")
            payload = {
                "schema": "portfolio_state_v1",
                "trading_day": "2026-04-30",
                "positions": [
                    {
                        "code": "005930",
                        "name": "삼성전자",
                        "entry_stage": 1,
                        "stop_price": 70_000,
                        "future_field_we_dont_know_yet": 12345,
                    }
                ],
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f)

            loaded = PortfolioState.load(path)

        self.assertEqual(len(loaded.state), 1)
        position = loaded.state.get("005930")
        self.assertEqual(position.entry_stage, 1)
        self.assertEqual(position.stop_price, 70_000)

    def test_save_does_not_leave_tmp_file_on_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "portfolio_state.json")
            PortfolioState().save(path)
            self.assertTrue(os.path.exists(path))
            self.assertFalse(os.path.exists(path + ".tmp"))

    def test_save_overwrites_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "portfolio_state.json")
            ps1 = PortfolioState()
            ps1.get_or_create("AAA")
            ps1.save(path)

            ps2 = PortfolioState()
            ps2.get_or_create("BBB")
            ps2.save(path)

            loaded = PortfolioState.load(path)
            codes = {p.code for p in loaded.state.values()}
            self.assertEqual(codes, {"BBB"})


if __name__ == "__main__":
    unittest.main()
