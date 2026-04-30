"""구조화된 룰 오버라이드 스키마 + 화이트리스트 + 검증 + dry_run/commit 적용기.

본 모듈은 단일 책임 원칙으로 *데이터 모델 + 정적 검증* (PR-B) 위에
PR-A 의 *응용 레이어* (load → preview → commit → log) 를 쌓는다.
모듈 이름이 같은 것은 의도된 단일 진입점 — 다른 코드는 절대 별도 경로로
모듈 상수를 변경하지 않는다.

금지 사항(코드 감사 시 다음 토큰들이 본 모듈에 zero match 여야 함):
    - 표현식 평가 함수 호출 (대괄호 없는 ev_al, ex_ec)
    - importlib 의 import_module 호출
    - dunder import 호출
    - 문자열 표현식 평가
    - whitelist 외 target 변경

스키마(JSON)::

    {
      "target": "exit_strategy.EXIT_PARTIAL_R",
      "op": "decrement",
      "by": 0.5,
      "min": 1.0,
      "max": 3.0,
      "reason": "최근 20영업일 기준 빠른 수익 반납 패턴 반복"
    }

지원 op:
    set        : value 필수. 결과 = clip(value, min, max)
    increment  : by   필수. 결과 = clip(current + by, min, max)
    decrement  : by   필수. 결과 = clip(current - by, min, max)
    multiply   : by   필수. 결과 = clip(current * by, min, max)
"""

from __future__ import annotations

import glob
import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

# === 정적 import — 동적 import 금지 정책 준수 ===
# 적용 가능한 모듈은 명시적으로 여기서 import 한다.
# 새 target 모듈을 추가하려면 (1) TARGET_WHITELIST 에 키 추가, (2) 본 import 추가,
# (3) _TARGET_MODULES 매핑 추가 — 이 세 곳을 동시에 손대야 한다(의도된 마찰).
import entry_strategy as _entry_strategy_mod
import exit_strategy as _exit_strategy_mod
from . import classifier as _classifier_mod


_logger = logging.getLogger("kiwoom.overrides")


ALLOWED_OPS = ("set", "increment", "decrement", "multiply")


# --- target whitelist ------------------------------------------------------
# 키:   "<module>.<NAME>" (NAME 은 모듈 최상위 상수만 허용)
# 값:   {"min": ..., "max": ...}
#       PR-A 적용기는 이 범위 안으로 강제 클램프한다. 룰의 min/max 는
#       이 하드 캡과 다시 한 번 교차해 적용 시점에 한 번 더 좁혀진다.
TARGET_WHITELIST: Dict[str, Dict[str, float]] = {
    # entry_strategy
    "entry_strategy.MAX_UPPER_WICK_RATIO":   {"min": 0.10, "max": 0.80},
    "entry_strategy.OVERHEATED_OPEN_RETURN": {"min": 0.03, "max": 0.20},
    "entry_strategy.OVERHEATED_BB55_DISTANCE": {"min": 0.01, "max": 0.10},
    "entry_strategy.DANTE_FIRST_ENTRY_RATIO": {"min": 0.0,  "max": 0.50},
    # exit_strategy
    "exit_strategy.EXIT_BE_R":           {"min": 0.30, "max": 1.50},
    "exit_strategy.EXIT_PARTIAL_R":      {"min": 1.00, "max": 3.50},
    "exit_strategy.EXIT_PARTIAL_RATIO":  {"min": 0.20, "max": 0.80},
    # 신설 예정 — exit_strategy 가 아직 모르면 PR-A 적용기는 skip + warn
    "exit_strategy.TRAIL_HIGHEST_GIVEBACK_R": {"min": 0.30, "max": 1.50},
}


