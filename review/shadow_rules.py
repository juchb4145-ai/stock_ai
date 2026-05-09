"""shadow 학습 트랙 → rolling 룰 후보(false-negative 기반).

기존 ``review/rules.py`` / ``review/rolling.py`` 는 *진입한 거래의 사후 결과*
(=trade_log + dante_entry_training) 만 보고 임계를 **빡빡하게** 만드는 후보를
낸다. 본 모듈은 그 짝꿍으로, *게이트가 거른 표본* (=dante_shadow_training) 의
사후 결과를 분석해 임계를 **완화** 해야 할 후보를 낸다.

설계 원칙:
  1. 산출물 스키마는 ``review.rolling.RuleCandidate`` 와 100% 호환 — 그대로
     ``rule_candidates_YYYYMMDD.json`` 의 candidates 배열에 합칠 수 있어야 한다.
  2. 자동 적용 후보는 *명시적으로 안전한 매핑* 만 발행한다. 화이트리스트
     (``review.overrides.TARGET_WHITELIST``) 에 등록된 target 이고, 다음 4중
     안전장치를 모두 통과해야 한다:
        - reason_code 별 n ≥ ``MIN_N_FOR_RELEASE``
        - reached_1r% ≥ ``SUSPECT_REACHED_1R_RATIO``
        - hit_stop% ≤ ``MAX_HIT_STOP_FOR_RELEASE`` (게이트가 결국 잘 거른 표본 제외)
        - 매핑된 GATE 가 ``_GATE_RELEASE_MAPPING`` 에 명시적으로 등록
  3. 매핑되지 않은 reason_code 는 RuleCandidate 발행을 하지 않고 ``evidence``
     섹션에만 노출 — 운영자가 검토 후 매핑을 명시적으로 추가하는 흐름.
  4. 같은 target 을 tighten 후보와 동시에 발행하면 ``release_blocked_by_tighten``
     사유로 release 후보가 ``allow_auto_apply=false`` 와 함께 비활성화된다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from training_recorder import (
    DANTE_SHADOW_TRAINING_CSV,
    DANTE_TRAINING_CSV,
)

from .overrides import Override, TARGET_WHITELIST
from .rolling import RuleCandidate
from .shadow_diagnostics import (
    GroupStats,
    ShadowRow,
    _read_entry_rows,
    _read_shadow_rows,
    aggregate_by_reason,
    aggregate_total,
)


# ---------------------------------------------------------------------------
# 트리거/안전 임계
# ---------------------------------------------------------------------------

# RuleCandidate 발행 최소 표본 수.
# shadow_diagnostics 의 MIN_N_FOR_SUSPECT(5) 보다 *높게* 둔다 — 의심 진단(노출용)
# 보다 자동 후보 발행은 한 단계 더 보수적이어야 안전.
MIN_N_FOR_RELEASE = 8

# reason_code 별 reached_1r% 가 이 임계 이상이면 release 후보 트리거.
SUSPECT_REACHED_1R_RATIO = 0.30

# hit_stop% 가 이 임계 이상이면 "게이트가 결국 잘 거른 표본" 으로 보고
# release 후보를 *비활성*. 1R 잠깐 도달 후 손절된 표본은 false-negative 가 아님.
MAX_HIT_STOP_FOR_RELEASE = 0.50


# ---------------------------------------------------------------------------
# GATE → entry_strategy 임계 매핑
# ---------------------------------------------------------------------------
# 매핑은 명시적으로만 활성. 새 reason_code 를 추가하려면 다음 세 가지를 모두
# 검증해야 한다:
#   1) 해당 임계가 ``review.overrides.TARGET_WHITELIST`` 에 등록되어 있는가
#   2) 완화 방향(increment vs decrement) 이 게이트 의미와 일치하는가
#   3) 같은 target 을 tighten 룰이 현재 정책에서 양방향으로 건드리지 않는가
#      (해당 시 PR-A 적용기 단계에서 release 가 자동 비활성화되도록 본 모듈이
#       마킹하지만, 운영자가 미리 알고 있어야 안전)
#
# 시작 매핑은 GATE_UPPER_WICK 만 등록. 현재 데이터에서는 hit_stop=100% 라
# 자동으로 안전장치(MAX_HIT_STOP_FOR_RELEASE) 에 의해 비활성되므로 즉시 후보는
# 발행되지 않는다 — 운영자가 매핑 추가 흐름을 무리 없이 검증할 수 있게 함.
@dataclass(frozen=True)
class _GateRelease:
    target: str        # "entry_strategy.MAX_UPPER_WICK_RATIO" 등 (TARGET_WHITELIST 에 있어야)
    op: str            # "increment" | "decrement"
    by: float          # 1회 완화 폭(매번 같은 값으로만 — 자동 누적 변경 방지)
    direction_label: str   # 사람용 — "완화"|"강화"
    note: str = ""


_GATE_RELEASE_MAPPING: Dict[str, _GateRelease] = {
    "GATE_UPPER_WICK": _GateRelease(
        target="entry_strategy.MAX_UPPER_WICK_RATIO",
        op="increment",   # MAX 가 *상한* 이므로 늘리면 통과 표본 증가 = 완화
        by=0.05,
        direction_label="완화",
        note="윗꼬리 허용 상한을 0.05 늘린다. hard cap 0.80.",
    ),
    "GATE_CHEJAN_SOFT": _GateRelease(
        target="entry_strategy.MIN_CHEJAN_STRENGTH_SOFT",
        op="decrement",   # MIN 이 *하한* 이라 낮추면 통과 표본 증가 = 완화
        by=5.0,
        direction_label="완화",
        note="체결강도 SOFT 하한을 5포인트 낮춘다. hard cap 80.",
    ),
    "GATE_CHEJAN_HARD_NO_TREND": _GateRelease(
        target="entry_strategy.MIN_CHEJAN_STRENGTH_HARD",
        op="decrement",
        by=5.0,
        direction_label="완화",
        note=(
            "체결강도 HARD 하한을 5포인트 낮춘다. hard cap 100 (=현재 SOFT 값) "
            "이라 SOFT 와 동일 또는 그 이하로는 절대 떨어지지 않는다."
        ),
    ),
    "GATE_VOLUME_SPEED": _GateRelease(
        target="entry_strategy.MIN_VOLUME_SPEED",
        op="decrement",
        by=50.0,
        direction_label="완화",
        note="거래속도 하한을 50주/초 낮춘다. hard cap 200 주/초.",
    ),
    "GATE_STAGE2_PULLBACK_SHALLOW": _GateRelease(
        target="entry_strategy.PULLBACK_MIN_PCT",
        op="decrement",
        by=0.001,
        direction_label="완화",
        note=(
            "본진입 최소 눌림 비율을 0.1% 낮춘다. hard cap 0.001 (=0.1%) ~ "
            "0.013 (PULLBACK_MAX_PCT 0.015 와 충돌 회피)."
        ),
    ),
}


# ---------------------------------------------------------------------------
# evidence 산출
# ---------------------------------------------------------------------------


def _ratio(num: int, denom: int) -> Optional[float]:
    return num / denom if denom else None


def build_shadow_evidence(
    *,
    shadow_csv: str = DANTE_SHADOW_TRAINING_CSV,
    entry_csv: str = DANTE_TRAINING_CSV,
) -> Dict[str, object]:
    """rolling_summary 에 끼울 shadow_evidence dict 를 만든다.

    Returns:
        {
          "shadow_n_total": int,           # 전체 누적
          "shadow_n_labeled": int,
          "ready_n_labeled": int,
          "trigger_thresholds": {
              "min_n": MIN_N_FOR_RELEASE,
              "min_reached_1r": SUSPECT_REACHED_1R_RATIO,
              "max_hit_stop": MAX_HIT_STOP_FOR_RELEASE,
          },
          "by_reason": [
              {
                "reason_code": str, "n": int,
                "reached_1r": float, "reached_2r": float,
                "hit_stop": float, "time_exit": float,
                "avg_max_return_25m": float, "avg_min_return_25m": float,
                "decision_status_breakdown": {"wait": int, "blocked": int},
                "is_suspect": bool,
                "is_release_candidate": bool,
                "release_reason_no_apply": str,  # 후보가 안 된 이유
                "mapped_target": Optional[str],
              }, ...
          ],
        }
    """
    shadow_rows: List[ShadowRow]
    entry_rows: List[ShadowRow]
    try:
        shadow_rows, shadow_meta = _read_shadow_rows(shadow_csv)
    except FileNotFoundError:
        shadow_rows, shadow_meta = [], {"n_total": 0, "n_labeled": 0}
    try:
        entry_rows, entry_meta = _read_entry_rows(entry_csv)
    except FileNotFoundError:
        entry_rows, entry_meta = [], {"n_total": 0, "n_labeled": 0}

    by_reason = aggregate_by_reason(shadow_rows)
    total_shadow = aggregate_total(shadow_rows, key="shadow")
    total_entry = aggregate_total(entry_rows, key="ready") if entry_rows else None

    by_reason_payload: List[Dict[str, object]] = []
    for g in by_reason:
        is_suspect = _is_suspect(g)
        candidate_check = _release_candidate_check(g)
        by_reason_payload.append({
            "reason_code": g.key,
            "n": g.n,
            "reached_1r": g.reached_1r_ratio,
            "reached_2r": g.reached_2r_ratio,
            "hit_stop": g.hit_stop_ratio,
            "time_exit": g.time_exit_ratio,
            "avg_max_return_25m": g.avg_max_return_25m,
            "avg_min_return_25m": g.avg_min_return_25m,
            "decision_status_breakdown": dict(g.statuses),
            "is_suspect": is_suspect,
            "is_release_candidate": candidate_check.is_candidate,
            "release_reason_no_apply": candidate_check.reason_no_apply,
            "mapped_target": candidate_check.target,
        })

    return {
        "shadow_n_total": int(shadow_meta.get("n_total", 0)),
        "shadow_n_labeled": int(shadow_meta.get("n_labeled", 0)),
        "ready_n_labeled": int(entry_meta.get("n_labeled", 0)),
        "shadow_overall": _stats_to_dict(total_shadow),
        "ready_overall": _stats_to_dict(total_entry) if total_entry else None,
        "trigger_thresholds": {
            "min_n": MIN_N_FOR_RELEASE,
            "min_reached_1r": SUSPECT_REACHED_1R_RATIO,
            "max_hit_stop": MAX_HIT_STOP_FOR_RELEASE,
        },
        "by_reason": by_reason_payload,
    }


def _stats_to_dict(g: GroupStats) -> Dict[str, object]:
    return {
        "n": g.n,
        "reached_1r": g.reached_1r_ratio,
        "reached_2r": g.reached_2r_ratio,
        "hit_stop": g.hit_stop_ratio,
        "time_exit": g.time_exit_ratio,
        "avg_max_return_25m": g.avg_max_return_25m,
        "avg_min_return_25m": g.avg_min_return_25m,
    }


def _is_suspect(g: GroupStats) -> bool:
    """shadow_diagnostics 의 의심 판정과 동일 임계 (n >= 5, reached_1r >= 30%).

    release 트리거(MIN_N_FOR_RELEASE=8) 보다 느슨해 운영자가 노출된 의심 게이트
    중에서 점진적으로 매핑을 추가하는 흐름을 지원한다.
    """
    if g.n < 5:
        return False
    if g.reached_1r_ratio is None:
        return False
    return g.reached_1r_ratio >= SUSPECT_REACHED_1R_RATIO


# ---------------------------------------------------------------------------
# release candidate 평가
# ---------------------------------------------------------------------------


@dataclass
class _ReleaseCheck:
    is_candidate: bool
    reason_no_apply: str
    target: Optional[str] = None


def _release_candidate_check(g: GroupStats) -> _ReleaseCheck:
    """reason_code 1개에 대해 release 후보 자격 + 비활성 사유를 모두 결정.

    화이트리스트에 매핑된 GATE 라도 통계 임계를 통과하지 못하면 명확한
    reason_no_apply 와 함께 ``is_candidate=False`` 로 반환한다.
    """
    mapping = _GATE_RELEASE_MAPPING.get(g.key)
    if mapping is None:
        return _ReleaseCheck(False, "unmapped_gate")
    if mapping.target not in TARGET_WHITELIST:
        return _ReleaseCheck(False, "target_not_whitelisted", target=mapping.target)
    if g.n < MIN_N_FOR_RELEASE:
        return _ReleaseCheck(False, f"n<{MIN_N_FOR_RELEASE}", target=mapping.target)
    if g.reached_1r_ratio is None:
        return _ReleaseCheck(False, "no_reached_1r_data", target=mapping.target)
    if g.reached_1r_ratio < SUSPECT_REACHED_1R_RATIO:
        return _ReleaseCheck(
            False,
            f"reached_1r<{int(SUSPECT_REACHED_1R_RATIO * 100)}%",
            target=mapping.target,
        )
    if g.hit_stop_ratio is not None and g.hit_stop_ratio > MAX_HIT_STOP_FOR_RELEASE:
        return _ReleaseCheck(
            False,
            f"hit_stop>{int(MAX_HIT_STOP_FOR_RELEASE * 100)}%(게이트가 결국 잘 거름)",
            target=mapping.target,
        )
    return _ReleaseCheck(True, "", target=mapping.target)


def evaluate_release_candidates(
    *,
    shadow_csv: str = DANTE_SHADOW_TRAINING_CSV,
    entry_csv: str = DANTE_TRAINING_CSV,
    windows_to_attribute: Sequence[int] = (5, 10, 20),
    tighten_targets_today: Optional[Sequence[str]] = None,
) -> List[RuleCandidate]:
    """매핑된 GATE 중 안전장치 4중을 모두 통과한 reason_code 만 RuleCandidate 발행.

    Args:
        shadow_csv: shadow 학습 트랙 CSV 경로.
        entry_csv: ready 비교용 (로드되긴 하지만 release 평가에는 직접 쓰지 않음).
        windows_to_attribute: rolling 의 windows 와 동일하게 채워 넣어 결과 JSON
            의 ``triggered_windows`` 가 어색하지 않게 한다(=항상 동일 누적이므로
            모든 윈도우에 동일 evidence 가 붙는다).
        tighten_targets_today: 같은 기준일에 tighten 룰이 *제안한* target 집합.
            release 후보가 같은 target 을 건드리면 ``allow_auto_apply=False`` +
            ``reason_no_apply="release_blocked_by_tighten:<target>"`` 로 비활성.
    """
    shadow_rows, _meta = _read_shadow_rows(shadow_csv)
    by_reason = aggregate_by_reason(shadow_rows)

    tighten_set = set(tighten_targets_today or ())
    out: List[RuleCandidate] = []
    for g in by_reason:
        check = _release_candidate_check(g)
        if not check.is_candidate or check.target is None:
            continue
        mapping = _GATE_RELEASE_MAPPING[g.key]

        # tighten 룰이 같은 target 을 동시에 건드리면 release 는 자동 비활성.
        # 후보 자체는 evidence 노출 목적으로 발행하되, allow_auto_apply=False 로
        # 표시해 PR-A 가 절대 setattr 하지 않게 한다.
        conflict = mapping.target in tighten_set
        reason_no_apply = (
            f"release_blocked_by_tighten:{mapping.target}"
            if conflict
            else "rolling 모듈은 후보만 생성한다 — 적용은 PR-A(dry_run)"
        )

        ev_payload = _stats_to_dict(g)
        # 모든 윈도우에 동일 evidence 부착 — shadow 데이터는 누적이라 윈도우 분할
        # 의미가 없음을 명시적으로 표현(consistent_across_windows=True 자연 충족).
        evidence = {f"{w}d": ev_payload for w in windows_to_attribute}
        evidence["mapping"] = {
            "reason_code": g.key,
            "target": mapping.target,
            "op": mapping.op,
            "by": mapping.by,
            "direction": mapping.direction_label,
            "note": mapping.note,
        }
        evidence["safety_gates"] = {
            "min_n": MIN_N_FOR_RELEASE,
            "min_reached_1r": SUSPECT_REACHED_1R_RATIO,
            "max_hit_stop": MAX_HIT_STOP_FOR_RELEASE,
            "tighten_conflict": conflict,
        }

        override = Override(
            target=mapping.target,
            op=mapping.op,
            by=mapping.by,
            reason=(
                f"shadow {g.key}: n={g.n}, reached_1r="
                f"{(g.reached_1r_ratio or 0) * 100:.1f}%, "
                f"hit_stop={(g.hit_stop_ratio or 0) * 100:.1f}% — "
                f"{mapping.direction_label} 후보"
            ),
        )

        out.append(RuleCandidate(
            rule_id=f"release_overtight_gate__{g.key}",
            title=f"⑥ 게이트 완화 후보 ({g.key})",
            triggered_windows=list(windows_to_attribute),
            confidence="low",   # shadow 기반은 ready 트랙과 직접 비교가 없는 단방향
                                # 시그널이므로 항상 low 로 시작 — 운영자 검토 필수
            n_largest_window=g.n,
            consistent_across_windows=True,   # 누적 단일 평가
            evidence=evidence,
            proposed_overrides=[override],
            auto_apply=False,
            allow_auto_apply=False,
            reason_no_apply=reason_no_apply,
        ))
    return out


# ---------------------------------------------------------------------------
# 디버그/노출 헬퍼
# ---------------------------------------------------------------------------


def list_unmapped_suspects(
    *,
    shadow_csv: str = DANTE_SHADOW_TRAINING_CSV,
) -> List[Tuple[str, GroupStats]]:
    """매핑이 없어 release 후보가 안 된 의심 게이트 목록을 운영자에게 보여주기 위한 헬퍼.

    rolling stdout 요약에 노출 가능. 매핑 추가 후보를 식별하는 흐름을 지원한다.
    """
    if not os.path.exists(shadow_csv):
        return []
    shadow_rows, _meta = _read_shadow_rows(shadow_csv)
    out: List[Tuple[str, GroupStats]] = []
    for g in aggregate_by_reason(shadow_rows):
        if g.key in _GATE_RELEASE_MAPPING:
            continue
        if not _is_suspect(g):
            continue
        out.append((g.key, g))
    return out
