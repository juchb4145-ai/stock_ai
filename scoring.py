"""main.py와 ai_server.py에서 공용으로 사용하는 매수/매도 점수 로직.

main.py 내부의 score_opening_trade / score_exit_timing fallback 로직과
ai_server.py 의 fallback_entry / fallback_exit 가 동일한 가중치/매직넘버를 가지고
두 곳에 중복되어 있어, 어느 한쪽만 수정되면 silently 발산하는 문제가 있었다.
이 모듈에 한 번만 정의하고 양쪽에서 import해 사용한다.
"""

import math
from typing import Any, Dict, List, Optional, Sequence


# === 진입(매수) 점수 ===

# 학습 CSV 헤더와 동기화되는 피처 목록(추가 시 entry_training.csv 마이그레이션 필요).
# headroom 등 신규 파생 피처는 features dict에는 들어가지만 학습 컬럼에는 추가하지 않는다.
ENTRY_FEATURE_NAMES = (
    "price_momentum",
    "open_return",
    "box_position",
    "direction_score",
    "volume_speed",
    "spread_rate",
)

# 모멘텀(직전 첫 틱 대비 등락률) 보정 상수: ~2.4% 모멘텀이면 만점
ENTRY_MOMENTUM_SHIFT = 0.004
ENTRY_MOMENTUM_SCALE = 0.024
# 시가 대비 등락률 보정
ENTRY_OPEN_RETURN_SHIFT = 0.003
ENTRY_OPEN_RETURN_SCALE = 0.035
# 거래속도(주/초) 만점 기준
ENTRY_VOLUME_SPEED_FULL = 3000.0
# 잔여 상승 여력(headroom) 만점 기준: 최근 고가 대비 +1.5% 이상 여력이면 만점
ENTRY_HEADROOM_FULL = 0.015
# box_position 종형 가중치의 sweet spot(눌림 ~ 중상단)과 표준편차
ENTRY_BOX_OPTIMAL = 0.55
ENTRY_BOX_SIGMA = 0.18
# 가중치(합 = 1.0). 추격(box 상단)을 줄이고 잔여여력(headroom)을 키워 눌림목 매수 전략과 정합.
ENTRY_WEIGHT_MOMENTUM = 0.24
ENTRY_WEIGHT_OPEN_RETURN = 0.18
ENTRY_WEIGHT_BOX = 0.10
ENTRY_WEIGHT_DIRECTION = 0.16
ENTRY_WEIGHT_VOLUME = 0.10
ENTRY_WEIGHT_SPREAD = 0.06
ENTRY_WEIGHT_HEADROOM = 0.16
# score(0~1)을 기대수익률로 환산할 때 곱하는 진폭(데이터 기반 calibration이 없을 때 fallback)
ENTRY_EXPECTED_RETURN_AMP = 0.04
# 스프레드가 1틱 비용처럼 작용하므로 expected_return에서 추가로 차감하는 계수
ENTRY_SPREAD_PENALTY_MULT = 1.0


# === 청산(매도) 점수 ===

# 거래속도 만점 기준(매도 판단 시)
EXIT_VOLUME_SPEED_FULL = 2500.0
# 가중치
EXIT_WEIGHT_DIRECTION = 0.30
EXIT_WEIGHT_VOLUME = 0.20
EXIT_WEIGHT_HIGH_HOLD = 0.20
EXIT_WEIGHT_SPREAD = 0.10
EXIT_WEIGHT_PROFIT = 0.20
EXIT_WEIGHT_TIME_PENALTY = 0.20
EXIT_WEIGHT_DRAWDOWN_PENALTY = 0.25


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


# 한국 주식 호가단위(틱사이즈, 2023-01-25 개정 기준).
# (가격 상한, 호가단위) — 가격 상한 미만이면 해당 호가단위.
_TICK_SIZE_TABLE = (
    (2_000, 1),
    (5_000, 5),
    (20_000, 10),
    (50_000, 50),
    (200_000, 100),
    (500_000, 500),
    (math.inf, 1_000),
)


