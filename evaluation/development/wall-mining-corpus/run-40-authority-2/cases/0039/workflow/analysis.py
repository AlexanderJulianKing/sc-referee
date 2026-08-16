import pandas as pd
from scipy import stats

df = pd.read_csv('data/input.csv')

led_group = df[df['light_type'] == 'LED']['plant_height'].values
natural_group = df[df['light_type'] == 'Natural']['plant_height'].values

t_statistic, p_value = stats.ttest_ind(led_group, natural_group)

led_mean = led_group.mean()
led_std = led_group.std()
nat_mean = natural_group.mean()
nat_std = natural_group.std()

report_text = f"""# Plant Height Analysis Under Different Light Conditions

## Study Design
This study compared plant height after 6 weeks of growth under two light conditions: LED lighting and natural sunlight exposure. All plants were grown in identical soil, containers, and climate-controlled conditions except for the light treatment.

## Group Characteristics
- LED Lighting: n={len(led_group)}, Mean height = {led_mean:.2f} cm, SD = {led_std:.2f} cm
- Natural Light: n={len(natural_group)}, Mean height = {nat_mean:.2f} cm, SD = {nat_std:.2f} cm

## Statistical Analysis
An independent samples t-test was performed to test for differences in plant height between the two light conditions.

**Results:**
- t({len(led_group) + len(natural_group) - 2}) = {t_statistic:.3f}
- p-value = {p_value:.4f}

## Interpretation
{'There was a statistically significant difference in plant height between the LED and natural light groups (p < 0.05).' if p_value < 0.05 else 'There was no statistically significant difference in plant height between the LED and natural light groups (p ≥ 0.05).'}

The group grown under {'LED' if led_mean > nat_mean else 'natural'} light showed {'higher' if led_mean > nat_mean else 'lower'} average plant heights, with a mean difference of {abs(led_mean - nat_mean):.2f} cm.
"""

with open('results/report.md', 'w') as f:
    f.write(report_text)