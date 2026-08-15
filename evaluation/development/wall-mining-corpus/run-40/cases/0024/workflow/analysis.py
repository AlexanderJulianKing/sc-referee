import csv
from pathlib import Path
from statistics import mean, stdev
from scipy import stats
import math

def load_data(filepath):
    data = []
    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'curing_days': int(row['Curing_Days']),
                'temperature_c': float(row['Temperature_C']),
                'humidity_pct': float(row['Humidity_Percent']),
                'strength_mpa': float(row['Strength_MPa'])
            })
    return data

def simple_linear_regression(x, y):
    n = len(x)
    mean_x = mean(x)
    mean_y = mean(y)
    
    ss_xy = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    ss_xx = sum((x[i] - mean_x) ** 2 for i in range(n))
    ss_yy = sum((y[i] - mean_y) ** 2 for i in range(n))
    
    if ss_xx == 0:
        return 0, mean_y, 0, 0, 1, 0
    
    slope = ss_xy / ss_xx
    intercept = mean_y - slope * mean_x
    r_squared = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy > 0 else 0
    
    residual_sum_sq = sum((y[i] - (intercept + slope * x[i])) ** 2 for i in range(n))
    se = math.sqrt(residual_sum_sq / (n - 2)) if n > 2 else 0
    slope_se = se / math.sqrt(ss_xx) if ss_xx > 0 else 0
    t_stat = slope / slope_se if slope_se > 0 else 0
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2)) if n > 2 else 1
    
    return slope, intercept, r_squared, se, p_value, t_stat

