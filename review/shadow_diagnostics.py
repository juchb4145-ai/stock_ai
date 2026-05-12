"""Shadow 학습 트랙 진단 (false-negative 측정).

``data/dante_shadow_training.csv`` 에 누적된 wait/blocked 표본을
``reason_code`` 단위로 잘라 25분 후 라벨(reached_1r/reached_2r/hit_stop/
time_exit, max/min_return_25m) 의 분포를 본다. 진입한 ready 표본
(``data/dante_entry_training.csv``) 과 같은 라벨 척도로 비교해
"게이트가 거른 표본이 실제로 안 갔는지(true-negative)" vs "갔는데
거른 건지(false-negative)" 를 한 장 표로 진단한다.

본 모듈은 ``entry_strategy`` / ``exit_strategy`` 의 어떤 상수도
수정하지 않는다. 출력은 stdout 요약 + 다음 마크다운 리포트:

    data/reviews/shadow_diagnostics_YYYYMMDD.md

CLI:
    python -m review.shadow_diagnostics
    python -m review.shadow_diagnostics --date 2026-05-04
    python -m review.shadow_diagnostics --shadow-csv data/dante_shadow_training.csv

헤더 호환성:
    옛날 ``dante_shadow_training.csv`` 는 ``reason_code`` 컬럼이 헤더에
    빠진 채로 만들어진 경우가 있다(``training_recorder.py`` 가 fields 를
    확장한 뒤로 헤더만 그대로 남음). ``_read_shadow_rows`` 가 이를
    자동 감지해 ``DANTE_SHADOW_TRAINING_FIELDS`` 정의를 fallback 으로
    삼아 컬럼명을 보정한다. ``--migrate-header`` 옵션으로 백업 후
    헤더 첫 줄만 표준 fields 로 다시 써둘 수 있다.
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from training_recorder import (
    DANTE_SHADOW_TRAINING_CSV,
    DANTE_SHADOW_TRAINING_FIELDS,
    DANTE_TRAINING_CSV,
    DANTE_TRAINING_FIELDS,
)


SHADOW_CSV_DEFAULT = DANTE_SHADOW_TRAINING_CSV
ENTRY_CSV_DEFAULT = DANTE_TRAINING_CSV
REVIEWS_DIR_DEFAULT = os.path.join("data", "reviews")

# reason_code 별 reached_1r% 가 이 임계 이상이면 "게이트 의심" flag.
# (ready 표본의 reached_1r% 와 별개의 절대 기준 — n 이 작을 때 ready 비교가
#  의미 없을 수 있어 절대 임계도 같이 둔다.)
SUSPECT_REACHED_1R_RATIO = 0.30
# reason_code 별 표본이 이 미만이면 "n 부족" 으로 의심 판정 보류.
MIN_N_FOR_SUSPECT = 5


# ---------------------------------------------------------------------------
# 데이터 모델
# ---------------------------------------------------------------------------


@dataclass
class ShadowRow:
    decision_status: str  # "wait" | "blocked"
    reason_code: str
    captured_time: Optional[datetime]
    code: str
    name: str
    entry_stage: int
    # 25분 라벨 (모두 옵셔널 — 라벨링 진행 중인 표본은 비어 있다)
    reached_1r: Optional[int]
    reached_2r: Optional[int]
    hit_stop: Optional[int]
    time_exit: Optional[int]
    max_return_25m: Optional[float]
    min_return_25m: Optional[float]
    return_5m: Optional[float]
    return_10m: Optional[float]
    return_20m: Optional[float]

    @property
    def is_labeled(self) -> bool:
        # 25분 horizon 까지 도달해 라벨 4종이 모두 채워진 행만 통계에 포함.
        return all(
            v is not None
            for v in (self.reached_1r, self.reached_2r, self.hit_stop, self.time_exit)
        )


@dataclass
class GroupStats:
    """reason_code 1개에 대한 25분 사후 라벨 분포."""

    key: str
    n: int = 0
    n_reached_1r: int = 0
    n_reached_2r: int = 0
    n_hit_stop: int = 0
    n_time_exit: int = 0
    sum_max_return_25m: float = 0.0
    sum_min_return_25m: float = 0.0
    n_with_max_min: int = 0
    statuses: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def add(self, row: ShadowRow) -> None:
        self.n += 1
        self.statuses[row.decision_status] += 1
        if row.reached_1r:
            self.n_reached_1r += 1
        if row.reached_2r:
            self.n_reached_2r += 1
        if row.hit_stop:
            self.n_hit_stop += 1
        if row.time_exit:
            self.n_time_exit += 1
        if row.max_return_25m is not None and row.min_return_25m is not None:
            self.sum_max_return_25m += row.max_return_25m
            self.sum_min_return_25m += row.min_return_25m
            self.n_with_max_min += 1

    def _ratio(self, num: int) -> Optional[float]:
        return num / self.n if self.n else None

    @property
    def reached_1r_ratio(self) -> Optional[float]:
        return self._ratio(self.n_reached_1r)

    @property
    def reached_2r_ratio(self) -> Optional[float]:
        return self._ratio(self.n_reached_2r)

    @property
    def hit_stop_ratio(self) -> Optional[float]:
        return self._ratio(self.n_hit_stop)

    @property
    def time_exit_ratio(self) -> Optional[float]:
        return self._ratio(self.n_time_exit)

    @property
    def avg_max_return_25m(self) -> Optional[float]:
        return (
            self.sum_max_return_25m / self.n_with_max_min
            if self.n_with_max_min
            else None
        )

    @property
    def avg_min_return_25m(self) -> Optional[float]:
        return (
            self.sum_min_return_25m / self.n_with_max_min
            if self.n_with_max_min
            else None
        )

    @property
    def status_breakdown(self) -> str:
        if not self.statuses:
            return ""
        ordered = sorted(self.statuses.items(), key=lambda x: (-x[1], x[0]))
        return " / ".join(f"{k}:{v}" for k, v in ordered)


# ---------------------------------------------------------------------------
# CSV 로더 (헤더 mismatch 자동 보정)
# ---------------------------------------------------------------------------


def _detect_header_mismatch(
    actual: Sequence[str], expected: Sequence[str]
) -> Optional[List[str]]:
    """헤더가 표준 fields 와 다르면 보정된 fields 를 반환, 같으면 None."""
    if list(actual) == list(expected):
        return None
    # 옛 헤더가 expected 의 부분집합(앞쪽 컬럼 누락) 이고 컬럼 개수만 차이나는
    # 흔한 케이스를 가정해 expected 그대로를 사용.
    if len(expected) >= len(actual):
        return list(expected)
    return None


def _to_int(value) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _to_float(value) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_captured_time(raw: str) -> Optional[datetime]:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _read_shadow_rows(path: str) -> Tuple[List[ShadowRow], Dict[str, object]]:
    """shadow CSV 를 읽어 ShadowRow 리스트와 메타(헤더 상태) 를 반환."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"shadow CSV 가 없습니다: {path}")
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [], {"path": path, "header_ok": True, "n_total": 0, "n_labeled": 0}
        body = [r for r in reader]

    expected = list(DANTE_SHADOW_TRAINING_FIELDS)
    corrected = _detect_header_mismatch(header, expected)
    fields = corrected if corrected is not None else list(header)
    header_ok = corrected is None

    rows: List[ShadowRow] = []
    for raw in body:
        if not raw:
            continue
        # 헤더보다 칸이 많으면 표준 fields 길이로 잘라 매핑(끝쪽 trailing 제거).
        sliced = raw[: len(fields)]
        if len(sliced) < len(fields):
            sliced = sliced + [""] * (len(fields) - len(sliced))
        record = dict(zip(fields, sliced))
        rows.append(
            ShadowRow(
                decision_status=record.get("decision_status", "") or "",
                reason_code=record.get("reason_code", "") or "",
                captured_time=_parse_captured_time(
                    record.get("captured_time", "") or ""
                ),
                code=record.get("code", "") or "",
                name=record.get("name", "") or "",
                entry_stage=_to_int(record.get("entry_stage")) or 0,
                reached_1r=_to_int(record.get("reached_1r")),
                reached_2r=_to_int(record.get("reached_2r")),
                hit_stop=_to_int(record.get("hit_stop")),
                time_exit=_to_int(record.get("time_exit")),
                max_return_25m=_to_float(record.get("max_return_25m")),
                min_return_25m=_to_float(record.get("min_return_25m")),
                return_5m=_to_float(record.get("return_5m")),
                return_10m=_to_float(record.get("return_10m")),
                return_20m=_to_float(record.get("return_20m")),
            )
        )

    n_labeled = sum(1 for r in rows if r.is_labeled)
    meta = {
        "path": path,
        "header_ok": header_ok,
        "header_actual": list(header),
        "header_used": fields,
        "n_total": len(rows),
        "n_labeled": n_labeled,
    }
    return rows, meta


