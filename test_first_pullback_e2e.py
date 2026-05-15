from __future__ import annotations

import sys
import types
import unittest
from unittest import mock


def _ensure_external_stubs() -> None:
    if "PyQt5" not in sys.modules:
        qax = types.ModuleType("PyQt5.QAxContainer")
        qax.QAxWidget = mock.MagicMock
        qax.__all__ = ["QAxWidget"]

        widgets = types.ModuleType("PyQt5.QtWidgets")
        widgets.QApplication = mock.MagicMock
        widgets.QWidget = mock.MagicMock
        widgets.__all__ = ["QApplication", "QWidget"]

        core = types.ModuleType("PyQt5.QtCore")
        core.QTimer = mock.MagicMock
        core.QObject = mock.MagicMock
        core.pyqtSignal = mock.MagicMock()
        core.__all__ = ["QTimer", "QObject", "pyqtSignal"]

        pyqt5 = types.ModuleType("PyQt5")
        pyqt5.QAxContainer = qax
        pyqt5.QtWidgets = widgets
        pyqt5.QtCore = core

        sys.modules["PyQt5"] = pyqt5
        sys.modules["PyQt5.QAxContainer"] = qax
        sys.modules["PyQt5.QtWidgets"] = widgets
        sys.modules["PyQt5.QtCore"] = core

    if "pandas" not in sys.modules:
        sys.modules["pandas"] = mock.MagicMock()


_ensure_external_stubs()

from bars import MinuteBar  # noqa: E402
from candidate_registry import (  # noqa: E402
    CONDITION_COMBO_DANTE_ONLY,
    CONDITION_COMBO_QUANT_AND_DANTE,
    CONDITION_COMBO_QUANT_ONLY,
    CandidateRegistry,
)
from momentum_breakout_strategy import (  # noqa: E402
    ENTRY_TYPE_BREAKOUT_SMALL,
    ENTRY_TYPE_PULLBACK_RECLAIM,
    EntryDecision,
    MomentumDecision,
)
from order_guard import (  # noqa: E402
    LIVE_ANALYSIS_ONLY_REASON_CODE,
    LIVE_BREAKOUT_BLOCK_REASON_CODE,
    OrderGuard,
    OrderRequest,
    RiskState,
)
from portfolio import PortfolioState  # noqa: E402
from quant_condition_strategy import QuantConditionStrategy, QuantStrategyConfig  # noqa: E402
from trade_config import TradeConfig  # noqa: E402

import main  # noqa: E402


class _MarketState:
    class _Snapshot:
        market_regime = "neutral"

    def snapshot(self):
        return self._Snapshot()


class _MinuteAggregator:
    def __init__(self, *, vwap: float = 10_420.0, low_after_high: int = 10_400):
        self.vwap = vwap
        self.low_after_high = low_after_high

    def all_bars(self, code):
        return [
            MinuteBar(1, 10_000, 10_800, 10_000, 10_450, 200_000, 0),
            MinuteBar(2, 10_450, 10_520, 10_400, 10_500, 120_000, 0),
        ]

    def intraday_vwap(self, code):
        return self.vwap

    def pullback_low_after_high(self, code):
        return self.low_after_high

    def first_pullback_reversal_confirmed(self, code, *, current_price):
        return True

    def sma_close(self, code, count):
        return 10_480


class _MomentumPass:
    def __init__(self):
        self.last_context = None

    def evaluate(self, ctx):
        self.last_context = ctx
        metrics = {
            "age_seconds": 120.0,
            "leader_score": ctx.leader_score,
            "trade_value_since_capture": ctx.trade_value_since_capture,
            "turnover_speed_per_min": ctx.turnover_speed_per_min or 0.0,
            "volume_ratio_1m": ctx.volume_ratio_1m or 0.0,
            "volume_ratio_5m": ctx.volume_ratio_5m or 0.0,
            "turnover_rank_market": ctx.turnover_rank_market,
            "turnover_rank_sector": ctx.turnover_rank_sector,
            "pullback_pct": ctx.pullback_from_high_pct,
            "pullback_dry_run": {},
        }
        return MomentumDecision(
            EntryDecision.BUY,
            "pullback reclaim test pass",
            "BUY_PULLBACK_RECLAIM",
            chase_risk_score=10.0,
            entry_ratio=1.0,
            entry_type=ENTRY_TYPE_PULLBACK_RECLAIM,
            position_size_multiplier=1.0,
            metrics=metrics,
        )


