"""일별 시장 컨텍스트(KOSPI/KOSDAQ 등락률 등) 를 trade_review 에 join.

진입/청산 통계는 그날 시장이 강세였는지 약세였는지에 따라 분포가 크게 다르다.
약세장 표본만으로 룰 임계를 빡빡하게 끌어내리고, 다음 강세장에 그대로 유지되면
진입이 거의 일어나지 않게 된다. 이를 막기 위해 매일의 시장 컨텍스트(KOSPI/KOSDAQ
의 종가 등락률 + 일중 최대상승률)를 한 줄짜리 JSON 으로 누적해 두고, 매 거래에
그 날의 컨텍스트를 join 한다. rolling 통계 단계에서 이 컬럼으로 분리 집계하면
"같은 게이트라도 강세/약세 분리 평균" 을 얻을 수 있다.

데이터 소스:
    {reviews_dir}/market_context_YYYY-MM-DD.json

스키마(``MarketContext.to_dict``):
    {
      "schema": "market_context_v1",
      "date": "2026-04-30",
      "generated_at": "2026-04-30T16:05:00",
      "kospi_close_return": 0.0078,
      "kosdaq_close_return": 0.0114,
      "kospi_intraday_high_return": 0.0125,
      "kosdaq_intraday_high_return": 0.0181,
      "kospi_close": 2_650.5,
      "kosdaq_close": 870.3,
      "source": "kiwoom_opt20006" | "manual" | "..."
    }

자동 fetch 가 어려운 환경(64-bit venv, CI 등)에서도 운영자가 수동으로 JSON 한
줄만 채워 넣으면 분석 파이프라인이 그대로 동작하도록, 모든 필드는 ``Optional`` 이며
파일 자체가 없어도 attach 단계는 graceful 하게 빈 컬럼으로 채운다.

분류:
    classify_market_strength 가 KOSPI 종가 등락률 ±0.5% 를 기준으로 strong/weak/
    neutral 로 단순 3분류한다. 임계는 통계가 쌓이면 추후 데이터 기반으로 재조정.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Dict, Iterable, Optional


_logger = logging.getLogger(__name__)


REVIEWS_DIR_DEFAULT = os.path.join("data", "reviews")
MARKET_CONTEXT_SCHEMA = "market_context_v1"

# 강세/약세 분류 임계 (일단 문헌적 기준으로 시작 — 표본 누적 후 재조정)
STRONG_DAY_RETURN_THRESHOLD = 0.005   # KOSPI 종가 +0.5% 이상
WEAK_DAY_RETURN_THRESHOLD = -0.005    # KOSPI 종가 -0.5% 이하


@dataclass
class MarketContext:
    """일별 매크로 한 줄."""
    date: str
    kospi_close_return: Optional[float] = None
    kosdaq_close_return: Optional[float] = None
    kospi_intraday_high_return: Optional[float] = None
    kosdaq_intraday_high_return: Optional[float] = None
    kospi_close: Optional[float] = None
    kosdaq_close: Optional[float] = None
    generated_at: str = ""
    source: str = ""

    def to_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = {"schema": MARKET_CONTEXT_SCHEMA}
        payload.update(asdict(self))
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "MarketContext":
        date = str(payload.get("date") or "").strip()
        if not date:
            raise ValueError("market_context: date 필드가 비어 있음")

        def _float(key: str) -> Optional[float]:
            value = payload.get(key)
            if value in (None, ""):
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        return cls(
            date=date,
            kospi_close_return=_float("kospi_close_return"),
            kosdaq_close_return=_float("kosdaq_close_return"),
            kospi_intraday_high_return=_float("kospi_intraday_high_return"),
            kosdaq_intraday_high_return=_float("kosdaq_intraday_high_return"),
            kospi_close=_float("kospi_close"),
            kosdaq_close=_float("kosdaq_close"),
            generated_at=str(payload.get("generated_at") or ""),
            source=str(payload.get("source") or ""),
        )


def context_path(date: str, reviews_dir: str = REVIEWS_DIR_DEFAULT) -> str:
    return os.path.join(reviews_dir, f"market_context_{date}.json")


def load_market_context(
    date: str,
    reviews_dir: str = REVIEWS_DIR_DEFAULT,
) -> Optional[MarketContext]:
    """date 의 매크로 JSON 을 읽어 반환. 없거나 손상돼 있으면 None.

    파일 부재는 정상 흐름이며 (자동 매크로 fetch 는 별도 인프라), attach 단계는
    None 을 받아도 빈 컬럼으로 graceful fallback 한다.
    """
    path = context_path(date, reviews_dir)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        _logger.warning("market_context 로드 실패 -- %s 무시: %s", path, exc)
        return None
    if not isinstance(payload, dict):
        return None
    try:
        return MarketContext.from_dict(payload)
    except ValueError as exc:
        _logger.warning("market_context 파싱 실패 -- %s 무시: %s", path, exc)
        return None


def save_market_context(
    ctx: MarketContext,
    reviews_dir: str = REVIEWS_DIR_DEFAULT,
) -> str:
    """매크로 1줄 JSON 을 atomic write 로 저장."""
    os.makedirs(reviews_dir, exist_ok=True)
    if not ctx.generated_at:
        ctx.generated_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    path = context_path(ctx.date, reviews_dir)
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(ctx.to_dict(), f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
        raise
    return path


def classify_market_strength(ctx: Optional[MarketContext]) -> str:
    """KOSPI 종가 등락률 기준 strong / weak / neutral 3분류.

    데이터가 None 이거나 KOSPI 등락률 자체가 None 이면 ``"unknown"``.
    """
    if ctx is None or ctx.kospi_close_return is None:
        return "unknown"
    r = ctx.kospi_close_return
    if r >= STRONG_DAY_RETURN_THRESHOLD:
        return "strong"
    if r <= WEAK_DAY_RETURN_THRESHOLD:
        return "weak"
    return "neutral"


# attach 단계에서 trade.features 에 채울 키 모음. CSV/rolling 단계는 이 키들을 기대.
MARKET_CONTEXT_FEATURE_KEYS = (
    "market_kospi_close_return",
    "market_kosdaq_close_return",
    "market_kospi_intraday_high_return",
    "market_kosdaq_intraday_high_return",
)
MARKET_CONTEXT_LABEL_KEY = "market_strength"


def attach_market_context(
    trades: Iterable,
    target_date: str,
    reviews_dir: str = REVIEWS_DIR_DEFAULT,
    *,
    context: Optional[MarketContext] = None,
) -> Optional[MarketContext]:
    """각 Trade 의 ``features`` 에 매크로 컬럼을 채워 넣는다.

    파일이 없으면 모든 매크로 컬럼은 None 으로 남고 ``market_strength`` 는
    ``"unknown"`` 이 된다. 다른 분석 단계가 매크로 부재를 graceful 하게 처리할 수
    있도록 키 자체는 항상 set 한다.

    Args:
        trades: ``review.loader.Trade`` 의 iterable.
        target_date: 매크로 JSON 파일을 찾을 기준 날짜.
        reviews_dir: 매크로 JSON 디렉토리.
        context: 미리 로드한 MarketContext 가 있으면 재사용(테스트 편의).

    Returns:
        실제로 사용된 MarketContext (또는 None — 데이터 부재).
    """
    ctx = context if context is not None else load_market_context(target_date, reviews_dir)
    strength = classify_market_strength(ctx)
    for trade in trades:
        features = getattr(trade, "features", None)
        if features is None:
            continue
        if ctx is not None:
            features["market_kospi_close_return"] = ctx.kospi_close_return
            features["market_kosdaq_close_return"] = ctx.kosdaq_close_return
            features["market_kospi_intraday_high_return"] = ctx.kospi_intraday_high_return
            features["market_kosdaq_intraday_high_return"] = ctx.kosdaq_intraday_high_return
        else:
            for key in MARKET_CONTEXT_FEATURE_KEYS:
                features.setdefault(key, None)
        features[MARKET_CONTEXT_LABEL_KEY] = strength
    return ctx