@dataclass
class Override:
    """구조화된 룰 오버라이드 단위.

    적용기는 (target, op, by/value, min, max) 만 사용한다. 그 외 메타는 reason
    같은 사람용 메모.
    """

    target: str
    op: str
    by: Optional[float] = None
    value: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    reason: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        out: Dict[str, Any] = {
            "target": self.target,
            "op": self.op,
            "reason": self.reason,
        }
        if self.value is not None:
            out["value"] = self.value
        if self.by is not None:
            out["by"] = self.by
        if self.min is not None:
            out["min"] = self.min
        if self.max is not None:
            out["max"] = self.max
        if self.extra:
            out["extra"] = self.extra
        return out

    @classmethod
    def from_dict(cls, payload: dict) -> "Override":
        return cls(
            target=str(payload["target"]),
            op=str(payload["op"]),
            by=_opt_float(payload.get("by")),
            value=_opt_float(payload.get("value")),
            min=_opt_float(payload.get("min")),
            max=_opt_float(payload.get("max")),
            reason=str(payload.get("reason") or ""),
            extra=dict(payload.get("extra") or {}),
        )


def _opt_float(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _is_nan(v) -> bool:
    return isinstance(v, float) and v != v


def validate_override(override: Override) -> None:
    """잘못된 override 면 ValueError. PR-A 적용기는 호출 직전 반드시 이 함수를 통과해야 한다.

    검증 항목:
      1) target 이 화이트리스트 안
      2) op 가 ALLOWED_OPS
      3) op 별 필수 필드 존재 (set→value, 그 외→by)
      4) 모든 수치 필드(value/by/min/max) 가 NaN 이 아님 (NaN 통과 시 모듈 상수가
         NaN 으로 오염될 수 있음)
      5) op=set 의 value 가 화이트리스트 hard cap 범위 안 (벗어나면 사전 거부)
      6) min <= max
    """
    if override.target not in TARGET_WHITELIST:
        raise ValueError(f"target 화이트리스트에 없음: {override.target}")
    if override.op not in ALLOWED_OPS:
        raise ValueError(f"허용되지 않은 op: {override.op} (허용: {ALLOWED_OPS})")

    # === NaN 가드(P1 #9) — 모든 수치 필드 검사 ===
    for field_name in ("value", "by", "min", "max"):
        val = getattr(override, field_name)
        if _is_nan(val):
            raise ValueError(f"override.{field_name} 가 NaN 입니다")

    # === op 별 필수 필드 ===
    if override.op == "set":
        if override.value is None:
            raise ValueError("op=set 은 value 가 필요합니다")
    else:
        if override.by is None:
            raise ValueError(f"op={override.op} 은 by 가 필요합니다")

    # === op=set 일 때 hard cap 사전 검증(P1 #9) ===
    # set 은 의도값 그대로 적용을 시도하므로, hard cap 범위 밖이면 사전 거부.
    # increment/decrement/multiply 는 현재값에서 얼마나 변할지 사전에 알 수 없으니
    # apply_override 의 클램프에 위임한다.
    if override.op == "set":
        cap = TARGET_WHITELIST[override.target]
        hard_min = cap.get("min")
        hard_max = cap.get("max")
        v = float(override.value)   # type: ignore[arg-type]
        if hard_min is not None and v < hard_min:
            raise ValueError(
                f"op=set value({v}) 가 hard cap min({hard_min}) 미만 — 거부"
            )
        if hard_max is not None and v > hard_max:
            raise ValueError(
                f"op=set value({v}) 가 hard cap max({hard_max}) 초과 — 거부"
            )

    # min/max sanity
    if override.min is not None and override.max is not None:
        if override.min > override.max:
            raise ValueError(f"min({override.min}) > max({override.max})")


def _clamp(value: float, lo: Optional[float], hi: Optional[float]) -> float:
    if lo is not None:
        value = max(value, lo)
    if hi is not None:
        value = min(value, hi)
    return value


def apply_override(override: Override, current_value: float) -> float:
    """현재 값에 override 를 적용해 새 값을 반환. PR-A 적용기가 사용한다.

    - 룰 자체의 min/max 와 화이트리스트의 하드 캡(min/max)을 모두 적용한다(교집합).
    - 절대 setattr 하지 않는다 — 호출 측이 직접 해야 한다.
    """
    validate_override(override)
    cap = TARGET_WHITELIST[override.target]
    hard_min = cap.get("min")
    hard_max = cap.get("max")
    rule_min = override.min
    rule_max = override.max

    if override.op == "set":
        new_value = float(override.value)  # type: ignore[arg-type]
    elif override.op == "increment":
        new_value = float(current_value) + float(override.by)  # type: ignore[arg-type]
    elif override.op == "decrement":
        new_value = float(current_value) - float(override.by)  # type: ignore[arg-type]
    elif override.op == "multiply":
        new_value = float(current_value) * float(override.by)  # type: ignore[arg-type]
    else:
        raise ValueError(f"unknown op: {override.op}")

    new_value = _clamp(new_value, rule_min, rule_max)
    new_value = _clamp(new_value, hard_min, hard_max)
    return new_value


# =====================================================================
# PR-A 응용 레이어: load → preview → commit → log
# =====================================================================


REVIEW_DIR_DEFAULT = os.path.join("data", "reviews")
MAIN_LOG_DEFAULT = os.path.join("data", "main.log")
DEFAULT_MAX_DAILY_RULE_CHANGES = 3

# target → 정적 import 한 모듈 객체. 동적 import / importlib 사용 금지.
_TARGET_MODULES: Dict[str, Any] = {
    "entry_strategy": _entry_strategy_mod,
    "exit_strategy": _exit_strategy_mod,
    "classifier": _classifier_mod,
}


def _resolve_module_and_attr(target: str) -> Tuple[Any, str]:
    """'<module>.<NAME>' → (module_object, attr_name). 화이트리스트 외 모듈은 거부."""
    if target not in TARGET_WHITELIST:
        raise ValueError(f"target whitelist 에 없음: {target}")
    if "." not in target:
        raise ValueError(f"target 은 'module.NAME' 형식이어야 함: {target}")
    module_part, attr_name = target.split(".", 1)
    module = _TARGET_MODULES.get(module_part)
    if module is None:
        raise ValueError(f"적용 가능한 모듈이 아님(import 누락): {module_part}")
    if not hasattr(module, attr_name):
        raise AttributeError(f"{module_part} 에 {attr_name} 이 없음")
    return module, attr_name


# ---------------------------------------------------------------------------
# 1) load_rule_candidates
# ---------------------------------------------------------------------------


_RULE_CANDIDATES_FILENAME_RE = re.compile(r"rule_candidates_(\d{8})\.json$")
_RULE_OVERRIDES_FILENAME_RE = re.compile(r"rule_overrides_(\d{4}-\d{2}-\d{2})\.json$")


def load_rule_candidates(source_dir: str, date: str) -> dict:
    """주어진 날짜 기준 누적 후보 JSON 을 우선, 없으면 일별 룰 추천 JSON 을 사용.

    Args:
        source_dir: 보통 ``data/reviews``.
        date: ``YYYY-MM-DD`` (필요 시 내부에서 ``YYYYMMDD`` 로 변환).

    Returns:
        {
          "source_file": <절대경로>,
          "schema": "rolling_v1" | "daily_v1" | "unknown",
          "candidates": [ {... 원본 candidate dict ...}, ... ],
        }

    적용 가능한 후보(=`proposed_overrides` 안에 Override 들)는 candidate.proposed_overrides 에서 꺼낸다.
    """
    yyyymmdd = date.replace("-", "")
    rolling_path = os.path.join(source_dir, f"rule_candidates_{yyyymmdd}.json")
    daily_path = os.path.join(source_dir, f"rule_overrides_{date}.json")

    chosen: Optional[str] = None
    if os.path.exists(rolling_path):
        chosen = rolling_path
        schema = "rolling_v1"
    elif os.path.exists(daily_path):
        chosen = daily_path
        schema = "daily_v1"
    else:
        raise FileNotFoundError(
            f"{date} 기준 적용 후보 파일이 없습니다. "
            f"(검색 경로: {rolling_path}, {daily_path})"
        )

    with open(chosen, encoding="utf-8") as f:
        payload = json.load(f)

    candidates = payload.get("candidates")
    if candidates is None:
        # daily(rule_overrides) 형식: proposed_overrides 가 평탄한 리스트
        proposed = payload.get("proposed_overrides") or []
        evidence = {e.get("rule"): e for e in (payload.get("evidence") or [])}
        # 동일 rule_id 별로 묶기
        grouped: Dict[str, dict] = {}
        for ov_dict in proposed:
            rule_id = ov_dict.get("source_rule") or "unknown"
            entry = grouped.setdefault(rule_id, {
                "rule_id": rule_id,
                "title": (evidence.get(rule_id) or {}).get("title", rule_id),
                "confidence": (evidence.get(rule_id) or {}).get("confidence", "low"),
                "consistent_across_windows": False,
                "n_largest_window": 0,
                "proposed_overrides": [],
                "auto_apply": False,
                "allow_auto_apply": False,
            })
            entry["proposed_overrides"].append(ov_dict)
        candidates = list(grouped.values())

    return {"source_file": chosen, "schema": schema, "candidates": candidates}


# ---------------------------------------------------------------------------
# 2) preview_overrides
# ---------------------------------------------------------------------------


def _rule_hash(rule_id: str, ov_dict: dict) -> str:
    """동일 룰+동일 override 내용에 대해 안정적인 해시. 감사 로그 / dedup 용."""
    payload = json.dumps({"rule_id": rule_id, "ov": ov_dict}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


_CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}


def _is_numeric(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def preview_overrides(
    payload: dict,
    *,
    mode: str = "dry_run",
    max_daily_rule_changes: int = DEFAULT_MAX_DAILY_RULE_CHANGES,
) -> List[dict]:
    """후보 → preview entry 리스트.

    각 entry 는 감사 로그용 13개 필드를 모두 포함. 이 함수는 절대 setattr 하지 않는다.

    skipped_reason 종류:
      - "" (=빈 문자열, 건너뛰지 않음)
      - "confidence_below_high"
      - "not_approved"            (allow_auto_apply == false)
      - "validation_failed"
      - "type_mismatch"
      - "no_change"               (new_value == old_value)
      - "exceeded_daily_limit"
    """
    if mode not in ("dry_run", "commit"):
        raise ValueError(f"mode 는 dry_run|commit 중 하나여야 함: {mode}")

    classifier_version = getattr(_classifier_mod, "CLASSIFIER_VERSION", "")

    # 1단계: 모든 (candidate × proposed_override) 조합을 평면화 + 검증
    flat: List[dict] = []
    for cand in payload.get("candidates", []):
        confidence = (cand.get("confidence") or "low").lower()
        allow_auto_apply = bool(cand.get("allow_auto_apply", False))
        rule_id = cand.get("rule_id", "")
        consistent = bool(cand.get("consistent_across_windows", False))
        n_largest = int(cand.get("n_largest_window", 0))
        for ov_dict in cand.get("proposed_overrides", []):
            entry = _build_preview_entry(
                ov_dict=ov_dict,
                rule_id=rule_id,
                confidence=confidence,
                allow_auto_apply=allow_auto_apply,
                mode=mode,
                consistent=consistent,
                n_largest=n_largest,
                classifier_version=classifier_version,
            )
            flat.append(entry)

    # 2단계: 일일 변경 한도 적용. dry_run 에서도 동일하게 평가해 audit 가
    # commit 단계 결과를 정확히 시뮬레이션하도록 한다(운영자 예측 가능성).
    # 정렬: confidence desc → consistent → n_largest desc.
    eligible = [e for e in flat if not e["skipped_reason"]]
    eligible.sort(key=lambda e: (
        -_CONFIDENCE_RANK.get(e["confidence"], -1),
        -1 if e["_consistent"] else 0,
        -e["_n_largest"],
    ))
    for e in eligible[max_daily_rule_changes:]:
        e["skipped_reason"] = "exceeded_daily_limit"
        e["applied"] = False

    # 내부용 키 정리
    for e in flat:
        e.pop("_consistent", None)
        e.pop("_n_largest", None)

    return flat


def _build_preview_entry(
    *,
    ov_dict: dict,
    rule_id: str,
    confidence: str,
    allow_auto_apply: bool,
    mode: str,
    consistent: bool,
    n_largest: int,
    classifier_version: str,
) -> dict:
    """개별 override → preview entry. setattr 안 함. 모든 검증/계산을 try/except 로 감싼다."""
    entry: Dict[str, Any] = {
        "target": ov_dict.get("target", ""),
        "op": ov_dict.get("op", ""),
        "old_value": None,
        "new_value": None,
        "confidence": confidence,
        "allow_auto_apply": allow_auto_apply,
        "reason": ov_dict.get("reason", ""),
        "validation_status": "pending",
        "skipped_reason": "",
        "applied": False,
        "rule_hash": _rule_hash(rule_id, ov_dict),
        "source_rule": rule_id,
        "classifier_version_before": classifier_version,
        "classifier_version_after": classifier_version,
        # 정렬용 내부 키(반환 직전 제거)
        "_consistent": consistent,
        "_n_largest": n_largest,
    }
    try:
        ov = Override.from_dict(ov_dict)
        validate_override(ov)
        module, attr_name = _resolve_module_and_attr(ov.target)
        old_value = getattr(module, attr_name)
        if not _is_numeric(old_value):
            entry["validation_status"] = "failed"
            entry["skipped_reason"] = "type_mismatch"
            entry["old_value"] = old_value
            return entry
        new_value = apply_override(ov, float(old_value))
        if not _is_numeric(new_value):
            entry["validation_status"] = "failed"
            entry["skipped_reason"] = "type_mismatch"
            entry["old_value"] = old_value
            return entry
        # 원본 타입 유지 (int 면 int, float 면 float)
        if isinstance(old_value, int):
            new_value = int(round(new_value))
        else:
            new_value = float(new_value)
        entry["old_value"] = old_value
        entry["new_value"] = new_value
        entry["validation_status"] = "ok"

        if new_value == old_value:
            entry["skipped_reason"] = "no_change"
            return entry

        # 적용 자격: confidence==high AND allow_auto_apply==true
        if mode == "commit":
            if confidence != "high":
                entry["skipped_reason"] = "confidence_below_high"
            elif not allow_auto_apply:
                entry["skipped_reason"] = "not_approved"
    except (ValueError, AttributeError, TypeError) as exc:
        entry["validation_status"] = "failed"
        entry["skipped_reason"] = "validation_failed"
        entry["reason"] = entry.get("reason", "") + f" | error={exc}"
    return entry


# ---------------------------------------------------------------------------
# 3) commit_overrides
# ---------------------------------------------------------------------------


def commit_overrides(
    preview_entries: List[dict],
    *,
    mode: str,
    fixture_hook: Optional[Callable[[], bool]] = None,
) -> List[dict]:
    """preview entries 중 적용 가능한 것만 setattr.

    fixture_hook 이 False 를 반환하면 같은 batch 내 모든 setattr 를 rollback 하고
    해당 entry 들을 ``applied=false, skipped_reason="fixture_failed"`` 로 마킹.

    mode == "dry_run" 일 때는 setattr 를 일절 호출하지 않고 ``applied=false`` 만 마킹.

    안전성 — preview_entries 가 외부에서 조작/오용된 경우에도 다음 두 게이트를
    *함수 시그니처 차원* 에서 한 번 더 적용한다(2단계 방어).
        - confidence == "high" 만 적용
        - allow_auto_apply 가 entry 에 명시적으로 true 일 때만 적용
    """
    if mode not in ("dry_run", "commit"):
        raise ValueError(f"mode 는 dry_run|commit 중 하나여야 함: {mode}")

    if mode == "dry_run":
        for e in preview_entries:
            e["applied"] = False
        return preview_entries

    rollback_stack: List[Tuple[Any, str, Any]] = []   # (module, attr, old_value)
    committed_entries: List[dict] = []
    for entry in preview_entries:
        if entry["skipped_reason"]:
            continue
        if entry["validation_status"] != "ok":
            continue
        # === 2단계 방어 — preview 와 중복이지만 합법 ===
        # preview 가 mode="dry_run" 으로 만든 entry 를 mode="commit" 으로 commit 시도하는
        # 경로를 막기 위해 confidence/approval 을 commit 시점에 한 번 더 검증한다.
        if entry.get("confidence") != "high":
            entry["skipped_reason"] = "confidence_below_high"
            continue
        if not entry.get("allow_auto_apply"):
            entry["skipped_reason"] = "not_approved"
            continue
        try:
            module, attr_name = _resolve_module_and_attr(entry["target"])
            old_value = getattr(module, attr_name)
            setattr(module, attr_name, entry["new_value"])
            rollback_stack.append((module, attr_name, old_value))
            entry["applied"] = True
            committed_entries.append(entry)
        except (ValueError, AttributeError, TypeError) as exc:
            entry["applied"] = False
            entry["skipped_reason"] = "validation_failed"
            entry["reason"] = entry.get("reason", "") + f" | commit_error={exc}"

    if fixture_hook is not None and committed_entries:
        try:
            ok = bool(fixture_hook())
        except Exception as exc:  # noqa: BLE001 — fixture_hook 의 어떤 예외도 rollback 트리거
            ok = False
            _logger.error("[OVERRIDE] fixture_hook 예외 — rollback: %s", exc)
        if not ok:
            # === rollback 단계화 (P1 #8) ===
            # 어떤 항목이 정확히 원복됐고, 어떤 항목은 rollback 자체가 실패해서
            # 부분 변경 상태로 남았는지 entry 별로 정확히 마킹한다.
            # rollback_stack 의 각 항목과 committed_entries 가 push 순서와 동일
            # 인덱스로 대응하므로, reversed 순회 시 (idx 도 역순) committed_entry
            # 한 건씩 결과를 정확히 매칭할 수 있다.
            rollback_failed_targets: List[str] = []
            for module, attr_name, old_value in reversed(rollback_stack):
                try:
                    setattr(module, attr_name, old_value)
                except Exception as exc:  # noqa: BLE001
                    target_str = f"{module.__name__}.{attr_name}"
                    rollback_failed_targets.append(target_str)
                    _logger.error("[OVERRIDE] rollback 실패 %s: %s — 부분 변경 상태",
                                  target_str, exc)
            for e in committed_entries:
                e["applied"] = False
                # rollback 실패한 entry 는 별도 사유로 마킹 → 운영자가 즉시 인지
                if e["target"] in rollback_failed_targets:
                    e["skipped_reason"] = "rollback_failed"
                else:
                    e["skipped_reason"] = "fixture_failed"
            if rollback_failed_targets:
                _logger.error(
                    "[OVERRIDE][SUMMARY] rollback 부분 실패 %d건 — 모듈 상태 점검 필요: %s",
                    len(rollback_failed_targets), ",".join(rollback_failed_targets),
                )

    return preview_entries


# ---------------------------------------------------------------------------
# 4) write_applied_overrides_log
# ---------------------------------------------------------------------------


_AUDIT_FIELDS = (
    "date", "mode", "source_file",
    "target", "old_value", "new_value", "op",
    "confidence", "reason",
    "validation_status", "skipped_reason", "applied",
    "rule_hash", "source_rule",
    "classifier_version_before", "classifier_version_after",
)


def write_applied_overrides_log(
    entries: List[dict],
    *,
    date: str,
    mode: str,
    source_file: str,
    log_dir: str = REVIEW_DIR_DEFAULT,
) -> str:
    """applied_overrides_YYYYMMDD.json 출력 + main.log 한 줄 요약.

    Returns: 작성된 JSON 파일 경로.
    """
    os.makedirs(log_dir, exist_ok=True)
    yyyymmdd = date.replace("-", "")
    out_path = os.path.join(log_dir, f"applied_overrides_{yyyymmdd}.json")

    audit_entries: List[dict] = []
    for e in entries:
        audit = {k: e.get(k) for k in _AUDIT_FIELDS if k in e or k in ("date", "mode", "source_file")}
        audit["date"] = date
        audit["mode"] = mode
        audit["source_file"] = source_file
        # 누락 필드 채우기
        for k in _AUDIT_FIELDS:
            audit.setdefault(k, None if k not in ("applied",) else False)
        audit_entries.append(audit)

    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "date": date,
        "mode": mode,
        "source_file": source_file,
        "schema": "applied_overrides_v1",
        "entries": audit_entries,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=_json_default)

    # main.log 한 줄 요약 — root logger 가 main.py 의 file handler 를 들고 있으면 자동 기록.
    mode_tag = "[DRY_RUN]" if mode == "dry_run" else "[COMMIT]"
    for e in entries:
        _logger.info(
            "[OVERRIDE]%s target=%s old=%s new=%s confidence=%s applied=%s%s",
            mode_tag,
            e.get("target", ""),
            e.get("old_value"),
            e.get("new_value"),
            e.get("confidence"),
            "true" if e.get("applied") else "false",
            f" skipped={e['skipped_reason']}" if e.get("skipped_reason") else "",
        )
    return out_path


def _json_default(obj):
    if isinstance(obj, float):
        if obj != obj:   # NaN
            return None
    raise TypeError(f"unserializable: {type(obj).__name__}")


# ---------------------------------------------------------------------------
# 5) load_and_apply_overrides — main hook
# ---------------------------------------------------------------------------


def load_and_apply_overrides(
    date: str,
    *,
    mode: str = "dry_run",
    source_dir: str = REVIEW_DIR_DEFAULT,
    log_dir: str = REVIEW_DIR_DEFAULT,
    max_daily_rule_changes: int = DEFAULT_MAX_DAILY_RULE_CHANGES,
    fixture_hook: Optional[Callable[[], bool]] = None,
) -> dict:
    """전체 파이프라인 main hook.

    main.py 부팅 시 다음과 같이 호출하면 된다::

        load_and_apply_overrides(date=target_date, mode="dry_run")
        # 또는
        load_and_apply_overrides(date=target_date, mode="commit",
                                  fixture_hook=run_fixture_tests)

    --commit 이 없으면 어떤 경우에도 setattr 가 일어나지 않는다.

    Returns:
        {
          "date": ..., "mode": ..., "source_file": ...,
          "applied_count": int, "skipped_count": int,
          "entries": [...], "audit_log_path": str,
        }
    """
    payload = load_rule_candidates(source_dir, date)
    preview = preview_overrides(
        payload, mode=mode, max_daily_rule_changes=max_daily_rule_changes,
    )
    final = commit_overrides(preview, mode=mode, fixture_hook=fixture_hook)
    log_path = write_applied_overrides_log(
        final, date=date, mode=mode, source_file=payload["source_file"], log_dir=log_dir,
    )

    applied = sum(1 for e in final if e.get("applied"))
    skipped = sum(1 for e in final if e.get("skipped_reason"))
    _logger.info(
        "[OVERRIDE][SUMMARY] date=%s mode=%s applied=%d skipped=%d total=%d source=%s",
        date, mode, applied, skipped, len(final), payload["source_file"],
    )
    return {
        "date": date,
        "mode": mode,
        "source_file": payload["source_file"],
        "applied_count": applied,
        "skipped_count": skipped,
        "entries": final,
        "audit_log_path": log_path,
    }
