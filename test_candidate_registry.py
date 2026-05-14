import json
import unittest

from candidate_registry import (
    CONDITION_COMBO_DANTE_ONLY,
    CONDITION_COMBO_QUANT_AND_DANTE,
    CONDITION_COMBO_QUANT_ONLY,
    CandidateRegistry,
    calculate_leader_score,
)


def _payload_from_log(line):
    return json.loads(line[line.index("{"):])


class CandidateRegistryTests(unittest.TestCase):
    def test_condition_detection_only_registers_candidate(self):
        registry = CandidateRegistry(signal_source="HTS_CONDITION_SEARCH")

        with self.assertLogs("candidate_registry", level="INFO") as logs:
            candidate = registry.register_detection(
                code="005930",
                name="Samsung",
                condition_name="quant_condition",
                condition_index="1",
                event_type="I",
                detected_at=123.0,
                meta={"strategy_name": "momentum-test"},
            )

        self.assertEqual(candidate.code, "005930")
        self.assertEqual(candidate.status, "WATCHING")
        self.assertEqual(candidate.capture_price, 0)
        self.assertEqual(candidate.signal_source, "HTS_CONDITION_SEARCH")
        payload = _payload_from_log(logs.output[0])
        self.assertEqual(payload["event"], "candidate_registered")
        self.assertEqual(payload["candidate_id"], candidate.candidate_id)
        self.assertEqual(payload["symbol"], "005930")
        self.assertEqual(payload["symbol_name"], "Samsung")
        self.assertEqual(payload["condition_name"], "quant_condition")
        self.assertEqual(payload["strategy_name"], "momentum-test")
        self.assertEqual(payload["lifecycle_state"], "registered")
        self.assertIn("ttl_sec", payload)

    def test_first_tick_becomes_capture_price(self):
        registry = CandidateRegistry()
        registry.register_detection(code="005930", name="Samsung")

        first = registry.on_tick(
            "005930",
            price=10_000,
            chejan_strength=110.0,
            accum_volume=12_345,
            entry_trigger_price=9_850,
        )
        second = registry.on_tick("005930", price=9_900, chejan_strength=105.0)
        candidate = registry.get("005930")

        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(candidate.capture_price, 10_000)
        self.assertEqual(candidate.entry_trigger_price, 9_850)
        self.assertEqual(candidate.recent_low_price, 9_900)
        self.assertEqual(candidate.volume_since_capture, 0)

    def test_tracks_high_since_capture_low_after_high_and_rebound(self):
        registry = CandidateRegistry()
        registry.register_detection(code="005930", name="Samsung", capture_price=10_000)

        registry.on_tick("005930", price=10_800)
        candidate = registry.get("005930")
        self.assertEqual(candidate.high_since_capture, 10_800)
        self.assertEqual(candidate.max_price_after_capture, 10_800)
        self.assertEqual(candidate.low_after_high, 0)

        registry.on_tick("005930", price=10_450)
        registry.on_tick("005930", price=10_500)
        candidate = registry.get("005930")

        self.assertEqual(candidate.high_since_capture, 10_800)
        self.assertEqual(candidate.low_after_high, 10_450)
        self.assertAlmostEqual(
            candidate.pullback_from_high_pct,
            (10_800 - 10_500) / 10_800,
        )
        self.assertAlmostEqual(candidate.rebound_from_low_pct, 10_500 / 10_450 - 1)

    def test_new_high_resets_low_after_high(self):
        registry = CandidateRegistry()
        registry.register_detection(code="005930", capture_price=10_000)

        registry.on_tick("005930", price=10_800)
        registry.on_tick("005930", price=10_450)
        registry.on_tick("005930", price=10_900)
        candidate = registry.get("005930")

        self.assertEqual(candidate.high_since_capture, 10_900)
        self.assertEqual(candidate.low_after_high, 0)
        self.assertEqual(candidate.pullback_from_high_pct, 0.0)

    def test_expires_old_candidates(self):
        registry = CandidateRegistry()
        registry.register_detection(code="005930", detected_at=100.0)

        with self.assertLogs("candidate_registry", level="INFO") as logs:
            expired = registry.expire(now=200.0, expiry_seconds=60)

        self.assertEqual([c.code for c in expired], ["005930"])
        self.assertIsNone(registry.get("005930"))
        payload = _payload_from_log(logs.output[0])
        self.assertEqual(payload["event"], "candidate_expired")
        self.assertEqual(payload["symbol"], "005930")
        self.assertEqual(payload["lifecycle_state"], "expired")
        self.assertEqual(payload["ttl_sec"], 60)

    def test_duplicate_within_ttl_keeps_first_signal_and_updates_last_seen(self):
        registry = CandidateRegistry(candidate_expiry_seconds=60)
        first = registry.register_detection(
            code="005930",
            condition_name="condition_a",
            detected_at=100.0,
            capture_price=10_000,
            meta={"strategy_name": "momentum-test"},
        )

        with self.assertLogs("candidate_registry", level="INFO") as logs:
            second = registry.register_detection(
                code="005930",
                condition_name="condition_b",
                detected_at=120.0,
                capture_price=9_900,
            )

        self.assertIs(first, second)
        self.assertEqual(second.candidate_id, first.candidate_id)
        self.assertEqual(second.detected_at, 100.0)
        self.assertEqual(second.first_detected_at, 100.0)
        self.assertEqual(second.first_capture_price, 10_000)
        self.assertEqual(second.capture_price, 10_000)
        self.assertEqual(second.last_detected_at, 120.0)
        self.assertEqual(second.last_capture_price, 9_900)
        self.assertEqual(second.refresh_count, 1)
        self.assertEqual(second.last_condition_name, "condition_b")
        payload = _payload_from_log(logs.output[0])
        self.assertEqual(payload["event"], "candidate_duplicate_refresh")
        self.assertEqual(payload["candidate_id"], first.candidate_id)
        self.assertEqual(payload["refresh_count"], 1)
        self.assertEqual(payload["lifecycle_state"], "refreshed")
        self.assertEqual(payload["ttl_sec"], 60)

    def test_duplicate_after_ttl_creates_new_candidate_id(self):
        registry = CandidateRegistry(candidate_expiry_seconds=60)
        first = registry.register_detection(
            code="005930",
            detected_at=100.0,
            capture_price=10_000,
        )
        with self.assertLogs("candidate_registry", level="INFO") as logs:
            second = registry.register_detection(
                code="005930",
                detected_at=200.0,
                capture_price=9_500,
            )

        self.assertIsNot(first, second)
        self.assertNotEqual(first.candidate_id, second.candidate_id)
        self.assertEqual(second.first_detected_at, 200.0)
        self.assertEqual(second.first_capture_price, 9_500)
        self.assertEqual(second.refresh_count, 0)
        payload = _payload_from_log(logs.output[0])
        self.assertEqual(payload["event"], "candidate_recreated_after_ttl")
        self.assertEqual(payload["old_candidate_id"], first.candidate_id)
        self.assertEqual(payload["candidate_id"], second.candidate_id)
        self.assertEqual(payload["lifecycle_state"], "recreated_after_ttl")

    def test_primary_condition_registers_quant_only_meta(self):
        registry = CandidateRegistry(
            primary_condition_name="단테떡상이_수정",
            bonus_condition_name="단테떡상이",
        )

        candidate = registry.register_detection(
            code="005930",
            condition_name="단테떡상이_수정",
            detected_at=100.0,
            capture_price=10_000,
        )

        self.assertTrue(candidate.meta["quant_detected"])
        self.assertFalse(candidate.meta["dante_detected"])
        self.assertEqual(candidate.meta["condition_combo"], CONDITION_COMBO_QUANT_ONLY)
        self.assertEqual(candidate.meta["first_condition_name"], "단테떡상이_수정")
        self.assertEqual(candidate.meta["last_condition_name"], "단테떡상이_수정")
        self.assertEqual(candidate.meta["condition_score_bonus"], 0.0)

    def test_bonus_after_primary_updates_combo_without_replacing_candidate(self):
        registry = CandidateRegistry(
            candidate_expiry_seconds=60,
            primary_condition_name="단테떡상이_수정",
            bonus_condition_name="단테떡상이",
        )
        first = registry.register_detection(
            code="005930",
            condition_name="단테떡상이_수정",
            detected_at=100.0,
            capture_price=10_000,
        )

        second = registry.register_detection(
            code="005930",
            condition_name="단테떡상이",
            detected_at=112.5,
            capture_price=9_900,
        )

        self.assertIs(first, second)
        self.assertEqual(second.candidate_id, first.candidate_id)
        self.assertEqual(second.capture_price, 10_000)
        self.assertEqual(second.last_capture_price, 9_900)
        self.assertEqual(second.refresh_count, 1)
        self.assertTrue(second.meta["quant_detected"])
        self.assertTrue(second.meta["dante_detected"])
        self.assertEqual(second.meta["condition_combo"], CONDITION_COMBO_QUANT_AND_DANTE)
        self.assertEqual(second.meta["first_condition_name"], "단테떡상이_수정")
        self.assertEqual(second.meta["last_condition_name"], "단테떡상이")
        self.assertEqual(second.meta["bonus_condition_detected_at"], 112.5)
        self.assertEqual(second.meta["time_between_conditions_sec"], 12.5)
        self.assertGreater(second.meta["condition_score_bonus"], 0.0)

    def test_bonus_only_registers_dante_only_meta(self):
        registry = CandidateRegistry(
            primary_condition_name="단테떡상이_수정",
            bonus_condition_name="단테떡상이",
        )

        candidate = registry.register_detection(
            code="005930",
            condition_name="단테떡상이",
            detected_at=100.0,
            meta={"candidate_role": "analysis_only"},
        )

        self.assertFalse(candidate.meta["quant_detected"])
        self.assertTrue(candidate.meta["dante_detected"])
        self.assertEqual(candidate.meta["condition_combo"], CONDITION_COMBO_DANTE_ONLY)
        self.assertEqual(candidate.meta["candidate_role"], "analysis_only")

    def test_leader_metrics_are_stored_without_breaking_tick_state(self):
        registry = CandidateRegistry()
        registry.register_detection(code="005930", name="Samsung", capture_price=10_000)

        registry.on_tick(
            "005930",
            price=10_500,
            volume_delta=1_000,
            trade_value=10_500_000,
            turnover_speed_per_min=180_000_000,
            volume_ratio_1m=2.2,
            volume_ratio_5m=1.6,
            turnover_rank_market=3,
            turnover_rank_sector=0,
            leader_score=82.5,
        )
        candidate = registry.get("005930")

        self.assertEqual(candidate.trade_value_since_capture, 10_500_000)
        self.assertEqual(candidate.turnover_rank_market, 3)
        self.assertAlmostEqual(candidate.volume_ratio_1m, 2.2)
        self.assertAlmostEqual(candidate.leader_score, 82.5)
        self.assertEqual(candidate.meta["leader_score"], 82.5)
        self.assertEqual(candidate.high_since_capture, 10_500)

    def test_ranked_candidates_prioritize_quant_and_dante_and_exclude_dante_only(self):
        registry = CandidateRegistry(
            primary_condition_name="primary",
            bonus_condition_name="bonus",
        )
        quant = registry.register_detection(
            code="000001",
            condition_name="primary",
            detected_at=100.0,
        )
        quant.update_leader_metrics(leader_score=95.0, turnover_rank_market=1)
        both = registry.register_detection(
            code="000002",
            condition_name="primary",
            detected_at=101.0,
        )
        registry.register_detection(
            code="000002",
            condition_name="bonus",
            detected_at=102.0,
        )
        both.update_leader_metrics(leader_score=70.0, turnover_rank_market=5)
        dante = registry.register_detection(
            code="000003",
            condition_name="bonus",
            detected_at=103.0,
            meta={"candidate_role": "analysis_only"},
        )
        dante.update_leader_metrics(leader_score=100.0, turnover_rank_market=1)

        ranked_live = registry.ranked_candidates()
        ranked_all = registry.ranked_candidates(include_analysis=True)

        self.assertEqual([c.code for c in ranked_live], ["000002", "000001"])
        self.assertEqual(ranked_all[-1].code, "000003")

    def test_calculate_leader_score_uses_available_metrics(self):
        score = calculate_leader_score(
            turnover_speed_per_min=250_000_000,
            volume_ratio_1m=2.5,
            volume_ratio_5m=2.0,
            trade_value_since_capture=600_000_000,
            turnover_rank_market=1,
            ranked_count=10,
            condition_combo=CONDITION_COMBO_QUANT_AND_DANTE,
            vwap_support_ok=True,
            chejan_strength=220.0,
            opening_phase=True,
        )

        self.assertGreaterEqual(score, 80.0)


if __name__ == "__main__":
    unittest.main()