def _read_entry_rows(path: str) -> Tuple[List[ShadowRow], Dict[str, object]]:
    """ready 표본도 같은 ShadowRow 모양으로 읽는다 (decision_status='ready' 고정)."""
    if not os.path.exists(path):
        return [], {"path": path, "exists": False, "n_total": 0, "n_labeled": 0}
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows: List[ShadowRow] = []
        for record in reader:
            rows.append(
                ShadowRow(
                    decision_status="ready",
                    reason_code="(ready)",
                    captured_time=_parse_captured_time(
                        record.get("captured_time", "") or ""
                    ),
                    code=record.get("code", "") or "",
                    name=record.get("name", "") or "",
                    entry_stage=_to_int(record.get("entry_stage")) or 0,
                    reached_1r=_to_int(record.get("reached_1r")),
                    reached_2r=_to_int(record.get("reached_2r")),
                    hit_stop=_to_int(record.get("hit_stop")),
                    time_exit=_to_int(record.get("time_exit")),
                    max_return_25m=_to_float(record.get("max_return_25m")),
                    min_return_25m=_to_float(record.get("min_return_25m")),
                    return_5m=_to_float(record.get("return_5m")),
                    return_10m=_to_float(record.get("return_10m")),
                    return_20m=_to_float(record.get("return_20m")),
                )
            )
    n_labeled = sum(1 for r in rows if r.is_labeled)
    return rows, {
        "path": path,
        "exists": True,
        "n_total": len(rows),
        "n_labeled": n_labeled,
    }


