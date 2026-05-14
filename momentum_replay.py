from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from bars import MinuteBar
from candidate_registry import Candidate, calculate_leader_score
from momentum_breakout_strategy import (
    EntryDecision,
    MomentumBreakoutStrategy,
    MomentumContext,
)
from trade_config import TRADE_CONFIG, TradeConfig


logger = logging.getLogger(__name__)


# Replay command:
# .\venv64\Scripts\python.exe .\momentum_replay.py --events .\sample_data\momentum_condition_events.csv --bars .\sample_data\momentum_minute_bars.csv --output .\sample_data\momentum_replay_results.csv
#
# This module intentionally does not import main.py, Kiwoom, OrderGuard, or any
# order API. It only builds MomentumContext objects and writes replay decisions.


RESULT_FIELDS = [
    "code",
    "detected_at",
    "capture_price",
    "evaluated_at",
    "current_price",
    "decision",
    "entry_price",
    "stop_price",
    "take_profit_price",
    "reason",
    "reason_code",
    "chase_risk_score",
    "pullback_pct",
    "volume_ratio",
    "spread_rate",
    "upper_wick_ratio",
]


@dataclass(frozen=True)
class ConditionReplayEvent:
    code: str
    detected_at: str
    detected_ts: float
    capture_price: int
    condition_name: str = ""
    name: str = ""
    chejan_strength: float = 0.0
    volume: int = 0
    trade_value: int = 0


@dataclass(frozen=True)
class ReplayBar:
    code: str
    at: str
    at_ts: float
    open: int
    high: int
    low: int
    close: int
    volume: int
    chejan_strength: float = 0.0
    bid_price: int = 0
    ask_price: int = 0
    spread_rate: float = 0.0
    vwap: float = 0.0
    volume_ratio: float = 0.0


@dataclass(frozen=True)
class MomentumReplayResult:
    code: str
    detected_at: str
    capture_price: int
    evaluated_at: str
    current_price: int
    decision: EntryDecision
    entry_price: Optional[int]
    stop_price: Optional[int]
    take_profit_price: Optional[int]
    reason: str
    reason_code: str
    chase_risk_score: float
    pullback_pct: float = 0.0
    volume_ratio: float = 0.0
    spread_rate: float = 0.0
    upper_wick_ratio: float = 0.0

    def as_csv_row(self) -> Dict[str, object]:
        return {
            "code": self.code,
            "detected_at": self.detected_at,
            "capture_price": self.capture_price,
            "evaluated_at": self.evaluated_at,
            "current_price": self.current_price,
            "decision": self.decision.value,
            "entry_price": self.entry_price or "",
            "stop_price": self.stop_price or "",
            "take_profit_price": self.take_profit_price or "",
            "reason": self.reason,
            "reason_code": self.reason_code,
            "chase_risk_score": round(self.chase_risk_score, 4),
            "pullback_pct": round(self.pullback_pct, 6),
            "volume_ratio": round(self.volume_ratio, 6),
            "spread_rate": round(self.spread_rate, 6),
            "upper_wick_ratio": round(self.upper_wick_ratio, 6),
        }


def _parse_ts(value: object) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        pass
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y%m%d%H%M%S",
        "%H:%M:%S",
        "%H%M%S",
    ):
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if parsed.year == 1900:
            parsed = parsed.replace(year=1970, month=1, day=1)
        return parsed.timestamp()
    raise ValueError(f"unsupported timestamp: {text}")


