import csv
from pathlib import Path
from scipy import stats
from statistics import mean, stdev

data_file = Path("data/input.csv")
results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

batches = {}
with open(data_file) as f:
    reader = csv.DictReader(f)
    for row in reader:
        batch_id = row['batch_id']
        hardness = float(row['hardness_value'])
        if batch_id not in batches:
            batches[batch_id] = []
        batches[batch_id].append(hardness)

batch_stats = {}
for batch_id in sorted(batches.keys()):
    values = batches[batch_id]
    batch_stats[batch_id] = {
        'mean': mean(values),
        'stdev': stdev(values) if len(values) > 1 else 0.0,
        'min': min(values),
        'max': max(values),
        'n': len(values)
    }

lines = ["# Hardness Consistency Analysis Report\n\n"]
lines.append("## Executive Summary\n\n")
total_measurements = sum(len(v) for v in batches.values())
lines.append(f"Analyzed {len(batches)} production batches with {total_measurements} total hardness measurements.\n\n")

lines.append("## Descriptive Statistics by Batch\n\n")
lines.append("| Batch | Mean (HRC) | Stdev | Min | Max | N |\n")
lines.append("|-------|------------|-------|-----|-----|---|\n")
for batch_id in sorted(batches.keys()):
    s = batch_stats[batch_id]
    lines.append(f"| {batch_id} | {s['mean']:.2f} | {s['stdev']:.2f} | {s['min']:.1f} | {s['max']:.1f} | {s['n']} |\n")
lines.append("\n")

lines.append("## Normality Assessment (Shapiro-Wilk Test)\n\n")
lines.append("| Batch | Test Statistic | p-value | Normal (α=0.05)? |\n")
lines.append("|-------|----------------|---------|------------------|\n")
for batch_id in sorted(batches.keys()):
    if len(batches[batch_id]) >= 3:
        w_stat, p_val = stats.shapiro(batches[batch_id])
        is_normal = "Yes" if p_val > 0.05 else "No"
        lines.append(f"| {batch_id} | {w_stat:.4f} | {p_val:.4f} | {is_normal} |\n")
lines.append("\n")

lines.append("## Equality of Variances (Levene's Test)\n\n")
batch_values = [batches[bid] for bid in sorted(batches.keys())]
levene_stat, levene_p = stats.levene(*batch_values)
lines.append(f"**Test Statistic:** {levene_stat:.4f}\n\n")
lines.append(f"**p-value:** {levene_p:.4f}\n\n")
equal_var = "Yes" if levene_p > 0.05 else "No"
lines.append(f"**Equal Variances (α=0.05):** {equal_var}\n\n")

lines.append("## One-Way ANOVA Results\n\n")
f_stat, anova_p = stats.f_oneway(*batch_values)
lines.append(f"**F-statistic:** {f_stat:.4f}\n\n")
lines.append(f"**p-value:** {anova_p:.4f}\n\n")
sig_diff = "Yes" if anova_p < 0.05 else "No"
lines.append(f"**Significant Difference (α=0.05):** {sig_diff}\n\n")

grand_mean = sum(sum(v) for v in batches.values()) / total_measurements
ss_between = sum(batch_stats[bid]['n'] * (batch_stats[bid]['mean'] - grand_mean)**2 
                 for bid in batches.keys())
ss_total = sum((x - grand_mean)**2 for values in batches.values() for x in values)
eta_squared = ss_between / ss_total if ss_total > 0 else 0.0
lines.append(f"**Eta-squared (Effect Size):** {eta_squared:.4f}\n\n")

lines.append("## Interpretation and Conclusions\n\n")
if anova_p < 0.05:
    lines.append("- Hardness values **differ significantly** across production batches.\n")
    if eta_squared < 0.06:
        lines.append("- The effect size is small, indicating statistical significance but modest practical differences.\n")
    elif eta_squared < 0.14:
        lines.append("- The effect size is medium, indicating meaningful production consistency variations.\n")
    else:
        lines.append("- The effect size is large, indicating substantial process control issues.\n")
else:
    lines.append("- No statistically significant hardness difference across batches.\n")

if levene_p < 0.05:
    lines.append("- **Variance heterogeneity detected:** Inconsistent hardness variability suggests process control inconsistencies.\n")

lines.append("\n## Recommendations\n\n")
lines.append("1. Investigate production parameters in high-hardness batches (review temperature and pressure profiles).\n")
lines.append("2. Audit quality control procedures for batches with elevated variance.\n")
lines.append("3. Implement tighter process parameter controls to reduce batch-to-batch variation.\n")
lines.append("4. Increase sampling frequency to detect process drift earlier.\n")

with open(Path("results/report.md"), 'w') as f:
    f.writelines(lines)
