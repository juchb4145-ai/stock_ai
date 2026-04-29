import json
import os
from typing import List, Optional

import joblib
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

import scoring

try:
    import lightgbm as lgb
except ImportError:
    lgb = None


MODEL_PKL_PATH = os.path.join("models", "opening_lgbm.pkl")
MODEL_TXT_PATH = os.path.join("models", "opening_lgbm.txt")
MODEL_META_PATH = os.path.join("models", "opening_lgbm_meta.json")
OPENING_TAKE_PROFIT_RATE = 0.012
OPENING_MAX_SPREAD_RATE = 0.006
EXIT_MIN_PROFIT_RATE = 0.007
EXIT_STRONG_PROFIT_RATE = 0.018
EXIT_TRAILING_DROP_RATE = 0.0035
EXIT_STALL_SECONDS = 7 * 60
EXIT_HOLD_SCORE_MIN = 0.45
OPENING_MAX_HOLD_SECONDS = 20 * 60
DEFAULT_ENTRY_THRESHOLD = 0.5
ENTRY_FEATURES = list(scoring.ENTRY_FEATURE_NAMES)


app = FastAPI(title="Kiwoom LightGBM AI Server")
model = None
model_name = "ServerFallbackScore"
model_threshold = DEFAULT_ENTRY_THRESHOLD
model_meta = {}


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


def load_model():
    global model, model_name, model_threshold, model_meta
    if os.path.exists(MODEL_PKL_PATH):
        model = joblib.load(MODEL_PKL_PATH)
        model_name = "LightGBM"
    elif lgb is not None and os.path.exists(MODEL_TXT_PATH):
        model = lgb.Booster(model_file=MODEL_TXT_PATH)
        model_name = "LightGBM"

    if os.path.exists(MODEL_META_PATH):
        try:
            with open(MODEL_META_PATH, "r", encoding="utf-8") as f:
                model_meta = json.load(f)
            threshold = model_meta.get("threshold")
            if isinstance(threshold, (int, float)) and 0 < float(threshold) < 1:
                model_threshold = float(threshold)
        except Exception as exc:
            print("[메타 로드 실패]", exc)


def _ticks_as_dicts(ticks):
    # pydantic v1/v2 호환
    out = []
    for tick in ticks:
        if hasattr(tick, "model_dump"):
            out.append(tick.model_dump())
        else:
            out.append(tick.dict())
    return out


def build_entry_features(req: EntryRequest):
    ticks = _ticks_as_dicts(req.ticks)
    if not ticks:
        return None
    return scoring.build_entry_features(
        ticks=ticks,
        current_price=req.current_price,
        open_price=req.open_price,
        high=req.high,
        low=req.low,
        ask=req.ask,
        bid=req.bid,
    )


def fallback_entry(req: EntryRequest, features) -> EntryResponse:
    if features is None:
        return EntryResponse(
            status="wait",
            score=0.0,
            expected_return=0.0,
            target_price=req.current_price,
            model_name="ServerFallbackScore",
            reason="실시간 가격 데이터 부족",
        )
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

    score = scoring.compute_entry_score(features, OPENING_MAX_SPREAD_RATE)
    expected_return = scoring.expected_return_from_score(
        score,
        features=features,
        opening_max_spread_rate=OPENING_MAX_SPREAD_RATE,
    )
    target_price = scoring.compute_target_price(req.current_price, expected_return, OPENING_TAKE_PROFIT_RATE)
    return EntryResponse(
        status="ready",
        score=score,
        expected_return=expected_return,
        target_price=target_price,
        model_name="ServerFallbackScore",
        reason="server fallback",
    )


def predict_lightgbm_entry(req: EntryRequest, features) -> EntryResponse:
    values = np.array([[features[name] for name in ENTRY_FEATURES]])
    if hasattr(model, "predict_proba"):
        prediction = model.predict_proba(values)
        score = scoring.clamp(float(prediction[0][1]))
    else:
        prediction = model.predict(values)
        score = scoring.clamp(float(prediction[0]))
    expected_return = scoring.expected_return_from_score(
        score,
        features=features,
        opening_max_spread_rate=OPENING_MAX_SPREAD_RATE,
    )
    target_price = scoring.compute_target_price(req.current_price, expected_return, OPENING_TAKE_PROFIT_RATE)

    # 학습 시 결정된 threshold 미만이면 매수 차단 신호로 응답해 main.py가 곧바로 회피하도록 한다.
    if score < model_threshold:
        return EntryResponse(
            status="blocked",
            score=score,
            expected_return=expected_return,
            target_price=target_price,
            model_name=model_name,
            reason="lightgbm score {:.3f} < threshold {:.3f}".format(score, model_threshold),
        )
    return EntryResponse(
        status="ready",
        score=score,
        expected_return=expected_return,
        target_price=target_price,
        model_name=model_name,
        reason="lightgbm score {:.3f} >= threshold {:.3f}".format(score, model_threshold),
    )


def fallback_exit(req: ExitRequest) -> ExitResponse:
    profit_rate = req.current_price / req.entry_price - 1 if req.entry_price > 0 else 0
    trailing_drop = req.current_price / req.highest_price - 1 if req.highest_price > 0 else 0
    ticks = _ticks_as_dicts(req.ticks)

    hold_score = scoring.compute_exit_hold_score(
        ticks=ticks,
        current_price=req.current_price,
        profit_rate=profit_rate,
        trailing_drop=trailing_drop,
        hold_seconds=req.hold_seconds,
        opening_max_spread_rate=OPENING_MAX_SPREAD_RATE,
        exit_min_profit_rate=EXIT_MIN_PROFIT_RATE,
        exit_strong_profit_rate=EXIT_STRONG_PROFIT_RATE,
        exit_trailing_drop_rate=EXIT_TRAILING_DROP_RATE,
        exit_stall_seconds=EXIT_STALL_SECONDS,
        opening_max_hold_seconds=OPENING_MAX_HOLD_SECONDS,
    )

    if profit_rate >= EXIT_STRONG_PROFIT_RATE:
        return ExitResponse(action="sell", score=hold_score, reason="강한 수익 구간 도달 {:.2%}".format(profit_rate), model_name="ServerFallbackScore")
    if profit_rate >= EXIT_MIN_PROFIT_RATE and trailing_drop <= -EXIT_TRAILING_DROP_RATE:
        return ExitResponse(action="sell", score=hold_score, reason="고점 대비 밀림 {:.2%}".format(trailing_drop), model_name="ServerFallbackScore")
    if profit_rate >= EXIT_MIN_PROFIT_RATE and req.hold_seconds >= EXIT_STALL_SECONDS and hold_score < EXIT_HOLD_SCORE_MIN:
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
        "threshold": model_threshold,
        "meta": {
            k: model_meta.get(k)
            for k in (
                "train_rows",
                "valid_rows",
                "valid_auc",
                "valid_accuracy_tuned",
                "valid_f1_tuned",
                "cv_auc_mean",
                "cv_f1_mean",
            )
            if k in model_meta
        },
    }


@app.post("/predict-entry", response_model=EntryResponse)
def predict_entry(req: EntryRequest):
    features = build_entry_features(req)
    if features is None or model is None:
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