# ---------------------------------------------------------------------------
# 헤더 마이그레이션 (선택)
# ---------------------------------------------------------------------------


def migrate_shadow_header(path: str) -> Dict[str, object]:
    """헤더가 표준 fields 와 다르면 백업 후 헤더만 다시 쓴다.

    데이터 본문은 그대로 두고, 첫 줄만 ``DANTE_SHADOW_TRAINING_FIELDS`` 로
    교체. 옛 헤더 그대로의 컬럼 순서가 새 fields 와 일치하지 않으면 본문이
    뒤틀릴 수 있으므로, 본 함수는 "옛 헤더 + 본문이 새 fields 순서로 이미
    저장돼 있는" 케이스(현재 dante_shadow_training.csv 의 상황) 만 안전한
    교체로 본다. 그 외 케이스는 변경 없이 reason 만 반환한다.
    """
    if not os.path.exists(path):
        return {"changed": False, "reason": "파일 없음"}
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        lines = f.readlines()
    if not lines:
        return {"changed": False, "reason": "빈 파일"}
    header = next(csv.reader([lines[0]]))
    expected = list(DANTE_SHADOW_TRAINING_FIELDS)
    if header == expected:
        return {"changed": False, "reason": "이미 표준 헤더"}
    # 안전 가드: 본문 첫 행 컬럼 수 == len(expected) 인지 확인.
    body_first_cells = next(csv.reader([lines[1]])) if len(lines) > 1 else []
    if body_first_cells and len(body_first_cells) != len(expected):
        return {
            "changed": False,
            "reason": f"본문 첫 행 컬럼 수({len(body_first_cells)}) 가 표준 fields({len(expected)}) 와 달라 자동 마이그레이션 거부",
        }
    backup = path + ".bak"
    shutil.copyfile(path, backup)
    new_header_line = ",".join(expected) + "\n"
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(new_header_line)
        if len(lines) > 1:
            f.writelines(lines[1:])
    return {
        "changed": True,
        "backup": backup,
        "old_header": header,
        "new_header": expected,
    }


