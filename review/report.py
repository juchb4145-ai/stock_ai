"""md / csv / json 리포트 생성."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from datetime import datetime
from statistics import mean
from typing import Dict, Iterable, List, Optional

from .loader import Trade
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
    "entry_vs_vwap_pct", "volume_ratio_1m",
    "breakout_candle_body_pct", "upper_wick_pct",
    "prior_3m_return_pct", "prior_5m_return_pct",
    # 기본 피처
    "open_return", "upper_wick_ratio",
    "px_over_bb55_pct", "chejan_strength", "volume_speed", "spread_rate",
    "reason", "exit_reason",
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
        "volume_ratio_1m": f.get("volume_ratio_1m"),
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
        "reason": trade.reason,
        "exit_reason": trade.exit_reason,
    }
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


def _summary_lines(trades: List[Trade]) -> List[str]:
    closed = [t for t in trades if t.is_closed]
    if not closed:
        return ["- 청산 완료된 거래 없음"]
    rs = [t.metrics.get("r_multiple", float("nan")) for t in closed]
    rs = [r for r in rs if r == r]
    win_rate = sum(1 for r in rs if r > 0) / len(rs) if rs else 0
    avg_r = mean(rs) if rs else float("nan")

    entry_counter = Counter(t.entry_class for t in closed)
    exit_counter = Counter(t.exit_class for t in closed)
    return [
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
    out.append("## 손실 큰 거래 Top 3")
    out.extend(_worst_trades_table(trades))
    out.append("")
    out.append("## 전체 거래")
    out.extend(_all_trades_table(trades))
    out.append("")
    out.append("## 다음 거래일 룰 추천")
    out.extend(_rule_lines(recs))
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
) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, f"trade_review_{target_date}.csv")
    md_path = os.path.join(out_dir, f"daily_review_{target_date}.md")
    json_path = os.path.join(out_dir, f"rule_overrides_{target_date}.json")
    write_trade_csv(trades, csv_path)
    write_markdown(trades, recs, md_path, target_date,
                   intraday_summary=intraday_summary)
    write_rule_overrides_json(recs, json_path, target_date)
    return {"csv": csv_path, "md": md_path, "json": json_path}
