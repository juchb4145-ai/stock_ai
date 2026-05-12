"""FastAPI shell for future Dante LightGBM inference.

The server is intentionally conservative: by default it does not override the
rule engine. It echoes the Dante rule decision and appends model metadata
(`model_score`, `model_action`) so main.py can log shadow results first. Once a
model is validated, callers can opt into enforcement per request.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

import scoring

try:
    import joblib
except ImportError:
    joblib = None

try:
    import lightgbm as lgb
except ImportError:
    lgb = None


MODEL_DIR = "models"
DANTE_MODEL_PKL_PATH = os.path.join(MODEL_DIR, "dante_lgbm.pkl")
DANTE_MODEL_TXT_PATH = os.path.join(MODEL_DIR, "dante_lgbm.txt")
DANTE_MODEL_META_PATH = os.path.join(MODEL_DIR, "dante_lgbm_meta.json")

DEFAULT_DANTE_THRESHOLD = 0.5
DEFAULT_TARGET = "reached_1r"
DANTE_FEATURES = list(scoring.DANTE_ENTRY_FEATURE_NAMES)

MODEL_ACTION_ALLOW = "shadow_allow"
MODEL_ACTION_BLOCK = "shadow_block"
MODEL_ACTION_UNAVAILABLE = "shadow_unavailable"


app = FastAPI(title="Kiwoom Dante LightGBM AI Server")
model = None
model_name = "DanteModelUnavailable"
model_threshold = DEFAULT_DANTE_THRESHOLD
model_ready_threshold = DEFAULT_DANTE_THRESHOLD
model_promotion_threshold = DEFAULT_DANTE_THRESHOLD
model_target = DEFAULT_TARGET
model_features = list(DANTE_FEATURES)
model_meta: Dict = {}


class DanteRuleDecision(BaseModel):
    status: str = "wait"
    ratio: float = 0.0
    stage: int = 1
    grade: str = ""
    reason: str = ""
    reason_code: str = ""


class DanteEntryRequest(BaseModel):
    code: str
    name: Optional[str] = ""
    current_price: int = 0
    rule: DanteRuleDecision = Field(default_factory=DanteRuleDecision)
    features: Dict[str, float] = Field(default_factory=dict)
    market_regime: str = ""
    market_gate_action: str = ""
    market_gate_reason: str = ""
    enforce_model: bool = False


class DanteEntryResponse(BaseModel):
    status: str
    code: str
    name: str = ""
    current_price: int = 0
    ratio: float = 0.0
    stage: int = 1
    grade: str = ""
    score: float = 0.0
    model_score: float = 0.0
    model_action: str = MODEL_ACTION_UNAVAILABLE
    model_name: str = "DanteModelUnavailable"
    model_target: str = DEFAULT_TARGET
    model_threshold: float = DEFAULT_DANTE_THRESHOLD
    model_ready_threshold: float = DEFAULT_DANTE_THRESHOLD
    model_promotion_threshold: float = DEFAULT_DANTE_THRESHOLD
    reason: str = ""
    reason_code: str = ""
    market_regime: str = ""
    market_gate_action: str = ""
    market_gate_reason: str = ""
    missing_features: List[str] = Field(default_factory=list)


class DanteEntryPlanRequest(DanteEntryRequest):
    ask: int = 0
    bid: int = 0
    breakout_high: int = 0
    recent_low: int = 0


class DanteEntryPlanResponse(DanteEntryResponse):
    entry_limit_price: int = 0
    stop_price: int = 0
    take_profit_price: int = 0
    risk_reward: float = 0.0
    max_risk_pct: float = 0.0
    expiry_seconds: int = 45
    plan_source: str = "rule_fallback"


class ExitRequest(BaseModel):
    code: str
    entry_price: int
    current_price: int
    highest_price: int
    hold_seconds: float


class ExitResponse(BaseModel):
    action: str
    score: float
    reason: str
    model_name: str


def _load_meta() -> None:
    global model_threshold, model_ready_threshold, model_promotion_threshold
    global model_target, model_features, model_meta
    if not os.path.exists(DANTE_MODEL_META_PATH):
        return
    try:
        with open(DANTE_MODEL_META_PATH, "r", encoding="utf-8") as file:
            model_meta = json.load(file)
    except Exception as exc:
        print("[dante model meta load failed]", exc)
        model_meta = {}
        return

    threshold = model_meta.get("threshold")
    if isinstance(threshold, (int, float)) and 0 < float(threshold) < 1:
        model_threshold = float(threshold)

    ready_threshold = model_meta.get("ready_threshold")
    if isinstance(ready_threshold, (int, float)) and 0 < float(ready_threshold) < 1:
        model_ready_threshold = float(ready_threshold)
    else:
        model_ready_threshold = model_threshold

    promotion_threshold = model_meta.get("promotion_threshold")
    if isinstance(promotion_threshold, (int, float)) and 0 < float(promotion_threshold) < 1:
        model_promotion_threshold = float(promotion_threshold)
    else:
        model_promotion_threshold = model_threshold

    # Backward-compatible field used by older callers.  Newer callers receive
    # the active threshold per response based on ready vs shadow promotion flow.
    model_threshold = model_promotion_threshold

    target = model_meta.get("target")
    if isinstance(target, str) and target:
        model_target = target

    features = model_meta.get("features")
    if isinstance(features, list) and all(isinstance(name, str) for name in features):
        model_features = list(features)


def load_model() -> None:
    global model, model_name
    _load_meta()
    if joblib is not None and os.path.exists(DANTE_MODEL_PKL_PATH):
        model = joblib.load(DANTE_MODEL_PKL_PATH)
        model_name = str(model_meta.get("model_name") or "DanteLightGBM")
    elif lgb is not None and os.path.exists(DANTE_MODEL_TXT_PATH):
        model = lgb.Booster(model_file=DANTE_MODEL_TXT_PATH)
        model_name = str(model_meta.get("model_name") or "DanteLightGBM")


def _feature_vector(features: Dict[str, float]) -> tuple[pd.DataFrame, List[str]]:
    missing = [name for name in model_features if name not in features]
    values = []
    for name in model_features:
        try:
            values.append(float(features.get(name, 0.0) or 0.0))
        except (TypeError, ValueError):
            values.append(0.0)
    return pd.DataFrame([values], columns=model_features, dtype=float), missing


def _predict_score(features: Dict[str, float]) -> tuple[float, List[str]]:
    values, missing = _feature_vector(features)
    if hasattr(model, "predict_proba"):
        prediction = model.predict_proba(values)
        score = float(prediction[0][1])
    else:
        prediction = model.predict(values)
        score = float(prediction[0])
    return scoring.clamp(score), missing


def _active_entry_threshold(req: DanteEntryRequest) -> float:
    if req.rule.status == "ready":
        return model_ready_threshold
    return model_promotion_threshold


def _rule_response(req: DanteEntryRequest) -> DanteEntryResponse:
    return DanteEntryResponse(
        status=req.rule.status,
        code=req.code,
        name=req.name or "",
        current_price=req.current_price,
        ratio=req.rule.ratio,
        stage=req.rule.stage,
        grade=req.rule.grade,
        score=req.rule.ratio,
        reason=req.rule.reason,
        reason_code=req.rule.reason_code,
        market_regime=req.market_regime,
        market_gate_action=req.market_gate_action,
        market_gate_reason=req.market_gate_reason,
    )


def _build_entry_plan(
    req: DanteEntryPlanRequest,
    *,
    response: DanteEntryResponse,
) -> DanteEntryPlanResponse:
    current = int(req.current_price or 0)
    bid = int(req.bid or 0)
    ask = int(req.ask or 0)
    recent_low = int(req.recent_low or 0)
    if current <= 0:
        return DanteEntryPlanResponse(**response.dict(), plan_source=response.model_name)

    unit = scoring.tick_size(current)
    if bid > 0:
        entry_limit = min(current, bid + unit)
    elif ask > 0:
        entry_limit = min(current, ask)
    else:
        entry_limit = current
    entry_limit = scoring.round_down_to_tick(entry_limit)

    stop_anchor = recent_low if recent_low > 0 else int(entry_limit * 0.987)
    stop_price = scoring.round_down_to_tick(stop_anchor - unit)
    if stop_price <= 0 or stop_price >= entry_limit:
        stop_price = scoring.round_down_to_tick(entry_limit * 0.985)

    risk_per_share = max(entry_limit - stop_price, unit)
    risk_pct = risk_per_share / entry_limit if entry_limit > 0 else 0.0
    target_r = 2.0
    if req.enforce_model and response.model_score and response.model_score >= max(response.model_threshold, 0.65):
        target_r = 2.3
    take_profit = scoring.round_up_to_tick(entry_limit + risk_per_share * target_r)
    rr = (take_profit - entry_limit) / risk_per_share if risk_per_share > 0 else 0.0

    return DanteEntryPlanResponse(
        **response.dict(),
        entry_limit_price=entry_limit,
        stop_price=stop_price,
        take_profit_price=take_profit,
        risk_reward=round(float(rr), 3),
        max_risk_pct=round(float(risk_pct), 5),
        expiry_seconds=45,
        plan_source=response.model_name,
    )


@app.on_event("startup")
def startup() -> None:
    load_model()


@app.get("/health")
def health() -> Dict:
    return {
        "ok": True,
        "model_loaded": model is not None,
        "model_name": model_name,
        "target": model_target,
        "threshold": model_threshold,
        "ready_threshold": model_ready_threshold,
        "promotion_threshold": model_promotion_threshold,
        "features": model_features,
        "feature_count": len(model_features),
        "meta": {
            key: model_meta.get(key)
            for key in (
                "train_rows",
                "valid_rows",
                "valid_auc",
                "valid_accuracy_tuned",
                "valid_f1_tuned",
                "cv_auc_mean",
                "cv_f1_mean",
                "positive_count",
                "negative_count",
            )
            if key in model_meta
        },
    }


@app.post("/predict-dante-entry", response_model=DanteEntryResponse)
def predict_dante_entry(req: DanteEntryRequest) -> DanteEntryResponse:
    response = _rule_response(req)
    response.model_name = model_name
    response.model_target = model_target
    active_threshold = _active_entry_threshold(req)
    response.model_threshold = active_threshold
    response.model_ready_threshold = model_ready_threshold
    response.model_promotion_threshold = model_promotion_threshold

    if model is None:
        response.model_action = MODEL_ACTION_UNAVAILABLE
        response.reason = "{} | model unavailable".format(response.reason).strip()
        return response

    try:
        model_score, missing = _predict_score(req.features)
    except Exception as exc:
        response.model_action = MODEL_ACTION_UNAVAILABLE
        response.reason = "{} | model error fallback: {}".format(response.reason, exc).strip()
        return response

    response.model_score = model_score
    response.score = model_score
    response.missing_features = missing
    response.model_action = (
        MODEL_ACTION_ALLOW if model_score >= active_threshold else MODEL_ACTION_BLOCK
    )

    if req.enforce_model and response.model_action == MODEL_ACTION_BLOCK:
        response.status = "blocked"
        response.ratio = 0.0
        response.reason = "dante model score {:.3f} < threshold {:.3f} ({})".format(
            model_score, active_threshold, response.reason
        )
    else:
        response.reason = "{} | dante model score {:.3f} {}".format(
            response.reason,
            model_score,
            ">=" if model_score >= active_threshold else "<",
        ).strip()
    return response


@app.post("/predict-dante-entry-plan", response_model=DanteEntryPlanResponse)
def predict_dante_entry_plan(req: DanteEntryPlanRequest) -> DanteEntryPlanResponse:
    response = predict_dante_entry(req)
    return _build_entry_plan(req, response=response)


@app.post("/predict-entry", response_model=DanteEntryResponse)
def predict_entry(req: DanteEntryRequest) -> DanteEntryResponse:
    """Compatibility alias while main.py migrates to /predict-dante-entry."""
    return predict_dante_entry(req)


@app.post("/predict-exit", response_model=ExitResponse)
def predict_exit(req: ExitRequest) -> ExitResponse:
    return ExitResponse(
        action="hold",
        score=0.0,
        reason="Dante exit model is not enabled; use rule exit strategy",
        model_name="DanteExitUnavailable",
    )
