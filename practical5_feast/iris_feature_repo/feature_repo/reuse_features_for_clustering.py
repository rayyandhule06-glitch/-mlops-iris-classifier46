# reuse_features_for_clustering.py
"""Demonstrates a completely different model (unsupervised clustering)
reusing the SAME registered engineered features without re-deriving them.
"""
import pandas as pd
from feast import FeatureStore

print("=" * 60)
print("FEAST FEATURE SERVICE TEST")
print("=" * 60)

store = FeatureStore(repo_path=".")

feature_service = store.get_feature_service(
    "iris_feature_service")

result = store.get_online_features(
    features=feature_service,
    entity_rows=[{"sample_id": 1}],
)

print("\nFeatures retrieved using Feature Service:")
print(result.to_dict())

# ------------------------------------------------------------------
# Reuse the very same feature service to train a structurally different
# model: unsupervised KMeans clustering over ALL samples, using only the
# features the feature store already serves. Nothing is re-derived here.
# ------------------------------------------------------------------
from sklearn.cluster import KMeans

source_df = pd.read_parquet("data/iris_features.parquet")
entity_rows = [{"sample_id": int(sid)} for sid in source_df["sample_id"]]

all_features = store.get_online_features(
    features=feature_service,
    entity_rows=entity_rows,
).to_df()

print(
    f"\nFeature Service reused for clustering: "
    f"retrieved {len(all_features)} rows x {all_features.shape[1] - 1} feature columns"
)

# Numeric feature columns only -- petal_length_bin is categorical and is not
# part of the Euclidean distance metric.
cluster_cols = [
    "sepal length (cm)",
    "sepal width (cm)",
    "petal length (cm)",
    "petal width (cm)",
    "sepal_area",
    "petal_area",
    "sepal_to_petal_length_ratio",
]
X = all_features[cluster_cols].astype("float64").values

kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
all_features["cluster"] = kmeans.fit_predict(X)

print("\nKMeans (k=3) cluster counts:")
for cluster_id, count in all_features["cluster"].value_counts().sort_index().items():
    print(f"  cluster {cluster_id}: {count} samples")

# Sanity check: how do the discovered clusters line up with the real species?
labelled = all_features[["sample_id", "cluster"]].merge(
    source_df[["sample_id", "species"]], on="sample_id"
)
print("\nCluster vs. actual species:")
print(pd.crosstab(labelled["cluster"], labelled["species"]).to_string())
