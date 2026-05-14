import json
import unittest

from candidate_registry import CandidateRegistry


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


if __name__ == "__main__":
    unittest.main()
