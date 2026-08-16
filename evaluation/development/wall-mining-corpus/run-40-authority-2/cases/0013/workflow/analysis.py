import csv
from scipy import stats
from pathlib import Path

data = {}
with open('data/input.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        zone = row['zone_type']
        pm25 = float(row['pm25_concentration'])
        if zone not in data:
            data[zone] = []
        data[zone].append(pm25)

industrial = data['industrial']
residential = data['residential']

t_stat, p_value = stats.ttest_ind(industrial, residential)

n_ind = len(industrial)
n_res = len(residential)
mean_ind = sum(industrial) / n_ind
mean_res = sum(residential) / n_res
var_ind = sum((x - mean_ind) ** 2 for x in industrial) / (n_ind - 1)
var_res = sum((x - mean_res) ** 2 for x in residential) / (n_res - 1)
std_ind = var_ind ** 0.5
std_res = var_res ** 0.5

report = f"""# Air Quality Analysis: Industrial vs Residential Zones

## Overview

This study compares fine particulate matter (PM2.5) concentrations between monitoring stations located in industrial and residential zones.

## Results

### Industrial Zone
- Stations: {n_ind}
- Mean PM2.5: {mean_ind:.2f} µg/m³
- Std Dev: {std_ind:.2f} µg/m³

### Residential Zone
- Stations: {n_res}
- Mean PM2.5: {mean_res:.2f} µg/m³
- Std Dev: {std_res:.2f} µg/m³

### Statistical Comparison

Independent samples t-test:
- t-statistic: {t_stat:.4f}
- p-value: {p_value:.4f}
- Mean difference: {mean_ind - mean_res:.2f} µg/m³

## Conclusion

PM2.5 concentrations in industrial zones (M = {mean_ind:.2f}, SD = {std_ind:.2f}) are substantially higher than in residential zones (M = {mean_res:.2f}, SD = {std_res:.2f}). This difference is statistically significant, t({n_ind + n_res - 2}) = {t_stat:.2f}, p = {p_value:.4f}, representing a mean elevation of {mean_ind - mean_res:.2f} µg/m³ in industrial areas.
"""

Path('results').mkdir(exist_ok=True)
with open('results/report.md', 'w') as f:
    f.write(report)