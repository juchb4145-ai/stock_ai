"""학습/거래 로그 기록을 담당하는 Mixin 모듈.

main.py 의 Kiwoom 클래스에서 다음 4개 트랙을 분리한다.

  1) entry_training (구학습; 현재 비활성)
        - register_training_sample / update_training_labels
        - ensure_training_data_file / append_training_row
  2) dante_entry_training (Phase A; ready 표본)
        - register_dante_training_sample / update_dante_training_labels
        - ensure_dante_training_data_file / append_dante_training_row
  3) dante_shadow_training (false-negative 측정용; wait/blocked 표본)
        - register_dante_shadow_sample / update_dante_shadow_training_labels
        - ensure_dante_shadow_training_data_file / append_dante_shadow_training_row
        - _is_dante_shadow_data_ready (사전조건 게이트)
  4) trade_log (모든 매수/매도 이벤트 누적 로그)
        - ensure_trade_log_file / append_trade_log

설계 원칙:
  - Kiwoom 클래스에 ``TrainingRecorderMixin`` 으로 합쳐지므로 ``self.X`` 로
    Kiwoom 의 인스턴스 필드(``pending_dante_samples`` 등) 에 접근한다.
  - 모듈 상수(``DANTE_TRAINING_CSV`` 등) 는 본 모듈에 모아두고 main.py 에서
    re-export 해 기존 ``from main import DANTE_TRAINING_CSV`` 사용처와의
    호환을 유지한다.
  - 외부 의존(scoring, exit_strategy) 은 함수 안에서 lazy import 가 아니라
    모듈 top-level 에서 import. 순환 의존이 없는 구조이므로 안전하다.
"""

from __future__ import annotations

import csv
import logging
import os
import time
import uuid
from typing import Any, Dict, Optional

import entry_strategy
import exit_strategy
import scoring
from market_state import SNAPSHOT_FIELD_NAMES


logger = logging.getLogger("kiwoom")


# ---------------------------------------------------------------------------
# 모듈 상수 (main.py 에서 re-export)
# ---------------------------------------------------------------------------

# === 구학습 트랙 (현재 비활성) ===
TRAINING_DATA_ENABLED = False
TRAINING_DATA_DIR = "data"
TRAINING_ENTRY_CSV = os.path.join(TRAINING_DATA_DIR, "entry_training.csv")
TRADE_LOG_CSV = os.path.join(TRAINING_DATA_DIR, "trade_log.csv")
TRAINING_SAMPLE_COOLDOWN_SECONDS = 30
TRAINING_LABEL_HORIZONS = (300, 600, 1200)

# === 단테 학습 트랙 (Phase A) ===
DANTE_TRAINING_DATA_ENABLED = True
DANTE_TRAINING_CSV = os.path.join(TRAINING_DATA_DIR, "dante_entry_training.csv")
DANTE_TRAINING_LABEL_HORIZONS = (300, 600, 1200)  # 5/10/20분 단순 수익률
DANTE_TRAINING_FINAL_HORIZON_SECONDS = 25 * 60  # 25분 후 reached_1r/2r/hit_stop/time_exit 확정
DANTE_TRAINING_SAMPLE_COOLDOWN_SECONDS = 60  # 같은 종목 연속 등록 방지

# === Market regime dry-run 메타 컬럼 (entry_strategy._apply_market_gate 가 채움) ===
# CSV 분석 시 group by 키. SNAPSHOT_FIELD_NAMES 는 market_state 모듈이 단일 출처.
MARKET_FIELDS = list(SNAPSHOT_FIELD_NAMES)
MARKET_GATE_FIELDS = ["market_gate_action", "market_gate_reason"]


DANTE_TRAINING_FIELDS = [
    "sample_id",
    "captured_at",
    "captured_time",
    "code",
    "name",
    "entry_stage",
    "entry_price",
    "ratio",
    "reason",
] + list(scoring.DANTE_ENTRY_FEATURE_NAMES) + [
    "return_5m",
    "return_10m",
    "return_20m",
    "max_return_25m",
    "min_return_25m",
    "reached_1r",
    "reached_2r",
    "hit_stop",
    "time_exit",
    "labeled_at",
] + MARKET_FIELDS + MARKET_GATE_FIELDS

