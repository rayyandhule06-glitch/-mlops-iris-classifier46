"""
Prepares the iris_features.csv from Experiment 4 into a Feast-ready
Parquet source with entity IDs and event timestamps.
"""
import pandas as pd
from pathlib import Path

# Repository root (this file lives in
# <repo>/practical5_feast/iris_feature_repo/feature_repo/).
# Resolving from the script's own location keeps the repo portable -- the
# laboratory manual hard-codes C:/Users/Admin/... which breaks on other machines.
repo_root = Path(__file__).resolve().parents[3]

# Input from Practical 4
input_file = repo_root / "data" / "processed" / "iris_features.csv"

# Output for Feast (relative to the feature_repo directory, i.e. data/iris_features.parquet)
output_file = Path(__file__).resolve().parent / "data" / "iris_features.parquet"

# Read feature-engineered data
df = pd.read_csv(input_file)

# Create sample_id
df.insert(0, "sample_id", range(len(df)))

# Create event timestamps
start_time = pd.Timestamp(
    "2026-08-15 15:20:02",
    tz="UTC",
)
df["event_timestamp"] = pd.date_range(
    start=start_time,
    periods=len(df),
    freq="min",
)

# Created timestamp
df["created_timestamp"] = df["event_timestamp"]

# Create output directory
output_file.parent.mkdir(
    parents=True,
    exist_ok=True,
)

# Save as Parquet
df.to_parquet(
    output_file,
    index=False,
)

print(
    f"Wrote {len(df)} rows to {output_file.relative_to(Path(__file__).resolve().parent)}"
)
