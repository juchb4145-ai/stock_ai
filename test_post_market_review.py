from __future__ import annotations

import csv
import inspect
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from review.post_market import (
    REVIEW_COLUMNS,
    load_condition_candidates,
    run_post_market_review,
)
import review.post_market as post_market
import tools.post_market_review as post_market_cli


TARGET_DATE = "2026-05-13"
YYYYMMDD = "20260513"
POST_MARKET_FIXTURE_DIR = Path("tests") / "fixtures" / "post_market"


def _write_csv(path: Path, fields, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _condition_rows():
    fields = [
        "logged_at",
        "event",
        "detected_at",
        "captured_at",
        "captured_time",
        "code",
        "name",
        "condition_name",
        "strategy_name",
        "condition_formula",
        "condition_formula_version",
        "condition_index",
        "event_type",
        "screen_no",
        "capture_price",
        "entry_trigger_price",
        "chejan_strength",
        "accum_volume",
        "signal_source",
        "source",
    ]
    specs = [
        ("WIN1", "Win Stock", "09:10:00", 10000),
        ("LOSS1", "Loss Stock", "09:15:00", 10000),
        ("MISS1", "Missed Stock", "09:20:00", 10000),
        ("GOOD1", "Good Reject", "09:25:00", 10000),
        ("CHGOOD", "Good Chase", "09:30:00", 10000),
        ("CHBAD", "Bad Chase", "09:35:00", 10000),
        ("DATA1", "Data Block", "09:40:00", 10000),
        ("TIME1", "Time Block", "14:25:00", 10000),
        ("GUARD1", "Guard Block", "09:45:00", 10000),
        ("NOBAR1", "No Bars", "09:50:00", 10000),
    ]
    rows = []
    for code, name, clock, price in specs:
        detected = f"{TARGET_DATE} {clock}"
        base = {
            "logged_at": detected,
            "detected_at": detected,
            "captured_at": detected,
            "captured_time": clock.replace(":", ""),
            "code": code,
            "name": name,
            "condition_name": "quant_condition",
            "strategy_name": "momentum-test",
            "condition_formula": "A and J",
            "condition_formula_version": "test",
            "condition_index": "1",
            "event_type": "I",
            "screen_no": "0150",
            "entry_trigger_price": "",
            "chejan_strength": "120",
            "accum_volume": "1000",
            "signal_source": "HTS_CONDITION_SEARCH",
            "source": "kiwoom",
        }
        rows.append({**base, "event": "condition_detected", "capture_price": ""})
        rows.append({**base, "event": "capture_price", "capture_price": str(price), "screen_no": "0160"})
    return fields, rows


def _write_bars(root: Path, code: str, start: str, prices) -> None:
    start_dt = datetime.strptime(f"{TARGET_DATE} {start}", "%Y-%m-%d %H:%M:%S")
    rows = []
    for idx, close in enumerate(prices):
        dt = start_dt + timedelta(minutes=idx)
        high = close
        low = close
        rows.append(
            {
                "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "open": close,
                "high": high,
                "low": low,
                "close": close,
                "volume": 1000 + idx,
            }
        )
    _write_csv(
        root / "intraday" / YYYYMMDD / f"{code}.csv",
        ["datetime", "open", "high", "low", "close", "volume"],
        rows,
    )


def _log_line(label: str, payload: dict) -> str:
    ts = payload.get("timestamp", f"{TARGET_DATE} 09:00:00")
    return f"{ts} [INFO] [{label}] {json.dumps(payload, ensure_ascii=False, sort_keys=True)}\n"


def _write_main_log(path: Path) -> None:
    events = []
    def momentum(code, ts, decision, reason_code, **extra):
        payload = {
            "event": "momentum_entry_decision",
            "timestamp": f"{TARGET_DATE} {ts}",
            "symbol": code,
            "symbol_name": code,
            "condition_name": "quant_condition",
            "decision": decision,
            "reason_code": reason_code,
            "reason_detail": reason_code,
            "capture_price": 10000,
            "current_price": 10000,
            "volume_ratio": 1.5,
            "turnover_speed_per_min": 60000000,
            "trade_strength": 120,
            "spread_rate": 0.001,
            "vwap": 9950,
            "chase_risk_score": 10,
            "high_distance_pct": 0.01,
            "upper_wick_ratio": 0.1,
            "market_data_available": True,
            "candle_cache_available": True,
        }
        payload.update(extra)
        events.append(_log_line("momentum_entry_decision", payload))

    momentum("WIN1", "09:10:30", "BUY", "buy_pullback_confirmed")
    momentum("LOSS1", "09:15:30", "BUY", "buy_pullback_confirmed")
    momentum("MISS1", "09:20:30", "REJECT", "weak_volume_ratio")
    momentum("GOOD1", "09:25:30", "REJECT", "reject_trade_strength")
    momentum("CHGOOD", "09:30:30", "BLOCK_CHASE", "block_chase_distance")
    momentum("CHBAD", "09:35:30", "BLOCK_CHASE", "block_chase_distance")
    momentum(
        "DATA1",
        "09:40:30",
        "WAIT_DATA",
        "missing_volume_ratio",
        market_data_available=False,
        volume_ratio=None,
    )
    momentum("TIME1", "14:25:30", "REJECT", "BLOCK_AFTER_ENTRY_CUTOFF", time_policy_reason_code="BLOCK_AFTER_ENTRY_CUTOFF")
    momentum("GUARD1", "09:45:30", "BUY", "buy_pullback_confirmed")
    momentum("NOBAR1", "09:50:30", "REJECT", "weak_volume_ratio")
    events.append(
        _log_line(
            "final_entry_decision",
            {
                "event": "final_entry_decision",
                "timestamp": f"{TARGET_DATE} 09:20:35",
                "symbol": "MISS1",
                "allowed": False,
                "status": "blocked",
                "reason_code": "weak_volume_ratio",
                "final_reason": "weak volume",
                "blocked_by": "momentum",
                "momentum_decision": "REJECT",
                "legacy_decision": "READY",
                "time_policy_decision": "ALLOW_ENTRY",
                "order_guard_decision": None,
                "strategy_version": "test-v1",
                "market_regime": "weak",
                "market_gate_action": "dry_run_block_chase_only",
                "market_gate_reason": "GATE_MARKET_WEAK_CHASE_BLOCK",
                "sector_regime": "risk_off",
                "sector_gate_action": "dry_run_block_chase_only",
                "sector_gate_reason": "GATE_SECTOR_RISK_OFF",
                "theme_regime": "neutral",
                "theme_gate_action": "dry_run_allow",
                "theme_gate_reason": "",
                "turnover_rank_sector": 3,
                "decision_trace": {
                    "momentum_decision": "REJECT",
                    "legacy_decision": "READY",
                    "time_policy_decision": "ALLOW_ENTRY",
                    "order_guard_decision": None,
                    "final_reason": "weak volume",
                    "strategy_version": "test-v1",
                    "blocked_by": "momentum",
                    "reason_code": "weak_volume_ratio",
                },
            },
        )
    )
    events.append(
        _log_line(
            "entry_decision_trace",
            {
                "event": "entry_decision_trace",
                "timestamp": f"{TARGET_DATE} 09:45:40",
                "symbol": "GUARD1",
                "guard_allowed": False,
                "guard_reason": "daily_buy_limit",
                "blocked_by": "daily_buy_limit",
            },
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(events), encoding="utf-8")


def _write_trade_log(path: Path) -> None:
    fields = [
        "logged_at",
        "event",
        "code",
        "name",
        "side",
        "order_type",
        "order_status",
        "order_no",
        "order_result",
        "quantity",
        "order_price",
        "current_price",
        "executed_price",
        "executed_quantity",
        "entry_price",
        "target_price",
        "score",
        "expected_return",
        "model_name",
        "model_score",
        "model_action",
        "model_target",
        "model_threshold",
        "reason",
        "exit_reason_code",
        "exit_type",
        "stop_reason",
        "exit_policy_source",
        "sell_retry_count",
        "unfilled_exit_qty",
        "sell_order_result",
        "exit_order_no",
        "exit_decision_trace",
        "hold_seconds",
        "profit_rate",
        "message",
        "market_regime",
        "market_gate_action",
        "market_gate_reason",
    ]
    rows = [
        {
            "logged_at": f"{TARGET_DATE} 09:11:00",
            "event": "would_order",
            "code": "WIN1",
            "name": "Win Stock",
            "side": "buy",
            "order_result": "DRY_RUN",
            "quantity": "10",
            "current_price": "10000",
            "entry_price": "10000",
            "reason": "paper buy",
        },
        {
            "logged_at": f"{TARGET_DATE} 09:20:00",
            "event": "would_order",
            "code": "WIN1",
            "name": "Win Stock",
            "side": "sell",
            "order_result": "DRY_RUN",
            "quantity": "10",
            "current_price": "10200",
            "entry_price": "10000",
            "profit_rate": "0.02",
            "reason": "paper target",
            "exit_reason_code": "take_profit_fixed_pct",
            "exit_type": "profit_take",
            "exit_policy_source": "exit_strategy.evaluate_exit",
            "sell_order_result": "DRY_RUN",
            "exit_order_no": "PAPER-WIN",
            "exit_decision_trace": json.dumps({"matched_rule": "take_profit_fixed_pct"}),
        },
        {
            "logged_at": f"{TARGET_DATE} 09:16:00",
            "event": "would_order",
            "code": "LOSS1",
            "name": "Loss Stock",
            "side": "buy",
            "order_result": "DRY_RUN",
            "quantity": "10",
            "current_price": "10000",
            "entry_price": "10000",
            "reason": "paper buy",
        },
        {
            "logged_at": f"{TARGET_DATE} 09:19:00",
            "event": "would_order",
            "code": "LOSS1",
            "name": "Loss Stock",
            "side": "sell",
            "order_result": "DRY_RUN",
            "quantity": "10",
            "current_price": "9850",
            "entry_price": "10000",
            "profit_rate": "-0.015",
            "reason": "paper stop",
            "exit_reason_code": "hard_stop_fixed_pct",
            "exit_type": "hard_stop",
            "stop_reason": "hard_stop_fixed_pct",
            "exit_policy_source": "exit_strategy.evaluate_exit",
            "sell_retry_count": "1",
            "unfilled_exit_qty": "0",
            "sell_order_result": "DRY_RUN",
            "exit_order_no": "PAPER-LOSS",
            "exit_decision_trace": json.dumps({"matched_rule": "hard_stop_fixed_pct"}),
        },
    ]
    full_rows = []
    for row in rows:
        base = {field: "" for field in fields}
        base.update(row)
        full_rows.append(base)
    _write_csv(path, fields, full_rows)


def _make_fixture(root: Path) -> dict:
    condition_path = root / "condition_captures.csv"
    fields, rows = _condition_rows()
    _write_csv(condition_path, fields, rows)
    _write_main_log(root / "main.log")
    _write_trade_log(root / "trade_log.csv")
    _write_bars(root, "WIN1", "09:10:00", [10000, 10100, 10200, 10150, 10200, 10300])
    _write_bars(root, "LOSS1", "09:15:00", [10000, 9900, 9850, 9800, 9820, 9810])
    _write_bars(root, "MISS1", "09:20:00", [10000, 10100, 10250, 10300, 10400, 10350])
    _write_bars(root, "GOOD1", "09:25:00", [10000, 9950, 9900, 9850, 9800, 9820])
    _write_bars(root, "CHGOOD", "09:30:00", [10000, 10050, 9950, 9900, 9850, 9800])
    _write_bars(root, "CHBAD", "09:35:00", [10000, 10150, 10300, 10450, 10500, 10400])
    _write_bars(root, "DATA1", "09:40:00", [10000, 10100, 10300, 10400, 10200, 10100])
    _write_bars(root, "TIME1", "14:25:00", [10000, 10050, 10250, 10300, 10200, 10100])
    _write_bars(root, "GUARD1", "09:45:00", [10000, 10020, 10030, 10010, 10000, 10000])
    return {
        "condition": condition_path,
        "main_log": root / "main.log",
        "trade_log": root / "trade_log.csv",
        "intraday": root / "intraday",
        "output": root / "reports",
    }


def _write_rotated_log_condition_fixture(path: Path) -> None:
    fields = [
        "logged_at",
        "event",
        "source_event",
        "created_at",
        "candidate_id",
        "symbol",
        "symbol_name",
        "detected_at",
        "captured_at",
        "captured_time",
        "code",
        "name",
        "condition_name",
        "strategy_name",
        "capture_price",
        "signal_source",
    ]
    rows = [
        {
            "logged_at": f"{TARGET_DATE} 09:00:00",
            "event": "condition_detected",
            "source_event": "condition_detected",
            "created_at": f"{TARGET_DATE} 09:00:00",
            "candidate_id": "cid-rot-1",
            "symbol": "ROT1",
            "symbol_name": "Rotated One",
            "detected_at": f"{TARGET_DATE} 09:00:00",
            "captured_at": f"{TARGET_DATE} 09:00:00",
            "captured_time": "090000",
            "code": "ROT1",
            "name": "Rotated One",
            "condition_name": "QuantCondition",
            "strategy_name": "momentum-test",
            "capture_price": "10000",
            "signal_source": "HTS_CONDITION_SEARCH",
        },
        {
            "logged_at": f"{TARGET_DATE} 09:05:00",
            "event": "condition_detected",
            "source_event": "condition_detected",
            "created_at": f"{TARGET_DATE} 09:05:00",
            "candidate_id": "",
            "symbol": "ROT2",
            "symbol_name": "Rotated Two",
            "detected_at": f"{TARGET_DATE} 09:05:00",
            "captured_at": f"{TARGET_DATE} 09:05:00",
            "captured_time": "090500",
            "code": "ROT2",
            "name": "Rotated Two",
            "condition_name": "QuantCondition",
            "strategy_name": "",
            "capture_price": "10000",
            "signal_source": "HTS_CONDITION_SEARCH",
        },
    ]
    _write_csv(path, fields, rows)


class PostMarketReviewTests(unittest.TestCase):
    def test_condition_capture_collects_all_detected_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = _make_fixture(Path(tmp))
            candidates = load_condition_candidates(
                target_date=TARGET_DATE,
                path=paths["condition"],
            )

            self.assertEqual(len(candidates), 10)
            self.assertTrue(any(c.symbol == "MISS1" for c in candidates))
            self.assertTrue(all(c.capture_price == 10000 for c in candidates))

    def test_review_classifies_traded_and_non_traded_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = _make_fixture(Path(tmp))

            result = run_post_market_review(
                target_date=TARGET_DATE,
                mode="paper",
                output_dir=paths["output"],
                condition_capture_path=paths["condition"],
                trade_log_path=paths["trade_log"],
                main_log_path=paths["main_log"],
                intraday_dir=paths["intraday"],
                min_missed_opportunity_pct=0.02,
                write_json=True,
            )

            by_symbol = {row.symbol: row for row in result.rows}
            self.assertEqual(by_symbol["WIN1"].review_category, "TRADED_WIN")
            self.assertEqual(by_symbol["LOSS1"].review_category, "TRADED_LOSS")
            self.assertEqual(by_symbol["MISS1"].review_category, "MISSED_OPPORTUNITY")
            self.assertEqual(by_symbol["GOOD1"].review_category, "GOOD_REJECT")
            self.assertEqual(by_symbol["CHGOOD"].review_category, "GOOD_BLOCK_CHASE")
            self.assertEqual(by_symbol["CHBAD"].review_category, "BAD_BLOCK_CHASE")
            self.assertEqual(by_symbol["DATA1"].review_category, "DATA_QUALITY_BLOCK")
            self.assertEqual(by_symbol["TIME1"].review_category, "TIME_POLICY_BLOCK")
            self.assertEqual(by_symbol["GUARD1"].review_category, "ORDER_GUARD_BLOCK")
            self.assertFalse(by_symbol["MISS1"].traded)
            self.assertGreater(by_symbol["MISS1"].mfe_pct, 0.02)
            self.assertEqual(by_symbol["TIME1"].block_source, "time_policy")
            self.assertTrue(by_symbol["TIME1"].would_have_passed_if_time_policy_relaxed)
            self.assertEqual(by_symbol["TIME1"].missed_reason_detail, "BLOCK_AFTER_ENTRY_CUTOFF")
            self.assertEqual(by_symbol["GUARD1"].block_source, "order_guard")
            self.assertEqual(by_symbol["GUARD1"].order_guard_rule, "daily_buy_limit")
            self.assertFalse(by_symbol["GUARD1"].would_have_passed_if_order_guard_relaxed)

    def test_reports_are_written_and_missing_values_are_not_zero_filled(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = _make_fixture(Path(tmp))

            result = run_post_market_review(
                target_date=TARGET_DATE,
                mode="paper",
                output_dir=paths["output"],
                condition_capture_path=paths["condition"],
                trade_log_path=paths["trade_log"],
                main_log_path=paths["main_log"],
                intraday_dir=paths["intraday"],
                write_json=True,
            )

            self.assertIsNotNone(result.paths)
            self.assertTrue(result.paths.csv.exists())
            self.assertTrue(result.paths.markdown.exists())
            self.assertTrue(result.paths.json.exists())
            self.assertIn("top_missed_by_mfe", result.paths.extra_csv)
            self.assertIn("sector_theme_missed_summary", result.paths.extra_csv)
            self.assertTrue(result.paths.extra_csv["top_missed_by_mfe"].exists())
            self.assertTrue(result.paths.extra_csv["sector_theme_missed_summary"].exists())
            with result.paths.csv.open("r", newline="", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(list(rows[0].keys()), REVIEW_COLUMNS)
            self.assertIn("missed_reason_detail", rows[0])
            self.assertIn("would_have_passed_if_time_policy_relaxed", rows[0])
            with result.paths.extra_csv["top_missed_by_mfe"].open("r", newline="", encoding="utf-8-sig") as f:
                missed_rows = list(csv.DictReader(f))
            self.assertEqual(missed_rows[0]["symbol"], "CHBAD")
            with result.paths.extra_csv["time_policy_what_if"].open("r", newline="", encoding="utf-8-sig") as f:
                what_if_rows = list(csv.DictReader(f))
            self.assertTrue(any(row["relaxation"] == "recoverable_time_policy_blocks" for row in what_if_rows))
            self.assertIn("paper_strategy_type", what_if_rows[0])
            self.assertIn("avg_close_return_pct", what_if_rows[0])
            self.assertTrue(any(row["relaxation"] == "recoverable_time_policy_blocks_unique" for row in what_if_rows))
            md = result.paths.markdown.read_text(encoding="utf-8")
            self.assertIn("TimePolicy Paper Validation Candidates", md)
            self.assertIn("paper-only validation list", md)
            for field in (
                "entry_time",
                "exit_time",
                "exit_reason_code",
                "exit_type",
                "stop_reason",
                "sell_retry_count",
                "unfilled_exit_qty",
                "sell_order_result",
                "exit_order_no",
                "exit_decision_trace",
                "strategy_name",
                "decision_trace",
                "join_quality",
                "market_regime",
                "market_gate_action",
                "market_gate_reason",
                "sector_regime",
                "sector_gate_action",
                "sector_gate_reason",
                "theme_regime",
                "theme_gate_action",
                "theme_gate_reason",
                "turnover_rank_sector",
                "data_quality",
                "review_category",
            ):
                self.assertIn(field, rows[0])
            win_row = next(row for row in rows if row["symbol"] == "WIN1")
            self.assertEqual(win_row["entry_time"], f"{TARGET_DATE} 09:11:00")
            self.assertEqual(win_row["exit_time"], f"{TARGET_DATE} 09:20:00")
            self.assertEqual(win_row["exit_reason_code"], "take_profit_fixed_pct")
            self.assertEqual(win_row["exit_type"], "profit_take")
            self.assertEqual(win_row["strategy_name"], "momentum-test")
            loss_row = next(row for row in rows if row["symbol"] == "LOSS1")
            self.assertEqual(loss_row["exit_reason_code"], "hard_stop_fixed_pct")
            self.assertEqual(loss_row["exit_type"], "hard_stop")
            self.assertEqual(loss_row["sell_retry_count"], "1")
            no_bar = next(row for row in rows if row["symbol"] == "NOBAR1")
            self.assertEqual(no_bar["mfe_pct"], "")
            self.assertNotEqual(no_bar["mfe_pct"], "0")
            payload = json.loads(result.paths.json.read_text(encoding="utf-8"))
            no_bar_json = next(row for row in payload if row["symbol"] == "NOBAR1")
            self.assertIsNone(no_bar_json["mfe_pct"])
            missed_json = next(row for row in payload if row["symbol"] == "MISS1")
            loss_json = next(row for row in payload if row["symbol"] == "LOSS1")
            self.assertIsInstance(loss_json["exit_decision_trace"], dict)
            self.assertEqual(loss_json["exit_decision_trace"]["matched_rule"], "hard_stop_fixed_pct")
            self.assertIsInstance(missed_json["decision_trace"], dict)
            self.assertEqual(missed_json["market_regime"], "weak")
            self.assertEqual(missed_json["market_gate_action"], "dry_run_block_chase_only")
            self.assertEqual(missed_json["sector_gate_reason"], "GATE_SECTOR_RISK_OFF")
            self.assertEqual(missed_json["theme_gate_action"], "dry_run_allow")
            self.assertEqual(missed_json["turnover_rank_sector"], 3.0)
            self.assertEqual(missed_json["decision_trace"]["market_gate_reason"], "GATE_MARKET_WEAK_CHASE_BLOCK")
            self.assertEqual(missed_json["decision_trace"]["momentum_decision"], "REJECT")
            self.assertEqual(missed_json["decision_trace"]["legacy_decision"], "READY")
            self.assertEqual(missed_json["decision_trace"]["time_policy_decision"], "ALLOW_ENTRY")
            self.assertIsNone(missed_json["decision_trace"]["order_guard_decision"])
            self.assertEqual(missed_json["decision_trace"]["final_reason"], "weak volume")
            md = result.paths.markdown.read_text(encoding="utf-8")
            self.assertIn("Missed Opportunities", md)
            self.assertIn("Good Rejects", md)
            self.assertIn("Reason Code Ranking", md)
            self.assertIn("Exit Type Performance", md)
            self.assertIn("hard_stop_fixed_pct", md)
            self.assertIn("Block Chase Review", md)
            self.assertIn("Data Quality Blocks", md)
            self.assertIn("Time Policy Blocks", md)
            self.assertIn("OrderGuard Blocks", md)
            self.assertIn("n_mfe", md)
            self.assertIn("missing_mfe", md)

    def test_markdown_reports_sector_theme_map_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = _make_fixture(root)
            sector_map = root / "sector_map.csv"
            theme_map = root / "theme_map.csv"
            sector_map.write_text("code,name,market,sector_code,sector_name,sector_index_code\n", encoding="utf-8")
            theme_map.write_text("theme_name,code,role\n", encoding="utf-8")

            result = run_post_market_review(
                target_date=TARGET_DATE,
                mode="paper",
                output_dir=paths["output"],
                condition_capture_path=paths["condition"],
                trade_log_path=paths["trade_log"],
                main_log_path=paths["main_log"],
                intraday_dir=paths["intraday"],
                sector_map_path=sector_map,
                theme_map_path=theme_map,
                write_json=True,
            )

            self.assertEqual(result.data_source_status["sector_map"]["status"], "header_only")
            self.assertEqual(result.data_source_status["theme_map"]["status"], "header_only")
            md = result.paths.markdown.read_text(encoding="utf-8")
            self.assertIn("Data Source Status", md)
            self.assertIn("| sector_map | header_only |", md)
            self.assertIn("| theme_map | header_only |", md)
            self.assertIn("fallback-only", md)
            self.assertTrue(all(not row.context_fields.get("sector_name") for row in result.rows))

    def test_static_sector_theme_maps_enrich_review_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            condition_path = root / "condition_captures.csv"
            _write_csv(
                condition_path,
                [
                    "logged_at",
                    "event",
                    "detected_at",
                    "code",
                    "name",
                    "condition_name",
                    "strategy_name",
                    "capture_price",
                ],
                [
                    {
                        "logged_at": f"{TARGET_DATE} 09:00:00",
                        "event": "condition_detected",
                        "detected_at": f"{TARGET_DATE} 09:00:00",
                        "code": "005930",
                        "name": "Samsung",
                        "condition_name": "quant",
                        "strategy_name": "static-map-test",
                        "capture_price": "10000",
                    }
                ],
            )
            _write_bars(root, "005930", "09:00:00", [10000, 10100, 10200])
            (root / "main.log").write_text("", encoding="utf-8")
            _write_csv(root / "trade_log.csv", ["logged_at", "event", "code"], [])
            sector_map = root / "sector_map.csv"
            theme_map = root / "theme_map.csv"
            _write_csv(
                sector_map,
                ["code", "name", "market", "sector_code", "sector_name", "sector_index_code"],
                [
                    {
                        "code": "005930",
                        "name": "Samsung",
                        "market": "KOSPI",
                        "sector_code": "101",
                        "sector_name": "반도체| ",
                        "sector_index_code": "IDX101",
                    }
                ],
            )
            _write_csv(
                theme_map,
                ["theme_name", "code", "role"],
                [
                    {"theme_name": "AI", "code": "005930", "role": "member"},
                    {"theme_name": "반도체", "code": "005930", "role": "leader"},
                    {"theme_name": "반도체", "code": "000660", "role": "member"},
                ],
            )

            result = run_post_market_review(
                target_date=TARGET_DATE,
                mode="paper",
                output_dir=root / "reports",
                condition_capture_path=condition_path,
                trade_log_path=root / "trade_log.csv",
                main_log_path=root / "main.log",
                intraday_dir=root / "intraday",
                sector_map_path=sector_map,
                theme_map_path=theme_map,
                write_json=True,
            )

            row = result.rows[0]
            self.assertEqual(row.context_fields["sector_code"], "101")
            self.assertEqual(row.context_fields["sector_name"], "반도체")
            self.assertEqual(row.context_fields["sector_index_code"], "IDX101")
            self.assertEqual(row.context_fields["theme_names"], "AI;반도체")
            self.assertEqual(row.context_fields["primary_theme"], "반도체")
            self.assertEqual(row.context_fields["theme_member_count"], 2)
            payload = json.loads(result.paths.json.read_text(encoding="utf-8"))
            self.assertEqual(payload[0]["sector_name"], "반도체")
            self.assertEqual(payload[0]["primary_theme"], "반도체")
            self.assertEqual(payload[0]["theme_member_count"], 2)

    def test_static_maps_do_not_overwrite_logged_context_or_gate_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            condition_path = root / "condition_captures.csv"
            _write_csv(
                condition_path,
                [
                    "logged_at",
                    "event",
                    "detected_at",
                    "code",
                    "name",
                    "condition_name",
                    "strategy_name",
                    "capture_price",
                ],
                [
                    {
                        "logged_at": f"{TARGET_DATE} 09:00:00",
                        "event": "condition_detected",
                        "detected_at": f"{TARGET_DATE} 09:00:00",
                        "code": "000660",
                        "name": "SK Hynix",
                        "condition_name": "quant",
                        "strategy_name": "static-map-test",
                        "capture_price": "10000",
                    }
                ],
            )
            _write_bars(root, "000660", "09:00:00", [10000, 10100, 10200])
            (root / "main.log").write_text(
                _log_line(
                    "momentum_entry_decision",
                    {
                        "event": "momentum_entry_decision",
                        "timestamp": f"{TARGET_DATE} 09:00:10",
                        "symbol": "000660",
                        "decision": "REJECT",
                        "reason_code": "weak_volume_ratio",
                        "sector_name": "Logged Sector",
                        "sector_code": "LOG",
                        "sector_regime": "risk_off",
                        "sector_gate_reason": "KEEP_SECTOR_GATE",
                        "theme_names": "LoggedTheme",
                        "primary_theme": "LoggedPrimary",
                        "theme_member_count": 7,
                        "theme_regime": "neutral",
                        "theme_gate_reason": "KEEP_THEME_GATE",
                    },
                ),
                encoding="utf-8",
            )
            _write_csv(root / "trade_log.csv", ["logged_at", "event", "code"], [])
            sector_map = root / "sector_map.csv"
            theme_map = root / "theme_map.csv"
            _write_csv(
                sector_map,
                ["code", "name", "market", "sector_code", "sector_name", "sector_index_code"],
                [
                    {
                        "code": "000660",
                        "name": "SK Hynix",
                        "market": "KOSPI",
                        "sector_code": "101",
                        "sector_name": "반도체",
                        "sector_index_code": "IDX101",
                    }
                ],
            )
            _write_csv(
                theme_map,
                ["theme_name", "code", "role"],
                [{"theme_name": "반도체", "code": "000660", "role": "leader"}],
            )

            result = run_post_market_review(
                target_date=TARGET_DATE,
                mode="paper",
                output_dir=root / "reports",
                condition_capture_path=condition_path,
                trade_log_path=root / "trade_log.csv",
                main_log_path=root / "main.log",
                intraday_dir=root / "intraday",
                sector_map_path=sector_map,
                theme_map_path=theme_map,
                write_json=True,
            )

            row = result.rows[0]
            self.assertEqual(row.context_fields["sector_name"], "Logged Sector")
            self.assertEqual(row.context_fields["sector_code"], "LOG")
            self.assertEqual(row.context_fields["theme_names"], "LoggedTheme")
            self.assertEqual(row.context_fields["primary_theme"], "LoggedPrimary")
            self.assertEqual(row.context_fields["theme_member_count"], 7)
            self.assertEqual(row.sector_gate_reason, "KEEP_SECTOR_GATE")
            self.assertEqual(row.theme_gate_reason, "KEEP_THEME_GATE")

    def test_post_market_readme_and_docs_index_links_exist(self):
        readme = Path("reports") / "post_market" / "README.md"
        self.assertTrue(readme.exists())
        text = readme.read_text(encoding="utf-8")
        self.assertIn("python -m tools.post_market_review", text)
        self.assertIn("missing 값은 0이 아닙니다", text)
        self.assertIn("docs/POST_MARKET_REVIEW_GUIDE.md", text)

        docs_index = Path("docs") / "README.md"
        root_readme = Path("README.md")
        combined = ""
        if docs_index.exists():
            combined += docs_index.read_text(encoding="utf-8", errors="replace")
        if root_readme.exists():
            combined += root_readme.read_text(encoding="utf-8", errors="replace")
        self.assertIn("POST_MARKET_REVIEW_GUIDE.md", combined)

    def test_sanitized_rotated_log_fixture_generates_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            condition_path = root / "condition_captures.csv"
            _write_rotated_log_condition_fixture(condition_path)
            _write_bars(root, "ROT1", "09:00:00", [10000, 10100, 10200, 10150])
            rotated_log = POST_MARKET_FIXTURE_DIR / "main.log.1"

            result = run_post_market_review(
                target_date=TARGET_DATE,
                mode="paper",
                output_dir=root / "reports",
                condition_capture_path=condition_path,
                trade_log_path=root / "missing_trade_log.csv",
                main_log_path=rotated_log,
                intraday_dir=root / "intraday",
                min_missed_opportunity_pct=0.02,
                write_json=True,
            )

            by_symbol = {row.symbol: row for row in result.rows}
            self.assertEqual(by_symbol["ROT1"].join_quality, "exact_candidate_id")
            self.assertEqual(by_symbol["ROT1"].reason_code, "weak_volume_ratio")
            self.assertEqual(by_symbol["ROT2"].join_quality, "fallback_symbol_time")
            self.assertIn("strategy_name_fallback_used", by_symbol["ROT2"].data_quality)
            self.assertIn("MISSING_MARKET_METRICS", by_symbol["ROT2"].data_quality)

            with result.paths.csv.open("r", newline="", encoding="utf-8-sig") as f:
                csv_rows = list(csv.DictReader(f))
            rot2 = next(row for row in csv_rows if row["symbol"] == "ROT2")
            self.assertEqual(rot2["mfe_pct"], "")
            self.assertNotEqual(rot2["mfe_pct"], "0")

            payload = json.loads(result.paths.json.read_text(encoding="utf-8"))
            rot1 = next(row for row in payload if row["symbol"] == "ROT1")
            self.assertIsInstance(rot1["decision_trace"], dict)
            self.assertEqual(rot1["decision_trace"]["momentum_decision"], "REJECT")

            md = result.paths.markdown.read_text(encoding="utf-8")
            self.assertIn("Reason Code Ranking", md)
            self.assertIn("Data Quality Blocks", md)

    def test_real_rotated_main_log_integration_when_available(self):
        real_log = Path("data") / "main.log.1"
        if not real_log.exists():
            self.skipTest("data/main.log.1 not found; skipping real rotated log integration test")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            condition_path = root / "condition_captures.csv"
            _write_rotated_log_condition_fixture(condition_path)

            result = run_post_market_review(
                target_date=TARGET_DATE,
                mode="paper",
                output_dir=root / "reports",
                condition_capture_path=condition_path,
                trade_log_path=root / "missing_trade_log.csv",
                main_log_path=real_log,
                intraday_dir=root / "intraday",
                write_json=True,
            )

            self.assertTrue(result.paths.csv.exists())
            self.assertTrue(result.paths.markdown.exists())
            self.assertTrue(result.paths.json.exists())
            with result.paths.csv.open("r", newline="", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(list(rows[0].keys()), REVIEW_COLUMNS)
            for row in rows:
                if row["mfe_pct"] == "":
                    self.assertNotEqual(row["mfe_pct"], "0")

    def test_live_mode_is_separate_from_paper_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = _make_fixture(Path(tmp))

            live = run_post_market_review(
                target_date=TARGET_DATE,
                mode="live",
                output_dir=paths["output"],
                condition_capture_path=paths["condition"],
                trade_log_path=paths["trade_log"],
                main_log_path=paths["main_log"],
                intraday_dir=paths["intraday"],
            )
            paper = run_post_market_review(
                target_date=TARGET_DATE,
                mode="paper",
                output_dir=paths["output"],
                condition_capture_path=paths["condition"],
                trade_log_path=paths["trade_log"],
                main_log_path=paths["main_log"],
                intraday_dir=paths["intraday"],
            )

            self.assertEqual(sum(1 for row in live.rows if row.traded), 0)
            self.assertEqual(sum(1 for row in paper.rows if row.traded), 2)
            self.assertIn("_live_", live.paths.csv.name)
            self.assertIn("_paper_", paper.paths.csv.name)

    def test_reason_stats_exclude_missing_mfe_mae(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = _make_fixture(Path(tmp))

            result = run_post_market_review(
                target_date=TARGET_DATE,
                mode="paper",
                output_dir=paths["output"],
                condition_capture_path=paths["condition"],
                trade_log_path=paths["trade_log"],
                main_log_path=paths["main_log"],
                intraday_dir=paths["intraday"],
                min_missed_opportunity_pct=0.02,
            )

            stats = {
                item["reason_code"]: item
                for item in post_market._reason_code_stats([row for row in result.rows if not row.traded])
            }
            weak = stats["weak_volume_ratio"]
            miss_row = next(row for row in result.rows if row.symbol == "MISS1")
            self.assertEqual(weak["count"], 2)
            self.assertEqual(weak["n_mfe"], 1)
            self.assertEqual(weak["n_mae"], 1)
            self.assertEqual(weak["missing_mfe"], 1)
            self.assertEqual(weak["missing_mae"], 1)
            self.assertAlmostEqual(weak["avg_mfe_pct"], miss_row.mfe_pct)
            self.assertAlmostEqual(weak["avg_mae_pct"], miss_row.mae_pct)

            nobar_row = next(row for row in result.rows if row.symbol == "NOBAR1")
            missing_only = post_market._reason_code_stats([nobar_row])[0]
            self.assertIsNone(missing_only["avg_mfe_pct"])
            self.assertIsNone(missing_only["avg_mae_pct"])
            self.assertEqual(missing_only["n_mfe"], 0)
            self.assertEqual(missing_only["n_mae"], 0)

    def test_cli_all_mode_writes_paper_and_live_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = _make_fixture(Path(tmp))
            rc = post_market_cli.main(
                [
                    "--date",
                    TARGET_DATE,
                    "--mode",
                    "all",
                    "--output",
                    str(paths["output"]),
                    "--condition-captures",
                    str(paths["condition"]),
                    "--trade-log",
                    str(paths["trade_log"]),
                    "--main-log",
                    str(paths["main_log"]),
                    "--intraday-dir",
                    str(paths["intraday"]),
                ]
            )

            self.assertEqual(rc, 0)
            self.assertTrue((paths["output"] / f"{YYYYMMDD}_paper_condition_review.csv").exists())
            self.assertTrue((paths["output"] / f"{YYYYMMDD}_live_condition_review.csv").exists())
            self.assertTrue((paths["output"] / f"{YYYYMMDD}_paper_condition_review.json").exists())
            self.assertTrue((paths["output"] / f"{YYYYMMDD}_live_condition_review.json").exists())

    def test_candidate_id_join_wins_over_symbol_time_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            condition_path = root / "condition_captures.csv"
            fields = [
                "logged_at",
                "event",
                "source_event",
                "created_at",
                "candidate_id",
                "symbol",
                "symbol_name",
                "detected_at",
                "captured_at",
                "captured_time",
                "code",
                "name",
                "condition_name",
                "strategy_name",
                "capture_price",
                "signal_source",
            ]
            _write_csv(
                condition_path,
                fields,
                [
                    {
                        "logged_at": f"{TARGET_DATE} 09:00:00",
                        "event": "condition_detected",
                        "source_event": "condition_detected",
                        "created_at": f"{TARGET_DATE} 09:00:00",
                        "candidate_id": "cid-first",
                        "symbol": "SAME1",
                        "symbol_name": "First",
                        "detected_at": f"{TARGET_DATE} 09:00:00",
                        "captured_at": f"{TARGET_DATE} 09:00:00",
                        "captured_time": "090000",
                        "code": "SAME1",
                        "name": "First",
                        "condition_name": "quant_condition",
                        "strategy_name": "momentum-test",
                        "capture_price": "10000",
                        "signal_source": "HTS_CONDITION_SEARCH",
                    },
                    {
                        "logged_at": f"{TARGET_DATE} 09:30:00",
                        "event": "condition_detected",
                        "source_event": "condition_detected",
                        "created_at": f"{TARGET_DATE} 09:30:00",
                        "candidate_id": "cid-second",
                        "symbol": "SAME1",
                        "symbol_name": "Second",
                        "detected_at": f"{TARGET_DATE} 09:30:00",
                        "captured_at": f"{TARGET_DATE} 09:30:00",
                        "captured_time": "093000",
                        "code": "SAME1",
                        "name": "Second",
                        "condition_name": "quant_condition",
                        "strategy_name": "momentum-test",
                        "capture_price": "10000",
                        "signal_source": "HTS_CONDITION_SEARCH",
                    },
                ],
            )
            (root / "main.log").write_text(
                _log_line(
                    "momentum_entry_decision",
                    {
                        "event": "momentum_entry_decision",
                        "timestamp": f"{TARGET_DATE} 09:00:05",
                        "symbol": "SAME1",
                        "candidate_id": "cid-second",
                        "decision": "REJECT",
                        "reason_code": "candidate_id_reason",
                    },
                ),
                encoding="utf-8",
            )

            result = run_post_market_review(
                target_date=TARGET_DATE,
                mode="paper",
                output_dir=root / "reports",
                condition_capture_path=condition_path,
                trade_log_path=root / "missing_trade_log.csv",
                main_log_path=root / "main.log",
                intraday_dir=root / "intraday",
            )

            by_id = {row.candidate_id: row for row in result.rows}
            self.assertEqual(by_id["cid-second"].reason_code, "candidate_id_reason")
            self.assertEqual(by_id["cid-second"].join_quality, "exact_candidate_id")
            self.assertNotEqual(by_id["cid-first"].reason_code, "candidate_id_reason")

    def test_ready_final_event_is_preserved_when_later_block_arrives(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fields = [
                "logged_at",
                "event",
                "source_event",
                "created_at",
                "candidate_id",
                "symbol",
                "symbol_name",
                "detected_at",
                "captured_at",
                "captured_time",
                "code",
                "name",
                "condition_name",
                "strategy_name",
                "capture_price",
                "signal_source",
                "symbol_market",
                "primary_index_code",
            ]
            _write_csv(
                root / "condition_captures.csv",
                fields,
                [
                    {
                        "logged_at": f"{TARGET_DATE} 09:00:00",
                        "event": "condition_detected",
                        "source_event": "condition_detected",
                        "created_at": f"{TARGET_DATE} 09:00:00",
                        "candidate_id": "cid-ready",
                        "symbol": "READY1",
                        "symbol_name": "Ready One",
                        "detected_at": f"{TARGET_DATE} 09:00:00",
                        "captured_at": f"{TARGET_DATE} 09:00:00",
                        "captured_time": "090000",
                        "code": "READY1",
                        "name": "Ready One",
                        "condition_name": "quant_condition",
                        "strategy_name": "momentum-test",
                        "capture_price": "10000",
                        "signal_source": "HTS_CONDITION_SEARCH",
                        "symbol_market": "KOSDAQ",
                        "primary_index_code": "201",
                    },
                ],
            )
            events = [
                _log_line(
                    "momentum_entry_decision",
                    {
                        "event": "momentum_entry_decision",
                        "timestamp": f"{TARGET_DATE} 09:01:00",
                        "symbol": "READY1",
                        "candidate_id": "cid-ready",
                        "decision": "BUY",
                        "reason_code": "buy_pullback_reclaim",
                        "current_price": 10100,
                        "market_data_available": True,
                        "candle_cache_available": True,
                    },
                ),
                _log_line(
                    "final_entry_decision",
                    {
                        "event": "final_entry_decision",
                        "timestamp": f"{TARGET_DATE} 09:01:00",
                        "symbol": "READY1",
                        "candidate_id": "cid-ready",
                        "allowed": True,
                        "status": "ready",
                        "reason_code": "FINAL_BUY_READY",
                        "final_reason": "ready",
                        "current_price": 10100,
                        "symbol_market": "KOSDAQ",
                        "primary_index_code": "201",
                    },
                ),
                _log_line(
                    "momentum_entry_decision",
                    {
                        "event": "momentum_entry_decision",
                        "timestamp": f"{TARGET_DATE} 09:02:00",
                        "symbol": "READY1",
                        "candidate_id": "cid-ready",
                        "decision": "REJECT",
                        "reason_code": "weak_volume_ratio",
                        "current_price": 9900,
                        "market_data_available": True,
                        "candle_cache_available": True,
                    },
                ),
                _log_line(
                    "final_entry_decision",
                    {
                        "event": "final_entry_decision",
                        "timestamp": f"{TARGET_DATE} 09:02:00",
                        "symbol": "READY1",
                        "candidate_id": "cid-ready",
                        "allowed": False,
                        "status": "blocked",
                        "reason_code": "FINAL_MOMENTUM_WEAK_VOLUME_RATIO",
                        "final_reason": "weak volume",
                        "current_price": 9900,
                    },
                ),
                _log_line(
                    "recovery_watch_queued",
                    {
                        "event": "recovery_watch_queued",
                        "timestamp": f"{TARGET_DATE} 09:02:01",
                        "symbol": "READY1",
                        "candidate_id": "cid-ready",
                        "reason_code": "FINAL_MOMENTUM_WEAK_VOLUME_RATIO",
                        "delay_seconds": 15,
                        "symbol_market": "KOSDAQ",
                    },
                ),
            ]
            (root / "main.log").write_text("".join(events), encoding="utf-8")
            _write_csv(
                root / "trade_log.csv",
                [
                    "logged_at",
                    "event",
                    "candidate_id",
                    "code",
                    "name",
                    "side",
                    "reason_code",
                    "reason",
                    "blocked_by",
                    "message",
                ],
                [
                    {
                        "logged_at": f"{TARGET_DATE} 09:01:05",
                        "event": "buy_skip",
                        "candidate_id": "cid-ready",
                        "code": "READY1",
                        "name": "Ready One",
                        "side": "buy",
                        "reason_code": "SHOULD_SKIP_BUY_MISSING_FIRST_POSITION_FOR_STAGE2",
                        "reason": "should_skip_buy",
                        "blocked_by": "position_state",
                        "message": "stage 2 entry requires an existing first position",
                    }
                ],
            )
            _write_bars(root, "READY1", "09:00:00", [10000, 10100, 10200, 9900])

            result = run_post_market_review(
                target_date=TARGET_DATE,
                mode="paper",
                output_dir=root / "reports",
                condition_capture_path=root / "condition_captures.csv",
                trade_log_path=root / "trade_log.csv",
                main_log_path=root / "main.log",
                intraday_dir=root / "intraday",
                min_missed_opportunity_pct=0.02,
                write_json=True,
            )

            row = result.rows[0]
            self.assertEqual(row.final_decision, "BUY")
            self.assertEqual(row.reason_code, "FINAL_BUY_READY")
            self.assertEqual(row.current_price, 10100)
            self.assertEqual(row.order_guard_reason, "SHOULD_SKIP_BUY_MISSING_FIRST_POSITION_FOR_STAGE2")
            self.assertEqual(row.review_category, "ORDER_GUARD_BLOCK")
            self.assertTrue(row.blocked_after_buy_ready)
            self.assertTrue(row.would_have_passed_if_order_guard_relaxed)
            self.assertEqual(row.order_guard_rule, "missing_first_position_for_stage2")
            self.assertTrue(row.order_guard_recoverable)
            self.assertEqual(row.context_fields["symbol_market"], "KOSDAQ")
            self.assertIn("recovery_watch_queued", row.candidate_lifecycle)
            self.assertEqual(row.recovery_watch_count, 1)
            self.assertEqual(row.recovery_watch_reasons, "FINAL_MOMENTUM_WEAK_VOLUME_RATIO")
            self.assertEqual(row.recovery_watch_delay_seconds, 15)
            self.assertIn("FINAL_READY_SUPERSEDED_BY_LATER_EVENT", row.data_quality)

            payload = json.loads(result.paths.json.read_text(encoding="utf-8"))
            ready_json = payload[0]
            self.assertEqual(ready_json["symbol_market"], "KOSDAQ")
            self.assertEqual(ready_json["primary_index_code"], "201")
            self.assertEqual(ready_json["recovery_watch_count"], 1)
            self.assertEqual(ready_json["recovery_watch_reasons"], "FINAL_MOMENTUM_WEAK_VOLUME_RATIO")

            md = result.paths.markdown.read_text(encoding="utf-8")
            self.assertIn("Recovery Watch", md)
            self.assertIn("FINAL_MOMENTUM_WEAK_VOLUME_RATIO", md)

    def test_unknown_candidate_id_does_not_fallback_to_same_symbol(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fields = [
                "logged_at",
                "event",
                "source_event",
                "created_at",
                "candidate_id",
                "symbol",
                "symbol_name",
                "detected_at",
                "captured_at",
                "captured_time",
                "code",
                "name",
                "condition_name",
                "strategy_name",
                "capture_price",
                "signal_source",
            ]
            _write_csv(
                root / "condition_captures.csv",
                fields,
                [
                    {
                        "logged_at": f"{TARGET_DATE} 09:00:00",
                        "event": "condition_detected",
                        "source_event": "condition_detected",
                        "created_at": f"{TARGET_DATE} 09:00:00",
                        "candidate_id": "cid-real",
                        "symbol": "SAME1",
                        "symbol_name": "Real Candidate",
                        "detected_at": f"{TARGET_DATE} 09:00:00",
                        "captured_at": f"{TARGET_DATE} 09:00:00",
                        "captured_time": "090000",
                        "code": "SAME1",
                        "name": "Real Candidate",
                        "condition_name": "quant_condition",
                        "strategy_name": "momentum-test",
                        "capture_price": "10000",
                        "signal_source": "HTS_CONDITION_SEARCH",
                    },
                ],
            )
            (root / "main.log").write_text(
                _log_line(
                    "momentum_entry_decision",
                    {
                        "event": "momentum_entry_decision",
                        "timestamp": f"{TARGET_DATE} 09:00:05",
                        "symbol": "SAME1",
                        "candidate_id": "cid-foreign",
                        "decision": "REJECT",
                        "reason_code": "foreign_reason",
                    },
                ),
                encoding="utf-8",
            )

            result = run_post_market_review(
                target_date=TARGET_DATE,
                mode="paper",
                output_dir=root / "reports",
                condition_capture_path=root / "condition_captures.csv",
                trade_log_path=root / "missing_trade_log.csv",
                main_log_path=root / "main.log",
                intraday_dir=root / "intraday",
            )

            self.assertNotEqual(result.rows[0].reason_code, "foreign_reason")
            self.assertEqual(result.rows[0].join_quality, "missing_join")

    def test_legacy_logs_without_candidate_id_use_fallback_join_quality(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fields, rows = _condition_rows()
            _write_csv(root / "condition_captures.csv", fields, rows[:2])
            (root / "main.log").write_text(
                _log_line(
                    "momentum_entry_decision",
                    {
                        "event": "momentum_entry_decision",
                        "timestamp": f"{TARGET_DATE} 09:10:30",
                        "symbol": "WIN1",
                        "decision": "REJECT",
                        "reason_code": "legacy_reason",
                    },
                ),
                encoding="utf-8",
            )

            result = run_post_market_review(
                target_date=TARGET_DATE,
                mode="paper",
                output_dir=root / "reports",
                condition_capture_path=root / "condition_captures.csv",
                trade_log_path=root / "missing_trade_log.csv",
                main_log_path=root / "main.log",
                intraday_dir=root / "intraday",
            )

            self.assertEqual(result.rows[0].reason_code, "legacy_reason")
            self.assertEqual(result.rows[0].join_quality, "fallback_symbol_time")

    def test_candidate_recreated_after_ttl_is_reported_as_lifecycle_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fields, rows = _condition_rows()
            fields = list(fields) + ["candidate_id"]
            rows[0]["candidate_id"] = "cid-recreated"
            rows[1]["candidate_id"] = "cid-recreated"
            _write_csv(root / "condition_captures.csv", fields, rows[:2])
            (root / "main.log").write_text(
                _log_line(
                    "candidate_recreated_after_ttl",
                    {
                        "event": "candidate_recreated_after_ttl",
                        "timestamp": f"{TARGET_DATE} 09:10:01",
                        "symbol": "WIN1",
                        "candidate_id": "cid-recreated",
                        "old_candidate_id": "cid-old",
                        "lifecycle_state": "recreated_after_ttl",
                    },
                ),
                encoding="utf-8",
            )

            result = run_post_market_review(
                target_date=TARGET_DATE,
                mode="paper",
                output_dir=root / "reports",
                condition_capture_path=root / "condition_captures.csv",
                trade_log_path=root / "missing_trade_log.csv",
                main_log_path=root / "main.log",
                intraday_dir=root / "intraday",
            )

            self.assertEqual(result.rows[0].candidate_lifecycle, "recreated_after_ttl")
            self.assertEqual(result.rows[0].join_quality, "exact_candidate_id")

    def test_post_market_modules_do_not_reference_live_order_api(self):
        combined = inspect.getsource(post_market) + inspect.getsource(post_market_cli)

        self.assertNotIn("SendOrder", combined)
        self.assertNotIn("dynamicCall", combined)
        self.assertNotIn("send_order", combined)
        self.assertNotIn("submit_order_guarded", combined)
        self.assertNotIn("place_buy_order", combined)


if __name__ == "__main__":
    unittest.main()
