# tests/test_model_quality.py
"""
Model quality tests for the Iris classifier.
"""

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


MIN_ACCEPTABLE_ACCURACY = 0.90

FEATURE_COLS = [
    "sepal length (cm)",
    "sepal width (cm)",
    "petal length (cm)",
    "petal width (cm)",
    "sepal_area",
    "petal_area",
    "sepal_to_petal_length_ratio",
]


def load_feature_data():
    return pd.read_csv("data/processed/iris_features.csv")


def prepare_data(df):
    X = df[FEATURE_COLS].copy()

    X = X.fillna(X.median())

    encoder = LabelEncoder()
    y = encoder.fit_transform(df["species"])

    return X, y, encoder


def train_model(X_train, y_train):
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        random_state=42
    )

    model.fit(X_train, y_train)

    return model


def test_predictions_are_known_labels():
    df = load_feature_data()

    X, y, encoder = prepare_data(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = train_model(X_train, y_train)

    predictions = model.predict(X_test)

    assert set(predictions).issubset(set(y))


def test_model_accuracy_meets_minimum_threshold():
    df = load_feature_data()

    X, y, encoder = prepare_data(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = train_model(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    assert accuracy >= MIN_ACCEPTABLE_ACCURACY, (
        f"Model accuracy {accuracy:.3f} is below the "
        f"minimum acceptable accuracy "
        f"{MIN_ACCEPTABLE_ACCURACY:.2f}"
    )