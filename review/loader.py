"""trade_log.csv + dante_entry_training.csv → Trade 객체 변환.

한 종목의 1차 추격 + 2차 본진입은 같은 Trade 로 묶고(분할매수 가중평균),
같은 날 청산 후 재진입은 별도 Trade 로 분리한다.

dante_entry_training 의 사후 라벨(return_5m/10m/20m, max/min_return_25m,
reached_1r/2r, hit_stop, time_exit) 은 buy_order 시각보다 ≤ 60초 전의
가장 최근 stage=1 샘플과 매칭한다. 매칭 실패시 라벨은 None.
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple


TRADE_LOG_DEFAULT = os.path.join("data", "trade_log.csv")
DANTE_TRAINING_DEFAULT = os.path.join("data", "dante_entry_training.csv")

# 같은 buy_order 와 매칭할 dante 샘플 검색 윈도우(초). buy_order 시각 - 이 윈도우.
DANTE_MATCH_WINDOW_SECONDS = 60


@dataclass
class Trade:
    date: str
    code: str
    name: str = ""
    # 진입
    entry_stage_max: int = 0
    grade: str = ""
    reason: str = ""
    score: float = 0.0
    entry_qty: int = 0
    entry_notional: int = 0           # qty*price 누적 → entry_avg_price 계산용
    entry_first_time: Optional[datetime] = None
    entry_last_time: Optional[datetime] = None
    target_price: int = 0
    # 청산
    exit_qty: int = 0
    exit_notional: int = 0
    exit_first_time: Optional[datetime] = None
    exit_last_time: Optional[datetime] = None
    exit_reason: str = ""
    realized_return: Optional[float] = None  # sell_order.profit_rate (있으면 우선)
    # 사후 라벨(dante_entry_training join)
    return_5m: Optional[float] = None
    return_10m: Optional[float] = None
    return_20m: Optional[float] = None
    max_return_25m: Optional[float] = None
    min_return_25m: Optional[float] = None
    reached_1r: Optional[int] = None
    reached_2r: Optional[int] = None
    hit_stop: Optional[int] = None
    time_exit: Optional[int] = None
    # 진입 피처 dict (chejan_strength, volume_speed, spread_rate,
    # upper_wick_ratio, open_return, ...)
    features: Dict[str, float] = field(default_factory=dict)
    # 분류/메트릭(나중에 채워짐)
    metrics: Dict[str, float] = field(default_factory=dict)
    entry_class: str = ""
    exit_class: str = ""
    notes: List[str] = field(default_factory=list)
    # === PR-D 분류 디버그 필드 ===
    late_chase_score: int = 0
    late_chase_reasons: List[str] = field(default_factory=list)
    breakout_chase_protected: bool = False
    classifier_version: str = ""

    @property
    def entry_avg_price(self) -> float:
        return self.entry_notional / self.entry_qty if self.entry_qty else 0.0

    @property
    def exit_avg_price(self) -> float:
        return self.exit_notional / self.exit_qty if self.exit_qty else 0.0

    @property
    def hold_seconds(self) -> Optional[float]:
        if self.entry_first_time and self.exit_last_time:
            return (self.exit_last_time - self.entry_first_time).total_seconds()
        return None

    @property
    def computed_return(self) -> Optional[float]:
        """trade_log 에 profit_rate 가 없을 때 fallback 으로 쓰는 체결가 기반 수익률."""
        if not self.entry_qty or not self.exit_qty:
            return None
        if self.entry_avg_price <= 0:
            return None
        return self.exit_avg_price / self.entry_avg_price - 1

    @property
    def final_return(self) -> Optional[float]:
        return self.realized_return if self.realized_return is not None else self.computed_return

    @property
    def is_closed(self) -> bool:
        return self.entry_qty > 0 and self.exit_qty > 0


def _parse_dt(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


def _parse_int(value: str, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(str(value).replace(",", "").lstrip("+")))
    except (TypeError, ValueError):
        return default


def _parse_float(value: str, default: Optional[float] = None) -> Optional[float]:
    try:
        if value in (None, ""):
            return default
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return default


def _normalize_code(code: str) -> str:
    return str(code or "").strip().lstrip("A")


# ---------------------------------------------------------------------------
# trade_log → 종목·일자별 Trade 생성
# ---------------------------------------------------------------------------


def _load_trade_log_rows(path: str, target_date: str) -> List[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"trade_log 가 없습니다: {path}")
    rows: List[dict] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            logged_at = row.get("logged_at", "")
            if not logged_at.startswith(target_date):
                continue
            rows.append(row)
    return rows


def _consume_buy_chejan(trade: Trade, row: dict) -> None:
    qty = _parse_int(row.get("executed_quantity"))
    price = _parse_int(row.get("executed_price"))
    if qty <= 0 or price <= 0:
        return
    if any(t == qty and p == price for t, p in trade._buy_dedup):
        return
    trade._buy_dedup.append((qty, price))
    trade.entry_qty += qty
    trade.entry_notional += qty * price
    ts = _parse_dt(row.get("logged_at", ""))
    if ts:
        if trade.entry_first_time is None or ts < trade.entry_first_time:
            trade.entry_first_time = ts
        if trade.entry_last_time is None or ts > trade.entry_last_time:
            trade.entry_last_time = ts


def _consume_sell_chejan(trade: Trade, row: dict) -> None:
    qty = _parse_int(row.get("executed_quantity"))
    price = _parse_int(row.get("executed_price"))
    if qty <= 0 or price <= 0:
        return
    if any(t == qty and p == price for t, p in trade._sell_dedup):
        return
    trade._sell_dedup.append((qty, price))
    trade.exit_qty += qty
    trade.exit_notional += qty * price
    ts = _parse_dt(row.get("logged_at", ""))
    if ts:
        if trade.exit_first_time is None or ts < trade.exit_first_time:
            trade.exit_first_time = ts
        if trade.exit_last_time is None or ts > trade.exit_last_time:
            trade.exit_last_time = ts


def _build_trades(rows: List[dict], target_date: str) -> List[Trade]:
    """trade_log rows → 종목별 Trade 리스트.

    같은 (date, code) 는 한 Trade. 같은 날 청산 후 재진입(=exit 가 끝난 뒤 새 buy_order)
    이 발생하면 새 Trade 로 분리한다.
    """
    grouped: Dict[str, List[dict]] = defaultdict(list)
    for row in rows:
        code = _normalize_code(row.get("code"))
        if not code:
            continue
        grouped[code].append(row)

    trades: List[Trade] = []
    for code, code_rows in grouped.items():
        code_rows.sort(key=lambda r: r.get("logged_at", ""))
        current: Optional[Trade] = None
        for row in code_rows:
            event = row.get("event", "")
            side = row.get("side", "")
            order_status = row.get("order_status", "")

            if event == "buy_order":
                if current is None or (current.exit_qty > 0 and current.exit_qty >= current.entry_qty):
                    if current is not None:
                        trades.append(current)
                    current = Trade(date=target_date, code=code, name=row.get("name", "") or "")
                    current._buy_dedup = []   # type: ignore[attr-defined]
                    current._sell_dedup = []  # type: ignore[attr-defined]
                if not current.name and row.get("name"):
                    current.name = row.get("name", "")
                if not current.reason and row.get("reason"):
                    current.reason = row.get("reason", "")
                if not current.target_price:
                    current.target_price = _parse_int(row.get("target_price"))
                score = _parse_float(row.get("score"))
                if score is not None and not current.score:
                    current.score = score
                continue

            if event == "chejan" and order_status == "체결":
                if current is None:
                    current = Trade(date=target_date, code=code, name=row.get("name", "") or "")
                    current._buy_dedup = []   # type: ignore[attr-defined]
                    current._sell_dedup = []  # type: ignore[attr-defined]
                if side == "buy":
                    _consume_buy_chejan(current, row)
                elif side == "sell":
                    _consume_sell_chejan(current, row)
                continue

            if event == "sell_order":
                if current is None:
                    continue
                if not current.exit_reason and row.get("reason"):
                    current.exit_reason = row.get("reason", "")
                pr = _parse_float(row.get("profit_rate"))
                if pr is not None:
                    current.realized_return = pr

        if current is not None:
            trades.append(current)
    return trades


# ---------------------------------------------------------------------------
# dante_entry_training join
# ---------------------------------------------------------------------------


def _load_dante_samples(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    out: List[dict] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            captured_at = _parse_float(row.get("captured_at"))
            if captured_at is None:
                continue
            row["_captured_at"] = captured_at
            row["_code"] = _normalize_code(row.get("code"))
            out.append(row)
    out.sort(key=lambda r: r["_captured_at"])
    return out


def _attach_dante_label(trade: Trade, samples: List[dict]) -> None:
    if trade.entry_first_time is None:
        return
    target_ts = trade.entry_first_time.timestamp()
    candidates = [
        s for s in samples
        if s["_code"] == trade.code
        and s["_captured_at"] <= target_ts + DANTE_MATCH_WINDOW_SECONDS
        and s["_captured_at"] >= target_ts - 5 * 60   # 5분 이상 옛날 샘플은 무시
    ]
    if not candidates:
        return
    sample = max(candidates, key=lambda s: s["_captured_at"])

    stage = _parse_int(sample.get("entry_stage"))
    grade_a = _parse_float(sample.get("breakout_grade_a"), default=0.0) or 0.0
    grade_b = _parse_float(sample.get("breakout_grade_b"), default=0.0) or 0.0
    if not trade.grade:
        trade.grade = "A" if grade_a >= 0.5 else ("B" if grade_b >= 0.5 else "")
    if stage > trade.entry_stage_max:
        trade.entry_stage_max = stage

    trade.return_5m = _parse_float(sample.get("return_5m"))
    trade.return_10m = _parse_float(sample.get("return_10m"))
    trade.return_20m = _parse_float(sample.get("return_20m"))
    trade.max_return_25m = _parse_float(sample.get("max_return_25m"))
    trade.min_return_25m = _parse_float(sample.get("min_return_25m"))
    trade.reached_1r = _parse_int(sample.get("reached_1r"), default=0)
    trade.reached_2r = _parse_int(sample.get("reached_2r"), default=0)
    trade.hit_stop = _parse_int(sample.get("hit_stop"), default=0)
    trade.time_exit = _parse_int(sample.get("time_exit"), default=0)

    feature_keys = (
        "chejan_strength",
        "volume_speed",
        "spread_rate",
        "obs_elapsed_sec",
        "px_over_env13_pct",
        "px_over_bb55_pct",
        "five_min_closes_count",
        "pullback_pct_from_high",
        "neg_bars_streak",
        "cur_bar_is_positive",
        "chejan_strength_trend",
        "upper_wick_ratio",
        "open_return",
    )
    for key in feature_keys:
        v = _parse_float(sample.get(key))
        if v is not None:
            trade.features[key] = v


# ---------------------------------------------------------------------------
# 외부 진입점
# ---------------------------------------------------------------------------


def load_trades(
    target_date: str,
    trade_log_path: str = TRADE_LOG_DEFAULT,
    dante_path: str = DANTE_TRAINING_DEFAULT,
) -> List[Trade]:
    """target_date('YYYY-MM-DD') 의 모든 Trade 를 만들어 반환."""
    rows = _load_trade_log_rows(trade_log_path, target_date)
    trades = _build_trades(rows, target_date)
    samples = _load_dante_samples(dante_path)
    for trade in trades:
        _attach_dante_label(trade, samples)
    return trades


def latest_trade_date(trade_log_path: str = TRADE_LOG_DEFAULT) -> Optional[str]:
    """trade_log.csv 마지막 날짜를 'YYYY-MM-DD' 로 반환."""
    if not os.path.exists(trade_log_path):
        return None
    last_date: Optional[str] = None
    with open(trade_log_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            logged_at = row.get("logged_at", "")
            if len(logged_at) >= 10:
                date_part = logged_at[:10]
                if last_date is None or date_part > last_date:
                    last_date = date_part
    return last_date
