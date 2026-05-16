"""md / csv / json 리포트 생성."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from datetime import datetime
from statistics import mean
from typing import Dict, Iterable, List, Optional

from .loader import (
    CONDITION_COMBO_DANTE_ONLY,
    CONDITION_COMBO_QUANT_AND_DANTE,
    CONDITION_COMBO_QUANT_ONLY,
    CONDITION_COMBO_UNKNOWN,
    CONDITION_META_FIELDS,
    SECTOR_THEME_FIELDS,
    Trade,
    normalize_condition_combo,
)
from .rules import RuleRecommendation


REVIEW_DIR_DEFAULT = os.path.join("data", "reviews")


# ---------------------------------------------------------------------------
# CSV: 거래 단위 상세
# ---------------------------------------------------------------------------


CSV_COLUMNS = [
    "date", "code", "name",
    "entry_class", "entry_label", "exit_class",
    # PR-D 디버그
    "late_chase_score", "late_chase_reasons",
    "breakout_chase_protected", "classifier_version",
    *CONDITION_META_FIELDS,
    "condition_meta_source", "dante_only_buy_warning",
    "grade", "entry_stage_max",
    "entry_avg_price", "exit_avg_price",
    "entry_first_time", "exit_last_time", "hold_seconds",
    "realized_return", "r_multiple",
    "mfe", "mae", "mfe_r", "mae_r",
    "return_5m", "return_10m", "return_20m",
    "give_back_r", "over_run_r", "bounce_after_stop_r",
    "be_violation",
    "reached_1r", "reached_2r", "hit_stop", "time_exit",
    # 1분봉 정밀 메트릭 (PR-B)
    "metric_source",
    "return_1m", "return_3m", "return_5m_intraday",
    "max_profit_3m", "max_drawdown_3m",
    "max_profit_5m", "max_drawdown_5m",
    "buy_price_to_1m_low_pct", "buy_price_to_3m_high_pct",
    # D 피처 (PR-B)
    "obs_elapsed_sec", "pullback_pct_from_high",
    "entry_after_peak_sec", "high_to_entry_drop_pct", "entry_near_session_high",
    "entry_vs_vwap_pct", "vwap_support_ok", "volume_ratio_1m", "volume_ratio_5m",
    "leader_score", "turnover_speed_per_min", "trade_value_since_capture",
    "turnover_rank_market", "turnover_rank_sector",
    *SECTOR_THEME_FIELDS,
    "breakout_candle_body_pct", "upper_wick_pct",
    "prior_3m_return_pct", "prior_5m_return_pct",
    # 기본 피처
    "open_return", "upper_wick_ratio",
    "px_over_bb55_pct", "chejan_strength", "volume_speed", "spread_rate",
    # 시장 컨텍스트 (review/market_context.py 가 attach)
    "market_strength",
    "market_kospi_close_return", "market_kosdaq_close_return",
    "market_kospi_intraday_high_return", "market_kosdaq_intraday_high_return",
    "reason_code", "plan_source", "reason", "exit_reason",
]


def _fmt(value):
    if value is None:
        return ""
    if isinstance(value, float):
        if value != value:  # NaN
            return ""
        return f"{value:.6f}"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


def _trade_row(trade: Trade) -> dict:
    m = trade.metrics
    f = trade.features
    row = {
        "date": trade.date,
        "code": trade.code,
        "name": trade.name,
        "entry_class": trade.entry_class,
        "entry_label": trade.entry_class,        # PR-D 별칭 — 동일 값
        "exit_class": trade.exit_class,
        # PR-D 디버그
        "late_chase_score": trade.late_chase_score,
        "late_chase_reasons": ";".join(trade.late_chase_reasons),
        "breakout_chase_protected": "true" if trade.breakout_chase_protected else "false",
        "classifier_version": trade.classifier_version,
        "condition_meta_source": trade.condition_meta_source,
        "dante_only_buy_warning": "true" if trade.dante_only_buy_warning else "false",
        "grade": trade.grade,
        "entry_stage_max": trade.entry_stage_max,
        "entry_avg_price": int(trade.entry_avg_price) if trade.entry_qty else "",
        "exit_avg_price": int(trade.exit_avg_price) if trade.exit_qty else "",
        "entry_first_time": trade.entry_first_time,
        "exit_last_time": trade.exit_last_time,
        "hold_seconds": m.get("hold_seconds"),
        "realized_return": m.get("realized_return"),
        "r_multiple": m.get("r_multiple"),
        "mfe": m.get("mfe"),
        "mae": m.get("mae"),
        "mfe_r": m.get("mfe_r"),
        "mae_r": m.get("mae_r"),
        "return_5m": m.get("return_5m"),
        "return_10m": m.get("return_10m"),
        "return_20m": m.get("return_20m"),
        "give_back_r": m.get("give_back_r"),
        "over_run_r": m.get("over_run_r"),
        "bounce_after_stop_r": m.get("bounce_after_stop_r"),
        "be_violation": m.get("be_violation"),
        "reached_1r": trade.reached_1r,
        "reached_2r": trade.reached_2r,
        "hit_stop": trade.hit_stop,
        "time_exit": trade.time_exit,
        # 1분봉 정밀 메트릭
        "metric_source": m.get("metric_source"),
        "return_1m": m.get("return_1m"),
        "return_3m": m.get("return_3m"),
        "return_5m_intraday": m.get("return_5m_intraday"),
        "max_profit_3m": m.get("max_profit_3m"),
        "max_drawdown_3m": m.get("max_drawdown_3m"),
        "max_profit_5m": m.get("max_profit_5m"),
        "max_drawdown_5m": m.get("max_drawdown_5m"),
        "buy_price_to_1m_low_pct": m.get("buy_price_to_1m_low_pct"),
        "buy_price_to_3m_high_pct": m.get("buy_price_to_3m_high_pct"),
        # D 피처
        "obs_elapsed_sec": f.get("obs_elapsed_sec"),
        "pullback_pct_from_high": f.get("pullback_pct_from_high"),
        "entry_after_peak_sec": f.get("entry_after_peak_sec"),
        "high_to_entry_drop_pct": f.get("high_to_entry_drop_pct"),
        "entry_near_session_high": f.get("entry_near_session_high"),
        "entry_vs_vwap_pct": f.get("entry_vs_vwap_pct"),
        "vwap_support_ok": f.get("vwap_support_ok"),
        "volume_ratio_1m": f.get("volume_ratio_1m"),
        "volume_ratio_5m": f.get("volume_ratio_5m"),
        "leader_score": f.get("leader_score"),
        "turnover_speed_per_min": f.get("turnover_speed_per_min"),
        "trade_value_since_capture": f.get("trade_value_since_capture"),
        "turnover_rank_market": f.get("turnover_rank_market"),
        "turnover_rank_sector": f.get("turnover_rank_sector"),
        **{field: f.get(field, "") for field in SECTOR_THEME_FIELDS},
        "breakout_candle_body_pct": f.get("breakout_candle_body_pct"),
        "upper_wick_pct": f.get("upper_wick_pct"),
        "prior_3m_return_pct": f.get("prior_3m_return_pct"),
        "prior_5m_return_pct": f.get("prior_5m_return_pct"),
        # 기존 피처
        "open_return": f.get("open_return"),
        "upper_wick_ratio": f.get("upper_wick_ratio"),
        "px_over_bb55_pct": f.get("px_over_bb55_pct"),
        "chejan_strength": f.get("chejan_strength"),
        "volume_speed": f.get("volume_speed"),
        "spread_rate": f.get("spread_rate"),
        # 시장 컨텍스트 — attach_market_context 가 trade.features 에 채움.
        # 매크로 JSON 이 없으면 strength="unknown", 나머지는 None 으로 graceful.
        "market_strength": f.get("market_strength", "unknown"),
        "market_kospi_close_return": f.get("market_kospi_close_return"),
        "market_kosdaq_close_return": f.get("market_kosdaq_close_return"),
        "market_kospi_intraday_high_return": f.get("market_kospi_intraday_high_return"),
        "market_kosdaq_intraday_high_return": f.get("market_kosdaq_intraday_high_return"),
        "reason_code": trade.reason_code,
        "plan_source": trade.plan_source,
        "reason": trade.reason,
        "exit_reason": trade.exit_reason,
    }
    for field in CONDITION_META_FIELDS:
        row[field] = getattr(trade, field, "")
    return {k: _fmt(v) for k, v in row.items()}


def write_trade_csv(trades: Iterable[Trade], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for trade in trades:
            writer.writerow(_trade_row(trade))


# ---------------------------------------------------------------------------
# JSON: 룰 오버라이드
# ---------------------------------------------------------------------------


def write_rule_overrides_json(
    recs: List[RuleRecommendation],
    path: str,
    target_date: str,
    condition_summary: Optional[Dict[str, Dict[str, object]]] = None,
    leader_summary: Optional[Dict[str, Dict[str, object]]] = None,
) -> None:
    """일자별 룰 추천 → 구조화된 Override 리스트(JSON).

    PR-A 적용기는 ``review.overrides.apply_override`` 만 사용해 처리한다.
    이 함수는 자동 적용을 직접 실행하지 않으며, low confidence 항목은 evidence
    에는 노출하되 ``proposed_overrides`` 에서는 제외해 PR-A 가 시도조차
    못하게 한다.
    """
    proposed: list = []
    evidence: list = []
    for rec in recs:
        evidence.append({
            "rule": rec.rule_id,
            "title": rec.title,
            "n": rec.n,
            "ratio": round(rec.ratio, 4),
            "confidence": rec.confidence,
            "summary": rec.summary,
        })
        if rec.confidence == "low":
            continue
        for ov in rec.overrides:
            d = ov.to_dict()
            d["source_rule"] = rec.rule_id
            d["source_confidence"] = rec.confidence
            proposed.append(d)
    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "target_date": target_date,
        "applies_to_next_trading_day": True,
        "auto_apply_globally_disabled": True,
        "schema": "review.overrides.Override v1",
        "condition_combo_summary": condition_summary or {},
        "leader_score_summary": leader_summary or {},
        "proposed_overrides": proposed,
        "evidence": evidence,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Markdown: 사람용 요약
# ---------------------------------------------------------------------------


def _fmt_pct(value, digits=2):
    if value is None or value != value:
        return "n/a"
    return f"{value * 100:+.{digits}f}%"


def _fmt_r(value, digits=2):
    if value is None or value != value:
        return "n/a"
    return f"{value:+.{digits}f}R"


def _fmt_dt(value):
    if not value:
        return ""
    return value.strftime("%H:%M:%S")


def _valid_numbers(values):
    return [value for value in values if value is not None and value == value]


def _ratio_from_attr(trades: List[Trade], attr: str) -> Optional[float]:
    values = [getattr(t, attr) for t in trades if getattr(t, attr) is not None]
    if not values:
        return None
    return sum(1 for value in values if value) / len(values)


def condition_combo_summary(trades: List[Trade]) -> Dict[str, Dict[str, object]]:
    groups: Dict[str, List[Trade]] = {
        CONDITION_COMBO_QUANT_ONLY: [],
        CONDITION_COMBO_QUANT_AND_DANTE: [],
        CONDITION_COMBO_DANTE_ONLY: [],
    }
    for trade in trades:
        combo = normalize_condition_combo(getattr(trade, "condition_combo", ""))
        groups.setdefault(combo, []).append(trade)
    if CONDITION_COMBO_UNKNOWN not in groups and any(
        normalize_condition_combo(getattr(t, "condition_combo", "")) == CONDITION_COMBO_UNKNOWN
        for t in trades
    ):
        groups[CONDITION_COMBO_UNKNOWN] = [
            t for t in trades
            if normalize_condition_combo(getattr(t, "condition_combo", "")) == CONDITION_COMBO_UNKNOWN
        ]

    out: Dict[str, Dict[str, object]] = {}
    for combo, combo_trades in groups.items():
        closed = [t for t in combo_trades if t.is_closed]
        rs = _valid_numbers([t.metrics.get("r_multiple", float("nan")) for t in closed])
        mfe_rs = _valid_numbers([t.metrics.get("mfe_r", float("nan")) for t in closed])
        mae_rs = _valid_numbers([t.metrics.get("mae_r", float("nan")) for t in closed])
        warnings = sum(1 for t in combo_trades if getattr(t, "dante_only_buy_warning", False))
        out[combo] = {
            "trades": len(combo_trades),
            "closed_trades": len(closed),
            "win_rate": (sum(1 for r in rs if r > 0) / len(rs)) if rs else None,
            "avg_r": mean(rs) if rs else None,
            "avg_mfe_r": mean(mfe_rs) if mfe_rs else None,
            "avg_mae_r": mean(mae_rs) if mae_rs else None,
            "hit_stop_rate": _ratio_from_attr(closed, "hit_stop"),
            "reached_1r_rate": _ratio_from_attr(closed, "reached_1r"),
            "dante_only_buy_warnings": warnings,
        }
    return out


def _condition_combo_lines(trades: List[Trade]) -> List[str]:
    summary = condition_combo_summary(trades)
    lines = [
        "| condition_combo | trades | win_rate | avg_r | avg_mfe_r | avg_mae_r | hit_stop_rate | reached_1r_rate | warnings |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for combo in (
        CONDITION_COMBO_QUANT_ONLY,
        CONDITION_COMBO_QUANT_AND_DANTE,
        CONDITION_COMBO_DANTE_ONLY,
        CONDITION_COMBO_UNKNOWN,
    ):
        if combo not in summary:
            continue
        stats = summary[combo]
        lines.append(
            "| {combo} | {trades} | {win} | {avg_r} | {mfe} | {mae} | {stop} | {r1} | {warn} |".format(
                combo=combo,
                trades=stats["trades"],
                win="n/a" if stats["win_rate"] is None else "{:.0%}".format(stats["win_rate"]),
                avg_r=_fmt_r(stats["avg_r"]),
                mfe=_fmt_r(stats["avg_mfe_r"]),
                mae=_fmt_r(stats["avg_mae_r"]),
                stop="n/a" if stats["hit_stop_rate"] is None else "{:.0%}".format(stats["hit_stop_rate"]),
                r1="n/a" if stats["reached_1r_rate"] is None else "{:.0%}".format(stats["reached_1r_rate"]),
                warn=stats["dante_only_buy_warnings"],
            )
        )
    warning_count = sum(
        int(stats.get("dante_only_buy_warnings") or 0) for stats in summary.values()
    )
    if warning_count:
        lines.append("")
        lines.append(f"- WARNING: DANTE_ONLY 실제 매수 의심 {warning_count}건. live 차단 경로를 점검하세요.")
    return lines


def _leader_score_bucket(value) -> str:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return "UNKNOWN"
    if score != score:
        return "UNKNOWN"
    if score >= 80.0:
        return "leader_score >= 80"
    if score >= 60.0:
        return "60 <= leader_score < 80"
    return "leader_score < 60"


def leader_score_summary(trades: List[Trade]) -> Dict[str, Dict[str, object]]:
    groups: Dict[str, List[Trade]] = {
        "leader_score >= 80": [],
        "60 <= leader_score < 80": [],
        "leader_score < 60": [],
        "UNKNOWN": [],
    }
    for trade in trades:
        groups[_leader_score_bucket(trade.features.get("leader_score"))].append(trade)
    out: Dict[str, Dict[str, object]] = {}
    for bucket, bucket_trades in groups.items():
        closed = [t for t in bucket_trades if t.is_closed]
        rs = _valid_numbers([t.metrics.get("r_multiple", float("nan")) for t in closed])
        out[bucket] = {
            "trades": len(bucket_trades),
            "closed_trades": len(closed),
            "win_rate": (sum(1 for r in rs if r > 0) / len(rs)) if rs else None,
            "avg_r": mean(rs) if rs else None,
            "hit_stop_rate": _ratio_from_attr(closed, "hit_stop"),
            "reached_1r_rate": _ratio_from_attr(closed, "reached_1r"),
        }
    return out


def _leader_score_lines(trades: List[Trade]) -> List[str]:
    summary = leader_score_summary(trades)
    lines = [
        "| leader_score_bucket | trades | win_rate | avg_r | hit_stop_rate | reached_1r_rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for bucket in ("leader_score >= 80", "60 <= leader_score < 80", "leader_score < 60", "UNKNOWN"):
        stats = summary[bucket]
        lines.append(
            "| {bucket} | {trades} | {win} | {avg_r} | {stop} | {r1} |".format(
                bucket=bucket,
                trades=stats["trades"],
                win="n/a" if stats["win_rate"] is None else "{:.0%}".format(stats["win_rate"]),
                avg_r=_fmt_r(stats["avg_r"]),
                stop="n/a" if stats["hit_stop_rate"] is None else "{:.0%}".format(stats["hit_stop_rate"]),
                r1="n/a" if stats["reached_1r_rate"] is None else "{:.0%}".format(stats["reached_1r_rate"]),
            )
        )
    return lines


def _feature_bucket(trade: Trade, field: str, default: str = "unknown") -> str:
    value = trade.features.get(field, "")
    value = str(value or "").strip()
    return value if value else default


def _max_return_25m(trade: Trade) -> Optional[float]:
    values = [
        trade.metrics.get("return_5m"),
        trade.metrics.get("return_10m"),
        trade.metrics.get("return_20m"),
        trade.metrics.get("return_5m_intraday"),
    ]
    valid = _valid_numbers(values)
    return max(valid) if valid else None


def _group_feature_performance(trades: List[Trade], field: str) -> Dict[str, Dict[str, object]]:
    groups: Dict[str, List[Trade]] = {}
    for trade in trades:
        groups.setdefault(_feature_bucket(trade, field), []).append(trade)

    out: Dict[str, Dict[str, object]] = {}
    for bucket, bucket_trades in groups.items():
        closed = [t for t in bucket_trades if t.is_closed]
        final_returns = _valid_numbers([t.final_return for t in closed])
        max_returns = _valid_numbers([_max_return_25m(t) for t in bucket_trades])
        out[bucket] = {
            "trades": len(bucket_trades),
            "ready": len(bucket_trades),
            "avg_return": mean(final_returns) if final_returns else None,
            "max_return_25m": mean(max_returns) if max_returns else None,
        }
    return out


def _feature_performance_lines(trades: List[Trade], field: str, label: str) -> List[str]:
    summary = _group_feature_performance(trades, field)
    lines = [
        f"| {label} | samples | ready | avg_return | avg_max_return_25m |",
        "|---|---:|---:|---:|---:|",
    ]
    for bucket in sorted(summary):
        stats = summary[bucket]
        lines.append(
            "| {bucket} | {samples} | {ready} | {avg_ret} | {max_ret} |".format(
                bucket=bucket,
                samples=stats["trades"],
                ready=stats["ready"],
                avg_ret="n/a" if stats["avg_return"] is None else "{:+.2%}".format(stats["avg_return"]),
                max_ret="n/a" if stats["max_return_25m"] is None else "{:+.2%}".format(stats["max_return_25m"]),
            )
        )
    return lines


def _market_sector_combo_lines(trades: List[Trade]) -> List[str]:
    groups: Dict[str, List[Trade]] = {}
    for trade in trades:
        market = _feature_bucket(trade, "market_regime")
        sector = _feature_bucket(trade, "sector_regime")
        groups.setdefault(f"{market}+{sector}", []).append(trade)

    lines = [
        "| market+sector | samples | avg_return | avg_max_return_25m |",
        "|---|---:|---:|---:|",
    ]
    for bucket in sorted(groups):
        bucket_trades = groups[bucket]
        closed = [t for t in bucket_trades if t.is_closed]
        final_returns = _valid_numbers([t.final_return for t in closed])
        max_returns = _valid_numbers([_max_return_25m(t) for t in bucket_trades])
        lines.append(
            "| {bucket} | {samples} | {avg_ret} | {max_ret} |".format(
                bucket=bucket,
                samples=len(bucket_trades),
                avg_ret="n/a" if not final_returns else "{:+.2%}".format(mean(final_returns)),
                max_ret="n/a" if not max_returns else "{:+.2%}".format(mean(max_returns)),
            )
        )
    return lines


def _unknown_ratio_lines(trades: List[Trade]) -> List[str]:
    total = len(trades)
    if total <= 0:
        return ["- no samples"]
    sector_unknown = sum(1 for t in trades if _feature_bucket(t, "sector_regime") == "unknown")
    theme_unknown = sum(1 for t in trades if _feature_bucket(t, "theme_regime") == "unknown")
    return [
        f"- sector unknown: **{sector_unknown}/{total} ({sector_unknown / total:.0%})**",
        f"- theme unknown: **{theme_unknown}/{total} ({theme_unknown / total:.0%})**",
    ]


def _sector_theme_watchlist_lines(trades: List[Trade]) -> List[str]:
    theme_strong_failed = [
        t for t in trades
        if _feature_bucket(t, "theme_regime") == "strong"
        and t.is_closed
        and (t.final_return is not None and t.final_return <= 0)
    ]
    sector_weak_success = [
        t for t in trades
        if _feature_bucket(t, "sector_regime") == "weak"
        and t.is_closed
        and (t.final_return is not None and t.final_return > 0)
    ]
    dry_run_candidates = [
        t for t in trades
        if _feature_bucket(t, "sector_gate_action", "") in ("dry_run_block_all", "dry_run_block_chase_only")
        or _feature_bucket(t, "theme_gate_action", "") in ("dry_run_block_chase_only", "dry_run_reduce_chase")
    ]

    def _items(rows: List[Trade], limit: int = 8) -> str:
        if not rows:
            return "none"
        return ", ".join(
            f"{t.name or t.code}({t.code}, {'n/a' if t.final_return is None else f'{t.final_return:+.2%}'})"
            for t in rows[:limit]
        )

    return [
        f"- theme strong failed: {_items(theme_strong_failed)}",
        f"- sector weak success: {_items(sector_weak_success)}",
        f"- dry-run gate candidates: {_items(dry_run_candidates)}",
    ]


def _profit_factor_from_r(rs: List[float]):
    wins = sum(r for r in rs if r > 0)
    losses = -sum(r for r in rs if r < 0)
    if losses <= 0:
        return None
    return wins / losses


def _summary_lines(trades: List[Trade]) -> List[str]:
    closed = [t for t in trades if t.is_closed]
    if not closed:
        return ["- 청산 완료된 거래 없음"]
    rs = [t.metrics.get("r_multiple", float("nan")) for t in closed]
    rs = _valid_numbers(rs)
    win_rate = sum(1 for r in rs if r > 0) / len(rs) if rs else 0
    avg_r = mean(rs) if rs else float("nan")
    pf_r = _profit_factor_from_r(rs)
    avg_win_r = mean([r for r in rs if r > 0]) if any(r > 0 for r in rs) else float("nan")
    avg_loss_r = mean([r for r in rs if r < 0]) if any(r < 0 for r in rs) else float("nan")
    mfe_rs = _valid_numbers([t.metrics.get("mfe_r", float("nan")) for t in closed])
    mae_rs = _valid_numbers([t.metrics.get("mae_r", float("nan")) for t in closed])
    giveback_rs = _valid_numbers([t.metrics.get("give_back_r", float("nan")) for t in closed])
    reached_1r = [t for t in closed if t.reached_1r is not None]
    reached_2r = [t for t in closed if t.reached_2r is not None]
    hit_stop = [t for t in closed if t.hit_stop is not None]

    entry_counter = Counter(t.entry_class for t in closed)
    exit_counter = Counter(t.exit_class for t in closed)
    return [
        f"- expectancy: **{avg_r:+.2f}R/trade** / win: **{win_rate:.0%}** / PF: **{'n/a' if pf_r is None else f'{pf_r:.2f}'}**",
        f"- payoff: avg_win **{_fmt_r(avg_win_r)}** / avg_loss **{_fmt_r(avg_loss_r)}**",
        f"- excursion: MFE **{_fmt_r(mean(mfe_rs) if mfe_rs else float('nan'))}** / MAE **{_fmt_r(mean(mae_rs) if mae_rs else float('nan'))}** / give-back **{_fmt_r(mean(giveback_rs) if giveback_rs else float('nan'))}**",
        f"- path: 1R **{'n/a' if not reached_1r else f'{sum(1 for t in reached_1r if t.reached_1r >= 1) / len(reached_1r):.0%}'}** / 2R **{'n/a' if not reached_2r else f'{sum(1 for t in reached_2r if t.reached_2r >= 1) / len(reached_2r):.0%}'}** / stop **{'n/a' if not hit_stop else f'{sum(1 for t in hit_stop if t.hit_stop >= 1) / len(hit_stop):.0%}'}**",
        f"- 청산 완료 거래: **{len(closed)}건**",
        f"- 평균 R: **{avg_r:+.2f}R** / 승률: **{win_rate:.0%}**",
        f"- 진입 분류: " + ", ".join(f"{k} {v}" for k, v in entry_counter.most_common()),
        f"- 청산 분류: " + ", ".join(f"{k} {v}" for k, v in exit_counter.most_common()),
    ]


def _worst_trades_table(trades: List[Trade], n: int = 3) -> List[str]:
    closed = [t for t in trades if t.is_closed and t.metrics.get("r_multiple") == t.metrics.get("r_multiple")]
    if not closed:
        return ["청산 거래 없음"]
    losers = sorted(closed, key=lambda t: t.metrics.get("r_multiple", 0))[:n]
    lines = [
        "| 종목 | 진입 | 청산 | R | MFE | MAE | give-back | 비고 |",
        "|------|------|------|---|-----|-----|-----------|------|",
    ]
    for t in losers:
        m = t.metrics
        note_parts = []
        if m.get("be_violation", 0) >= 1.0:
            note_parts.append("+1R후 손절")
        if t.entry_class == "fake_breakout":
            note_parts.append("가짜돌파")
        lines.append(
            "| {name}({code}) | {ec} | {xc} | {r} | {mfe} | {mae} | {gb} | {note} |".format(
                name=t.name or "-",
                code=t.code,
                ec=t.entry_class,
                xc=t.exit_class,
                r=_fmt_r(m.get("r_multiple")),
                mfe=_fmt_r(m.get("mfe_r")),
                mae=_fmt_r(m.get("mae_r")),
                gb=_fmt_r(m.get("give_back_r")),
                note=" / ".join(note_parts),
            )
        )
    return lines


def _all_trades_table(trades: List[Trade]) -> List[str]:
    if not trades:
        return ["거래 없음"]
    lines = [
        "| 시각 | 종목 | 진입 | 청산 | R | MFE | MAE | 사유 |",
        "|------|------|------|------|---|-----|-----|------|",
    ]
    for t in sorted(trades, key=lambda x: x.entry_first_time or datetime.min):
        m = t.metrics
        lines.append(
            "| {tm} | {name}({code}) | {ec} | {xc} | {r} | {mfe} | {mae} | {reason} |".format(
                tm=_fmt_dt(t.entry_first_time),
                name=t.name or "-",
                code=t.code,
                ec=t.entry_class,
                xc=t.exit_class,
                r=_fmt_r(m.get("r_multiple")),
                mfe=_fmt_r(m.get("mfe_r")),
                mae=_fmt_r(m.get("mae_r")),
                reason=(t.exit_reason or t.reason or "")[:30],
            )
        )
    return lines


def _rule_lines(recs: List[RuleRecommendation]) -> List[str]:
    if not recs:
        return ["- 추천 룰 없음(분류 표본 부족 또는 임계 미충족)"]
    lines = []
    for rec in recs:
        marker = "" if rec.confidence != "low" else " (low confidence)"
        lines.append(f"- **{rec.title}**{marker}: {rec.summary}")
    return lines


def _intraday_lines(intraday_summary: Optional[Dict[str, List[str]]]) -> List[str]:
    if not intraday_summary:
        return ["- 1분봉 단계 미실행"]
    n_intra = len(intraday_summary.get("with_intraday", []))
    n_fb = len(intraday_summary.get("fallback", []))
    n_miss = len(intraday_summary.get("missing", []))
    lines = [
        f"- 1분봉 정밀 메트릭: **{n_intra}건**",
        f"- 5분봉 fallback: **{n_fb}건**",
        f"- missing(1분봉/5분봉 모두 없음): **{n_miss}건**",
    ]
    if n_miss:
        codes = ", ".join(intraday_summary["missing"])
        lines.append(f"  - missing codes: `{codes}` — `python fetch_minute_bars.py {{date}}` 재시도 권장")
    return lines


def write_markdown(
    trades: List[Trade],
    recs: List[RuleRecommendation],
    path: str,
    target_date: str,
    intraday_summary: Optional[Dict[str, List[str]]] = None,
    shadow_diagnostics_section: Optional[List[str]] = None,
) -> None:
    out: List[str] = []
    out.append(f"# {target_date} 매매 복기")
    out.append("")
    out.append("## 요약")
    out.extend(_summary_lines(trades))
    out.append("")
    out.append("## 1분봉 데이터 소스")
    out.extend(_intraday_lines(intraday_summary))
    out.append("")
    out.append("## 조건식 조합별 성과")
    out.extend(_condition_combo_lines(trades))
    out.append("")
    out.append("## leader_score bucket performance")
    out.extend(_leader_score_lines(trades))
    out.append("")
    out.append("## sector regime performance")
    out.extend(_feature_performance_lines(trades, "sector_regime", "sector_regime"))
    out.append("")
    out.append("## sector gate dry-run performance")
    out.extend(_feature_performance_lines(trades, "sector_gate_action", "sector_gate_action"))
    out.append("")
    out.append("## market+sector combo performance")
    out.extend(_market_sector_combo_lines(trades))
    out.append("")
    out.append("## theme regime performance")
    out.extend(_feature_performance_lines(trades, "theme_regime", "theme_regime"))
    out.append("")
    out.append("## sector/theme unknown ratio")
    out.extend(_unknown_ratio_lines(trades))
    out.append("")
    out.append("## sector/theme dry-run review")
    out.extend(_sector_theme_watchlist_lines(trades))
    out.append("")
    out.append("## 손실 큰 거래 Top 3")
    out.extend(_worst_trades_table(trades))
    out.append("")
    out.append("## 전체 거래")
    out.extend(_all_trades_table(trades))
    out.append("")
    out.append("## 다음 거래일 룰 추천")
    out.extend(_rule_lines(recs))
    out.append("")
    if shadow_diagnostics_section:
        out.append("## 거절 표본 사후 결과 (shadow 진단)")
        out.extend(shadow_diagnostics_section)
        out.append("")
    out.append("---")
    out.append("> 자동 생성. `data/reviews/rule_overrides_*.json` 의 proposed_overrides 는")
    out.append("> PR-A(dry_run) 적용기에서만 검토되며, 본 모듈은 자동 적용하지 않습니다.")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


# ---------------------------------------------------------------------------
# 통합 진입점
# ---------------------------------------------------------------------------


def write_reports(
    trades: List[Trade],
    recs: List[RuleRecommendation],
    target_date: str,
    out_dir: str = REVIEW_DIR_DEFAULT,
    intraday_summary: Optional[Dict[str, List[str]]] = None,
    include_shadow_diagnostics: bool = True,
    shadow_csv: Optional[str] = None,
    entry_csv: Optional[str] = None,
) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, f"trade_review_{target_date}.csv")
    md_path = os.path.join(out_dir, f"daily_review_{target_date}.md")
    json_path = os.path.join(out_dir, f"rule_overrides_{target_date}.json")
    write_trade_csv(trades, csv_path)

    # shadow 진단 섹션 — 부수효과로 shadow_diagnostics_*.md 도 갱신.
    # CSV 가 없거나 어떤 이유로 실패해도 daily_review 본문 작성을 막지 않는다.
    shadow_section: Optional[List[str]] = None
    shadow_paths: Dict[str, str] = {}
    if include_shadow_diagnostics:
        try:
            from .shadow_diagnostics import build_daily_review_section
        except ImportError:
            shadow_section = None
        else:
            kwargs: Dict[str, object] = {"out_dir": out_dir}
            if shadow_csv:
                kwargs["shadow_csv"] = shadow_csv
            if entry_csv:
                kwargs["entry_csv"] = entry_csv
            try:
                shadow_section = build_daily_review_section(target_date, **kwargs)
            except FileNotFoundError as exc:
                shadow_section = [f"- shadow CSV 미발견: {exc}"]
            except Exception as exc:  # 진단 실패해도 daily_review 자체는 살림
                shadow_section = [f"- shadow 진단 실패: {exc}"]
            else:
                cum_md = os.path.join(out_dir, "shadow_diagnostics_all.md")
                day_md = os.path.join(
                    out_dir, f"shadow_diagnostics_{target_date.replace('-', '')}.md"
                )
                if os.path.exists(cum_md):
                    shadow_paths["shadow_diagnostics_all"] = cum_md
                if os.path.exists(day_md):
                    shadow_paths["shadow_diagnostics_day"] = day_md

    write_markdown(trades, recs, md_path, target_date,
                   intraday_summary=intraday_summary,
                   shadow_diagnostics_section=shadow_section)
    write_rule_overrides_json(
        recs,
        json_path,
        target_date,
        condition_summary=condition_combo_summary(trades),
        leader_summary=leader_score_summary(trades),
    )
    return {"csv": csv_path, "md": md_path, "json": json_path, **shadow_paths}