class _MomentumBreakoutProbe:
    def __init__(self):
        self.last_context = None

    def evaluate(self, ctx):
        self.last_context = ctx
        metrics = {
            "age_seconds": 120.0,
            "leader_score": ctx.leader_score,
            "trade_value_since_capture": ctx.trade_value_since_capture,
            "turnover_speed_per_min": ctx.turnover_speed_per_min or 0.0,
            "volume_ratio_1m": ctx.volume_ratio_1m or 0.0,
            "volume_ratio_5m": ctx.volume_ratio_5m or 0.0,
            "turnover_rank_market": ctx.turnover_rank_market,
            "turnover_rank_sector": ctx.turnover_rank_sector,
            "pullback_pct": ctx.pullback_from_high_pct,
            "paper_only_breakout_probe": 1.0,
            "orderable_live": 0.0,
            "pullback_dry_run": {},
        }
        return MomentumDecision(
            EntryDecision.BUY,
            "breakout small probe test",
            "BUY_BREAKOUT_SMALL",
            chase_risk_score=8.0,
            entry_ratio=0.25,
            entry_type=ENTRY_TYPE_BREAKOUT_SMALL,
            position_size_multiplier=0.25,
            metrics=metrics,
        )


class _FirstPullbackStub:
    parse_int = main.Kiwoom.parse_int
    parse_float = main.Kiwoom.parse_float
    ensure_monitoring_stock = main.Kiwoom.ensure_monitoring_stock
    monitoring_volume_5m = main.Kiwoom.monitoring_volume_5m
    monitoring_volume_window = main.Kiwoom.monitoring_volume_window
    monitoring_volume_1m = main.Kiwoom.monitoring_volume_1m
    update_monitoring_tick = main.Kiwoom.update_monitoring_tick
    build_momentum_context = main.Kiwoom.build_momentum_context
    score_safe_pullback_trade = main.Kiwoom.score_safe_pullback_trade
    build_final_entry_decision = main.Kiwoom.build_final_entry_decision
    apply_final_entry_decision = main.Kiwoom.apply_final_entry_decision
    final_entry_block_prediction = main.Kiwoom.final_entry_block_prediction
    _condition_log_meta = main.Kiwoom._condition_log_meta
    current_open_position_risk = main.Kiwoom.current_open_position_risk
    build_position_size_plan = main.Kiwoom.build_position_size_plan
    format_position_size_plan = main.Kiwoom.format_position_size_plan
    place_buy_order = main.Kiwoom.place_buy_order
    submit_order_guarded = main.Kiwoom.submit_order_guarded

    def __init__(
        self,
        *,
        vwap: float = 10_420.0,
        low_after_high: int = 10_400,
        rich_leader: bool = True,
        with_candidate: bool = True,
    ):
        self.rich_leader = rich_leader
        self.monitoring_dict = {}
        self.realtime_ticks = {}
        self.condition_registered_at = {}
        self.quant_strategy = QuantConditionStrategy()
        self.momentum_strategy = _MomentumPass()
        self.minute_aggregator = _MinuteAggregator(
            vwap=vwap,
            low_after_high=low_after_high,
        )
        self.five_min_cache = {}
        self.market_state = _MarketState()
        self.portfolio = PortfolioState()
        self.order_context = {}
        self.order_prices = {}
        self.entry_times = {}
        self.highest_prices = {}
        self.pending_order_codes = set()
        self.bought_codes = set()
        self.best = {}
        self.target_returns = {}
        self.dante_reentry_watchlist = {}
        self.dante_a_watchlist = {}
        self.trade_log_calls = []
        self.last_order_guard_decision = None
        self.order_guard = OrderGuard(
            TradeConfig(
                dry_run=True,
                live_trading_enabled=True,
                paper_portfolio_enabled=False,
                time_policy_enabled=False,
                max_position_size=10_000_000,
                max_daily_exposure=100_000_000,
            )
        )
        if with_candidate:
            self.candidate_registry = CandidateRegistry(
                primary_condition_name=main.PRIMARY_CONDITION_NAME,
                bonus_condition_name=main.BONUS_CONDITION_NAME,
            )

    def normalize_code(self, code):
        return str(code or "").strip().lstrip("A")

    def get_code_name(self, code):
        return "테스트"

    def active_position_count(self):
        return 0

    def evaluate_time_filter(self, code, *, current_price, accum_volume):
        return {
            "ok": True,
            "phase": "test",
            "weight": 1.0,
            "daily_turnover": current_price * accum_volume,
            "turnover_rank": 1,
            "ranked_count": 1,
        }

    def realtime_daily_turnover(self, code, *, current_price, accum_volume):
        return current_price * accum_volume

    def realtime_turnover_rank(self, code, *, current_turnover):
        return (1, 1) if self.rich_leader else (0, 10)

    def is_opening_leader_phase(self, now_ts=None):
        return True

    def is_big_buyer_tick(self, code, tick):
        return False

    def get_deposit(self, force=False):
        return 10_000_000

    def build_order_risk_state(self, request):
        return RiskState(mode="paper")

    def append_trade_log(self, *args, **kwargs):
        self.trade_log_calls.append((args, kwargs))

    def estimate_net_target_return(self, entry_price, target_price):
        return target_price / entry_price - 1 if entry_price else 0.0

    def save_best(self):
        return None

    def save_portfolio_state(self):
        return None

    def register_realtime_stock(self, code):
        return None

    def clear_monitoring_stock(self, code, reason=""):
        self.monitoring_dict.pop(self.normalize_code(code), None)

    def log_final_entry_decision(self, *args, **kwargs):
        return None

    def send_order(self, *args, **kwargs):
        raise AssertionError("dry-run e2e must not call live SendOrder")

    def seed_quant_candidate(
        self,
        *,
        include_bonus: bool = True,
        include_low: bool = True,
        rich_ticks: bool = True,
        chejan_strength: float = 150.0,
    ):
        code = "000001"
        if hasattr(self, "candidate_registry"):
            self.candidate_registry.register_detection(
                code=code,
                name="테스트",
                condition_name=main.PRIMARY_CONDITION_NAME,
                detected_at=100.0,
                capture_price=10_000,
                capture_accum_volume=1 if rich_ticks else 1_000,
            )
            if include_bonus:
                self.candidate_registry.register_detection(
                    code=code,
                    name="테스트",
                    condition_name=main.BONUS_CONDITION_NAME,
                    detected_at=101.0,
                )
            self.candidate_registry.on_tick(
                code,
                price=10_800,
                chejan_strength=chejan_strength,
                accum_volume=200_001 if rich_ticks else 1_010,
                volume_delta=200_000 if rich_ticks else 10,
            )
            if include_low:
                self.candidate_registry.on_tick(
                    code,
                    price=10_400,
                    chejan_strength=chejan_strength,
                    accum_volume=400_001 if rich_ticks else 1_020,
                    volume_delta=200_000 if rich_ticks else 10,
                )
            candidate = self.candidate_registry.get(code)
            candidate_id = candidate.candidate_id if candidate is not None else ""
            condition_combo = (
                (candidate.meta or {}).get("condition_combo", "")
                if candidate is not None
                else CONDITION_COMBO_QUANT_AND_DANTE
            )
        else:
            candidate_id = ""
            condition_combo = CONDITION_COMBO_QUANT_ONLY

        self.monitoring_dict[code] = {
            "capture_price": 10_000,
            "target_price": self.quant_strategy.trigger_price(10_000),
            "capture_accum_volume": 1 if rich_ticks else 1_000,
            "breakout_volume": 1 if rich_ticks else 1_000,
            "candidate_id": candidate_id,
            "condition_name": main.PRIMARY_CONDITION_NAME,
            "condition_combo": condition_combo,
            "quant_detected": True,
            "dante_detected": condition_combo == CONDITION_COMBO_QUANT_AND_DANTE,
        }
        if rich_ticks:
            self.realtime_ticks[code] = [
                {"received_at": 1_000.0, "close": 10_000, "high": 10_000, "accum_volume": 1, "volume_delta": 1, "chejan_strength": chejan_strength},
                {"received_at": 1_060.0, "close": 10_800, "high": 10_800, "accum_volume": 200_001, "volume_delta": 200_000, "chejan_strength": chejan_strength},
                {"received_at": 1_120.0, "close": 10_400, "high": 10_400, "accum_volume": 400_001, "volume_delta": 200_000, "chejan_strength": chejan_strength},
                {"received_at": 1_180.0, "close": 10_500, "high": 10_500, "accum_volume": 500_001, "volume_delta": 100_000, "chejan_strength": chejan_strength},
            ]
        else:
            self.realtime_ticks[code] = [
                {"received_at": 1_000.0, "close": 10_000, "high": 10_000, "accum_volume": 1_000, "volume_delta": 0, "chejan_strength": chejan_strength},
                {"received_at": 1_060.0, "close": 10_800, "high": 10_800, "accum_volume": 1_010, "volume_delta": 10, "chejan_strength": chejan_strength},
                {"received_at": 1_120.0, "close": 10_400, "high": 10_400, "accum_volume": 1_020, "volume_delta": 10, "chejan_strength": chejan_strength},
                {"received_at": 1_180.0, "close": 10_500, "high": 10_500, "accum_volume": 1_030, "volume_delta": 10, "chejan_strength": chejan_strength},
            ]
        return code


