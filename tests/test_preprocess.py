# tests/test_preprocess.py
"""
Unit tests for the preprocessing stage (src/pipeline/preprocess.py),
covering normal operation and edge/adversarial cases.
"""

import pandas as pd
import pytest
from src.pipeline.preprocess import preprocess


NUMERIC_COLS = [
    "sepal length (cm)",
    "sepal width (cm)",
    "petal length (cm)",
    "petal width (cm)",
]


@pytest.fixture
def valid_raw_df(tmp_path):
    df = pd.DataFrame({
        "sepal length (cm)": [5.1, 4.9, 4.7],
        "sepal width (cm)": [3.5, 3.0, 3.2],
        "petal length (cm)": [1.4, 1.4, 1.3],
        "petal width (cm)": [0.2, 0.2, 0.2],
        "species": ["setosa", "setosa", "setosa"],
        "collected_at": ["2026-01-01"] * 3,
    })

    path = tmp_path / "raw.csv"
    df.to_csv(path, index=False)
    return path


def test_preprocess_removes_duplicates(tmp_path, valid_raw_df):
    df = pd.read_csv(valid_raw_df)

    df_with_dupe = pd.concat(
        [df, df.iloc[[0]]],
        ignore_index=True
    )

    dupe_path = tmp_path / "raw_with_dupe.csv"
    df_with_dupe.to_csv(dupe_path, index=False)

    out_path = tmp_path / "out.csv"

    result = preprocess(str(dupe_path), str(out_path))

    assert len(result) == 3, "Duplicate row was not removed"


def test_preprocess_imputes_missing_numeric_values(tmp_path, valid_raw_df):
    df = pd.read_csv(valid_raw_df)

    df.loc[0, "sepal length (cm)"] = None

    missing_path = tmp_path / "raw_with_missing.csv"
    df.to_csv(missing_path, index=False)

    out_path = tmp_path / "out.csv"

    result = preprocess(str(missing_path), str(out_path))

    assert result["sepal length (cm)"].isnull().sum() == 0, \
        "Missing value was not imputed"

    expected_median = df["sepal length (cm)"].median()

    assert result.loc[0, "sepal length (cm)"] == pytest.approx(
        expected_median
    )


def test_preprocess_drops_rows_with_missing_target(tmp_path, valid_raw_df):
    df = pd.read_csv(valid_raw_df)

    df.loc[0, "species"] = None

    missing_target_path = tmp_path / "raw_missing_target.csv"
    df.to_csv(missing_target_path, index=False)

    out_path = tmp_path / "out.csv"

    result = preprocess(
        str(missing_target_path),
        str(out_path)
    )

    assert len(result) == 2, \
        "Row with missing target label was not dropped"


def test_preprocess_handles_empty_dataframe(tmp_path):
    empty_df = pd.DataFrame(
        columns=NUMERIC_COLS + ["species", "collected_at"]
    )

    empty_path = tmp_path / "empty.csv"
    empty_df.to_csv(empty_path, index=False)

    out_path = tmp_path / "out.csv"

    result = preprocess(
        str(empty_path),
        str(out_path)
    )

    assert len(result) == 0
    assert list(result.columns[:4]) == NUMERIC_COLS