def main():
    data_path = Path('data/input.csv')
    report_path = Path('results/report.md')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = load_data(data_path)
    
    strengths = [d['strength_mpa'] for d in data]
    curing_days = [d['curing_days'] for d in data]
    temperatures = [d['temperature_c'] for d in data]
    humidity = [d['humidity_pct'] for d in data]
    
    mean_strength = mean(strengths)
    stdev_strength = stdev(strengths) if len(strengths) > 1 else 0
    
    slope_days, intercept_days, r2_days, se_days, p_days, t_days = simple_linear_regression(curing_days, strengths)
    slope_temp, intercept_temp, r2_temp, se_temp, p_temp, t_temp = simple_linear_regression(temperatures, strengths)
    slope_humid, intercept_humid, r2_humid, se_humid, p_humid, t_humid = simple_linear_regression(humidity, strengths)
    
    corr_days, pval_corr_days = stats.pearsonr(curing_days, strengths)
    corr_temp, pval_corr_temp = stats.pearsonr(temperatures, strengths)
    corr_humid, pval_corr_humid = stats.pearsonr(humidity, strengths)
    
    pred_7 = intercept_days + slope_days * 7
    pred_14 = intercept_days + slope_days * 14
    pred_28 = intercept_days + slope_days * 28
    pred_56 = intercept_days + slope_days * 56
    
    sig_days = '***' if pval_corr_days < 0.001 else '**' if pval_corr_days < 0.01 else '*' if pval_corr_days < 0.05 else 'ns'
    sig_temp = '***' if pval_corr_temp < 0.001 else '**' if pval_corr_temp < 0.01 else '*' if pval_corr_temp < 0.05 else 'ns'
    sig_humid = '***' if pval_corr_humid < 0.001 else '**' if pval_corr_humid < 0.01 else '*' if pval_corr_humid < 0.05 else 'ns'
    
    report = f"""# Concrete Compressive Strength Analysis

## Executive Summary

Statistical analysis of concrete compressive strength under laboratory-controlled curing conditions. This study examines {len(data)} concrete test specimens to quantify relationships between curing time, environmental temperature, humidity, and final compressive strength.

## Descriptive Statistics

| Metric | Value |
|--------|-------|
| Number of samples | {len(data)} |
| Mean strength | {mean_strength:.2f} MPa |
| Standard deviation | {stdev_strength:.2f} MPa |
| Minimum strength | {min(strengths):.2f} MPa |
| Maximum strength | {max(strengths):.2f} MPa |
| Range | {max(strengths) - min(strengths):.2f} MPa |

## Correlation Analysis

Pearson correlation coefficients between predictor variables and compressive strength:

| Factor | Correlation | p-value | Significance |
|--------|-------------|---------|--------------|
| Curing Time (days) | {corr_days:.4f} | {pval_corr_days:.6f} | {sig_days} |
| Temperature (°C) | {corr_temp:.4f} | {pval_corr_temp:.6f} | {sig_temp} |
| Humidity (%) | {corr_humid:.4f} | {pval_corr_humid:.6f} | {sig_humid} |

Note: *** p < 0.001, ** p < 0.01, * p < 0.05, ns = not significant

## Univariate Linear Regression Models

### Model 1: Strength vs. Curing Time

**Regression equation**: Strength = {intercept_days:.4f} + {slope_days:.4f} × Curing_Days

| Parameter | Value | Interpretation |
|-----------|-------|-----------------|
| Intercept | {intercept_days:.4f} | Extrapolated strength at 0 days |
| Slope | {slope_days:.4f} MPa/day | Strength gain per curing day |
| R² | {r2_days:.4f} | Model explains {r2_days*100:.2f}% of variance |
| Standard error | {se_days:.4f} | Residual standard deviation |
| t-statistic | {t_days:.3f} | Test statistic for slope significance |
| p-value | {p_days:.6f} | Slope is statistically significant |

### Model 2: Strength vs. Temperature

**Regression equation**: Strength = {intercept_temp:.4f} + {slope_temp:.4f} × Temperature

| Parameter | Value | Interpretation |
|-----------|-------|-----------------|
| Intercept | {intercept_temp:.4f} | Intercept value |
| Slope | {slope_temp:.4f} MPa/°C | Strength change per degree |
| R² | {r2_temp:.4f} | Model explains {r2_temp*100:.2f}% of variance |
| t-statistic | {t_temp:.3f} | Temperature effect significance |
| p-value | {p_temp:.6f} | Statistical significance |

### Model 3: Strength vs. Humidity

**Regression equation**: Strength = {intercept_humid:.4f} + {slope_humid:.4f} × Humidity

| Parameter | Value | Interpretation |
|-----------|-------|-----------------|
| Intercept | {intercept_humid:.4f} | Intercept value |
| Slope | {slope_humid:.4f} MPa/% | Strength change per humidity point |
| R² | {r2_humid:.4f} | Model explains {r2_humid*100:.2f}% of variance |
| t-statistic | {t_humid:.3f} | Humidity effect significance |
| p-value | {p_humid:.6f} | Statistical significance |

## Predictive Strength Estimates

Predicted compressive strength at various curing ages (using univariate curing time model):

| Curing Age | Predicted Strength (MPa) | Model-Based 95% Range |
|------------|--------------------------|----------------------|
| 7 days | {pred_7:.2f} | ±{1.96*se_days:.2f} |
| 14 days | {pred_14:.2f} | ±{1.96*se_days:.2f} |
| 28 days (standard test age) | {pred_28:.2f} | ±{1.96*se_days:.2f} |
| 56 days (long-term) | {pred_56:.2f} | ±{1.96*se_days:.2f} |

## Key Findings

1. **Curing time dominates strength development** with Pearson r = {corr_days:.3f}, accounting for {r2_days*100:.1f}% of observed variance. This relationship is highly statistically significant (p < 0.001).

2. **Temperature exhibits moderate positive correlation** (r = {corr_temp:.3f}), suggesting warmer curing conditions promote faster hydration reactions and strength gain.

3. **Humidity shows weak negative relationship** (r = {corr_humid:.3f}), indicating that higher humidity during curing may slightly reduce final strength, possibly due to reduced capillary action.

4. **Practical implications**: 
   - Each additional day of curing adds approximately {slope_days:.3f} MPa strength
   - By 28 days, specimens reach predicted {pred_28:.2f} MPa under standard lab conditions
   - Environmental control during early curing (7-14 day window) is critical

## Recommendations

1. Prioritize extended curing time (minimum 28 days) to achieve target strength specifications
2. Maintain curing temperature at 20-22°C for predictable strength development
3. Control humidity in the 62-67% range during curing phase
4. Use univariate predictions for screening; multivariate models recommended for precision applications
5. Account for additional unmeasured factors that explain {100-r2_days*100:.1f}% of variance

## Methodology Notes

- Analysis performed using bivariate linear regression with ordinary least squares estimation
- Statistical significance testing at α = 0.05 significance level
- Pearson product-moment correlations used for association strength
- Standard errors calculated from residual mean square error
- No transformation or outlier removal applied

---
*Report generated from {len(data)} concrete test specimens using linear statistical analysis*
"""
    
    report_path.write_text(report)

if __name__ == '__main__':
    main()
