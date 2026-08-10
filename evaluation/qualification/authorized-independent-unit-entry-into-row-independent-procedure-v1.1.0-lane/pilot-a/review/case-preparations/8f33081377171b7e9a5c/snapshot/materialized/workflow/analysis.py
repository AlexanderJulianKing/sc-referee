import csv
from pathlib import Path
from scipy.stats import ttest_ind

rows = list(csv.DictReader(Path("inputs/data.csv").read_text(encoding="utf-8").splitlines()))
left = [float(row["a"]) for row in rows]
right = [float(row["b"]) for row in rows]
result = ttest_ind(left, right)
Path("results/report.md").write_text(f"[selected-result] {result}\n", encoding="utf-8")
