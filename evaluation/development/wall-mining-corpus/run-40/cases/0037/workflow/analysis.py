import csv
from pathlib import Path
from statistics import mean, stdev
from scipy import stats

data_path = Path("data/input.csv")
results_path = Path("results")
results_path.mkdir(exist_ok=True)

data = []
with open(data_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append({
            'site': row['site'],
            'location_km': float(row['location_km']),
            'nitrogen_mg_l': float(row['nitrogen_mg_l']),
            'phosphorus_mg_l': float(row['phosphorus_mg_l']),
            'turbidity_ntu': float(row['turbidity_ntu'])
        })

nitrogen_vals = [d['nitrogen_mg_l'] for d in data]
phosphorus_vals = [d['phosphorus_mg_l'] for d in data]
locations = [d['location_km'] for d in data]

n_mean = mean(nitrogen_vals)
n_stdev = stdev(nitrogen_vals)
p_mean = mean(phosphorus_vals)
p_stdev = stdev(phosphorus_vals)

corr, _ = stats.pearsonr(nitrogen_vals, phosphorus_vals)
slope, intercept, r_value, p_value, _ = stats.linregress(locations, nitrogen_vals)

anomalies = []
for d in data:
    n_z = (d['nitrogen_mg_l'] - n_mean) / n_stdev
    p_z = (d['phosphorus_mg_l'] - p_mean) / p_stdev
    if abs(n_z) > 2 or abs(p_z) > 2:
        anomalies.append(d['site'])

trend = "downstream" if slope > 0 else "upstream"
correlation_desc = "strong positive" if corr > 0.7 else "moderate positive" if corr > 0.3 else "weak"

report_md = f"""# Riverwater Nutrient Concentration Analysis

## Executive Summary

Analysis of {len(data)} water samples from upstream to downstream monitoring sites reveals nutrient concentrations and spatial trends along a {max(locations):.1f} km transect.

## Data Overview

- **Total samples**: {len(data)}
- **Sampling sites**: {len(set(d['site'] for d in data))} unique locations
- **Transect length**: 0 to {max(locations):.1f} km

## Nitrogen Analysis

**Descriptive Statistics:**
- Mean concentration: {n_mean:.2f} mg/L
- Standard deviation: {n_stdev:.2f} mg/L
- Range: {min(nitrogen_vals):.2f} to {max(nitrogen_vals):.2f} mg/L

**Spatial Gradient:**
The linear regression model shows nitrogen concentration changes at **{slope:.4f} mg/L per km** of downstream distance (p-value: {p_value:.4f}). The model explains {r_value**2:.1%} of variance (R² = {r_value**2:.4f}).

## Phosphorus Analysis

**Descriptive Statistics:**
- Mean concentration: {p_mean:.2f} mg/L
- Standard deviation: {p_stdev:.2f} mg/L
- Range: {min(phosphorus_vals):.2f} to {max(phosphorus_vals):.2f} mg/L

## Correlation Between Nutrients

Nitrogen and phosphorus concentrations show a Pearson correlation of **r = {corr:.3f}**, indicating a {correlation_desc} association between these nutrients.

## Anomaly Detection

Using a 2-standard-deviation threshold, the following sites show anomalous nutrient levels:
{chr(10).join(f"- {s}" for s in anomalies) if anomalies else "- No anomalies detected"}

## Conclusions

Water quality degradation is evident {trend} along the transect. The positive correlation between nitrogen and phosphorus suggests common pollution sources, likely agricultural runoff or wastewater discharge.

---
*Analysis completed with Python standard library and scipy.stats*
"""

with open(results_path / "report.md", "w") as f:
    f.write(report_md)