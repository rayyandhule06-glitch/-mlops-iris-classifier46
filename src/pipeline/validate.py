"""Stage 4: Data Validation.

Schema and statistical checks that must pass before data can
flow downstream to training. Raises on failure to hard-stop the pipeline.
"""

import argparse
import logging
import sys

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("validate")

EXPECTED_COLUMNS = {
    "sepal length (cm)",
    "sepal width (cm)",
    "petal length (cm)",
    "petal width (cm)",
    "species",
    "sepal_area",
    "petal_area",
    "sepal_to_petal_length_ratio",
    "petal_length_bin",
}

VALID_SPECIES = {"setosa", "versicolor", "virginica"}

RANGE_CHECKS = {
    "sepal length (cm)": (3.0, 9.0),
    "sepal width (cm)": (1.5, 5.5),
    "petal length (cm)": (0.5, 8.0),
    "petal width (cm)": (0.05, 3.0),
}


class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass


def validate(input_path: str) -> pd.DataFrame:
    """Validate the processed Iris dataset and return it if valid."""
    df = pd.read_csv(input_path)
    errors = []

    # Check required columns
    missing_cols = EXPECTED_COLUMNS - set(df.columns)
    if missing_cols:
        errors.append(f"Missing expected columns: {missing_cols}")

    # Check for missing values
    if df.isnull().any().any():
        null_cols = df.columns[df.isnull().any()].tolist()
        errors.append(f"Unexpected null values in columns: {null_cols}")

    # Check valid species labels only when the column exists
    if "species" in df.columns:
        invalid_species = set(df["species"].dropna().unique()) - VALID_SPECIES
        if invalid_species:
            errors.append(f"Unexpected species values: {invalid_species}")

    # Check numeric ranges only when the columns exist
    for col, (low, high) in RANGE_CHECKS.items():
        if col not in df.columns:
            continue

        out_of_range = df[(df[col] < low) | (df[col] > high)]
        if not out_of_range.empty:
            errors.append(
                f"{len(out_of_range)} rows out of expected range "
                f"for '{col}' ({low}-{high})"
            )

    # Raise one exception containing all validation errors
    if errors:
        for error in errors:
            logger.error(error)

        raise DataValidationError(
            f"Validation failed with {len(errors)} error(s): "
            + "; ".join(errors)
        )

    logger.info(
        "Validation PASSED: %d rows, %d columns, all checks satisfied",
        len(df),
        df.shape[1],
    )

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/processed/iris_features.csv"
    )
    args = parser.parse_args()

    try:
        validate(args.input)
    except DataValidationError as error:
        logger.error("Pipeline halted: %s", error)
        sys.exit(1)