class FirstPullbackEndToEndTests(unittest.TestCase):
    def test_high_since_capture_values_flow_to_ready_prediction_and_trade_log(self):
        kw = _FirstPullbackStub()
        code = kw.seed_quant_candidate()

        prediction = kw.score_safe_pullback_trade(code)

        self.assertEqual(prediction["status"], "ready")
        self.assertEqual(prediction["reason_code"], "QUANT_FIRST_PULLBACK_READY")
        self.assertEqual(prediction["condition_combo"], CONDITION_COMBO_QUANT_AND_DANTE)
        self.assertEqual(prediction["high_since_capture"], 10_800)
        self.assertEqual(prediction["low_after_high"], 10_400)
        self.assertAlmostEqual(
            prediction["pullback_from_high_pct"],
            (10_800 - 10_500) / 10_800,
        )
        self.assertAlmostEqual(prediction["rebound_from_low_pct"], 10_500 / 10_400 - 1)
        self.assertEqual(prediction["intraday_vwap"], 10_420.0)
        self.assertTrue(prediction["vwap_support_ok"])
        self.assertGreaterEqual(prediction["leader_score"], kw.quant_strategy.config.min_leader_score)
        self.assertGreater(prediction["current_price"], prediction["capture_price"])

        kw.place_buy_order(code, prediction, ratio=prediction["ratio"], stage=2)

        self.assertEqual(len(kw.trade_log_calls), 1)
        event_args, row = kw.trade_log_calls[0]
        self.assertEqual(event_args[0], "would_order")
        self.assertEqual(row["reason_code"], "QUANT_FIRST_PULLBACK_READY")
        self.assertEqual(row["high_since_capture"], 10_800)
        self.assertEqual(row["low_after_high"], 10_400)
        self.assertAlmostEqual(row["pullback_from_high_pct"], (10_800 - 10_500) / 10_800)
        self.assertAlmostEqual(row["rebound_from_low_pct"], 10_500 / 10_400 - 1)
        self.assertEqual(row["intraday_vwap"], 10_420.0)
        self.assertTrue(row["vwap_support_ok"])
        self.assertGreaterEqual(row["leader_score"], kw.quant_strategy.config.min_leader_score)

    def test_vwap_below_blocks_ready_in_main_path(self):
        kw = _FirstPullbackStub(vwap=10_600.0)
        code = kw.seed_quant_candidate()

        prediction = kw.score_safe_pullback_trade(code)

        self.assertEqual(prediction["status"], "wait")
        self.assertIn("SAFE_VWAP_SUPPORT_WAIT", prediction["reason_code"])
        self.assertFalse(prediction["vwap_support_ok"])
        self.assertEqual(prediction["high_since_capture"], 10_800)
        self.assertEqual(prediction["low_after_high"], 10_400)

    def test_weak_leader_score_blocks_ready_in_main_path(self):
        kw = _FirstPullbackStub(rich_leader=False)
        code = kw.seed_quant_candidate(rich_ticks=False)

        prediction = kw.score_safe_pullback_trade(code)

        self.assertEqual(prediction["status"], "wait")
        self.assertIn("WAIT_LEADER_SCORE", prediction["reason_code"])
        self.assertLess(prediction["leader_score"], kw.quant_strategy.config.min_leader_score)
        self.assertEqual(prediction["high_since_capture"], 10_800)
        self.assertEqual(prediction["low_after_high"], 10_400)

    def test_missing_low_after_high_from_strategy_input_waits(self):
        kw = _FirstPullbackStub(with_candidate=False, low_after_high=0)
        code = kw.seed_quant_candidate(include_low=False)

        prediction = kw.score_safe_pullback_trade(code)

        self.assertEqual(prediction["status"], "wait")
        self.assertIn("SAFE_LOW_AFTER_HIGH_MISSING", prediction["reason_code"])
        self.assertEqual(prediction["high_since_capture"], 10_800)
        self.assertEqual(prediction["low_after_high"], 0)


