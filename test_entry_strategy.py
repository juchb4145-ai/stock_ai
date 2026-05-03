"""entry_strategy 단위 테스트.

실행:
    .\\venv64\\Scripts\\python.exe -m pytest -q test_entry_strategy.py
또는:
    .\\venv64\\Scripts\\python.exe test_entry_strategy.py
(unittest 자동 발견)
"""

from __future__ import annotations

import time
import unittest
from typing import List

from bars import FiveMinIndicators, MinuteBar
from portfolio import Position
import entry_strategy as es
import market_state as ms


def make_bar(*, ts: float, open_: int, high: int, low: int, close: int, volume: int = 100) -> MinuteBar:
    return MinuteBar(
        minute_start=int(ts // 60) * 60,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        received_at=ts,
    )


def default_five_min_ind() -> FiveMinIndicators:
    """A급 진입을 통과시키는 표준 5분봉 스냅샷.

    BB(55) 상단을 현재가보다 살짝 위에 둬서 과열 게이트는 통과시키되,
    Envelope(13) 상단을 현재가와 동등하게 잡아 trend_up == True 가 되도록 한다.
    개별 테스트는 필드를 바꿔 게이트별 케이스를 만든다.
    """
    return FiveMinIndicators(
        bb_upper_45_2=9_950,
        bb_upper_55_2=10_300,
        env_upper_13_25=10_000,
        env_upper_22_25=10_300,
        bb_upper_45_2_prev=10_010,
        bb_upper_55_2_prev=10_310,
        env_upper_13_25_prev=10_020,
        env_upper_22_25_prev=10_320,
        last_close=10_000,
        closes_count=60,
        cur_open=9_960,
        cur_high=10_005,
        cur_low=9_950,
        prev_open=9_900,
        prev_high=9_980,
        prev_low=9_870,
        prev_close=9_960,
        pre_prev_close=9_900,
    )


def build_ctx(
    *,
    current_price: int = 10_000,
    open_price: int | None = None,
    ask: int = 10_010,
    bid: int = 9_990,
    spread_rate: float = 0.002,
    chejan_strength: float = 130.0,
    chejan_strength_history: List[float] | None = None,
    volume_speed: float = 1_000.0,
    minute_bars: List[MinuteBar] | None = None,
    five_min_ind: FiveMinIndicators | None = "default",
    condition_registered_at: float | None = None,
    now_ts: float | None = None,
    tick_count: int = 10,
    position: Position | None = None,
    is_breakout_zero_bar: bool = True,
    is_breakout_prev_bar: bool = False,
    upper_wick_ratio_zero_bar: float = 0.1,
    px_over_bb55_pct: float | None = None,
    open_return: float | None = None,
    market_state: ms.MarketSnapshot | None = None,
) -> es.EntryContext:
    now = now_ts or time.time()
    if five_min_ind == "default":
        five_min_ind = default_five_min_ind()
    if open_price is None:
        open_price = max(int(current_price * 0.97), 1)  # 디폴트: 시가 대비 +3% (과열 안 걸림)
    if open_return is None:
        open_return = (current_price / open_price - 1) if open_price > 0 else 0.0
    if px_over_bb55_pct is None:
        if five_min_ind is not None and five_min_ind.bb_upper_55_2:
            px_over_bb55_pct = current_price / five_min_ind.bb_upper_55_2 - 1
        else:
            px_over_bb55_pct = 0.0
    return es.EntryContext(
        code="000001",
        name="테스트",
        current_price=current_price,
        open_price=open_price,
        high=current_price,
        low=current_price,
        ask=ask,
        bid=bid,
        chejan_strength=chejan_strength,
        volume_speed=volume_speed,
        spread_rate=spread_rate,
        minute_bars=minute_bars or [],
        five_min_ind=five_min_ind,
        condition_registered_at=condition_registered_at if condition_registered_at is not None else now - 60,
        now_ts=now,
        tick_count=tick_count,
        position=position,
        chejan_strength_history=chejan_strength_history or [125.0, 128.0, 130.0, 132.0, 134.0, 135.0],
        is_breakout_zero_bar=is_breakout_zero_bar,
        is_breakout_prev_bar=is_breakout_prev_bar,
        upper_wick_ratio_zero_bar=upper_wick_ratio_zero_bar,
        px_over_bb55_pct=px_over_bb55_pct,
        open_return=open_return,
        market_state=market_state,
    )


def make_market_snap(*, regime: str, pct: float = 0.0) -> ms.MarketSnapshot:
    """테스트용 MarketSnapshot. classify_regime 임계와 어긋나도 regime 을 강제 부여한다."""
    return ms.MarketSnapshot(
        market_pct=pct,
        market_slope_1m=None,
        market_slope_3m=None,
        market_drawdown_from_high=None,
        market_regime=regime,
    )


class FirstEntryTests(unittest.TestCase):
    def test_ready_when_all_gates_pass(self):
        ctx = build_ctx()
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "ready")
        self.assertAlmostEqual(d.ratio, es.DANTE_FIRST_ENTRY_RATIO)

    def test_blocks_on_excessive_spread(self):
        ctx = build_ctx(spread_rate=0.02)  # 2% 스프레드
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "blocked")
        self.assertIn("스프레드", d.reason)
        self.assertEqual(d.reason_code, es.GATE_SPREAD)

    def test_waits_when_observation_short(self):
        now = time.time()
        ctx = build_ctx(condition_registered_at=now - 5, now_ts=now)
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "wait")
        self.assertIn("관찰", d.reason)
        self.assertEqual(d.reason_code, es.GATE_OBSERVATION_SHORT)

    def test_waits_on_low_chejan_strength(self):
        ctx = build_ctx(chejan_strength=50.0)
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "wait")
        self.assertIn("체결강도", d.reason)
        self.assertEqual(d.reason_code, es.GATE_CHEJAN_SOFT)

    def test_waits_on_low_volume_speed(self):
        ctx = build_ctx(volume_speed=10.0)
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "wait")
        self.assertIn("거래속도", d.reason)
        self.assertEqual(d.reason_code, es.GATE_VOLUME_SPEED)

    def test_waits_when_below_5min_envelope(self):
        ind = FiveMinIndicators(
            bb_upper_45_2=11_000,
            bb_upper_55_2=11_500,
            env_upper_13_25=10_500,
            env_upper_22_25=10_800,
            last_close=10_000,
            closes_count=60,
        )
        ctx = build_ctx(five_min_ind=ind, current_price=10_100, px_over_bb55_pct=-0.12, open_return=0.01)
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "wait")
        self.assertIn("추세", d.reason)

    def test_passes_when_above_5min_bb55(self):
        ind = FiveMinIndicators(
            bb_upper_45_2=10_500,
            bb_upper_55_2=10_400,
            env_upper_13_25=10_600,
            env_upper_22_25=10_800,
            last_close=10_500,
            closes_count=60,
            cur_open=10_300,
            cur_high=10_510,
            cur_low=10_280,
            prev_close=10_350,
            bb_upper_45_2_prev=10_490,
            bb_upper_55_2_prev=10_390,
            env_upper_13_25_prev=10_590,
            env_upper_22_25_prev=10_790,
        )
        ctx = build_ctx(
            five_min_ind=ind,
            current_price=10_500,
            px_over_bb55_pct=10_500 / 10_400 - 1,
            open_return=0.02,
        )
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "ready")

    def test_blocks_if_position_already_entered(self):
        pos = Position(code="000001", entry_stage=1, entry_price=10_000)
        ctx = build_ctx(position=pos)
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "blocked")

    def test_waits_when_neither_zero_nor_prev_breakout(self):
        ctx = build_ctx(is_breakout_zero_bar=False, is_breakout_prev_bar=False)
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "wait")
        self.assertIn("0봉/1봉", d.reason)
        self.assertEqual(d.reason_code, es.GATE_NO_BREAKOUT)

    def test_a_grade_ready_with_grade_field(self):
        ctx = build_ctx(is_breakout_zero_bar=True, is_breakout_prev_bar=False)
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "ready")
        self.assertEqual(d.grade, "A")
        self.assertAlmostEqual(d.ratio, es.DANTE_FIRST_ENTRY_RATIO)
        self.assertEqual(d.stage, 1)
        self.assertEqual(d.reason_code, es.READY_AGRADE_FIRST)

    def test_blocks_on_fake_breakout_upper_wick(self):
        ctx = build_ctx(upper_wick_ratio_zero_bar=0.55)  # > MAX_UPPER_WICK_RATIO
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "wait")
        self.assertIn("윗꼬리", d.reason)

    def test_blocks_on_overheated_open_return(self):
        ctx = build_ctx(open_return=0.12)  # 시가 대비 +12%
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "blocked")
        self.assertIn("시가", d.reason)
        self.assertEqual(d.reason_code, es.GATE_OVERHEAT_OPEN)

    def test_blocks_on_overheated_bb55_distance(self):
        ctx = build_ctx(px_over_bb55_pct=0.06)  # BB55 +6%
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "blocked")
        self.assertIn("BB55", d.reason)
        self.assertEqual(d.reason_code, es.GATE_OVERHEAT_BB55)

    def test_chejan_strength_120_passes_without_history(self):
        # 120 이상이면 추세 미상이어도 통과
        ctx = build_ctx(chejan_strength=125.0, chejan_strength_history=[])
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "ready")

    def test_chejan_strength_soft_with_rising_history_passes(self):
        # 100~120 사이 + 뒷 절반 평균이 앞 절반보다 크고 100 이상이면 통과
        history = [101.0, 105.0, 108.0, 112.0, 115.0, 118.0]
        ctx = build_ctx(chejan_strength=115.0, chejan_strength_history=history)
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "ready")

    def test_chejan_strength_soft_without_rising_blocks(self):
        # 100~120 사이지만 추세 평탄/하락이면 wait
        history = [115.0, 113.0, 111.0, 109.0, 107.0, 105.0]
        ctx = build_ctx(chejan_strength=105.0, chejan_strength_history=history)
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "wait")
        self.assertIn("체결강도 약함", d.reason)

    def test_chejan_strength_below_soft_blocks(self):
        ctx = build_ctx(chejan_strength=85.0)
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "wait")
        self.assertIn("체결강도 부족", d.reason)