def _int(row: Dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(float(str(row.get(key, "")).strip() or default))
    except (TypeError, ValueError):
        return default


def _float(row: Dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(str(row.get(key, "")).strip() or default)
    except (TypeError, ValueError):
        return default


def mock_condition_event(
    *,
    code: str,
    detected_at: str,
    capture_price: int,
    condition_name: str = "mock_condition",
    name: str = "",
) -> ConditionReplayEvent:
    return ConditionReplayEvent(
        code=code,
        detected_at=detected_at,
        detected_ts=_parse_ts(detected_at),
        capture_price=int(capture_price),
        condition_name=condition_name,
        name=name,
    )


def load_condition_events(path: Path | str) -> List[ConditionReplayEvent]:
    events: List[ConditionReplayEvent] = []
    with Path(path).open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            code = str(row.get("code", "")).strip()
            detected_at = str(row.get("detected_at", "")).strip()
            capture_price = _int(row, "capture_price")
            if not code or not detected_at or capture_price <= 0:
                continue
            events.append(
                ConditionReplayEvent(
                    code=code,
                    detected_at=detected_at,
                    detected_ts=_parse_ts(detected_at),
                    capture_price=capture_price,
                    condition_name=str(row.get("condition_name", "")).strip(),
                    name=str(row.get("name", "")).strip(),
                    chejan_strength=_float(row, "chejan_strength"),
                    volume=_int(row, "volume"),
                    trade_value=_int(row, "trade_value"),
                )
            )
    return events


def load_minute_bars(path: Path | str) -> Dict[str, List[ReplayBar]]:
    bars_by_code: Dict[str, List[ReplayBar]] = {}
    with Path(path).open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            code = str(row.get("code", "")).strip()
            at = str(row.get("at", "") or row.get("timestamp", "")).strip()
            if not code or not at:
                continue
            bar = ReplayBar(
                code=code,
                at=at,
                at_ts=_parse_ts(at),
                open=_int(row, "open"),
                high=_int(row, "high"),
                low=_int(row, "low"),
                close=_int(row, "close"),
                volume=_int(row, "volume"),
                chejan_strength=_float(row, "chejan_strength"),
                bid_price=_int(row, "bid_price"),
                ask_price=_int(row, "ask_price"),
                spread_rate=_float(row, "spread_rate"),
                vwap=_float(row, "vwap"),
                volume_ratio=_float(row, "volume_ratio"),
            )
            if bar.close <= 0:
                continue
            bars_by_code.setdefault(code, []).append(bar)
    for bars in bars_by_code.values():
        bars.sort(key=lambda item: item.at_ts)
    return bars_by_code


class MomentumReplayRunner:
    def __init__(
        self,
        *,
        config: TradeConfig = TRADE_CONFIG,
        strategy: Optional[MomentumBreakoutStrategy] = None,
        stop_loss_pct: Optional[float] = None,
        take_profit_pct: Optional[float] = None,
    ):
        self.config = config
        self.strategy = strategy or MomentumBreakoutStrategy(config)
        self.stop_loss_pct = (
            float(stop_loss_pct)
            if stop_loss_pct is not None
            else config.resolved_replay_stop_loss_pct
        )
        self.take_profit_pct = (
            float(take_profit_pct)
            if take_profit_pct is not None
            else config.resolved_replay_take_profit_pct
        )
        logger.info(
            "[momentum_replay_config] %s",
            json.dumps(
                {
                    "event": "momentum_replay_config",
                    "risk_reward_profile_name": config.risk_reward_profile_name,
                    "default_stop_loss_pct": config.default_stop_loss_pct,
                    "default_take_profit_pct": config.default_take_profit_pct,
                    "replay_stop_loss_pct": self.stop_loss_pct,
                    "replay_take_profit_pct": self.take_profit_pct,
                    "replay_uses_default_stop": stop_loss_pct is None
                    and config.replay_stop_loss_pct is None,
                    "replay_uses_default_take_profit": take_profit_pct is None
                    and config.replay_take_profit_pct is None,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        )

    def run(
        self,
        *,
        events: Sequence[ConditionReplayEvent],
        bars_by_code: Dict[str, Iterable[ReplayBar]],
    ) -> List[MomentumReplayResult]:
        results: List[MomentumReplayResult] = []
        for event in events:
            result = self._run_one(event, list(bars_by_code.get(event.code, [])))
            results.append(result)
        return results

    def _run_one(
        self,
        event: ConditionReplayEvent,
        bars: Sequence[ReplayBar],
    ) -> MomentumReplayResult:
        candidate = Candidate(
            code=event.code,
            name=event.name,
            condition_name=event.condition_name,
            detected_at=event.detected_ts,
            capture_price=event.capture_price,
            capture_accum_volume=event.volume,
            last_price=event.capture_price,
            last_chejan_strength=event.chejan_strength,
            meta={"replay": True},
        )
        replay_bars = [bar for bar in bars if bar.at_ts >= event.detected_ts]
        if not replay_bars:
            return self._result_from_no_data(event)

        seen: List[MinuteBar] = []
        volumes: List[int] = []
        high_since_capture = event.capture_price
        vwap_pv = 0.0
        vwap_v = 0
        last_decision = None
        last_bar = replay_bars[-1]

        for bar in replay_bars:
            high_since_capture = max(high_since_capture, bar.high, bar.close)
            volume_delta = max(0, int(bar.volume))
            vwap_pv += float(bar.close) * float(volume_delta)
            vwap_v += volume_delta
            candidate.on_tick(
                price=bar.close,
                chejan_strength=bar.chejan_strength,
                volume_delta=volume_delta,
                trade_value=volume_delta * bar.close,
            )
            seen.append(
                MinuteBar(
                    minute_start=int(bar.at_ts // 60) * 60,
                    open=bar.open or bar.close,
                    high=bar.high or bar.close,
                    low=bar.low or bar.close,
                    close=bar.close,
                    volume=volume_delta,
                    received_at=bar.at_ts,
                )
            )

            volume_ratio = bar.volume_ratio or self._volume_ratio(volume_delta, volumes)
            volumes.append(volume_delta)
            vwap = bar.vwap or (vwap_pv / vwap_v if vwap_v > 0 else 0.0)
            prior_bars = seen[:-1]
            lookback = max(int(getattr(self.config, "high_distance_lookback_bars", 5) or 5), 1)
            prior_window = prior_bars[-lookback:]
            prior_highs = [b.high for b in prior_window if b.high > 0]
            prior_lows = [b.low for b in prior_window if b.low > 0]
            prior_high = max(prior_highs) if prior_highs else None
            prior_low = min(prior_lows) if prior_lows else None
            short_ma = (
                sum(b.close for b in seen[-5:]) / min(len(seen), 5)
                if seen
                else None
            )
            if bar.high > bar.low and bar.close > 0:
                signal_candle_range_pct = (bar.high - bar.low) / bar.close
                position_in_signal_candle_pct = (bar.close - bar.low) / (bar.high - bar.low)
                upper_wick_ratio = self._upper_wick_ratio(bar)
            else:
                signal_candle_range_pct = None
                position_in_signal_candle_pct = None
                upper_wick_ratio = None
            trade_value_since_capture = int(candidate.trade_value_since_capture or 0)
            leader_score = calculate_leader_score(
                turnover_speed_per_min=(float(bar.close) * float(volume_delta)) if volume_delta > 0 else 0.0,
                volume_ratio_1m=float(volume_ratio or 0.0),
                volume_ratio_5m=float(volume_ratio or 0.0),
                trade_value_since_capture=float(trade_value_since_capture or 0.0),
                turnover_rank_market=1 if trade_value_since_capture > 0 else 0,
                ranked_count=1 if trade_value_since_capture > 0 else 0,
                condition_combo=str((candidate.meta or {}).get("condition_combo", "")),
                vwap_support_ok=not vwap or bar.close >= vwap,
                chejan_strength=bar.chejan_strength or candidate.last_chejan_strength,
                opening_phase=True,
                config=self.config,
            )
            # Legacy replay fixtures do not carry live turnover-rank snapshots.
            # Keep the replay focused on historical momentum behavior.
            leader_score = max(
                leader_score,
                float(getattr(self.config, "opening_min_leader_score", 0.0) or 0.0),
            )
            ctx = MomentumContext(
                candidate=candidate,
                current_price=bar.close,
                chejan_strength=bar.chejan_strength or candidate.last_chejan_strength,
                spread_rate=bar.spread_rate or self._spread_rate(bar) or None,
                volume_ratio=volume_ratio or None,
                turnover_speed_per_min=(float(bar.close) * float(volume_delta)) if volume_delta > 0 else None,
                trade_value_since_capture=trade_value_since_capture,
                volume_ratio_1m=volume_ratio or 0.0,
                volume_ratio_5m=volume_ratio or 0.0,
                turnover_rank_market=1 if trade_value_since_capture > 0 else 0,
                turnover_rank_sector=0,
                leader_score=leader_score,
                intraday_vwap=vwap or None,
                minute_bars=seen[-5:],
                prior_high=prior_high,
                prior_low=prior_low,
                short_ma=short_ma,
                high_since_capture=high_since_capture,
                upper_wick_ratio=upper_wick_ratio,
                signal_candle_range_pct=signal_candle_range_pct,
                position_in_signal_candle_pct=position_in_signal_candle_pct,
                recent_low_to_current_pct=(
                    bar.close / prior_low - 1
                    if prior_low and prior_low > 0 and bar.close > prior_low
                    else None
                ),
                tick_count=candidate.tick_count,
                now_ts=bar.at_ts,
            )
            last_decision = self.strategy.evaluate(ctx)
            last_bar = bar
            if last_decision.action in {
                EntryDecision.BUY,
                EntryDecision.BLOCK_CHASE,
                EntryDecision.REJECT,
            }:
                break

        if last_decision is None:
            return self._result_from_no_data(event)
        return self._result_from_decision(event, last_bar, last_decision)

    @staticmethod
    def _volume_ratio(volume: int, previous_volumes: Sequence[int]) -> float:
        positives = [v for v in previous_volumes if v > 0]
        if not positives:
            return 0.0
        avg = sum(positives[-5:]) / min(len(positives), 5)
        if avg <= 0:
            return 0.0
        return float(volume) / avg

    @staticmethod
    def _spread_rate(bar: ReplayBar) -> float:
        if bar.ask_price > 0 and bar.bid_price > 0:
            mid = (bar.ask_price + bar.bid_price) / 2.0
            if mid > 0:
                return max(0.0, (bar.ask_price - bar.bid_price) / mid)
        return 0.0

    @staticmethod
    def _upper_wick_ratio(bar: ReplayBar) -> float:
        high = bar.high or bar.close
        low = bar.low or bar.close
        if high <= low:
            return 0.0
        return max(0.0, min(1.0, (high - bar.close) / (high - low)))

    def _result_from_decision(
        self,
        event: ConditionReplayEvent,
        bar: ReplayBar,
        decision,
    ) -> MomentumReplayResult:
        entry_price = bar.close if decision.action == EntryDecision.BUY else None
        stop_price = (
            int(entry_price * (1.0 - self.stop_loss_pct)) if entry_price else None
        )
        take_profit_price = (
            int(entry_price * (1.0 + self.take_profit_pct)) if entry_price else None
        )
        metrics = decision.metrics or {}
        return MomentumReplayResult(
            code=event.code,
            detected_at=event.detected_at,
            capture_price=event.capture_price,
            evaluated_at=bar.at,
            current_price=bar.close,
            decision=decision.action,
            entry_price=entry_price,
            stop_price=stop_price,
            take_profit_price=take_profit_price,
            reason=decision.reason,
            reason_code=decision.reason_code,
            chase_risk_score=decision.chase_risk_score
            or float(metrics.get("chase_risk_score", 0.0)),
            pullback_pct=float(metrics.get("pullback_pct", 0.0)),
            volume_ratio=float(metrics.get("volume_ratio", 0.0)),
            spread_rate=float(metrics.get("spread_rate", 0.0)),
            upper_wick_ratio=float(metrics.get("upper_wick_ratio", 0.0)),
        )

    @staticmethod
    def _result_from_no_data(event: ConditionReplayEvent) -> MomentumReplayResult:
        return MomentumReplayResult(
            code=event.code,
            detected_at=event.detected_at,
            capture_price=event.capture_price,
            evaluated_at="",
            current_price=0,
            decision=EntryDecision.REJECT,
            entry_price=None,
            stop_price=None,
            take_profit_price=None,
            reason="no replay bars after condition event",
            reason_code="REJECT_NO_REPLAY_DATA",
            chase_risk_score=0.0,
        )


def write_results_csv(path: Path | str, results: Sequence[MomentumReplayResult]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        for result in results:
            writer.writerow(result.as_csv_row())


def print_results(results: Sequence[MomentumReplayResult]) -> None:
    writer = csv.DictWriter(sys.stdout, fieldnames=RESULT_FIELDS)
    writer.writeheader()
    for result in results:
        writer.writerow(result.as_csv_row())


def run_replay(
    *,
    events_path: Path | str,
    bars_path: Path | str,
    output_path: Path | str,
    config: TradeConfig = TRADE_CONFIG,
) -> List[MomentumReplayResult]:
    events = load_condition_events(events_path)
    bars_by_code = load_minute_bars(bars_path)
    runner = MomentumReplayRunner(config=config)
    results = runner.run(events=events, bars_by_code=bars_by_code)
    write_results_csv(output_path, results)
    return results


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Replay MomentumBreakoutStrategy decisions from mock condition events and minute bars."
    )
    parser.add_argument(
        "--events",
        default="sample_data/momentum_condition_events.csv",
        help="CSV with mock condition-search detections.",
    )
    parser.add_argument(
        "--bars",
        default="sample_data/momentum_minute_bars.csv",
        help="CSV with 1m/5m bars after each detection.",
    )
    parser.add_argument(
        "--output",
        default="sample_data/momentum_replay_results.csv",
        help="CSV path for replay decisions.",
    )
    args = parser.parse_args(argv)

    results = run_replay(
        events_path=args.events,
        bars_path=args.bars,
        output_path=args.output,
    )
    print_results(results)
    print(f"saved {len(results)} replay rows to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
