import json
import unittest
from datetime import datetime

from bars import MinuteBar
from candidate_registry import Candidate
from momentum_breakout_strategy import (
    EntryDecision,
    MomentumBreakoutStrategy,
    MomentumContext,
)
from trade_config import TradeConfig
from time_policy import load_timezone


SEOUL = load_timezone("Asia/Seoul")


def _ts(clock: str) -> float:
    hour, minute, second = [int(part) for part in clock.split(":")]
    return datetime(2026, 5, 13, hour, minute, second, tzinfo=SEOUL).timestamp()


def _bars(reversal=True):
    if reversal:
        return [
            MinuteBar(0, 10_050, 10_080, 9_940, 9_960, 1_000, 1.0),
            MinuteBar(60, 9_950, 10_020, 9_930, 10_010, 1_500, 2.0),
        ]
    return [
        MinuteBar(0, 10_050, 10_080, 9_940, 9_960, 1_000, 1.0),
        MinuteBar(60, 9_980, 10_000, 9_900, 9_920, 1_200, 2.0),
    ]


def _candidate(**kwargs):
    payload = {
        "code": "005930",
        "name": "삼성전자",
        "detected_at": 100.0,
        "capture_price": 10_000,
        "capture_accum_volume": 10_000,
        "last_price": 9_850,
        "last_chejan_strength": 120.0,
        "tick_count": 8,
    }
    payload.update(kwargs)
    return Candidate(**payload)


def _ctx(**overrides):
    candidate = overrides.pop("candidate", _candidate())
    payload = {
        "candidate": candidate,
        "current_price": 9_850,
        "chejan_strength": 120.0,
        "spread_rate": 0.001,
        "volume_ratio": 1.5,
        "turnover_speed_per_min": 80_000_000,
        "trade_value_since_capture": 400_000_000,
        "volume_ratio_1m": 1.5,
        "volume_ratio_5m": 1.5,
        "turnover_rank_market": 1,
        "turnover_rank_sector": 0,
        "leader_score": 85.0,
        "intraday_vwap": 9_800,
        "minute_bars": _bars(),
        "prior_high": 10_080,
        "prior_low": 9_940,
        "short_ma": 9_985,
        "high_since_capture": 10_000,
        "upper_wick_ratio": 0.1,
        "signal_candle_range_pct": 0.009,
        "position_in_signal_candle_pct": 0.8,
        "recent_low_to_current_pct": 0.0,
        "tick_count": 8,
        "now_ts": 200.0,
    }
    payload.update(overrides)
    return MomentumContext(**payload)


