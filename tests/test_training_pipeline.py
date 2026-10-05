# tests/test_training_pipeline.py
"""
End-to-end smoke tests for the training pipeline.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier


def make_synthetic_dataset():
    rng = np.random.RandomState(42)

    X = rng.randn(30, 4)
    y = rng.randint(0, 3, size=30)

    return X, y


def test_training_pipeline_fits_without_error():
    X, y = make_synthetic_dataset()

    model = RandomForestClassifier(
        n_estimators=10,
        random_state=42
    )

    model.fit(X, y)

    predictions = model.predict(X)

    assert predictions is not None


def test_predictions_have_correct_shape():
    X, y = make_synthetic_dataset()

    model = RandomForestClassifier(
        n_estimators=10,
        random_state=42
    )

    model.fit(X, y)

    predictions = model.predict(X)

    assert predictions.shape == (len(X),)


def test_predict_proba_rows_sum_to_one():
    X, y = make_synthetic_dataset()

    model = RandomForestClassifier(
        n_estimators=10,
        random_state=42
    )

    model.fit(X, y)

    probabilities = model.predict_proba(X)

    assert np.allclose(
        probabilities.sum(axis=1),
        1.0
    )