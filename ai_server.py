import os
from typing import List, Optional

import joblib
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

try:
    import lightgbm as lgb
except ImportError:
    lgb = None


MODEL_PKL_PATH = os.path.join("models", "opening_lgbm.pkl")
MODEL_TXT_PATH = os.path.join("models", "opening_lgbm.txt")
OPENING_TAKE_PROFIT_RATE = 0.012
OPENING_MAX_SPREAD_RATE = 0.006
EXIT_MIN_PROFIT_RATE = 0.007
EXIT_STRONG_PROFIT_RATE = 0.018
EXIT_TRAILING_DROP_RATE = 0.0035
EXIT_HOLD_SCORE_MIN = 0.45
ENTRY_FEATURES = [
    "price_momentum",
    "open_return",
    "box_position",
    "direction_score",
    "volume_speed",
    "spread_rate",
]


app = FastAPI(title="Kiwoom LightGBM AI Server")
model = None
model_name = "ServerFallbackScore"


class Tick(BaseModel):
    received_at: float
    signed_at: Optional[str] = ""
    close: int
    high: int
    open: int
    low: int
    ask: int
    bid: int
    accum_volume: int


class EntryRequest(BaseModel):
    code: str
    name: Optional[str] = ""
    current_price: int
    open_price: int
    high: int
    low: int
    ask: int
    bid: int
    ticks: List[Tick]


class EntryResponse(BaseModel):
    status: str
    score: float
    expected_return: float
    target_price: int
    model_name: str
    reason: str


class ExitRequest(BaseModel):
    code: str
    entry_price: int
    current_price: int
    highest_price: int
    hold_seconds: float
    ticks: List[Tick]


class ExitResponse(BaseModel):
    action: str
    score: float
    reason: str
    model_name: str


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def load_model():
    global model, model_name
    if os.path.exists(MODEL_PKL_PATH):
        model = joblib.load(MODEL_PKL_PATH)
        model_name = "LightGBM"
        return
    if lgb is not None and os.path.exists(MODEL_TXT_PATH):
        model = lgb.Booster(model_file=MODEL_TXT_PATH)
        model_name = "LightGBM"


def tick_dict(tick):
    return tick.dict()


def build_entry_features(req):
    ticks = [tick_dict(tick) for tick in req.ticks]
    first = ticks[0]
    last = ticks[-1]
    highs = [tick["high"] for tick in ticks if tick["high"] > 0]
    lows = [tick["low"] for tick in ticks if tick["low"] > 0]
    high = max(highs) if highs else req.high
    low = min(lows) if lows else req.low
    current_price = req.current_price
    open_price = req.open_price
    spread_rate = (req.ask - req.bid) / current_price if current_price > 0 else 1
    elapsed = max(last["received_at"] - first["received_at"], 1)
    price_momentum = current_price / first["close"] - 1 if first["close"] > 0 else 0
    open_return = current_price / open_price - 1 if open_price > 0 else 0
    box_position = (current_price - low) / (high - low) if high > low else 0.5
    recent_ticks = ticks[-min(5, len(ticks)):]
    up_count = 0
    for prev, cur in zip(recent_ticks, recent_ticks[1:]):
        if cur["close"] > prev["close"]:
            up_count += 1
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


def fallback_entry(req, features):
    spread_rate = features["spread_rate"]
    if spread_rate < 0 or spread_rate > OPENING_MAX_SPREAD_RATE:
        return EntryResponse(
            status="blocked",
            score=0.0,
            expected_return=0.0,
            target_price=req.current_price,
            model_name="ServerFallbackScore",
            reason="호가 스프레드 과다 {:.2%}".format(spread_rate),
        )

    momentum_score = clamp((features["price_momentum"] + 0.004) / 0.024)
    open_return_score = clamp((features["open_return"] + 0.003) / 0.035)
    box_score = clamp(features["box_position"])
    spread_score = clamp(1 - spread_rate / OPENING_MAX_SPREAD_RATE)
    volume_score = clamp(features["volume_speed"] / 3000)
    score = (
        momentum_score * 0.28
        + open_return_score * 0.20
        + box_score * 0.18
        + features["direction_score"] * 0.18
        + volume_score * 0.10
        + spread_score * 0.06
    )
    expected_return = (score - 0.5) * 0.04
    target_return = min(max(expected_return, OPENING_TAKE_PROFIT_RATE * 0.6), OPENING_TAKE_PROFIT_RATE)
    target_price = round(int(req.current_price * (1 + target_return)), -1)
    return EntryResponse(
        status="ready",
        score=score,
        expected_return=expected_return,
        target_price=target_price,
        model_name="ServerFallbackScore",
        reason="server fallback",
    )


