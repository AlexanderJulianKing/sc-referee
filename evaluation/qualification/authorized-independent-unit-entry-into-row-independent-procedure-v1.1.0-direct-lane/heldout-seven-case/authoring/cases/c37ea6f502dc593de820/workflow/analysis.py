import csv
from pathlib import Path
import scipy.stats as st
rows = list(csv.DictReader(Path("inputs/data.csv").read_text(encoding="utf-8").splitlines()))
staged = rows
left = [float(row["a"]) for row in staged]
right = [float(row["b"]) for row in staged]
result = st.mannwhitneyu(left, right)
Path("results/report.md").write_text(f"[selected-result] {result}\n", encoding="utf-8")
