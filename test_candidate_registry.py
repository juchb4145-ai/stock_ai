import unittest

from candidate_registry import CandidateRegistry


class CandidateRegistryTests(unittest.TestCase):
    def test_condition_detection_only_registers_candidate(self):
        registry = CandidateRegistry(signal_source="HTS_CONDITION_SEARCH")

        candidate = registry.register_detection(
            code="005930",
            name="삼성전자",
            condition_name="단테떡상이_수정",
            condition_index="1",
            event_type="I",
            detected_at=123.0,
        )

        self.assertEqual(candidate.code, "005930")
        self.assertEqual(candidate.status, "WATCHING")
        self.assertEqual(candidate.capture_price, 0)
        self.assertEqual(candidate.signal_source, "HTS_CONDITION_SEARCH")

    def test_first_tick_becomes_capture_price(self):
        registry = CandidateRegistry()
        registry.register_detection(code="005930", name="삼성전자")

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

    def test_expires_old_candidates(self):
        registry = CandidateRegistry()
        registry.register_detection(code="005930", detected_at=100.0)

        expired = registry.expire(now=200.0, expiry_seconds=60)

        self.assertEqual([c.code for c in expired], ["005930"])
        self.assertIsNone(registry.get("005930"))

    def test_duplicate_within_ttl_keeps_first_signal_and_updates_last_seen(self):
        registry = CandidateRegistry(candidate_expiry_seconds=60)
        first = registry.register_detection(
            code="005930",
            condition_name="condition_a",
            detected_at=100.0,
            capture_price=10_000,
            meta={"strategy_name": "퀀트조건식"},
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
        self.assertIn("candidate_duplicate_refresh", "\n".join(logs.output))

    def test_duplicate_after_ttl_creates_new_candidate_id(self):
        registry = CandidateRegistry(candidate_expiry_seconds=60)
        first = registry.register_detection(
            code="005930",
            detected_at=100.0,
            capture_price=10_000,
        )
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


if __name__ == "__main__":
    unittest.main()
