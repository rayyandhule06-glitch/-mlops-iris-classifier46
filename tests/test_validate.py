# tests/test_validate.py
"""
Unit tests for data validation (src/pipeline/validate.py).
"""

import pandas as pd
import pytest

from src.pipeline.validate import validate, DataValidationError


def valid_df():
    return pd.DataFrame({
        "sepal length (cm)": [5.1, 6.2],
        "sepal width (cm)": [3.5, 3.0],
        "petal length (cm)": [1.4, 4.5],
        "petal width (cm)": [0.2, 1.5],
        "sepal_area": [17.85, 18.6],
        "petal_area": [0.28, 6.75],
        "sepal_to_petal_length_ratio": [3.64, 1.38],
        "petal_length_bin": ["short", "medium"],
        "species": ["setosa", "versicolor"],
    })


def test_validate_clean_data_passes(tmp_path):
    df = valid_df()
    path = tmp_path / "valid.csv"
    df.to_csv(path, index=False)

    result = validate(str(path))

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2


def test_validate_missing_column_raises(tmp_path):
    df = valid_df().drop(columns=["sepal_area"])
    path = tmp_path / "missing_column.csv"
    df.to_csv(path, index=False)

    with pytest.raises(DataValidationError, match="Validation failed"):
        validate(str(path))


def test_validate_invalid_species_raises(tmp_path):
    df = valid_df()
    df.loc[0, "species"] = "unknown"
    path = tmp_path / "invalid_species.csv"
    df.to_csv(path, index=False)

    with pytest.raises(DataValidationError, match="Validation failed"):
        validate(str(path))


def test_validate_out_of_range_sepal_length_raises(tmp_path):
    df = valid_df()
    df.loc[0, "sepal length (cm)"] = 100.0
    path = tmp_path / "out_of_range.csv"
    df.to_csv(path, index=False)

    with pytest.raises(DataValidationError, match="Validation failed"):
        validate(str(path))