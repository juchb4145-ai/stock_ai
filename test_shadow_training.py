"""단테 shadow 학습 트랙 단위 테스트.

shadow 트랙은 게이트가 wait/blocked 으로 거른 종목을 같은 25분 horizon 으로
사후 라벨링해, false-negative 분석에 쓴다.

main.py 는 PyQt5 를 top-level 에서 import 하지만, 본 테스트는 Kiwoom 인스턴스를
생성하지 않고 unbound 메서드만 직접 호출한다. 따라서 PyQt5 가 설치돼 있지 않은
CI/64bit venv 에서도 sys.modules stub 만 채워 두면 main 모듈을 import 할 수 있다.

실행:
    python -m unittest test_shadow_training -v
"""

from __future__ import annotations

from datetime import datetime
import os
import sys
import tempfile
import time
import types
import unittest
from unittest import mock


def _ensure_external_stubs() -> None:
    """PyQt5/pandas 미설치 환경에서도 main.py 를 import 할 수 있도록 sys.modules 채우기.

    main.py 는 32-bit 환경에서 키움 OpenAPI 와 함께 동작하지만, 본 테스트는 64-bit/CI
    어디서든 돌아야 하므로 외부 의존을 mock 으로 대체한다. shadow 트랙 메서드는 이
    의존들을 직접 호출하지 않으므로 attribute access 만 살아 있으면 충분하다.
    """
    if "PyQt5" not in sys.modules:
        qax = types.ModuleType("PyQt5.QAxContainer")
        qax.QAxWidget = mock.MagicMock
        qax.__all__ = ["QAxWidget"]

        widgets = types.ModuleType("PyQt5.QtWidgets")
        widgets.QApplication = mock.MagicMock
        widgets.QWidget = mock.MagicMock
        widgets.__all__ = ["QApplication", "QWidget"]

        core = types.ModuleType("PyQt5.QtCore")
        core.QTimer = mock.MagicMock
        core.QObject = mock.MagicMock
        core.pyqtSignal = mock.MagicMock()
        core.__all__ = ["QTimer", "QObject", "pyqtSignal"]

        pyqt5 = types.ModuleType("PyQt5")
        pyqt5.QAxContainer = qax
        pyqt5.QtWidgets = widgets
        pyqt5.QtCore = core

        sys.modules["PyQt5"] = pyqt5
        sys.modules["PyQt5.QAxContainer"] = qax
        sys.modules["PyQt5.QtWidgets"] = widgets
        sys.modules["PyQt5.QtCore"] = core

    if "pandas" not in sys.modules:
        sys.modules["pandas"] = mock.MagicMock()


_ensure_external_stubs()
import main  # noqa: E402  외부 stub 후에 import
import training_recorder  # noqa: E402  shadow CSV 경로 patch 대상
import market_state as ms  # noqa: E402  market dry-run 메타 테스트용


class _StubFiveMinInd:
    def __init__(self, closes_count: int = 60) -> None:
        self.closes_count = closes_count
        self.env_upper_13_25 = 9_900
        self.bb_upper_55_2 = 9_950


class _StubCtx:
    """register_dante_shadow_sample 가 사용하는 EntryContext 필드만 모방."""

    def __init__(
        self,
        *,
        current_price: int = 10_000,
        ask: int = 10_005,
        bid: int = 9_995,
        chejan_strength: float = 110.0,
        volume_speed: float = 800.0,
        spread_rate: float = 0.001,
        tick_count: int = 10,
        elapsed_sec: float = 60.0,
        five_min_closes_count: int = 60,
        position=None,
        market_state=None,
        now_ts: float | None = None,
    ) -> None:
        self.current_price = current_price
        self.ask = ask
        self.bid = bid
        self.chejan_strength = chejan_strength
        self.volume_speed = volume_speed
        self.spread_rate = spread_rate
        self.tick_count = tick_count
        now = now_ts if now_ts is not None else datetime(2026, 4, 30, 10, 0, 0).timestamp()
        self.now_ts = now
        self.condition_registered_at = now - elapsed_sec
        if five_min_closes_count > 0:
            self.five_min_ind = _StubFiveMinInd(five_min_closes_count)
        else:
            self.five_min_ind = None
        self.position = position
        self.minute_bars = []
        self.chejan_strength_history = []
        self.is_breakout_zero_bar = False
        self.is_breakout_prev_bar = False
        self.upper_wick_ratio_zero_bar = 0.2
        self.open_return = 0.05
        self.market_state = market_state