# ---------------------------------------------------------------------------
# 집계
# ---------------------------------------------------------------------------


def _filter_by_date(
    rows: Iterable[ShadowRow], target_date: Optional[str]
) -> List[ShadowRow]:
    if target_date is None:
        return list(rows)
    return [
        r
        for r in rows
        if r.captured_time is not None
        and r.captured_time.strftime("%Y-%m-%d") == target_date
    ]


def aggregate_by_reason(rows: Iterable[ShadowRow]) -> List[GroupStats]:
    buckets: Dict[str, GroupStats] = {}
    for r in rows:
        if not r.is_labeled:
            continue
        key = r.reason_code or "(empty)"
        buckets.setdefault(key, GroupStats(key=key)).add(r)
    return sorted(buckets.values(), key=lambda g: (-g.n, g.key))


def aggregate_total(rows: Iterable[ShadowRow], key: str) -> GroupStats:
    g = GroupStats(key=key)
    for r in rows:
        if not r.is_labeled:
            continue
        g.add(r)
    return g


# ---------------------------------------------------------------------------
# 출력
# ---------------------------------------------------------------------------


def _fmt_pct(value: Optional[float], digits: int = 1) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.{digits}f}%"


def _fmt_signed_pct(value: Optional[float], digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:+.{digits}f}%"


def _suspect_flag(g: GroupStats) -> str:
    if g.n < MIN_N_FOR_SUSPECT:
        return ""
    if g.reached_1r_ratio is None:
        return ""
    if g.reached_1r_ratio >= SUSPECT_REACHED_1R_RATIO:
        return "[검토]"
    return ""


