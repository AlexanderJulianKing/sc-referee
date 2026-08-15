from pathlib import Path
import csv
from statistics import mean, stdev
from scipy import stats

input_path = Path("data/input.csv")
output_path = Path("results/report.md")

data = []
with open(input_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append({
            'site': row['site_id'],
            'date': row['date'],
            'pH': float(row['pH']),
            'DO': float(row['dissolved_oxygen_mg_L']),
            'turbidity': float(row['turbidity_NTU']),
            'temp': float(row['temperature_C'])
        })

sites = {}
for record in data:
    site = record['site']
    if site not in sites:
        sites[site] = {'pH': [], 'DO': [], 'turbidity': [], 'temp': []}
    sites[site]['pH'].append(record['pH'])
    sites[site]['DO'].append(record['DO'])
    sites[site]['turbidity'].append(record['turbidity'])
    sites[site]['temp'].append(record['temp'])

site_stats = {}
for site, measurements in sites.items():
    site_stats[site] = {}
    for param in ['pH', 'DO', 'turbidity', 'temp']:
        values = measurements[param]
        site_stats[site][param] = {
            'mean': mean(values),
            'stdev': stdev(values) if len(values) > 1 else 0.0,
            'min': min(values),
            'max': max(values)
        }

params = ['pH', 'DO', 'turbidity', 'temp']
correlations = {}
for i, p1 in enumerate(params):
    for p2 in params[i+1:]:
        v1 = [d[p1] for d in data]
        v2 = [d[p2] for d in data]
        r, pval = stats.pearsonr(v1, v2)
        correlations[f"{p1}-{p2}"] = (r, pval)

lines = [
    "# Water Quality Assessment Report",
    "",
    "## Executive Summary",
    f"Analyzed {len(data)} water samples from {len(sites)} monitoring stations over 3 months.",
    "",
    "## Measurements by Site",
    ""
]

for site in sorted(site_stats.keys()):
    lines.append(f"### {site}")
    lines.append("")
    lines.append("| Parameter | Mean | Std Dev | Range |")
    lines.append("|-----------|------|---------|-------|")
    for param in params:
        m = site_stats[site][param]['mean']
        s = site_stats[site][param]['stdev']
        mn = site_stats[site][param]['min']
        mx = site_stats[site][param]['max']
        lines.append(f"| {param} | {m:.2f} | {s:.2f} | {mn:.2f}–{mx:.2f} |")
    lines.append("")

lines.append("## Parameter Correlations")
lines.append("")
lines.append("| Variable Pair | Pearson r | P-value | Strength |")
lines.append("|---------------|-----------|---------|----------|")
for pair in sorted(correlations.keys()):
    r, pval = correlations[pair]
    if pval < 0.05:
        strength = "Significant" if abs(r) > 0.5 else "Weak sig."
    else:
        strength = "Weak"
    lines.append(f"| {pair} | {r:.3f} | {pval:.4f} | {strength} |")
lines.append("")

lines.append("## Water Quality Interpretation")
lines.append("")

all_do = [d['DO'] for d in data]
do_avg = mean(all_do)
all_turb = [d['turbidity'] for d in data]
turb_avg = mean(all_turb)

for site in sorted(site_stats.keys()):
    site_do = site_stats[site]['DO']['mean']
    site_turb = site_stats[site]['turbidity']['mean']
    
    if site_do < do_avg - stdev(all_do) * 0.3:
        lines.append(f"- **{site}**: Oxygen stress detected (DO {site_do:.2f} mg/L)")
    if site_turb > turb_avg + stdev(all_turb) * 0.3:
        lines.append(f"- **{site}**: Elevated turbidity ({site_turb:.2f} NTU)")

report = "\n".join(lines)

output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, 'w') as f:
    f.write(report)