def tick_size(price: float) -> int:
    """가격대별 호가단위(원)를 반환한다. 비정상 입력은 1원으로 보수적으로 처리."""
    if price is None or price <= 0:
        return 1
    for upper, unit in _TICK_SIZE_TABLE:
        if price < upper:
            return unit
    return 1_000


def round_up_to_tick(price: float) -> int:
    """가격을 해당 가격대의 호가단위로 올림 처리한다."""
    if price is None or price <= 0:
        return 0
    unit = tick_size(price)
    return int(math.ceil(price / unit) * unit)


def gaussian_score(value: float, optimal: float, sigma: float) -> float:
    """optimal 부근에서 1, 멀어질수록 0에 가까워지는 종형 점수."""
    if sigma <= 0:
        return 0.0
    z = (value - optimal) / sigma
    return math.exp(-0.5 * z * z)


def build_entry_features(
    ticks: List[Dict],
    current_price: int,
    open_price: int,
    high: int,
    low: int,
    ask: int,
    bid: int,
) -> Optional[Dict[str, float]]:
    """실시간 틱과 호가/가격으로부터 진입 점수용 피처를 만든다.

    필요한 데이터가 부족하면 None을 반환한다.
    """
    if not ticks:
        return None
    first = ticks[0]
    last = ticks[-1]
    if current_price <= 0 or open_price <= 0 or high <= low or ask <= 0 or bid <= 0:
        return None

    spread_rate = (ask - bid) / current_price
    elapsed = max(last["received_at"] - first["received_at"], 1)
    price_momentum = current_price / first["close"] - 1 if first["close"] > 0 else 0
    open_return = current_price / open_price - 1
    box_position = (current_price - low) / (high - low) if high > low else 0.5

    recent_ticks = ticks[-min(5, len(ticks)):]
    up_count = sum(
        1 for prev, cur in zip(recent_ticks, recent_ticks[1:])
        if cur["close"] > prev["close"]
    )
    direction_score = up_count / max(len(recent_ticks) - 1, 1)

    volume_delta = max(last["accum_volume"] - first["accum_volume"], 0)
    volume_speed = volume_delta / elapsed

    # 잔여 상승 여력(headroom): 최근 고가 대비 현재가가 얼마나 떨어져 있는지(눌림 정도).
    # 0이면 고가 추격, 양수가 클수록 눌림이 깊다. headroom_score는 0~1로 정규화한다.
    headroom = (high - current_price) / current_price if current_price > 0 else 0.0
    return {
        "price_momentum": price_momentum,
        "open_return": open_return,
        "box_position": box_position,
        "direction_score": direction_score,
        "volume_speed": volume_speed,
        "spread_rate": spread_rate,
        "headroom": headroom,
    }


def compute_entry_score(features: Dict[str, float], opening_max_spread_rate: float) -> float:
    """피처 dict로부터 0~1 사이의 진입 점수를 계산한다.

    box_position은 종형 가중치(0.55 부근이 최대)로 바꿔 고점 추격을 막고,
    headroom(잔여 상승 여력)을 추가해 눌림 구간을 선호하도록 한다.
    """
    momentum_score = clamp((features["price_momentum"] + ENTRY_MOMENTUM_SHIFT) / ENTRY_MOMENTUM_SCALE)
    open_return_score = clamp((features["open_return"] + ENTRY_OPEN_RETURN_SHIFT) / ENTRY_OPEN_RETURN_SCALE)
    box_score = gaussian_score(features["box_position"], ENTRY_BOX_OPTIMAL, ENTRY_BOX_SIGMA)
    spread_score = clamp(1 - features["spread_rate"] / opening_max_spread_rate) if opening_max_spread_rate > 0 else 0.0
    volume_score = clamp(features["volume_speed"] / ENTRY_VOLUME_SPEED_FULL)
    headroom_score = clamp(features.get("headroom", 0.0) / ENTRY_HEADROOM_FULL)

    return (
        momentum_score * ENTRY_WEIGHT_MOMENTUM
        + open_return_score * ENTRY_WEIGHT_OPEN_RETURN
        + box_score * ENTRY_WEIGHT_BOX
        + features["direction_score"] * ENTRY_WEIGHT_DIRECTION
        + volume_score * ENTRY_WEIGHT_VOLUME
        + spread_score * ENTRY_WEIGHT_SPREAD
        + headroom_score * ENTRY_WEIGHT_HEADROOM
    )


