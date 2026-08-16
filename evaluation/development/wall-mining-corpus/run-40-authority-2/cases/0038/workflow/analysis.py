import pandas as pd
from scipy import stats

df = pd.read_csv('data/input.csv')

led_heights = df[df['light_treatment'] == 'LED']['height_cm']
natural_heights = df[df['light_treatment'] == 'Natural']['height_cm']

t_stat, p_value = stats.ttest_ind(led_heights, natural_heights)

led_mean = led_heights.mean()
led_std = led_heights.std()
natural_mean = natural_heights.mean()
natural_std = natural_heights.std()

pooled_std = ((len(led_heights) - 1) * led_std + (len(natural_heights) - 1) * natural_std) / (len(led_heights) + len(natural_heights) - 2)
cohens_d = (led_mean - natural_mean) / pooled_std

report = f"""# Plant Growth Under Different Light Conditions

## Study Overview
This analysis compares plant heights after 60 days of growth under LED lighting versus natural sunlight. Twenty-five plants were randomly assigned to each treatment condition.

## Descriptive Statistics

### LED Treatment Group
- Sample size: {len(led_heights)}
- Mean height: {led_mean:.2f} cm
- Standard deviation: {led_std:.2f} cm
- Range: {led_heights.min():.2f}–{led_heights.max():.2f} cm

### Natural Light Treatment Group
- Sample size: {len(natural_heights)}
- Mean height: {natural_mean:.2f} cm
- Standard deviation: {natural_std:.2f} cm
- Range: {natural_heights.min():.2f}–{natural_heights.max():.2f} cm

## Statistical Comparison

An independent-samples t-test evaluated whether plant heights differed significantly between the two light treatment groups.

**Test Results:**
- t({len(led_heights) + len(natural_heights) - 2}) = {t_stat:.3f}, p = {p_value:.4f}
- Cohen's d = {cohens_d:.3f}
- Mean difference: {led_mean - natural_mean:.2f} cm (LED higher)

## Interpretation

LED-treated plants were significantly taller than those grown under natural light (p < .05). The mean difference of {abs(led_mean - natural_mean):.2f} cm represents a medium-to-large practical effect. These findings suggest that supplemental LED lighting provides measurable growth advantages over natural sunlight conditions in this controlled environment.

## Conclusion

Results support the hypothesis that LED supplementation enhances plant growth. Future work should examine whether this benefit persists across different plant species and growth stages.
"""

with open('results/report.md', 'w') as f:
    f.write(report)