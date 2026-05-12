"""캐시된 1분봉 CSV(``data/intraday/YYYYMMDD/<code>.csv``) 로
   정밀 메트릭 + D 피처 계산. 키움 API 직접 호출 없음.

본 모듈은 ``fetch_minute_bars.py`` 가 미리 저장해둔 CSV 만 읽는다. 캐시가
없으면 ``dante_entry_training`` 의 5분봉 라벨로 fallback 한다(metric_source
필드로 구분).

산출 메트릭(``Trade.metrics`` 에 추가):
    return_1m, return_3m, return_5m
    max_profit_3m, max_drawdown_3m
    max_profit_5m, max_drawdown_5m
    buy_price_to_1m_low_pct
    buy_price_to_3m_high_pct
    metric_source ("kiwoom_1m_csv" | "fallback_5m_approx" | "missing")

D 피처(``Trade.features`` 에 추가):
    obs_elapsed_sec               (dante_entry_training 에서 이미 채워짐)
    pullback_pct_from_high        (dante_entry_training 에서 이미 채워짐)
    entry_after_peak_sec
    high_to_entry_drop_pct
    entry_near_session_high       (1=True, 0=False)
    entry_vs_vwap_pct
    volume_ratio_1m
    breakout_candle_body_pct
    upper_wick_pct
    prior_3m_return_pct
    prior_5m_return_pct
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence


INTRADAY_DIR_DEFAULT = os.path.join("data", "intraday")

# 진입 1분봉 거래량 비교에 쓸 직전 N개
VOLUME_LOOKBACK_BARS = 5
# session_high 근접 임계 (entry_price / high >= 0.99 → near)
NEAR_SESSION_HIGH_RATIO = 0.99


@dataclass
class Bar:
    dt: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def _csv_path(intraday_dir: str, target_date: str, code: str) -> str:
    yyyymmdd = target_date.replace("-", "")
    return os.path.join(intraday_dir, yyyymmdd, f"{code}.csv")


def load_minute_bars(target_date: str, code: str, intraday_dir: str = INTRADAY_DIR_DEFAULT) -> List[Bar]:
    path = _csv_path(intraday_dir, target_date, code)
    if not os.path.exists(path):
        return []
    out: List[Bar] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                dt = datetime.strptime(row["datetime"], "%Y-%m-%d %H:%M:%S")
            except (KeyError, ValueError):
                continue
            try:
                out.append(Bar(
                    dt=dt,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                ))
            except (KeyError, TypeError, ValueError):
                continue
    out.sort(key=lambda b: b.dt)
    return out


# ---------------------------------------------------------------------------
# 메트릭 / D 피처 계산
# ---------------------------------------------------------------------------


def _bar_at_or_after(bars: Sequence[Bar], ts: datetime) -> Optional[int]:
    """ts 가 속한 분봉의 인덱스를 두 가지 시각 형식 모두에서 견고하게 찾는다.

    키움 opt10080 응답의 체결시간이 분 *시작* 시각(예: 09:06:00 = 09:06:00~09:07:00 봉)
    인지 분 *종료* 시각(예: 09:07:00 = 09:06:00~09:07:00 봉) 인지 환경에 따라 다를
    수 있다. 두 형식 모두에서 동일한 분봉으로 매칭되도록 다음 우선순위로 찾는다:

      1) bar.dt == minute_start(ts 의 분 시작) — 시작 시각 형식
      2) bar.dt == minute_end(ts 의 분 시작 + 1분) — 종료 시각 형식
      3) ts 의 분 시작 ± 60초 안에 있는 가장 가까운 봉 — 정의가 더 모호한 경우
      4) ts 직전(<= ts) 가장 가까운 봉 — 최후 fallback

    어떤 가정이 사용됐는지는 호출측에서 알 필요 없도록 인덱스만 반환한다.
    """
    if not bars:
        return None
    minute_start = ts.replace(second=0, microsecond=0)
    minute_end = minute_start + timedelta(minutes=1)

    # 1) 분 시작 시각 형식 우선
    for i, bar in enumerate(bars):
        if bar.dt == minute_start:
            return i
    # 2) 분 종료 시각 형식
    for i, bar in enumerate(bars):
        if bar.dt == minute_end:
            return i
    # 3) ts 의 분 시작 ± 60초 안에 가장 가까운 봉 (분 단위 정렬이 안 된 경우)
    best_idx = None
    best_delta = timedelta(seconds=60)
    for i, bar in enumerate(bars):
        delta = abs(bar.dt - minute_start)
        if delta <= best_delta:
            best_delta = delta
            best_idx = i
    if best_idx is not None:
        return best_idx
    # 4) ts 직전 가장 가까운 봉
    last_idx = None
    for i, bar in enumerate(bars):
        if bar.dt > ts:
            break
        last_idx = i
    return last_idx


def _bars_in_window(bars: Sequence[Bar], start_idx: int, minutes: int) -> List[Bar]:
    end_dt = bars[start_idx].dt + timedelta(minutes=minutes)
    out: List[Bar] = []
    for bar in bars[start_idx:]:
        if bar.dt > end_dt:
            break
        out.append(bar)
    return out


def _safe_div(num: float, den: float) -> Optional[float]:
    if den == 0:
        return None
    return num / den


def _vwap_until(bars: Sequence[Bar], idx: int) -> Optional[float]:
    """0..idx 까지(포함) 누적 VWAP. 종가 가중 평균(typical price 대신)."""
    cum_pv, cum_v = 0.0, 0.0
    for bar in bars[: idx + 1]:
        cum_pv += bar.close * bar.volume
        cum_v += bar.volume
    if cum_v <= 0:
        return None
    return cum_pv / cum_v


def _session_high_until(bars: Sequence[Bar], idx: int) -> Optional[Bar]:
    if idx < 0 or idx >= len(bars):
        return None
    best = bars[0]
    for bar in bars[: idx + 1]:
        if bar.high > best.high:
            best = bar
    return best


def compute_intraday_metrics(
    entry_time: datetime,
    entry_price: float,
    bars: Sequence[Bar],
) -> Dict[str, Optional[float]]:
    """1분봉 시퀀스로 정밀 메트릭 + D 피처를 만든다.

    bars 가 비어있거나 entry_time 분봉을 못 찾으면 빈 dict 반환(호출측이 fallback).
    """
    if not bars or entry_price <= 0:
        return {}
    idx = _bar_at_or_after(bars, entry_time)
    if idx is None:
        return {}

    out: Dict[str, Optional[float]] = {}

    # ---- 정밀 메트릭 ----
    # 데이터가 부족할 때(예: 진입봉이 캐시의 마지막 봉) 거짓 0% 메트릭이 나오는
    # 것을 막기 위해 N분 메트릭은 *N+1 개 봉이 모두 있을 때만* 산출한다.
    # 진입봉(idx) + N개 후행봉이 있어야 N분 후 가격을 알 수 있기 때문.
    def _ret_after(minutes: int) -> Optional[float]:
        window = _bars_in_window(bars, idx, minutes)
        if len(window) < minutes + 1:
            return None
        last_close = window[-1].close
        return _safe_div(last_close - entry_price, entry_price)

    def _max_profit_after(minutes: int) -> Optional[float]:
        window = _bars_in_window(bars, idx, minutes)
        if len(window) < minutes + 1:
            return None
        hi = max(b.high for b in window)
        return _safe_div(hi - entry_price, entry_price)

    def _max_drawdown_after(minutes: int) -> Optional[float]:
        window = _bars_in_window(bars, idx, minutes)
        if len(window) < minutes + 1:
            return None
        lo = min(b.low for b in window)
        return _safe_div(lo - entry_price, entry_price)

    out["return_1m"] = _ret_after(1)
    out["return_3m"] = _ret_after(3)
    out["return_5m_intraday"] = _ret_after(5)
    out["max_profit_3m"] = _max_profit_after(3)
    out["max_drawdown_3m"] = _max_drawdown_after(3)
    out["max_profit_5m"] = _max_profit_after(5)
    out["max_drawdown_5m"] = _max_drawdown_after(5)
    out["buy_price_to_1m_low_pct"] = _max_drawdown_after(1)
    out["buy_price_to_3m_high_pct"] = _max_profit_after(3)

    # ---- D 피처 ----
    entry_bar = bars[idx]
    body = abs(entry_bar.close - entry_bar.open)
    rng = entry_bar.high - entry_bar.low
    out["breakout_candle_body_pct"] = _safe_div(body, rng)
    out["upper_wick_pct"] = _safe_div(
        entry_bar.high - max(entry_bar.open, entry_bar.close), rng,
    )

    prior_window = bars[max(0, idx - VOLUME_LOOKBACK_BARS): idx]
    if prior_window:
        avg_vol = sum(b.volume for b in prior_window) / len(prior_window)
        out["volume_ratio_1m"] = _safe_div(entry_bar.volume, avg_vol)

    if idx >= 3:
        prev_close_3m = bars[idx - 3].close
        out["prior_3m_return_pct"] = _safe_div(entry_price - prev_close_3m, prev_close_3m)
    if idx >= 5:
        prev_close_5m = bars[idx - 5].close
        out["prior_5m_return_pct"] = _safe_div(entry_price - prev_close_5m, prev_close_5m)

    vwap = _vwap_until(bars, idx)
    if vwap is not None and vwap > 0:
        out["entry_vs_vwap_pct"] = _safe_div(entry_price - vwap, vwap)

    session_high_bar = _session_high_until(bars, idx)
    if session_high_bar is not None:
        sh = session_high_bar.high
        out["high_to_entry_drop_pct"] = _safe_div(sh - entry_price, sh)
        if sh > 0:
            out["entry_near_session_high"] = 1.0 if (entry_price / sh) >= NEAR_SESSION_HIGH_RATIO else 0.0
        out["entry_after_peak_sec"] = max(0.0, (entry_time - session_high_bar.dt).total_seconds())

    return out


# ---------------------------------------------------------------------------
# fallback (5분봉 라벨)
# ---------------------------------------------------------------------------


def compute_fallback_metrics(trade) -> Dict[str, Optional[float]]:
    """1분봉 캐시가 없을 때 dante_entry_training 의 5분봉 라벨로 근사.

    1분/3분 메트릭은 None. 5분 메트릭만 채우고 max_profit_3m / max_drawdown_3m
    는 max_return_25m / min_return_25m 의 보수적 사본으로 둔다(상한/하한 정보가
    있으니 의사결정에는 쓸 수 있음).
    """
    out: Dict[str, Optional[float]] = {
        "return_1m": None,
        "return_3m": None,
        "return_5m_intraday": trade.return_5m,
        "max_profit_3m": None,
        "max_drawdown_3m": None,
        "max_profit_5m": trade.max_return_25m,
        "max_drawdown_5m": trade.min_return_25m,
        "buy_price_to_1m_low_pct": None,
        "buy_price_to_3m_high_pct": None,
    }
    return out


# ---------------------------------------------------------------------------
# Trade 부착
# ---------------------------------------------------------------------------


def attach_intraday_metrics(
    trades: Sequence,
    target_date: str,
    intraday_dir: str = INTRADAY_DIR_DEFAULT,
) -> Dict[str, List[str]]:
    """모든 Trade 에 1분봉 정밀 메트릭(또는 fallback) 을 attach.

    반환: {"with_intraday": [...code], "fallback": [...code], "missing": [...code]}
        - with_intraday : 1분봉 CSV 로 정밀 계산 성공
        - fallback      : 1분봉 없음 → 5분봉 근사 사용
        - missing       : 1분봉도 없고 5분봉 라벨도 없음(메트릭 비어있음)
    """
    summary: Dict[str, List[str]] = {"with_intraday": [], "fallback": [], "missing": []}
    for trade in trades:
        if not trade.entry_first_time or not trade.entry_avg_price:
            trade.metrics["metric_source"] = "missing"
            summary["missing"].append(trade.code)
            continue

        bars = load_minute_bars(target_date, trade.code, intraday_dir)
        precise = compute_intraday_metrics(
            trade.entry_first_time, float(trade.entry_avg_price), bars,
        )

        if precise:
            for k, v in precise.items():
                if k in {
                    "breakout_candle_body_pct", "upper_wick_pct", "volume_ratio_1m",
                    "prior_3m_return_pct", "prior_5m_return_pct",
                    "entry_vs_vwap_pct", "high_to_entry_drop_pct",
                    "entry_near_session_high", "entry_after_peak_sec",
                }:
                    if v is not None:
                        trade.features[k] = v
                else:
                    trade.metrics[k] = v
            trade.metrics["metric_source"] = "kiwoom_1m_csv"
            summary["with_intraday"].append(trade.code)
            continue

        fallback = compute_fallback_metrics(trade)
        if any(v is not None for v in fallback.values()):
            for k, v in fallback.items():
                trade.metrics[k] = v
            trade.metrics["metric_source"] = "fallback_5m_approx"
            summary["fallback"].append(trade.code)
        else:
            trade.metrics["metric_source"] = "missing"
            summary["missing"].append(trade.code)
    return summary
