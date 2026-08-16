import pandas as pd
import os
from scipy import stats

df = pd.read_csv('data/input.csv')

upstream_oxygen = df[df['site'] == 'upstream']['dissolved_oxygen_mg_L'].dropna()
downstream_oxygen = df[df['site'] == 'downstream']['dissolved_oxygen_mg_L'].dropna()

statistic, p_value = stats.mannwhitneyu(upstream_oxygen, downstream_oxygen, alternative='two-sided')

upstream_stats = {
    'mean': upstream_oxygen.mean(),
    'median': upstream_oxygen.median(),
    'std': upstream_oxygen.std(),
    'n': len(upstream_oxygen)
}

downstream_stats = {
    'mean': downstream_oxygen.mean(),
    'median': downstream_oxygen.median(),
    'std': downstream_oxygen.std(),
    'n': len(downstream_oxygen)
}

difference = downstream_stats['mean'] - upstream_stats['mean']
direction = 'lower' if difference < 0 else 'higher'
interpretation = 'oxygen depletion' if difference < 0 else 'improved conditions'
significance = 'statistically significant (p < 0.05)' if p_value < 0.05 else 'not significant (p ≥ 0.05)'

report = f"""# River Water Quality Analysis: Upstream vs Downstream

## Objective

This study compared dissolved oxygen concentrations between two river sampling sites to evaluate potential water quality impacts from discharge activities. Daily measurements were collected from an upstream reference location and a downstream location over a 10-day monitoring period.

## Sample Overview

- **Total samples:** {len(df)}
- **Upstream samples:** {upstream_stats['n']}
- **Downstream samples:** {downstream_stats['n']}
- **Collection period:** January 15-24, 2026

## Descriptive Statistics

### Upstream Site (Reference)
- Mean DO: {upstream_stats['mean']:.2f} mg/L
- Median DO: {upstream_stats['median']:.2f} mg/L
- Std Dev: {upstream_stats['std']:.2f} mg/L

### Downstream Site
- Mean DO: {downstream_stats['mean']:.2f} mg/L
- Median DO: {downstream_stats['median']:.2f} mg/L
- Std Dev: {downstream_stats['std']:.2f} mg/L

### Difference
Mean difference: {abs(difference):.2f} mg/L ({direction})

## Statistical Analysis

Mann-Whitney U test was selected to compare dissolved oxygen levels, as it is robust to non-normal distributions and appropriate for small sample sizes.

**Test Results:**
- U-statistic: {statistic:.1f}
- p-value: {p_value:.5f}
- Result: {significance}

## Interpretation

The downstream location exhibits {difference:.2f} mg/L {direction} dissolved oxygen compared to the upstream reference site. This difference is {significance}. The observed pattern is consistent with {interpretation} in the downstream area, potentially attributable to organic matter loading or industrial discharge impacts on the aquatic system.

## Conclusion

Continued monitoring is warranted to track temporal trends and assess whether dissolved oxygen concentrations remain below acceptable standards for aquatic life protection.
"""

os.makedirs('results', exist_ok=True)
with open('results/report.md', 'w') as f:
    f.write(report)