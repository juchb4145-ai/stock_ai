from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from fetch_minute_bars import (
    collect_condition_capture_codes,
    collect_target_codes,
    collect_traded_codes,
)


TARGET_DATE = "2026-05-13"


def _write_csv(path: Path, fields, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class FetchMinuteBarsCodeCollectionTest(unittest.TestCase):
    def test_collect_traded_codes_includes_paper_would_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trade_log = Path(tmp) / "trade_log.csv"
            _write_csv(
                trade_log,
                ["logged_at", "event", "code"],
                [
                    {"logged_at": f"{TARGET_DATE} 09:01:00", "event": "would_order", "code": "A005930"},
                    {"logged_at": f"{TARGET_DATE} 09:02:00", "event": "chejan", "code": "000660"},
                    {"logged_at": f"{TARGET_DATE} 09:03:00", "event": "sell_order", "code": "035420"},
                    {"logged_at": "2026-05-12 09:01:00", "event": "would_order", "code": "123456"},
                    {"logged_at": f"{TARGET_DATE} 09:04:00", "event": "would_order", "code": "005930"},
                ],
            )

            self.assertEqual(
                collect_traded_codes(str(trade_log), TARGET_DATE),
                ["005930", "000660"],
            )

    def test_collect_condition_capture_codes_returns_all_detected_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            captures = Path(tmp) / "condition_captures.csv"
            _write_csv(
                captures,
                ["logged_at", "event", "detected_at", "captured_at", "code", "name"],
                [
                    {
                        "logged_at": f"{TARGET_DATE} 09:01:00",
                        "event": "condition_detected",
                        "detected_at": f"{TARGET_DATE} 09:01:00",
                        "captured_at": "",
                        "code": "A005930",
                        "name": "one",
                    },
                    {
                        "logged_at": f"{TARGET_DATE} 09:02:00",
                        "event": "capture_price",
                        "detected_at": "",
                        "captured_at": f"{TARGET_DATE} 09:02:00",
                        "code": "000660",
                        "name": "two",
                    },
                    {
                        "logged_at": f"{TARGET_DATE} 09:03:00",
                        "event": "capture_price",
                        "detected_at": "",
                        "captured_at": f"{TARGET_DATE} 09:03:00",
                        "code": "005930",
                        "name": "duplicate",
                    },
                    {
                        "logged_at": "2026-05-12 09:01:00",
                        "event": "condition_detected",
                        "detected_at": "2026-05-12 09:01:00",
                        "captured_at": "",
                        "code": "123456",
                        "name": "old",
                    },
                ],
            )

            self.assertEqual(
                collect_condition_capture_codes(str(captures), TARGET_DATE),
                ["005930", "000660"],
            )

    def test_collect_target_codes_all_prefers_condition_universe_and_adds_trades(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            captures = root / "condition_captures.csv"
            trade_log = root / "trade_log.csv"
            _write_csv(
                captures,
                ["logged_at", "event", "detected_at", "captured_at", "code"],
                [
                    {
                        "logged_at": f"{TARGET_DATE} 09:01:00",
                        "event": "condition_detected",
                        "detected_at": f"{TARGET_DATE} 09:01:00",
                        "captured_at": "",
                        "code": "005930",
                    },
                    {
                        "logged_at": f"{TARGET_DATE} 09:02:00",
                        "event": "condition_detected",
                        "detected_at": f"{TARGET_DATE} 09:02:00",
                        "captured_at": "",
                        "code": "000660",
                    },
                ],
            )
            _write_csv(
                trade_log,
                ["logged_at", "event", "code"],
                [
                    {"logged_at": f"{TARGET_DATE} 09:03:00", "event": "chejan", "code": "000660"},
                    {"logged_at": f"{TARGET_DATE} 09:04:00", "event": "would_order", "code": "035420"},
                ],
            )

            self.assertEqual(
                collect_target_codes(
                    target_date=TARGET_DATE,
                    source="all",
                    trade_log_path=str(trade_log),
                    condition_capture_path=str(captures),
                ),
                ["005930", "000660", "035420"],
            )

    def test_collect_target_codes_all_allows_missing_trade_log_when_captures_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            captures = Path(tmp) / "condition_captures.csv"
            _write_csv(
                captures,
                ["logged_at", "event", "detected_at", "captured_at", "code"],
                [
                    {
                        "logged_at": f"{TARGET_DATE} 09:01:00",
                        "event": "condition_detected",
                        "detected_at": f"{TARGET_DATE} 09:01:00",
                        "captured_at": "",
                        "code": "005930",
                    },
                ],
            )

            self.assertEqual(
                collect_target_codes(
                    target_date=TARGET_DATE,
                    source="all",
                    trade_log_path=str(Path(tmp) / "missing_trade_log.csv"),
                    condition_capture_path=str(captures),
                ),
                ["005930"],
            )


if __name__ == "__main__":
    unittest.main()