def predict_lightgbm_entry(req, features):
    values = np.array([[features[name] for name in ENTRY_FEATURES]])
    if hasattr(model, "predict_proba"):
        prediction = model.predict_proba(values)
        score = clamp(float(prediction[0][1]))
    else:
        prediction = model.predict(values)
        score = clamp(float(prediction[0]))
    expected_return = (score - 0.5) * 0.04
    target_return = min(max(expected_return, OPENING_TAKE_PROFIT_RATE * 0.6), OPENING_TAKE_PROFIT_RATE)
    target_price = round(int(req.current_price * (1 + target_return)), -1)
    return EntryResponse(
        status="ready",
        score=score,
        expected_return=expected_return,
        target_price=target_price,
        model_name=model_name,
        reason="lightgbm",
    )


def fallback_exit(req):
    profit_rate = req.current_price / req.entry_price - 1 if req.entry_price > 0 else 0
    trailing_drop = req.current_price / req.highest_price - 1 if req.highest_price > 0 else 0
    ticks = [tick_dict(tick) for tick in req.ticks]
    recent_ticks = ticks[-min(8, len(ticks)):]
    direction_score = 0.5
    volume_score = 0.5
    high_hold_score = 0.5
    spread_score = 0.5

    if len(recent_ticks) >= 3:
        up_count = 0
        for prev, cur in zip(recent_ticks, recent_ticks[1:]):
            if cur["close"] >= prev["close"]:
                up_count += 1
        direction_score = up_count / max(len(recent_ticks) - 1, 1)

        first_recent = recent_ticks[0]
        last_recent = recent_ticks[-1]
        elapsed = max(last_recent["received_at"] - first_recent["received_at"], 1)
        volume_delta = max(last_recent["accum_volume"] - first_recent["accum_volume"], 0)
        volume_score = clamp((volume_delta / elapsed) / 2500)

        closes = [tick["close"] for tick in recent_ticks if tick["close"] > 0]
        if closes:
            recent_high = max(closes)
            recent_low = min(closes)
            if recent_high > recent_low:
                high_hold_score = clamp((req.current_price - recent_low) / (recent_high - recent_low))

        ask = last_recent["ask"]
        bid = last_recent["bid"]
        if ask > 0 and bid > 0 and req.current_price > 0:
            spread_rate = (ask - bid) / req.current_price
            spread_score = clamp(1 - spread_rate / OPENING_MAX_SPREAD_RATE)

    profit_score = clamp((profit_rate - EXIT_MIN_PROFIT_RATE) / (EXIT_STRONG_PROFIT_RATE - EXIT_MIN_PROFIT_RATE))
    time_penalty = clamp(req.hold_seconds / (20 * 60))
    drawdown_penalty = clamp(abs(min(trailing_drop, 0)) / (EXIT_TRAILING_DROP_RATE * 2))
    hold_score = clamp(
        direction_score * 0.30
        + volume_score * 0.20
        + high_hold_score * 0.20
        + spread_score * 0.10
        + profit_score * 0.20
        - time_penalty * 0.20
        - drawdown_penalty * 0.25
    )

    if profit_rate >= EXIT_STRONG_PROFIT_RATE:
        return ExitResponse(action="sell", score=hold_score, reason="강한 수익 구간 도달 {:.2%}".format(profit_rate), model_name="ServerFallbackScore")
    if profit_rate >= EXIT_MIN_PROFIT_RATE and trailing_drop <= -EXIT_TRAILING_DROP_RATE:
        return ExitResponse(action="sell", score=hold_score, reason="고점 대비 밀림 {:.2%}".format(trailing_drop), model_name="ServerFallbackScore")
    if profit_rate >= EXIT_MIN_PROFIT_RATE and hold_score < EXIT_HOLD_SCORE_MIN:
        return ExitResponse(action="sell", score=hold_score, reason="상승 지속 점수 약화 {:.2f}".format(hold_score), model_name="ServerFallbackScore")
    return ExitResponse(action="hold", score=hold_score, reason="상승 지속 점수 {:.2f}".format(hold_score), model_name="ServerFallbackScore")


@app.on_event("startup")
def startup():
    load_model()


@app.get("/health")
def health():
    return {
        "ok": True,
        "model_loaded": model is not None,
        "model_name": model_name,
    }


@app.post("/predict-entry", response_model=EntryResponse)
def predict_entry(req: EntryRequest):
    features = build_entry_features(req)
    if model is None:
        return fallback_entry(req, features)
    try:
        return predict_lightgbm_entry(req, features)
    except Exception as exc:
        response = fallback_entry(req, features)
        response.reason = "model error fallback: {}".format(exc)
        return response


@app.post("/predict-exit", response_model=ExitResponse)
def predict_exit(req: ExitRequest):
    return fallback_exit(req)
