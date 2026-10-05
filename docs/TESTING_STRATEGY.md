# Testing Strategy

## Experiment 8: Unit Testing

This document describes the automated testing strategy used for the Iris Classification MLOps project.

## 1. Objective

The objective of Experiment 8 is to:

* Write unit tests for data processing functions.
* Test the training pipeline.
* Validate model outputs and model quality.
* Create an automated test suite using `pytest`.
* Generate test coverage and JUnit test reports.
* Make the testing process suitable for continuous integration (CI).

## 2. Testing Framework

The following tools were used:

* **Python 3.11.9**
* **pytest 9.1.1** – for running automated tests.
* **pytest-cov 7.1.0** – for measuring code coverage.
* **scikit-learn** – for model training and evaluation.
* **pandas** – for data processing.
* **NumPy** – for numerical operations.

## 3. Test Structure

The following test files were created:

| Test File                         | Purpose                                      |
| --------------------------------- | -------------------------------------------- |
| `tests/test_preprocess.py`        | Tests data preprocessing functions           |
| `tests/test_features.py`          | Tests feature engineering functions          |
| `tests/test_validate.py`          | Tests data validation functions              |
| `tests/test_training_pipeline.py` | Tests model training and prediction pipeline |
| `tests/test_model_quality.py`     | Tests model output and minimum accuracy      |

A `pytest.ini` configuration file was also created to define the test directory and pytest settings.

## 4. Testing Layers

### 4.1 Preprocessing Tests

The preprocessing tests verify:

* Duplicate rows are removed.
* Missing numeric values are imputed.
* Rows with missing target values are removed.
* Empty DataFrames are handled correctly.

**Result:** 4 tests passed.

### 4.2 Feature Engineering Tests

The feature engineering tests verify:

* Sepal area calculation.
* Petal area calculation.
* Petal length category/bin assignment.
* Handling of zero petal length without crashing.

**Result:** 3 tests passed.

### 4.3 Data Validation Tests

The validation tests verify:

* Clean data passes validation.
* Missing required columns are detected.
* Invalid species values are detected.
* Out-of-range feature values are detected.

**Result:** 4 tests passed.

### 4.4 Training Pipeline Tests

The training pipeline tests verify:

* The Random Forest model can be trained without errors.
* Predictions have the correct shape.
* Prediction probabilities for each row sum to 1.

**Result:** 3 tests passed.

### 4.5 Model Quality Tests

The model quality tests verify:

* Model predictions belong to known class labels.
* Model accuracy meets the minimum acceptable accuracy threshold of 90%.

**Result:** 2 tests passed.

## 5. Test Execution

The complete test suite was executed using:

```bash
pytest -v
```

The result was:

```text
16 passed in 1.51s
```

Therefore, all **16 automated tests passed successfully**.

## 6. Coverage Report

Code coverage was generated using:

```bash
pytest --cov=src --cov-report=term-missing --junitxml=test-results.xml
```

The overall coverage result was:

```text
TOTAL    427    356    17%
```

Important pipeline coverage results:

| Source File                  | Coverage |
| ---------------------------- | -------: |
| `src/pipeline/features.py`   |      75% |
| `src/pipeline/preprocess.py` |      83% |
| `src/pipeline/validate.py`   |      76% |
| **Overall source coverage**  |  **17%** |

The lower overall coverage is because the project contains several training, MLflow, and utility scripts that were not directly executed by these unit tests.

## 7. JUnit Test Report

A JUnit XML test report was generated automatically:

```text
test-results.xml
```

This report can be used by CI/CD systems to collect and display automated test results.

## 8. Test Result Summary

| Metric           | Result    |
| ---------------- | --------- |
| Total tests      | 16        |
| Passed           | 16        |
| Failed           | 0         |
| Overall coverage | 17%       |
| JUnit report     | Generated |
| Test framework   | pytest    |

## 9. Conclusion

Experiment 8 successfully implemented an automated unit testing framework for the Iris Classification MLOps project. Tests were created for preprocessing, feature engineering, data validation, training pipeline, and model quality. All **16 tests passed successfully**, confirming that the tested components are functioning correctly. A coverage report and JUnit XML report were also generated, making the testing setup suitable for automated CI/CD workflows.
