# Iris Feature Repository (Experiment 5)

A local Feast feature repository built on the Experiment 4 data pipeline output
(`data/processed/iris_features.csv`). It registers the Iris measurements and the engineered
features, serves them from a SQLite online store, and provides point-in-time-correct offline
retrieval for training.

A quick view of what's in this repository's `feature_repo/` directory:

* `feature_store.yaml` contains the local provider setup: file registry (`data/registry.db`) and
  SQLite online store (`data/online_store.db`)
* `features.py` contains the feature definitions: the `sample_id` entity, the `iris_measurements`
  and `iris_engineered_features` feature views, and the `iris_feature_service`
* `.feastignore` stops Feast from importing the helper and consumer scripts as feature definitions
* `prepare_feature_source.py` (Step 3) converts the Experiment 4 CSV into
  `data/iris_features.parquet`, adding `sample_id`, `event_timestamp` and `created_timestamp`
* `get_online_features.py` (Step 6) retrieves the latest feature values from the online store
* `get_historical_features.py` (Step 7) retrieves point-in-time-correct features for training
* `reuse_features_for_clustering.py` (Step 8) reuses the feature service for a KMeans clustering
  model, demonstrating feature reusability
* `data/` contains the prepared Parquet feature source
* `test_workflow.py` is the Feast template's example workflow script

You can run the overall workflow with:

```bash
python prepare_feature_source.py
feast apply
feast materialize-incremental $(date -u +"%Y-%m-%dT%H:%M:%S")
python get_online_features.py
python get_historical_features.py
python reuse_features_for_clustering.py
```

See `docs/FEATURE_STORE_ANALYSIS.md` for the full analysis and the observed results.

## To move from this into a more production ready workflow:
> See more details in [Running Feast in production](https://docs.feast.dev/how-to-guides/running-feast-in-production)

1. First: you should start with a different Feast template, which delegates to a more scalable offline store. 
   - For example, running `feast init -t gcp`
   or `feast init -t aws` or `feast init -t snowflake`. 
   - You can see your options if you run `feast init --help`.
2. `feature_store.yaml` points to a local file as a registry. You'll want to setup a remote file (e.g. in S3/GCS) or a 
SQL registry. See [registry docs](https://docs.feast.dev/getting-started/concepts/registry) for more details. 
3. This example uses a file [offline store](https://docs.feast.dev/getting-started/components/offline-store) 
   to generate training data. It does not scale. We recommend instead using a data warehouse such as BigQuery, 
   Snowflake, Redshift. There is experimental support for Spark as well.
4. Setup CI/CD + dev vs staging vs prod environments to automatically update the registry as you change Feast feature definitions. See [docs](https://docs.feast.dev/how-to-guides/running-feast-in-production#1.-automatically-deploying-changes-to-your-feature-definitions).
5. (optional) Regularly scheduled materialization to power low latency feature retrieval (e.g. via Airflow). See [Batch data ingestion](https://docs.feast.dev/getting-started/concepts/data-ingestion#batch-data-ingestion)
for more details.
6. (optional) Deploy feature server instances with `feast serve` to expose endpoints to retrieve online features.
   - See [Python feature server](https://docs.feast.dev/reference/feature-servers/python-feature-server) for details.
   - Use cases can also directly call the Feast client to fetch features as per [Feature retrieval](https://docs.feast.dev/getting-started/concepts/feature-retrieval)