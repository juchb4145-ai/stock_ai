"""Train the Dante LightGBM entry model.

This script trains the model consumed by ai_server.py:

    models/dante_lgbm.pkl
    models/dante_lgbm_meta.json

It reads both ready samples and shadow samples so the model can learn from
missed opportunities as well as rule-approved entries. By default the target is
`good_trade`, which matches the current R-based strategy better than a bare
1R touch: the sample must reach +1R without touching -1R during the label window.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from typing import Dict, Iterable, List, Optional, Tuple

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

try:
    from sklearn.model_selection import StratifiedGroupKFold
except ImportError:  # pragma: no cover - older sklearn fallback
    StratifiedGroupKFold = None

import scoring


DATA_PATHS = (
    os.path.join("data", "dante_entry_training.csv"),
    os.path.join("data", "dante_shadow_training.csv"),
)
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "dante_lgbm.pkl")
MODEL_META_PATH = os.path.join(MODEL_DIR, "dante_lgbm_meta.json")
FEATURES = list(scoring.DANTE_ENTRY_FEATURE_NAMES)
DEFAULT_TARGET = "good_trade"
SUPPORTED_TARGETS = ("good_trade", "reached_1r", "reached_2r", "hit_stop")
MIN_TRAINING_ROWS = 500
DEFAULT_THRESHOLD = 0.5
VALID_SIZE = 0.2
RANDOM_STATE = 1234
CV_SPLITS = 5
READY_MIN_PRECISION = 0.55
PROMOTION_MIN_PRECISION = 0.70
MIN_THRESHOLD_POSITIVES = 5
SEGMENT_TOP_N = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Dante LightGBM entry model")
    parser.add_argument("--target", default=DEFAULT_TARGET, choices=SUPPORTED_TARGETS)
    parser.add_argument("--min-rows", type=int, default=MIN_TRAINING_ROWS)
    parser.add_argument(
        "--validation",
        default="time",
        choices=("time", "random"),
        help="Use the latest captured dates as holdout by default; random keeps legacy behavior.",
    )
    parser.add_argument("--ready-min-precision", type=float, default=READY_MIN_PRECISION)
    parser.add_argument("--promotion-min-precision", type=float, default=PROMOTION_MIN_PRECISION)
    parser.add_argument("--dry-run", action="store_true", help="Train/evaluate without writing model files")
    return parser.parse_args()


def _read_csv(path: str, source: str) -> pd.DataFrame:
    if not os.path.exists(path):
        print("[skip] missing {}".format(path))
        return pd.DataFrame()
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            row.pop(None, None)  # tolerate rows written with a newer/older header
            rows.append(row)
    df = pd.DataFrame(rows)
    df["source_file"] = source
    return df


def _coerce_numeric(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def _label_columns_for_target(target: str) -> List[str]:
    if target == "good_trade":
        return ["reached_1r", "hit_stop"]
    return [target]


def _prepare_target(df: pd.DataFrame, target: str) -> pd.DataFrame:
    out = df.copy()
    if target == "good_trade":
        out[target] = (
            (out["reached_1r"].astype(int) == 1)
            & (out["hit_stop"].astype(int) == 0)
        ).astype(int)
    elif target == "hit_stop":
        # For hit_stop, the raw positive class means "bad". Flip it so label 1
        # always means a desirable entry for the model/server threshold contract.
        out[target] = 1 - out[target].astype(int)
    else:
        out[target] = out[target].astype(int)
    return out


def _attach_split_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    captured = None
    if "captured_time" in out.columns:
        captured = pd.to_datetime(out["captured_time"], errors="coerce")
    if captured is None or captured.isna().all():
        captured = pd.to_datetime(pd.to_numeric(out.get("captured_at"), errors="coerce"), unit="s", errors="coerce")
    out["captured_date"] = captured.dt.strftime("%Y-%m-%d").fillna("unknown")
    code = out["code"].astype(str) if "code" in out.columns else pd.Series("unknown", index=out.index)
    out["split_group"] = code + "_" + out["captured_date"].astype(str)
    return out


def load_training_data(target: str) -> pd.DataFrame:
    frames = [
        _read_csv(DATA_PATHS[0], "entry"),
        _read_csv(DATA_PATHS[1], "shadow"),
    ]
    df = pd.concat([frame for frame in frames if not frame.empty], ignore_index=True)
    if df.empty:
        raise FileNotFoundError("No Dante training CSV rows found")

    label_columns = _label_columns_for_target(target)
    missing = [column for column in FEATURES + label_columns if column not in df.columns]
    if missing:
        raise ValueError("Dante training columns missing: {}".format(missing))

    if "sample_id" in df.columns:
        df = df.drop_duplicates(subset=["sample_id"], keep="last")

    df = _coerce_numeric(df, FEATURES + label_columns)
    df = df.dropna(subset=FEATURES + label_columns).copy()
    df = _prepare_target(df, target)
    return _attach_split_columns(df)


def make_model() -> lgb.LGBMClassifier:
    return lgb.LGBMClassifier(
        n_estimators=2000,
        learning_rate=0.02,
        max_depth=-1,
        num_leaves=31,
        min_child_samples=30,
        subsample=0.8,
        colsample_bytree=0.8,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        verbosity=-1,
    )


def metrics_at_threshold(y_true, probabilities, threshold: float) -> Dict[str, float]:
    predictions = (probabilities >= threshold).astype(int)
    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
    }


def find_best_threshold(y_true, probabilities) -> Dict[str, float]:
    best = {"threshold": DEFAULT_THRESHOLD, "f1": -1.0, "accuracy": 0.0}
    for threshold in np.arange(0.30, 0.91, 0.01):
        current = metrics_at_threshold(y_true, probabilities, float(round(threshold, 2)))
        if current["f1"] > best["f1"] or (
            current["f1"] == best["f1"] and current["accuracy"] > best["accuracy"]
        ):
            best = current
    return best


def find_precision_threshold(y_true, probabilities, min_precision: float) -> Dict[str, float]:
    fallback = find_best_threshold(y_true, probabilities)
    best: Optional[Dict[str, float]] = None
    for threshold in np.arange(0.30, 0.91, 0.01):
        rounded = float(round(threshold, 2))
        predictions = (probabilities >= rounded).astype(int)
        if int(predictions.sum()) < MIN_THRESHOLD_POSITIVES:
            continue
        current = metrics_at_threshold(y_true, probabilities, rounded)
        if current["precision"] < min_precision:
            continue
        if best is None:
            best = current
            continue
        if current["f1"] > best["f1"] or (
            current["f1"] == best["f1"] and current["precision"] > best["precision"]
        ):
            best = current
    if best is None:
        fallback = dict(fallback)
        fallback["precision_constraint_met"] = False
        fallback["min_precision"] = float(min_precision)
        return fallback
    best["precision_constraint_met"] = True
    best["min_precision"] = float(min_precision)
    return best


def _safe_auc(y_true, probabilities) -> Optional[float]:
    if len(pd.Series(y_true).dropna().unique()) < 2:
        return None
    return float(roc_auc_score(y_true, probabilities))


def _safe_stratified_random_split(df: pd.DataFrame, target: str) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, object]]:
    y = df[target]
    stratify = y if y.value_counts().min() >= 2 else None
    train_df, valid_df = train_test_split(
        df,
        test_size=VALID_SIZE,
        random_state=RANDOM_STATE,
        stratify=stratify,
    )
    return train_df.copy(), valid_df.copy(), {
        "validation_method": "random_stratified",
        "valid_dates": sorted(valid_df["captured_date"].dropna().unique().tolist()),
    }


def split_train_valid(df: pd.DataFrame, target: str, validation: str) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, object]]:
    if validation == "random":
        return _safe_stratified_random_split(df, target)

    dates = [date for date in sorted(df["captured_date"].dropna().unique().tolist()) if date != "unknown"]
    if len(dates) < 2:
        train_df, valid_df, meta = _safe_stratified_random_split(df, target)
        meta["validation_method"] = "random_fallback_no_dates"
        return train_df, valid_df, meta

    target_valid_rows = max(int(len(df) * VALID_SIZE), 1)
    valid_dates: List[str] = []
    for date in reversed(dates):
        valid_dates.insert(0, date)
        valid_df = df[df["captured_date"].isin(valid_dates)]
        train_df = df[~df["captured_date"].isin(valid_dates)]
        if len(valid_df) >= target_valid_rows and len(train_df) > 0:
            break

    if train_df[target].nunique() < 2 or valid_df[target].nunique() < 2:
        train_df, valid_df, meta = _safe_stratified_random_split(df, target)
        meta["validation_method"] = "random_fallback_class_balance"
        return train_df, valid_df, meta

    return train_df.copy(), valid_df.copy(), {
        "validation_method": "latest_date_holdout",
        "valid_dates": valid_dates,
        "valid_groups": int(valid_df["split_group"].nunique()),
        "train_groups": int(train_df["split_group"].nunique()),
    }


def run_cv(df: pd.DataFrame, target: str) -> Optional[Dict[str, float]]:
    x = df[FEATURES]
    y = df[target]
    min_class_count = int(y.value_counts().min())
    n_splits = min(CV_SPLITS, min_class_count)
    if n_splits < 2:
        return None

    groups = df["split_group"] if "split_group" in df.columns else None
    use_group_cv = StratifiedGroupKFold is not None and groups is not None and int(groups.nunique()) >= n_splits
    if use_group_cv:
        kfold = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
        splits = kfold.split(x, y, groups)
        cv_method = "stratified_group_kfold_by_code_date"
    else:
        kfold = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
        splits = kfold.split(x, y)
        cv_method = "stratified_kfold"

    aucs: List[float] = []
    accuracies: List[float] = []
    f1s: List[float] = []
    precisions: List[float] = []
    recalls: List[float] = []

    for train_index, valid_index in splits:
        x_train = x.iloc[train_index]
        y_train = y.iloc[train_index]
        x_valid = x.iloc[valid_index]
        y_valid = y.iloc[valid_index]

        model = make_model()
        model.fit(
            x_train,
            y_train,
            eval_set=[(x_valid, y_valid)],
            eval_metric="auc",
            callbacks=[lgb.early_stopping(stopping_rounds=100, verbose=False)],
        )
        probabilities = model.predict_proba(x_valid)[:, 1]
        tuned = find_best_threshold(y_valid, probabilities)
        auc = _safe_auc(y_valid, probabilities)
        if auc is not None:
            aucs.append(auc)
        accuracies.append(tuned["accuracy"])
        f1s.append(tuned["f1"])
        precisions.append(tuned["precision"])
        recalls.append(tuned["recall"])

    result = {
        "cv_splits": int(n_splits),
        "cv_method": cv_method,
        "cv_accuracy_mean": float(np.mean(accuracies)),
        "cv_f1_mean": float(np.mean(f1s)),
        "cv_precision_mean": float(np.mean(precisions)),
        "cv_recall_mean": float(np.mean(recalls)),
    }
    if aucs:
        result["cv_auc_mean"] = float(np.mean(aucs))
        result["cv_auc_std"] = float(np.std(aucs))
    return result


def _segment_rows(df: pd.DataFrame, y_true, probabilities, threshold: float, group_col: str, limit: Optional[int] = None) -> List[Dict[str, object]]:
    if group_col not in df.columns:
        return []
    work = df[[group_col]].copy()
    work["_y"] = list(y_true)
    work["_p"] = list(probabilities)
    rows: List[Dict[str, object]] = []
    for key, group in work.groupby(group_col, dropna=False):
        if len(group) == 0:
            continue
        metrics = metrics_at_threshold(group["_y"], group["_p"], threshold)
        auc = _safe_auc(group["_y"], group["_p"])
        payload: Dict[str, object] = {
            str(group_col): "" if pd.isna(key) else str(key),
            "n": int(len(group)),
            "positive_rate": float(group["_y"].mean()),
            "avg_score": float(group["_p"].mean()),
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1": metrics["f1"],
        }
        if auc is not None:
            payload["auc"] = auc
        rows.append(payload)
    rows.sort(key=lambda item: int(item["n"]), reverse=True)
    return rows[:limit] if limit is not None else rows


def build_segment_report(valid_df: pd.DataFrame, target: str, probabilities, threshold: float) -> Dict[str, object]:
    y_true = valid_df[target].to_numpy()
    return {
        "threshold": float(threshold),
        "by_source": _segment_rows(valid_df, y_true, probabilities, threshold, "source_file"),
        "by_decision_status": _segment_rows(valid_df, y_true, probabilities, threshold, "decision_status"),
        "by_reason_code_top": _segment_rows(valid_df, y_true, probabilities, threshold, "reason_code", SEGMENT_TOP_N),
    }


def _atomic_dump_joblib(model, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix="dante_lgbm_", suffix=".pkl", dir=os.path.dirname(path))
    os.close(fd)
    try:
        joblib.dump(model, tmp_path)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _atomic_write_json(data: Dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix="dante_lgbm_meta_", suffix=".json", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def train(
    target: str,
    min_rows: int,
    dry_run: bool = False,
    validation: str = "time",
    ready_min_precision: float = READY_MIN_PRECISION,
    promotion_min_precision: float = PROMOTION_MIN_PRECISION,
) -> Dict:
    df = load_training_data(target)
    total_rows = int(len(df))
    positive_count = int(df[target].sum())
    negative_count = int(total_rows - positive_count)
    source_counts = {str(k): int(v) for k, v in df["source_file"].value_counts().items()}

    print("Dante data: rows={}, positives={}, negatives={}, target={}".format(
        total_rows, positive_count, negative_count, target
    ))
    print("sources: {}".format(source_counts))

    if total_rows < min_rows:
        raise ValueError("Not enough rows: {} < {}".format(total_rows, min_rows))
    if positive_count <= 0 or negative_count <= 0:
        raise ValueError("Need both positive and negative classes")

    train_df, valid_df, split_meta = split_train_valid(df, target, validation)
    x_train = train_df[FEATURES]
    y_train = train_df[target]
    x_valid = valid_df[FEATURES]
    y_valid = valid_df[target]

    model = make_model()
    model.fit(
        x_train,
        y_train,
        eval_set=[(x_valid, y_valid)],
        eval_metric="auc",
        callbacks=[lgb.early_stopping(stopping_rounds=100, verbose=False)],
    )

    probabilities = model.predict_proba(x_valid)[:, 1]
    default_metrics = metrics_at_threshold(y_valid, probabilities, DEFAULT_THRESHOLD)
    tuned_metrics = find_best_threshold(y_valid, probabilities)
    ready_metrics = find_precision_threshold(y_valid, probabilities, ready_min_precision)
    promotion_metrics = find_precision_threshold(y_valid, probabilities, promotion_min_precision)
    auc = _safe_auc(y_valid, probabilities)
    cv_result = run_cv(df, target)
    segment_report = build_segment_report(valid_df, target, probabilities, promotion_metrics["threshold"])

    meta = {
        "model_name": "DanteLightGBM",
        "target": target,
        "threshold": promotion_metrics["threshold"],
        "ready_threshold": ready_metrics["threshold"],
        "promotion_threshold": promotion_metrics["threshold"],
        "threshold_policy": {
            "legacy_threshold_field": "promotion_threshold",
            "ready_min_precision": float(ready_min_precision),
            "promotion_min_precision": float(promotion_min_precision),
            "min_threshold_positives": MIN_THRESHOLD_POSITIVES,
        },
        "features": FEATURES,
        "train_rows": int(len(x_train)),
        "valid_rows": int(len(x_valid)),
        "total_rows": total_rows,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "source_counts": source_counts,
        "valid_accuracy_default_0_5": default_metrics["accuracy"],
        "valid_precision_default_0_5": default_metrics["precision"],
        "valid_recall_default_0_5": default_metrics["recall"],
        "valid_f1_default_0_5": default_metrics["f1"],
        "valid_accuracy_tuned": tuned_metrics["accuracy"],
        "valid_precision_tuned": tuned_metrics["precision"],
        "valid_recall_tuned": tuned_metrics["recall"],
        "valid_f1_tuned": tuned_metrics["f1"],
        "valid_accuracy_ready_threshold": ready_metrics["accuracy"],
        "valid_precision_ready_threshold": ready_metrics["precision"],
        "valid_recall_ready_threshold": ready_metrics["recall"],
        "valid_f1_ready_threshold": ready_metrics["f1"],
        "valid_accuracy_promotion_threshold": promotion_metrics["accuracy"],
        "valid_precision_promotion_threshold": promotion_metrics["precision"],
        "valid_recall_promotion_threshold": promotion_metrics["recall"],
        "valid_f1_promotion_threshold": promotion_metrics["f1"],
        "ready_precision_constraint_met": ready_metrics.get("precision_constraint_met", False),
        "promotion_precision_constraint_met": promotion_metrics.get("precision_constraint_met", False),
        "segment_report": segment_report,
    }
    meta.update(split_meta)
    if auc is not None:
        meta["valid_auc"] = auc
    if cv_result is not None:
        meta.update(cv_result)

    if not dry_run:
        _atomic_dump_joblib(model, MODEL_PATH)
        _atomic_write_json(meta, MODEL_META_PATH)
        print("saved model: {}".format(MODEL_PATH))
        print("saved meta: {}".format(MODEL_META_PATH))
    else:
        print("[dry-run] model files not written")

    print("valid f1 threshold: {:.2f}".format(tuned_metrics["threshold"]))
    print("ready/promotion thresholds: {:.2f}/{:.2f}".format(
        ready_metrics["threshold"], promotion_metrics["threshold"]
    ))
    print("promotion f1/precision/recall: {:.4f}/{:.4f}/{:.4f}".format(
        promotion_metrics["f1"], promotion_metrics["precision"], promotion_metrics["recall"]
    ))
    if auc is not None:
        print("valid auc: {:.4f}".format(auc))
    if cv_result is not None and "cv_auc_mean" in cv_result:
        print("cv auc: {:.4f} +/- {:.4f}".format(
            cv_result["cv_auc_mean"], cv_result["cv_auc_std"]
        ))
    return meta


if __name__ == "__main__":
    args = parse_args()
    train(
        target=args.target,
        min_rows=args.min_rows,
        dry_run=args.dry_run,
        validation=args.validation,
        ready_min_precision=args.ready_min_precision,
        promotion_min_precision=args.promotion_min_precision,
    )