def _live_guard_decision(prediction, *, code="000001"):
    guard = OrderGuard(
        TradeConfig(
            dry_run=False,
            live_trading_enabled=True,
            paper_portfolio_enabled=False,
            time_policy_enabled=False,
            max_position_size=10_000_000,
            max_daily_exposure=100_000_000,
        )
    )
    current_price = int(prediction.get("current_price") or 10_500)
    request = OrderRequest(
        rqname="buy",
        screen_no="0001",
        order_type=1,
        code=code,
        quantity=1,
        price=current_price,
        order_gubun="00",
        side="buy",
        name=str(prediction.get("name", "test") or "test"),
        reason=str(prediction.get("reason", "scenario") or "scenario"),
        current_price=current_price,
        entry_price=int(prediction.get("entry_limit_price") or current_price),
        target_price=int(prediction.get("take_profit_price") or current_price + 200),
        stop_price=int(prediction.get("stop_price") or current_price - 150),
        plan_source=str(prediction.get("plan_source", "") or ""),
        context=dict(prediction),
    )
    return guard.validate(
        request,
        risk_state=RiskState(
            mode="live",
            account_state_available=True,
            daily_loss_available=True,
        ),
    )


def _paper_guard_decision(prediction, *, code="000001"):
    guard = OrderGuard(
        TradeConfig(
            dry_run=True,
            live_trading_enabled=True,
            paper_portfolio_enabled=True,
            time_policy_enabled=False,
            max_position_size=10_000_000,
            max_daily_exposure=100_000_000,
        )
    )
    current_price = int(prediction.get("current_price") or 10_500)
    request = OrderRequest(
        rqname="buy",
        screen_no="0001",
        order_type=1,
        code=code,
        quantity=1,
        price=current_price,
        order_gubun="00",
        side="buy",
        name=str(prediction.get("name", "test") or "test"),
        reason=str(prediction.get("reason", "scenario") or "scenario"),
        current_price=current_price,
        entry_price=int(prediction.get("entry_limit_price") or current_price),
        target_price=int(prediction.get("take_profit_price") or current_price + 200),
        stop_price=int(prediction.get("stop_price") or current_price - 150),
        plan_source=str(prediction.get("plan_source", "") or ""),
        context=dict(prediction),
    )
    return guard.validate(request)