def _markdown_lines(
    *,
    target_label: str,
    shadow_meta: Dict[str, object],
    entry_meta: Dict[str, object],
    total_shadow: GroupStats,
    total_entry: Optional[GroupStats],
    by_reason: Sequence[GroupStats],
) -> List[str]:
    lines: List[str] = []
    lines.append(f"# {target_label} shadow 진단 (false-negative 측정)")
    lines.append("")
    lines.append(
        f"- shadow CSV: `{shadow_meta['path']}` — 총 {shadow_meta['n_total']}건 / "
        f"라벨링 완료 {shadow_meta['n_labeled']}건"
    )
    if not shadow_meta.get("header_ok", True):
        lines.append(
            "- ⚠️ shadow CSV 헤더에 누락된 컬럼이 감지됨 — `DANTE_SHADOW_TRAINING_FIELDS` 정의를 fallback 으로 보정해 읽었습니다. "
            "`python -m review.shadow_diagnostics --migrate-header` 로 헤더 첫 줄만 안전하게 교체할 수 있습니다."
        )
    if entry_meta.get("exists"):
        lines.append(
            f"- entry CSV: `{entry_meta['path']}` — 총 {entry_meta['n_total']}건 / "
            f"라벨링 완료 {entry_meta['n_labeled']}건"
        )
    else:
        lines.append(
            f"- entry CSV: `{entry_meta['path']}` 없음 (ready 비교 행은 생략)"
        )
    lines.append(
        f"- 라벨링 완료(=25분 horizon 도달) 표본만 통계에 포함합니다. "
        f"reason_code 별 n ≥ {MIN_N_FOR_SUSPECT} & reached_1r ≥ "
        f"{int(SUSPECT_REACHED_1R_RATIO * 100)}% 일 때 [검토] 마크."
    )
    lines.append("")

    lines.append("## 요약 — 트랙별 25분 라벨 비교")
    lines.append("")
    lines.append(
        "| 트랙 | n | reached_1r% | reached_2r% | hit_stop% | time_exit% | "
        "avg max_25m | avg min_25m | status 분포 |"
    )
    lines.append(
        "|------|--:|------------:|------------:|----------:|-----------:|"
        "------------:|------------:|--------------|"
    )

    def _row(label: str, g: GroupStats) -> str:
        return (
            f"| {label} | {g.n} | {_fmt_pct(g.reached_1r_ratio)} | "
            f"{_fmt_pct(g.reached_2r_ratio)} | {_fmt_pct(g.hit_stop_ratio)} | "
            f"{_fmt_pct(g.time_exit_ratio)} | "
            f"{_fmt_signed_pct(g.avg_max_return_25m)} | "
            f"{_fmt_signed_pct(g.avg_min_return_25m)} | "
            f"{g.status_breakdown or '-'} |"
        )

    if total_entry is not None and total_entry.n > 0:
        lines.append(_row("ready (entry CSV)", total_entry))
    lines.append(_row("shadow (wait+blocked)", total_shadow))
    lines.append("")

    lines.append("## reason_code 별 사후 결과 — 게이트 의심 순")
    lines.append("")
    if not by_reason:
        lines.append("> 라벨링 완료된 shadow 표본이 없습니다.")
        lines.append("")
        return lines

    lines.append(
        "| reason_code | n | reached_1r% | reached_2r% | hit_stop% | time_exit% | "
        "avg max_25m | avg min_25m | status | flag |"
    )
    lines.append(
        "|-------------|--:|------------:|------------:|----------:|-----------:|"
        "------------:|------------:|--------|------|"
    )
    # reached_1r_ratio 내림차순(=의심 큰 것 먼저), 같으면 n 큰 것 먼저.
    ranked = sorted(
        by_reason,
        key=lambda g: (
            -(g.reached_1r_ratio if g.reached_1r_ratio is not None else 0.0),
            -g.n,
            g.key,
        ),
    )
    for g in ranked:
        lines.append(
            f"| {g.key} | {g.n} | {_fmt_pct(g.reached_1r_ratio)} | "
            f"{_fmt_pct(g.reached_2r_ratio)} | {_fmt_pct(g.hit_stop_ratio)} | "
            f"{_fmt_pct(g.time_exit_ratio)} | "
            f"{_fmt_signed_pct(g.avg_max_return_25m)} | "
            f"{_fmt_signed_pct(g.avg_min_return_25m)} | "
            f"{g.status_breakdown or '-'} | {_suspect_flag(g) or '-'} |"
        )
    lines.append("")

    lines.append("## 해석 가이드")
    lines.append("")
    lines.append(
        "- **reached_1r% 가 낮을수록** 게이트가 잘 거른 것 (true-negative). "
        "0~10% 면 그 reason_code 는 안전한 거절 사유입니다."
    )
    lines.append(
        "- **reached_1r% 가 ready 트랙과 비슷하거나 그 이상** 이라면 게이트가 "
        "수익날 표본까지 거부 중일 가능성 (false-negative). 해당 게이트의 "
        "임계 완화를 검토하세요."
    )
    lines.append(
        "- **n 이 작을수록** 통계 신뢰도가 낮습니다. n ≥ 5 까지 누적된 "
        "reason_code 만 [검토] 플래그를 부여합니다."
    )
    lines.append(
        "- 본 모듈은 진단만 합니다. 실제 임계 조정은 `review.rules` 또는 "
        "PR-A(dry_run) 적용기에서 수행하세요."
    )
    lines.append("")
    lines.append("---")
    lines.append("> 자동 생성 · 진단 전용 · 실거래/모듈 상수 영향 0.")
    return lines


