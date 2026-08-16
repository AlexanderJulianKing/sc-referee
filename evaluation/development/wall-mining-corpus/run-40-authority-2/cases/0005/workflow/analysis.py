import csv
from pathlib import Path
from scipy import stats

data_file = Path("data/input.csv")
output_dir = Path("results")

full_sun = []
partial_shade = []

with open(data_file) as f:
    reader = csv.DictReader(f)
    for row in reader:
        height = float(row["height_cm"])
        condition = row["condition"].strip()
        if condition == "full_sun":
            full_sun.append(height)
        else:
            partial_shade.append(height)

t_stat, p_val = stats.ttest_ind(full_sun, partial_shade)

mean_full = sum(full_sun) / len(full_sun)
mean_shade = sum(partial_shade) / len(partial_shade)
std_full = (sum((x - mean_full) ** 2 for x in full_sun) / len(full_sun)) ** 0.5
std_shade = (sum((x - mean_shade) ** 2 for x in partial_shade) / len(partial_shade)) ** 0.5

output_dir.mkdir(parents=True, exist_ok=True)

report = output_dir / "report.md"
with open(report, "w") as f:
    f.write("# Plant Growth Analysis: Light Condition Effects\n\n")
    f.write("## Overview\n")
    f.write("This experiment compared tomato seedling heights under two light conditions over an 8-week growing period.\n\n")
    f.write("## Methods\n")
    f.write(f"- Full sun group: n = {len(full_sun)}\n")
    f.write(f"- Partial shade group: n = {len(partial_shade)}\n")
    f.write("- Outcome: Plant height in centimeters\n\n")
    f.write("## Results\n\n")
    f.write("### Summary Statistics\n\n")
    f.write("| Treatment | Mean (cm) | Std Dev (cm) | Sample Size |\n")
    f.write("|-----------|-----------|--------------|-------------|\n")
    f.write(f"| Full Sun | {mean_full:.2f} | {std_full:.2f} | {len(full_sun)} |\n")
    f.write(f"| Partial Shade | {mean_shade:.2f} | {std_shade:.2f} | {len(partial_shade)} |\n\n")
    f.write("### Statistical Comparison\n\n")
    f.write("Independent samples t-test results:\n\n")
    f.write(f"- t-statistic = {t_stat:.4f}\n")
    f.write(f"- p-value = {p_val:.6f}\n\n")
    f.write("## Interpretation\n")
    if p_val < 0.05:
        f.write(f"A statistically significant difference was found (p < 0.05). ")
        f.write(f"Full sun seedlings were {mean_full - mean_shade:.1f} cm taller on average.\n")
    else:
        f.write(f"No significant difference was detected between treatment groups (p = {p_val:.4f}).\n")