def _scenario_row(name, prediction, guard_decision, expected, *, code="000001"):
    reason_code = str(prediction.get("reason_code", "") or "")
    final_reason_code = str(prediction.get("final_reason_code", "") or "")
    if final_reason_code == "FINAL_PAPER_ONLY_BREAKOUT_PROBE":
        reason_code = final_reason_code
    return {
        "case": name,
        "condition_combo": str(prediction.get("condition_combo", "") or "UNKNOWN"),
        "reason_code": reason_code,
        "final_entry_allowed": bool(prediction.get("final_entry_allowed", False)),
        "order_guard_allowed": bool(getattr(guard_decision, "allowed", False)),
        "live_order_allowed": bool(
            getattr(guard_decision, "allowed", False)
            and getattr(guard_decision, "live", False)
        ),
        "expected": expected,
        "guard_reason": str(getattr(guard_decision, "reason", "") or ""),
        "code": code,
    }


def _format_scenario_table(rows):
    headers = [
        "case",
        "condition_combo",
        "reason_code",
        "final_entry_allowed",
        "order_guard_allowed",
        "live_order_allowed",
        "expected",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row[key]) for key in headers) + " |")
    return "\n".join(lines)


class FirstPullbackScenarioTableTests(unittest.TestCase):
    maxDiff = None

    def test_first_pullback_entry_scenarios_without_kiwoom_api(self):
        rows = []

        kw = _FirstPullbackStub()
        code = kw.seed_quant_candidate(include_bonus=False)
        prediction = kw.score_safe_pullback_trade(code)
        guard_decision = _live_guard_decision(prediction, code=code)
        rows.append(
            _scenario_row(
                "1_QUANT_ONLY_PULLBACK_READY",
                prediction,
                guard_decision,
                "live allowed",
                code=code,
            )
        )
        self.assertEqual(prediction["condition_combo"], CONDITION_COMBO_QUANT_ONLY)
        self.assertEqual(prediction["reason_code"], "QUANT_FIRST_PULLBACK_READY")
        self.assertTrue(prediction["final_entry_allowed"])
        self.assertTrue(guard_decision.allowed)
        self.assertTrue(guard_decision.live)

        kw = _FirstPullbackStub()
        code = kw.seed_quant_candidate(include_bonus=True)
        prediction = kw.score_safe_pullback_trade(code)
        guard_decision = _live_guard_decision(prediction, code=code)
        rows.append(
            _scenario_row(
                "2_QUANT_AND_DANTE_BONUS",
                prediction,
                guard_decision,
                "bonus reflected/live allowed",
                code=code,
            )
        )
        self.assertEqual(prediction["condition_combo"], CONDITION_COMBO_QUANT_AND_DANTE)
        self.assertGreater(float(prediction.get("condition_score_bonus", 0.0) or 0.0), 0.0)
        self.assertTrue(prediction["final_entry_allowed"])
        self.assertTrue(guard_decision.allowed)
        self.assertTrue(guard_decision.live)

        registry = CandidateRegistry(
            primary_condition_name=main.PRIMARY_CONDITION_NAME,
            bonus_condition_name=main.BONUS_CONDITION_NAME,
        )
        dante_only = registry.register_detection(
            code="000003",
            name="테스트",
            condition_name=main.BONUS_CONDITION_NAME,
            detected_at=100.0,
            capture_price=10_000,
            meta={"candidate_role": "analysis_only"},
        )
        prediction = {
            "code": "000003",
            "name": "테스트",
            "current_price": 10_500,
            "entry_limit_price": 10_500,
            "take_profit_price": 10_710,
            "stop_price": 10_340,
            "ratio": 1.0,
            "reason_code": "BUY_PULLBACK_RECLAIM",
            "momentum_reason_code": "BUY_PULLBACK_RECLAIM",
            "entry_type": ENTRY_TYPE_PULLBACK_RECLAIM,
            "final_entry_allowed": True,
            "condition_combo": CONDITION_COMBO_DANTE_ONLY,
            "candidate_role": "analysis_only",
        }
        guard_decision = _live_guard_decision(prediction, code="000003")
        rows.append(
            _scenario_row(
                "3_DANTE_ONLY_ANALYSIS_ONLY",
                prediction,
                guard_decision,
                "analysis-only live blocked",
                code="000003",
            )
        )
        self.assertEqual(dante_only.meta["condition_combo"], CONDITION_COMBO_DANTE_ONLY)
        self.assertEqual(dante_only.meta["candidate_role"], "analysis_only")
        self.assertFalse(guard_decision.allowed)
        self.assertEqual(guard_decision.reason, LIVE_ANALYSIS_ONLY_REASON_CODE)

        kw = _FirstPullbackStub()
        kw.momentum_strategy = _MomentumBreakoutProbe()
        code = kw.seed_quant_candidate(include_bonus=True)
        prediction = kw.score_safe_pullback_trade(code)
        guard_decision = _live_guard_decision(prediction, code=code)
        paper_decision = _paper_guard_decision(prediction, code=code)
        rows.append(
            _scenario_row(
                "4_BREAKOUT_SMALL_PAPER_ONLY",
                prediction,
                guard_decision,
                "paper-only/live blocked",
                code=code,
            )
        )
        self.assertEqual(prediction["final_reason_code"], "FINAL_PAPER_ONLY_BREAKOUT_PROBE")
        self.assertTrue(prediction["final_entry_allowed"])
        self.assertFalse(guard_decision.allowed)
        self.assertEqual(guard_decision.reason, LIVE_BREAKOUT_BLOCK_REASON_CODE)
        self.assertTrue(paper_decision.allowed)
        self.assertFalse(paper_decision.live)

        kw = _FirstPullbackStub(rich_leader=False)
        code = kw.seed_quant_candidate(include_bonus=False, rich_ticks=False)
        prediction = kw.score_safe_pullback_trade(code)
        guard_decision = _live_guard_decision(prediction, code=code)
        rows.append(
            _scenario_row(
                "5_WEAK_LEADER_SCORE",
                prediction,
                guard_decision,
                "wait/no live order",
                code=code,
            )
        )
        self.assertIn("WAIT_LEADER_SCORE", prediction["reason_code"])
        self.assertFalse(prediction.get("final_entry_allowed", False))
        self.assertFalse(guard_decision.allowed)

        kw = _FirstPullbackStub(vwap=10_600.0)
        code = kw.seed_quant_candidate(include_bonus=False)
        prediction = kw.score_safe_pullback_trade(code)
        guard_decision = _live_guard_decision(prediction, code=code)
        rows.append(
            _scenario_row(
                "6_BELOW_VWAP",
                prediction,
                guard_decision,
                "wait/no live order",
                code=code,
            )
        )
        self.assertIn("SAFE_VWAP_SUPPORT_WAIT", prediction["reason_code"])
        self.assertFalse(prediction.get("final_entry_allowed", False))
        self.assertFalse(guard_decision.allowed)

        kw = _FirstPullbackStub(with_candidate=False, low_after_high=0)
        code = kw.seed_quant_candidate(include_bonus=False, include_low=False)
        prediction = kw.score_safe_pullback_trade(code)
        guard_decision = _live_guard_decision(prediction, code=code)
        rows.append(
            _scenario_row(
                "7_LOW_AFTER_HIGH_MISSING",
                prediction,
                guard_decision,
                "wait/no live order",
                code=code,
            )
        )
        self.assertIn("SAFE_LOW_AFTER_HIGH_MISSING", prediction["reason_code"])
        self.assertFalse(prediction.get("final_entry_allowed", False))
        self.assertFalse(guard_decision.allowed)

        kw = _FirstPullbackStub()
        kw.quant_strategy = QuantConditionStrategy(
            QuantStrategyConfig(leader_score_enabled=False)
        )
        code = kw.seed_quant_candidate(include_bonus=False, chejan_strength=80.0)
        prediction = kw.score_safe_pullback_trade(code)
        guard_decision = _live_guard_decision(prediction, code=code)
        rows.append(
            _scenario_row(
                "8_WEAK_CHEJAN_STRENGTH",
                prediction,
                guard_decision,
                "wait/no live order",
                code=code,
            )
        )
        self.assertIn("SAFE_CHEJAN_WAIT", prediction["reason_code"])
        self.assertFalse(prediction.get("final_entry_allowed", False))
        self.assertFalse(guard_decision.allowed)

        print("\n" + _format_scenario_table(rows))


