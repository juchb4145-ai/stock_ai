"""main.py와 ai_server.py에서 공용으로 사용하는 매수/매도 점수 로직.

main.py 내부의 score_opening_trade / score_exit_timing fallback 로직과
ai_server.py 의 fallback_entry / fallback_exit 가 동일한 가중치/매직넘버를 가지고
두 곳에 중복되어 있어, 어느 한쪽만 수정되면 silently 발산하는 문제가 있었다.
이 모듈에 한 번만 정의하고 양쪽에서 import해 사용한다.
"""

from typing import Dict, List, Optional


# === 진입(매수) 점수 ===

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
# 가중치
ENTRY_WEIGHT_MOMENTUM = 0.28
ENTRY_WEIGHT_OPEN_RETURN = 0.20
ENTRY_WEIGHT_BOX = 0.18
ENTRY_WEIGHT_DIRECTION = 0.18
ENTRY_WEIGHT_VOLUME = 0.10
ENTRY_WEIGHT_SPREAD = 0.06
# score(0~1)을 기대수익률로 환산할 때 곱하는 진폭
ENTRY_EXPECTED_RETURN_AMP = 0.04


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
    return {
        "price_momentum": price_momentum,
        "open_return": open_return,
        "box_position": box_position,
        "direction_score": direction_score,
        "volume_speed": volume_speed,
        "spread_rate": spread_rate,
    }


def compute_entry_score(features: Dict[str, float], opening_max_spread_rate: float) -> float:
    """피처 dict로부터 0~1 사이의 진입 점수를 계산한다."""
    momentum_score = clamp((features["price_momentum"] + ENTRY_MOMENTUM_SHIFT) / ENTRY_MOMENTUM_SCALE)
    open_return_score = clamp((features["open_return"] + ENTRY_OPEN_RETURN_SHIFT) / ENTRY_OPEN_RETURN_SCALE)
    box_score = clamp(features["box_position"])
    spread_score = clamp(1 - features["spread_rate"] / opening_max_spread_rate) if opening_max_spread_rate > 0 else 0.0
    volume_score = clamp(features["volume_speed"] / ENTRY_VOLUME_SPEED_FULL)

    return (
        momentum_score * ENTRY_WEIGHT_MOMENTUM
        + open_return_score * ENTRY_WEIGHT_OPEN_RETURN
        + box_score * ENTRY_WEIGHT_BOX
        + features["direction_score"] * ENTRY_WEIGHT_DIRECTION
        + volume_score * ENTRY_WEIGHT_VOLUME
        + spread_score * ENTRY_WEIGHT_SPREAD
    )


def expected_return_from_score(score: float) -> float:
    return (score - 0.5) * ENTRY_EXPECTED_RETURN_AMP


def compute_target_price(
    current_price: int,
    expected_return: float,
    take_profit_rate: float,
) -> int:
    target_return = min(max(expected_return, take_profit_rate * 0.6), take_profit_rate)
    return round(int(current_price * (1 + target_return)), -1)


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