class GradeBPullbackTests(unittest.TestCase):
    def _bars_with_b_grade_pullback(self) -> List[MinuteBar]:
        ts = time.time() - 60 * 5
        # 직전 고점 10_300, 음봉 2개로 약 0.6% 눌림 후 양봉 반전
        return [
            make_bar(ts=ts, open_=10_000, high=10_300, low=9_980, close=10_280),  # 양봉(고점 형성)
            make_bar(ts=ts + 60, open_=10_280, high=10_290, low=10_230, close=10_240),  # 음봉
            make_bar(ts=ts + 120, open_=10_240, high=10_250, low=10_200, close=10_220),  # 음봉
            make_bar(ts=ts + 180, open_=10_220, high=10_260, low=10_215, close=10_240),  # 진행봉(양봉)
        ]

    def test_b_grade_ready_on_first_pullback(self):
        bars = self._bars_with_b_grade_pullback()
        # 1봉전 돌파만 만족 (zero=False, prev=True), 1분봉 첫 눌림+양봉반전 OK
        ctx = build_ctx(
            current_price=bars[-1].close,
            minute_bars=bars,
            is_breakout_zero_bar=False,
            is_breakout_prev_bar=True,
        )
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "ready")
        self.assertEqual(d.grade, "B")
        self.assertAlmostEqual(d.ratio, es.DANTE_GRADE_B_RATIO)
        self.assertEqual(d.stage, 2)
        self.assertEqual(d.reason_code, es.READY_BGRADE_PULLBACK)

    def test_b_grade_waits_when_no_pullback(self):
        ts = time.time() - 60 * 3
        bars = [
            make_bar(ts=ts, open_=10_200, high=10_280, low=10_180, close=10_270),
            make_bar(ts=ts + 60, open_=10_270, high=10_280, low=10_250, close=10_278),
        ]
        ctx = build_ctx(
            current_price=10_278,
            minute_bars=bars,
            is_breakout_zero_bar=False,
            is_breakout_prev_bar=True,
        )
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "wait")
        self.assertIn("B급", d.reason)


