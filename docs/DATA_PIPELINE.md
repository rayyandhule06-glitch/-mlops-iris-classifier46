# Data Pipeline Documentation

## Overview

This document describes the end-to-end data pipeline for the Iris classifier project.
The pipeline was introduced in **Experiment 4** and is implemented as a **DVC Pipeline**
declared in `dvc.yaml`.

The pipeline ingests raw data, cleans it, derives new model-useful features, and validates
the result **before** it is allowed to flow downstream to model training. Every stage is a
separate, independently runnable Python module under `src/pipeline/`, so that each stage has
clearly declared inputs and outputs and can be tested and re-run in isolation.

## Pipeline Diagram

```text
                     +-----------+
                     |  collect  |    src/pipeline/collect.py
                     +-----------+
                           |
                           v
              data/raw/iris_raw.csv
                           |
                           v
                    +--------------+
                    |  preprocess  |    src/pipeline/preprocess.py
                    +--------------+
                           |
                           v
        data/processed/iris_preprocessed.csv
                           |
                           v
                     +-----------+
                     | features  |    src/pipeline/features.py
                     +-----------+
                           |
                           v
          data/processed/iris_features.csv
                           |
                           v
                     +-----------+
                     | validate  |    src/pipeline/validate.py
                     +-----------+
                           |
             +-------------+-------------+
             |                           |
             v                           v
  PASS: flows downstream        FAIL: raises DataValidationError
  to model training             and exits with status code 1
```

## Declared Dependency Graph (`dvc.yaml`)