def _print_summary(
    *,
    target_label: str,
    shadow_meta: Dict[str, object],
    entry_meta: Dict[str, object],
    total_shadow: GroupStats,
    total_entry: Optional[GroupStats],
    by_reason: Sequence[GroupStats],
    md_path: Optional[str],
) -> None:
    print(f"== shadow_diagnostics {target_label} ==")
    print(
        f"  shadow: {shadow_meta['n_total']} (labeled {shadow_meta['n_labeled']})"
        f"   entry: {entry_meta.get('n_total', 0)} (labeled {entry_meta.get('n_labeled', 0)})"
    )
    if not shadow_meta.get("header_ok", True):
        print("  [WARN] shadow CSV 헤더에 누락 컬럼 - fallback 으로 보정해 읽었습니다.")
    if total_entry is not None and total_entry.n > 0:
        print(
            f"  ready : n={total_entry.n} 1R={_fmt_pct(total_entry.reached_1r_ratio)} "
            f"2R={_fmt_pct(total_entry.reached_2r_ratio)} stop={_fmt_pct(total_entry.hit_stop_ratio)}"
        )
    print(
        f"  shadow: n={total_shadow.n} 1R={_fmt_pct(total_shadow.reached_1r_ratio)} "
        f"2R={_fmt_pct(total_shadow.reached_2r_ratio)} stop={_fmt_pct(total_shadow.hit_stop_ratio)}"
    )
    suspects = [g for g in by_reason if _suspect_flag(g)]
    if suspects:
        print(f"  [검토] reason_code (n>={MIN_N_FOR_SUSPECT}, reached_1r>="
              f"{int(SUSPECT_REACHED_1R_RATIO * 100)}%):")
        for g in suspects:
            print(
                f"    - {g.key}: n={g.n} 1R={_fmt_pct(g.reached_1r_ratio)} "
                f"stop={_fmt_pct(g.hit_stop_ratio)} avg_max={_fmt_signed_pct(g.avg_max_return_25m)}"
            )
    else:
        print("  [검토] 의심 reason_code 없음 — 게이트가 잘 거르는 중.")
    if md_path:
        print(f"  - markdown: {md_path}")


# ---------------------------------------------------------------------------
# 엔트리 포인트
# ---------------------------------------------------------------------------


