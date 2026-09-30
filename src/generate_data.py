# scripts/generate_data.py 
import pandas as pd 
from sklearn.datasets import load_iris 
 
iris = load_iris(as_frame=True) 
df = iris.frame 
df.to_csv("data/raw/iris_v1.csv", index=False) 
print(f"Saved {len(df)} rows to data/raw/iris_v1.csv")