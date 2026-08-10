import csv
from pathlib import Path
from scipy.stats import mannwhitneyu

rows = list(csv.DictReader(Path("inputs/data.csv").read_text(encoding="utf-8").splitlines()))
left = [float(row["a"]) for row in rows]
right = [float(row["b"]) for row in rows]
result = mannwhitneyu(left, right)
Path("results/report.md").write_text(f"[selected-result] {result}\n", encoding="utf-8")
