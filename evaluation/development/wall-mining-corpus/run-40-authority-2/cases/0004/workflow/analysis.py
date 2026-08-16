import pandas as pd
from scipy import stats
import os

os.makedirs('results', exist_ok=True)

df = pd.read_csv('data/input.csv')

df = df.dropna(subset=['colony_diameter_mm'])
df = df[df['colony_diameter_mm'] > 0]

group_a = df[df['media_type'] == 'A']['colony_diameter_mm'].values
group_b = df[df['media_type'] == 'B']['colony_diameter_mm'].values

t_stat, p_value = stats.ttest_ind(group_a, group_b)

mean_a = group_a.mean()
std_a = group_a.std()
n_a = len(group_a)

mean_b = group_b.mean()
std_b = group_b.std()
n_b = len(group_b)

se_a = std_a / (n_a ** 0.5)
se_b = std_b / (n_b ** 0.5)

report = f"""# Bacterial Colony Growth Comparison

## Objective
Compare colony diameter growth between two culture media formulations after 48-hour incubation.

## Methods
- Culture Media A: Standard formulation (control group)
- Culture Media B: Experimental formulation (test group)
- Response variable: Colony diameter (mm)
- Statistical test: Independent samples t-test

## Results

### Sample Composition
| Group | Media Type | Plates |
|-------|-----------|--------|
| A (Control) | Standard | {n_a} |
| B (Test) | Experimental | {n_b} |

### Descriptive Statistics
| Media | Mean Diameter (mm) | Std Dev | SE | N |
|-------|-------------------|--------|-----|---|
| A | {mean_a:.2f} | {std_a:.2f} | {se_a:.2f} | {n_a} |
| B | {mean_b:.2f} | {std_b:.2f} | {se_b:.2f} | {n_b} |

### Statistical Inference
Independent samples t-test:
- t-statistic: {t_stat:.3f}
- p-value: {p_value:.4f}
- Degrees of freedom: {n_a + n_b - 2}

## Interpretation
"""

if p_value < 0.05:
    report += f"Media B produced significantly larger colonies than Media A (p = {p_value:.4f}). The experimental formulation shows a mean increase of {mean_b - mean_a:.2f} mm in colony diameter compared to the standard formulation."
else:
    report += f"No statistically significant difference in colony diameter was detected between the two media formulations (p = {p_value:.4f}). Both formulations supported similar bacterial growth rates."

with open('results/report.md', 'w') as f:
    f.write(report)