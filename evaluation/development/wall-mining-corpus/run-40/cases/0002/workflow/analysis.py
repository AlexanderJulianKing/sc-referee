import csv
from pathlib import Path
from statistics import mean, stdev
from scipy import stats

data_path = Path("data") / "input.csv"
report_path = Path("results") / "report.md"
Path("results").mkdir(exist_ok=True)

# Load and organize measurements by treatment
treatment_heights = {}
with open(data_path) as f:
    for row in csv.DictReader(f):
        treatment = row["treatment"]
        height = float(row["height_cm"])
        if treatment not in treatment_heights:
            treatment_heights[treatment] = []
        treatment_heights[treatment].append(height)

# Calculate statistics for each treatment
summary = {}
for treatment in sorted(treatment_heights.keys()):
    heights = treatment_heights[treatment]
    summary[treatment] = {
        "mean": mean(heights),
        "stdev": stdev(heights) if len(heights) > 1 else 0,
        "n": len(heights)
    }

# Run one-way ANOVA
groups = [treatment_heights[t] for t in sorted(treatment_heights.keys())]
f_stat, p_val = stats.f_oneway(*groups)

# Generate report
report = "# Plant Growth Analysis Under Different Lighting\n\n"
report += "## Summary Statistics by Treatment\n\n"

for treatment in sorted(summary.keys()):
    s = summary[treatment]
    report += f"### {treatment.replace('_', ' ').title()}\n"
    report += f"- Mean height: {s['mean']:.2f} cm\n"
    report += f"- Standard deviation: {s['stdev']:.2f} cm\n"
    report += f"- Sample size: {s['n']}\n\n"

report += "## Statistical Analysis\n\n"
report += "### One-Way ANOVA\n\n"
report += f"- F-statistic: {f_stat:.4f}\n"
report += f"- p-value: {p_val:.6f}\n\n"

if p_val < 0.05:
    report += "**Finding**: Significant differences in plant height across light treatments (p < 0.05).\n"
else:
    report += "**Finding**: No significant differences in plant height across light treatments.\n"

with open(report_path, "w") as f:
    f.write(report)