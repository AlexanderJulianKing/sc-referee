import csv
from pathlib import Path
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression, RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

rows = list(csv.DictReader(Path("inputs/data.csv").read_text(encoding="utf-8").splitlines()))
first = [float(row["s1"]) for row in rows]
second = [float(row["s2"]) for row in rows]
features = np.column_stack([first, second])
levels = [int(row["level"]) for row in rows]
anchor = [float(row["anchor"]) for row in rows]
outcome = [float(row["y"]) for row in rows]
sorter = LogisticRegression(max_iter=1000).fit(features, levels)
shares = sorter.predict_proba(features)
label = sorter.predict(features)
mean = shares @ np.array([0.0, 1.0, 2.0])
scale = RidgeCV().fit(features, anchor)
reading = scale.predict(features)
stack = make_pipeline(StandardScaler(), RidgeCV()).fit(features, anchor)
wrapped = stack.predict(features)
bounded = np.clip(mean, 0.0, 2.0)
plain = mean
exposure = reading
summary = LinearRegression().fit(np.column_stack([exposure]), outcome)
Path("results/report.md").write_text(
    "[selected-result] %.6f\n" % summary.coef_[0], encoding="utf-8"
)