`dvc.yaml` declares each stage with its command (`cmd`), its dependencies (`deps` — the input
files **and** the stage's own code file), and its outputs (`outs`):

```text
collect  --->  preprocess  --->  features  --->  validate
```

| Stage        | `deps`                                                              | `outs`                                |
| ------------ | ------------------------------------------------------------------- | ------------------------------------- |
| `collect`    | _(none declared)_                                                   | `data/raw/iris_raw.csv`                |
| `preprocess` | `data/raw/iris_raw.csv`, `src/pipeline/preprocess.py`               | `data/processed/iris_preprocessed.csv` |
| `features`   | `data/processed/iris_preprocessed.csv`, `src/pipeline/features.py`  | `data/processed/iris_features.csv`     |
| `validate`   | `data/processed/iris_features.csv`, `src/pipeline/validate.py`      | _(none — terminal stage)_              |

## Pipeline Layout in the Repository

```text
mlops-iris-classifier/
├── dvc.yaml                          # pipeline stage definitions (deps / outs)
├── dvc.lock                          # hashes of every dep and out from the last run
├── data/
│   ├── raw/
│   │   ├── iris_raw.csv              # output of collect
│   │   └── iris_v1.csv (+ .dvc)      # Experiment 3 dataset version
│   ├── processed/
│   │   ├── iris_preprocessed.csv     # output of preprocess
│   │   └── iris_features.csv         # output of features
│   └── validated/                    # staging zone for data that passed validation
└── src/pipeline/
    ├── __init__.py
    ├── collect.py                    # Stage 1: Data Collection
    ├── preprocess.py                 # Stage 2: Data Preprocessing
    ├── features.py                   # Stage 3: Feature Engineering
    └── validate.py                   # Stage 4: Data Validation
```

---

## Stage 1 — Data Collection

**Module:** `src/pipeline/collect.py`

**Purpose:** Simulate ingesting raw data from an external source and write it to the raw data
zone, together with basic collection-time metadata.

**Inputs:** None declared in `dvc.yaml`. The source data is loaded through
`sklearn.datasets.load_iris(as_frame=True)`, which stands in for an external source such as a
database or an API endpoint.

**Outputs:** `data/raw/iris_raw.csv`

**Transformations performed:**

| Step | Description |
| ---- | ----------- |
| Load source | `load_iris(as_frame=True)` returns a 150-row data frame of the four measurements plus the integer `target`. |
| Rename target | The `target` column is renamed to `species`. |
| Decode labels | Integer targets `0, 1, 2` are mapped to `setosa`, `versicolor`, `virginica` using `iris.target_names`. |
| Attach metadata | A `collected_at` column is added holding the collection time in UTC (ISO-8601). |

**Resulting schema:** 150 rows × 6 columns —
`sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)`,
`species`, `collected_at`.

**Run standalone:**

```bash
python src/pipeline/collect.py --output data/raw/iris_raw.csv
```

**Observed output:**

```text
2026-09-30 ... [INFO] Collected 150 rows -> data/raw/iris_raw.csv
```

---

## Stage 2 — Data Preprocessing

**Module:** `src/pipeline/preprocess.py`

**Purpose:** Clean the raw data — remove exact duplicate records, correct column types, and
impute missing values — so that downstream stages always receive a tidy, typed table.

**Inputs:** `data/raw/iris_raw.csv`

**Outputs:** `data/processed/iris_preprocessed.csv`

**Transformations performed:**

| Step | Description |
| ---- | ----------- |
| Drop duplicates | `df.drop_duplicates()` removes exact duplicate records (all columns identical, including `collected_at`). |
| Type coercion | Each of the four measurement columns is forced to numeric with `pd.to_numeric(..., errors="coerce")`. |
| Missing-value imputation | Any `NaN` produced by coercion (or already present) is filled with that column's **median**; the count and the median used are logged. |
| Drop unusable targets | Rows whose `species` label is missing are dropped — the label cannot be imputed. |
| Drop collection metadata | The `collected_at` column is removed, since it is pipeline provenance metadata, not a model feature. |

**Resulting schema:** 149 rows × 5 columns (the four measurements plus `species`).

> **Note on the duplicate drop:** the standard Iris dataset contains one exact duplicated
> record (a *virginica* observation that appears twice), so preprocessing reduces
> 150 raw rows to 149 clean rows. This is genuine, expected de-duplication behaviour, and the
> log line `Dropped 1 duplicate rows` records it.

**Run standalone:**

```bash
python src/pipeline/preprocess.py --input data/raw/iris_raw.csv --output data/processed/iris_preprocessed.csv
```

**Observed output:**

```text
2026-09-30 ... [INFO] Dropped 1 duplicate rows
2026-09-30 ... [INFO] Preprocessed 149 rows -> data/processed/iris_preprocessed.csv
```

---

## Stage 3 — Feature Engineering

**Module:** `src/pipeline/features.py`

**Purpose:** Derive new, model-useful variables from the raw measurements. Interaction terms
and ratios make relationships between measurements explicit, which helps the model and makes
the data easier to reason about. Binning turns a continuous measurement into an interpretable
category that is also convenient for drift monitoring.

**Inputs:** `data/processed/iris_preprocessed.csv`

**Outputs:** `data/processed/iris_features.csv`

**Features derived:**

| New feature                   | Formula / logic                                              | Rationale |
| ----------------------------- | ------------------------------------------------------------ | --------- |
| `sepal_area`                  | `sepal length (cm) * sepal width (cm)`                       | Explicit interaction term capturing overall sepal size. |
| `petal_area`                  | `petal length (cm) * petal width (cm)`                       | Explicit interaction term capturing overall petal size; strongly separates the species. |
| `sepal_to_petal_length_ratio` | `sepal length (cm) / petal length (cm)`                      | Scale-invariant shape ratio; a zero denominator is replaced with `pd.NA` instead of producing an infinity. |
| `petal_length_bin`            | `pd.cut(petal length, bins=[0, 2, 4.5, 7], labels=["short", "medium", "long"])` | Interpretable categorical bucket of petal length. |

**Resulting schema:** 149 rows × 9 columns — the four raw measurements, `species`, and the four
engineered features listed above.

**Run standalone:**

```bash
python src/pipeline/features.py --input data/processed/iris_preprocessed.csv --output data/processed/iris_features.csv
```

**Observed output:**

```text
2026-09-30 ... [INFO] Engineered 9 features -> data/processed/iris_features.csv
```

---

## Stage 4 — Data Validation

**Module:** `src/pipeline/validate.py`

**Purpose:** Verify that the data meets defined structural (schema) and statistical
(distributional) expectations before it is allowed to flow downstream to training.
It is the pipeline's primary defence against a **silent failure** — a run that completes
successfully but trains a model on corrupted data.

**Inputs:** `data/processed/iris_features.csv`

**Outputs:** None — this is the terminal stage. Its "output" is a verdict: it either returns
the validated data frame, or it raises and halts the pipeline.

**Validation rules enforced:**

| # | Category | Rule | Implementation |
| - | -------- | ---- | -------------- |
| 1 | Schema | All 9 expected columns are present | `EXPECTED_COLUMNS - set(df.columns)` must be empty. |
| 2 | Schema | No unexpected null values in any column | `df.isnull().any().any()` must be `False`. |
| 3 | Distributional | Species label is one of `setosa`, `versicolor`, `virginica` | `set(df["species"].unique()) - VALID_SPECIES` must be empty. |
| 4 | Distributional | `sepal length (cm)` within 3.0 – 9.0 | Range check against `RANGE_CHECKS`. |
| 5 | Distributional | `sepal width (cm)` within 1.5 – 5.5 | Range check against `RANGE_CHECKS`. |
| 6 | Distributional | `petal length (cm)` within 0.5 – 8.0 | Range check against `RANGE_CHECKS`. |
| 7 | Distributional | `petal width (cm)` within 0.05 – 3.0 | Range check against `RANGE_CHECKS`. |

**Failure semantics:** every failed rule is logged as `[ERROR]`. If at least one rule fails the
stage raises `DataValidationError`, which is caught in the `__main__` block, logged as
`Pipeline halted: ...`, and converted into `sys.exit(1)`. A non-zero exit status is the standard
signal that makes an orchestrator (or a CI job) stop the pipeline instead of training on bad data.

**Run standalone:**

```bash
python src/pipeline/validate.py --input data/processed/iris_features.csv
echo "exit code: $?"
```

**Observed output on good data:**

```text
2026-09-30 ... [INFO] Validation PASSED: 149 rows, 9 columns, all checks satisfied
exit code: 0
```

**Observed output on corrupted data** (one `sepal length (cm)` value manually set to `50`):

```text
2026-09-30 ... [ERROR] 1 rows out of expected range for 'sepal length (cm)' (3.0-9.0)
2026-09-30 ... [ERROR] Pipeline halted: Validation failed with 1 error(s)
exit code: 1
```

---

## Running the Pipeline

### First run — `dvc repro`

From the project root:

```bash
dvc repro
```

DVC walks the dependency graph in order and executes every stage whose declared dependencies
have changed. On a first run all four stages execute:

```text
Running stage 'collect':
> python src/pipeline/collect.py --output data/raw/iris_raw.csv
... [INFO] Collected 150 rows -> data/raw/iris_raw.csv
Running stage 'preprocess':
> python src/pipeline/preprocess.py --input data/raw/iris_raw.csv --output data/processed/iris_preprocessed.csv
... [INFO] Dropped 1 duplicate rows
... [INFO] Preprocessed 149 rows -> data/processed/iris_preprocessed.csv
Running stage 'features':
> python src/pipeline/features.py --input data/processed/iris_preprocessed.csv --output data/processed/iris_features.csv
... [INFO] Engineered 9 features -> data/processed/iris_features.csv
Running stage 'validate':
> python src/pipeline/validate.py --input data/processed/iris_features.csv
... [INFO] Validation PASSED: 149 rows, 9 columns, all checks satisfied
Updating lock file 'dvc.lock'
Use `dvc push` to send your updates to remote storage.
```

Exit status is `0`.

### Second run — dependency-aware caching

Running `dvc repro` again with no changes made re-executes nothing:

```text
Stage 'collect' didn't change, skipping
Stage 'preprocess' didn't change, skipping
Stage 'features' didn't change, skipping
Stage 'validate' didn't change, skipping
```

DVC compares the current content hashes of each stage's `deps` with the hashes stored in
`dvc.lock`. Because nothing changed, every stage is skipped and its existing outputs are reused.
Changing any dependency — for example editing `src/pipeline/features.py` — causes that stage and
every downstream stage to be re-executed, while upstream stages are still skipped. This gives the
pipeline the correctness of a build system combined with the efficiency of not recomputing work
whose inputs are unchanged.

### Viewing the dependency graph — `dvc dag`

```bash
dvc dag
```

```text
  +---------+
  | collect |
  +---------+
       *
       *
       *
+------------+
| preprocess |
+------------+
       *
       *
       *
 +----------+
 | features |
 +----------+
       *
       *
       *
 +----------+
 | validate |
 +----------+
+--------------------------+
| data\raw\iris_v1.csv.dvc |
+--------------------------+
```

The graph confirms the correct linear order: `collect -> preprocess -> features -> validate`.

### Negative test — validation must halt the pipeline

Manually corrupt the feature file, then re-run the validation stage directly:

```bash
python -c "import pandas as pd; d = pd.read_csv('data/processed/iris_features.csv'); d.loc[0, 'sepal length (cm)'] = 50.0; d.to_csv('data/processed/iris_features.csv', index=False)"
python src/pipeline/validate.py --input data/processed/iris_features.csv
echo $?     # -> 1
```

Observed:

```text
[ERROR] 1 rows out of expected range for 'sepal length (cm)' (3.0-9.0)
[ERROR] Pipeline halted: Validation failed with 1 error(s)
1
```

The out-of-range value is caught, the stage raises, and the process exits with status code `1` —
the signal that stops an orchestrated or CI-driven pipeline before bad data can reach training.
Restoring the file makes the stage pass again with exit status `0` (use
`dvc checkout data/processed/iris_features.csv` or `dvc repro` to restore the DVC-tracked output).

### `dvc.lock`

After every successful `dvc repro`, `dvc.lock` is created/updated. It captures the exact MD5 hash
and byte size of every stage dependency and output from the last run, which is what makes the
skip/re-run decisions reproducible:

```yaml
stages:
  preprocess:
    deps:
    - path: data/raw/iris_raw.csv
      md5: 0d235b79c4c4b1af6b0601fb587b887e
      size: 8992
    - path: src/pipeline/preprocess.py
      md5: ...
    outs:
    - path: data/processed/iris_preprocessed.csv
      md5: a14ddf816aea4f7a003d1f974d3aaef1
      size: 4002
```

---

## Git and DVC Workflow for the Pipeline

`dvc.yaml` and `dvc.lock` are text files and belong in Git, while the data files they describe are
tracked by DVC. The complete workflow is:

```text
Define stages in dvc.yaml
        ↓
dvc repro          (execute stages + write dvc.lock)
        ↓
git add dvc.yaml dvc.lock src/pipeline/ data/raw/.gitignore data/processed/.gitignore
        ↓
git commit -m "feat: add end-to-end DVC data pipeline (collect -> preprocess -> features -> validate)"
        ↓
dvc push           (upload data outputs to the configured DVC remote)
        ↓
git push origin main
```

Because the stage outputs live under `data/`, DVC adds them to the `.gitignore` files in those
directories (`data/raw/.gitignore`, `data/processed/.gitignore`) so the CSVs are never committed
directly to Git.

---

## Verification Results

| # | Check | Command | Result |
| - | ----- | ------- | ------ |
| 1 | Full pipeline executes in order, exit code 0 | `dvc repro` | Pass — all 4 stages ran, `Updating lock file 'dvc.lock'` |
| 2 | Unchanged re-run is fully cached | `dvc repro` (second time) | Pass — all 4 stages reported `didn't change, skipping` |
| 3 | Dependency graph is linear and correct | `dvc dag` | Pass — `collect -> preprocess -> features -> validate` |
| 4 | Validation halts on bad data | corrupt `iris_features.csv`, run `validate.py` | Pass — range error logged, exit code `1` |
| 5 | Validation passes on good data | run `validate.py` | Pass — `149 rows, 9 columns, all checks satisfied`, exit code `0` |
| 6 | Lock file records dep/out hashes | inspect `dvc.lock` | Pass — hash + size recorded for every dep and out |
| 7 | Data quality | `pandas` shape checks | 150 raw rows → 149 after de-duplication → 9 feature columns |

---

## Notes and Known Limitations

* **`collect` declares no `deps`.** `src/pipeline/collect.py` is not listed as a dependency of the
  `collect` stage, matching the stage definition given in the laboratory manual. A consequence is
  that editing `collect.py` alone does not invalidate the stage — DVC has nothing to hash and
  reports `Stage 'collect' didn't change, skipping`. Adding `src/pipeline/collect.py` to that
  stage's `deps` in `dvc.yaml` removes this blind spot.
* **`collect` output is non-deterministic.** The `collected_at` UTC timestamp written by
  `collect.py` changes on every execution, so the raw file's hash (and therefore everything
  downstream) changes whenever the stage actually runs.
* **`data/validated/` is currently unused.** The directory is created as the staging zone for data
  that has passed validation, but the terminal stage does not write into it; validated data is
  consumed in memory by downstream training code.
* **Imputation is silent when there is nothing to impute.** The median-imputation branch in
  `preprocess.py` only logs when a column actually contains missing values, so a clean run produces
  no imputation log lines — expected behaviour, not a skipped step.

## Conclusion

The data pipeline is declarative and reproducible. Each stage is an isolated module with declared
inputs and outputs, wired together by `dvc.yaml` and pinned by `dvc.lock`. Running `dvc repro`
executes the whole `collect -> preprocess -> features -> validate` chain and re-executes only the
stages whose dependencies actually changed, while the validation stage hard-stops the pipeline with
a non-zero exit code the moment the data stops meeting its schema or range expectations —
preventing corrupted data from silently reaching model training.
