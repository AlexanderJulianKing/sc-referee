import csv
from pathlib import Path
from scipy import stats
import statistics

data_path = Path('data/input.csv')
results_path = Path('results/report.md')
results_path.parent.mkdir(parents=True, exist_ok=True)

samples = []
with open(data_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        samples.append({
            'region': row['region'],
            'depth': int(row['depth']),
            'ph': float(row['ph'])
        })

by_region = {}
for sample in samples:
    region = sample['region']
    by_region.setdefault(region, []).append(sample['ph'])

stats_by_region = {}
for region, values in by_region.items():
    stats_by_region[region] = {
        'count': len(values),
        'mean': statistics.mean(values),
        'stdev': statistics.stdev(values) if len(values) > 1 else 0.0,
        'median': statistics.median(values),
        'min': min(values),
        'max': max(values)
    }

regions = sorted(by_region.keys())
if len(regions) > 2:
    f_stat, p_val = stats.f_oneway(*[by_region[r] for r in regions])
    test_name = "One-way ANOVA"
else:
    f_stat, p_val = stats.ttest_ind(by_region[regions[0]], by_region[regions[1]])
    test_name = "Independent t-test"

report = "# Soil pH Analysis\n\n"
report += f"## Summary\n\nAnalysis of {len(samples)} soil pH measurements across {len(regions)} regions.\n\n"

report += "## Regional Statistics\n\n"
report += "| Region | N | Mean | StdDev | Median | Min | Max |\n"
report += "|--------|---|------|--------|--------|-----|-----|\n"
for region in regions:
    s = stats_by_region[region]
    report += f"| {region} | {s['count']} | {s['mean']:.2f} | {s['stdev']:.2f} | {s['median']:.2f} | {s['min']:.2f} | {s['max']:.2f} |\n"

report += f"\n## Statistical Comparison\n\n{test_name} results:\n\n"
report += f"- Test statistic: {f_stat:.4f}\n"
report += f"- P-value: {p_val:.4f}\n"

if p_val < 0.05:
    report += f"\n**Significant difference detected** (p < 0.05) in pH across regions.\n"
else:
    report += f"\n**No significant difference** (p ≥ 0.05) in pH across regions.\n"

with open(results_path, 'w') as f:
    f.write(report)