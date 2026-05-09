"""단테조건식 편입 종목의 1차/2차 분할매수 평가.

전략:
  - A급: 조건식 편입 후 추세 필터/체결강도/거래속도/스프레드 게이트
    통과 시 즉시 매수하지 않고 감시 상태로 둔다.
  - A급 본진입: 감시 시작 후 1분봉 첫 눌림(직전 고점 대비 -0.4~-1.5%) +
    1~2개 음봉 이후 양봉 반전 + 체결강도 유지가 모두 충족될 때 100% 본진입.
  - 1차 체결 후 PULLBACK_WINDOW_MAX_SECONDS 안에 눌림이 발생하지 않으면
    단일 포지션으로 락(should_lock_single_position == True) → 추가매수 금지.

이 모듈은 순수 함수만 노출한다. IO/주문은 main.py 가 결정/실행한다.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from bars import FiveMinIndicators, MinuteBar
from market_state import (
    MarketSnapshot,
    REGIME_NEUTRAL,
    REGIME_RISK_OFF,
    REGIME_UNKNOWN,
    REGIME_WEAK,
)
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
# 거래대금 속도 임계 (원/분). 실시간성은 유지하고, 조건식 편입 후 받은 틱 구간을
# 분당 거래대금으로 환산해 가격대별 왜곡(저가주는 느슨/고가주는 과도하게 엄격)을 줄인다.
MIN_TURNOVER_SPEED_PER_MIN = 50_000_000.0
# 기존 학습 피처/로그 호환용 주/초 기준. 신규 게이트는 거래대금 속도를 우선 사용한다.
MIN_VOLUME_SPEED = 300.0
# 호가 스프레드 상한
MAX_SPREAD_RATE = 0.006

# === 가짜 돌파 / 과열 차단 ===
# 5분봉 진행봉의 윗꼬리 비율 (high-close)/(high-low). 임계 초과 시 가짜 돌파로 보고 1차 추격 차단.
# 2026-05-04 daily_review: 가짜돌파 3/8건(38%), 평균 윗꼬리 1% / 시가대비 +4.0% — 0.40→0.30 으로 강화.
MAX_UPPER_WICK_RATIO = 0.30
# 시가 대비 등락률이 +N 이상이면 이미 너무 오른 종목 — 추격 차단 (눌림으로만 진입 허용)
# 같은 배경으로 0.10→0.08 으로 강화.
OVERHEATED_OPEN_RETURN = 0.08
# 장 초반은 +8%를 유지하되, 장중에는 눌림 구조가 확인된 주도주 재진입을 조금 더 허용한다.
OVERHEATED_OPEN_RETURN_MORNING = 0.10
OVERHEATED_OPEN_RETURN_MIDDAY = 0.12
OVERHEATED_OPEN_RETURN_LATE = 0.10
# 현재가가 BB(55,2) 상단보다 +N 이상 위면 과열 — 추격 차단
OVERHEATED_BB55_DISTANCE = 0.04

# === 2차(본진입) 눌림 정의 ===
PULLBACK_MIN_PCT = 0.003  # 직전 고점 대비 -0.3% 이상
PULLBACK_MAX_PCT = 0.015  # 직전 고점 대비 -1.5% 이내
# 직전 고점 대비 -2% 초과로 밀린 종목은 위태로 보고 본진입 차단
MAX_DRAWDOWN_FROM_HIGH = 0.020
# 직전 1~2 음봉 후 현재봉 양봉 전환 패턴
PULLBACK_NEG_BARS_MIN = 0
PULLBACK_NEG_BARS_MAX = 2
# 본진입 윈도우 (1차 체결 후)
PULLBACK_WINDOW_MAX_SECONDS = 10 * 60

# === Re-entry after profitable exit ===
# A leader often shakes out after the first profit-taking leg.  This setup is
# deliberately separate from the first A/B entry so same-day re-entry requires
# a real shakeout and recovery, not just another chase.
REENTRY_WATCH_WINDOW_SECONDS = 30 * 60
REENTRY_MIN_DROP_FROM_HIGH = 0.018
REENTRY_MAX_DROP_FROM_HIGH = 0.065
REENTRY_RECOVERY_BUFFER_PCT = 0.002
REENTRY_RATIO = 0.5


# === reason_code enum ===
# 자유 형식 한글 reason 과 짝을 이루는 안정 식별자. shadow 학습 트랙에서
# false-negative 분석 시 group by 키로 쓰인다(수치가 들어간 한글 문자열은
# 카디널리티가 폭발하므로 별도 코드 컬럼이 필요).
#
# 명명 규칙: GATE_* (게이트 거절) / READY_* (합격 분기). 같은 게이트가 단계별로
# 상태가 다른 경우(stage1 spread 는 blocked, stage2 spread 는 wait) 도 게이트
# 식별자는 동일하게 두고, 단계 구분이 필요한 항목만 STAGE2_ prefix 를 단다.
# wait/blocked/ready 분리는 EntryDecision.status 로 직교 식별 가능.

# Stage1 공통 게이트
GATE_ALREADY_ENTERED = "GATE_ALREADY_ENTERED"
GATE_PRICE_DATA = "GATE_PRICE_DATA"
GATE_SPREAD = "GATE_SPREAD"
GATE_TICKS_INSUFFICIENT = "GATE_TICKS_INSUFFICIENT"
GATE_OBSERVATION_SHORT = "GATE_OBSERVATION_SHORT"
GATE_VOLUME_SPEED = "GATE_VOLUME_SPEED"
GATE_CHEJAN_SOFT = "GATE_CHEJAN_SOFT"
GATE_CHEJAN_HARD_NO_TREND = "GATE_CHEJAN_HARD_NO_TREND"
GATE_FIVEMIN_CACHE = "GATE_FIVEMIN_CACHE"
GATE_TREND_FILTER = "GATE_TREND_FILTER"
GATE_UPPER_WICK = "GATE_UPPER_WICK"
GATE_OVERHEAT_OPEN = "GATE_OVERHEAT_OPEN"
GATE_OVERHEAT_BB55 = "GATE_OVERHEAT_BB55"
GATE_NO_BREAKOUT = "GATE_NO_BREAKOUT"

# Stage1 B급 풀백
GATE_BGRADE_NO_MINUTE_BARS = "GATE_BGRADE_NO_MINUTE_BARS"
GATE_BGRADE_NO_HIGH = "GATE_BGRADE_NO_HIGH"
GATE_BGRADE_DRAWDOWN = "GATE_BGRADE_DRAWDOWN"
GATE_BGRADE_PULLBACK_SHALLOW = "GATE_BGRADE_PULLBACK_SHALLOW"
GATE_BGRADE_PULLBACK_DEEP = "GATE_BGRADE_PULLBACK_DEEP"
GATE_BGRADE_NO_REVERSAL = "GATE_BGRADE_NO_REVERSAL"

# Stage2 본진입
GATE_STAGE2_NO_FIRST = "GATE_STAGE2_NO_FIRST"
GATE_STAGE2_WINDOW_EXPIRED = "GATE_STAGE2_WINDOW_EXPIRED"
GATE_STAGE2_PRICE_DATA = "GATE_STAGE2_PRICE_DATA"
GATE_STAGE2_SPREAD = "GATE_STAGE2_SPREAD"
GATE_STAGE2_CHEJAN = "GATE_STAGE2_CHEJAN"
GATE_STAGE2_VOLUME = "GATE_STAGE2_VOLUME"
GATE_STAGE2_HIGH_DATA = "GATE_STAGE2_HIGH_DATA"
GATE_STAGE2_DRAWDOWN = "GATE_STAGE2_DRAWDOWN"
GATE_STAGE2_PULLBACK_SHALLOW = "GATE_STAGE2_PULLBACK_SHALLOW"
GATE_STAGE2_PULLBACK_DEEP = "GATE_STAGE2_PULLBACK_DEEP"
GATE_STAGE2_NO_REVERSAL = "GATE_STAGE2_NO_REVERSAL"

# 합격 분기
READY_AGRADE_FIRST = "READY_AGRADE_FIRST"
READY_AGRADE_SECOND = "READY_AGRADE_SECOND"
READY_BGRADE_PULLBACK = "READY_BGRADE_PULLBACK"
READY_REENTRY_PULLBACK = "READY_REENTRY_PULLBACK"
WATCH_AGRADE_BREAKOUT = "WATCH_AGRADE_BREAKOUT"


# === Market regime dry-run gate (1차 PR: status/ratio 변경 없음, 메타만 부여) ===
# 다음 PR 에서 표본 누적 후 일부를 실제 status="blocked" 로 승격할 때
# reason_code 와 동일한 명명 규칙(`GATE_*`)을 그대로 쓸 수 있도록 정의해 둔다.
MARKET_GATE_WEAK_CHASE_BLOCK = "GATE_MARKET_WEAK_CHASE_BLOCK"
MARKET_GATE_RISK_OFF = "GATE_MARKET_RISK_OFF"

MARKET_ACTION_ALLOW = "dry_run_allow"
MARKET_ACTION_BLOCK_CHASE_ONLY = "dry_run_block_chase_only"
MARKET_ACTION_BLOCK_ALL = "dry_run_block_all"


@dataclass
class EntryDecision:
    """1차/2차 진입 평가 결과."""

    status: str  # "ready" | "wait" | "blocked"
    ratio: float = 0.0  # 매수 비율(0~1). status=="ready" 일 때만 의미 있음.
    stage: int = 0  # 1 또는 2 (어느 단계인지 호출측이 식별하기 위함)
    reason: str = ""
    grade: str = ""  # "A"(0봉 돌파 분할) / "B"(1봉 돌파 일괄) / "" (해당 없음)
    reason_code: str = ""  # GATE_*/READY_* enum. shadow 분석 시 안정 group by 키.
    # === Market regime dry-run 메타 (status/ratio 에는 영향 없음) ===
    # 1차 PR 에서는 학습/거래 로그에 기록만 하고 실제 매수 행동은 변경하지 않는다.
    # 다음 PR 에서 표본 분포를 본 뒤 일부 케이스를 실제 status="blocked" 로 승격 예정.
    market_regime: str = ""           # "strong"|"neutral"|"weak"|"risk_off"|"unknown"
    market_gate_action: str = ""      # MARKET_ACTION_*
    market_gate_reason: str = ""      # ""|MARKET_GATE_WEAK_CHASE_BLOCK|MARKET_GATE_RISK_OFF


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
    # === Market regime snapshot (None 가능 — 미수신 시 _apply_market_gate 가 neutral fallback) ===
    market_state: Optional[MarketSnapshot] = None


def turnover_speed_per_min(ctx: EntryContext) -> float:
    """Return real-time traded value speed as KRW per minute."""
    if ctx.current_price <= 0 or ctx.volume_speed <= 0:
        return 0.0
    return float(ctx.volume_speed) * float(ctx.current_price) * 60.0


def _hhmmss_from_ts(ts: float) -> int:
    try:
        return int(time.strftime("%H%M%S", time.localtime(float(ts))))
    except (TypeError, ValueError, OSError):
        return 0


def has_recent_pullback_structure(minute_bars: Sequence[MinuteBar], *, lookback: int = 8) -> bool:
    """최근 1분봉에 눌림 후 회복 구조가 있으면 장중 과열 기준 완화 대상으로 본다."""
    recent = list(minute_bars[-lookback:]) if minute_bars else []
    if len(recent) < 2:
        return False

    for idx in range(len(recent) - 1, 0, -1):
        prev = recent[idx - 1]
        cur = recent[idx]
        if (
            prev.open > 0
            and prev.close > 0
            and cur.open > 0
            and cur.close > 0
            and prev.close < prev.open
            and cur.close > cur.open
        ):
            return True

    highs = [bar.high for bar in recent if bar.high > 0]
    if not highs:
        return False
    recent_high = max(highs)
    current = recent[-1].close
    if recent_high <= 0 or current <= 0:
        return False
    pullback = (recent_high - current) / recent_high
    return PULLBACK_MIN_PCT <= pullback <= MAX_DRAWDOWN_FROM_HIGH


def overheated_open_return_limit(ctx: EntryContext) -> float:
    """시간대별 시가 대비 과열 기준. 장중 완화는 눌림 구조가 있을 때만 적용한다."""
    now = _hhmmss_from_ts(ctx.now_ts)
    if now < 93000:
        return OVERHEATED_OPEN_RETURN
    if now < 110000:
        scheduled_limit = OVERHEATED_OPEN_RETURN_MORNING
    elif now < 140000:
        scheduled_limit = OVERHEATED_OPEN_RETURN_MIDDAY
    else:
        scheduled_limit = OVERHEATED_OPEN_RETURN_LATE
    if scheduled_limit > OVERHEATED_OPEN_RETURN and not has_recent_pullback_structure(ctx.minute_bars):
        return OVERHEATED_OPEN_RETURN
    return scheduled_limit


def _apply_market_gate(decision: EntryDecision, ctx: EntryContext) -> EntryDecision:
    """매크로 regime 에 따라 decision 의 dry-run 메타 3개만 채워 반환.

    1차 PR 에서는 status/ratio/grade/reason_code 를 절대 건드리지 않는다.
    실제 매수 행동은 변경되지 않으며, ready/shadow/trade_log CSV 에 메타가 기록되어
    표본 누적 후 다음 PR 에서 정책 승격 여부를 결정한다.

    정책:
        - strong/neutral: action=dry_run_allow, reason=""
        - weak: A급 0봉 추격(READY_AGRADE_FIRST) 만 dry_run_block_chase_only,
                그 외(B급 풀백/Stage2 본진입/wait/blocked) 는 dry_run_allow
        - risk_off: 모든 분기에서 dry_run_block_all
        - unknown 또는 ctx.market_state 미수신: neutral 로 fallback → dry_run_allow
    """
    snap = ctx.market_state
    if snap is None:
        regime = REGIME_NEUTRAL
    else:
        regime = snap.market_regime or REGIME_UNKNOWN
        if regime == REGIME_UNKNOWN:
            regime = REGIME_NEUTRAL

    decision.market_regime = regime

    if regime == REGIME_RISK_OFF:
        decision.market_gate_action = MARKET_ACTION_BLOCK_ALL
        decision.market_gate_reason = MARKET_GATE_RISK_OFF
        return decision

    if regime == REGIME_WEAK and decision.reason_code == READY_AGRADE_FIRST:
        decision.market_gate_action = MARKET_ACTION_BLOCK_CHASE_ONLY
        decision.market_gate_reason = MARKET_GATE_WEAK_CHASE_BLOCK
        return decision

    decision.market_gate_action = MARKET_ACTION_ALLOW
    decision.market_gate_reason = ""
    return decision


def evaluate_first_entry(ctx: EntryContext) -> EntryDecision:
    """공개 API 래퍼. 내부 평가 후 매크로 dry-run 메타를 부여해 반환."""
    return _apply_market_gate(_evaluate_first_entry_inner(ctx), ctx)


def _evaluate_first_entry_inner(ctx: EntryContext) -> EntryDecision:
    """신규 종목(entry_stage==0) 평가. A급(0봉 돌파)/B급(1봉 돌파만) 으로 분기.

    - A급: 0봉전 4개 상한선 동시 돌파 + 모든 게이트 통과 → 매수 없이 감시 시작(stage=1 wait)
    - B급: 1봉전 동시 돌파만 + 1분봉 첫 눌림+양봉 반전 + 게이트 통과 → 본진입 100%(stage=2)
    - 둘 다 아니면 wait

    공통 게이트:
      관찰시간/틱수/스프레드/거래속도/체결강도(120↑ 또는 100~120 + 추세 상승)/
      5분봉 캐시 충분/추세 필터/가짜돌파(윗꼬리)/과열(시가대비, BB55 거리)
    """
    if ctx.position is not None and ctx.position.entry_stage > 0:
        return EntryDecision(
            "blocked", 0.0, 1, "이미 진입 완료",
            reason_code=GATE_ALREADY_ENTERED,
        )
    if ctx.current_price <= 0 or ctx.ask <= 0 or ctx.bid <= 0:
        return EntryDecision(
            "wait", 0.0, 1, "가격/호가 데이터 부족",
            reason_code=GATE_PRICE_DATA,
        )
    if ctx.spread_rate < 0 or ctx.spread_rate > MAX_SPREAD_RATE:
        return EntryDecision(
            "blocked", 0.0, 1, "스프레드 과다 {:.2%}".format(ctx.spread_rate),
            reason_code=GATE_SPREAD,
        )
    if ctx.tick_count < DANTE_MIN_TICKS:
        return EntryDecision(
            "wait", 0.0, 1, "실시간 틱 부족 {}/{}".format(ctx.tick_count, DANTE_MIN_TICKS),
            reason_code=GATE_TICKS_INSUFFICIENT,
        )

    elapsed = ctx.now_ts - (ctx.condition_registered_at or ctx.now_ts)
    if elapsed < DANTE_MIN_OBSERVATION_SECONDS:
        return EntryDecision(
            "wait", 0.0, 1,
            "조건편입 관찰 {:.0f}/{}초".format(elapsed, DANTE_MIN_OBSERVATION_SECONDS),
            reason_code=GATE_OBSERVATION_SHORT,
        )

    turnover_speed = turnover_speed_per_min(ctx)
    if turnover_speed < MIN_TURNOVER_SPEED_PER_MIN:
        return EntryDecision(
            "wait", 0.0, 1,
            "거래속도(거래대금) 부족 {:.1f}백만원/분 < {:.1f}백만원/분 ({:.0f}주/초)".format(
                turnover_speed / 1_000_000,
                MIN_TURNOVER_SPEED_PER_MIN / 1_000_000,
                ctx.volume_speed,
            ),
            reason_code=GATE_VOLUME_SPEED,
        )

    # === 체결강도 강화 게이트 ===
    # Hard(120) 이상이면 무조건 통과, Soft~Hard(100~120) 사이는 추세 상승 시만 통과,
    # Soft(100) 미만이면 차단. chejan_strength == 0 (데이터 미수신) 은 일단 통과.
    if ctx.chejan_strength > 0:
        if ctx.chejan_strength < MIN_CHEJAN_STRENGTH_SOFT:
            return EntryDecision(
                "wait", 0.0, 1,
                "체결강도 부족 {:.1f} < {}".format(ctx.chejan_strength, MIN_CHEJAN_STRENGTH_SOFT),
                reason_code=GATE_CHEJAN_SOFT,
            )
        if ctx.chejan_strength < MIN_CHEJAN_STRENGTH_HARD:
            if not _chejan_strength_rising(ctx.chejan_strength_history, MIN_CHEJAN_STRENGTH_SOFT):
                return EntryDecision(
                    "wait", 0.0, 1,
                    "체결강도 약함 {:.1f} (상승 미확인, Hard {} 미만)".format(
                        ctx.chejan_strength, MIN_CHEJAN_STRENGTH_HARD
                    ),
                    reason_code=GATE_CHEJAN_HARD_NO_TREND,
                )

    # === 5분봉 추세 필터 / 돌파 등급 판정에 캐시 필수 ===
    if ctx.five_min_ind is None or ctx.five_min_ind.closes_count < 13:
        return EntryDecision(
            "wait", 0.0, 1, "5분봉 캐시 미준비",
            reason_code=GATE_FIVEMIN_CACHE,
        )
    if not ctx.five_min_ind.trend_up(ctx.current_price):
        return EntryDecision(
            "wait", 0.0, 1,
            "5분봉 추세 미통과 (현재 {} < Env13 {} / BB55 {})".format(
                ctx.current_price,
                int(ctx.five_min_ind.env_upper_13_25 or 0),
                int(ctx.five_min_ind.bb_upper_55_2 or 0),
            ),
            reason_code=GATE_TREND_FILTER,
        )

    # === 가짜 돌파 게이트 (5분봉 진행봉 윗꼬리) ===
    if ctx.upper_wick_ratio_zero_bar > MAX_UPPER_WICK_RATIO:
        return EntryDecision(
            "wait", 0.0, 1,
            "5분봉 윗꼬리 과다 {:.0%} > {:.0%}".format(
                ctx.upper_wick_ratio_zero_bar, MAX_UPPER_WICK_RATIO
            ),
            reason_code=GATE_UPPER_WICK,
        )

    # === 과열 게이트 ===
    open_return_limit = overheated_open_return_limit(ctx)
    if ctx.open_return > open_return_limit:
        return EntryDecision(
            "blocked", 0.0, 1,
            "시가 대비 과열 {:.1%} > {:.1%}".format(ctx.open_return, open_return_limit),
            reason_code=GATE_OVERHEAT_OPEN,
        )
    if ctx.px_over_bb55_pct > OVERHEATED_BB55_DISTANCE:
        return EntryDecision(
            "blocked", 0.0, 1,
            "BB55 대비 과열 +{:.1%} > {:.1%}".format(
                ctx.px_over_bb55_pct, OVERHEATED_BB55_DISTANCE
            ),
            reason_code=GATE_OVERHEAT_BB55,
        )

    # === A급 / B급 분기 ===
    if ctx.is_breakout_zero_bar:
        return EntryDecision(
            "wait", 0.0, 1,
            "A급 0봉 돌파 감시 시작(즉시 매수 없음)",
            grade="A",
            reason_code=WATCH_AGRADE_BREAKOUT,
        )

    if ctx.is_breakout_prev_bar:
        # B급: 추격 안 하고 1분봉 첫 눌림 + 양봉 반전 시 한 번에 본진입(100%)
        return _evaluate_b_grade_pullback(ctx)

    return EntryDecision(
        "wait", 0.0, 1, "0봉/1봉 동시 돌파 미확인",
        reason_code=GATE_NO_BREAKOUT,
    )


def _evaluate_b_grade_pullback(ctx: EntryContext) -> EntryDecision:
    """B급(1봉전 돌파만) 종목의 첫 눌림 본진입 평가.

    breakout_high 가 없으므로 1분봉의 최근 N개 봉 high 를 기준 고점으로 사용.
    조건: 눌림 -0.4~-1.5% + 1~2 음봉 후 양봉 반전.
    통과 시 ratio=1.0, stage=2 로 한 번에 매수(이후 추가매수 없음).
    """
    bars = ctx.minute_bars
    if not bars:
        return EntryDecision(
            "wait", 0.0, 1, "B급: 1분봉 미수신",
            reason_code=GATE_BGRADE_NO_MINUTE_BARS,
        )

    recent = bars[-min(len(bars), 10):]
    high_since = max((b.high for b in recent if b.high > 0), default=0)
    if high_since <= 0:
        return EntryDecision(
            "wait", 0.0, 1, "B급: 1분봉 고점 데이터 없음",
            reason_code=GATE_BGRADE_NO_HIGH,
        )

    pullback_pct = (high_since - ctx.current_price) / high_since
    if pullback_pct > MAX_DRAWDOWN_FROM_HIGH:
        return EntryDecision(
            "blocked", 0.0, 1, "B급: 고점 대비 -{:.2%} 초과".format(pullback_pct),
            reason_code=GATE_BGRADE_DRAWDOWN,
        )
    if pullback_pct < PULLBACK_MIN_PCT:
        return EntryDecision(
            "wait", 0.0, 1,
            "B급: 눌림 부족 ({:.2%} < {:.2%})".format(pullback_pct, PULLBACK_MIN_PCT),
            reason_code=GATE_BGRADE_PULLBACK_SHALLOW,
        )
    if pullback_pct > PULLBACK_MAX_PCT:
        return EntryDecision(
            "wait", 0.0, 1,
            "B급: 눌림 깊음 ({:.2%} > {:.2%})".format(pullback_pct, PULLBACK_MAX_PCT),
            reason_code=GATE_BGRADE_PULLBACK_DEEP,
        )

    if not _has_neg_then_positive_pattern(
        bars,
        neg_min=PULLBACK_NEG_BARS_MIN,
        neg_max=PULLBACK_NEG_BARS_MAX,
        reference_high=high_since,
        min_low_pullback_pct=PULLBACK_MIN_PCT,
    ):
        return EntryDecision(
            "wait", 0.0, 1, "B급: 음봉→양봉 반전 미확인",
            reason_code=GATE_BGRADE_NO_REVERSAL,
        )

    return EntryDecision(
        "ready", DANTE_GRADE_B_RATIO, 2,
        "B급 첫 눌림 본진입 (눌림 {:.2%}, {:.0%})".format(
            pullback_pct, DANTE_GRADE_B_RATIO
        ),
        grade="B",
        reason_code=READY_BGRADE_PULLBACK,
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
    """공개 API 래퍼. 내부 평가 후 매크로 dry-run 메타를 부여해 반환."""
    return _apply_market_gate(_evaluate_second_entry_inner(ctx), ctx)


def evaluate_a_grade_watch_entry(
    ctx: EntryContext,
    *,
    breakout_high: int,
    watch_started_at: float,
    pullback_window_deadline: float,
) -> EntryDecision:
    """Evaluate an A-grade breakout that is being watched without a first buy."""
    return _apply_market_gate(
        _evaluate_a_grade_watch_entry_inner(
            ctx,
            breakout_high=breakout_high,
            watch_started_at=watch_started_at,
            pullback_window_deadline=pullback_window_deadline,
        ),
        ctx,
    )


def _evaluate_a_grade_watch_entry_inner(
    ctx: EntryContext,
    *,
    breakout_high: int,
    watch_started_at: float,
    pullback_window_deadline: float,
) -> EntryDecision:
    if pullback_window_deadline > 0 and ctx.now_ts > pullback_window_deadline:
        return EntryDecision(
            "blocked",
            0.0,
            2,
            "A-watch window expired ({:.0f}s)".format(
                ctx.now_ts - (watch_started_at or ctx.now_ts)
            ),
            grade="A",
            reason_code=GATE_STAGE2_WINDOW_EXPIRED,
        )
    if ctx.current_price <= 0 or ctx.ask <= 0 or ctx.bid <= 0:
        return EntryDecision(
            "wait", 0.0, 2, "A-watch price/quote data missing",
            grade="A",
            reason_code=GATE_STAGE2_PRICE_DATA,
        )
    if ctx.spread_rate < 0 or ctx.spread_rate > MAX_SPREAD_RATE:
        return EntryDecision(
            "wait", 0.0, 2, "A-watch spread too wide {:.2%}".format(ctx.spread_rate),
            grade="A",
            reason_code=GATE_STAGE2_SPREAD,
        )
    if ctx.chejan_strength > 0 and ctx.chejan_strength < MIN_CHEJAN_STRENGTH:
        return EntryDecision(
            "wait", 0.0, 2,
            "A-watch chejan weak {:.1f} < {}".format(ctx.chejan_strength, MIN_CHEJAN_STRENGTH),
            grade="A",
            reason_code=GATE_STAGE2_CHEJAN,
        )
    turnover_speed = turnover_speed_per_min(ctx)
    if turnover_speed < MIN_TURNOVER_SPEED_PER_MIN * 0.5:
        return EntryDecision(
            "wait", 0.0, 2,
            "A-watch 거래속도(거래대금) 약화 {:.1f}백만원/분".format(turnover_speed / 1_000_000),
            grade="A",
            reason_code=GATE_STAGE2_VOLUME,
        )
    if breakout_high <= 0:
        return EntryDecision(
            "wait", 0.0, 2, "A-watch breakout high missing",
            grade="A",
            reason_code=GATE_STAGE2_HIGH_DATA,
        )

    pullback_pct = (breakout_high - ctx.current_price) / breakout_high
    if pullback_pct > MAX_DRAWDOWN_FROM_HIGH:
        return EntryDecision(
            "blocked", 0.0, 2,
            "A-watch drawdown from high exceeded {:.2%}".format(pullback_pct),
            grade="A",
            reason_code=GATE_STAGE2_DRAWDOWN,
        )
    if pullback_pct < PULLBACK_MIN_PCT:
        return EntryDecision(
            "wait", 0.0, 2,
            "A-watch pullback shallow ({:.2%} < {:.2%})".format(pullback_pct, PULLBACK_MIN_PCT),
            grade="A",
            reason_code=GATE_STAGE2_PULLBACK_SHALLOW,
        )
    if pullback_pct > PULLBACK_MAX_PCT:
        return EntryDecision(
            "wait", 0.0, 2,
            "A-watch pullback deep ({:.2%} > {:.2%})".format(pullback_pct, PULLBACK_MAX_PCT),
            grade="A",
            reason_code=GATE_STAGE2_PULLBACK_DEEP,
        )
    if not _has_neg_then_positive_pattern(
        ctx.minute_bars,
        neg_min=PULLBACK_NEG_BARS_MIN,
        neg_max=PULLBACK_NEG_BARS_MAX,
        reference_high=breakout_high,
        min_low_pullback_pct=PULLBACK_MIN_PCT,
    ):
        return EntryDecision(
            "wait", 0.0, 2, "A-watch reversal not confirmed",
            grade="A",
            reason_code=GATE_STAGE2_NO_REVERSAL,
        )

    return EntryDecision(
        "ready",
        1.0,
        2,
        "A-watch first pullback entry (pullback {:.2%}, 100%)".format(pullback_pct),
        grade="A",
        reason_code=READY_AGRADE_SECOND,
    )


def _evaluate_second_entry_inner(ctx: EntryContext) -> EntryDecision:
    """2차(본진입) 가능 여부 평가. position.entry_stage == 1 인 종목에만 적용."""
    pos = ctx.position
    if pos is None or pos.entry_stage != 1:
        return EntryDecision(
            "blocked", 0.0, 2, "1차 미체결 또는 본진입 완료",
            reason_code=GATE_STAGE2_NO_FIRST,
        )

    deadline = pos.pullback_window_deadline
    if deadline > 0 and ctx.now_ts > deadline:
        return EntryDecision(
            "blocked",
            0.0,
            2,
            "본진입 윈도우 만료(1차 후 {:.0f}초)".format(
                ctx.now_ts - (pos.entry1_time or ctx.now_ts)
            ),
            reason_code=GATE_STAGE2_WINDOW_EXPIRED,
        )

    if ctx.current_price <= 0 or ctx.ask <= 0 or ctx.bid <= 0:
        return EntryDecision(
            "wait", 0.0, 2, "가격/호가 데이터 부족",
            reason_code=GATE_STAGE2_PRICE_DATA,
        )
    if ctx.spread_rate < 0 or ctx.spread_rate > MAX_SPREAD_RATE:
        return EntryDecision(
            "wait", 0.0, 2, "스프레드 과다 {:.2%}".format(ctx.spread_rate),
            reason_code=GATE_STAGE2_SPREAD,
        )

    if ctx.chejan_strength > 0 and ctx.chejan_strength < MIN_CHEJAN_STRENGTH:
        return EntryDecision(
            "wait",
            0.0,
            2,
            "체결강도 약화 {:.1f} < {}".format(ctx.chejan_strength, MIN_CHEJAN_STRENGTH),
            reason_code=GATE_STAGE2_CHEJAN,
        )

    turnover_speed = turnover_speed_per_min(ctx)
    if turnover_speed < MIN_TURNOVER_SPEED_PER_MIN * 0.5:
        return EntryDecision(
            "wait",
            0.0,
            2,
            "거래속도(거래대금) 약화 {:.1f}백만원/분".format(turnover_speed / 1_000_000),
            reason_code=GATE_STAGE2_VOLUME,
        )

    breakout_high = pos.breakout_high or pos.entry_price
    if breakout_high <= 0:
        return EntryDecision(
            "wait", 0.0, 2, "고점 추적 데이터 부족",
            reason_code=GATE_STAGE2_HIGH_DATA,
        )
    pullback_pct = (breakout_high - ctx.current_price) / breakout_high

    if pullback_pct > MAX_DRAWDOWN_FROM_HIGH:
        return EntryDecision(
            "blocked",
            0.0,
            2,
            "고점 대비 -{:.2%} 초과(차단)".format(pullback_pct),
            reason_code=GATE_STAGE2_DRAWDOWN,
        )
    if pullback_pct < PULLBACK_MIN_PCT:
        return EntryDecision(
            "wait",
            0.0,
            2,
            "눌림 부족 ({:.2%} < {:.2%})".format(pullback_pct, PULLBACK_MIN_PCT),
            reason_code=GATE_STAGE2_PULLBACK_SHALLOW,
        )
    if pullback_pct > PULLBACK_MAX_PCT:
        return EntryDecision(
            "wait",
            0.0,
            2,
            "눌림 깊음 ({:.2%} > {:.2%})".format(pullback_pct, PULLBACK_MAX_PCT),
            reason_code=GATE_STAGE2_PULLBACK_DEEP,
        )

    if not _has_neg_then_positive_pattern(
        ctx.minute_bars,
        neg_min=PULLBACK_NEG_BARS_MIN,
        neg_max=PULLBACK_NEG_BARS_MAX,
        reference_high=breakout_high,
        min_low_pullback_pct=PULLBACK_MIN_PCT,
    ):
        return EntryDecision(
            "wait", 0.0, 2, "음봉→양봉 반전 미확인",
            reason_code=GATE_STAGE2_NO_REVERSAL,
        )

    return EntryDecision(
        "ready",
        DANTE_SECOND_ENTRY_RATIO,
        2,
        "A급 본진입 (눌림 {:.2%}, {:.0%})".format(pullback_pct, DANTE_SECOND_ENTRY_RATIO),
        grade="A",
        reason_code=READY_AGRADE_SECOND,
    )


def should_lock_single_position(ctx: EntryContext) -> bool:
    """1차 후 윈도우 안에 눌림이 안 오면 본진입을 포기하고 단일 포지션으로 잠근다."""
    pos = ctx.position
    if pos is None or pos.entry_stage != 1:
        return False
    if pos.pullback_window_deadline <= 0:
        return False
    return ctx.now_ts > pos.pullback_window_deadline


def compute_pullback_anchor(
    bars: Sequence[MinuteBar],
    *,
    breakout_high_hint: int = 0,
    lookback: int = 15,
) -> Tuple[int, int, bool]:
    """Locate ``(high, low_after_high, valid)`` within the most recent bars.

    - ``high``: 최근 ``lookback`` 개 봉 중 최고 ``high``.
      ``breakout_high_hint`` 가 더 크면 그것을 사용하고, ``i_high`` 는 lookback
      바깥에서 형성된 고점으로 간주(=lookback 전체를 high 이후 구간으로 본다).
    - ``low``: ``i_high`` 이후 봉들의 최저 ``low``.
      이 정의로 "high 형성 → 풀백 → 회복" 시퀀스만 유효하다고 인정하며,
      과거 저점이 우연히 더 낮은 케이스(상승 추세 중)는 valid=False 로 거른다.
    - ``valid``: high/low 가 모두 양수이고 ``low < high`` 인 경우만 True.

    bars 가 비거나 의미 있는 high/low 가 없으면 ``(0, 0, False)``.
    """
    if not bars:
        return 0, 0, False
    recent = list(bars[-lookback:])
    valid_highs = [
        (idx, int(getattr(bar, "high", 0) or 0))
        for idx, bar in enumerate(recent)
    ]
    valid_highs = [(idx, h) for idx, h in valid_highs if h > 0]
    if not valid_highs:
        return 0, 0, False
    i_high, bar_high = max(valid_highs, key=lambda item: item[1])

    if breakout_high_hint > bar_high:
        # hint 가 lookback 바깥에서 형성된 더 높은 고점 — recent 전체를 high 이후로 본다.
        bar_high = breakout_high_hint
        i_high = -1

    # high 가 발생한 봉 *자체* 의 low 는 풀백 산출에서 제외(low→high 인지 high→low 인지
    # 분간 불가). high 봉 *이후* 봉들의 low 만 풀백으로 인정.
    after_bars = recent if i_high < 0 else recent[i_high + 1:]
    valid_lows = [int(getattr(bar, "low", 0) or 0) for bar in after_bars]
    valid_lows = [low for low in valid_lows if low > 0]
    if not valid_lows:
        return bar_high, 0, False
    low = min(valid_lows)
    if low >= bar_high:
        return bar_high, low, False
    return bar_high, low, True


def _has_neg_then_positive_pattern(
    bars: List[MinuteBar],
    *,
    neg_min: int,
    neg_max: int,
    reference_high: int = 0,
    min_low_pullback_pct: float = 0.0,
) -> bool:
    """Confirm a positive reversal after a real pullback.

    If zero completed negative bars are allowed, require the current/recent low
    to have touched the pullback zone so a plain green continuation bar does not
    pass as a pullback reversal.
    """
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
    if neg_min <= neg <= neg_max and neg > 0:
        return True
    if neg != 0 or neg_min > 0:
        return False
    if reference_high <= 0 or min_low_pullback_pct <= 0:
        return True

    recent = bars[-min(len(bars), 3):]
    recent_low = min((bar.low for bar in recent if bar.low > 0), default=0)
    if recent_low <= 0:
        return False
    low_pullback_pct = (reference_high - recent_low) / reference_high
    return low_pullback_pct >= min_low_pullback_pct and cur.close > recent_low


def evaluate_reentry_after_exit(ctx: EntryContext, watch: dict) -> EntryDecision:
    """Evaluate a same-day re-entry after a completed profitable exit."""
    if not isinstance(watch, dict):
        return EntryDecision("blocked", 0.0, 2, "re-entry watch missing")

    deadline = float(watch.get("deadline", 0) or 0)
    if deadline > 0 and ctx.now_ts > deadline:
        return EntryDecision(
            "blocked",
            0.0,
            2,
            "re-entry watch expired",
            reason_code=GATE_STAGE2_WINDOW_EXPIRED,
        )

    if ctx.position is not None and (ctx.position.is_holding() or ctx.position.is_pending()):
        return EntryDecision(
            "blocked",
            0.0,
            2,
            "re-entry already has active position",
            reason_code=GATE_ALREADY_ENTERED,
        )

    if ctx.current_price <= 0 or ctx.ask <= 0 or ctx.bid <= 0:
        return EntryDecision("wait", 0.0, 2, "re-entry price/quote data missing")

    if ctx.spread_rate > MAX_SPREAD_RATE:
        return EntryDecision(
            "wait",
            0.0,
            2,
            "re-entry spread too wide {:.2%}".format(ctx.spread_rate),
            reason_code=GATE_STAGE2_SPREAD,
        )

    if ctx.chejan_strength < MIN_CHEJAN_STRENGTH:
        return EntryDecision(
            "wait",
            0.0,
            2,
            "re-entry chejan weak {:.1f} < {}".format(
                ctx.chejan_strength, MIN_CHEJAN_STRENGTH
            ),
            reason_code=GATE_STAGE2_CHEJAN,
        )

    turnover_speed = turnover_speed_per_min(ctx)
    if turnover_speed < MIN_TURNOVER_SPEED_PER_MIN:
        return EntryDecision(
            "wait",
            0.0,
            2,
            "re-entry 거래속도(거래대금) 약화 {:.1f}백만원/분".format(turnover_speed / 1_000_000),
            reason_code=GATE_VOLUME_SPEED,
        )

    breakout_high = int(watch.get("breakout_high", 0) or 0)
    entry_price = int(watch.get("entry_price", 0) or 0)
    pullback_low = int(watch.get("pullback_low", 0) or 0)
    if breakout_high <= 0 or entry_price <= 0 or pullback_low <= 0:
        return EntryDecision(
            "wait",
            0.0,
            2,
            "re-entry anchor data missing",
            reason_code=GATE_STAGE2_HIGH_DATA,
        )

    drop_from_high = (breakout_high - pullback_low) / breakout_high
    if drop_from_high < REENTRY_MIN_DROP_FROM_HIGH:
        return EntryDecision(
            "wait",
            0.0,
            2,
            "re-entry pullback shallow ({:.2%} < {:.2%})".format(
                drop_from_high, REENTRY_MIN_DROP_FROM_HIGH
            ),
            reason_code=GATE_STAGE2_PULLBACK_SHALLOW,
        )
    if drop_from_high > REENTRY_MAX_DROP_FROM_HIGH:
        return EntryDecision(
            "blocked",
            0.0,
            2,
            "re-entry pullback too deep ({:.2%} > {:.2%})".format(
                drop_from_high, REENTRY_MAX_DROP_FROM_HIGH
            ),
            reason_code=GATE_STAGE2_DRAWDOWN,
        )

    recovery_price = int(entry_price * (1 - REENTRY_RECOVERY_BUFFER_PCT))
    if ctx.current_price < recovery_price:
        return EntryDecision(
            "wait",
            0.0,
            2,
            "re-entry waiting recovery {} < {}".format(ctx.current_price, recovery_price),
            reason_code=GATE_STAGE2_NO_REVERSAL,
        )

    if not _has_neg_then_positive_pattern(
        list(ctx.minute_bars[-5:]) if ctx.minute_bars else [],
        neg_min=0,
        neg_max=3,
        reference_high=breakout_high,
        min_low_pullback_pct=REENTRY_MIN_DROP_FROM_HIGH,
    ):
        return EntryDecision(
            "wait",
            0.0,
            2,
            "re-entry reversal not confirmed",
            reason_code=GATE_STAGE2_NO_REVERSAL,
        )

    return _apply_market_gate(
        EntryDecision(
            "ready",
            REENTRY_RATIO,
            2,
            "same-day re-entry after pullback recovery (drop {:.2%}, {:.0%})".format(
                drop_from_high, REENTRY_RATIO
            ),
            grade="A",
            reason_code=READY_REENTRY_PULLBACK,
        ),
        ctx,
    )
