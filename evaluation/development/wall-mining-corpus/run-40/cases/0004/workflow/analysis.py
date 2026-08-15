import csv
import pathlib
from statistics import mean, stdev
from scipy import stats

data_path = pathlib.Path("data/input.csv")
results_path = pathlib.Path("results")
results_path.mkdir(exist_ok=True)

readings = {}
with open(data_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        station = row['station']
        pm25 = float(row['pm25_micrograms'])
        if station not in readings:
            readings[station] = []
        readings[station].append(pm25)

stats_by_station = {}
for station, values in readings.items():
    stats_by_station[station] = {
        'n': len(values),
        'mean': mean(values),
        'std': stdev(values) if len(values) > 1 else 0,
        'min': min(values),
        'max': max(values)
    }

groups = [values for values in readings.values()]
f_stat, p_value = stats.f_oneway(*groups)

all_values = sum(readings.values(), [])
overall_mean = mean(all_values)

report_lines = [
    "# Urban Air Quality Analysis",
    "",
    "## Summary",
    f"Analyzed PM2.5 concentrations across {len(readings)} monitoring stations over {len(all_values)} measurements.",
    "",
    "## Station Statistics",
    ""
]

for station in sorted(readings.keys()):
    s = stats_by_station[station]
    report_lines.append(f"### {station}")
    report_lines.append(f"- Samples: {s['n']}")
    report_lines.append(f"- Mean PM2.5: {s['mean']:.2f} µg/m³")
    report_lines.append(f"- Std Dev: {s['std']:.2f} µg/m³")
    report_lines.append(f"- Range: {s['min']:.1f} – {s['max']:.1f} µg/m³")
    report_lines.append("")

report_lines.extend([
    "## Statistical Comparison",
    "",
    "### ANOVA Test",
    "Testing whether mean PM2.5 differs significantly across stations.",
    "",
    f"- F-statistic: {f_stat:.4f}",
    f"- p-value: {p_value:.4f}",
])

if p_value < 0.05:
    report_lines.append("- **Conclusion**: Significant difference detected (p < 0.05)")
else:
    report_lines.append("- **Conclusion**: No significant difference detected (p ≥ 0.05)")

report_lines.extend([
    "",
    "## Overall Results",
    f"- Overall mean PM2.5: {overall_mean:.2f} µg/m³",
    f"- Total measurements: {len(all_values)}",
])

with open(results_path / "report.md", "w") as f:
    f.write("\n".join(report_lines))