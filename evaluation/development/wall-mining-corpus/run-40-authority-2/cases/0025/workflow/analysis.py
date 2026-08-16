import os
import pandas as pd
import numpy as np
from scipy import stats

# Read data
df = pd.read_csv('data/input.csv')

# Group data by station type
urban_readings = df[df['station_type'] == 'Urban']['pm25_level']
rural_readings = df[df['station_type'] == 'Rural']['pm25_level']

# Extract values for test
urban_data = urban_readings.values
rural_data = rural_readings.values

# Perform Mann-Whitney U test
statistic, p_value = stats.mannwhitneyu(urban_data, rural_data, alternative='two-sided')

# Calculate descriptive statistics
urban_mean = float(urban_readings.mean())
rural_mean = float(rural_readings.mean())
urban_std = float(urban_readings.std())
rural_std = float(rural_readings.std())

# Write report
conclusion_type = "Statistically significant difference" if p_value < 0.05 else "No statistically significant difference"

report = f"""# Air Quality Analysis Report

## Summary
Analysis comparing PM2.5 levels between urban and rural monitoring stations.

### Urban Stations
- Mean: {urban_mean:.2f} µg/m³
- Std Dev: {urban_std:.2f}
- N: {len(urban_data)}

### Rural Stations
- Mean: {rural_mean:.2f} µg/m³
- Std Dev: {rural_std:.2f}
- N: {len(rural_data)}

## Statistical Test
Mann-Whitney U Test (non-parametric comparison of two independent groups)
- Test Statistic: {statistic:.2f}
- P-value: {p_value:.4f}

## Conclusion
{conclusion_type} detected between urban and rural PM2.5 levels (p = {p_value:.4f}).
"""

# Ensure results directory exists
os.makedirs('results', exist_ok=True)

# Write report
with open('results/report.md', 'w') as f:
    f.write(report)