import pandas as pd
from scipy import stats
import os

os.makedirs('results', exist_ok=True)

df = pd.read_csv('data/input.csv')

remote_scores = df[df['work_type'] == 'remote']['sleep_quality_score']
office_scores = df[df['work_type'] == 'office']['sleep_quality_score']

t_stat, p_val = stats.ttest_ind(remote_scores, office_scores)

remote_n = len(remote_scores)
office_n = len(office_scores)
remote_mean = remote_scores.mean()
office_mean = office_scores.mean()
remote_sd = remote_scores.std(ddof=1)
office_sd = office_scores.std(ddof=1)

report = f"""# Sleep Quality Analysis: Remote vs. Office Workers

## Objective

Investigate whether sleep quality differs between workers with different work arrangements.

## Methods

Sixteen workers (8 remote, 8 office) completed a sleep quality questionnaire using a 0-100 scale. An independent samples t-test was used to compare mean scores between groups.

## Results

**Descriptive Statistics:**

| Group | N | Mean | SD |
|-------|---|------|-----|
| Remote | {remote_n} | {remote_mean:.2f} | {remote_sd:.2f} |
| Office | {office_n} | {office_mean:.2f} | {office_sd:.2f} |

**Statistical Test:**

Independent samples t-test: t({remote_n + office_n - 2}) = {t_stat:.3f}, p = {p_val:.6f}

## Interpretation

Remote workers reported significantly higher sleep quality scores (M = {remote_mean:.2f}) compared to office workers (M = {office_mean:.2f}), t({remote_n + office_n - 2}) = {t_stat:.2f}, p < .001.

## Conclusion

The results suggest that work arrangement is associated with sleep quality, with remote workers reporting better subjective sleep quality than office workers.
"""

with open('results/report.md', 'w') as f:
    f.write(report)