"""최근 N영업일 trade_review_*.csv 누적 통계 + rule_candidates 산출.

본 모듈은 main.py 에 일절 연결되지 않는 독립 분석 모듈이다. 산출물은
오직 ``data/reviews/`` 아래 두 JSON 파일이며, 자동 적용은 PR-A(dry_run)
에서 별도 모듈이 담당한다.

CLI:
    python -m review.rolling                                 # 오늘 기준
    python -m review.rolling 2026-04-30                       # 기준일 지정
    python -m review.rolling 2026-04-30 --windows 5,10,20     # 윈도우 변경
    python -m review.rolling --reviews-dir tests/fixtures/reviews

데이터 소스:
    {reviews_dir}/trade_review_YYYY-MM-DD.csv     # 거래 단위 진실 소스
    {reviews_dir}/rule_overrides_YYYY-MM-DD.json  # 그날 발동된 룰 evidence(보조)

출력:
    {reviews_dir}/rolling_summary_YYYYMMDD.json
    {reviews_dir}/rule_candidates_YYYYMMDD.json
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean
from typing import Dict, Iterable, List, Optional, Tuple

from .overrides import Override


REVIEWS_DIR_DEFAULT = os.path.join("data", "reviews")
DEFAULT_WINDOWS = (5, 10, 20)

# === confidence 임계 (사용자 명세) ===
CONFIDENCE_LOW_MAX = 20      # n < 20 → low
CONFIDENCE_MEDIUM_MAX = 40   # 20 ≤ n < 40 → medium
# n ≥ 40 + 동일 손실 패턴 반복(=윈도우 일관성) → high

# === 분류기 버전 정책 ===
# trade_review_*.csv 의 classifier_version 컬럼 기준.
# - "v2"     : 현재 분류기(권장). 룰 후보 평가의 신호원.
# - "v1"     : 1분봉 D 피처 부재로 fallback 된 거래. 분류 임계가 다르므로 후보 평가에서
#              제외하고 audit 가독성을 위해 by_classifier_version 통계로만 노출.
# - 빈 값/기타: 과거 fixture 호환을 위해 "v2" default 로 취급(현재 운영 trade_review 는
#              항상 v2 를 적는다 — review.classifier 의 _classify_entry 가 강제).
DEFAULT_CLASSIFIER_VERSION = "v2"
CANDIDATE_CLASSIFIER_VERSIONS = ("v2",)

CONDITION_COMBO_UNKNOWN = "UNKNOWN"
CONDITION_COMBO_QUANT_ONLY = "QUANT_ONLY"
CONDITION_COMBO_QUANT_AND_DANTE = "QUANT_AND_DANTE"
CONDITION_COMBO_DANTE_ONLY = "DANTE_ONLY"
CONDITION_COMBO_VALUES = {
    CONDITION_COMBO_QUANT_ONLY,
    CONDITION_COMBO_QUANT_AND_DANTE,
    CONDITION_COMBO_DANTE_ONLY,
}
CONDITION_COMBO_MIN_N = 2
CONDITION_COMBO_AVG_R_DIFF = 0.25
CONDITION_COMBO_WIN_RATE_DIFF = 0.10
DANTE_ONLY_SHADOW_STOP_RATE = 0.50
DANTE_ONLY_SHADOW_REACHED_1R_MAX = 0.25

# === rule candidate 트리거 임계 (review/rules.py 와 동일하게 유지) ===
FAKE_BREAKOUT_RATIO_BLOCK = 0.30
A_VS_B_DIFF_R = 0.5
LATE_TAKE_RATIO = 0.25
FAST_TAKE_RATIO = 0.25
BE_VIOLATION_RATIO = 0.30

# === 룰별 권장 오버라이드 ===
# eval/exec 사용 금지. 모든 항목은 review/overrides.py 의 Override 스키마와
# 1:1 일치하는 dict 로 구성한다. PR-A 적용기는 review.overrides.apply_override
# 만 사용해 setattr 한다.
PROPOSED_OVERRIDES: Dict[str, List[dict]] = {
    "block_fake_breakout": [
        {
            "target": "entry_strategy.MAX_UPPER_WICK_RATIO",
            "op": "decrement", "by": 0.10, "min": 0.20,
            "reason": "최근 누적 윈도우에서 가짜돌파 비율 ≥30% 반복",
        },
        {
            "target": "entry_strategy.OVERHEATED_OPEN_RETURN",
            "op": "decrement", "by": 0.02, "min": 0.05,
            "reason": "가짜돌파 표본의 평균 시가대비 등락률 과열",
        },
    ],
    "wait_for_pullback": [
        {
            "target": "entry_strategy.DANTE_FIRST_ENTRY_RATIO",
            "op": "set", "value": 0.0,
            "reason": "A급 1차 추격 평균 R<0, B급/본진입 평균 R>0 — 추격 비활성",
        },
    ],
    "take_profit_faster": [
        {
            "target": "exit_strategy.EXIT_PARTIAL_R",
            "op": "decrement", "by": 0.5, "min": 1.0,
            "reason": "익절 거래의 give-back 평균 ≥1R 반복 — 부분익절 R 단축",
        },
    ],
    "apply_trailing": [
        {
            "target": "exit_strategy.EXIT_PARTIAL_RATIO",
            "op": "decrement", "by": 0.2, "min": 0.2,
            "reason": "fast_take 비율 높음 — 부분익절 비율 축소 후 잔량 트레일",
        },
        {
            "target": "exit_strategy.TRAIL_HIGHEST_GIVEBACK_R",
            "op": "set", "value": 0.7,
            "reason": "잔량 trailing 활성화(고점 대비 0.7R 반납 시 청산)",
        },
    ],
    "break_even_cut": [
        {
            "target": "exit_strategy.EXIT_BE_R",
            "op": "decrement", "by": 0.3, "min": 0.5,
            "reason": "+1R 도달 후 손절 비율 ≥30% 반복 — BE 스탑 조기 이동",
        },
    ],
}

RULE_TITLES = {
    "block_fake_breakout": "① 진입 금지(가짜돌파 게이트 강화)",
    "wait_for_pullback":   "② 더 기다리기(A급 1차 추격 비활성)",
    "take_profit_faster":  "③ 빨리 익절(부분익절 R 단축)",
    "apply_trailing":      "④ 트레일링 적용(잔량 추세 따라가기)",
    "break_even_cut":      "⑤ 본절컷(BE 스탑 조기 이동)",
}


# ---------------------------------------------------------------------------
# 파일 발견 / 로드
# ---------------------------------------------------------------------------


_TRADE_REVIEW_RE = re.compile(r"trade_review_(\d{4}-\d{2}-\d{2})\.csv$")


def discover_review_dates(reviews_dir: str) -> List[str]:
    """reviews_dir 에서 trade_review_*.csv 의 날짜를 오름차순으로 모은다."""
    if not os.path.isdir(reviews_dir):
        return []
    out: List[str] = []
    for path in glob.glob(os.path.join(reviews_dir, "trade_review_*.csv")):
        m = _TRADE_REVIEW_RE.search(os.path.basename(path))
        if m:
            out.append(m.group(1))
    return sorted(set(out))


def select_window_dates(
    available: List[str],
    as_of_date: str,
    window: int,
) -> List[str]:
    """as_of_date(포함) 이전 가장 최근 window 개 영업일을 반환."""
    eligible = [d for d in available if d <= as_of_date]
    if not eligible:
        return []
    return eligible[-window:]


def _parse_float(value, default: Optional[float] = None) -> Optional[float]:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_int(value, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _parse_boolish(value) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in ("1", "true", "t", "yes", "y"):
        return True
    if text in ("0", "false", "f", "no", "n"):
        return False
    return None


def _condition_combo(row: Dict[str, object]) -> str:
    combo = str(row.get("condition_combo") or "").strip().upper()
    if combo in CONDITION_COMBO_VALUES:
        return combo
    quant = _parse_boolish(row.get("quant_detected"))
    dante = _parse_boolish(row.get("dante_detected"))
    if quant and dante:
        return CONDITION_COMBO_QUANT_AND_DANTE
    if quant:
        return CONDITION_COMBO_QUANT_ONLY
    if dante:
        return CONDITION_COMBO_DANTE_ONLY
    return CONDITION_COMBO_UNKNOWN


_NUMERIC_FIELDS = {
    "realized_return", "r_multiple",
    "mfe", "mae", "mfe_r", "mae_r",
    "return_5m", "return_10m", "return_20m",
    "give_back_r", "over_run_r", "bounce_after_stop_r",
    "be_violation",
    "open_return", "upper_wick_ratio", "px_over_bb55_pct",
    "chejan_strength", "volume_speed", "spread_rate",
    "hold_seconds",
    "condition_score_bonus", "time_between_conditions_sec",
    "leader_score", "turnover_speed_per_min", "volume_ratio_1m", "volume_ratio_5m",
    "trade_value_since_capture", "turnover_rank_market", "turnover_rank_sector",
}

_INT_FIELDS = {"reached_1r", "reached_2r", "hit_stop", "time_exit", "entry_stage_max"}


def load_trade_rows(reviews_dir: str, dates: Iterable[str]) -> List[Dict[str, object]]:
    """주어진 날짜 리스트의 trade_review_*.csv 를 모두 합쳐 row dict 리스트 반환."""
    rows: List[Dict[str, object]] = []
    for date in dates:
        path = os.path.join(reviews_dir, f"trade_review_{date}.csv")
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8-sig") as f:
            for raw in csv.DictReader(f):
                row: Dict[str, object] = {}
                for k, v in raw.items():
                    if k in _NUMERIC_FIELDS:
                        row[k] = _parse_float(v)
                    elif k in _INT_FIELDS:
                        row[k] = _parse_int(v)
                    else:
                        row[k] = v
                row["condition_combo"] = _condition_combo(row)
                rows.append(row)
    return rows


def load_shadow_condition_rows(path: Optional[str], dates: Iterable[str]) -> List[Dict[str, object]]:
    if not path or not os.path.exists(path):
        return []
    date_set = set(dates)
    rows: List[Dict[str, object]] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for raw in csv.DictReader(f):
            captured = str(raw.get("captured_time") or raw.get("logged_at") or "")
            date_part = captured[:10]
            if date_set and date_part not in date_set:
                continue
            row: Dict[str, object] = {}
            for k, v in raw.items():
                if k in _NUMERIC_FIELDS:
                    row[k] = _parse_float(v)
                elif k in _INT_FIELDS:
                    row[k] = _parse_int(v)
                else:
                    row[k] = v
            row["condition_combo"] = _condition_combo(row)
            rows.append(row)
    return rows


def load_overrides_evidence(reviews_dir: str, dates: Iterable[str]) -> List[dict]:
    """rule_overrides_*.json 의 evidence 만 모은다(보조 메타)."""
    out: List[dict] = []
    for date in dates:
        path = os.path.join(reviews_dir, f"rule_overrides_{date}.json")
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        for item in payload.get("evidence") or []:
            entry = dict(item)
            entry["date"] = date
            out.append(entry)
    return out


# ---------------------------------------------------------------------------
# 통계 집계
# ---------------------------------------------------------------------------


def _safe_mean(xs):
    xs = [x for x in xs if x is not None and x == x]
    if not xs:
        return None
    return mean(xs)


def _profit_factor(returns: List[float]) -> Optional[float]:
    """승의 합 / 패의 합 절대값. 패가 0이면 None."""
    wins = sum(r for r in returns if r is not None and r > 0)
    losses = -sum(r for r in returns if r is not None and r < 0)
    if losses <= 0:
        return None
    return wins / losses


def _payoff_ratio(rs: List[float]) -> Optional[float]:
    wins = [r for r in rs if r is not None and r == r and r > 0]
    losses = [-r for r in rs if r is not None and r == r and r < 0]
    if not wins or not losses:
        return None
    avg_loss = mean(losses)
    if avg_loss <= 0:
        return None
    return mean(wins) / avg_loss


def _ratio(rows: List[Dict[str, object]], field: str) -> Optional[float]:
    values = [r.get(field) for r in rows if r.get(field) is not None]
    if not values:
        return None
    return sum(1 for value in values if value) / len(values)


def _aggregate_group(rows: List[Dict[str, object]]) -> Dict[str, object]:
    if not rows:
        return {"n": 0, "win_rate": None, "avg_r": None,
                "avg_mfe_r": None, "avg_mae_r": None,
                "avg_give_back_r": None, "avg_realized": None,
                "profit_factor": None, "payoff_ratio": None,
                "reached_1r_rate": None, "reached_2r_rate": None,
                "hit_stop_rate": None, "expectancy_ok": False}
    rs = [r.get("r_multiple") for r in rows]
    realized = [r.get("realized_return") for r in rows]
    mfe = [r.get("mfe_r") for r in rows]
    mae = [r.get("mae_r") for r in rows]
    give_back = [r.get("give_back_r") for r in rows]
    valid_realized = [r for r in realized if r is not None and r == r]
    wins = sum(1 for r in valid_realized if r > 0)
    win_rate = wins / len(valid_realized) if valid_realized else None
    avg_r = _safe_mean(rs)
    return {
        "n": len(rows),
        "win_rate": win_rate,
        "avg_r": avg_r,
        "avg_realized": _safe_mean(valid_realized),
        "avg_mfe_r": _safe_mean(mfe),
        "avg_mae_r": _safe_mean(mae),
        "avg_give_back_r": _safe_mean(give_back),
        "profit_factor": _profit_factor(valid_realized),
        "payoff_ratio": _payoff_ratio(rs),
        "reached_1r_rate": _ratio(rows, "reached_1r"),
        "reached_2r_rate": _ratio(rows, "reached_2r"),
        "hit_stop_rate": _ratio(rows, "hit_stop"),
        "expectancy_ok": bool(avg_r is not None and avg_r > 0),
    }


def _confidence_for_n(n: int) -> str:
    if n < CONFIDENCE_LOW_MAX:
        return "low"
    if n < CONFIDENCE_MEDIUM_MAX:
        return "medium"
    return "high"


def _row_classifier_version(row: Dict[str, object]) -> str:
    """row 의 분류기 버전을 추출. 빈 값은 최신(v2) default."""
    cv = str(row.get("classifier_version") or "").strip()
    return cv if cv else DEFAULT_CLASSIFIER_VERSION


def _filter_candidate_rows(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """룰 후보 평가에 들어갈 row 만 골라낸다.

    현재 정책: ``CANDIDATE_CLASSIFIER_VERSIONS = ("v2",)`` 만 통과. v1 fallback /
    빈 값(legacy) / 기타 분류기는 제외해 후보 평가가 v2 표본으로만 결정되게 한다.
    by_classifier_version 통계는 별도로 v1 도 노출(audit 가독성).
    """
    return [r for r in rows if _row_classifier_version(r) in CANDIDATE_CLASSIFIER_VERSIONS]


def _leader_score_bucket(row: Dict[str, object]) -> str:
    score = row.get("leader_score")
    if score is None or score != score:
        return "UNKNOWN"
    try:
        score_f = float(score)
    except (TypeError, ValueError):
        return "UNKNOWN"
    if score_f >= 80.0:
        return "leader_score >= 80"
    if score_f >= 60.0:
        return "60 <= leader_score < 80"
    return "leader_score < 60"


@dataclass
class WindowStats:
    """단일 윈도우(예: 10영업일)의 누적 통계.

    confidence 는 *후보 평가에 실제로 쓰이는 표본 수* 기준이라 v2 only count 를 본다.
    n_total 은 전체 row 수(분류기 버전 무관) 라 v1/v2 비율 모니터링용으로 따로 둔다.
    """
    window: int
    dates: List[str]
    n_total: int
    n_candidate: int                       # v2(=후보 평가 대상) row 수
    overall: Dict[str, object]
    by_entry: Dict[str, Dict[str, object]] = field(default_factory=dict)
    by_exit: Dict[str, Dict[str, object]] = field(default_factory=dict)
    by_combo: Dict[str, Dict[str, object]] = field(default_factory=dict)
    by_condition_combo: Dict[str, Dict[str, object]] = field(default_factory=dict)
    by_condition_combo_entry_class: Dict[str, Dict[str, object]] = field(default_factory=dict)
    by_condition_combo_exit_class: Dict[str, Dict[str, object]] = field(default_factory=dict)
    by_leader_score_bucket: Dict[str, Dict[str, object]] = field(default_factory=dict)
    by_classifier: Dict[str, Dict[str, object]] = field(default_factory=dict)
    confidence: str = "low"

    def to_dict(self) -> dict:
        return {
            "window": self.window,
            "dates": self.dates,
            "n_total": self.n_total,
            "n_candidate": self.n_candidate,
            "confidence": self.confidence,
            "overall": self.overall,
            "by_entry_class": self.by_entry,
            "by_exit_class": self.by_exit,
            "by_entry_exit": self.by_combo,
            "by_condition_combo": self.by_condition_combo,
            "by_condition_combo_entry_class": self.by_condition_combo_entry_class,
            "by_condition_combo_exit_class": self.by_condition_combo_exit_class,
            "by_leader_score_bucket": self.by_leader_score_bucket,
            "by_classifier_version": self.by_classifier,
        }


def aggregate_window(
    window: int,
    dates: List[str],
    rows: List[Dict[str, object]],
) -> WindowStats:
    overall = _aggregate_group(rows)
    by_entry: Dict[str, Dict[str, object]] = {}
    by_exit: Dict[str, Dict[str, object]] = {}
    by_combo: Dict[str, Dict[str, object]] = {}
    by_condition_combo: Dict[str, Dict[str, object]] = {}
    by_condition_combo_entry_class: Dict[str, Dict[str, object]] = {}
    by_condition_combo_exit_class: Dict[str, Dict[str, object]] = {}
    by_leader_score_bucket: Dict[str, Dict[str, object]] = {}
    by_classifier: Dict[str, Dict[str, object]] = {}

    grouped_e: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    grouped_x: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    grouped_c: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    grouped_condition: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    grouped_condition_entry: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    grouped_condition_exit: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    grouped_leader: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    grouped_v: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        ec = (row.get("entry_class") or "unclassified") or "unclassified"
        xc = (row.get("exit_class") or "unclassified") or "unclassified"
        cc = _condition_combo(row)
        grouped_e[str(ec)].append(row)
        grouped_x[str(xc)].append(row)
        grouped_c[f"{ec}|{xc}"].append(row)
        grouped_condition[cc].append(row)
        grouped_condition_entry[f"{cc}|{ec}"].append(row)
        grouped_condition_exit[f"{cc}|{xc}"].append(row)
        grouped_leader[_leader_score_bucket(row)].append(row)
        grouped_v[_row_classifier_version(row)].append(row)
    for k, v in grouped_e.items():
        by_entry[k] = _aggregate_group(v)
    for k, v in grouped_x.items():
        by_exit[k] = _aggregate_group(v)
    for k, v in grouped_c.items():
        by_combo[k] = _aggregate_group(v)
    for k, v in grouped_condition.items():
        by_condition_combo[k] = _aggregate_group(v)
    for k, v in grouped_condition_entry.items():
        by_condition_combo_entry_class[k] = _aggregate_group(v)
    for k, v in grouped_condition_exit.items():
        by_condition_combo_exit_class[k] = _aggregate_group(v)
    for k, v in grouped_leader.items():
        by_leader_score_bucket[k] = _aggregate_group(v)
    for k, v in grouped_v.items():
        by_classifier[k] = _aggregate_group(v)

    n_candidate = sum(
        1 for row in rows if _row_classifier_version(row) in CANDIDATE_CLASSIFIER_VERSIONS
    )
    return WindowStats(
        window=window,
        dates=dates,
        n_total=len(rows),
        n_candidate=n_candidate,
        overall=overall,
        by_entry=by_entry,
        by_exit=by_exit,
        by_combo=by_combo,
        by_condition_combo=by_condition_combo,
        by_condition_combo_entry_class=by_condition_combo_entry_class,
        by_condition_combo_exit_class=by_condition_combo_exit_class,
        by_leader_score_bucket=by_leader_score_bucket,
        by_classifier=by_classifier,
        confidence=_confidence_for_n(n_candidate),
    )


# ---------------------------------------------------------------------------
# 룰 candidate 추출
# ---------------------------------------------------------------------------


@dataclass
class RuleCandidate:
    rule_id: str
    title: str
    triggered_windows: List[int]
    confidence: str                       # low / medium / high
    n_largest_window: int                 # 가장 큰 윈도우의 트리거 표본 수
    consistent_across_windows: bool       # 5/10/20 모두 트리거?
    evidence: Dict[str, dict] = field(default_factory=dict)  # window→ratio/n/메트릭
    proposed_overrides: List[Override] = field(default_factory=list)
    auto_apply: bool = False
    # PR-A 정책: 후보가 PR-A 의 commit 단계에서 setattr 시도되어도 좋은지 여부.
    # 기본값은 False — 사람이 직접 JSON 을 편집해 true 로 바꿔야 commit 적용된다
    # (Approval-by-edit 패턴; 별도 승인 파일 없이 동일 JSON 편집만으로 인증).
    allow_auto_apply: bool = False
    reason_no_apply: str = "rolling 모듈은 후보만 생성한다 — 적용은 PR-A(dry_run)"

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "triggered_windows": self.triggered_windows,
            "confidence": self.confidence,
            "n_largest_window": self.n_largest_window,
            "consistent_across_windows": self.consistent_across_windows,
            "evidence": self.evidence,
            "proposed_overrides": [o.to_dict() for o in self.proposed_overrides],
            "auto_apply": self.auto_apply,
            "allow_auto_apply": self.allow_auto_apply,
            "reason_no_apply": self.reason_no_apply,
        }


# ---- 윈도우별 룰 평가(rules.py 와 동일 임계). 트리거되면 evidence dict 반환 ----

def _eval_block_fake(rows: List[dict]) -> Optional[dict]:
    if not rows:
        return None
    fakes = [r for r in rows if r.get("entry_class") == "fake_breakout"]
    n, total = len(fakes), len(rows)
    ratio = n / total if total else 0
    if ratio >= FAKE_BREAKOUT_RATIO_BLOCK and n >= 2:
        return {
            "n": n, "total": total, "ratio": ratio,
            "avg_upper_wick": _safe_mean([f.get("upper_wick_ratio") for f in fakes]),
            "avg_open_return": _safe_mean([f.get("open_return") for f in fakes]),
        }
    return None


def _eval_wait_pullback(rows: List[dict]) -> Optional[dict]:
    a = [r for r in rows if r.get("entry_class") == "breakout_chase"]
    b = [r for r in rows if r.get("entry_class") == "first_pullback"]
    if len(a) < 2 or len(b) < 1:
        return None
    a_r = _safe_mean([r.get("r_multiple") for r in a])
    b_r = _safe_mean([r.get("r_multiple") for r in b])
    if a_r is None or b_r is None:
        return None
    if a_r < 0 and b_r > 0 and (b_r - a_r) >= A_VS_B_DIFF_R:
        return {"n": len(a), "total": len(rows),
                "ratio": len(a) / len(rows),
                "a_avg_r": a_r, "b_avg_r": b_r}
    return None


def _eval_take_faster(rows: List[dict]) -> Optional[dict]:
    realized = [r for r in rows if (r.get("realized_return") or 0) > 0]
    late = [r for r in realized if r.get("exit_class") == "late_take"]
    if len(late) < 2 or not realized:
        return None
    ratio = len(late) / len(realized)
    if ratio >= LATE_TAKE_RATIO:
        return {"n": len(late), "total": len(realized), "ratio": ratio,
                "avg_give_back_r": _safe_mean([r.get("give_back_r") for r in late])}
    return None


def _eval_trailing(rows: List[dict]) -> Optional[dict]:
    realized = [r for r in rows if (r.get("realized_return") or 0) > 0]
    fast = [r for r in realized if r.get("exit_class") == "fast_take"]
    if len(fast) < 2 or not realized:
        return None
    ratio = len(fast) / len(realized)
    if ratio >= FAST_TAKE_RATIO:
        return {"n": len(fast), "total": len(realized), "ratio": ratio,
                "avg_over_run_r": _safe_mean([r.get("over_run_r") for r in fast])}
    return None


def _eval_be_cut(rows: List[dict]) -> Optional[dict]:
    losers = [r for r in rows if (r.get("realized_return") or 0) < 0]
    if not losers:
        return None
    be = [r for r in losers if (r.get("be_violation") or 0) >= 1.0]
    if len(be) < 2:
        return None
    ratio = len(be) / len(losers)
    if ratio >= BE_VIOLATION_RATIO:
        return {"n": len(be), "total": len(losers), "ratio": ratio}
    return None


def _rows_by_condition_combo(rows: List[dict], combo: str) -> List[dict]:
    return [r for r in rows if _condition_combo(r) == combo]


def _eval_prefer_quant_and_dante(rows: List[dict]) -> Optional[dict]:
    quant = _rows_by_condition_combo(rows, CONDITION_COMBO_QUANT_ONLY)
    both = _rows_by_condition_combo(rows, CONDITION_COMBO_QUANT_AND_DANTE)
    if len(quant) < CONDITION_COMBO_MIN_N or len(both) < CONDITION_COMBO_MIN_N:
        return None
    q = _aggregate_group(quant)
    b = _aggregate_group(both)
    q_avg = q.get("avg_r")
    b_avg = b.get("avg_r")
    q_win = q.get("win_rate")
    b_win = b.get("win_rate")
    if b_avg is None or q_avg is None or b_win is None or q_win is None:
        return None
    if (
        b_avg - q_avg >= CONDITION_COMBO_AVG_R_DIFF
        or b_win - q_win >= CONDITION_COMBO_WIN_RATE_DIFF
    ):
        return {
            "n": len(both),
            "total": len(rows),
            "ratio": len(both) / max(len(rows), 1),
            "quant_only": q,
            "quant_and_dante": b,
        }
    return None


def _eval_relax_quant_only(rows: List[dict]) -> Optional[dict]:
    quant = _rows_by_condition_combo(rows, CONDITION_COMBO_QUANT_ONLY)
    both = _rows_by_condition_combo(rows, CONDITION_COMBO_QUANT_AND_DANTE)
    if len(quant) < CONDITION_COMBO_MIN_N:
        return None
    q = _aggregate_group(quant)
    b = _aggregate_group(both)
    q_avg = q.get("avg_r")
    q_win = q.get("win_rate")
    if q_avg is None or q_win is None:
        return None
    both_avg = b.get("avg_r")
    materially_worse = both_avg is not None and q_avg + CONDITION_COMBO_AVG_R_DIFF < both_avg
    if q_avg > 0 and q_win >= 0.5 and not materially_worse:
        return {
            "n": len(quant),
            "total": len(rows),
            "ratio": len(quant) / max(len(rows), 1),
            "quant_only": q,
            "quant_and_dante": b,
        }
    return None


def _eval_disable_breakout_probe_live(rows: List[dict]) -> Optional[dict]:
    def text(row: dict) -> str:
        return " ".join(
            str(row.get(key) or "")
            for key in ("reason_code", "plan_source", "entry_class", "reason")
        ).upper()

    breakout = [
        r for r in rows
        if "BREAKOUT_SMALL" in text(r)
        or "BUY_BREAKOUT_SMALL" in text(r)
        or "BREAKOUT_PROBE" in text(r)
    ]
    pullback = [
        r for r in rows
        if "BUY_PULLBACK_RECLAIM" in text(r)
        or "PULLBACK_RECLAIM" in text(r)
        or "QUANT_FIRST_PULLBACK_READY" in text(r)
        or str(r.get("entry_class") or "") == "first_pullback"
    ]
    if len(breakout) < CONDITION_COMBO_MIN_N or len(pullback) < CONDITION_COMBO_MIN_N:
        return None
    breakout_avg = _aggregate_group(breakout).get("avg_r")
    pullback_avg = _aggregate_group(pullback).get("avg_r")
    if breakout_avg is None or pullback_avg is None:
        return None
    if breakout_avg < pullback_avg and breakout_avg < 0:
        return {
            "n": len(breakout),
            "total": len(rows),
            "ratio": len(breakout) / max(len(rows), 1),
            "breakout_avg_r": breakout_avg,
            "pullback_avg_r": pullback_avg,
        }
    return None


def _eval_penalize_dante_only_shadow(shadow_rows: List[dict]) -> Optional[dict]:
    dante = _rows_by_condition_combo(shadow_rows, CONDITION_COMBO_DANTE_ONLY)
    if len(dante) < CONDITION_COMBO_MIN_N:
        return None
    stats = _aggregate_group(dante)
    hit_stop_rate = stats.get("hit_stop_rate")
    reached_1r_rate = stats.get("reached_1r_rate")
    stop_bad = hit_stop_rate is not None and hit_stop_rate >= DANTE_ONLY_SHADOW_STOP_RATE
    r1_bad = reached_1r_rate is not None and reached_1r_rate <= DANTE_ONLY_SHADOW_REACHED_1R_MAX
    if stop_bad or r1_bad:
        return {
            "n": len(dante),
            "total": len(shadow_rows),
            "ratio": len(dante) / max(len(shadow_rows), 1),
            "dante_only_shadow": stats,
        }
    return None


RULE_EVALUATORS = {
    "block_fake_breakout": _eval_block_fake,
    "wait_for_pullback":   _eval_wait_pullback,
    "take_profit_faster":  _eval_take_faster,
    "apply_trailing":      _eval_trailing,
    "break_even_cut":      _eval_be_cut,
}


def evaluate_candidates(
    rows_by_window: Dict[int, List[dict]],
    window_total_by_window: Dict[int, int],
    shadow_rows_by_window: Optional[Dict[int, List[dict]]] = None,
) -> List[RuleCandidate]:
    """윈도우별 rows 를 받아 5종 룰 candidate 평가.

    confidence 계산(사용자 명세):
      - 윈도우 전체 거래 수 N 기준(가장 큰 윈도우)
          N < 20             → low
          20 ≤ N < 40        → medium 후보
          N ≥ 40             → high 후보
      - high 후보는 5/10/20 모든 윈도우에서 같은 룰이 트리거되어야(=동일 손실 패턴
        반복) 최종 high. 하나라도 빠지면 medium 으로 강등.

    n_largest_window 필드는 *룰 트리거 표본 수*(예: 가짜돌파 건수) 로
    별도 기록한다 — confidence 와는 다른 의미라 혼동 방지.
    """
    out: List[RuleCandidate] = []
    windows_sorted = sorted(rows_by_window.keys())
    for rule_id, evaluator in RULE_EVALUATORS.items():
        per_window: Dict[int, dict] = {}
        for w in windows_sorted:
            ev = evaluator(rows_by_window[w])
            if ev is not None:
                per_window[w] = ev
        if not per_window:
            continue

        triggered = sorted(per_window.keys())
        consistent = set(triggered) == set(windows_sorted)

        largest_w = max(triggered)
        n_trigger = int(per_window[largest_w].get("n", 0))
        n_window_total = int(window_total_by_window.get(largest_w, 0))

        confidence = _confidence_for_n(n_window_total)
        if confidence == "high" and not consistent:
            confidence = "medium"

        evidence = {f"{w}d": per_window[w] for w in triggered}

        proposed = [Override.from_dict(d) for d in PROPOSED_OVERRIDES.get(rule_id, [])]
        out.append(RuleCandidate(
            rule_id=rule_id,
            title=RULE_TITLES.get(rule_id, rule_id),
            triggered_windows=triggered,
            confidence=confidence,
            n_largest_window=n_trigger,
            consistent_across_windows=consistent,
            evidence=evidence,
            proposed_overrides=proposed,
        ))
    combo_evaluators = {
        "prefer_quant_and_dante": _eval_prefer_quant_and_dante,
        "relax_quant_only": _eval_relax_quant_only,
        "disable_breakout_probe_live": _eval_disable_breakout_probe_live,
    }
    combo_titles = {
        "prefer_quant_and_dante": "QUANT_AND_DANTE 우선",
        "relax_quant_only": "QUANT_ONLY 단독 허용 완화",
        "disable_breakout_probe_live": "돌파 소량 live 비활성 유지",
    }
    combo_summaries = {
        "prefer_quant_and_dante": "QUANT_AND_DANTE가 QUANT_ONLY보다 평균 R 또는 승률이 우위입니다.",
        "relax_quant_only": "QUANT_ONLY가 단독으로도 충분한 기대값을 보입니다.",
        "disable_breakout_probe_live": "BREAKOUT_SMALL 계열이 BUY_PULLBACK_RECLAIM보다 부진합니다.",
    }
    for rule_id, evaluator in combo_evaluators.items():
        per_window: Dict[int, dict] = {}
        for w in windows_sorted:
            ev = evaluator(rows_by_window[w])
            if ev is not None:
                per_window[w] = ev
        if not per_window:
            continue
        triggered = sorted(per_window.keys())
        consistent = set(triggered) == set(windows_sorted)
        largest_w = max(triggered)
        n_trigger = int(per_window[largest_w].get("n", 0))
        n_window_total = int(window_total_by_window.get(largest_w, 0))
        confidence = _confidence_for_n(n_window_total)
        if confidence == "high" and not consistent:
            confidence = "medium"
        out.append(RuleCandidate(
            rule_id=rule_id,
            title=combo_titles[rule_id],
            triggered_windows=triggered,
            confidence=confidence,
            n_largest_window=n_trigger,
            consistent_across_windows=consistent,
            evidence={f"{w}d": per_window[w] for w in triggered},
            proposed_overrides=[],
            reason_no_apply=combo_summaries[rule_id],
        ))

    if shadow_rows_by_window:
        per_window = {}
        for w in windows_sorted:
            ev = _eval_penalize_dante_only_shadow(shadow_rows_by_window.get(w, []))
            if ev is not None:
                per_window[w] = ev
        if per_window:
            triggered = sorted(per_window.keys())
            consistent = set(triggered) == set(windows_sorted)
            largest_w = max(triggered)
            n_trigger = int(per_window[largest_w].get("n", 0))
            n_window_total = int(per_window[largest_w].get("total", 0))
            confidence = _confidence_for_n(n_window_total)
            if confidence == "high" and not consistent:
                confidence = "medium"
            out.append(RuleCandidate(
                rule_id="penalize_dante_only",
                title="DANTE_ONLY 매수 금지 유지",
                triggered_windows=triggered,
                confidence=confidence,
                n_largest_window=n_trigger,
                consistent_across_windows=consistent,
                evidence={f"{w}d": per_window[w] for w in triggered},
                proposed_overrides=[],
                reason_no_apply="DANTE_ONLY shadow 표본의 손절률/1R 도달률이 불리합니다.",
            ))
    return out


# ---------------------------------------------------------------------------
# 출력
# ---------------------------------------------------------------------------


def _json_default(obj):
    if isinstance(obj, float):
        if obj != obj:  # NaN
            return None
    raise TypeError(f"unserializable: {type(obj).__name__}")


def write_rolling_outputs(
    reviews_dir: str,
    as_of_date: str,
    window_stats: List[WindowStats],
    candidates: List[RuleCandidate],
    overrides_evidence_by_window: Dict[int, List[dict]],
    shadow_evidence: Optional[Dict[str, object]] = None,
) -> Dict[str, str]:
    os.makedirs(reviews_dir, exist_ok=True)
    yyyymmdd = as_of_date.replace("-", "")
    summary_path = os.path.join(reviews_dir, f"rolling_summary_{yyyymmdd}.json")
    candidates_path = os.path.join(reviews_dir, f"rule_candidates_{yyyymmdd}.json")

    summary_payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "as_of_date": as_of_date,
        "windows": [s.window for s in window_stats],
        "stats": [s.to_dict() for s in window_stats],
        "overrides_evidence_by_window": {
            f"{w}d": ev for w, ev in overrides_evidence_by_window.items()
        },
    }
    if shadow_evidence is not None:
        summary_payload["shadow_evidence"] = shadow_evidence
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, ensure_ascii=False, indent=2, default=_json_default)

    candidates_payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "as_of_date": as_of_date,
        "windows": [s.window for s in window_stats],
        "auto_apply_globally_disabled": True,
        "note": (
            "rolling 모듈은 후보만 만든다. 모든 confidence 의 후보가 auto_apply=false 로 떨어지며, "
            "실제 적용은 PR-A(dry_run) 의 별도 모듈이 담당한다."
        ),
        "candidates": [c.to_dict() for c in candidates],
    }
    with open(candidates_path, "w", encoding="utf-8") as f:
        json.dump(candidates_payload, f, ensure_ascii=False, indent=2, default=_json_default)

    return {"summary": summary_path, "candidates": candidates_path}


# ---------------------------------------------------------------------------
# 파이프라인
# ---------------------------------------------------------------------------


@dataclass
class RollingResult:
    as_of_date: str
    windows: List[int]
    window_stats: List[WindowStats]
    candidates: List[RuleCandidate]
    overrides_evidence_by_window: Dict[int, List[dict]]
    shadow_evidence: Optional[Dict[str, object]] = None
    output_paths: Dict[str, str] = field(default_factory=dict)


def run_rolling(
    as_of_date: Optional[str] = None,
    windows: Tuple[int, ...] = DEFAULT_WINDOWS,
    reviews_dir: str = REVIEWS_DIR_DEFAULT,
    write: bool = True,
    include_shadow: bool = True,
    shadow_csv: Optional[str] = None,
    entry_csv: Optional[str] = None,
) -> RollingResult:
    available = discover_review_dates(reviews_dir)
    if not available:
        raise FileNotFoundError(
            f"{reviews_dir} 에 trade_review_*.csv 가 없습니다. analyze_today.py 를 먼저 돌리세요."
        )
    if as_of_date is None:
        as_of_date = available[-1]

    window_stats: List[WindowStats] = []
    rows_by_window: Dict[int, List[dict]] = {}
    shadow_rows_by_window: Dict[int, List[dict]] = {}
    overrides_evidence_by_window: Dict[int, List[dict]] = {}
    for w in windows:
        dates = select_window_dates(available, as_of_date, w)
        rows = load_trade_rows(reviews_dir, dates)
        shadow_rows = load_shadow_condition_rows(
            shadow_csv or os.path.join("data", "dante_shadow_training.csv"),
            dates,
        )
        evidence = load_overrides_evidence(reviews_dir, dates)
        rows_by_window[w] = rows
        shadow_rows_by_window[w] = shadow_rows
        overrides_evidence_by_window[w] = evidence
        window_stats.append(aggregate_window(w, dates, rows))

    # 룰 후보 평가는 v2 분류기 표본만으로 — v1 fallback 거래는 분류 임계가 다르므로
    # 통계가 흐려진다. 전체 rows 는 by_classifier_version 통계 노출에만 쓰인다.
    candidate_rows_by_window = {
        w: _filter_candidate_rows(rows_by_window[w]) for w in windows
    }
    window_total_by_window = {w: len(candidate_rows_by_window[w]) for w in windows}
    candidates = evaluate_candidates(
        candidate_rows_by_window,
        window_total_by_window,
        shadow_rows_by_window=shadow_rows_by_window,
    )

    # === shadow 트랙(false-negative) 통합 ===
    # tighten 룰이 같은 target 을 동시에 건드리면 release 후보를 자동으로 무력화한다.
    # 양방향 동시 변경 → 모듈 상수 진동 위험을 PR-A 적용기 이전 단계에서 차단.
    shadow_evidence: Optional[Dict[str, object]] = None
    if include_shadow and any(candidate_rows_by_window.values()):
        try:
            from .shadow_rules import (
                build_shadow_evidence,
                evaluate_release_candidates,
            )
        except ImportError:
            shadow_evidence = None
        else:
            sr_kwargs: Dict[str, object] = {}
            if shadow_csv:
                sr_kwargs["shadow_csv"] = shadow_csv
            if entry_csv:
                sr_kwargs["entry_csv"] = entry_csv
            try:
                shadow_evidence = build_shadow_evidence(**sr_kwargs)  # type: ignore[arg-type]
            except FileNotFoundError:
                shadow_evidence = None
            else:
                tighten_targets = {
                    ov.target for cand in candidates for ov in cand.proposed_overrides
                }
                release_kwargs = dict(sr_kwargs)
                release_kwargs["windows_to_attribute"] = list(windows)
                release_kwargs["tighten_targets_today"] = tighten_targets
                release_candidates = evaluate_release_candidates(**release_kwargs)  # type: ignore[arg-type]
                candidates = list(candidates) + release_candidates

    paths: Dict[str, str] = {}
    if write:
        paths = write_rolling_outputs(
            reviews_dir, as_of_date, window_stats, candidates,
            overrides_evidence_by_window,
            shadow_evidence=shadow_evidence,
        )

    return RollingResult(
        as_of_date=as_of_date,
        windows=list(windows),
        window_stats=window_stats,
        candidates=candidates,
        overrides_evidence_by_window=overrides_evidence_by_window,
        shadow_evidence=shadow_evidence,
        output_paths=paths,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m review.rolling",
        description="최근 N영업일 누적 통계 + rule_candidates 산출 (자동 적용 없음).",
    )
    parser.add_argument(
        "as_of_date", nargs="?", default=None,
        help="기준일 YYYY-MM-DD (생략시 reviews_dir 의 마지막 날짜).",
    )
    parser.add_argument(
        "--windows", default=",".join(str(w) for w in DEFAULT_WINDOWS),
        help="콤마로 구분된 윈도우 영업일 (기본 5,10,20).",
    )
    parser.add_argument(
        "--reviews-dir", default=REVIEWS_DIR_DEFAULT,
        help=f"리뷰 산출 디렉토리 (기본 {REVIEWS_DIR_DEFAULT}).",
    )
    parser.add_argument(
        "--no-write", action="store_true",
        help="JSON 출력 생략(stdout 요약만).",
    )
    parser.add_argument(
        "--no-shadow", action="store_true",
        help="shadow 트랙(거절 표본) 평가/출력을 건너뛴다(테스트/디버그용).",
    )
    return parser.parse_args(argv)


def _print_summary(result: RollingResult) -> None:
    print(f"== rolling summary as_of {result.as_of_date} ==")
    for s in result.window_stats:
        ovr = s.overall
        avg_r = ovr.get("avg_r")
        win_rate = ovr.get("win_rate")
        pf = ovr.get("profit_factor")
        hit_stop = ovr.get("hit_stop_rate")
        payoff = ovr.get("payoff_ratio")
        print(
            "  [{w}d] dates={d}건 trades={n} avg_r={ar} win={wr} pf={pf} confidence={c}".format(
                w=s.window,
                d=len(s.dates),
                n=s.n_total,
                ar=("n/a" if avg_r is None else f"{avg_r:+.2f}R"),
                wr=("n/a" if win_rate is None else f"{win_rate:.0%}"),
                pf=("n/a" if pf is None else f"{pf:.2f}"),
                c=s.confidence,
            )
        )
    if not result.candidates:
        print("  - 룰 후보 없음")
    else:
        print(f"  - 룰 후보 {len(result.candidates)}건 (모두 auto_apply=false):")
        for c in result.candidates:
            print(
                "      - {r} | windows={w} | confidence={c} | n={n} | consistent={x}".format(
                    r=c.rule_id, w=c.triggered_windows, c=c.confidence,
                    n=c.n_largest_window, x=c.consistent_across_windows,
                )
            )

    # shadow 요약 — 매핑 미등록 의심 게이트는 별도로 안내해 매핑 추가 흐름을 지원.
    if result.shadow_evidence:
        ev = result.shadow_evidence
        n_lab = ev.get("shadow_n_labeled", 0)
        suspects = [
            r for r in (ev.get("by_reason") or []) if r.get("is_suspect")
        ]
        candidates_n = sum(
            1 for r in (ev.get("by_reason") or []) if r.get("is_release_candidate")
        )
        print(
            f"  - shadow 트랙: 라벨링 {n_lab}건, 의심 게이트 {len(suspects)}개, "
            f"release 후보 {candidates_n}개"
        )
        unmapped = [r for r in suspects if r.get("mapped_target") is None]
        if unmapped:
            top = sorted(unmapped, key=lambda r: -(r.get("reached_1r") or 0))[:3]
            for r in top:
                print(
                    "      - 매핑 미등록 의심 게이트: {k} (n={n}, 1R={p}%)".format(
                        k=r.get("reason_code"),
                        n=r.get("n"),
                        p=int((r.get("reached_1r") or 0) * 100),
                    )
                )

    if result.output_paths:
        for kind, path in result.output_paths.items():
            print(f"  - {kind}: {path}")


def _reconfigure_stdout_utf8() -> None:
    """Windows 콘솔 cp949 에서 em-dash 등 비-cp949 문자 출력 실패를 회피."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def main(argv: Optional[List[str]] = None) -> int:
    _reconfigure_stdout_utf8()
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])
    try:
        windows = tuple(int(x) for x in args.windows.split(",") if x.strip())
    except ValueError:
        print("--windows 는 콤마로 구분된 정수여야 합니다.", file=sys.stderr)
        return 2
    if not windows:
        print("--windows 가 비어 있습니다.", file=sys.stderr)
        return 2

    try:
        result = run_rolling(
            as_of_date=args.as_of_date,
            windows=windows,
            reviews_dir=args.reviews_dir,
            write=not args.no_write,
            include_shadow=not args.no_shadow,
        )
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    _print_summary(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
