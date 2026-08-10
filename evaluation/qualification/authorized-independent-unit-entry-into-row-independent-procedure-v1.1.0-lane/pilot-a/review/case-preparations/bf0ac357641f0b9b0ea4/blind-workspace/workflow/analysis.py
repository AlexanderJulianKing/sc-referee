import csv
from pathlib import Path
from scipy.stats import ttest_rel

rows = list(csv.DictReader(Path("inputs/data.csv").open(newline="", encoding="utf-8")))
left = [float(row["a"]) for row in rows]
right = [float(row["b"]) for row in rows]
result = ttest_rel(left, right)
Path("results/report.md").write_text(f"[selected-result] {result}\n", encoding="utf-8")