class MomentumBreakoutStrategyTests(unittest.TestCase):
    def test_buy_after_pullback_with_reversal_and_vwap(self):
        strategy = MomentumBreakoutStrategy(TradeConfig())

        decision = strategy.evaluate(_ctx())

        self.assertEqual(decision.action, EntryDecision.BUY)
        self.assertEqual(decision.reason_code, "BUY_PULLBACK_RECLAIM")
        self.assertEqual(decision.entry_type, "PULLBACK_RECLAIM")
        self.assertEqual(decision.entry_ratio, 1.0)

    def test_time_policy_blocks_buy_even_when_momentum_setup_is_valid(self):
        strategy = MomentumBreakoutStrategy(TradeConfig())

        decision = strategy.evaluate(_ctx(now_ts=_ts("09:01:00")))

        self.assertNotEqual(decision.action, EntryDecision.BUY)
        self.assertEqual(decision.reason_code, "BLOCK_OPENING_STABILIZATION")

    def test_waits_for_first_pullback(self):
        strategy = MomentumBreakoutStrategy(TradeConfig())

        decision = strategy.evaluate(_ctx(current_price=9_950))

        self.assertEqual(decision.action, EntryDecision.WAIT_PULLBACK)

    def test_default_config_does_not_buy_breakout_probe_at_capture_or_above(self):
        strategy = MomentumBreakoutStrategy(TradeConfig())

        decision = strategy.evaluate(
            _ctx(
                current_price=10_010,
                high_since_capture=10_010,
                intraday_vwap=9_980,
                short_ma=9_990,
                recent_low_to_current_pct=0.0,
            )
        )

        self.assertNotEqual(decision.reason_code, "BUY_BREAKOUT_SMALL")
        self.assertNotEqual(decision.action, EntryDecision.BUY)
        self.assertEqual(decision.reason_code, "WAIT_PULLBACK")

    def test_blocks_chase_when_too_far_from_capture(self):
        strategy = MomentumBreakoutStrategy(TradeConfig(max_chase_distance_pct=0.03))

        decision = strategy.evaluate(_ctx(current_price=10_500, high_since_capture=10_500))

        self.assertEqual(decision.action, EntryDecision.BLOCK_CHASE)

    def test_midday_vwap_reclaim_is_paper_only_buy(self):
        strategy = MomentumBreakoutStrategy(TradeConfig(candidate_expiry_seconds=10_000_000_000))

        decision = strategy.evaluate(
            _ctx(
                now_ts=_ts("10:45:00"),
                current_price=10_200,
                intraday_vwap=10_100,
                high_since_capture=10_600,
                turnover_speed_per_min=350_000_000,
                volume_ratio=0.8,
                volume_ratio_1m=1.0,
                volume_ratio_5m=0.7,
                short_ma=10_050,
                chejan_strength=130.0,
            )
        )

        self.assertEqual(decision.action, EntryDecision.BUY)
        self.assertEqual(decision.reason_code, "MIDDAY_VWAP_RECLAIM_PAPER_ONLY")
        self.assertEqual(decision.entry_type, "MIDDAY_VWAP_RECLAIM")
        self.assertEqual(decision.metrics["orderable_live"], 0.0)

    def test_afternoon_second_wave_is_evaluated_as_paper_strategy(self):
        strategy = MomentumBreakoutStrategy(TradeConfig(candidate_expiry_seconds=10_000_000_000))

        decision = strategy.evaluate(
            _ctx(
                now_ts=_ts("13:30:00"),
                current_price=10_200,
                intraday_vwap=10_050,
                prior_high=10_500,
                high_since_capture=10_600,
                short_ma=10_100,
                turnover_speed_per_min=350_000_000,
                chejan_strength=125.0,
            )
        )

        self.assertEqual(decision.action, EntryDecision.BUY)
        self.assertEqual(decision.reason_code, "AFTERNOON_SECOND_WAVE_PAPER_ONLY")
        self.assertEqual(decision.entry_type, "AFTERNOON_SECOND_WAVE")

    def test_after_cutoff_closing_strength_is_paper_only(self):
        strategy = MomentumBreakoutStrategy(TradeConfig(candidate_expiry_seconds=10_000_000_000))

        decision = strategy.evaluate(
            _ctx(
                now_ts=_ts("14:25:00"),
                current_price=10_200,
                intraday_vwap=10_050,
                high_since_capture=10_600,
                turnover_speed_per_min=350_000_000,
                chejan_strength=170.0,
            )
        )

        self.assertEqual(decision.action, EntryDecision.BUY)
        self.assertEqual(decision.reason_code, "CLOSING_STRENGTH_PAPER_ONLY")
        self.assertEqual(decision.entry_type, "CLOSING_STRENGTH")

    def test_strong_chase_candidate_becomes_trend_continuation_paper_only(self):
        strategy = MomentumBreakoutStrategy(
            TradeConfig(
                max_chase_distance_pct=0.03,
                max_signal_candle_range_pct=0.20,
                max_recent_low_to_current_pct=0.20,
                max_extension_from_vwap_pct=0.20,
                max_extension_from_short_ma_pct=0.20,
                max_position_in_signal_candle_pct=1.0,
                candidate_expiry_seconds=10_000_000_000,
            )
        )

        decision = strategy.evaluate(
            _ctx(
                now_ts=_ts("09:40:00"),
                current_price=10_500,
                high_since_capture=10_500,
                intraday_vwap=10_200,
                short_ma=10_100,
                chejan_strength=170.0,
                upper_wick_ratio=0.10,
            )
        )

        self.assertEqual(decision.action, EntryDecision.BUY)
        self.assertEqual(decision.reason_code, "TREND_CONTINUATION_PAPER_ONLY")
        self.assertEqual(decision.entry_type, "TREND_CONTINUATION")

    def test_rejects_when_strength_or_vwap_fails(self):
        strategy = MomentumBreakoutStrategy(TradeConfig())

        weak = strategy.evaluate(_ctx(chejan_strength=80.0))
        vwap_lost = strategy.evaluate(_ctx(current_price=9_850, intraday_vwap=9_900))

        self.assertEqual(weak.action, EntryDecision.REJECT)
        self.assertEqual(vwap_lost.action, EntryDecision.REJECT)

    def test_rejects_expired_candidate(self):
        strategy = MomentumBreakoutStrategy(TradeConfig(candidate_expiry_seconds=60))

        decision = strategy.evaluate(_ctx(now_ts=200.0, candidate=_candidate(detected_at=100.0)))

        self.assertEqual(decision.action, EntryDecision.REJECT)
        self.assertEqual(decision.reason_code, "CANDIDATE_EXPIRED")

    def test_waits_when_volume_ratio_is_zero(self):
        strategy = MomentumBreakoutStrategy(TradeConfig())

        decision = strategy.evaluate(_ctx(volume_ratio=0.0))

        self.assertEqual(decision.action, EntryDecision.WAIT_DATA)
        self.assertEqual(decision.reason_code, "INVALID_VOLUME_RATIO")

    def test_waits_when_turnover_speed_missing(self):
        strategy = MomentumBreakoutStrategy(TradeConfig())

        decision = strategy.evaluate(_ctx(turnover_speed_per_min=None))

        self.assertEqual(decision.action, EntryDecision.WAIT_DATA)
        self.assertEqual(decision.reason_code, "MISSING_TURNOVER_SPEED")

    def test_waits_when_leader_score_is_too_weak(self):
        strategy = MomentumBreakoutStrategy(
            TradeConfig(opening_min_leader_score=70.0, candidate_expiry_seconds=10_000_000_000)
        )

        decision = strategy.evaluate(_ctx(leader_score=40.0, now_ts=_ts("09:10:00")))

        self.assertEqual(decision.action, EntryDecision.WAIT_PULLBACK)
        self.assertEqual(decision.reason_code, "WAIT_LEADER_SCORE")

    def test_blocks_weak_leader_after_opening_phase(self):
        strategy = MomentumBreakoutStrategy(
            TradeConfig(post_opening_min_leader_score=60.0, candidate_expiry_seconds=10_000_000_000)
        )

        decision = strategy.evaluate(_ctx(leader_score=40.0, now_ts=_ts("09:45:00")))

        self.assertEqual(decision.action, EntryDecision.BLOCK_CHASE)
        self.assertEqual(decision.reason_code, "BLOCK_WEAK_LEADER")

    def test_near_threshold_weak_leader_continues_to_vwap_gate_when_pullback_context_is_constructive(self):
        strategy = MomentumBreakoutStrategy(
            TradeConfig(post_opening_min_leader_score=60.0, candidate_expiry_seconds=10_000_000_000)
        )

        decision = strategy.evaluate(
            _ctx(
                leader_score=56.5,
                now_ts=_ts("09:45:00"),
                intraday_vwap=9_900,
                turnover_speed_per_min=350_000_000,
                chejan_strength=125.0,
                volume_ratio=0.1,
                volume_ratio_1m=0.1,
                volume_ratio_5m=0.1,
            )
        )

        self.assertEqual(decision.action, EntryDecision.REJECT)
        self.assertEqual(decision.reason_code, "BLOCK_BELOW_VWAP_WEAK_FLOW")
        self.assertEqual(decision.metrics["leader_score_context_relief"], 1.0)

    def test_near_threshold_weak_leader_does_not_turn_shallow_good_reject_into_buy(self):
        strategy = MomentumBreakoutStrategy(
            TradeConfig(post_opening_min_leader_score=60.0, candidate_expiry_seconds=10_000_000_000)
        )

        decision = strategy.evaluate(
            _ctx(
                leader_score=58.5,
                now_ts=_ts("09:45:00"),
                current_price=10_010,
                intraday_vwap=9_900,
                high_since_capture=10_080,
                chejan_strength=155.0,
                turnover_speed_per_min=40_000_000,
                upper_wick_ratio=0.29,
            )
        )

        self.assertEqual(decision.action, EntryDecision.WAIT_PULLBACK)
        self.assertEqual(decision.reason_code, "WAIT_PULLBACK")
        self.assertEqual(decision.metrics["leader_score_context_relief"], 1.0)

    def test_sub_context_minimum_weak_leader_still_blocks_after_opening_phase(self):
        strategy = MomentumBreakoutStrategy(
            TradeConfig(post_opening_min_leader_score=60.0, candidate_expiry_seconds=10_000_000_000)
        )

        decision = strategy.evaluate(
            _ctx(
                leader_score=54.9,
                now_ts=_ts("09:45:00"),
                current_price=10_010,
                intraday_vwap=9_900,
                chejan_strength=180.0,
                upper_wick_ratio=0.1,
            )
        )

        self.assertEqual(decision.action, EntryDecision.BLOCK_CHASE)
        self.assertEqual(decision.reason_code, "BLOCK_WEAK_LEADER")

    def test_missing_vwap_forbids_buy(self):
        strategy = MomentumBreakoutStrategy(TradeConfig(require_vwap_filter=True))

        decision = strategy.evaluate(_ctx(intraday_vwap=None))

        self.assertEqual(decision.action, EntryDecision.WAIT_DATA)
        self.assertEqual(decision.reason_code, "MISSING_VWAP")

    def test_missing_candle_cache_forbids_breakout_probe(self):
        strategy = MomentumBreakoutStrategy(TradeConfig())

        decision = strategy.evaluate(
            _ctx(
                current_price=10_010,
                minute_bars=(),
                prior_high=None,
                prior_low=None,
                short_ma=None,
                upper_wick_ratio=None,
                signal_candle_range_pct=None,
                position_in_signal_candle_pct=None,
                recent_low_to_current_pct=None,
            )
        )

        self.assertEqual(decision.action, EntryDecision.WAIT_DATA)
        self.assertEqual(decision.reason_code, "MISSING_CANDLE_CACHE")

    def test_missing_wick_risk_forbids_buy(self):
        strategy = MomentumBreakoutStrategy(TradeConfig())

        decision = strategy.evaluate(_ctx(upper_wick_ratio=None))

        self.assertEqual(decision.action, EntryDecision.WAIT_DATA)
        self.assertEqual(decision.reason_code, "MISSING_WICK_RISK")

    def test_prior_high_excludes_current_bar_for_chase_distance(self):
        strategy = MomentumBreakoutStrategy(
            TradeConfig(
                max_chase_distance_pct=0.03,
                max_signal_candle_range_pct=0.20,
                max_recent_low_to_current_pct=0.20,
                max_extension_from_vwap_pct=0.20,
                max_extension_from_short_ma_pct=0.20,
                max_position_in_signal_candle_pct=1.0,
            )
        )
        bars = [
            MinuteBar(0, 9_900, 10_000, 9_850, 9_950, 1_000, 1.0),
            MinuteBar(60, 10_350, 10_450, 10_300, 10_400, 2_000, 2.0),
        ]

        decision = strategy.evaluate(
            _ctx(
                current_price=10_400,
                minute_bars=bars,
                prior_high=None,
                prior_low=None,
                short_ma=10_175,
                signal_candle_range_pct=0.014,
                position_in_signal_candle_pct=0.67,
                recent_low_to_current_pct=0.056,
                intraday_vwap=10_200,
                high_since_capture=10_450,
            )
        )

        self.assertEqual(decision.metrics["prior_high"], 10_000.0)
        self.assertEqual(decision.action, EntryDecision.BLOCK_CHASE)
        self.assertEqual(decision.reason_code, "BLOCK_CHASE_DISTANCE")

    def test_signal_candle_top_is_hard_blocked(self):
        strategy = MomentumBreakoutStrategy(
            TradeConfig(
                max_chase_distance_pct=0.20,
                max_signal_candle_range_pct=0.10,
                max_recent_low_to_current_pct=0.20,
                max_extension_from_vwap_pct=0.20,
                max_extension_from_short_ma_pct=0.20,
                max_position_in_signal_candle_pct=0.90,
            )
        )
        bars = [
            MinuteBar(0, 9_900, 10_000, 9_850, 9_950, 1_000, 1.0),
            MinuteBar(60, 10_000, 10_500, 10_000, 10_480, 8_000, 2.0),
        ]

        decision = strategy.evaluate(
            _ctx(
                current_price=10_480,
                minute_bars=bars,
                prior_high=None,
                prior_low=None,
                short_ma=10_215,
                high_since_capture=10_500,
                intraday_vwap=10_250,
                upper_wick_ratio=0.04,
                signal_candle_range_pct=0.048,
                position_in_signal_candle_pct=0.96,
                recent_low_to_current_pct=0.064,
            )
        )

        self.assertEqual(decision.action, EntryDecision.BLOCK_CHASE)
        self.assertEqual(decision.reason_code, "BLOCK_SIGNAL_CANDLE_TOP")

    def test_low_volume_pullback_can_buy_as_partial_position_after_rebound(self):
        strategy = MomentumBreakoutStrategy(
            TradeConfig(min_turnover_speed_per_min=999_999_999)
        )

        decision = strategy.evaluate(
            _ctx(
                volume_ratio=0.05,
                turnover_speed_per_min=10_000_000,
                recent_low_to_current_pct=0.004,
            )
        )

        self.assertEqual(decision.action, EntryDecision.BUY)
        self.assertEqual(decision.reason_code, "BUY_PULLBACK_RECLAIM")
        self.assertEqual(decision.entry_ratio, 0.25)
        self.assertEqual(decision.position_size_multiplier, 0.25)
        self.assertEqual(decision.metrics["weak_volume_partial_relief"], 1.0)

    def test_low_volume_without_rebound_stays_rejected(self):
        strategy = MomentumBreakoutStrategy(
            TradeConfig(min_turnover_speed_per_min=999_999_999)
        )

        decision = strategy.evaluate(
            _ctx(
                volume_ratio=0.05,
                turnover_speed_per_min=10_000_000,
                recent_low_to_current_pct=0.0,
            )
        )

        self.assertEqual(decision.action, EntryDecision.REJECT)
        self.assertEqual(decision.reason_code, "WEAK_VOLUME_RATIO")

    def test_weak_volume_relief_after_0930_is_paper_only(self):
        strategy = MomentumBreakoutStrategy(
            TradeConfig(min_turnover_speed_per_min=999_999_999, candidate_expiry_seconds=10_000_000_000)
        )

        decision = strategy.evaluate(
            _ctx(
                now_ts=_ts("09:45:00"),
                volume_ratio=0.5,
                turnover_speed_per_min=350_000_000,
                recent_low_to_current_pct=0.0,
                chejan_strength=140.0,
                intraday_vwap=9_800,
            )
        )

        self.assertEqual(decision.action, EntryDecision.BUY)
        self.assertEqual(decision.reason_code, "WEAK_VOLUME_RELIEF_PAPER_ONLY")
        self.assertEqual(decision.entry_type, "WEAK_VOLUME_RELIEF_PAPER_ONLY")

    def test_first_pullback_leader_turnover_relief_allows_weak_volume_ratio(self):
        strategy = MomentumBreakoutStrategy(
            TradeConfig(
                min_turnover_speed_per_min=500_000_000,
                max_chase_distance_pct=0.03,
                max_signal_candle_range_pct=0.02,
                candidate_expiry_seconds=10_000_000_000,
            )
        )

        decision = strategy.evaluate(
            _ctx(
                current_price=10_500,
                high_since_capture=10_800,
                low_after_high=10_400,
                pullback_from_high_pct=(10_800 - 10_500) / 10_800,
                rebound_from_low_pct=10_500 / 10_400 - 1,
                volume_ratio=0.5,
                volume_ratio_1m=0.5,
                volume_ratio_5m=0.5,
                turnover_speed_per_min=300_000_000,
                leader_score=75.0,
                chejan_strength=120.0,
                intraday_vwap=10_420,
                short_ma=10_450,
                signal_candle_range_pct=0.05,
                position_in_signal_candle_pct=0.95,
                recent_low_to_current_pct=0.009,
                now_ts=_ts("09:15:00"),
            )
        )

        self.assertEqual(decision.action, EntryDecision.BUY)
        self.assertEqual(decision.reason_code, "BUY_PULLBACK_RECLAIM")
        self.assertEqual(decision.metrics["flow_score_bucket"], "first_pullback_leader_turnover_relief")
        self.assertEqual(decision.metrics["volume_gate_relaxed_by_first_pullback"], 1.0)
        self.assertEqual(decision.metrics["hard_chase_relaxed_by_first_pullback"], 1.0)

    def test_marginal_spread_can_buy_as_partial_position_when_flow_confirms(self):
        strategy = MomentumBreakoutStrategy(
            TradeConfig(min_turnover_speed_per_min=999_999_999)
        )

        decision = strategy.evaluate(
            _ctx(
                spread_rate=0.0065,
                volume_ratio=0.20,
                turnover_speed_per_min=10_000_000,
                recent_low_to_current_pct=0.004,
            )
        )

        self.assertEqual(decision.action, EntryDecision.BUY)
        self.assertEqual(decision.reason_code, "BUY_PULLBACK_RECLAIM")
        self.assertEqual(decision.entry_ratio, 0.25)
        self.assertEqual(decision.metrics["spread_gate_relaxed"], 1.0)

    def test_was_below_vwap_waits_for_reclaim_buffer_before_buying(self):
        strategy = MomentumBreakoutStrategy(TradeConfig())

        decision = strategy.evaluate(
            _ctx(
                was_below_vwap=True,
                current_price=9_850,
                intraday_vwap=9_845,
            )
        )

        self.assertEqual(decision.action, EntryDecision.WAIT_RECLAIM_VWAP)
        self.assertEqual(decision.reason_code, "WAIT_RECLAIM_VWAP")
        self.assertEqual(decision.metrics["vwap_reclaim_confirmed"], 0.0)

    def test_logs_raw_momentum_metrics_for_each_decision(self):
        strategy = MomentumBreakoutStrategy(TradeConfig())

        with self.assertLogs("momentum_breakout_strategy", level="INFO") as logs:
            decision = strategy.evaluate(_ctx())

        payload = _log_payload(logs.output[-1])
        self.assertEqual(decision.action, EntryDecision.BUY)
        self.assertEqual(payload["event"], "momentum_entry_decision")
        self.assertEqual(payload["reason_code"], "buy_pullback_reclaim")
        self.assertEqual(payload["entry_type"], "PULLBACK_RECLAIM")
        self.assertEqual(payload["prior_high_source"], "candle")
        self.assertIn("chase_risk_score", payload)
        self.assertEqual(payload["volume_ratio"], 1.5)
        self.assertEqual(payload["spread_rate"], 0.001)
        self.assertEqual(payload["vwap"], 9_800.0)

    def test_missing_metrics_log_as_null_not_zero(self):
        strategy = MomentumBreakoutStrategy(TradeConfig())

        with self.assertLogs("momentum_breakout_strategy", level="INFO") as logs:
            decision = strategy.evaluate(_ctx(volume_ratio=None))

        payload = _log_payload(logs.output[-1])
        self.assertEqual(decision.action, EntryDecision.WAIT_DATA)
        self.assertEqual(payload["reason_code"], "missing_volume_ratio")
        self.assertIsNone(payload["volume_ratio"])
        self.assertEqual(payload["blocked_by"], "missing_volume_ratio")


def _log_payload(line):
    return json.loads(line.split("] ", 1)[1])


if __name__ == "__main__":
    unittest.main()
