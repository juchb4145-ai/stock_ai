"""단테조건식 편입 종목의 1차/2차 분할매수 평가.

전략:
  - 1차 (소량 25%): 조건식 편입 후 추세 필터/체결강도/거래속도/스프레드 게이트
    통과 시 즉시 추격(시장가).
  - 2차 (본진입 75%): 1차 체결 후 1분봉 첫 눌림(직전 고점 대비 -0.4~-1.5%) +
    1~2개 음봉 이후 양봉 반전 + 체결강도 유지가 모두 충족될 때 본진입.
  - 1차 체결 후 PULLBACK_WINDOW_MAX_SECONDS 안에 눌림이 발생하지 않으면
    단일 포지션으로 락(should_lock_single_position == True) → 추가매수 금지.

이 모듈은 순수 함수만 노출한다. IO/주문은 main.py 가 결정/실행한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from bars import FiveMinIndicators, MinuteBar
from portfolio import Position


# === 분할매수 비율 (합 = 1.0) ===
DANTE_FIRST_ENTRY_RATIO = 0.25
DANTE_SECOND_ENTRY_RATIO = 0.75
# B급(1봉전 돌파만) 본진입 비율 — 1차 추격 없이 첫 눌림에서 한 번에 매수
DANTE_GRADE_B_RATIO = 1.0

# === 1차 진입 게이트 ===
# 조건식 편입 후 최소 관찰 시간(초). 편입 직후 첫 틱 한두 개로 매수가
# 발사되지 않도록 짧게 강제한다.
DANTE_MIN_OBSERVATION_SECONDS = 30
# 1차 진입에 필요한 최소 실시간 틱 수
DANTE_MIN_TICKS = 5
# 체결강도 임계 — Soft 미만은 차단, Soft~Hard 사이는 추세 상승 시만 통과, Hard 이상은 무조건 통과
MIN_CHEJAN_STRENGTH = 100.0  # backward-compat alias = MIN_CHEJAN_STRENGTH_SOFT
MIN_CHEJAN_STRENGTH_SOFT = 100.0
MIN_CHEJAN_STRENGTH_HARD = 120.0
# 체결강도 추세 평가에 사용할 최근 틱 개수
CHEJAN_STRENGTH_TREND_LOOKBACK = 6
# 거래속도 임계 (주/초). 조건식이 일거래량 5만 이상을 이미 거르므로
# 추가 게이트는 보수적으로 낮게 잡는다.
MIN_VOLUME_SPEED = 500.0
# 호가 스프레드 상한
MAX_SPREAD_RATE = 0.006

# === 가짜 돌파 / 과열 차단 ===
# 5분봉 진행봉의 윗꼬리 비율 (high-close)/(high-low). 0.4 초과 시 가짜 돌파로 보고 1차 추격 차단.
MAX_UPPER_WICK_RATIO = 0.4
# 시가 대비 등락률이 +N 이상이면 이미 너무 오른 종목 — 추격 차단 (눌림으로만 진입 허용)
OVERHEATED_OPEN_RETURN = 0.10
# 현재가가 BB(55,2) 상단보다 +N 이상 위면 과열 — 추격 차단
OVERHEATED_BB55_DISTANCE = 0.04

# === 2차(본진입) 눌림 정의 ===
PULLBACK_MIN_PCT = 0.004  # 직전 고점 대비 -0.4% 이상
PULLBACK_MAX_PCT = 0.015  # 직전 고점 대비 -1.5% 이내
# 직전 고점 대비 -2% 초과로 밀린 종목은 위태로 보고 본진입 차단
MAX_DRAWDOWN_FROM_HIGH = 0.020
# 직전 1~2 음봉 후 현재봉 양봉 전환 패턴
PULLBACK_NEG_BARS_MIN = 1
PULLBACK_NEG_BARS_MAX = 2
# 본진입 윈도우 (1차 체결 후)
PULLBACK_WINDOW_MAX_SECONDS = 10 * 60


@dataclass
class EntryDecision:
    """1차/2차 진입 평가 결과."""

    status: str  # "ready" | "wait" | "blocked"
    ratio: float = 0.0  # 매수 비율(0~1). status=="ready" 일 때만 의미 있음.
    stage: int = 0  # 1 또는 2 (어느 단계인지 호출측이 식별하기 위함)
    reason: str = ""
    grade: str = ""  # "A"(0봉 돌파 분할) / "B"(1봉 돌파 일괄) / "" (해당 없음)


@dataclass
class EntryContext:
    """진입 평가에 필요한 모든 입력 데이터."""

    code: str
    name: str
    current_price: int
    open_price: int
    high: int
    low: int
    ask: int
    bid: int
    chejan_strength: float
    volume_speed: float  # 주/초
    spread_rate: float
    minute_bars: List[MinuteBar]
    five_min_ind: Optional[FiveMinIndicators]
    condition_registered_at: float
    now_ts: float
    tick_count: int
    position: Optional[Position] = None
    # === 새 게이트 입력(호출측이 ctx 빌드 시 채움) ===
    chejan_strength_history: List[float] = field(default_factory=list)
    is_breakout_zero_bar: bool = False
    is_breakout_prev_bar: bool = False
    upper_wick_ratio_zero_bar: float = 0.0
    px_over_bb55_pct: float = 0.0  # (현재가 / BB(55,2) 상단) - 1
    open_return: float = 0.0       # (현재가 / 시가) - 1


def evaluate_first_entry(ctx: EntryContext) -> EntryDecision:
    """신규 종목(entry_stage==0) 평가. A급(0봉 돌파)/B급(1봉 돌파만) 으로 분기.

    - A급: 0봉전 4개 상한선 동시 돌파 + 모든 게이트 통과 → 1차 추격 25%(stage=1)
    - B급: 1봉전 동시 돌파만 + 1분봉 첫 눌림+양봉 반전 + 게이트 통과 → 본진입 100%(stage=2)
    - 둘 다 아니면 wait

    공통 게이트:
      관찰시간/틱수/스프레드/거래속도/체결강도(120↑ 또는 100~120 + 추세 상승)/
      5분봉 캐시 충분/추세 필터/가짜돌파(윗꼬리)/과열(시가대비, BB55 거리)
    """
    if ctx.position is not None and ctx.position.entry_stage > 0:
        return EntryDecision("blocked", 0.0, 1, "이미 진입 완료")
    if ctx.current_price <= 0 or ctx.ask <= 0 or ctx.bid <= 0:
        return EntryDecision("wait", 0.0, 1, "가격/호가 데이터 부족")
    if ctx.spread_rate < 0 or ctx.spread_rate > MAX_SPREAD_RATE:
        return EntryDecision("blocked", 0.0, 1, "스프레드 과다 {:.2%}".format(ctx.spread_rate))
    if ctx.tick_count < DANTE_MIN_TICKS:
        return EntryDecision(
            "wait", 0.0, 1, "실시간 틱 부족 {}/{}".format(ctx.tick_count, DANTE_MIN_TICKS)
        )

    elapsed = ctx.now_ts - (ctx.condition_registered_at or ctx.now_ts)
    if elapsed < DANTE_MIN_OBSERVATION_SECONDS:
        return EntryDecision(
            "wait", 0.0, 1,
            "조건편입 관찰 {:.0f}/{}초".format(elapsed, DANTE_MIN_OBSERVATION_SECONDS),
        )

    if ctx.volume_speed < MIN_VOLUME_SPEED:
        return EntryDecision(
            "wait", 0.0, 1,
            "거래속도 부족 {:.0f} < {}주/초".format(ctx.volume_speed, MIN_VOLUME_SPEED),
        )

    # === 체결강도 강화 게이트 ===
    # Hard(120) 이상이면 무조건 통과, Soft~Hard(100~120) 사이는 추세 상승 시만 통과,
    # Soft(100) 미만이면 차단. chejan_strength == 0 (데이터 미수신) 은 일단 통과.
    if ctx.chejan_strength > 0:
        if ctx.chejan_strength < MIN_CHEJAN_STRENGTH_SOFT:
            return EntryDecision(
                "wait", 0.0, 1,
                "체결강도 부족 {:.1f} < {}".format(ctx.chejan_strength, MIN_CHEJAN_STRENGTH_SOFT),
            )
        if ctx.chejan_strength < MIN_CHEJAN_STRENGTH_HARD:
            if not _chejan_strength_rising(ctx.chejan_strength_history, MIN_CHEJAN_STRENGTH_SOFT):
                return EntryDecision(
                    "wait", 0.0, 1,
                    "체결강도 약함 {:.1f} (상승 미확인, Hard {} 미만)".format(
                        ctx.chejan_strength, MIN_CHEJAN_STRENGTH_HARD
                    ),
                )

    # === 5분봉 추세 필터 / 돌파 등급 판정에 캐시 필수 ===
    if ctx.five_min_ind is None or ctx.five_min_ind.closes_count < 13:
        return EntryDecision("wait", 0.0, 1, "5분봉 캐시 미준비")
    if not ctx.five_min_ind.trend_up(ctx.current_price):
        return EntryDecision(
            "wait", 0.0, 1,
            "5분봉 추세 미통과 (현재 {} < Env13 {} / BB55 {})".format(
                ctx.current_price,
                int(ctx.five_min_ind.env_upper_13_25 or 0),
                int(ctx.five_min_ind.bb_upper_55_2 or 0),
            ),
        )

    # === 가짜 돌파 게이트 (5분봉 진행봉 윗꼬리) ===
    if ctx.upper_wick_ratio_zero_bar > MAX_UPPER_WICK_RATIO:
        return EntryDecision(
            "wait", 0.0, 1,
            "5분봉 윗꼬리 과다 {:.0%} > {:.0%}".format(
                ctx.upper_wick_ratio_zero_bar, MAX_UPPER_WICK_RATIO
            ),
        )

    # === 과열 게이트 ===
    if ctx.open_return > OVERHEATED_OPEN_RETURN:
        return EntryDecision(
            "blocked", 0.0, 1,
            "시가 대비 과열 {:.1%} > {:.1%}".format(ctx.open_return, OVERHEATED_OPEN_RETURN),
        )
    if ctx.px_over_bb55_pct > OVERHEATED_BB55_DISTANCE:
        return EntryDecision(
            "blocked", 0.0, 1,
            "BB55 대비 과열 +{:.1%} > {:.1%}".format(
                ctx.px_over_bb55_pct, OVERHEATED_BB55_DISTANCE
            ),
        )

    # === A급 / B급 분기 ===
    if ctx.is_breakout_zero_bar:
        return EntryDecision(
            "ready", DANTE_FIRST_ENTRY_RATIO, 1,
            "A급 0봉 돌파 1차 추격 ({:.0%})".format(DANTE_FIRST_ENTRY_RATIO),
            grade="A",
        )

    if ctx.is_breakout_prev_bar:
        # B급: 추격 안 하고 1분봉 첫 눌림 + 양봉 반전 시 한 번에 본진입(100%)
        return _evaluate_b_grade_pullback(ctx)

    return EntryDecision("wait", 0.0, 1, "0봉/1봉 동시 돌파 미확인")


def _evaluate_b_grade_pullback(ctx: EntryContext) -> EntryDecision:
    """B급(1봉전 돌파만) 종목의 첫 눌림 본진입 평가.

    breakout_high 가 없으므로 1분봉의 최근 N개 봉 high 를 기준 고점으로 사용.
    조건: 눌림 -0.4~-1.5% + 1~2 음봉 후 양봉 반전.
    통과 시 ratio=1.0, stage=2 로 한 번에 매수(이후 추가매수 없음).
    """
    bars = ctx.minute_bars
    if not bars:
        return EntryDecision("wait", 0.0, 1, "B급: 1분봉 미수신")

    recent = bars[-min(len(bars), 10):]
    high_since = max((b.high for b in recent if b.high > 0), default=0)
    if high_since <= 0:
        return EntryDecision("wait", 0.0, 1, "B급: 1분봉 고점 데이터 없음")

    pullback_pct = (high_since - ctx.current_price) / high_since
    if pullback_pct > MAX_DRAWDOWN_FROM_HIGH:
        return EntryDecision(
            "blocked", 0.0, 1, "B급: 고점 대비 -{:.2%} 초과".format(pullback_pct)
        )
    if pullback_pct < PULLBACK_MIN_PCT:
        return EntryDecision(
            "wait", 0.0, 1,
            "B급: 눌림 부족 ({:.2%} < {:.2%})".format(pullback_pct, PULLBACK_MIN_PCT),
        )
    if pullback_pct > PULLBACK_MAX_PCT:
        return EntryDecision(
            "wait", 0.0, 1,
            "B급: 눌림 깊음 ({:.2%} > {:.2%})".format(pullback_pct, PULLBACK_MAX_PCT),
        )

    if not _has_neg_then_positive_pattern(
        bars,
        neg_min=PULLBACK_NEG_BARS_MIN,
        neg_max=PULLBACK_NEG_BARS_MAX,
    ):
        return EntryDecision("wait", 0.0, 1, "B급: 음봉→양봉 반전 미확인")

    return EntryDecision(
        "ready", DANTE_GRADE_B_RATIO, 2,
        "B급 첫 눌림 본진입 (눌림 {:.2%}, {:.0%})".format(
            pullback_pct, DANTE_GRADE_B_RATIO
        ),
        grade="B",
    )


def _chejan_strength_rising(history: Sequence[float], min_recent_avg: float) -> bool:
    """최근 체결강도가 우상향이고 후반부 평균이 임계값 이상인지 판단.

    history 의 앞 절반 평균과 뒷 절반 평균을 비교해, 뒷 절반이 더 크고
    동시에 min_recent_avg 이상이어야 True.
    표본이 너무 적으면(< 4) False — 모호한 경우 보수적으로 진입 보류.
    """
    if not history or len(history) < 4:
        return False
    half = len(history) // 2
    head = list(history[:half])
    tail = list(history[half:])
    if not head or not tail:
        return False
    head_mean = sum(head) / len(head)
    tail_mean = sum(tail) / len(tail)
    return tail_mean >= min_recent_avg and tail_mean >= head_mean


def evaluate_second_entry(ctx: EntryContext) -> EntryDecision:
    """2차(본진입) 가능 여부 평가. position.entry_stage == 1 인 종목에만 적용."""
    pos = ctx.position
    if pos is None or pos.entry_stage != 1:
        return EntryDecision("blocked", 0.0, 2, "1차 미체결 또는 본진입 완료")

    deadline = pos.pullback_window_deadline
    if deadline > 0 and ctx.now_ts > deadline:
        return EntryDecision(
            "blocked",
            0.0,
            2,
            "본진입 윈도우 만료(1차 후 {:.0f}초)".format(
                ctx.now_ts - (pos.entry1_time or ctx.now_ts)
            ),
        )

    if ctx.current_price <= 0 or ctx.ask <= 0 or ctx.bid <= 0:
        return EntryDecision("wait", 0.0, 2, "가격/호가 데이터 부족")
    if ctx.spread_rate < 0 or ctx.spread_rate > MAX_SPREAD_RATE:
        return EntryDecision("wait", 0.0, 2, "스프레드 과다 {:.2%}".format(ctx.spread_rate))

    if ctx.chejan_strength > 0 and ctx.chejan_strength < MIN_CHEJAN_STRENGTH:
        return EntryDecision(
            "wait",
            0.0,
            2,
            "체결강도 약화 {:.1f} < {}".format(ctx.chejan_strength, MIN_CHEJAN_STRENGTH),
        )

    if ctx.volume_speed < MIN_VOLUME_SPEED * 0.5:
        return EntryDecision(
            "wait",
            0.0,
            2,
            "거래속도 약화 {:.0f}".format(ctx.volume_speed),
        )

    breakout_high = pos.breakout_high or pos.entry_price
    if breakout_high <= 0:
        return EntryDecision("wait", 0.0, 2, "고점 추적 데이터 부족")
    pullback_pct = (breakout_high - ctx.current_price) / breakout_high

    if pullback_pct > MAX_DRAWDOWN_FROM_HIGH:
        return EntryDecision(
            "blocked",
            0.0,
            2,
            "고점 대비 -{:.2%} 초과(차단)".format(pullback_pct),
        )
    if pullback_pct < PULLBACK_MIN_PCT:
        return EntryDecision(
            "wait",
            0.0,
            2,
            "눌림 부족 ({:.2%} < {:.2%})".format(pullback_pct, PULLBACK_MIN_PCT),
        )
    if pullback_pct > PULLBACK_MAX_PCT:
        return EntryDecision(
            "wait",
            0.0,
            2,
            "눌림 깊음 ({:.2%} > {:.2%})".format(pullback_pct, PULLBACK_MAX_PCT),
        )

    if not _has_neg_then_positive_pattern(
        ctx.minute_bars,
        neg_min=PULLBACK_NEG_BARS_MIN,
        neg_max=PULLBACK_NEG_BARS_MAX,
    ):
        return EntryDecision("wait", 0.0, 2, "음봉→양봉 반전 미확인")

    return EntryDecision(
        "ready",
        DANTE_SECOND_ENTRY_RATIO,
        2,
        "A급 본진입 (눌림 {:.2%}, {:.0%})".format(pullback_pct, DANTE_SECOND_ENTRY_RATIO),
        grade="A",
    )


def should_lock_single_position(ctx: EntryContext) -> bool:
    """1차 후 윈도우 안에 눌림이 안 오면 본진입을 포기하고 단일 포지션으로 잠근다."""
    pos = ctx.position
    if pos is None or pos.entry_stage != 1:
        return False
    if pos.pullback_window_deadline <= 0:
        return False
    return ctx.now_ts > pos.pullback_window_deadline


def _has_neg_then_positive_pattern(
    bars: List[MinuteBar], *, neg_min: int, neg_max: int
) -> bool:
    """직전 1~N개 봉이 모두 음봉이고, 현재(진행)봉이 양봉인지 확인."""
    if len(bars) < neg_min + 1:
        return False
    cur = bars[-1]
    if cur.close <= cur.open:
        return False
    neg = 0
    for bar in reversed(bars[:-1]):
        if bar.close < bar.open:
            neg += 1
            if neg > neg_max:
                return False
        else:
            break
    return neg_min <= neg <= neg_max
