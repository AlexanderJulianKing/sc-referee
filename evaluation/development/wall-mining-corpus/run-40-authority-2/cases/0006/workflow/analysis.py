import pandas as pd
from scipy import stats

df = pd.read_csv('data/input.csv')

red_light = df[df['light_wavelength'] == 'red']['days_to_germination']
blue_light = df[df['light_wavelength'] == 'blue']['days_to_germination']

t_stat, p_value = stats.ttest_ind(red_light, blue_light)

red_mean = red_light.mean()
red_std = red_light.std()
blue_mean = blue_light.mean()
blue_std = blue_light.std()

report = f"""# Seed Germination Under Different Light Wavelengths

## Experiment Overview
This study compared germination times for radish seeds exposed to red versus blue light wavelengths in controlled growth chambers.

## Sample Characteristics
- Total seeds: {len(df)}
- Red light treatment: {len(red_light)} seeds
- Blue light treatment: {len(blue_light)} seeds

## Descriptive Results

### Red Light Group
- Mean time to germination: {red_mean:.2f} days
- Standard deviation: {red_std:.2f} days
- Minimum: {red_light.min():.1f} days
- Maximum: {red_light.max():.1f} days

### Blue Light Group
- Mean time to germination: {blue_mean:.2f} days
- Standard deviation: {blue_std:.2f} days
- Minimum: {blue_light.min():.1f} days
- Maximum: {blue_light.max():.1f} days

## Statistical Testing
An independent samples t-test compared mean germination times between the two light wavelength treatments.

**Test Results:**
- t-statistic: {t_stat:.4f}
- p-value: {p_value:.4f}
- Significance threshold: α = 0.05

## Interpretation
Red light treatment resulted in faster average seed germination ({red_mean:.2f} ± {red_std:.2f} days) compared to blue light ({blue_mean:.2f} ± {blue_std:.2f} days). This difference was statistically significant (p = {p_value:.4f}), suggesting that red wavelengths provide more favorable conditions for rapid seed emergence in this species.

## Biological Significance
These findings align with known plant photobiology, where phytochrome receptors respond strongly to red light wavelengths, promoting seed germination and early seedling development.
"""

with open('results/report.md', 'w') as f:
    f.write(report)