class _SchedulerStub:
    normalize_code = main.Kiwoom.normalize_code
    parse_float = main.Kiwoom.parse_float
    _condition_eval_state = main.Kiwoom._condition_eval_state
    condition_eval_priority = main.Kiwoom.condition_eval_priority
    process_next_condition_stock = main.Kiwoom.process_next_condition_stock
    requeue_condition_stock = main.Kiwoom.requeue_condition_stock
    condition_recheck_delay_seconds = main.Kiwoom.condition_recheck_delay_seconds
    mark_condition_eval_result = main.Kiwoom.mark_condition_eval_result

    def __init__(self, *, mode="consume"):
        self.mode = mode
        self.pending_condition_codes = []
        self.condition_eval_state = {}
        self.processing_condition = False
        self.no_tick_codes = set()
        self.monitoring_dict = {}
        self.candidate_registry = CandidateRegistry(
            primary_condition_name=main.PRIMARY_CONDITION_NAME,
            bonus_condition_name=main.BONUS_CONDITION_NAME,
        )
        self.handled = []

    def reset_daily_state(self):
        return None

    def expire_candidate_registry(self):
        return None

    def handle_condition_stock(self, code):
        code = self.normalize_code(code)
        self.handled.append(code)
        if self.mode == "wait_leader":
            prediction = {
                "status": "wait",
                "reason_code": "FINAL_LEGACY_VETO_WAIT_LEADER_SCORE",
                "final_reason_code": "FINAL_LEGACY_VETO_WAIT_LEADER_SCORE",
                "leader_score": 40.0,
                "turnover_speed_per_min": 100_000_000,
            }
            self.mark_condition_eval_result(code, prediction)
            self.requeue_condition_stock(
                code,
                delay_seconds=self.condition_recheck_delay_seconds(code, prediction),
                reason_code=prediction["reason_code"],
            )