class _StubDecision:
    def __init__(
        self,
        status: str = "wait",
        stage: int = 1,
        ratio: float = 0.0,
        reason: str = "",
        reason_code: str = "",
        market_regime: str = "",
        market_gate_action: str = "",
        market_gate_reason: str = "",
    ) -> None:
        self.status = status
        self.stage = stage
        self.ratio = ratio
        self.reason = reason
        self.reason_code = reason_code
        self.market_regime = market_regime
        self.market_gate_action = market_gate_action
        self.market_gate_reason = market_gate_reason


class _StubPosition:
    def __init__(self, entry_stage: int = 0, breakout_high: int = 0) -> None:
        self.entry_stage = entry_stage
        self.breakout_high = breakout_high


class _StubKiwoom:
    """Shadow 트랙 메서드만 호출 가능한 최소 Kiwoom 모방.

    인스턴스 필드만 재현하고, 메서드는 main.Kiwoom 의 unbound 함수를 그대로 가져다 쓴다.
    """

    register_dante_shadow_sample = main.Kiwoom.register_dante_shadow_sample
    update_dante_shadow_training_labels = main.Kiwoom.update_dante_shadow_training_labels
    ensure_dante_shadow_training_data_file = main.Kiwoom.ensure_dante_shadow_training_data_file
    append_dante_shadow_training_row = main.Kiwoom.append_dante_shadow_training_row
    _is_dante_shadow_data_ready = main.Kiwoom._is_dante_shadow_data_ready

    def __init__(self) -> None:
        self.pending_dante_shadow_samples = {}
        self.last_dante_shadow_sample_at = {}


class ShadowTrainingFieldsTests(unittest.TestCase):
    def test_fields_compose_status_code_then_dante(self):
        # decision_status + reason_code 가 분류축으로 앞에 박혀 있어야
        # 분석 시 두 축으로 group by 가 자연스럽다.
        self.assertEqual(
            main.DANTE_SHADOW_TRAINING_FIELDS,
            ["decision_status", "reason_code"] + main.DANTE_TRAINING_FIELDS,
        )

    def test_separate_csv_path(self):
        self.assertNotEqual(main.DANTE_SHADOW_TRAINING_CSV, main.DANTE_TRAINING_CSV)
        self.assertTrue(main.DANTE_SHADOW_TRAINING_CSV.endswith(".csv"))

    def test_dante_training_fields_end_with_market_columns(self):
        # 라벨링 컬럼들 뒤에 MARKET_FIELDS + MARKET_GATE_FIELDS 가 끝에 박혀 있어야 한다
        # (rolling/분석 측에서 ``df.columns[-7:]`` 같은 위치 추출이 가능하도록).
        tail = (
            list(training_recorder.MARKET_FIELDS)
            + list(training_recorder.MARKET_GATE_FIELDS)
        )
        self.assertEqual(main.DANTE_TRAINING_FIELDS[-len(tail):], tail)
        self.assertEqual(main.DANTE_SHADOW_TRAINING_FIELDS[-len(tail):], tail)


