import numpy as np
import pandas as pd
from scipy import stats
import os

df = pd.read_csv('data/input.csv')

required_columns = ['site', 'dissolved_oxygen']
for col in required_columns:
    assert col in df.columns, f"Missing column: {col}"

df_clean = df[df['dissolved_oxygen'].notna()].copy()
assert len(df_clean) > 0, "No valid measurements found"

upstream_do = df_clean[df_clean['site'] == 'Upstream']['dissolved_oxygen'].values
downstream_do = df_clean[df_clean['site'] == 'Downstream']['dissolved_oxygen'].values

assert len(upstream_do) > 0, "No upstream measurements"
assert len(downstream_do) > 0, "No downstream measurements"

statistic, p_value = stats.mannwhitneyu(upstream_do, downstream_do)

upstream_mean = np.mean(upstream_do)
upstream_median = np.median(upstream_do)
upstream_std = np.std(upstream_do, ddof=1)
downstream_mean = np.mean(downstream_do)
downstream_median = np.median(downstream_do)
downstream_std = np.std(downstream_do, ddof=1)

os.makedirs('results', exist_ok=True)

report = f"""# River Dissolved Oxygen Comparison Study

## Background
Dissolved oxygen (DO) levels are a critical indicator of aquatic ecosystem health. This analysis compares DO concentrations between an upstream reference station and a downstream monitoring location on a river system.

## Sample Description
**Upstream Station (Reference):**
- Sample size: {len(upstream_do)}
- Mean DO: {upstream_mean:.2f} mg/L
- Median DO: {upstream_median:.2f} mg/L
- SD: {upstream_std:.2f} mg/L

**Downstream Station (Test):**
- Sample size: {len(downstream_do)}
- Mean DO: {downstream_mean:.2f} mg/L
- Median DO: {downstream_median:.2f} mg/L
- SD: {downstream_std:.2f} mg/L

## Statistical Analysis
Mann-Whitney U test was applied to compare median dissolved oxygen concentrations between sites (non-parametric approach suitable for environmental data).

**Test Results:**
- U-statistic: {statistic:.1f}
- p-value: {p_value:.6f}
- Significance level: α = 0.05

## Interpretation
"""

if p_value < 0.05:
    if upstream_mean > downstream_mean:
        report += f"The upstream reference site exhibits significantly higher dissolved oxygen levels than the downstream site (p = {p_value:.6f}). This difference suggests potential oxygen depletion downstream, possibly due to biological oxygen demand or anthropogenic inputs."
    else:
        report += f"The downstream site unexpectedly shows significantly higher dissolved oxygen levels (p = {p_value:.6f}). This may indicate improved conditions or specific hydrodynamic factors."
else:
    report += f"No statistically significant difference in dissolved oxygen concentrations was detected between sites (p = {p_value:.6f}). The observed difference is consistent with natural variation."

report += "\n\n## Recommendations\nContinue regular monitoring to track temporal trends in water quality conditions."

with open('results/report.md', 'w') as f:
    f.write(report)
