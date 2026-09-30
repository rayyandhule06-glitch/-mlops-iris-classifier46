# Feature Store Analysis

## Overview

Experiment 5 introduced a **Feature Store** (Feast 0.66.0) on top of the Experiment 4 data
pipeline. The Experiment 4 output `data/processed/iris_features.csv` is converted into a
Feast-ready Parquet source, registered as an entity + two feature views + one feature service,
materialized into a SQLite online store, and then retrieved through both the **online**
(low-latency serving) and **offline** (point-in-time-correct training) paths.

The whole feature repository lives in `practical5_feast/iris_feature_repo/feature_repo/`.

## Architecture

```text
                Experiment 4 pipeline output
          data/processed/iris_features.csv  (149 rows x 9 columns)
                                |
                     prepare_feature_source.py
              (adds sample_id + event_timestamp + created_timestamp)
                                |
                                v
              data/iris_features.parquet   (149 rows x 12 columns)
                                |
                            features.py
        (Entity sample_id -> 2 FeatureViews -> 1 FeatureService)
                                |
                            feast apply
                                |
                                v
                    data/registry.db  (versioned metadata)
                                |
                     feast materialize-incremental
                                |
                 +--------------+---------------+
                 |                              |
                 v                              v
        OFFLINE STORE                   ONLINE STORE
   (Parquet, full history)          (SQLite, latest value only)
   get_historical_features()        get_online_features()
   -> training datasets             -> real-time prediction
        Step 7                           Step 6 / Step 8
```

Both stores are populated from the **same** `features.py` definitions and the **same** Parquet
source, which is what structurally guarantees that a feature served online is computed identically
to the one used in training.

## Registered Feast Objects

| Object | Kind | Details |
| ------ | ---- | ------- |
| `sample_id` | Entity | `join_keys=["sample_id"]`, `ValueType.INT64` — one Iris flower sample |
| `iris_measurements` | FeatureView | TTL 365 days; `sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)` — all `Float32` |
| `iris_engineered_features` | FeatureView | TTL 365 days; `sepal_area`, `petal_area`, `sepal_to_petal_length_ratio` (`Float32`), `petal_length_bin` (`String`) |
| `iris_feature_service` | FeatureService | `iris_measurements` + `iris_engineered_features` — the reusable bundle consumed by models |
| `iris_features_source` | FileSource | `data/iris_features.parquet`, `timestamp_field=event_timestamp`, `created_timestamp_column=created_timestamp` |

## Benefit 1 — Elimination of Training-Serving Skew

Training-serving skew is the situation where the features computed for offline training differ
from those available at online inference time. The feature store removes it structurally rather
than by developer discipline, because **the same `iris_engineered_features` definition feeds both
paths**.

Evidence — the same entity (`sample_id = 1`) retrieved through both code paths returned identical
values:

| Feature | Online path (Step 6) | Offline path (Step 7) | Match |
| ------- | -------------------: | --------------------: | :---: |
| `sepal length (cm)` | 4.9 | 4.9 | ✅ |
| `sepal width (cm)` | 3.0 | 3.0 | ✅ |
| `petal length (cm)` | 1.4 | 1.4 | ✅ |
| `petal width (cm)` | 0.2 | 0.2 | ✅ |
| `sepal_area` | 14.7 | 14.70 | ✅ |
| `petal_area` | 0.28 | 0.28 | ✅ |
| `sepal_to_petal_length_ratio` | 3.5 | 3.500000 | ✅ |
| `petal_length_bin` | short | short | ✅ |

The online values are served from SQLite (latest value per entity); the offline values come from
an as-of join against the Parquet history. They agree because neither path recomputes anything —
both read the values produced by the single registered definition.

## Benefit 2 — Feature Reusability Across Models

Step 8 reuses the exact same `iris_feature_service` for a **structurally different model**: an
unsupervised KMeans clustering task instead of the supervised classifier of Experiment 4.
**Zero feature code was re-implemented** — the script contains no
`sepal length * sepal width` arithmetic at all:

```python
feature_service = store.get_feature_service("iris_feature_service")
all_features = store.get_online_features(features=feature_service, entity_rows=entity_rows).to_df()
```

Observed result of the reuse (149 samples retrieved in a single online call, 8 feature columns):

```text
Feature Service reused for clustering: retrieved 149 rows x 8 feature columns

KMeans (k=3) cluster counts:
  cluster 0: 61 samples
  cluster 1: 38 samples
  cluster 2: 50 samples

Cluster vs. actual species:
species  setosa  versicolor  virginica
cluster
0             0          46         15
1             0           4         34
2            50           0          0
```

The clusters are non-trivial and recover the known Iris species groupings — `setosa` is isolated
perfectly (cluster 2 = all 50 setosa) and `versicolor` / `virginica` are largely separated — even
though clustering never saw the `species` label. This demonstrates that the registered features are
meaningful and directly consumable by a model that has nothing in common with the classifier that
motivated them.

## Benefit 3 — Centralized Governance

`features.py` is the **single source of truth** for feature logic across the whole project:

* The Iris measurement features and the four engineered features are declared once, with explicit
  dtypes and a 365-day TTL, rather than being re-derived in each model's training script.
* `registry.db` is a versioned metadata store recording exactly which entity, feature views and
  feature service exist — so the feature contract is auditable and cannot drift silently.
