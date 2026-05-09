"""Train the Dante LightGBM entry model.

This script trains the model consumed by ai_server.py:

    models/dante_lgbm.pkl
    models/dante_lgbm_meta.json

It reads both ready samples and shadow samples so the model can learn from
missed opportunities as well as rule-approved entries. By default the target is
`reached_1r`, which is dense enough for an early shadow model.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from typing import Dict, Iterable, List, Optional

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

import scoring


DATA_PATHS = (
    os.path.join("data", "dante_entry_training.csv"),
    os.path.join("data", "dante_shadow_training.csv"),
)
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "dante_lgbm.pkl")
MODEL_META_PATH = os.path.join(MODEL_DIR, "dante_lgbm_meta.json")
FEATURES = list(scoring.DANTE_ENTRY_FEATURE_NAMES)
DEFAULT_TARGET = "reached_1r"
SUPPORTED_TARGETS = ("reached_1r", "reached_2r", "hit_stop")
MIN_TRAINING_ROWS = 500
DEFAULT_THRESHOLD = 0.5
VALID_SIZE = 0.2
RANDOM_STATE = 1234
CV_SPLITS = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Dante LightGBM entry model")
    parser.add_argument("--target", default=DEFAULT_TARGET, choices=SUPPORTED_TARGETS)
    parser.add_argument("--min-rows", type=int, default=MIN_TRAINING_ROWS)
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


def load_training_data(target: str) -> pd.DataFrame:
    frames = [
        _read_csv(DATA_PATHS[0], "entry"),
        _read_csv(DATA_PATHS[1], "shadow"),
    ]
    df = pd.concat([frame for frame in frames if not frame.empty], ignore_index=True)
    if df.empty:
        raise FileNotFoundError("No Dante training CSV rows found")

    missing = [column for column in FEATURES + [target] if column not in df.columns]
    if missing:
        raise ValueError("Dante training columns missing: {}".format(missing))

    if "sample_id" in df.columns:
        df = df.drop_duplicates(subset=["sample_id"], keep="last")

    df = _coerce_numeric(df, FEATURES + [target])
    df = df.dropna(subset=FEATURES + [target]).copy()
    df[target] = df[target].astype(int)

    # For hit_stop, the positive class means "bad". Flip it so label 1 always
    # means a desirable entry for the model/server threshold contract.
    if target == "hit_stop":
        df[target] = 1 - df[target]

    return df


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
    for threshold in np.arange(0.30, 0.81, 0.01):
        current = metrics_at_threshold(y_true, probabilities, float(round(threshold, 2)))
        if current["f1"] > best["f1"] or (
            current["f1"] == best["f1"] and current["accuracy"] > best["accuracy"]
        ):
            best = current
    return best


def _safe_auc(y_true, probabilities) -> Optional[float]:
    if len(pd.Series(y_true).dropna().unique()) < 2:
        return None
    return float(roc_auc_score(y_true, probabilities))


def run_cv(df: pd.DataFrame, target: str) -> Optional[Dict[str, float]]:
    x = df[FEATURES]
    y = df[target]
    min_class_count = int(y.value_counts().min())
    n_splits = min(CV_SPLITS, min_class_count)
    if n_splits < 2:
        return None

    kfold = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    aucs: List[float] = []
    accuracies: List[float] = []
    f1s: List[float] = []
    precisions: List[float] = []
    recalls: List[float] = []

    for train_index, valid_index in kfold.split(x, y):
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
        "cv_accuracy_mean": float(np.mean(accuracies)),
        "cv_f1_mean": float(np.mean(f1s)),
        "cv_precision_mean": float(np.mean(precisions)),
        "cv_recall_mean": float(np.mean(recalls)),
    }
    if aucs:
        result["cv_auc_mean"] = float(np.mean(aucs))
        result["cv_auc_std"] = float(np.std(aucs))
    return result


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


def train(target: str, min_rows: int, dry_run: bool = False) -> Dict:
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

    x = df[FEATURES]
    y = df[target]
    stratify = y if y.value_counts().min() >= 2 else None
    x_train, x_valid, y_train, y_valid = train_test_split(
        x,
        y,
        test_size=VALID_SIZE,
        random_state=RANDOM_STATE,
        stratify=stratify,
    )

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
    auc = _safe_auc(y_valid, probabilities)
    cv_result = run_cv(df, target)

    meta = {
        "model_name": "DanteLightGBM",
        "target": target,
        "threshold": tuned_metrics["threshold"],
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
    }
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

    print("valid tuned threshold: {:.2f}".format(tuned_metrics["threshold"]))
    print("valid f1/precision/recall: {:.4f}/{:.4f}/{:.4f}".format(
        tuned_metrics["f1"], tuned_metrics["precision"], tuned_metrics["recall"]
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
    train(target=args.target, min_rows=args.min_rows, dry_run=args.dry_run)
