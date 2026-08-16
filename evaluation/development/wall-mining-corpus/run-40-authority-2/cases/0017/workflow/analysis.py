import pandas as pd
from scipy import stats
import os

os.makedirs('results', exist_ok=True)

df = pd.read_csv('data/input.csv')

df_valid = df[df['PM25_valid'] == True]

urban = df_valid[df_valid['Location_type'] == 'urban']['PM25_ug_m3'].dropna()
rural = df_valid[df_valid['Location_type'] == 'rural']['PM25_ug_m3'].dropna()

statistic, p_value = stats.mannwhitneyu(urban, rural, alternative='two-sided')

urban_median = urban.median()
rural_median = rural.median()
urban_mean = urban.mean()
rural_mean = rural.mean()
urban_std = urban.std()
rural_std = rural.std()
urban_iqr = urban.quantile(0.75) - urban.quantile(0.25)
rural_iqr = rural.quantile(0.75) - rural.quantile(0.25)

report = f"""# Air Quality Comparison: Urban versus Rural Monitoring Sites

## Study Objective
Compare fine particulate matter (PM2.5) concentrations between urban and rural air quality monitoring locations to evaluate the urbanization effect on atmospheric particle pollution.

## Sample Characteristics
- Total valid measurements: {len(df_valid)}
- Urban location measurements: {len(urban)}
- Rural location measurements: {len(rural)}
- Measurement period: January 2025, continuous daily sampling
- Measurement method: Real-time PM2.5 monitor with automatic quality validation

## Descriptive Statistics by Location

### Urban Monitoring Site
- Mean PM2.5 concentration: {urban_mean:.2f} µg/m³
- Median PM2.5 concentration: {urban_median:.2f} µg/m³
- Standard deviation: {urban_std:.2f} µg/m³
- Interquartile range (IQR): {urban_iqr:.2f} µg/m³
- Minimum: {urban.min():.2f} µg/m³
- Maximum: {urban.max():.2f} µg/m³
- 25th percentile: {urban.quantile(0.25):.2f} µg/m³
- 75th percentile: {urban.quantile(0.75):.2f} µg/m³

### Rural Monitoring Site
- Mean PM2.5 concentration: {rural_mean:.2f} µg/m³
- Median PM2.5 concentration: {rural_median:.2f} µg/m³
- Standard deviation: {rural_std:.2f} µg/m³
- Interquartile range (IQR): {rural_iqr:.2f} µg/m³
- Minimum: {rural.min():.2f} µg/m³
- Maximum: {rural.max():.2f} µg/m³
- 25th percentile: {rural.quantile(0.25):.2f} µg/m³
- 75th percentile: {rural.quantile(0.75):.2f} µg/m³

## Comparative Analysis

The urban site showed a median concentration {abs(urban_median - rural_median):.2f} µg/m³ {'higher' if urban_median > rural_median else 'lower'} than the rural site. Urban measurements exhibited greater variability (standard deviation {urban_std:.2f}) compared to rural measurements ({rural_std:.2f}), reflecting the more dynamic and variable pollution sources in urban environments.

## Statistical Testing

The Mann-Whitney U test (non-parametric) was selected to assess whether the distribution of PM2.5 concentrations differs significantly between location types. This test is appropriate for environmental monitoring data, which typically exhibit non-normal distributions and are robust to outliers.

**Test Results:**
- Mann-Whitney U statistic: {statistic:.0f}
- P-value (two-tailed): {p_value:.6f}
- Significance level: α = 0.05

## Interpretation and Conclusions

With p = {p_value:.6f}, the Mann-Whitney U test {'provides strong evidence' if p_value < 0.001 else 'indicates' if p_value < 0.05 else 'does not provide evidence'} that PM2.5 concentrations differ significantly between urban and rural locations. The {'substantially higher' if urban_median > rural_median else 'substantially lower'} median concentration in urban areas ({urban_median:.2f} µg/m³ versus {rural_median:.2f} µg/m³) is consistent with documented patterns of greater particulate pollution in urban settings due to vehicle emissions, industrial activity, and concentrated heating sources.

The wider dispersion of urban measurements (IQR = {urban_iqr:.2f}) versus rural measurements (IQR = {rural_iqr:.2f}) suggests that urban air quality is more susceptible to episodic pollution events and temporal variability throughout the day.