# === 단테 shadow 학습 트랙 (false-negative 측정) ===
DANTE_SHADOW_TRAINING_DATA_ENABLED = True
DANTE_SHADOW_TRAINING_CSV = os.path.join(TRAINING_DATA_DIR, "dante_shadow_training.csv")
DANTE_SHADOW_SAMPLE_COOLDOWN_SECONDS = 90  # ready 보다 길게(wait 줄줄이 막기)
DANTE_SHADOW_TRAINING_FIELDS = ["decision_status", "reason_code"] + DANTE_TRAINING_FIELDS
DANTE_CAPTURE_START_HHMMSS = 90500
DANTE_CAPTURE_END_HHMMSS = 143000

# === 구학습 entry CSV 헤더 (스코어/모델/기대수익 등) ===
ENTRY_FEATURE_NAMES = [
    "price_momentum",
    "open_return",
    "box_position",
    "direction_score",
    "volume_speed",
    "spread_rate",
]
TRAINING_ENTRY_FIELDS = [
    "sample_id",
    "captured_at",
    "captured_time",
    "code",
    "name",
    "entry_price",
    "score",
    "expected_return",
    "target_price",
    "model_name",
    "status",
    "reason",
] + ENTRY_FEATURE_NAMES + [
    "return_5m",
    "return_10m",
    "return_20m",
    "success_10m",
]

TRADE_LOG_FIELDS = [
    "logged_at",
    "event",
    "code",
    "name",
    "side",
    "order_type",
    "order_status",
    "order_no",
    "order_result",
    "quantity",
    "order_price",
    "current_price",
    "executed_price",
    "executed_quantity",
    "entry_price",
    "target_price",
    "score",
    "expected_return",
    "model_name",
    "reason",
    "hold_seconds",
    "profit_rate",
    "message",
    # Market regime dry-run 메타 — 매수 이벤트 시 진입 시점 매크로를 같이 박는다.
    # 매도 이벤트는 빈값 허용(진입 시점 메타가 의미 적음).
    "market_regime",
    "market_gate_action",
    "market_gate_reason",
]

# update_training_labels 가 success_10m 라벨 분기에 사용하는 임계.
# main.py 의 MIN_EXPECTED_RETURN 과 동일 의미. 두 곳에 두지 않기 위해 본 모듈을
# 단일 출처로 둔다.
MIN_EXPECTED_RETURN = 0.006


def _attach_market_meta(row: Dict[str, Any], ctx: Any, decision: Any) -> None:
    """row 에 MARKET_FIELDS + MARKET_GATE_FIELDS 를 채워 넣는다(in-place).

    ``ctx.market_state`` 가 None 이면 5개 매크로 컬럼은 빈 문자열, gate 메타 2개는
    decision 에서 그대로 가져온다(_apply_market_gate 가 None ctx 도 neutral fallback
    으로 채워주므로 항상 string).
    """
    snap = getattr(ctx, "market_state", None)
    if snap is not None:
        row.update(snap.as_row_dict())
    else:
        for key in MARKET_FIELDS:
            row[key] = ""
    row["market_gate_action"] = getattr(decision, "market_gate_action", "") or ""
    row["market_gate_reason"] = getattr(decision, "market_gate_reason", "") or ""


def _is_regular_dante_capture_session(ts: float) -> bool:
    """단테 학습 표본을 남길 수 있는 평일 장중 매수 관찰 구간인지 확인한다."""
    local = time.localtime(ts)
    if local.tm_wday >= 5:
        return False
    hhmmss = local.tm_hour * 10000 + local.tm_min * 100 + local.tm_sec
    return DANTE_CAPTURE_START_HHMMSS <= hhmmss <= DANTE_CAPTURE_END_HHMMSS


# ---------------------------------------------------------------------------
# Mixin
# ---------------------------------------------------------------------------