* Quality and ownership are centralized: adding or changing a feature means editing one file and
  running `feast apply`, and every consuming model picks the change up automatically.
* `.feastignore` restricts Feast's repo parsing to the definition file only, so the retrieval and
  helper scripts sitting in the same directory are never executed during `feast apply` — keeping
  registration deterministic and side-effect free.

## Point-in-Time Correctness

`get_historical_features` performs an **as-of join**: for each historical label row it returns only
feature values whose `event_timestamp` was at or before that row's own timestamp. A naive join
using "current" values would leak future information into training and produce unrealistically
optimistic offline metrics that do not hold up in production. Because the entity DataFrame in
Step 7 supplies each row's own `event_timestamp`, Feast returns the value valid *at that moment* —
exactly what would genuinely have been available for prediction at that historical time.

## Verification Evidence

| # | Check | Command | Result |
| - | ----- | ------- | ------ |
| 1 | Feast installed | `pip show feast` | `feast 0.66.0` |
| 2 | Repository initialized | `feast init -t local iris_feature_repo` | created `feature_repo/` with `feature_store.yaml` + `data/` |
| 3 | Source prepared | `python prepare_feature_source.py` | `Wrote 149 rows to data\iris_features.parquet`; shape `(149, 12)` |
| 4 | Definitions compile/import | `python -m py_compile features.py` | no output (success); `import features` OK |
| 5 | Registration | `feast apply` | 1 entity + 2 feature views + 1 feature service; `registry.db` created |
| 6 | Re-apply is idempotent | `feast apply` (again) | `No changes to registry` / `No changes to infrastructure` |
| 7 | Entity listed | `feast entities list` | `sample_id  ValueType.INT64` |
| 8 | Feature views listed | `feast feature-views list` | `iris_engineered_features`, `iris_measurements` — both `{'sample_id'}`, ENABLED |
| 9 | Materialization | `feast materialize-incremental <UTC now>` | 2 feature views; `online_store.db` 28,672 → 348,160 bytes |
| 10 | Online state | `feast feature-views list` | both now `AVAILABLE_ONLINE` |
| 11 | Online retrieval | `python get_online_features.py` | sample_id 1 matches the manual exactly; **no null values** for sample_id 0, 1, 2 |
| 12 | Offline retrieval | `python get_historical_features.py` | 5 point-in-time rows, all 8 feature columns populated |
| 13 | Feature service reuse | `python reuse_features_for_clustering.py` | 149 rows retrieved, KMeans k=3 → 61 / 38 / 50, clusters recover species |
| 14 | Feature service listed | `feast feature-services list` | `iris_feature_service` with all 8 features |

## Notes and Deviations from the Manual

* **Python 3.13 instead of 3.11.** The manual's `py -3.11 -m venv .venv-feast` could not be followed
  literally because Python 3.11 is not installed on this machine. The environment was created with
  the installed **Python 3.13.14** (`py -3.13 -m venv .venv-feast`), which Feast supports
  (`Requires-Python >=3.10`). Nothing else about the setup changed.
* **`scikit-learn` added to the Feast environment.** The manual's Step 8 listing only *retrieves*
  features through the feature service, but its verification step requires the script to "print
  non-trivial cluster counts". The script therefore also runs a KMeans model over the retrieved
  features, which needs `scikit-learn` in `.venv-feast`.
* **`.feastignore` added.** Feast imports every `.py` file in the repo directory as a
  feature-definition module, so without this file `feast apply` also executed
  `prepare_feature_source.py` (rewriting the Parquet on every apply) and would have executed the
  retrieval scripts too.
* **The path to Experiment 4's output is resolved relative to the script**, not hard-coded to
  `C:/Users/Admin/...`, so the repository works on any machine.
* **`feast apply` reports 1 entity + 2 feature views**, not the 5 entities/views shown in the
  manual's sample terminal output — that output is from before the driver example files were
  deleted, and the manual's own verification criterion is "1 entity + 2 feature views created".
* **The manual's "150 rows" expectation is inconsistent with its own script.** The verification
  section states that `get_historical_features.py` should produce "a DataFrame with exactly 150
  rows (matching the Experiment 4 dataset size)". In reality the Experiment 4 dataset is **149
  rows** (one exact duplicate record is removed by the preprocess stage), and the manual's own
  Step 7 script calls `.head(5)`, so it retrieves **5** point-in-time-correct rows. The script's
  behaviour is correct; the verification wording is not. All 8 feature columns are fully populated
  for those rows, which is the property the check is really about.
* **Materialization is a scheduled step, not a one-time one.** `materialize-incremental` must be
  re-run to push new feature values into the online store; the online store only ever holds the
  latest value per entity.
* **`event_timestamp` values are synthetic** (`2026-08-15 15:20:02` + 1 minute per row), as
  specified by the manual, because the Iris dataset has no genuine observation timestamps. The
  365-day TTL still covers them for the materialization date used here.
* **Version control.** `features.py`, `feature_store.yaml` and `data/registry.db` (the versioned
  feature metadata) are committed to Git, as is the small prepared Parquet source.
  `data/online_store.db` is git-ignored because it is runtime state fully regenerated by
  `feast materialize-incremental`. The `.venv-feast` environment is ignored; its exact contents are
  recorded in `practical5_feast/requirements-feast.txt` (feast 0.66.0, pandas 2.3.3,
  pyarrow 25.0.1, scikit-learn 1.9.1).
