import pandas as pd
from scipy import stats

df = pd.read_csv('data/input.csv')

traditional_branches = df[df['pruning_method'] == 'traditional']['fruit_bearing_branches'].values
experimental_branches = df[df['pruning_method'] == 'experimental']['fruit_bearing_branches'].values

t_stat, p_value = stats.ttest_ind(traditional_branches, experimental_branches)

trad_mean = traditional_branches.mean()
trad_std = traditional_branches.std(ddof=1)
trad_n = len(traditional_branches)

exp_mean = experimental_branches.mean()
exp_std = experimental_branches.std(ddof=1)
exp_n = len(experimental_branches)

sig_string = "statistically significant" if p_value < 0.05 else "not statistically significant"
direction = "higher" if exp_mean > trad_mean else "lower" if exp_mean < trad_mean else "similar"

report_text = f"""# Fruit-Bearing Branch Productivity Analysis

## Study Design
This analysis compares the number of fruit-bearing branches on apple trees using two different pruning methods. Trees were randomly assigned to either a traditional hand-pruning method or an experimental machine-assisted pruning method.

## Descriptive Statistics

| Pruning Method | Mean | Std Dev | N |
|---|---|---|---|
| Traditional | {trad_mean:.2f} | {trad_std:.2f} | {trad_n} |
| Experimental | {exp_mean:.2f} | {exp_std:.2f} | {exp_n} |

## Statistical Test
An independent samples t-test was used to test whether the mean number of fruit-bearing branches differs between the two pruning methods.

- t-statistic: {t_stat:.4f}
- p-value: {p_value:.4f}
- Significance level: α = 0.05

## Findings
The independent samples t-test revealed that the difference in mean fruit-bearing branch counts between the traditional and experimental pruning methods was {sig_string} (p = {p_value:.4f}). The experimental method resulted in a {direction} mean productivity compared to the traditional approach.
"""

with open('results/report.md', 'w') as f:
    f.write(report_text)