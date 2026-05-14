from __future__ import annotations

import csv
import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime

from review import rolling
from review.loader import (
    CONDITION_COMBO_DANTE_ONLY,
    CONDITION_COMBO_QUANT_AND_DANTE,
    CONDITION_COMBO_QUANT_ONLY,
    CONDITION_COMBO_UNKNOWN,
    Trade,
    load_trades,
)
from review.metrics import attach_metrics
from review.report import write_reports
from training_recorder import DANTE_SHADOW_TRAINING_FIELDS, DANTE_TRAINING_FIELDS


def _write_csv(path: str, fields: list[str], rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class ConditionComboLoaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="combo_review_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_trade_log_combo_join_unknown_and_dante_only_warning(self):
        trade_log = os.path.join(self.tmp, "trade_log.csv")
        fields = [
            "logged_at", "event", "code", "name", "side", "order_status",
            "executed_quantity", "executed_price", "candidate_id",
            "condition_combo", "quant_detected", "dante_detected",
        ]
        _write_csv(
            trade_log,
            fields,
            [
                {
                    "logged_at": "2026-05-14 09:01:00",
                    "event": "buy_order",
                    "code": "A000001",
                    "name": "unknown",
                },
                {
                    "logged_at": "2026-05-14 09:02:00",
                    "event": "buy_order",
                    "code": "A000002",
                    "name": "dante-only",
                    "candidate_id": "cand-dante",
                    "condition_combo": CONDITION_COMBO_DANTE_ONLY,
                    "dante_detected": "true",
                },
                {
                    "logged_at": "2026-05-14 09:02:01",
                    "event": "chejan",
                    "code": "A000002",
                    "name": "dante-only",
                    "side": "buy",
                    "order_status": "泥닿껐",
                    "executed_quantity": "10",
                    "executed_price": "10000",
                    "candidate_id": "cand-dante",
                    "condition_combo": CONDITION_COMBO_DANTE_ONLY,
                    "dante_detected": "true",
                },
            ],
        )

        trades = load_trades(
            "2026-05-14",
            trade_log_path=trade_log,
            dante_path=os.path.join(self.tmp, "missing_dante.csv"),
            condition_capture_path=os.path.join(self.tmp, "missing_captures.csv"),
        )
        by_code = {t.code: t for t in trades}

        self.assertEqual(by_code["000001"].condition_combo, CONDITION_COMBO_UNKNOWN)
        self.assertEqual(by_code["000002"].condition_combo, CONDITION_COMBO_DANTE_ONLY)
        self.assertTrue(by_code["000002"].dante_only_buy_warning)


class ConditionComboReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="combo_report_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _trade(self, code: str, combo: str, ret: float, *, hit_stop: int = 0, reached_1r: int = 1) -> Trade:
        trade = Trade(date="2026-05-14", code=code, name=code)
        trade.condition_combo = combo
        trade.entry_qty = 1
        trade.entry_notional = 10_000
        trade.exit_qty = 1
        trade.exit_notional = int(10_000 * (1 + ret))
        trade.entry_first_time = datetime(2026, 5, 14, 9, 0, 0)
        trade.exit_last_time = datetime(2026, 5, 14, 9, 10, 0)
        trade.realized_return = ret
        trade.max_return_25m = max(ret, 0.02)
        trade.min_return_25m = min(ret, -0.005)
        trade.reached_1r = reached_1r
        trade.hit_stop = hit_stop
        trade.features["leader_score"] = 85.0 if combo == CONDITION_COMBO_QUANT_AND_DANTE else 65.0
        trade.features["volume_ratio_1m"] = 2.0
        trade.features["turnover_speed_per_min"] = 180_000_000.0
        return trade

    def test_report_outputs_condition_combo_to_csv_json_and_markdown(self):
        trades = [
            self._trade("000001", CONDITION_COMBO_QUANT_ONLY, 0.015),
            self._trade("000002", CONDITION_COMBO_QUANT_AND_DANTE, -0.015, hit_stop=1, reached_1r=0),
        ]
        attach_metrics(trades)

        paths = write_reports(
            trades,
            [],
            "2026-05-14",
            out_dir=self.tmp,
            include_shadow_diagnostics=False,
        )

        with open(paths["csv"], newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(rows[0]["condition_combo"], CONDITION_COMBO_QUANT_ONLY)
        self.assertEqual(rows[1]["condition_combo"], CONDITION_COMBO_QUANT_AND_DANTE)

        with open(paths["json"], encoding="utf-8") as f:
            payload = json.load(f)
        self.assertIn("condition_combo_summary", payload)
        self.assertIn("leader_score_summary", payload)
        self.assertEqual(payload["condition_combo_summary"][CONDITION_COMBO_QUANT_ONLY]["trades"], 1)

        with open(paths["md"], encoding="utf-8") as f:
            md = f.read()
        self.assertIn("조건식 조합별 성과", md)
        self.assertIn(CONDITION_COMBO_QUANT_AND_DANTE, md)
        self.assertIn("leader_score >= 80", md)


class ConditionComboTrainingSchemaTests(unittest.TestCase):
    def test_training_csv_headers_include_condition_combo_fields(self):
        for fields in (DANTE_TRAINING_FIELDS, DANTE_SHADOW_TRAINING_FIELDS):
            self.assertIn("primary_condition_name", fields)
            self.assertIn("bonus_condition_name", fields)
            self.assertIn("condition_combo", fields)
            self.assertIn("time_between_conditions_sec", fields)
            self.assertIn("leader_score", fields)
            self.assertIn("volume_ratio_1m", fields)
            self.assertIn("turnover_speed_per_min", fields)


class ConditionComboRollingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="combo_rolling_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_review(self, rows: list[dict], date: str = "2026-05-14") -> None:
        fields = [
            "date", "code", "name", "entry_class", "exit_class", "classifier_version",
            "condition_combo", "reason_code", "plan_source",
            "leader_score", "volume_ratio_1m",
            "realized_return", "r_multiple", "mfe_r", "mae_r",
            "reached_1r", "hit_stop",
        ]
        path = os.path.join(self.tmp, f"trade_review_{date}.csv")
        normalized = []
        for i, row in enumerate(rows):
            item = {
                "date": date,
                "code": f"R{i:04d}",
                "name": "review",
                "entry_class": row.get("entry_class", "breakout_chase"),
                "exit_class": row.get("exit_class", "clean_exit"),
                "classifier_version": "v2",
                "condition_combo": row.get("condition_combo", ""),
                "reason_code": row.get("reason_code", ""),
                "plan_source": row.get("plan_source", ""),
                "leader_score": row.get("leader_score", ""),
                "volume_ratio_1m": row.get("volume_ratio_1m", ""),
                "realized_return": row.get("realized_return", 0.0),
                "r_multiple": row.get("r_multiple", 0.0),
                "mfe_r": row.get("mfe_r", 1.0),
                "mae_r": row.get("mae_r", -0.2),
                "reached_1r": row.get("reached_1r", 1),
                "hit_stop": row.get("hit_stop", 0),
            }
            normalized.append(item)
        _write_csv(path, fields, normalized)

    def test_rolling_summary_groups_condition_combo_and_unknown(self):
        self._write_review([
            {"condition_combo": CONDITION_COMBO_QUANT_ONLY, "r_multiple": 1.0, "realized_return": 0.015},
            {"condition_combo": CONDITION_COMBO_QUANT_ONLY, "r_multiple": -1.0, "realized_return": -0.015},
            {"condition_combo": "", "r_multiple": 0.5, "realized_return": 0.0075},
        ])

        result = rolling.run_rolling(
            as_of_date="2026-05-14",
            windows=(1,),
            reviews_dir=self.tmp,
            write=True,
            include_shadow=False,
        )
        stats = result.window_stats[0].to_dict()
        self.assertIn("by_condition_combo", stats)
        self.assertIn("by_leader_score_bucket", stats)
        self.assertEqual(stats["by_condition_combo"][CONDITION_COMBO_QUANT_ONLY]["n"], 2)
        self.assertEqual(stats["by_condition_combo"][CONDITION_COMBO_UNKNOWN]["n"], 1)

        with open(result.output_paths["summary"], encoding="utf-8") as f:
            payload = json.load(f)
        self.assertIn("by_condition_combo", payload["stats"][0])

    def test_condition_combo_rule_candidates_are_created(self):
        self._write_review([
            {"condition_combo": CONDITION_COMBO_QUANT_ONLY, "r_multiple": 0.0, "realized_return": 0.0},
            {"condition_combo": CONDITION_COMBO_QUANT_ONLY, "r_multiple": 0.0, "realized_return": 0.0},
            {"condition_combo": CONDITION_COMBO_QUANT_AND_DANTE, "r_multiple": 1.0, "realized_return": 0.015},
            {"condition_combo": CONDITION_COMBO_QUANT_AND_DANTE, "r_multiple": 1.0, "realized_return": 0.015},
            {"condition_combo": CONDITION_COMBO_QUANT_ONLY, "reason_code": "BUY_BREAKOUT_SMALL", "r_multiple": -1.0, "realized_return": -0.015},
            {"condition_combo": CONDITION_COMBO_QUANT_ONLY, "reason_code": "BREAKOUT_SMALL", "r_multiple": -1.0, "realized_return": -0.015},
            {"condition_combo": CONDITION_COMBO_QUANT_AND_DANTE, "reason_code": "BUY_PULLBACK_RECLAIM", "entry_class": "first_pullback", "r_multiple": 1.0, "realized_return": 0.015},
            {"condition_combo": CONDITION_COMBO_QUANT_AND_DANTE, "reason_code": "QUANT_FIRST_PULLBACK_READY", "entry_class": "first_pullback", "r_multiple": 1.0, "realized_return": 0.015},
        ])

        result = rolling.run_rolling(
            as_of_date="2026-05-14",
            windows=(1,),
            reviews_dir=self.tmp,
            write=False,
            include_shadow=False,
        )
        rule_ids = {c.rule_id for c in result.candidates}
        self.assertIn("prefer_quant_and_dante", rule_ids)
        self.assertIn("disable_breakout_probe_live", rule_ids)

    def test_penalize_dante_only_uses_shadow_rows(self):
        self._write_review([
            {"condition_combo": CONDITION_COMBO_QUANT_ONLY, "r_multiple": 0.5, "realized_return": 0.0075},
            {"condition_combo": CONDITION_COMBO_QUANT_ONLY, "r_multiple": 0.5, "realized_return": 0.0075},
        ])
        shadow_csv = os.path.join(self.tmp, "dante_shadow_training.csv")
        _write_csv(
            shadow_csv,
            ["captured_time", "code", "condition_combo", "reached_1r", "hit_stop"],
            [
                {"captured_time": "2026-05-14 09:00:00", "code": "S1", "condition_combo": CONDITION_COMBO_DANTE_ONLY, "reached_1r": 0, "hit_stop": 1},
                {"captured_time": "2026-05-14 09:01:00", "code": "S2", "condition_combo": CONDITION_COMBO_DANTE_ONLY, "reached_1r": 0, "hit_stop": 1},
            ],
        )

        result = rolling.run_rolling(
            as_of_date="2026-05-14",
            windows=(1,),
            reviews_dir=self.tmp,
            write=False,
            include_shadow=False,
            shadow_csv=shadow_csv,
        )
        rule_ids = {c.rule_id for c in result.candidates}
        self.assertIn("penalize_dante_only", rule_ids)


if __name__ == "__main__":
    unittest.main()
