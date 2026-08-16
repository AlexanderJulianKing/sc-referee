import pandas as pd
from scipy import stats
import os

os.makedirs('results', exist_ok=True)

df = pd.read_csv('data/input.csv')

if df.empty:
    raise ValueError("Input CSV is empty")

if not {'request_id', 'cdn_provider', 'load_time_ms'}.issubset(df.columns):
    raise ValueError("Missing required columns")

provider_a_times = df[df['cdn_provider'] == 'ProviderA']['load_time_ms'].dropna()
provider_b_times = df[df['cdn_provider'] == 'ProviderB']['load_time_ms'].dropna()

if len(provider_a_times) == 0 or len(provider_b_times) == 0:
    raise ValueError("One or both groups are empty after filtering")

t_stat, p_value = stats.ttest_ind(provider_a_times, provider_b_times)

mean_a = provider_a_times.mean()
median_a = provider_a_times.median()
std_a = provider_a_times.std()
min_a = provider_a_times.min()
max_a = provider_a_times.max()
n_a = len(provider_a_times)

mean_b = provider_b_times.mean()
median_b = provider_b_times.median()
std_b = provider_b_times.std()
min_b = provider_b_times.min()
max_b = provider_b_times.max()
n_b = len(provider_b_times)

mean_diff = mean_a - mean_b

report = f"""# CDN Provider Performance Analysis

## Overview

This study compares page load times between two content delivery network (CDN) providers across {len(df)} independent network requests originating from multiple geographic regions.

## Sample Summary

- Total Requests: {len(df)}
- ProviderA: {n_a} requests
- ProviderB: {n_b} requests

## Descriptive Statistics

### ProviderA Load Times
- Mean: {mean_a:.2f} ms
- Median: {median_a:.2f} ms
- Standard Deviation: {std_a:.2f} ms
- Range: {min_a:.2f} - {max_a:.2f} ms

### ProviderB Load Times
- Mean: {mean_b:.2f} ms
- Median: {median_b:.2f} ms
- Standard Deviation: {std_b:.2f} ms
- Range: {min_b:.2f} - {max_b:.2f} ms

## Statistical Analysis

### Two-Sample t-test Results
- t-statistic: {t_stat:.4f}
- p-value: {p_value:.6f}
- Significance level: α = 0.05

### Interpretation
"""

if p_value < 0.05:
    direction = "longer" if mean_diff > 0 else "shorter"
    report += f"There is a statistically significant difference in mean load times between the two providers (p = {p_value:.6f}). ProviderA has {direction} load times by approximately {abs(mean_diff):.2f} ms on average."
else:
    report += f"No statistically significant difference was detected between the providers at the 0.05 significance level (p = {p_value:.4f}). Both CDN providers demonstrate comparable performance characteristics."

report += f"\n\n## Conclusion\n\nBased on an analysis of {len(df)} independent network requests, this study provides empirical evidence regarding the relative performance of the two CDN providers. Organizations should use these load time comparisons in conjunction with other factors such as geographic coverage, reliability, cost structure, and customer support when evaluating CDN solutions.\n"

with open('results/report.md', 'w') as f:
    f.write(report)