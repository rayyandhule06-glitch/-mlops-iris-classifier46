# get_online_features.py
"""Step 6: retrieve the latest feature values for a single entity from the
online store (the low-latency serving path)."""
import pandas as pd
from feast import FeatureStore

FEATURES = [
    "iris_measurements:sepal length (cm)",
    "iris_measurements:sepal width (cm)",
    "iris_measurements:petal length (cm)",
    "iris_measurements:petal width (cm)",
    "iris_engineered_features:sepal_area",
    "iris_engineered_features:petal_area",
    "iris_engineered_features:sepal_to_petal_length_ratio",
    "iris_engineered_features:petal_length_bin",
]

print("=" * 60)
print("FEAST ONLINE FEATURE RETRIEVAL TEST")
print("=" * 60)

store = FeatureStore(repo_path=".")

result = store.get_online_features(
    features=FEATURES,

    entity_rows=[
        {"sample_id": 1}
    ],
)

result_dict = result.to_dict()

result_df = pd.DataFrame(result_dict)

print("\nFeatures retrieved for sample_id = 1:")
print(result_df.to_string(index=False))

# ------------------------------------------------------------------
# Additional verification: every requested feature key must be
# populated (no None values) for sample_id 0, 1 and 2.
# ------------------------------------------------------------------
multi_dict = store.get_online_features(
    features=FEATURES,
    entity_rows=[
        {"sample_id": 0},
        {"sample_id": 1},
        {"sample_id": 2},
    ],
).to_dict()

null_keys = [k for k, values in multi_dict.items() if any(v is None for v in values)]

print("\nNull-value check for sample_id 0, 1 and 2:")
print("  entity ids:", multi_dict["sample_id"])
print("  keys with null values:", null_keys if null_keys else "NONE - all requested features populated")
