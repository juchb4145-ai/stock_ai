import json
import os
import tempfile

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

import scoring


DATA_PATH = os.path.join("data", "entry_training.csv")
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "opening_lgbm.pkl")
MODEL_META_PATH = os.path.join(MODEL_DIR, "opening_lgbm_meta.json")
# main.py / ai_server.py 와 같은 source of truth를 사용해 feature 순서가 어긋나지 않도록 한다.
FEATURES = list(scoring.ENTRY_FEATURE_NAMES)
TARGET = "success_10m"
MIN_TRAINING_ROWS = 500
DEFAULT_THRESHOLD = 0.5
VALID_SIZE = 0.2
RANDOM_STATE = 1234
CV_SPLITS = 5


def load_training_data():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError("학습 데이터가 없습니다: {}".format(DATA_PATH))

    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    missing = [column for column in FEATURES + [TARGET] if column not in df.columns]
    if missing:
        raise ValueError("학습 데이터 컬럼 누락: {}".format(missing))

    df = df.dropna(subset=FEATURES + [TARGET]).copy()
    for column in FEATURES + [TARGET]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=FEATURES + [TARGET]).copy()
    df[TARGET] = df[TARGET].astype(int)
    return df


def make_model():
    return lgb.LGBMClassifier(
        n_estimators=2000,
        learning_rate=0.02,
        max_depth=-1,
        num_leaves=15,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_STATE,
        class_weight="balanced",
        verbosity=-1,
    )


def find_best_threshold(y_true, probabilities):
    best_threshold = DEFAULT_THRESHOLD
    best_f1 = -1.0
    best_accuracy = 0.0
    for threshold in np.arange(0.30, 0.71, 0.01):
        predictions = (probabilities >= threshold).astype(int)
        f1 = f1_score(y_true, predictions, zero_division=0)
        accuracy = accuracy_score(y_true, predictions)
        if f1 > best_f1 or (f1 == best_f1 and accuracy > best_accuracy):
            best_f1 = f1
            best_accuracy = accuracy
            best_threshold = float(round(threshold, 2))
    return best_threshold, best_f1, best_accuracy


def run_cv(df):
    x = df[FEATURES]
    y = df[TARGET]
    min_class_count = y.value_counts().min()
    n_splits = min(CV_SPLITS, int(min_class_count))
    if n_splits < 2:
        return None

    kfold = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    fold_aucs = []
    fold_accuracies = []
    fold_f1s = []

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
            callbacks=[
                lgb.early_stopping(stopping_rounds=100, verbose=False),
            ],
        )
        probabilities = model.predict_proba(x_valid)[:, 1]
        threshold, _, _ = find_best_threshold(y_valid, probabilities)
        predictions = (probabilities >= threshold).astype(int)
        fold_aucs.append(roc_auc_score(y_valid, probabilities))
        fold_accuracies.append(accuracy_score(y_valid, predictions))
        fold_f1s.append(f1_score(y_valid, predictions, zero_division=0))

    return {
        "cv_splits": n_splits,
        "cv_auc_mean": float(np.mean(fold_aucs)),
        "cv_auc_std": float(np.std(fold_aucs)),
        "cv_accuracy_mean": float(np.mean(fold_accuracies)),
        "cv_f1_mean": float(np.mean(fold_f1s)),
    }


def train():
    df = load_training_data()
    total_rows = len(df)
    positive_count = int(df[TARGET].sum())
    negative_count = int(total_rows - positive_count)
    print("데이터 현황: 전체 {}건 (성공 {}, 실패 {})".format(total_rows, positive_count, negative_count))

    if total_rows < MIN_TRAINING_ROWS:
        print(
            "[학습 보류] 학습 데이터가 {}건 미만이므로 기존 모델을 유지합니다. (현재 {}건 / 기준 {}건)".format(
                MIN_TRAINING_ROWS,
                total_rows,
                MIN_TRAINING_ROWS,
            )
        )
        if os.path.exists(MODEL_PATH):
            print("기존 모델 유지: {}".format(MODEL_PATH))
        else:
            print("주의: 기존 모델 파일이 없어 fallback 점수 로직이 사용됩니다.")
        return

    if df[TARGET].nunique() < 2:
        raise ValueError("성공/실패 클래스가 모두 있어야 학습할 수 있습니다.")

    x = df[FEATURES]
    y = df[TARGET]
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
        callbacks=[
            lgb.early_stopping(stopping_rounds=100, verbose=False),
        ],
    )

    probabilities = model.predict_proba(x_valid)[:, 1]
    default_predictions = (probabilities >= DEFAULT_THRESHOLD).astype(int)
    default_accuracy = accuracy_score(y_valid, default_predictions)
    auc = roc_auc_score(y_valid, probabilities)

    best_threshold, best_f1, tuned_accuracy = find_best_threshold(y_valid, probabilities)
    tuned_predictions = (probabilities >= best_threshold).astype(int)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    cv_result = run_cv(df)
    model_meta = {
        "model_name": "LightGBM",
        "threshold": best_threshold,
        "features": FEATURES,
        "train_rows": int(len(x_train)),
        "valid_rows": int(len(x_valid)),
        "valid_auc": float(auc),
        "valid_accuracy_default_0_5": float(default_accuracy),
        "valid_accuracy_tuned": float(tuned_accuracy),
        "valid_f1_tuned": float(best_f1),
        "positive_count": positive_count,
        "negative_count": negative_count,
    }
    if cv_result is not None:
        model_meta.update(cv_result)

    # ai_server가 운영 중에 같은 파일을 읽을 수 있어 atomic 교체로 부분 쓰기 방지
    fd, tmp_path = tempfile.mkstemp(prefix="opening_lgbm_meta_", suffix=".json", dir=MODEL_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(model_meta, file, ensure_ascii=False, indent=2)
        os.replace(tmp_path, MODEL_META_PATH)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    print("학습 완료: {}".format(MODEL_PATH))
    print("메타 저장: {}".format(MODEL_META_PATH))
    print("학습 데이터: {}건, 검증 데이터: {}건".format(len(x_train), len(x_valid)))
    print("accuracy@0.50: {:.4f}".format(default_accuracy))
    print("accuracy@tuned({:.2f}): {:.4f}".format(best_threshold, tuned_accuracy))
    print("f1@tuned({:.2f}): {:.4f}".format(best_threshold, best_f1))
    print("auc: {:.4f}".format(auc))
    if cv_result is not None:
        print(
            "cv({}fold) auc: {:.4f} ± {:.4f}, acc: {:.4f}, f1: {:.4f}".format(
                cv_result["cv_splits"],
                cv_result["cv_auc_mean"],
                cv_result["cv_auc_std"],
                cv_result["cv_accuracy_mean"],
                cv_result["cv_f1_mean"],
            )
        )


if __name__ == "__main__":
    train()
