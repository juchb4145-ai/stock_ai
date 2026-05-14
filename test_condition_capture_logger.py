from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from condition_capture_logger import (
    CONDITION_CAPTURE_FIELDS,
    ConditionCaptureLogger,
    read_condition_captures,
)


class ConditionCaptureLoggerTests(unittest.TestCase):
    def test_detection_row_includes_candidate_and_strategy_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "condition_captures.csv"
            logger = ConditionCaptureLogger(str(path))

            logger.append_detection(
                code="A005930",
                candidate_id="candidate-1",
                name="삼성전자",
                condition_name="퀀트조건식",
                strategy_name="momentum-test",
                signal_source="HTS_CONDITION_SEARCH",
                detected_at="2026-05-13 09:00:00",
            )

            rows = read_condition_captures(str(path))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["candidate_id"], "candidate-1")
            self.assertEqual(rows[0]["symbol"], "A005930")
            self.assertEqual(rows[0]["symbol_name"], "삼성전자")
            self.assertEqual(rows[0]["strategy_name"], "momentum-test")
            self.assertEqual(rows[0]["condition_name"], "퀀트조건식")
            self.assertEqual(rows[0]["signal_source"], "HTS_CONDITION_SEARCH")
            self.assertEqual(rows[0]["source_event"], "condition_detected")
            self.assertEqual(rows[0]["created_at"], rows[0]["logged_at"])
            self.assertEqual(rows[0]["capture_price"], "")

    def test_existing_capture_file_header_is_extended(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "condition_captures.csv"
            old_fields = ["logged_at", "event", "detected_at", "code", "name"]
            with path.open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=old_fields)
                writer.writeheader()
                writer.writerow(
                    {
                        "logged_at": "2026-05-13 09:00:00",
                        "event": "condition_detected",
                        "detected_at": "2026-05-13 09:00:00",
                        "code": "005930",
                        "name": "삼성전자",
                    }
                )

            logger = ConditionCaptureLogger(str(path))
            logger.append_detection(
                code="000660",
                candidate_id="candidate-2",
                name="SK하이닉스",
                condition_name="퀀트조건식",
                strategy_name="momentum-test",
                detected_at="2026-05-13 09:05:00",
            )

            with path.open("r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertEqual(reader.fieldnames, CONDITION_CAPTURE_FIELDS)
            self.assertEqual(rows[0]["symbol"], "005930")
            self.assertEqual(rows[0]["source_event"], "condition_detected")
            self.assertEqual(rows[1]["candidate_id"], "candidate-2")
            backups = list(path.parent.glob("condition_captures.csv.bak_*"))
            self.assertEqual(len(backups), 1)


if __name__ == "__main__":
    unittest.main()