def calibrated_return_from_score(
    score: float,
    calibration: Optional[Sequence[Dict[str, float]]],
) -> Optional[float]:
    """학습 데이터 기반 score→평균 return_10m 매핑 테이블에서 보간된 기대수익률을 구한다.

    calibration 형식: [{"score": 0.55, "return": 0.004, "count": 23}, ...] (score 오름차순)
    데이터 부족 구간(count<5)은 calibration에서 제외되어 있다고 가정.
    적용할 항목이 없으면 None을 반환해 호출 측이 fallback을 쓰도록 한다.
    """
    if not calibration:
        return None
    points = [(p["score"], p["return"]) for p in calibration if p.get("count", 0) >= 1]
    if not points:
        return None
    if score <= points[0][0]:
        return float(points[0][1])
    if score >= points[-1][0]:
        return float(points[-1][1])
    for (s0, r0), (s1, r1) in zip(points, points[1:]):
        if s0 <= score <= s1:
            if s1 == s0:
                return float(r0)
            ratio = (score - s0) / (s1 - s0)
            return float(r0 + (r1 - r0) * ratio)
    return float(points[-1][1])


def expected_return_from_score(
    score: float,
    features: Optional[Dict[str, float]] = None,
    opening_max_spread_rate: float = 0.0,
    calibration: Optional[Sequence[Dict[str, float]]] = None,
) -> float:
    """score(0~1)을 기대수익률로 환산한다.

    - calibration 테이블이 있으면 score→평균 return 매핑을 사용한다.
    - 없으면 (score-0.5)*amp 의 기존 선형 매핑을 fallback으로 사용한다.
    - features와 opening_max_spread_rate가 주어지면 스프레드 비용을 추가로 차감한다.
    """
    base = calibrated_return_from_score(score, calibration)
    if base is None:
        base = (score - 0.5) * ENTRY_EXPECTED_RETURN_AMP

    if features is not None:
        spread_rate = max(float(features.get("spread_rate", 0.0)), 0.0)
        # 왕복 호가 비용 근사: 매수/매도에서 각각 절반의 스프레드를 부담한다고 가정.
        base -= spread_rate * ENTRY_SPREAD_PENALTY_MULT
    return base


def compute_target_price(
    current_price: int,
    expected_return: float,
    take_profit_rate: float,
) -> int:
    """기대수익률을 take_profit 범위로 캡한 뒤, 가격대별 호가단위로 올림한다."""
    target_return = min(max(expected_return, take_profit_rate * 0.6), take_profit_rate)
    raw = current_price * (1 + target_return)
    rounded = round_up_to_tick(raw)
    if rounded <= current_price:
        rounded = current_price + tick_size(current_price)
    return rounded


# =====================================================================
# 단테 추세전략(Phase A) 학습 트랙용 피처 정의.
#
# Phase A 는 데이터 수집만 활성화하므로 모델 학습/추론에는 아직 쓰이지 않는다.
# Phase B 에서 train_dante_lgbm.py 가 같은 헤더를 읽어 모델을 학습한다.
# 컬럼 순서는 학습 코드와의 단일 source of truth 이므로 신중히 변경한다.
# =====================================================================

