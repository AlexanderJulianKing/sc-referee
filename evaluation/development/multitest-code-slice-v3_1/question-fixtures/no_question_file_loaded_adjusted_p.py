import pandas as pd

adjusted = pd.read_csv("adjusted.csv")["p_adjusted"]
for p in adjusted:
    print(p < 0.05)