class ConditionEvaluationSchedulerTests(unittest.TestCase):
    def test_opening_batch_candidates_all_get_first_eval_within_sixty_seconds(self):
        kw = _SchedulerStub()
        kw.pending_condition_codes = [f"{idx:06d}" for idx in range(40)]
        for code in kw.pending_condition_codes:
            kw._condition_eval_state(code)["next_eval_at"] = 0.0

        start = 1_000.0
        for offset in range(60):
            with mock.patch("main.time.time", return_value=start + offset):
                kw.process_next_condition_stock()

        self.assertEqual(len(set(kw.handled)), 40)
        self.assertLessEqual(
            max(kw.condition_eval_state[code]["last_eval_at"] for code in kw.handled) - start,
            39,
        )

    def test_wait_leader_score_candidate_does_not_monopolize_queue_every_second(self):
        kw = _SchedulerStub(mode="wait_leader")
        kw.pending_condition_codes = ["000001"]
        kw._condition_eval_state("000001")["next_eval_at"] = 0.0

        start = 1_000.0
        for offset in range(600):
            with mock.patch("main.time.time", return_value=start + offset):
                kw.process_next_condition_stock()

        self.assertLessEqual(kw.condition_eval_state["000001"]["eval_count"], 41)
        self.assertGreaterEqual(kw.condition_eval_state["000001"]["next_eval_at"], start + 600)

    def test_quant_and_dante_candidate_is_prioritized_over_quant_only(self):
        kw = _SchedulerStub()
        quant = kw.candidate_registry.register_detection(
            code="000001",
            condition_name=main.PRIMARY_CONDITION_NAME,
            detected_at=100.0,
        )
        quant.update_leader_metrics(leader_score=95.0, turnover_speed_per_min=900_000_000)
        both = kw.candidate_registry.register_detection(
            code="000002",
            condition_name=main.PRIMARY_CONDITION_NAME,
            detected_at=100.0,
        )
        kw.candidate_registry.register_detection(
            code="000002",
            condition_name=main.BONUS_CONDITION_NAME,
            detected_at=101.0,
        )
        both.update_leader_metrics(leader_score=70.0, turnover_speed_per_min=300_000_000)
        kw.pending_condition_codes = ["000001", "000002"]

        with mock.patch("main.time.time", return_value=1_000.0):
            kw.process_next_condition_stock()

        self.assertEqual(kw.handled, ["000002"])


if __name__ == "__main__":
    unittest.main()
