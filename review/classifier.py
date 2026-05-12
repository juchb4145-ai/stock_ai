"""Trade 의 entry_class / exit_class 를 자동 부여한다.

진입 4종 + unclassified:
  - breakout_chase  : A급 0봉 돌파 1차 추격 (보호 패턴 포함)
  - first_pullback  : B급 / 2차 본진입 (눌림 후 진입; late_chase 검사 면제)
  - late_chase      : 진입 시 과열/추격 신호 다발 (PR-D v2 강화)
  - fake_breakout   : 진입 후 한 번도 못 오르고 손절 영역 진입
  - unclassified

청산 4종 + clean_exit:
  - good_stop       : 손절 후 안 반등
  - bad_stop        : +1R 갔다 손절 OR 손절 후 +1R 이상 반등
  - fast_take       : 익절했는데 over_run >= 1R 이고 give_back<=0.3R
  - late_take       : 익절했지만 give_back >= 0.7R
  - clean_exit      : 위 4개에 안 걸린 정상 청산

PR-D 변경(late_chase 강화):
  - 단일 조건이 아니라 10개 조건 중 N개 이상 충족 시 분류
  - 강한 late_chase 패턴은 score 와 무관하게 즉시 트리거
  - 강한 breakout_chase 패턴은 late_chase 점수가 높아도 보호
  - 새 1분봉 피처가 하나도 없으면 v1 (open_return / px_over_bb55_pct) 로 fallback
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from exit_strategy import R_UNIT_PCT

from .loader import Trade


CLASSIFIER_VERSION = "v2"

# === 청산 분류 임계 (기존 유지) ===
FAKE_BREAKOUT_MFE_R = 0.5
FAKE_BREAKOUT_MAE_R = -1.0
GOOD_STOP_BOUNCE_R = 0.5
BAD_STOP_BOUNCE_R = 1.0
FAST_TAKE_OVER_RUN_R = 1.0
FAST_TAKE_GIVE_BACK_R = 0.3
LATE_TAKE_GIVE_BACK_R = 0.7

# === v1 호환 임계 (기존; 새 피처 없을 때 fallback 으로만 사용) ===
LATE_CHASE_OPEN_RETURN = 0.07
LATE_CHASE_BB55_DIST = 0.03

# === PR-D late_chase 강화 임계 (사용자 추천값, 모두 보수적) ===
# 각 임계는 review.intraday 의 D 피처와 1:1 대응한다.
LATE_CHASE_NEAR_HIGH_FLAG = 1.0     # entry_near_session_high == 1
LATE_CHASE_PRIOR_3M = 0.03          # prior_3m_return_pct
LATE_CHASE_PRIOR_5M = 0.05          # prior_5m_return_pct
LATE_CHASE_VS_VWAP = 0.02           # entry_vs_vwap_pct
LATE_CHASE_HIGH_DROP = 0.008        # high_to_entry_drop_pct (낮을수록 고점 근접)
LATE_CHASE_PULLBACK = 0.01          # pullback_pct_from_high
LATE_CHASE_PEAK_SEC = 60            # entry_after_peak_sec
LATE_CHASE_OBS_SEC = 180            # obs_elapsed_sec
LATE_CHASE_UPPER_WICK = 0.35        # upper_wick_pct
LATE_CHASE_WEAK_BODY = 0.45         # breakout_candle_body_pct (낮을수록 약한 몸통)

# 점수 N개 이상 충족 시 late_chase 후보
LATE_CHASE_MIN_SCORE = 3

# === 강한 breakout_chase 보호 패턴 ===
# 모두 동시 충족 시 late_chase 점수 높아도 breakout_chase 로 분류한다.
BREAKOUT_PROTECT_VOL_RATIO = 2.0    # volume_ratio_1m
BREAKOUT_PROTECT_BODY_MIN = 0.55    # breakout_candle_body_pct
BREAKOUT_PROTECT_WICK_MAX = 0.25    # upper_wick_pct

# 새 피처 키 모음 — 이 중 하나라도 features 에 있으면 v2 활성화
NEW_FEATURE_KEYS = (
    "entry_near_session_high",
    "prior_3m_return_pct",
    "prior_5m_return_pct",
    "entry_vs_vwap_pct",
    "high_to_entry_drop_pct",
    "pullback_pct_from_high",
    "entry_after_peak_sec",
    "obs_elapsed_sec",
    "upper_wick_pct",
    "breakout_candle_body_pct",
    "volume_ratio_1m",
)


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------


def _get(features: dict, key: str) -> Optional[float]:
    """피처 dict 에서 값을 꺼낸다. None 또는 NaN 이면 None 반환."""
    v = features.get(key)
    if v is None:
        return None
    try:
        if v != v:   # NaN
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _ge(value: Optional[float], threshold: float) -> bool:
    """value 가 None 이면 False — 사용자 요구 '피처가 None 이면 false 처리'."""
    return value is not None and value >= threshold


def _le(value: Optional[float], threshold: float) -> bool:
    return value is not None and value <= threshold


def _eq(value: Optional[float], target: float) -> bool:
    return value is not None and value == target


def _has_any_new_feature(features: dict) -> bool:
    return any(features.get(k) is not None for k in NEW_FEATURE_KEYS)


# ---------------------------------------------------------------------------
# late_chase 점수 / 강한 패턴 / 보호 패턴
# ---------------------------------------------------------------------------


def _late_chase_score(features: dict) -> Tuple[int, List[str]]:
    """10개 조건 중 충족 개수와 reason 리스트를 반환."""
    reasons: List[str] = []

    near_high = _get(features, "entry_near_session_high")
    prior_3m = _get(features, "prior_3m_return_pct")
    prior_5m = _get(features, "prior_5m_return_pct")
    vs_vwap = _get(features, "entry_vs_vwap_pct")
    high_drop = _get(features, "high_to_entry_drop_pct")
    pullback = _get(features, "pullback_pct_from_high")
    peak_sec = _get(features, "entry_after_peak_sec")
    obs_sec = _get(features, "obs_elapsed_sec")
    wick = _get(features, "upper_wick_pct")
    body = _get(features, "breakout_candle_body_pct")

    if _eq(near_high, LATE_CHASE_NEAR_HIGH_FLAG):
        reasons.append("near_session_high")
    if _ge(prior_3m, LATE_CHASE_PRIOR_3M):
        reasons.append("prior_3m_overshot")
    if _ge(prior_5m, LATE_CHASE_PRIOR_5M):
        reasons.append("prior_5m_overshot")
    if _ge(vs_vwap, LATE_CHASE_VS_VWAP):
        reasons.append("above_vwap")
    if _le(high_drop, LATE_CHASE_HIGH_DROP):
        reasons.append("shallow_drop_from_high")
    if _le(pullback, LATE_CHASE_PULLBACK):
        reasons.append("no_pullback")
    if _ge(peak_sec, LATE_CHASE_PEAK_SEC):
        reasons.append("late_after_peak")
    if _ge(obs_sec, LATE_CHASE_OBS_SEC):
        reasons.append("long_observation")
    if _ge(wick, LATE_CHASE_UPPER_WICK):
        reasons.append("long_upper_wick")
    if _le(body, LATE_CHASE_WEAK_BODY):
        reasons.append("weak_body")

    return len(reasons), reasons


def _is_strong_late_chase(features: dict) -> bool:
    """강한 late_chase 패턴 — 점수 무관하게 트리거.

    "고점 근처 + 직전 3분 과상승 + 눌림 부재" 가 모두 동시.
    """
    near_high = _get(features, "entry_near_session_high")
    prior_3m = _get(features, "prior_3m_return_pct")
    pullback = _get(features, "pullback_pct_from_high")
    return (
        _eq(near_high, LATE_CHASE_NEAR_HIGH_FLAG)
        and _ge(prior_3m, LATE_CHASE_PRIOR_3M)
        and _le(pullback, LATE_CHASE_PULLBACK)
    )


def _is_breakout_protected(features: dict) -> bool:
    """강한 돌파 패턴 보호 — 거래량 급증 + 강한 몸통 + 짧은 윗꼬리 동시."""
    vol_ratio = _get(features, "volume_ratio_1m")
    body = _get(features, "breakout_candle_body_pct")
    wick = _get(features, "upper_wick_pct")
    return (
        _ge(vol_ratio, BREAKOUT_PROTECT_VOL_RATIO)
        and _ge(body, BREAKOUT_PROTECT_BODY_MIN)
        and _le(wick, BREAKOUT_PROTECT_WICK_MAX)
    )


def _v1_late_chase(features: dict) -> Tuple[bool, List[str]]:
    """v1 호환 late_chase. 새 피처가 하나도 없을 때만 fallback 으로 사용.

    open_return / px_over_bb55_pct 만 봄.
    """
    reasons: List[str] = []
    open_return = _get(features, "open_return")
    px_over_bb55 = _get(features, "px_over_bb55_pct")
    if _ge(open_return, LATE_CHASE_OPEN_RETURN):
        reasons.append("v1_open_return_overshot")
    if _ge(px_over_bb55, LATE_CHASE_BB55_DIST):
        reasons.append("v1_px_over_bb55")
    return (len(reasons) > 0, reasons)


# ---------------------------------------------------------------------------
# entry / exit 분류
# ---------------------------------------------------------------------------


def _classify_entry(trade: Trade) -> str:
    """entry_class 결정 + Trade 디버그 필드 채움.

    분류 우선순위:
      1) fake_breakout
      2) first_pullback (B급 / 2차 본진입) — late_chase 검사 면제
      3) late_chase   (PR-D v2 강화)
      4) breakout_chase (A급 / 1차 추격, late_chase 보호 포함)
      5) unclassified
    """
    trade.classifier_version = CLASSIFIER_VERSION

    mfe = trade.metrics.get("mfe_r")
    mae = trade.metrics.get("mae_r")
    if (
        mfe is not None and mae is not None
        and mfe == mfe and mae == mae   # NaN 가드
        and mfe < FAKE_BREAKOUT_MFE_R
        and mae <= FAKE_BREAKOUT_MAE_R
    ):
        return "fake_breakout"

    # B급 / 2차 본진입은 정의상 눌림 진입이라 late_chase 검사 자체를 건너뜀.
    if trade.grade == "B" or trade.entry_stage_max >= 2:
        return "first_pullback"

    # === late_chase 평가 ===
    # v2 score 는 10개 D 피처 조건만 카운트한다(임계값 LATE_CHASE_MIN_SCORE=3 의
    # 의미 단위와 일관되도록). v1 reason 은 별도 필드로 분리해 audit 가독성 보존.
    score, reasons = _late_chase_score(trade.features)
    strong = _is_strong_late_chase(trade.features)
    protected = _is_breakout_protected(trade.features)
    v1_reasons: List[str] = []

    is_late = False
    if _has_any_new_feature(trade.features):
        if not protected:
            if strong or score >= LATE_CHASE_MIN_SCORE:
                is_late = True
    else:
        # 새 피처가 하나도 없으면 v1 호환 — open_return / bb55 만 본다.
        # P1 #10: v1 경로에서도 breakout_chase_protected 검사를 동일하게 적용한다.
        v1_late, v1_reasons = _v1_late_chase(trade.features)
        if v1_late and not protected:
            is_late = True

    if strong and "strong_late_chase_pattern" not in reasons:
        reasons.append("strong_late_chase_pattern")
    # v1 reason 은 score 와 무관하게 audit 에 노출(추적용)
    reasons.extend(v1_reasons)

    trade.late_chase_score = score
    trade.late_chase_reasons = reasons
    trade.breakout_chase_protected = bool(protected)

    if is_late:
        return "late_chase"

    if trade.grade == "A" or trade.entry_stage_max == 1:
        return "breakout_chase"

    # 폴백 정책 — dante_entry_training 매칭이 안 돼서 grade="" 이고 stage=0 인
    # 거래라도, 1분봉 정밀 메트릭(metric_source == "kiwoom_1m_csv")이 부착되어
    # 있으면 정상 진입으로 간주해 breakout_chase 로 분류한다. 그래야 rolling
    # 통계의 by_entry_class 가 "unclassified" 로 채워져 룰 후보 평가가 흔들리는
    # 것을 막는다(P0 #3).
    if trade.metrics.get("metric_source") == "kiwoom_1m_csv":
        return "breakout_chase"

    return "unclassified"


def _classify_exit(trade: Trade) -> str:
    realized = trade.final_return
    if realized is None:
        return "open"

    bounce_r = trade.metrics.get("bounce_after_stop_r")
    over_run_r = trade.metrics.get("over_run_r")
    give_back_r = trade.metrics.get("give_back_r")
    mfe_r = trade.metrics.get("mfe_r")

    # 손절
    if realized < 0:
        be_violation = trade.metrics.get("be_violation", 0.0) >= 1.0
        if be_violation:
            return "bad_stop"
        if bounce_r == bounce_r and bounce_r is not None and bounce_r >= BAD_STOP_BOUNCE_R:
            return "bad_stop"
        if mfe_r == mfe_r and mfe_r is not None and mfe_r >= 1.0:
            return "bad_stop"
        return "good_stop"

    # 익절(또는 본절 위 청산)
    if realized > 0:
        if (
            over_run_r == over_run_r and over_run_r is not None
            and give_back_r == give_back_r and give_back_r is not None
            and over_run_r >= FAST_TAKE_OVER_RUN_R
            and give_back_r <= FAST_TAKE_GIVE_BACK_R
        ):
            return "fast_take"
        if (
            give_back_r == give_back_r and give_back_r is not None
            and give_back_r >= LATE_TAKE_GIVE_BACK_R
        ):
            return "late_take"
        return "clean_exit"

    return "clean_exit"


def classify_trades(trades: Iterable[Trade]) -> None:
    for trade in trades:
        trade.entry_class = _classify_entry(trade)
        trade.exit_class = _classify_exit(trade)