def build_daily_review_section(
    target_date: str,
    *,
    shadow_csv: str = SHADOW_CSV_DEFAULT,
    entry_csv: str = ENTRY_CSV_DEFAULT,
    out_dir: Optional[str] = REVIEWS_DIR_DEFAULT,
    top_n: int = 5,
) -> List[str]:
    """daily_review 마크다운에 끼워 넣을 'shadow 진단' 섹션 lines 를 만든다.

    부수효과로 ``shadow_diagnostics_<YYYYMMDD>.md`` (그날만) 와
    ``shadow_diagnostics_all.md`` (전체 누적) 두 상세 리포트를
    ``out_dir`` 에 갱신해 둔다. ``out_dir=None`` 이면 저장 생략.

    데이터 누적이 적어 그날 표본만으로 통계가 안 나오는 경우가 많아,
    daily_review 본문에는 **누적 통계 기반 의심 게이트 Top N** 만 짧게
    노출하고, 그날 라벨링 완료 표본 수는 한 줄로 알린다.
    """
    today_outcome = run_diagnostics(
        shadow_csv=shadow_csv,
        entry_csv=entry_csv,
        target_date=target_date,
        out_dir=out_dir,
        write_markdown=out_dir is not None,
    )
    cumulative_outcome = run_diagnostics(
        shadow_csv=shadow_csv,
        entry_csv=entry_csv,
        target_date=None,
        out_dir=out_dir,
        write_markdown=out_dir is not None,
    )

    cum_shadow_meta: Dict[str, object] = cumulative_outcome["shadow_meta"]
    cum_entry_meta: Dict[str, object] = cumulative_outcome["entry_meta"]
    today_shadow_meta: Dict[str, object] = today_outcome["shadow_meta"]
    cum_shadow: GroupStats = cumulative_outcome["total_shadow"]
    cum_entry: Optional[GroupStats] = cumulative_outcome["total_entry"]
    cum_by_reason: Sequence[GroupStats] = cumulative_outcome["by_reason"]

    today_shadow_rows = today_outcome["total_shadow"].n  # 그날 라벨링 완료 표본 수
    cum_shadow_n = cum_shadow.n
    cum_entry_n = cum_entry.n if cum_entry is not None else 0

    lines: List[str] = []
    lines.append(
        f"- 오늘 라벨링 완료 거절 표본: **{today_shadow_rows}건** / "
        f"전체 누적 거절 표본: **{cum_shadow_n}건** "
        f"(ready 누적 {cum_entry_n}건)"
    )
    if cum_entry is not None and cum_entry.n > 0:
        lines.append(
            f"- 누적 트랙 비교 — ready: 1R={_fmt_pct(cum_entry.reached_1r_ratio)} / "
            f"stop={_fmt_pct(cum_entry.hit_stop_ratio)}, "
            f"shadow: 1R={_fmt_pct(cum_shadow.reached_1r_ratio)} / "
            f"stop={_fmt_pct(cum_shadow.hit_stop_ratio)}"
        )
    else:
        lines.append(
            f"- shadow 누적 1R={_fmt_pct(cum_shadow.reached_1r_ratio)} / "
            f"stop={_fmt_pct(cum_shadow.hit_stop_ratio)}"
        )

    suspects = [g for g in cum_by_reason if _suspect_flag(g)]
    if not suspects:
        lines.append(
            f"- 의심 게이트(n≥{MIN_N_FOR_SUSPECT}, reached_1r≥"
            f"{int(SUSPECT_REACHED_1R_RATIO * 100)}%): 없음 — 게이트가 잘 거르는 중."
        )
    else:
        # reached_1r 내림차순 정렬은 by_reason 단계에서 이미 적용됨.
        ranked = sorted(
            suspects,
            key=lambda g: (
                -(g.reached_1r_ratio or 0.0),
                -g.n,
                g.key,
            ),
        )[:top_n]
        lines.append(
            f"- 의심 게이트 Top {len(ranked)} (n≥{MIN_N_FOR_SUSPECT}, "
            f"reached_1r≥{int(SUSPECT_REACHED_1R_RATIO * 100)}%, 누적 기준):"
        )
        for g in ranked:
            lines.append(
                f"  - **{g.key}**: n={g.n}, "
                f"1R={_fmt_pct(g.reached_1r_ratio)}, "
                f"stop={_fmt_pct(g.hit_stop_ratio)}, "
                f"avg_max={_fmt_signed_pct(g.avg_max_return_25m)}"
            )

    if not today_shadow_meta.get("header_ok", True):
        lines.append(
            "- ⚠️ shadow CSV 헤더에 누락 컬럼 — `python -m review.shadow_diagnostics --migrate-header` 권장."
        )

    if out_dir:
        cum_path = cumulative_outcome.get("markdown_path")
        if cum_path:
            lines.append(f"- 상세: `{cum_path}` (전체 누적), 그날만은 `shadow_diagnostics_{target_date.replace('-', '')}.md`")
    return lines


