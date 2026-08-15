import csv
import pathlib
from statistics import mean
from scipy import stats

data_path = pathlib.Path("data") / "input.csv"
report_path = pathlib.Path("results") / "report.md"
report_path.parent.mkdir(exist_ok=True)

samples = []
with open(data_path) as f:
    for row in csv.DictReader(f):
        samples.append({
            'field': row['field_id'],
            'N': float(row['nitrogen_ppm']),
            'P': float(row['phosphorus_ppm']),
            'K': float(row['potassium_ppm']),
            'pH': float(row['soil_pH']),
            'OM': float(row['organic_matter_pct'])
        })

by_field = {}
for s in samples:
    if s['field'] not in by_field:
        by_field[s['field']] = []
    by_field[s['field']].append(s)

field_stats = {}
for field, field_samples in by_field.items():
    field_stats[field] = {
        'N': mean(x['N'] for x in field_samples),
        'P': mean(x['P'] for x in field_samples),
        'K': mean(x['K'] for x in field_samples),
        'pH': mean(x['pH'] for x in field_samples),
        'OM': mean(x['OM'] for x in field_samples),
        'n': len(field_samples)
    }

deficient = {}
for field, stats_d in field_stats.items():
    issues = []
    if stats_d['N'] < 30:
        issues.append(f"N ({stats_d['N']:.1f}ppm)")
    if stats_d['P'] < 15:
        issues.append(f"P ({stats_d['P']:.1f}ppm)")
    if stats_d['K'] < 150:
        issues.append(f"K ({stats_d['K']:.1f}ppm)")
    if issues:
        deficient[field] = issues

all_N = [s['N'] for s in samples]
all_P = [s['P'] for s in samples]
all_K = [s['K'] for s in samples]
all_pH = [s['pH'] for s in samples]
all_OM = [s['OM'] for s in samples]

r_NP, p_NP = stats.pearsonr(all_N, all_P)
r_NK, p_NK = stats.pearsonr(all_N, all_K)
r_pH_OM, p_pH_OM = stats.pearsonr(all_pH, all_OM)

report = f"""# Soil Fertility Analysis

## Executive Summary

Analyzed {len(samples)} soil samples from {len(field_stats)} fields to assess nutrient availability and soil health indicators.

## Field Results

"""

for field in sorted(field_stats.keys()):
    s = field_stats[field]
    report += f"### {field} (n={s['n']})\n"
    report += f"- Nitrogen: {s['N']:.1f} ppm\n"
    report += f"- Phosphorus: {s['P']:.1f} ppm\n"
    report += f"- Potassium: {s['K']:.1f} ppm\n"
    report += f"- pH: {s['pH']:.2f}\n"
    report += f"- Organic matter: {s['OM']:.2f}%\n\n"

if deficient:
    report += "## Nutrient Deficiencies\n\n"
    for field in sorted(deficient.keys()):
        report += f"{field}: {', '.join(deficient[field])}\n"
    report += "\n"

report += f"""## Correlations

- N-P: r={r_NP:.3f}, p={p_NP:.4f}
- N-K: r={r_NK:.3f}, p={p_NK:.4f}
- pH-OM: r={r_pH_OM:.3f}, p={p_pH_OM:.4f}

## Management Recommendations

Deficient fields require targeted fertilizer applications. Maintain pH 6.0-7.0 and build organic matter through residue incorporation. Monitor annually.

## Methods

Standard soil test. Deficiency thresholds: N<30, P<15, K<150 ppm. Correlations via Pearson.
"""

with open(report_path, 'w') as f:
    f.write(report)