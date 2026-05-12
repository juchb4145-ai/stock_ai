"""분류·메트릭 통계 → 다음 거래일 룰 추천.

각 룰은:
  - 트리거 통계 검사 (표본수/비율/평균 R)
  - 추천 파라미터 변경 (entry_strategy / exit_strategy 의 모듈 상수 오버라이드)
  - confidence: 'high'(n>=5) / 'medium'(n>=3) / 'low'(n<3)
를 반환한다. low 는 적용 후보에서 빠지지만 리포트에는 노출한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Dict, List, Optional

from entry_strategy import (
    DANTE_FIRST_ENTRY_RATIO,
    MAX_UPPER_WICK_RATIO,
    OVERHEATED_OPEN_RETURN,
)
from exit_strategy import (
    EXIT_BE_R,
    EXIT_PARTIAL_R,
    EXIT_PARTIAL_RATIO,
)

from .loader import Trade
from .overrides import Override


# === 룰 발동 임계 ===
FAKE_BREAKOUT_RATIO_BLOCK = 0.30   # ① 진입 금지
A_VS_B_DIFF_R = 0.5                # ② 더 기다리기 (A 평균R - B 평균R) <= -0.5
LATE_TAKE_RATIO = 0.25             # ③ 빨리 익절
FAST_TAKE_RATIO = 0.25             # ④ 트레일링 적용
BE_VIOLATION_RATIO = 0.30          # ⑤ 본절컷


@dataclass
class RuleRecommendation:
    rule_id: str
    title: str
    n: int                       # 트리거 표본 수
    ratio: float                 # 비율(0~1)
    confidence: str              # high / medium / low
    summary: str                 # 사람용 한 줄 설명
    overrides: List[Override] = field(default_factory=list)
    evidence: Dict[str, float] = field(default_factory=dict)

    def overrides_as_dicts(self) -> List[dict]:
        return [o.to_dict() for o in self.overrides]


def _confidence(n: int) -> str:
    if n >= 5:
        return "high"
    if n >= 3:
        return "medium"
    return "low"


def _safe_mean(xs):
    xs = [x for x in xs if x == x]  # NaN 제거
    if not xs:
        return float("nan")
    return mean(xs)


# ---------------------------------------------------------------------------
# 개별 룰
# ---------------------------------------------------------------------------


def _rule_block_fake_breakout(trades: List[Trade]) -> Optional[RuleRecommendation]:
    total = len(trades)
    if total == 0:
        return None
    fakes = [t for t in trades if t.entry_class == "fake_breakout"]
    n = len(fakes)
    ratio = n / total
    if ratio < FAKE_BREAKOUT_RATIO_BLOCK or n < 2:
        return None

    wick = _safe_mean([t.features.get("upper_wick_ratio", 0.0) for t in fakes])
    open_ret = _safe_mean([t.features.get("open_return", 0.0) for t in fakes])

    new_wick = max(0.20, round(MAX_UPPER_WICK_RATIO - 0.10, 2))
    new_open = max(0.05, round(OVERHEATED_OPEN_RETURN - 0.02, 2))

    return RuleRecommendation(
        rule_id="block_fake_breakout",
        title="① 진입 금지(가짜돌파 게이트 강화)",
        n=n,
        ratio=ratio,
        confidence=_confidence(n),
        summary=(
            f"가짜돌파 {n}/{total}건 ({ratio:.0%}). "
            f"평균 윗꼬리 {wick:.0%}, 시가대비 {open_ret:+.1%}. "
            f"MAX_UPPER_WICK_RATIO {MAX_UPPER_WICK_RATIO:.2f}→{new_wick:.2f}, "
            f"OVERHEATED_OPEN_RETURN {OVERHEATED_OPEN_RETURN:.2f}→{new_open:.2f}"
        ),
        overrides=[
            Override(
                target="entry_strategy.MAX_UPPER_WICK_RATIO",
                op="set", value=new_wick,
                reason=f"가짜돌파 {n}/{total}건, 평균 윗꼬리 {wick:.0%}",
            ),
            Override(
                target="entry_strategy.OVERHEATED_OPEN_RETURN",
                op="set", value=new_open,
                reason=f"가짜돌파 표본 평균 시가대비 {open_ret:+.1%}",
            ),
        ],
        evidence={"avg_upper_wick": wick, "avg_open_return": open_ret},
    )


def _rule_wait_for_pullback(trades: List[Trade]) -> Optional[RuleRecommendation]:
    a_trades = [t for t in trades if t.entry_class == "breakout_chase"]
    b_trades = [t for t in trades if t.entry_class == "first_pullback"]
    if len(a_trades) < 2 or len(b_trades) < 1:
        return None
    a_r = _safe_mean([t.metrics.get("r_multiple") for t in a_trades])
    b_r = _safe_mean([t.metrics.get("r_multiple") for t in b_trades])
    if a_r != a_r or b_r != b_r:
        return None
    if not (a_r < 0 and b_r > 0 and (b_r - a_r) >= A_VS_B_DIFF_R):
        return None

    return RuleRecommendation(
        rule_id="wait_for_pullback",
        title="② 더 기다리기(A급 1차 추격 비활성, 눌림 진입만 허용)",
        n=len(a_trades),
        ratio=len(a_trades) / max(len(trades), 1),
        confidence=_confidence(len(a_trades)),
        summary=(
            f"A급 추격 {len(a_trades)}건 평균 {a_r:+.2f}R, "
            f"B급/본진입 {len(b_trades)}건 평균 {b_r:+.2f}R. "
            f"DANTE_FIRST_ENTRY_RATIO {DANTE_FIRST_ENTRY_RATIO:.2f}→0.0 권장"
        ),
        overrides=[
            Override(
                target="entry_strategy.DANTE_FIRST_ENTRY_RATIO",
                op="set", value=0.0,
                reason=(
                    f"A급 평균 {a_r:+.2f}R, B급/본진입 평균 {b_r:+.2f}R — 추격 비활성"
                ),
            ),
        ],
        evidence={"a_avg_r": a_r, "b_avg_r": b_r},
    )


def _rule_take_profit_faster(trades: List[Trade]) -> Optional[RuleRecommendation]:
    winners = [t for t in trades if (t.final_return or 0) > 0]
    if not winners:
        return None
    late = [t for t in winners if t.exit_class == "late_take"]
    if len(late) < 2:
        return None
    ratio = len(late) / len(winners)
    if ratio < LATE_TAKE_RATIO:
        return None
    avg_give = _safe_mean([t.metrics.get("give_back_r") for t in late])

    new_partial_r = max(1.0, round(EXIT_PARTIAL_R - 0.5, 2))
    return RuleRecommendation(
        rule_id="take_profit_faster",
        title="③ 빨리 익절(부분익절 +2R→+1.5R)",
        n=len(late),
        ratio=ratio,
        confidence=_confidence(len(late)),
        summary=(
            f"늦은익절 {len(late)}/{len(winners)}건 ({ratio:.0%}), "
            f"평균 give-back {avg_give:+.2f}R. "
            f"EXIT_PARTIAL_R {EXIT_PARTIAL_R}→{new_partial_r}"
        ),
        overrides=[
            Override(
                target="exit_strategy.EXIT_PARTIAL_R",
                op="set", value=new_partial_r, min=1.0,
                reason=f"늦은익절 {len(late)}/{len(winners)}건, 평균 give-back {avg_give:+.2f}R",
            ),
        ],
        evidence={"avg_give_back_r": avg_give},
    )


def _rule_apply_trailing(trades: List[Trade]) -> Optional[RuleRecommendation]:
    winners = [t for t in trades if (t.final_return or 0) > 0]
    if not winners:
        return None
    fast = [t for t in winners if t.exit_class == "fast_take"]
    if len(fast) < 2:
        return None
    ratio = len(fast) / len(winners)
    if ratio < FAST_TAKE_RATIO:
        return None
    avg_over = _safe_mean([t.metrics.get("over_run_r") for t in fast])

    new_partial_ratio = max(0.2, round(EXIT_PARTIAL_RATIO - 0.2, 2))
    return RuleRecommendation(
        rule_id="apply_trailing",
        title="④ 트레일링 적용(부분익절 비율 ↓, 잔량 추세 따라가기)",
        n=len(fast),
        ratio=ratio,
        confidence=_confidence(len(fast)),
        summary=(
            f"빠른익절 {len(fast)}/{len(winners)}건 ({ratio:.0%}), "
            f"평균 over-run {avg_over:+.2f}R. "
            f"EXIT_PARTIAL_RATIO {EXIT_PARTIAL_RATIO}→{new_partial_ratio} "
            "(부분익절 후 잔량은 5MA + chandelier 트레일)"
        ),
        overrides=[
            Override(
                target="exit_strategy.EXIT_PARTIAL_RATIO",
                op="set", value=new_partial_ratio, min=0.2,
                reason=f"빠른익절 {len(fast)}/{len(winners)}건, 평균 over-run {avg_over:+.2f}R",
            ),
            Override(
                target="exit_strategy.TRAIL_HIGHEST_GIVEBACK_R",
                op="set", value=0.7,
                reason="잔량 trailing 활성화 — 고점 대비 0.7R 반납 시 청산",
            ),
        ],
        evidence={"avg_over_run_r": avg_over},
    )


def _rule_break_even_cut(trades: List[Trade]) -> Optional[RuleRecommendation]:
    losers = [t for t in trades if (t.final_return or 0) < 0]
    if not losers:
        return None
    be_violations = [t for t in losers if t.metrics.get("be_violation", 0.0) >= 1.0]
    n = len(be_violations)
    if n < 2:
        return None
    ratio = n / len(losers)
    if ratio < BE_VIOLATION_RATIO:
        return None

    new_be_r = max(0.5, round(EXIT_BE_R - 0.3, 2))
    return RuleRecommendation(
        rule_id="break_even_cut",
        title="⑤ 본절컷(BE 스탑 이동을 +0.7R로 앞당김)",
        n=n,
        ratio=ratio,
        confidence=_confidence(n),
        summary=(
            f"+1R 도달 후 손절 {n}/{len(losers)}건 ({ratio:.0%}). "
            f"EXIT_BE_R {EXIT_BE_R}→{new_be_r}"
        ),
        overrides=[
            Override(
                target="exit_strategy.EXIT_BE_R",
                op="set", value=new_be_r, min=0.5,
                reason=f"+1R 도달 후 손절 {n}/{len(losers)}건 ({ratio:.0%})",
            ),
        ],
        evidence={},
    )


# ---------------------------------------------------------------------------
# 외부 진입점
# ---------------------------------------------------------------------------


RULE_FUNCS = (
    _rule_block_fake_breakout,
    _rule_wait_for_pullback,
    _rule_take_profit_faster,
    _rule_apply_trailing,
    _rule_break_even_cut,
)


def recommend_rules(trades: List[Trade]) -> List[RuleRecommendation]:
    closed = [t for t in trades if t.is_closed]
    out: List[RuleRecommendation] = []
    for func in RULE_FUNCS:
        rec = func(closed)
        if rec is not None:
            out.append(rec)
    return out
