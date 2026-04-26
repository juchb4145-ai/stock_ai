import os

import joblib
import lightgbm as lgb
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split


DATA_PATH = os.path.join("data", "entry_training.csv")
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "opening_lgbm.pkl")
FEATURES = [
    "price_momentum",
    "open_return",
    "box_position",
    "direction_score",
    "volume_speed",
    "spread_rate",
]
TARGET = "success_10m"
MIN_TRAINING_ROWS = 50


def load_training_data():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError("학습 데이터가 없습니다: {}".format(DATA_PATH))

    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    missing = [column for column in FEATURES + [TARGET] if column not in df.columns]
    if missing:
        raise ValueError("학습 데이터 컬럼 누락: {}".format(missing))

    df = df.dropna(subset=FEATURES + [TARGET])
    for column in FEATURES + [TARGET]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=FEATURES + [TARGET])
    df[TARGET] = df[TARGET].astype(int)
    return df


def train():
    df = load_training_data()
    if len(df) < MIN_TRAINING_ROWS:
        raise ValueError("학습 데이터가 부족합니다. 현재 {}건, 최소 {}건 필요".format(len(df), MIN_TRAINING_ROWS))
    if df[TARGET].nunique() < 2:
        raise ValueError("성공/실패 클래스가 모두 있어야 학습할 수 있습니다.")

    x = df[FEATURES]
    y = df[TARGET]
    stratify = y if y.value_counts().min() >= 2 else None
    x_train, x_valid, y_train, y_valid = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=1234,
        stratify=stratify,
    )

    model = lgb.LGBMClassifier(
        n_estimators=200,
        learning_rate=0.03,
        max_depth=3,
        num_leaves=7,
        min_child_samples=10,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=1234,
    )
    model.fit(x_train, y_train)

    probabilities = model.predict_proba(x_valid)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    accuracy = accuracy_score(y_valid, predictions)
    try:
        auc = roc_auc_score(y_valid, probabilities)
    except ValueError:
        auc = None

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print("학습 완료: {}".format(MODEL_PATH))
    print("학습 데이터: {}건, 검증 데이터: {}건".format(len(x_train), len(x_valid)))
    print("accuracy: {:.4f}".format(accuracy))
    if auc is not None:
        print("auc: {:.4f}".format(auc))


if __name__ == "__main__":
    train()
