"""진입 정책 dry_run 비교 (실거래 영향 0).

``data/dante_entry_training.csv`` 에 누적된 진입 후보 표본을 같은 후보
풀로 두고, 6개 진입 정책이 각각 어떤 표본을 통과/거부하는지를 시뮬레이션
한다. 사후 라벨(reached_1r/2r/hit_stop/return_*) 은 학습 CSV 에서 그대로
가져오고, ``data/intraday/YYYYMMDD/<code>.csv`` 캐시가 있으면 D 피처를
보강해 ``review.classifier`` 의 fake_breakout / late_chase 분류 규칙과
같은 임계로 분류 결과를 부여한다.

본 모듈은 ``entry_strategy`` / ``exit_strategy`` 의 어떤 상수도 변경하지
않는다. 출력은 다음 두 파일이며 모두 dry_run 산출물이다:

    data/reviews/strategy_policy_comparison_YYYYMMDD.csv
    data/reviews/strategy_policy_comparison_YYYYMMDD.md

CLI:
    python -m review.policy_replay
    python -m review.policy_replay --date 2026-04-30
    python -m review.policy_replay --training-csv data/dante_entry_training.csv

비교 정책:

    BASE                현재 로직 (A급 0봉 돌파 시 1차 추격 25%)
    CONSERVATIVE_A      A급 0봉 돌파 시 1차 추격 10%
    MICRO_A             A급 0봉 돌파 시 1차 추격 5%
    PULLBACK_ONLY       A급 0봉 즉시 진입 금지(=A급 표본 전부 차단)
    LATENCY_GATED       obs_elapsed_sec ≤ 60 만 즉시 진입 / >60 눌림 대기 / >180 제외
    HIGH_CHASE_BLOCKED  near_session_high == 1 + 얕은 눌림 차단(강한 돌파 예외)

출력 메트릭(정책별 진입 표본 한정):

    n_candidates / n_entries / n_blocked
    near_high_ratio
    avg_pullback_pct_from_high / avg_high_to_entry_drop_pct
    late_chase_ratio / fake_breakout_ratio
    win_rate / avg_return / expected_value_r
    avg_mfe / avg_mae / worst_return / profit_factor
    avg_return_1m / 3m / 5m / 10m

사후 라벨 → R-multiple 단순화:

    reached_2r==1                          → +2.0R
    reached_1r==1 + hit_stop==1            →  0.0R (BE 컷)
    reached_1r==1                          → +1.0R
    hit_stop==1                            → -1.0R
    그 외                                  → return_20m / R_UNIT_PCT

부분익절·잔량 트레일링은 단순화한다. 정책 간 비교를 같은 척도로 두는 것이
목적이라 BASE 도 같은 단순화를 따른다.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean
from typing import Callable, Dict, List, Optional, Sequence

from exit_strategy import R_UNIT_PCT
from review import classifier as _clf
from review.intraday import (
    INTRADAY_DIR_DEFAULT,
    compute_intraday_metrics,
    load_minute_bars,
)


TRAINING_CSV_DEFAULT = os.path.join("data", "dante_entry_training.csv")
REVIEWS_DIR_DEFAULT = os.path.join("data", "reviews")


# === 정책 임계 (사용자 명세를 단일 출처로 보존) ===
LATENCY_FAST_MAX_SEC = 60.0          # obs ≤ 60s 만 즉시 진입
LATENCY_OBSERVE_MAX_SEC = 180.0      # 60 < obs ≤ 180s 는 눌림 대기, > 180s 는 신규진입 제외
HIGH_CHASE_PULLBACK_MIN_PCT = 0.007  # 0.7% — 사용자 명세("0.7" → pullback_pct_from_high < 0.7%)

# 강한 돌파 예외(HIGH_CHASE_BLOCKED 정책의 escape hatch).
# review.classifier._is_breakout_protected 와 동일한 임계를 의도적으로 재사용.
EXCEPT_VOLUME_RATIO_MIN = _clf.BREAKOUT_PROTECT_VOL_RATIO    # 2.0
EXCEPT_BREAKOUT_BODY_MIN = _clf.BREAKOUT_PROTECT_BODY_MIN    # 0.55
EXCEPT_UPPER_WICK_MAX = _clf.BREAKOUT_PROTECT_WICK_MAX       # 0.25

# BASE 정책의 1차 추격 비율 — entry_strategy.DANTE_FIRST_ENTRY_RATIO 와 일치하는
# 의미값을 모듈 상수로만 사용한다(절대 setattr 안 함).
BASE_RATIO = 0.25
CONSERVATIVE_RATIO = 0.10
MICRO_RATIO = 0.05


# ---------------------------------------------------------------------------
# Sample
# ---------------------------------------------------------------------------


@dataclass
class Sample:
    """학습 CSV 1행 + (있으면) intraday D 피처 보강 결과."""

    code: str
    name: str
    captured_time: datetime
    entry_price: float
    obs_elapsed_sec: Optional[float]
    pullback_pct_from_high: Optional[float]
    breakout_grade_a: bool
    breakout_grade_b: bool
    return_5m_label: Optional[float]
    return_10m_label: Optional[float]
    return_20m_label: Optional[float]
    max_return_25m: Optional[float]
    min_return_25m: Optional[float]
    reached_1r: int
    reached_2r: int
    hit_stop: int
    time_exit: int
    metric_source: str
    features: Dict[str, Optional[float]] = field(default_factory=dict)
    intraday_metrics: Dict[str, Optional[float]] = field(default_factory=dict)

    @property
    def grade(self) -> str:
        if self.breakout_grade_a:
            return "A"
        if self.breakout_grade_b:
            return "B"
        return ""

    @property
    def mfe_r(self) -> Optional[float]:
        if self.max_return_25m is None or R_UNIT_PCT <= 0:
            return None
        return self.max_return_25m / R_UNIT_PCT

    @property
    def mae_r(self) -> Optional[float]:
        if self.min_return_25m is None or R_UNIT_PCT <= 0:
            return None
        return self.min_return_25m / R_UNIT_PCT

    @property
    def simulated_r(self) -> float:
        if self.reached_2r == 1:
            return 2.0
        if self.reached_1r == 1 and self.hit_stop == 1:
            return 0.0
        if self.reached_1r == 1:
            return 1.0
        if self.hit_stop == 1:
            return -1.0
        if self.return_20m_label is not None:
            return self.return_20m_label / R_UNIT_PCT if R_UNIT_PCT > 0 else 0.0
        return 0.0

    @property
    def simulated_return(self) -> float:
        return self.simulated_r * R_UNIT_PCT

    @property
    def near_session_high(self) -> bool:
        v = self.features.get("entry_near_session_high")
        return v is not None and v >= 1.0

    @property
    def entry_class(self) -> str:
        return classify_sample(
            features=self.features,
            mfe_r=self.mfe_r,
            mae_r=self.mae_r,
            grade=self.grade,
            entry_stage_max=2 if self.grade == "B" else 1,
        )


def classify_sample(
    *,
    features: Dict[str, Optional[float]],
    mfe_r: Optional[float],
    mae_r: Optional[float],
    grade: str,
    entry_stage_max: int,
) -> str:
    """``review.classifier._classify_entry`` 와 같은 규칙을 sample 단위로 적용.

    fake_breakout → first_pullback → late_chase → breakout_chase 순으로 평가.
    NEW_FEATURE_KEYS 가 하나도 없으면 v1(open_return / px_over_bb55_pct) 로 fallback.
    """
    if (
        mfe_r is not None and mae_r is not None
        and mfe_r == mfe_r and mae_r == mae_r
        and mfe_r < _clf.FAKE_BREAKOUT_MFE_R
        and mae_r <= _clf.FAKE_BREAKOUT_MAE_R
    ):
        return "fake_breakout"
    if grade == "B" or entry_stage_max >= 2:
        return "first_pullback"

    score, _reasons = _clf._late_chase_score(features)
    strong = _clf._is_strong_late_chase(features)
    protected = _clf._is_breakout_protected(features)
    has_new = _clf._has_any_new_feature(features)

    is_late = False
    if has_new:
        if not protected and (strong or score >= _clf.LATE_CHASE_MIN_SCORE):
            is_late = True
    else:
        v1_late, _ = _clf._v1_late_chase(features)
        if v1_late and not protected:
            is_late = True

    if is_late:
        return "late_chase"
    return "breakout_chase"


# ---------------------------------------------------------------------------
# 입력 로드
# ---------------------------------------------------------------------------


def _to_float(v) -> Optional[float]:
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int(v, default: int = 0) -> int:
    f = _to_float(v)
    if f is None:
        return default
    return int(f)


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _normalize_code(code: str) -> str:
    return str(code or "").strip().lstrip("A")


def load_samples(
    training_csv: str,
    *,
    target_date: Optional[str] = None,
    intraday_dir: str = INTRADAY_DIR_DEFAULT,
) -> List[Sample]:
    """학습 CSV → Sample 리스트.

    target_date 가 None 이면 CSV 의 captured_time 기준 가장 최신 날짜의
    표본만 사용한다(가장 최근 거래일).
    """
    if not os.path.exists(training_csv):
        raise FileNotFoundError(f"training csv 가 없습니다: {training_csv}")

    raw_rows: List[Dict[str, str]] = []
    with open(training_csv, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            captured_time = row.get("captured_time") or ""
            if len(captured_time) < 10:
                continue
            raw_rows.append(row)
    if not raw_rows:
        return []

    if target_date is None:
        target_date = max(r.get("captured_time", "")[:10] for r in raw_rows)

    rows = [r for r in raw_rows if r.get("captured_time", "").startswith(target_date)]
    samples: List[Sample] = []
    for row in rows:
        captured_time = _parse_dt(row.get("captured_time"))
        if captured_time is None:
            continue
        code = _normalize_code(row.get("code", ""))
        name = row.get("name") or ""
        entry_price = _to_float(row.get("entry_price")) or 0.0
        if not code or entry_price <= 0:
            continue

        sample = Sample(
            code=code,
            name=name,
            captured_time=captured_time,
            entry_price=entry_price,
            obs_elapsed_sec=_to_float(row.get("obs_elapsed_sec")),
            pullback_pct_from_high=_to_float(row.get("pullback_pct_from_high")),
            breakout_grade_a=(_to_float(row.get("breakout_grade_a")) or 0.0) >= 0.5,
            breakout_grade_b=(_to_float(row.get("breakout_grade_b")) or 0.0) >= 0.5,
            return_5m_label=_to_float(row.get("return_5m")),
            return_10m_label=_to_float(row.get("return_10m")),
            return_20m_label=_to_float(row.get("return_20m")),
            max_return_25m=_to_float(row.get("max_return_25m")),
            min_return_25m=_to_float(row.get("min_return_25m")),
            reached_1r=_to_int(row.get("reached_1r")),
            reached_2r=_to_int(row.get("reached_2r")),
            hit_stop=_to_int(row.get("hit_stop")),
            time_exit=_to_int(row.get("time_exit")),
            metric_source="training_csv",
        )

        # 학습 CSV 에서 직접 채울 수 있는 features.
        feats: Dict[str, Optional[float]] = {
            "open_return": _to_float(row.get("open_return")),
            "px_over_bb55_pct": _to_float(row.get("px_over_bb55_pct")),
            "px_over_env13_pct": _to_float(row.get("px_over_env13_pct")),
            "upper_wick_ratio": _to_float(row.get("upper_wick_ratio")),
            "pullback_pct_from_high": sample.pullback_pct_from_high,
            "obs_elapsed_sec": sample.obs_elapsed_sec,
            "chejan_strength": _to_float(row.get("chejan_strength")),
            "volume_speed": _to_float(row.get("volume_speed")),
            "spread_rate": _to_float(row.get("spread_rate")),
        }

        intraday = _attach_intraday(
            target_date=target_date,
            code=code,
            captured_time=captured_time,
            entry_price=entry_price,
            intraday_dir=intraday_dir,
        )
        sample.intraday_metrics = intraday
        if intraday:
            sample.metric_source = "training_csv+kiwoom_1m_csv"
        for key, value in intraday.items():
            if value is None:
                continue
            if isinstance(value, float) and value != value:
                continue
            feats[key] = value
        sample.features = feats
        samples.append(sample)

    samples.sort(key=lambda s: s.captured_time)
    return samples


def _attach_intraday(
    *,
    target_date: str,
    code: str,
    captured_time: datetime,
    entry_price: float,
    intraday_dir: str,
) -> Dict[str, Optional[float]]:
    """intraday CSV 가 있으면 D 피처 dict, 없으면 빈 dict 반환."""
    bars = load_minute_bars(target_date, code, intraday_dir=intraday_dir)
    if not bars:
        return {}
    return compute_intraday_metrics(captured_time, entry_price, bars)


# ---------------------------------------------------------------------------
# 정책
# ---------------------------------------------------------------------------


@dataclass
class PolicyDecision:
    would_enter: bool
    ratio: float
    note: str = ""


@dataclass
class Policy:
    name: str
    title: str
    description: str
    decide: Callable[[Sample], PolicyDecision]


def _decide_base(sample: Sample) -> PolicyDecision:
    return PolicyDecision(True, BASE_RATIO, "현재 로직 — A급 25%")


def _decide_conservative_a(sample: Sample) -> PolicyDecision:
    return PolicyDecision(True, CONSERVATIVE_RATIO, "A급 1차 추격 10%")


def _decide_micro_a(sample: Sample) -> PolicyDecision:
    return PolicyDecision(True, MICRO_RATIO, "A급 1차 추격 5%")


def _decide_pullback_only(sample: Sample) -> PolicyDecision:
    # 학습 CSV 의 표본은 모두 'ready' 시점이라 grade 가 분명함.
    if sample.breakout_grade_a:
        return PolicyDecision(False, 0.0, "A급 0봉 즉시 진입 금지")
    if sample.breakout_grade_b:
        return PolicyDecision(True, 1.0, "B급 첫 눌림 진입")
    return PolicyDecision(False, 0.0, "등급 없음 — 차단")


def _decide_latency_gated(sample: Sample) -> PolicyDecision:
    obs = sample.obs_elapsed_sec
    if obs is None:
        return PolicyDecision(False, 0.0, "obs_elapsed_sec 결측 — 차단")
    if obs > LATENCY_OBSERVE_MAX_SEC:
        return PolicyDecision(
            False, 0.0,
            f"obs {obs:.0f}s > {LATENCY_OBSERVE_MAX_SEC:.0f}s — 신규진입 제외",
        )
    if obs > LATENCY_FAST_MAX_SEC:
        return PolicyDecision(
            False, 0.0,
            f"obs {obs:.0f}s > {LATENCY_FAST_MAX_SEC:.0f}s — 즉시진입 금지(눌림 대기)",
        )
    return PolicyDecision(
        True, BASE_RATIO,
        f"obs {obs:.0f}s ≤ {LATENCY_FAST_MAX_SEC:.0f}s — A급 1차 추격",
    )


def _decide_high_chase_blocked(sample: Sample) -> PolicyDecision:
    near = sample.near_session_high
    pull = sample.pullback_pct_from_high
    shallow = pull is not None and pull < HIGH_CHASE_PULLBACK_MIN_PCT
    if not (near and shallow):
        return PolicyDecision(True, BASE_RATIO, "")

    # 강한 돌파 예외 — review.classifier 의 보호 패턴과 같은 임계를 사용.
    vol_ratio = sample.features.get("volume_ratio_1m")
    body = sample.features.get("breakout_candle_body_pct")
    wick = sample.features.get("upper_wick_pct")
    strong = (
        vol_ratio is not None and vol_ratio >= EXCEPT_VOLUME_RATIO_MIN
        and body is not None and body >= EXCEPT_BREAKOUT_BODY_MIN
        and wick is not None and wick <= EXCEPT_UPPER_WICK_MAX
    )
    if strong:
        return PolicyDecision(True, BASE_RATIO, "고점 근접이지만 강한 돌파 예외 — 진입 허용")
    return PolicyDecision(False, 0.0, "고점 근접 + 얕은 눌림 — 차단")


POLICIES: List[Policy] = [
    Policy(
        "BASE",
        "현재 로직 유지",
        f"A급 0봉 돌파 시 1차 추격 {BASE_RATIO:.0%} (현재 entry_strategy 와 동일).",
        _decide_base,
    ),
    Policy(
        "CONSERVATIVE_A",
        "A급 1차 추격 10% 축소",
        f"A급 0봉 돌파 시 1차 추격 {CONSERVATIVE_RATIO:.0%}, 잔량은 첫 눌림 본진입 대기.",
        _decide_conservative_a,
    ),
    Policy(
        "MICRO_A",
        "A급 1차 추격 5% 축소",
        f"A급 0봉 돌파 시 1차 추격 {MICRO_RATIO:.0%}, 잔량은 첫 눌림 본진입 대기.",
        _decide_micro_a,
    ),
    Policy(
        "PULLBACK_ONLY",
        "A급 0봉 즉시 진입 금지",
        "조건식 편입 후 첫 눌림이 확인될 때만 진입(=A급 추격 표본 전부 차단).",
        _decide_pullback_only,
    ),
    Policy(
        "LATENCY_GATED",
        "obs_elapsed_sec 60/180초 게이트",
        f"obs ≤ {LATENCY_FAST_MAX_SEC:.0f}s 만 A급 1차 진입, "
        f"{LATENCY_FAST_MAX_SEC:.0f} < obs ≤ {LATENCY_OBSERVE_MAX_SEC:.0f}s 는 눌림 대기, "
        f"obs > {LATENCY_OBSERVE_MAX_SEC:.0f}s 는 신규진입 제외.",
        _decide_latency_gated,
    ),
    Policy(
        "HIGH_CHASE_BLOCKED",
        "고점 근접 + 얕은 눌림 차단",
        f"entry_near_session_high == 1 AND pullback_pct_from_high < "
        f"{HIGH_CHASE_PULLBACK_MIN_PCT:.1%} 이면 진입 차단. "
        f"단, volume_ratio_1m ≥ {EXCEPT_VOLUME_RATIO_MIN}, "
        f"breakout_candle_body_pct ≥ {EXCEPT_BREAKOUT_BODY_MIN}, "
        f"upper_wick_pct ≤ {EXCEPT_UPPER_WICK_MAX} 동시 충족 시 강한 돌파 예외.",
        _decide_high_chase_blocked,
    ),
]


# ---------------------------------------------------------------------------
# 집계
# ---------------------------------------------------------------------------


@dataclass
class PolicyResult:
    name: str
    title: str
    description: str
    n_candidates: int
    n_entries: int
    n_blocked: int
    block_reasons: Dict[str, int] = field(default_factory=dict)
    entry_codes: List[str] = field(default_factory=list)
    metrics: Dict[str, Optional[float]] = field(default_factory=dict)


def _safe_mean(values: Sequence[Optional[float]]) -> Optional[float]:
    xs = [v for v in values if v is not None and v == v]
    return mean(xs) if xs else None


def _ratio(numerator: int, denominator: int) -> Optional[float]:
    if denominator <= 0:
        return None
    return numerator / denominator


def evaluate_policy(policy: Policy, samples: Sequence[Sample]) -> PolicyResult:
    n_candidates = len(samples)
    entries: List[Sample] = []
    block_reasons: Dict[str, int] = {}
    for s in samples:
        decision = policy.decide(s)
        if decision.would_enter:
            entries.append(s)
        else:
            key = decision.note or "차단"
            block_reasons[key] = block_reasons.get(key, 0) + 1

    classes = [s.entry_class for s in entries]
    near_high_flags = [1.0 if s.near_session_high else 0.0 for s in entries]

    win_returns = [s.simulated_return for s in entries if s.simulated_return > 0]
    loss_returns = [s.simulated_return for s in entries if s.simulated_return < 0]
    sum_win = sum(win_returns)
    sum_loss = -sum(loss_returns) if loss_returns else 0.0
    if sum_loss > 0:
        profit_factor: Optional[float] = sum_win / sum_loss
    elif sum_win > 0:
        profit_factor = float("inf")
    else:
        profit_factor = None

    avg_return_5m_combined = _safe_mean([
        s.intraday_metrics.get("return_5m_intraday")
        if s.intraday_metrics.get("return_5m_intraday") is not None
        else s.return_5m_label
        for s in entries
    ])

    metrics: Dict[str, Optional[float]] = {
        "near_high_ratio": _safe_mean(near_high_flags) if entries else None,
        "avg_pullback_pct_from_high": _safe_mean([s.pullback_pct_from_high for s in entries]),
        "avg_high_to_entry_drop_pct": _safe_mean([
            s.features.get("high_to_entry_drop_pct") for s in entries
        ]),
        "late_chase_ratio": _ratio(classes.count("late_chase"), len(classes)),
        "fake_breakout_ratio": _ratio(classes.count("fake_breakout"), len(classes)),
        "win_rate": _ratio(len(win_returns), len(entries)),
        "avg_return": _safe_mean([s.simulated_return for s in entries]),
        "expected_value_r": _safe_mean([s.simulated_r for s in entries]),
        "avg_mfe": _safe_mean([s.max_return_25m for s in entries]),
        "avg_mae": _safe_mean([s.min_return_25m for s in entries]),
        "worst_return": min((s.simulated_return for s in entries), default=None),
        "profit_factor": profit_factor,
        "avg_return_1m": _safe_mean([s.intraday_metrics.get("return_1m") for s in entries]),
        "avg_return_3m": _safe_mean([s.intraday_metrics.get("return_3m") for s in entries]),
        "avg_return_5m": avg_return_5m_combined,
        "avg_return_10m": _safe_mean([s.return_10m_label for s in entries]),
    }

    return PolicyResult(
        name=policy.name,
        title=policy.title,
        description=policy.description,
        n_candidates=n_candidates,
        n_entries=len(entries),
        n_blocked=n_candidates - len(entries),
        block_reasons=block_reasons,
        entry_codes=[s.code for s in entries],
        metrics=metrics,
    )


# ---------------------------------------------------------------------------
# 출력
# ---------------------------------------------------------------------------


_METRIC_KEYS = [
    "near_high_ratio",
    "avg_pullback_pct_from_high",
    "avg_high_to_entry_drop_pct",
    "late_chase_ratio",
    "fake_breakout_ratio",
    "win_rate",
    "avg_return",
    "expected_value_r",
    "avg_mfe",
    "avg_mae",
    "worst_return",
    "profit_factor",
    "avg_return_1m",
    "avg_return_3m",
    "avg_return_5m",
    "avg_return_10m",
]
_CSV_COLUMNS = ["policy", "title", "n_candidates", "n_entries", "n_blocked"] + _METRIC_KEYS


def _fmt_csv(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if value != value:
            return ""
        if value == float("inf"):
            return "inf"
        if value == float("-inf"):
            return "-inf"
        return f"{value:.6f}"
    return str(value)


def write_csv(results: Sequence[PolicyResult], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_COLUMNS)
        writer.writeheader()
        for r in results:
            row: Dict[str, object] = {
                "policy": r.name,
                "title": r.title,
                "n_candidates": r.n_candidates,
                "n_entries": r.n_entries,
                "n_blocked": r.n_blocked,
            }
            for key in _METRIC_KEYS:
                row[key] = _fmt_csv(r.metrics.get(key))
            writer.writerow(row)


def _fmt_pct(value, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and value != value):
        return "n/a"
    if value == float("inf"):
        return "+inf"
    if value == float("-inf"):
        return "-inf"
    return f"{value * 100:+.{digits}f}%"


def _fmt_ratio(value, digits: int = 1) -> str:
    if value is None or (isinstance(value, float) and value != value):
        return "n/a"
    return f"{value * 100:.{digits}f}%"


def _fmt_pf(value) -> str:
    if value is None:
        return "n/a"
    if value == float("inf"):
        return "+inf"
    return f"{value:.2f}"


def _fmt_r(value, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and value != value):
        return "n/a"
    return f"{value:+.{digits}f}R"


def write_markdown(
    results: Sequence[PolicyResult],
    samples: Sequence[Sample],
    *,
    target_date: str,
    path: str,
) -> None:
    grade_a = sum(1 for s in samples if s.breakout_grade_a)
    grade_b = sum(1 for s in samples if s.breakout_grade_b)
    with_intraday = sum(1 for s in samples if s.intraday_metrics)

    lines: List[str] = []
    lines.append(f"# {target_date} 진입 정책 dry_run 비교")
    lines.append("")
    lines.append(
        f"- 후보 표본: **{len(samples)}건** (등급 A {grade_a} / B {grade_b}) "
        f"— source: `data/dante_entry_training.csv`"
    )
    lines.append(
        f"- intraday 캐시 보강된 표본: **{with_intraday}/{len(samples)}건** "
        f"(보강 안 된 표본은 D 피처 일부가 결측 → 평균에서 자동 제외)"
    )
    lines.append(
        "- 사후 라벨 단순화: hit_stop=-1R / reached_1r=+1R / reached_2r=+2R / "
        "그 외 = return_20m 기반(부분익절·잔량 트레일링은 단순화)."
    )
    lines.append(
        "- 본 모듈은 entry_strategy / exit_strategy 의 어떤 상수도 변경하지 않습니다 (dry_run only)."
    )
    lines.append("")

    lines.append("## 정책 정의")
    lines.append("")
    lines.append("| 정책 | 설명 |")
    lines.append("|------|------|")
    for r in results:
        lines.append(f"| **{r.name}** | {r.description} |")
    lines.append("")

    lines.append("## 핵심 비교 — 진입 표본 / 분류 / 기대값")
    lines.append("")
    lines.append(
        "| 정책 | 후보 | 진입 | 차단 | near_high | avg_pullback | high→entry | "
        "late_chase | fake_breakout | 승률 | 평균수익 | 기대값(R) |"
    )
    lines.append(
        "|------|-----:|-----:|-----:|----------:|-------------:|-----------:|"
        "-----------:|--------------:|-----:|---------:|----------:|"
    )
    for r in results:
        m = r.metrics
        lines.append(
            "| {name} | {nc} | {ne} | {nb} | {nh} | {ap} | {hd} | "
            "{lc} | {fb} | {wr} | {ar} | {ev} |".format(
                name=r.name,
                nc=r.n_candidates,
                ne=r.n_entries,
                nb=r.n_blocked,
                nh=_fmt_ratio(m.get("near_high_ratio")),
                ap=_fmt_pct(m.get("avg_pullback_pct_from_high")),
                hd=_fmt_pct(m.get("avg_high_to_entry_drop_pct")),
                lc=_fmt_ratio(m.get("late_chase_ratio")),
                fb=_fmt_ratio(m.get("fake_breakout_ratio")),
                wr=_fmt_ratio(m.get("win_rate")),
                ar=_fmt_pct(m.get("avg_return")),
                ev=_fmt_r(m.get("expected_value_r")),
            )
        )
    lines.append("")

    lines.append("## MFE / MAE / 손익비")
    lines.append("")
    lines.append("| 정책 | 평균 MFE | 평균 MAE | 최대 손실 | 손익비 |")
    lines.append("|------|---------:|---------:|----------:|-------:|")
    for r in results:
        m = r.metrics
        lines.append(
            "| {name} | {mfe} | {mae} | {worst} | {pf} |".format(
                name=r.name,
                mfe=_fmt_pct(m.get("avg_mfe")),
                mae=_fmt_pct(m.get("avg_mae")),
                worst=_fmt_pct(m.get("worst_return")),
                pf=_fmt_pf(m.get("profit_factor")),
            )
        )
    lines.append("")

    lines.append("## 진입 후 1/3/5/10분 평균 수익률")
    lines.append("")
    lines.append("| 정책 | 1분 | 3분 | 5분 | 10분 |")
    lines.append("|------|----:|----:|----:|-----:|")
    for r in results:
        m = r.metrics
        lines.append(
            "| {n} | {a} | {b} | {c} | {d} |".format(
                n=r.name,
                a=_fmt_pct(m.get("avg_return_1m")),
                b=_fmt_pct(m.get("avg_return_3m")),
                c=_fmt_pct(m.get("avg_return_5m")),
                d=_fmt_pct(m.get("avg_return_10m")),
            )
        )
    lines.append("")

    lines.append("## 차단 사유 분포")
    lines.append("")
    any_blocked = False
    for r in results:
        if r.n_blocked == 0:
            continue
        any_blocked = True
        lines.append(f"### {r.name}")
        lines.append("")
        for reason, count in sorted(r.block_reasons.items(), key=lambda kv: -kv[1]):
            lines.append(f"- {reason}: {count}건")
        lines.append("")
    if not any_blocked:
        lines.append("(모든 정책이 모든 표본을 통과시켰습니다.)")
        lines.append("")

    lines.append("## 진입 후보 코드 목록")
    lines.append("")
    for r in results:
        codes = ", ".join(r.entry_codes) if r.entry_codes else "(없음)"
        lines.append(f"- **{r.name}** ({r.n_entries}건): {codes}")
    lines.append("")

    lines.append("---")
    lines.append(
        "> 자동 생성 · dry_run · 실거래/모듈 상수 영향 0. "
        "정책 임계는 `review/policy_replay.py` 의 모듈 상수에서만 변경 가능합니다."
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_outputs(
    results: Sequence[PolicyResult],
    samples: Sequence[Sample],
    *,
    target_date: str,
    out_dir: str,
) -> Dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    yyyymmdd = target_date.replace("-", "")
    csv_path = os.path.join(out_dir, f"strategy_policy_comparison_{yyyymmdd}.csv")
    md_path = os.path.join(out_dir, f"strategy_policy_comparison_{yyyymmdd}.md")
    write_csv(results, csv_path)
    write_markdown(results, samples, target_date=target_date, path=md_path)
    return {"csv": csv_path, "markdown": md_path}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m review.policy_replay",
        description="진입 정책 6종을 같은 후보 풀로 dry_run 비교 (실거래 영향 0).",
    )
    parser.add_argument(
        "--date", default=None,
        help="대상 날짜 YYYY-MM-DD (생략 시 학습 CSV 의 마지막 날짜).",
    )
    parser.add_argument(
        "--training-csv", default=TRAINING_CSV_DEFAULT,
        help=f"학습 CSV 경로 (기본 {TRAINING_CSV_DEFAULT}).",
    )
    parser.add_argument(
        "--intraday-dir", default=INTRADAY_DIR_DEFAULT,
        help=f"1분봉 캐시 디렉토리 (기본 {INTRADAY_DIR_DEFAULT}).",
    )
    parser.add_argument(
        "--out-dir", default=REVIEWS_DIR_DEFAULT,
        help=f"산출 디렉토리 (기본 {REVIEWS_DIR_DEFAULT}).",
    )
    return parser.parse_args(argv)


def _print_summary(
    results: Sequence[PolicyResult],
    samples: Sequence[Sample],
    paths: Dict[str, str],
    target_date: str,
) -> None:
    print(f"== policy_replay {target_date} (samples={len(samples)}) ==")
    for r in results:
        m = r.metrics
        print(
            "  [{name:<18}] entries={ne}/{nc} late={lc} fake={fb} win={wr} avg_R={ev}".format(
                name=r.name,
                ne=r.n_entries,
                nc=r.n_candidates,
                lc=_fmt_ratio(m.get("late_chase_ratio")),
                fb=_fmt_ratio(m.get("fake_breakout_ratio")),
                wr=_fmt_ratio(m.get("win_rate")),
                ev=_fmt_r(m.get("expected_value_r")),
            )
        )
    for kind, path in paths.items():
        print(f"  - {kind}: {path}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])
    try:
        samples = load_samples(
            args.training_csv,
            target_date=args.date,
            intraday_dir=args.intraday_dir,
        )
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not samples:
        print("후보 표본이 없습니다. 학습 CSV / 날짜 옵션을 확인하세요.", file=sys.stderr)
        return 2

    target_date = args.date or samples[0].captured_time.strftime("%Y-%m-%d")
    results = [evaluate_policy(p, samples) for p in POLICIES]
    paths = write_outputs(results, samples, target_date=target_date, out_dir=args.out_dir)
    _print_summary(results, samples, paths, target_date)
    return 0


if __name__ == "__main__":
    sys.exit(main())