class SecondEntryTests(unittest.TestCase):
    def _position_after_stage1(self, *, breakout_high: int = 10_300, deadline_in: float = 600.0) -> Position:
        now = time.time()
        return Position(
            code="000001",
            entry_stage=1,
            entry_price=10_000,
            quantity=10,
            planned_quantity=40,
            entry1_time=now - 120,
            pullback_window_deadline=now + deadline_in,
            breakout_high=breakout_high,
        )

    def _bars_with_pullback(self, *, neg_count: int = 2) -> List[MinuteBar]:
        ts = time.time() - 60 * (neg_count + 2)
        bars: List[MinuteBar] = []
        # 직전 양봉 (눌림 시작 전)
        bars.append(make_bar(ts=ts, open_=10_000, high=10_300, low=9_980, close=10_280))
        ts += 60
        # 음봉 N개
        last_close = 10_280
        for _ in range(neg_count):
            cand_close = last_close - 30
            bars.append(make_bar(ts=ts, open_=last_close, high=last_close + 5, low=cand_close - 10, close=cand_close))
            last_close = cand_close
            ts += 60
        # 현재 진행봉 (양봉 반전)
        bars.append(make_bar(ts=ts, open_=last_close, high=last_close + 40, low=last_close - 5, close=last_close + 30))
        return bars

    def test_ready_on_classic_pullback_with_two_neg_bars(self):
        pos = self._position_after_stage1(breakout_high=10_300)
        bars = self._bars_with_pullback(neg_count=2)
        ctx = build_ctx(position=pos, current_price=bars[-1].close, minute_bars=bars)
        d = es.evaluate_second_entry(ctx)
        self.assertEqual(d.status, "ready")
        self.assertAlmostEqual(d.ratio, es.DANTE_SECOND_ENTRY_RATIO)
        self.assertEqual(d.reason_code, es.READY_AGRADE_SECOND)

    def test_waits_when_pullback_too_shallow(self):
        pos = self._position_after_stage1(breakout_high=10_300)
        bars = self._bars_with_pullback(neg_count=2)
        # 현재가를 고점에 가깝게 → 눌림 부족
        ctx = build_ctx(position=pos, current_price=10_298, minute_bars=bars)
        d = es.evaluate_second_entry(ctx)
        self.assertEqual(d.status, "wait")
        self.assertIn("눌림 부족", d.reason)
        self.assertEqual(d.reason_code, es.GATE_STAGE2_PULLBACK_SHALLOW)

    def test_blocks_when_drawdown_exceeds_max(self):
        pos = self._position_after_stage1(breakout_high=10_500)
        bars = self._bars_with_pullback(neg_count=2)
        # 고점 10_500 대비 -3% → MAX_DRAWDOWN_FROM_HIGH(0.020) 초과
        ctx = build_ctx(position=pos, current_price=10_180, minute_bars=bars)
        d = es.evaluate_second_entry(ctx)
        self.assertEqual(d.status, "blocked")
        self.assertEqual(d.reason_code, es.GATE_STAGE2_DRAWDOWN)

    def test_waits_when_no_negative_then_positive_pattern(self):
        pos = self._position_after_stage1(breakout_high=10_300)
        # 음봉 없이 곧장 진행 (현재봉도 양봉이지만 직전이 양봉)
        ts = time.time() - 60
        bars = [
            make_bar(ts=ts, open_=10_200, high=10_280, low=10_180, close=10_270),
            make_bar(ts=ts + 60, open_=10_270, high=10_300, low=10_250, close=10_290),
        ]
        ctx = build_ctx(position=pos, current_price=10_220, minute_bars=bars)
        d = es.evaluate_second_entry(ctx)
        self.assertEqual(d.status, "wait")
        self.assertIn("음봉", d.reason)

    def test_blocks_when_window_expired(self):
        pos = self._position_after_stage1(breakout_high=10_300)
        pos.pullback_window_deadline = time.time() - 1  # 만료
        bars = self._bars_with_pullback(neg_count=2)
        ctx = build_ctx(position=pos, current_price=bars[-1].close, minute_bars=bars)
        d = es.evaluate_second_entry(ctx)
        self.assertEqual(d.status, "blocked")
        self.assertIn("윈도우", d.reason)
        self.assertEqual(d.reason_code, es.GATE_STAGE2_WINDOW_EXPIRED)

    def test_should_lock_single_position_after_window(self):
        pos = self._position_after_stage1(breakout_high=10_300)
        pos.pullback_window_deadline = time.time() - 1
        ctx = build_ctx(position=pos)
        self.assertTrue(es.should_lock_single_position(ctx))

    def test_should_not_lock_during_window(self):
        pos = self._position_after_stage1(breakout_high=10_300)
        ctx = build_ctx(position=pos)
        self.assertFalse(es.should_lock_single_position(ctx))


