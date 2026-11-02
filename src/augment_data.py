# src/augment_data.py
import pandas as pd
import numpy as np

df = pd.read_csv("data/raw/iris_v1.csv")
rng = np.random.default_rng(42)
noise = rng.normal(0, 0.05, size=(20, 4))
sample = df.sample(20, random_state=42).reset_index(drop=True)
sample.iloc[:, :4] = sample.iloc[:, :4].values + noise
augmented = pd.concat([df, sample], ignore_index=True)
augmented.to_csv("data/raw/iris_v1.csv", index=False)
print(f"Dataset now has {len(augmented)} rows")