DANTE_ENTRY_FEATURE_NAMES = (
    "chejan_strength",         # 체결강도(% 단위, 100 이상이면 매수 우위)
    "volume_speed",            # 거래속도(주/초)
    "spread_rate",             # (ask-bid)/현재가
    "obs_elapsed_sec",         # 조건편입 후 경과 초
    "px_over_env13_pct",       # (현재가 / Envelope(13,2.5) 상단) - 1
    "px_over_bb55_pct",        # (현재가 / BB(55,2) 상단) - 1
    "five_min_closes_count",   # 5분봉 캐시 종가 개수(부족하면 추세필터 신뢰도 낮음)
    "pullback_pct_from_high",  # (breakout_high - 현재가) / breakout_high (1차 후 갱신된 고점 대비)
    "neg_bars_streak",         # 진행봉 직전부터 연속된 1분 음봉 개수
    "cur_bar_is_positive",     # 진행봉이 양봉이면 1, 아니면 0
    # === 단테 등급/가짜돌파/과열 보강(이 헤더는 학습 코드와의 단일 source of truth) ===
    "breakout_grade_a",        # 0봉전 동시 돌파 (A급) 1, 아니면 0
    "breakout_grade_b",        # 1봉전 동시 돌파만 (B급) 1, 0봉전도 돌파했으면 0
    "chejan_strength_trend",   # 체결강도 history 의 (후반 평균 - 전반 평균). 양수면 우상향
    "upper_wick_ratio",        # 5분봉 진행봉 윗꼬리 비율 (0~1). 가짜 돌파 지표
    "open_return",             # (현재가 / 시가) - 1. 과열 지표
)


def build_dante_entry_features(
    *,
    current_price: int,
    chejan_strength: float,
    volume_speed: float,
    spread_rate: float,
    obs_elapsed_sec: float,
    env_upper_13: Optional[float],
    bb_upper_55: Optional[float],
    five_min_closes_count: int,
    breakout_high: int,
    minute_bars: Sequence[Any],
    chejan_strength_history: Optional[Sequence[float]] = None,
    is_breakout_zero_bar: bool = False,
    is_breakout_prev_bar: bool = False,
    upper_wick_ratio: float = 0.0,
    open_return: float = 0.0,
) -> Dict[str, float]:
    """단테 학습 트랙용 단일 샘플 피처를 만든다.

    minute_bars 는 ``open`` / ``close`` 속성을 가진 객체 시퀀스(예: bars.MinuteBar)이며
    가장 오래된 봉이 인덱스 0, 진행봉이 마지막에 위치한다고 가정한다.
    chejan_strength_history 의 앞 절반과 뒷 절반 평균 차이를 trend 피처로 사용한다.
    데이터가 비어있거나 0인 경우는 모두 0.0 으로 떨어뜨려 LightGBM 이 NaN 으로 인식하지 않게 한다.
    """
    if current_price and env_upper_13 and env_upper_13 > 0:
        px_over_env13 = current_price / env_upper_13 - 1
    else:
        px_over_env13 = 0.0

    if current_price and bb_upper_55 and bb_upper_55 > 0:
        px_over_bb55 = current_price / bb_upper_55 - 1
    else:
        px_over_bb55 = 0.0

    if breakout_high and breakout_high > 0:
        pullback_pct = (breakout_high - current_price) / breakout_high
    else:
        pullback_pct = 0.0

    neg_streak = 0
    cur_positive = 0
    if minute_bars:
        cur = minute_bars[-1]
        cur_open = getattr(cur, "open", 0)
        cur_close = getattr(cur, "close", 0)
        if cur_close > cur_open:
            cur_positive = 1
        for bar in reversed(list(minute_bars[:-1])):
            bar_open = getattr(bar, "open", 0)
            bar_close = getattr(bar, "close", 0)
            if bar_close < bar_open:
                neg_streak += 1
            else:
                break

    chejan_trend = 0.0
    if chejan_strength_history:
        history = list(chejan_strength_history)
        half = len(history) // 2
        if half > 0 and len(history) - half > 0:
            head = history[:half]
            tail = history[half:]
            chejan_trend = (sum(tail) / len(tail)) - (sum(head) / len(head))

    grade_a_flag = 1.0 if is_breakout_zero_bar else 0.0
    grade_b_flag = 1.0 if (is_breakout_prev_bar and not is_breakout_zero_bar) else 0.0

    return {
        "chejan_strength": float(chejan_strength or 0.0),
        "volume_speed": float(volume_speed or 0.0),
        "spread_rate": float(spread_rate or 0.0),
        "obs_elapsed_sec": float(max(obs_elapsed_sec, 0.0)),
        "px_over_env13_pct": float(px_over_env13),
        "px_over_bb55_pct": float(px_over_bb55),
        "five_min_closes_count": float(int(five_min_closes_count or 0)),
        "pullback_pct_from_high": float(pullback_pct),
        "neg_bars_streak": float(neg_streak),
        "cur_bar_is_positive": float(cur_positive),
        "breakout_grade_a": grade_a_flag,
        "breakout_grade_b": grade_b_flag,
        "chejan_strength_trend": float(chejan_trend),
        "upper_wick_ratio": float(max(0.0, min(1.0, upper_wick_ratio or 0.0))),
        "open_return": float(open_return or 0.0),
    }