class ShadowTrainingRegistrationTests(unittest.TestCase):
    def test_skip_when_decision_ready(self):
        kw = _StubKiwoom()
        kw.register_dante_shadow_sample(
            code="000001", name="A", ctx=_StubCtx(),
            decision=_StubDecision(status="ready"), current_price=10_000,
        )
        self.assertEqual(kw.pending_dante_shadow_samples, {})

    def test_skip_when_ticks_insufficient(self):
        kw = _StubKiwoom()
        kw.register_dante_shadow_sample(
            code="000001", name="A", ctx=_StubCtx(tick_count=1),
            decision=_StubDecision(status="wait", reason="체결강도 부족"),
            current_price=10_000,
        )
        self.assertEqual(kw.pending_dante_shadow_samples, {})

    def test_skip_when_observation_too_short(self):
        kw = _StubKiwoom()
        kw.register_dante_shadow_sample(
            code="000001", name="A", ctx=_StubCtx(elapsed_sec=5.0),
            decision=_StubDecision(status="wait", reason="관찰 시간 부족"),
            current_price=10_000,
        )
        self.assertEqual(kw.pending_dante_shadow_samples, {})

    def test_skip_when_five_min_cache_missing(self):
        kw = _StubKiwoom()
        kw.register_dante_shadow_sample(
            code="000001", name="A", ctx=_StubCtx(five_min_closes_count=0),
            decision=_StubDecision(status="wait", reason="5분봉 캐시 미준비"),
            current_price=10_000,
        )
        self.assertEqual(kw.pending_dante_shadow_samples, {})

    def test_skip_when_outside_regular_capture_session(self):
        kw = _StubKiwoom()
        night_ts = datetime(2026, 4, 30, 21, 27, 24).timestamp()
        kw.register_dante_shadow_sample(
            code="000001", name="A", ctx=_StubCtx(now_ts=night_ts),
            decision=_StubDecision(status="wait", reason="X"),
            current_price=10_000,
        )
        self.assertEqual(kw.pending_dante_shadow_samples, {})

    def test_skip_on_weekend_even_during_capture_hours(self):
        kw = _StubKiwoom()
        weekend_ts = datetime(2026, 5, 3, 10, 0, 0).timestamp()
        kw.register_dante_shadow_sample(
            code="000001", name="A", ctx=_StubCtx(now_ts=weekend_ts),
            decision=_StubDecision(status="wait", reason="X"),
            current_price=10_000,
        )
        self.assertEqual(kw.pending_dante_shadow_samples, {})

    def test_skip_when_already_full_position(self):
        kw = _StubKiwoom()
        ctx = _StubCtx(position=_StubPosition(entry_stage=2))
        kw.register_dante_shadow_sample(
            code="000001", name="A", ctx=ctx,
            decision=_StubDecision(status="blocked", reason="이미 진입 완료"),
            current_price=10_000,
        )
        self.assertEqual(kw.pending_dante_shadow_samples, {})

    def test_register_when_wait_with_full_data(self):
        kw = _StubKiwoom()
        kw.register_dante_shadow_sample(
            code="000001", name="A", ctx=_StubCtx(),
            decision=_StubDecision(status="wait", reason="윗꼬리 과다"),
            current_price=10_000,
        )
        self.assertEqual(len(kw.pending_dante_shadow_samples), 1)
        sample = next(iter(kw.pending_dante_shadow_samples.values()))
        row = sample["row"]
        self.assertEqual(row["decision_status"], "wait")
        self.assertEqual(row["code"], "000001")
        self.assertEqual(row["entry_price"], 10_000)
        self.assertEqual(row["ratio"], 0.0)
        self.assertEqual(row["reason"], "윗꼬리 과다")

    def test_register_when_blocked_with_full_data(self):
        kw = _StubKiwoom()
        kw.register_dante_shadow_sample(
            code="000002", name="B", ctx=_StubCtx(),
            decision=_StubDecision(status="blocked", reason="시가 대비 과열"),
            current_price=11_000,
        )
        self.assertEqual(len(kw.pending_dante_shadow_samples), 1)
        sample = next(iter(kw.pending_dante_shadow_samples.values()))
        self.assertEqual(sample["row"]["decision_status"], "blocked")

    def test_register_persists_reason_code(self):
        # decision.reason_code 가 row 에 그대로 보존돼야 분석측에서 안정 group by 가 가능.
        kw = _StubKiwoom()
        kw.register_dante_shadow_sample(
            code="000003", name="C", ctx=_StubCtx(),
            decision=_StubDecision(
                status="blocked",
                reason="시가 대비 과열 12.0% > 10.0%",
                reason_code="GATE_OVERHEAT_OPEN",
            ),
            current_price=11_000,
        )
        sample = next(iter(kw.pending_dante_shadow_samples.values()))
        self.assertEqual(sample["row"]["reason_code"], "GATE_OVERHEAT_OPEN")
        self.assertEqual(sample["row"]["decision_status"], "blocked")

    def test_register_reason_code_defaults_to_empty(self):
        # reason_code 가 비어 있는 결정도 안전하게 빈 문자열로 들어가야 한다.
        kw = _StubKiwoom()
        kw.register_dante_shadow_sample(
            code="000004", name="D", ctx=_StubCtx(),
            decision=_StubDecision(status="wait", reason="X"),
            current_price=10_000,
        )
        sample = next(iter(kw.pending_dante_shadow_samples.values()))
        self.assertEqual(sample["row"]["reason_code"], "")

    def test_shadow_row_persists_market_meta_when_present(self):
        # MarketSnapshot + decision 의 dry-run 메타가 row 에 그대로 박혀야 분석에서 join 가능.
        kw = _StubKiwoom()
        snap = ms.MarketSnapshot(
            market_pct=-0.012,
            market_slope_1m=-0.001,
            market_slope_3m=-0.006,
            market_drawdown_from_high=-0.018,
            market_regime=ms.REGIME_WEAK,
        )
        kw.register_dante_shadow_sample(
            code="000005", name="E",
            ctx=_StubCtx(market_state=snap),
            decision=_StubDecision(
                status="wait", reason="0봉/1봉 동시 돌파 미확인",
                reason_code="GATE_NO_BREAKOUT",
                market_regime=ms.REGIME_WEAK,
                market_gate_action="dry_run_allow",
                market_gate_reason="",
            ),
            current_price=10_000,
        )
        row = next(iter(kw.pending_dante_shadow_samples.values()))["row"]
        self.assertEqual(row["market_regime"], ms.REGIME_WEAK)
        self.assertAlmostEqual(row["market_pct"], -0.012)
        self.assertAlmostEqual(row["market_drawdown_from_high"], -0.018)
        self.assertEqual(row["market_gate_action"], "dry_run_allow")
        self.assertEqual(row["market_gate_reason"], "")

    def test_shadow_row_market_meta_blank_when_snapshot_missing(self):
        # ctx.market_state=None → MARKET_FIELDS 5개 모두 빈 문자열, gate 메타 2개는
        # decision 에 박혀 있는 값을 그대로 유지(entry_strategy 가 항상 채워주므로).
        kw = _StubKiwoom()
        kw.register_dante_shadow_sample(
            code="000006", name="F",
            ctx=_StubCtx(market_state=None),
            decision=_StubDecision(
                status="wait", reason="X", reason_code="GATE_NO_BREAKOUT",
                market_regime=ms.REGIME_NEUTRAL,
                market_gate_action="dry_run_allow",
            ),
            current_price=10_000,
        )
        row = next(iter(kw.pending_dante_shadow_samples.values()))["row"]
        for k in training_recorder.MARKET_FIELDS:
            self.assertEqual(row[k], "")
        self.assertEqual(row["market_gate_action"], "dry_run_allow")
        self.assertEqual(row["market_gate_reason"], "")

    def test_cooldown_blocks_repeat_registration(self):
        kw = _StubKiwoom()
        decision = _StubDecision(status="wait", reason="X")
        kw.register_dante_shadow_sample(
            code="000001", name="A", ctx=_StubCtx(),
            decision=decision, current_price=10_000,
        )
        kw.register_dante_shadow_sample(
            code="000001", name="A", ctx=_StubCtx(),
            decision=decision, current_price=10_010,
        )
        self.assertEqual(len(kw.pending_dante_shadow_samples), 1)


