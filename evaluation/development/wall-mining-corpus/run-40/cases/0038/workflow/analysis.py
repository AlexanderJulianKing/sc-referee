from pathlib import Path
import csv
from statistics import mean, stdev
from scipy import stats

data_path = Path("data/input.csv")
results_path = Path("results/report.md")
results_path.parent.mkdir(parents=True, exist_ok=True)

measurements = []
with open(data_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        measurements.append({
            'location': row['location'],
            'date': row['date'],
            'depth_m': float(row['depth_m']),
            'temperature_c': float(row['temperature_c']),
            'ph': float(row['ph']),
            'dissolved_oxygen_mg_l': float(row['dissolved_oxygen_mg_l']),
            'conductivity_us_cm': float(row['conductivity_us_cm'])
        })

locations = {}
for m in measurements:
    loc = m['location']
    if loc not in locations:
        locations[loc] = []
    locations[loc].append(m)

location_stats = {}
for loc, data in locations.items():
    temps = [m['temperature_c'] for m in data]
    dos = [m['dissolved_oxygen_mg_l'] for m in data]
    phs = [m['ph'] for m in data]
    conds = [m['conductivity_us_cm'] for m in data]
    
    location_stats[loc] = {
        'count': len(data),
        'temp_mean': mean(temps),
        'temp_std': stdev(temps) if len(temps) > 1 else 0,
        'do_mean': mean(dos),
        'do_std': stdev(dos) if len(dos) > 1 else 0,
        'ph_mean': mean(phs),
        'ph_std': stdev(phs) if len(phs) > 1 else 0,
        'cond_mean': mean(conds),
        'cond_std': stdev(conds) if len(conds) > 1 else 0,
    }

params = ['temperature_c', 'ph', 'dissolved_oxygen_mg_l', 'conductivity_us_cm']
param_data = {p: [m[p] for m in measurements] for p in params}

correlations = {}
for i, p1 in enumerate(params):
    for p2 in params[i+1:]:
        data1 = param_data[p1]
        data2 = param_data[p2]
        corr, p_value = stats.pearsonr(data1, data2)
        correlations[f"{p1} vs {p2}"] = {'r': corr, 'p': p_value}

anomalies = []
for param in params:
    data = param_data[param]
    m = mean(data)
    s = stdev(data) if len(data) > 1 else 1
    
    for i, measurement in enumerate(measurements):
        z_score = (measurement[param] - m) / s if s > 0 else 0
        if abs(z_score) > 2.5:
            anomalies.append({
                'location': measurement['location'],
                'date': measurement['date'],
                'parameter': param,
                'value': measurement[param],
                'z_score': z_score
            })

report = []
report.append("# Water Quality Monitoring Analysis Report\n\n")
report.append(f"**Analysis Date:** 2026-08-15\n")
report.append(f"**Total Measurements:** {len(measurements)}\n")
report.append(f"**Sampling Locations:** {len(locations)}\n\n")

report.append("## Summary Statistics by Location\n\n")
for loc in sorted(locations.keys()):
    stats_loc = location_stats[loc]
    report.append(f"### {loc}\n\n")
    report.append(f"- Samples: {stats_loc['count']}\n")
    report.append(f"- Temperature: {stats_loc['temp_mean']:.2f} ± {stats_loc['temp_std']:.2f} °C\n")
    report.append(f"- pH: {stats_loc['ph_mean']:.2f} ± {stats_loc['ph_std']:.2f}\n")
    report.append(f"- Dissolved Oxygen: {stats_loc['do_mean']:.2f} ± {stats_loc['do_std']:.2f} mg/L\n")
    report.append(f"- Conductivity: {stats_loc['cond_mean']:.1f} ± {stats_loc['cond_std']:.1f} µS/cm\n\n")

report.append("## Correlation Analysis\n\n")
report.append("Pearson correlation coefficients between parameters:\n\n")
for pair, stats_pair in sorted(correlations.items()):
    r = stats_pair['r']
    p = stats_pair['p']
    sig = "**" if p < 0.05 else ""
    report.append(f"- {pair}: {sig}r = {r:.3f}{sig} (p = {p:.4f})\n")

report.append("\n## Anomaly Detection\n\n")
if anomalies:
    report.append(f"Detected {len(anomalies)} anomalous reading(s) (|z-score| > 2.5):\n\n")
    for anom in anomalies:
        report.append(f"- {anom['location']} on {anom['date']}: {anom['parameter']} = {anom['value']:.2f} (z = {anom['z_score']:.2f})\n")
else:
    report.append("No anomalous readings detected.\n")

report.append("\n## Quality Assessment\n\n")
report.append("Water quality assessment based on standard thresholds:\n\n")
for loc in sorted(locations.keys()):
    stats_loc = location_stats[loc]
    issues = []
    
    if stats_loc['do_mean'] < 5:
        issues.append("Low dissolved oxygen")
    if stats_loc['ph_mean'] < 6.5 or stats_loc['ph_mean'] > 8.5:
        issues.append("pH outside optimal range")
    
    if issues:
        report.append(f"- **{loc}:** {'; '.join(issues)}\n")
    else:
        report.append(f"- **{loc}:** Within acceptable ranges\n")

with open(results_path, 'w') as f:
    f.write(''.join(report))

print(f"Report written to {results_path}")