def compute_exit_hold_score(
    *,
    ticks: List[Dict],
    current_price: int,
    profit_rate: float,
    trailing_drop: float,
    hold_seconds: float,
    opening_max_spread_rate: float,
    exit_min_profit_rate: float,
    exit_strong_profit_rate: float,
    exit_trailing_drop_rate: float,
    exit_stall_seconds: float,
    opening_max_hold_seconds: float,
) -> float:
    """청산 보유 점수(0~1). 0에 가까울수록 매도, 1에 가까울수록 보유."""
    recent_ticks = ticks[-min(8, len(ticks)):] if ticks else []
    direction_score = 0.5
    volume_score = 0.5
    high_hold_score = 0.5
    spread_score = 0.5

    if len(recent_ticks) >= 3:
        up_count = sum(
            1 for prev, cur in zip(recent_ticks, recent_ticks[1:])
            if cur["close"] >= prev["close"]
        )
        direction_score = up_count / max(len(recent_ticks) - 1, 1)

        first_recent = recent_ticks[0]
        last_recent = recent_ticks[-1]
        elapsed = max(last_recent["received_at"] - first_recent["received_at"], 1)
        volume_delta = max(last_recent["accum_volume"] - first_recent["accum_volume"], 0)
        volume_speed = volume_delta / elapsed
        volume_score = clamp(volume_speed / EXIT_VOLUME_SPEED_FULL)

        closes = [tick["close"] for tick in recent_ticks if tick["close"] > 0]
        if closes:
            recent_high = max(closes)
            recent_low = min(closes)
            if recent_high > recent_low:
                high_hold_score = clamp((current_price - recent_low) / (recent_high - recent_low))

        ask = last_recent.get("ask", 0)
        bid = last_recent.get("bid", 0)
        if ask > 0 and bid > 0 and current_price > 0 and opening_max_spread_rate > 0:
            spread_rate = (ask - bid) / current_price
            spread_score = clamp(1 - spread_rate / opening_max_spread_rate)

    profit_score = clamp(
        (profit_rate - exit_min_profit_rate)
        / max(exit_strong_profit_rate - exit_min_profit_rate, 1e-9)
    )
    time_penalty_window = max(opening_max_hold_seconds - exit_stall_seconds, 1)
    time_penalty = clamp((hold_seconds - exit_stall_seconds) / time_penalty_window)
    drawdown_penalty = clamp(abs(min(trailing_drop, 0)) / (exit_trailing_drop_rate * 2))

    hold_score = (
        direction_score * EXIT_WEIGHT_DIRECTION
        + volume_score * EXIT_WEIGHT_VOLUME
        + high_hold_score * EXIT_WEIGHT_HIGH_HOLD
        + spread_score * EXIT_WEIGHT_SPREAD
        + profit_score * EXIT_WEIGHT_PROFIT
        - time_penalty * EXIT_WEIGHT_TIME_PENALTY
        - drawdown_penalty * EXIT_WEIGHT_DRAWDOWN_PENALTY
    )
    return clamp(hold_score)