def run_diagnostics(
    *,
    shadow_csv: str = SHADOW_CSV_DEFAULT,
    entry_csv: str = ENTRY_CSV_DEFAULT,
    target_date: Optional[str] = None,
    out_dir: Optional[str] = REVIEWS_DIR_DEFAULT,
    write_markdown: bool = True,
) -> Dict[str, object]:
    """shadow CSV 를 읽어 reason_code 별 사후 라벨 통계를 집계하고
    선택적으로 마크다운 리포트를 저장한다."""
    shadow_rows, shadow_meta = _read_shadow_rows(shadow_csv)
    entry_rows, entry_meta = _read_entry_rows(entry_csv)

    shadow_filtered = _filter_by_date(shadow_rows, target_date)
    entry_filtered = _filter_by_date(entry_rows, target_date)

    target_label = target_date or "전체기간"

    total_shadow = aggregate_total(shadow_filtered, key="shadow")
    total_entry = (
        aggregate_total(entry_filtered, key="ready") if entry_meta.get("exists") else None
    )
    by_reason = aggregate_by_reason(shadow_filtered)

    md_path: Optional[str] = None
    if write_markdown and out_dir:
        os.makedirs(out_dir, exist_ok=True)
        # 파일명 — 특정 날짜면 그 날짜, 전체기간이면 'all'
        suffix = (
            target_date.replace("-", "") if target_date else "all"
        )
        md_path = os.path.join(out_dir, f"shadow_diagnostics_{suffix}.md")
        lines = _markdown_lines(
            target_label=target_label,
            shadow_meta=shadow_meta,
            entry_meta=entry_meta,
            total_shadow=total_shadow,
            total_entry=total_entry,
            by_reason=by_reason,
        )
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    return {
        "target_label": target_label,
        "shadow_meta": shadow_meta,
        "entry_meta": entry_meta,
        "total_shadow": total_shadow,
        "total_entry": total_entry,
        "by_reason": by_reason,
        "markdown_path": md_path,
    }


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m review.shadow_diagnostics",
        description="shadow 학습 트랙(=게이트가 거른 wait/blocked 표본) 의 25분 사후 라벨을 reason_code 단위로 집계해 false-negative 가능성을 진단한다.",
    )
    parser.add_argument(
        "--shadow-csv", default=SHADOW_CSV_DEFAULT,
        help=f"shadow CSV 경로 (기본 {SHADOW_CSV_DEFAULT}).",
    )
    parser.add_argument(
        "--entry-csv", default=ENTRY_CSV_DEFAULT,
        help=f"ready 비교용 entry CSV 경로 (기본 {ENTRY_CSV_DEFAULT}).",
    )
    parser.add_argument(
        "--date", default=None,
        help="대상 날짜 YYYY-MM-DD (생략 시 전체 누적).",
    )
    parser.add_argument(
        "--out-dir", default=REVIEWS_DIR_DEFAULT,
        help=f"마크다운 리포트 저장 디렉토리 (기본 {REVIEWS_DIR_DEFAULT}).",
    )
    parser.add_argument(
        "--no-markdown", action="store_true",
        help="마크다운 리포트 저장 생략 (stdout 요약만).",
    )
    parser.add_argument(
        "--migrate-header", action="store_true",
        help="shadow CSV 헤더가 표준 fields 와 다르면 백업 후 첫 줄만 교체.",
    )
    return parser.parse_args(argv)


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


def main(argv: Optional[Sequence[str]] = None) -> int:
    _reconfigure_stdout_utf8()
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])

    if args.migrate_header:
        result = migrate_shadow_header(args.shadow_csv)
        if result.get("changed"):
            print(f"[migrate-header] OK — backup: {result.get('backup')}")
            print(f"  old: {result.get('old_header')}")
            print(f"  new: {result.get('new_header')}")
        else:
            print(f"[migrate-header] skip — {result.get('reason')}")
        return 0

    try:
        outcome = run_diagnostics(
            shadow_csv=args.shadow_csv,
            entry_csv=args.entry_csv,
            target_date=args.date,
            out_dir=args.out_dir,
            write_markdown=not args.no_markdown,
        )
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    _print_summary(
        target_label=outcome["target_label"],
        shadow_meta=outcome["shadow_meta"],
        entry_meta=outcome["entry_meta"],
        total_shadow=outcome["total_shadow"],
        total_entry=outcome["total_entry"],
        by_reason=outcome["by_reason"],
        md_path=outcome["markdown_path"],
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