class ShadowTrainingLabelingTests(unittest.TestCase):
    def test_label_finalization_writes_csv_row(self):
        kw = _StubKiwoom()
        with tempfile.TemporaryDirectory() as tmp:
            shadow_path = os.path.join(tmp, "shadow.csv")
            with mock.patch.object(training_recorder, "DANTE_SHADOW_TRAINING_CSV", shadow_path), \
                 mock.patch.object(training_recorder, "TRAINING_DATA_DIR", tmp):
                kw.register_dante_shadow_sample(
                    code="000001", name="A", ctx=_StubCtx(),
                    decision=_StubDecision(
                        status="blocked",
                        reason="과열",
                        reason_code="GATE_OVERHEAT_OPEN",
                    ),
                    current_price=10_000,
                )
                self.assertEqual(len(kw.pending_dante_shadow_samples), 1)
                sample = next(iter(kw.pending_dante_shadow_samples.values()))
                # 25분 + 1초 후, +2% 도달 시점
                future = sample["captured_at"] + main.DANTE_TRAINING_FINAL_HORIZON_SECONDS + 1
                kw.update_dante_shadow_training_labels("000001", 10_200, future)

                self.assertEqual(kw.pending_dante_shadow_samples, {})
                self.assertTrue(os.path.exists(shadow_path))
                with open(shadow_path, encoding="utf-8-sig") as f:
                    lines = f.readlines()
                # 헤더 + 1 행
                self.assertEqual(len(lines), 2)
                header = lines[0].strip().split(",")
                self.assertEqual(header[0], "decision_status")
                self.assertEqual(header[1], "reason_code")
                # 첫 데이터 행: blocked,GATE_OVERHEAT_OPEN,...
                cells = lines[1].rstrip("\r\n").split(",")
                self.assertEqual(cells[0], "blocked")
                self.assertEqual(cells[1], "GATE_OVERHEAT_OPEN")

    def test_max_min_returns_tracked_during_horizon(self):
        kw = _StubKiwoom()
        with tempfile.TemporaryDirectory() as tmp:
            shadow_path = os.path.join(tmp, "shadow.csv")
            with mock.patch.object(training_recorder, "DANTE_SHADOW_TRAINING_CSV", shadow_path), \
                 mock.patch.object(training_recorder, "TRAINING_DATA_DIR", tmp):
                kw.register_dante_shadow_sample(
                    code="000001", name="A", ctx=_StubCtx(),
                    decision=_StubDecision(status="wait", reason="X"),
                    current_price=10_000,
                )
                sample = next(iter(kw.pending_dante_shadow_samples.values()))
                base = sample["captured_at"]
                # horizon 내부 틱들 — max/min 추적만 일어나야 함, finalize 는 아직 안 됨
                kw.update_dante_shadow_training_labels("000001", 10_300, base + 60)
                kw.update_dante_shadow_training_labels("000001", 9_800, base + 120)
                self.assertEqual(len(kw.pending_dante_shadow_samples), 1)
                self.assertEqual(sample["max_price"], 10_300)
                self.assertEqual(sample["min_price"], 9_800)
                # horizon 만료 후 finalize
                kw.update_dante_shadow_training_labels(
                    "000001", 10_000,
                    base + main.DANTE_TRAINING_FINAL_HORIZON_SECONDS + 1,
                )
                self.assertEqual(kw.pending_dante_shadow_samples, {})

    def test_label_skips_other_codes(self):
        kw = _StubKiwoom()
        with tempfile.TemporaryDirectory() as tmp:
            shadow_path = os.path.join(tmp, "shadow.csv")
            with mock.patch.object(training_recorder, "DANTE_SHADOW_TRAINING_CSV", shadow_path), \
                 mock.patch.object(training_recorder, "TRAINING_DATA_DIR", tmp):
                kw.register_dante_shadow_sample(
                    code="000001", name="A", ctx=_StubCtx(),
                    decision=_StubDecision(status="wait", reason="X"),
                    current_price=10_000,
                )
                sample = next(iter(kw.pending_dante_shadow_samples.values()))
                base = sample["captured_at"]
                # 다른 종목의 틱이 들어와도 영향 없어야 함
                kw.update_dante_shadow_training_labels("999999", 99_999, base + 60)
                self.assertEqual(sample["max_price"], 10_000)
                self.assertEqual(sample["min_price"], 10_000)


if __name__ == "__main__":
    unittest.main()