class TrainingRecorderMixin:
    """학습/거래 로그 CSV 기록 메서드 모음.

    Kiwoom 클래스에 mixin 으로 합쳐진다. ``__init__`` 에서 다음 인스턴스 필드가
    이미 만들어져 있다고 가정한다(현재 main.Kiwoom 이 모두 충족).

      - ``self.pending_training_samples``        : Dict[str, dict]
      - ``self.last_training_sample_at``         : Dict[str, float]
      - ``self.pending_dante_samples``           : Dict[str, dict]
      - ``self.last_dante_sample_at``            : Dict[str, float]
      - ``self.pending_dante_shadow_samples``    : Dict[str, dict]
      - ``self.last_dante_shadow_sample_at``     : Dict[str, float]

    외부 메서드 의존:
      - ``self.normalize_code(code)``  (update_training_labels 가 사용)
    """

    # ------------------------------------------------------------------
    # 구학습 트랙(entry_training.csv) — 현재 비활성
    # ------------------------------------------------------------------

    def ensure_training_data_file(self) -> None:
        if not TRAINING_DATA_ENABLED:
            return
        os.makedirs(TRAINING_DATA_DIR, exist_ok=True)
        if os.path.exists(TRAINING_ENTRY_CSV):
            return
        with open(TRAINING_ENTRY_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=TRAINING_ENTRY_FIELDS)
            writer.writeheader()

    def append_training_row(self, row: Dict[str, Any]) -> None:
        if not TRAINING_DATA_ENABLED:
            return
        self.ensure_training_data_file()
        with open(TRAINING_ENTRY_CSV, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=TRAINING_ENTRY_FIELDS)
            writer.writerow(row)

    def register_training_sample(
        self,
        code: str,
        name: str,
        entry_price: int,
        features: Dict[str, float],
        prediction: Dict[str, Any],
    ) -> None:
        if not TRAINING_DATA_ENABLED:
            return
        now = time.time()
        last_at = self.last_training_sample_at.get(code, 0)
        if now - last_at < TRAINING_SAMPLE_COOLDOWN_SECONDS:
            return

        sample_id = uuid.uuid4().hex
        row = {
            "sample_id": sample_id,
            "captured_at": now,
            "captured_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "code": code,
            "name": name,
            "entry_price": entry_price,
            "score": prediction.get("score", 0),
            "expected_return": prediction.get("expected_return", 0),
            "target_price": prediction.get("target_price", entry_price),
            "model_name": prediction.get("model_name", ""),
            "status": prediction.get("status", ""),
            "reason": prediction.get("reason", ""),
        }
        for feature_name in ENTRY_FEATURE_NAMES:
            row[feature_name] = features.get(feature_name, 0)
        for horizon in TRAINING_LABEL_HORIZONS:
            row["return_{}m".format(horizon // 60)] = ""
        row["success_10m"] = ""

        self.pending_training_samples[sample_id] = {
            "code": code,
            "captured_at": now,
            "entry_price": entry_price,
            "row": row,
            "labeled_horizons": set(),
        }
        self.last_training_sample_at[code] = now
        logger.info(
            "[학습데이터 후보] {} {} 기준가 {} sample {}".format(
                name, code, entry_price, sample_id[:8]
            )
        )

    def update_training_labels(self, code: str, current_price: int, received_at: float) -> None:
        if not TRAINING_DATA_ENABLED:
            return
        code = self.normalize_code(code)
        completed = []
        for sample_id, sample in list(self.pending_training_samples.items()):
            if sample["code"] != code:
                continue
            elapsed = received_at - sample["captured_at"]
            for horizon in TRAINING_LABEL_HORIZONS:
                if horizon in sample["labeled_horizons"] or elapsed < horizon:
                    continue
                return_rate = current_price / sample["entry_price"] - 1
                sample["row"]["return_{}m".format(horizon // 60)] = return_rate
                sample["labeled_horizons"].add(horizon)
            if len(sample["labeled_horizons"]) == len(TRAINING_LABEL_HORIZONS):
                return_10m = sample["row"].get("return_10m", 0)
                sample["row"]["success_10m"] = 1 if return_10m >= MIN_EXPECTED_RETURN else 0
                self.append_training_row(sample["row"])
                completed.append(sample_id)
                logger.info(
                    "[학습데이터 저장] {} sample {} 10분수익률 {:.2%}".format(
                        code, sample_id[:8], return_10m
                    )
                )

        for sample_id in completed:
            self.pending_training_samples.pop(sample_id, None)

    # ------------------------------------------------------------------
    # 단테 학습 트랙(Phase A)
    # ------------------------------------------------------------------

    def ensure_dante_training_data_file(self) -> None:
        if not DANTE_TRAINING_DATA_ENABLED:
            return
        os.makedirs(TRAINING_DATA_DIR, exist_ok=True)
        if os.path.exists(DANTE_TRAINING_CSV):
            return
        with open(DANTE_TRAINING_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=DANTE_TRAINING_FIELDS)
            writer.writeheader()

    def append_dante_training_row(self, row: Dict[str, Any]) -> None:
        if not DANTE_TRAINING_DATA_ENABLED:
            return
        self.ensure_dante_training_data_file()
        with open(DANTE_TRAINING_CSV, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=DANTE_TRAINING_FIELDS)
            writer.writerow(row)

    def register_dante_training_sample(
        self,
        *,
        code: str,
        name: str,
        ctx: Any,
        decision: Any,
        current_price: int,
    ) -> None:
        """1차/2차 매수 'ready' 결정 직후 호출. 진입 피처를 캡처하고 사후 라벨링 큐에 등록한다.

        실제 매수 발주(send_order) 와 무관하게 호출된다.
        매수 차단/실패가 일어나도 단테 게이트가 'ready' 라고 판단했으면 가설 표본으로 누적한다.
        같은 종목에서 1분 안에 두 번 ready 가 떨어져도 한 번만 기록한다.
        """
        if not DANTE_TRAINING_DATA_ENABLED:
            return
        if decision is None or getattr(decision, "status", "") != "ready":
            return
        if current_price <= 0:
            return

        now = time.time()
        last_at = self.last_dante_sample_at.get(code, 0)
        if now - last_at < DANTE_TRAINING_SAMPLE_COOLDOWN_SECONDS:
            return

        five_min = ctx.five_min_ind
        env_upper = five_min.env_upper_13_25 if five_min is not None else None
        bb_upper = five_min.bb_upper_55_2 if five_min is not None else None
        closes_count = five_min.closes_count if five_min is not None else 0
        breakout_high = ctx.position.breakout_high if ctx.position is not None else 0
        obs_elapsed = now - (ctx.condition_registered_at or now)

        features = scoring.build_dante_entry_features(
            current_price=current_price,
            chejan_strength=ctx.chejan_strength,
            volume_speed=ctx.volume_speed,
            spread_rate=ctx.spread_rate,
            obs_elapsed_sec=obs_elapsed,
            env_upper_13=env_upper,
            bb_upper_55=bb_upper,
            five_min_closes_count=closes_count,
            breakout_high=breakout_high,
            minute_bars=ctx.minute_bars,
            chejan_strength_history=ctx.chejan_strength_history,
            is_breakout_zero_bar=ctx.is_breakout_zero_bar,
            is_breakout_prev_bar=ctx.is_breakout_prev_bar,
            upper_wick_ratio=ctx.upper_wick_ratio_zero_bar,
            open_return=ctx.open_return,
        )

        sample_id = uuid.uuid4().hex
        row = {
            "sample_id": sample_id,
            "captured_at": now,
            "captured_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "code": code,
            "name": name,
            "entry_stage": int(getattr(decision, "stage", 1)),
            "entry_price": int(current_price),
            "ratio": float(getattr(decision, "ratio", 0.0)),
            "reason": getattr(decision, "reason", ""),
        }
        row.update(features)
        for horizon in DANTE_TRAINING_LABEL_HORIZONS:
            row["return_{}m".format(horizon // 60)] = ""
        row["max_return_25m"] = ""
        row["min_return_25m"] = ""
        row["reached_1r"] = ""
        row["reached_2r"] = ""
        row["hit_stop"] = ""
        row["time_exit"] = ""
        row["labeled_at"] = ""
        _attach_market_meta(row, ctx, decision)

        self.pending_dante_samples[sample_id] = {
            "code": code,
            "captured_at": now,
            "entry_price": int(current_price),
            "row": row,
            "labeled_horizons": set(),
            "max_price": int(current_price),
            "min_price": int(current_price),
            "finalized": False,
        }
        self.last_dante_sample_at[code] = now
        logger.info(
            "[단테 학습데이터] 후보 등록 {} {} stage={} ratio={:.2f} sample {}".format(
                name, code, row["entry_stage"], row["ratio"], sample_id[:8]
            )
        )

    def update_dante_training_labels(
        self, code: str, current_price: int, received_at: float
    ) -> None:
        """매 틱 수신 시 호출. 진행 중인 단테 샘플에 max/min/horizon 라벨을 갱신한다.

        25분 경과한 샘플은 reached_1r/reached_2r/hit_stop/time_exit 를 확정하고 CSV 에 flush.
        """
        if not DANTE_TRAINING_DATA_ENABLED:
            return
        if not self.pending_dante_samples:
            return
        if current_price is None or current_price <= 0:
            return
        completed = []
        for sample_id, sample in list(self.pending_dante_samples.items()):
            if sample.get("finalized"):
                continue
            if sample.get("code") != code:
                continue
            entry_price = sample.get("entry_price", 0)
            if entry_price <= 0:
                continue
            elapsed = received_at - sample.get("captured_at", received_at)
            if current_price > sample.get("max_price", current_price):
                sample["max_price"] = current_price
            if current_price < sample.get("min_price", current_price):
                sample["min_price"] = current_price
            for horizon in DANTE_TRAINING_LABEL_HORIZONS:
                if horizon in sample["labeled_horizons"] or elapsed < horizon:
                    continue
                sample["row"]["return_{}m".format(horizon // 60)] = current_price / entry_price - 1
                sample["labeled_horizons"].add(horizon)
            if elapsed >= DANTE_TRAINING_FINAL_HORIZON_SECONDS:
                row = sample["row"]
                max_ret = sample["max_price"] / entry_price - 1
                min_ret = sample["min_price"] / entry_price - 1
                r_unit = exit_strategy.R_UNIT_PCT
                row["max_return_25m"] = max_ret
                row["min_return_25m"] = min_ret
                row["reached_1r"] = 1 if max_ret >= r_unit * exit_strategy.EXIT_BE_R else 0
                row["reached_2r"] = 1 if max_ret >= r_unit * exit_strategy.EXIT_PARTIAL_R else 0
                row["hit_stop"] = 1 if min_ret <= -r_unit else 0
                row["time_exit"] = 1 if max_ret < r_unit * exit_strategy.EXIT_BE_R else 0
                row["labeled_at"] = received_at
                self.append_dante_training_row(row)
                sample["finalized"] = True
                completed.append(sample_id)
                logger.info(
                    "[단테 학습데이터] 라벨 완료 {} sample {} max {:.2%} min {:.2%} 1R={} 2R={} stop={}".format(
                        code, sample_id[:8], max_ret, min_ret,
                        row["reached_1r"], row["reached_2r"], row["hit_stop"],
                    )
                )
        for sample_id in completed:
            self.pending_dante_samples.pop(sample_id, None)

    # ------------------------------------------------------------------
    # 단테 shadow 학습 트랙 (false-negative 측정)
    # ------------------------------------------------------------------

    def ensure_dante_shadow_training_data_file(self) -> None:
        if not DANTE_SHADOW_TRAINING_DATA_ENABLED:
            return
        os.makedirs(TRAINING_DATA_DIR, exist_ok=True)
        if os.path.exists(DANTE_SHADOW_TRAINING_CSV):
            return
        with open(DANTE_SHADOW_TRAINING_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=DANTE_SHADOW_TRAINING_FIELDS)
            writer.writeheader()

    def append_dante_shadow_training_row(self, row: Dict[str, Any]) -> None:
        if not DANTE_SHADOW_TRAINING_DATA_ENABLED:
            return
        self.ensure_dante_shadow_training_data_file()
        with open(DANTE_SHADOW_TRAINING_CSV, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=DANTE_SHADOW_TRAINING_FIELDS)
            writer.writerow(row)

    def _is_dante_shadow_data_ready(self, ctx: Any) -> bool:
        """shadow 표본을 등록할지 판단하는 데이터 사전조건 게이트.

        의미 있는 false-negative 측정을 하려면, 게이트가 거절한 이유가 "데이터 부족"이
        아니라 "전략 임계 미달" 이어야 한다. 그렇지 않은 표본(틱 부족/관찰시간 부족/
        5분봉 캐시 미준비) 은 분석 가치가 없으므로 여기서 모두 걸러낸다.
        이미 본진입까지 끝난 종목(entry_stage>=2) 도 매수 여지가 없으므로 제외한다.
        """
        ctx_now = getattr(ctx, "now_ts", None)
        if ctx_now is None:
            ctx_now = time.time()
        if not _is_regular_dante_capture_session(float(ctx_now)):
            return False
        if ctx.position is not None and ctx.position.entry_stage >= 2:
            return False
        if ctx.current_price <= 0 or ctx.ask <= 0 or ctx.bid <= 0:
            return False
        if ctx.tick_count < entry_strategy.DANTE_MIN_TICKS:
            return False
        elapsed = ctx.now_ts - (ctx.condition_registered_at or ctx.now_ts)
        if elapsed < entry_strategy.DANTE_MIN_OBSERVATION_SECONDS:
            return False
        if ctx.five_min_ind is None or ctx.five_min_ind.closes_count < 13:
            return False
        return True

    def register_dante_shadow_sample(
        self,
        *,
        code: str,
        name: str,
        ctx: Any,
        decision: Any,
        current_price: int,
    ) -> None:
        """게이트가 wait/blocked 으로 거른 1차/2차 평가 결과를 사후 라벨링용으로 캡처한다.

        ready 표본(dante_entry_training.csv) 과 짝을 이루어 false-negative 측정에 쓰인다.
        진입 피처 계산은 ready 경로(register_dante_training_sample) 와 동일하게 수행하며,
        구분을 위해 row 첫 컬럼에 decision_status("wait"|"blocked") 를 추가한다.
        같은 종목의 wait 가 줄줄이 발생해도 cooldown 으로 한 번만 기록한다.
        """
        if not DANTE_SHADOW_TRAINING_DATA_ENABLED:
            return
        if decision is None:
            return
        status = getattr(decision, "status", "")
        if status not in ("wait", "blocked"):
            return
        if current_price <= 0:
            return
        if not self._is_dante_shadow_data_ready(ctx):
            return

        now = time.time()
        last_at = self.last_dante_shadow_sample_at.get(code, 0)
        if now - last_at < DANTE_SHADOW_SAMPLE_COOLDOWN_SECONDS:
            return

        five_min = ctx.five_min_ind
        env_upper = five_min.env_upper_13_25 if five_min is not None else None
        bb_upper = five_min.bb_upper_55_2 if five_min is not None else None
        closes_count = five_min.closes_count if five_min is not None else 0
        breakout_high = ctx.position.breakout_high if ctx.position is not None else 0
        obs_elapsed = now - (ctx.condition_registered_at or now)

        features = scoring.build_dante_entry_features(
            current_price=current_price,
            chejan_strength=ctx.chejan_strength,
            volume_speed=ctx.volume_speed,
            spread_rate=ctx.spread_rate,
            obs_elapsed_sec=obs_elapsed,
            env_upper_13=env_upper,
            bb_upper_55=bb_upper,
            five_min_closes_count=closes_count,
            breakout_high=breakout_high,
            minute_bars=ctx.minute_bars,
            chejan_strength_history=ctx.chejan_strength_history,
            is_breakout_zero_bar=ctx.is_breakout_zero_bar,
            is_breakout_prev_bar=ctx.is_breakout_prev_bar,
            upper_wick_ratio=ctx.upper_wick_ratio_zero_bar,
            open_return=ctx.open_return,
        )

        sample_id = uuid.uuid4().hex
        row = {
            "decision_status": status,
            "reason_code": getattr(decision, "reason_code", ""),
            "sample_id": sample_id,
            "captured_at": now,
            "captured_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "code": code,
            "name": name,
            "entry_stage": int(getattr(decision, "stage", 1)),
            "entry_price": int(current_price),
            "ratio": 0.0,
            "reason": getattr(decision, "reason", ""),
        }
        row.update(features)
        for horizon in DANTE_TRAINING_LABEL_HORIZONS:
            row["return_{}m".format(horizon // 60)] = ""
        row["max_return_25m"] = ""
        row["min_return_25m"] = ""
        row["reached_1r"] = ""
        row["reached_2r"] = ""
        row["hit_stop"] = ""
        row["time_exit"] = ""
        row["labeled_at"] = ""
        _attach_market_meta(row, ctx, decision)

        self.pending_dante_shadow_samples[sample_id] = {
            "code": code,
            "captured_at": now,
            "entry_price": int(current_price),
            "row": row,
            "labeled_horizons": set(),
            "max_price": int(current_price),
            "min_price": int(current_price),
            "finalized": False,
        }
        self.last_dante_shadow_sample_at[code] = now
        logger.info(
            "[단테 shadow] 후보 등록 {} {} status={} stage={} sample {}".format(
                name, code, status, row["entry_stage"], sample_id[:8]
            )
        )

    def update_dante_shadow_training_labels(
        self, code: str, current_price: int, received_at: float
    ) -> None:
        """매 틱 수신 시 호출. 진행 중인 shadow 샘플에 max/min/horizon 라벨을 갱신한다.

        구조는 update_dante_training_labels 와 동일하지만 별도 dict/CSV 에 쓴다.
        25분 경과 시 reached_1r/reached_2r/hit_stop/time_exit 를 확정하고 shadow CSV 에 flush.
        """
        if not DANTE_SHADOW_TRAINING_DATA_ENABLED:
            return
        if not self.pending_dante_shadow_samples:
            return
        if current_price is None or current_price <= 0:
            return
        completed = []
        for sample_id, sample in list(self.pending_dante_shadow_samples.items()):
            if sample.get("finalized"):
                continue
            if sample.get("code") != code:
                continue
            entry_price = sample.get("entry_price", 0)
            if entry_price <= 0:
                continue
            elapsed = received_at - sample.get("captured_at", received_at)
            if current_price > sample.get("max_price", current_price):
                sample["max_price"] = current_price
            if current_price < sample.get("min_price", current_price):
                sample["min_price"] = current_price
            for horizon in DANTE_TRAINING_LABEL_HORIZONS:
                if horizon in sample["labeled_horizons"] or elapsed < horizon:
                    continue
                sample["row"]["return_{}m".format(horizon // 60)] = current_price / entry_price - 1
                sample["labeled_horizons"].add(horizon)
            if elapsed >= DANTE_TRAINING_FINAL_HORIZON_SECONDS:
                row = sample["row"]
                max_ret = sample["max_price"] / entry_price - 1
                min_ret = sample["min_price"] / entry_price - 1
                r_unit = exit_strategy.R_UNIT_PCT
                row["max_return_25m"] = max_ret
                row["min_return_25m"] = min_ret
                row["reached_1r"] = 1 if max_ret >= r_unit * exit_strategy.EXIT_BE_R else 0
                row["reached_2r"] = 1 if max_ret >= r_unit * exit_strategy.EXIT_PARTIAL_R else 0
                row["hit_stop"] = 1 if min_ret <= -r_unit else 0
                row["time_exit"] = 1 if max_ret < r_unit * exit_strategy.EXIT_BE_R else 0
                row["labeled_at"] = received_at
                self.append_dante_shadow_training_row(row)
                sample["finalized"] = True
                completed.append(sample_id)
                logger.info(
                    "[단테 shadow] 라벨 완료 {} sample {} status={} max {:.2%} min {:.2%} 1R={} stop={}".format(
                        code, sample_id[:8], row["decision_status"], max_ret, min_ret,
                        row["reached_1r"], row["hit_stop"],
                    )
                )
        for sample_id in completed:
            self.pending_dante_shadow_samples.pop(sample_id, None)

    # ------------------------------------------------------------------
    # 거래 로그 (모든 매수/매도 이벤트)
    # ------------------------------------------------------------------

    def ensure_trade_log_file(self) -> None:
        os.makedirs(TRAINING_DATA_DIR, exist_ok=True)
        if os.path.exists(TRADE_LOG_CSV):
            return
        with open(TRADE_LOG_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=TRADE_LOG_FIELDS)
            writer.writeheader()

    def append_trade_log(self, event: str, **kwargs: Any) -> None:
        self.ensure_trade_log_file()
        row: Dict[str, Any] = {field: "" for field in TRADE_LOG_FIELDS}
        row["logged_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        row["event"] = event
        for key, value in kwargs.items():
            if key in row:
                row[key] = value
        with open(TRADE_LOG_CSV, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=TRADE_LOG_FIELDS)
            writer.writerow(row)