class MarketDryRunGateTests(unittest.TestCase):
    """1차 PR: market regime 은 status/ratio 변경 없이 메타만 부착한다.

    테스트는 (1) 실제 진입 행동(status/ratio/grade/reason_code) 가 매크로에 의해
    절대 바뀌지 않는지, (2) market_gate_action / market_gate_reason 메타가 정책대로
    부여되는지 두 축에 집중한다.
    """

    def test_unknown_when_market_state_missing_falls_back_to_allow(self):
        # ctx.market_state=None 시 neutral fallback → action=dry_run_allow
        ctx = build_ctx()
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "ready")
        self.assertEqual(d.reason_code, es.READY_AGRADE_FIRST)
        self.assertEqual(d.market_regime, ms.REGIME_NEUTRAL)
        self.assertEqual(d.market_gate_action, es.MARKET_ACTION_ALLOW)
        self.assertEqual(d.market_gate_reason, "")

    def test_unknown_regime_treated_as_neutral(self):
        # snapshot 자체는 있으나 regime 이 unknown 이면 neutral 로 처리
        snap = make_market_snap(regime=ms.REGIME_UNKNOWN)
        ctx = build_ctx(market_state=snap)
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.market_regime, ms.REGIME_NEUTRAL)
        self.assertEqual(d.market_gate_action, es.MARKET_ACTION_ALLOW)

    def test_strong_keeps_allow_for_a_grade(self):
        snap = make_market_snap(regime=ms.REGIME_STRONG, pct=0.01)
        ctx = build_ctx(market_state=snap)
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "ready")
        self.assertEqual(d.market_regime, ms.REGIME_STRONG)
        self.assertEqual(d.market_gate_action, es.MARKET_ACTION_ALLOW)

    def test_weak_blocks_a_grade_chase_only_but_status_unchanged(self):
        # weak 매크로 + A급 0봉 추격 ready → action=block_chase_only, status 는 그대로 ready
        snap = make_market_snap(regime=ms.REGIME_WEAK, pct=-0.008)
        ctx = build_ctx(market_state=snap)
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "ready")
        self.assertAlmostEqual(d.ratio, es.DANTE_FIRST_ENTRY_RATIO)
        self.assertEqual(d.reason_code, es.READY_AGRADE_FIRST)
        self.assertEqual(d.market_regime, ms.REGIME_WEAK)
        self.assertEqual(d.market_gate_action, es.MARKET_ACTION_BLOCK_CHASE_ONLY)
        self.assertEqual(d.market_gate_reason, es.MARKET_GATE_WEAK_CHASE_BLOCK)

    def test_weak_allows_b_grade_pullback(self):
        # weak 매크로 + B급 첫 눌림 ready → action=allow (chase 가 아니므로)
        ts = time.time() - 60 * 5
        bars = [
            make_bar(ts=ts, open_=10_000, high=10_300, low=9_980, close=10_280),
            make_bar(ts=ts + 60, open_=10_280, high=10_290, low=10_230, close=10_240),
            make_bar(ts=ts + 120, open_=10_240, high=10_250, low=10_200, close=10_220),
            make_bar(ts=ts + 180, open_=10_220, high=10_260, low=10_215, close=10_240),
        ]
        snap = make_market_snap(regime=ms.REGIME_WEAK, pct=-0.008)
        ctx = build_ctx(
            current_price=bars[-1].close,
            minute_bars=bars,
            is_breakout_zero_bar=False,
            is_breakout_prev_bar=True,
            market_state=snap,
        )
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "ready")
        self.assertEqual(d.reason_code, es.READY_BGRADE_PULLBACK)
        self.assertEqual(d.market_regime, ms.REGIME_WEAK)
        self.assertEqual(d.market_gate_action, es.MARKET_ACTION_ALLOW)
        self.assertEqual(d.market_gate_reason, "")

    def test_weak_keeps_allow_for_non_ready_decisions(self):
        # weak 매크로 + wait/blocked 결정 → 매크로는 allow (block_chase_only 는 A급 ready 한정)
        snap = make_market_snap(regime=ms.REGIME_WEAK, pct=-0.008)
        ctx = build_ctx(spread_rate=0.02, market_state=snap)  # 스프레드로 blocked
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "blocked")
        self.assertEqual(d.reason_code, es.GATE_SPREAD)
        self.assertEqual(d.market_gate_action, es.MARKET_ACTION_ALLOW)

    def test_risk_off_marks_block_all_for_a_grade_ready(self):
        snap = make_market_snap(regime=ms.REGIME_RISK_OFF, pct=-0.02)
        ctx = build_ctx(market_state=snap)
        d = es.evaluate_first_entry(ctx)
        # status/ratio/reason_code 는 변경 없음
        self.assertEqual(d.status, "ready")
        self.assertAlmostEqual(d.ratio, es.DANTE_FIRST_ENTRY_RATIO)
        self.assertEqual(d.reason_code, es.READY_AGRADE_FIRST)
        # 메타만 block_all
        self.assertEqual(d.market_regime, ms.REGIME_RISK_OFF)
        self.assertEqual(d.market_gate_action, es.MARKET_ACTION_BLOCK_ALL)
        self.assertEqual(d.market_gate_reason, es.MARKET_GATE_RISK_OFF)

    def test_risk_off_marks_block_all_even_for_wait(self):
        # risk_off 는 ready 가 아닌 결정에도 block_all 메타가 붙는다(분석 시 표본 분리용).
        snap = make_market_snap(regime=ms.REGIME_RISK_OFF, pct=-0.02)
        ctx = build_ctx(is_breakout_zero_bar=False, is_breakout_prev_bar=False, market_state=snap)
        d = es.evaluate_first_entry(ctx)
        self.assertEqual(d.status, "wait")
        self.assertEqual(d.reason_code, es.GATE_NO_BREAKOUT)
        self.assertEqual(d.market_gate_action, es.MARKET_ACTION_BLOCK_ALL)
        self.assertEqual(d.market_gate_reason, es.MARKET_GATE_RISK_OFF)

    def test_risk_off_marks_block_all_for_second_entry(self):
        # evaluate_second_entry 도 동일 wrapping
        snap = make_market_snap(regime=ms.REGIME_RISK_OFF, pct=-0.02)
        pos = Position(
            code="000001",
            entry_stage=1,
            entry_price=10_000,
            quantity=10,
            planned_quantity=40,
            entry1_time=time.time() - 120,
            pullback_window_deadline=time.time() + 600,
            breakout_high=10_300,
        )
        ctx = build_ctx(position=pos, market_state=snap)
        d = es.evaluate_second_entry(ctx)
        # status 자체는 평가 결과 그대로(여기선 wait/blocked 어느 쪽이든)
        self.assertIn(d.status, ("ready", "wait", "blocked"))
        self.assertEqual(d.market_regime, ms.REGIME_RISK_OFF)
        self.assertEqual(d.market_gate_action, es.MARKET_ACTION_BLOCK_ALL)
        self.assertEqual(d.market_gate_reason, es.MARKET_GATE_RISK_OFF)


if __name__ == "__main__":
    unittest.main()
