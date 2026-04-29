"""R-multiple 트레일링 + 구조 기반 청산 평가.

매도 정책:
  1. 손절: 현재가 ≤ stop_price → 전량 매도. 초기 stop = entry_price * (1 - R_UNIT_PCT).
  2. +1R 도달 → stop_price 를 entry_price 로 상향(BE 보장).
  3. +2R 도달 + partial_taken==False → 50% 부분 익절(partial_sell).
  4. 부분 익절 후 잔량 추세 이탈 청산 — 다음 중 하나:
        - 1분봉 종가가 1분봉 5MA 이탈
        - 체결강도 EXIT_MIN_CHEJAN_STRENGTH 미만으로 약화
        - 현재가가 5분봉 Envelope(13,2.5) 상단 아래로 이탈
  5. 시간 손절: entry1_time 기준 EXIT_TIME_LIMIT_SECONDS 경과 + r < 1R → 청산.
  6. 강제 청산은 main.py 의 OPENING_FORCE_EXIT 시간이 별도로 처리한다.

이 모듈은 순수 함수만 노출한다. stop 갱신/partial 마킹은 ExitDecision 의
플래그를 통해 호출측이 Position 에 직접 반영한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from bars import FiveMinIndicators, MinuteBar
from portfolio import Position


# === R-multiple 정의 ===
R_UNIT_PCT = 0.015  # 1R = ±1.5%
EXIT_BE_R = 1.0  # +1R 도달 시 BE 스탑 이동
EXIT_PARTIAL_R = 2.0  # +2R 도달 시 부분 익절
EXIT_PARTIAL_RATIO = 0.5  # 부분 익절 비율
EXIT_TIME_LIMIT_SECONDS = 25 * 60  # 1차 진입 후 N초 경과 + r<1R 이면 시간 손절
EXIT_MIN_CHEJAN_STRENGTH = 80.0  # 체결강도 약화 임계
EXIT_MA_PERIOD = 5  # 1분봉 N MA 이탈 시 청산
ENV_BREAK_BUFFER_PCT = 0.001  # 5분봉 Env 상단 -0.1% 까지는 노이즈로 간주


@dataclass
class ExitDecision:
    """청산 평가 결과.

    action:
      - "hold": 보유 유지(stop 갱신은 update_stop_to_be 로 별도 표시)
      - "sell": 전량 매도
      - "partial_sell": qty_ratio 비율만큼 부분 매도
    """

    action: str
    qty_ratio: float = 0.0
    reason: str = ""
    update_stop_to_be: bool = False  # 호출측이 pos.stop_price = pos.entry_price 로 옮겨야 함
    mark_partial_taken: bool = False  # 호출측이 pos.partial_taken = True 로 표시해야 함


@dataclass
class ExitContext:
    """청산 평가 입력."""

    position: Position
    current_price: int
    chejan_strength: float
    minute_bars: List[MinuteBar]
    five_min_ind: Optional[FiveMinIndicators]
    now_ts: float


def evaluate_exit(ctx: ExitContext) -> ExitDecision:
    pos = ctx.position
    cur = ctx.current_price
    if pos.entry_price <= 0 or cur <= 0:
        return ExitDecision("hold", 0.0, "진입가/현재가 없음")

    profit_rate = cur / pos.entry_price - 1
    r_unit = pos.r_unit_pct if pos.r_unit_pct > 0 else R_UNIT_PCT
    r = profit_rate / r_unit if r_unit > 0 else 0.0

    # 1) 손절(최우선)
    if pos.stop_price > 0 and cur <= pos.stop_price:
        return ExitDecision(
            "sell",
            1.0,
            "손절(stop {} 도달, 수익 {:.2%})".format(pos.stop_price, profit_rate),
        )

    # 2) +1R 도달 시 BE 스탑 이동 플래그 (sell 액션 없이 hold/partial 결정에 함께 실어 보냄)
    update_stop = False
    if r >= EXIT_BE_R and pos.stop_price < pos.entry_price:
        update_stop = True

    # 3) +2R 도달 + 미부분익절 → 50% 부분 익절
    if r >= EXIT_PARTIAL_R and not pos.partial_taken:
        return ExitDecision(
            "partial_sell",
            EXIT_PARTIAL_RATIO,
            "+2R 도달 부분익절 ({:.2%})".format(profit_rate),
            update_stop_to_be=update_stop,
            mark_partial_taken=True,
        )

    # 4) 부분익절 이후 잔량 추세 이탈 청산
    if pos.partial_taken:
        # 4a) 1분봉 5MA 이탈
        if len(ctx.minute_bars) >= EXIT_MA_PERIOD:
            recent = ctx.minute_bars[-EXIT_MA_PERIOD:]
            sma5 = sum(b.close for b in recent) / EXIT_MA_PERIOD
            if cur < sma5:
                return ExitDecision(
                    "sell",
                    1.0,
                    "1분봉 {}MA 이탈 (SMA {:.0f} > 현재가 {})".format(
                        EXIT_MA_PERIOD, sma5, cur
                    ),
                    update_stop_to_be=update_stop,
                )

        # 4b) 체결강도 약화
        if 0 < ctx.chejan_strength < EXIT_MIN_CHEJAN_STRENGTH:
            return ExitDecision(
                "sell",
                1.0,
                "체결강도 약화 {:.1f} < {}".format(
                    ctx.chejan_strength, EXIT_MIN_CHEJAN_STRENGTH
                ),
                update_stop_to_be=update_stop,
            )

        # 4c) 5분봉 Envelope(13,2.5) 상단 이탈
        if ctx.five_min_ind and ctx.five_min_ind.env_upper_13_25:
            env = ctx.five_min_ind.env_upper_13_25
            buffer = env * ENV_BREAK_BUFFER_PCT
            if cur < env - buffer:
                return ExitDecision(
                    "sell",
                    1.0,
                    "5분봉 Env(13) 이탈 (env {:.0f} > 현재가 {})".format(env, cur),
                    update_stop_to_be=update_stop,
                )

    # 5) 시간 손절
    entry_anchor = pos.entry1_time or pos.entry_time or ctx.now_ts
    elapsed = ctx.now_ts - entry_anchor
    if elapsed >= EXIT_TIME_LIMIT_SECONDS and r < EXIT_BE_R:
        return ExitDecision(
            "sell",
            1.0,
            "시간 손절 ({:.0f}초 경과, R={:.2f}, 수익 {:.2%})".format(
                elapsed, r, profit_rate
            ),
            update_stop_to_be=update_stop,
        )

    return ExitDecision(
        "hold",
        0.0,
        "보유 (R={:.2f}, 수익 {:.2%}{})".format(
            r, profit_rate, ", BE 이동" if update_stop else ""
        ),
        update_stop_to_be=update_stop,
    )
