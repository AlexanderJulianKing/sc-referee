import csv
from scipy import stats

def load_data(filepath):
    records = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                yield_val = float(row['yield_kg'])
                if yield_val > 0:
                    records.append(row)
            except (ValueError, KeyError):
                continue
    return records

def main():
    records = load_data('data/input.csv')
    
    drip_yields = []
    traditional_yields = []
    
    for record in records:
        yield_val = float(record['yield_kg'])
        if record['irrigation_method'] == 'drip':
            drip_yields.append(yield_val)
        elif record['irrigation_method'] == 'traditional':
            traditional_yields.append(yield_val)
    
    statistic, p_value = stats.mannwhitneyu(drip_yields, traditional_yields, alternative='two-sided')
    
    drip_mean = sum(drip_yields) / len(drip_yields) if drip_yields else 0
    trad_mean = sum(traditional_yields) / len(traditional_yields) if traditional_yields else 0
    drip_median = sorted(drip_yields)[len(drip_yields) // 2] if drip_yields else 0
    trad_median = sorted(traditional_yields)[len(traditional_yields) // 2] if traditional_yields else 0
    
    report = f"""# Irrigation Method Comparison: Field Trial Yield Analysis

## Study Design

This analysis compares crop yield performance between drip irrigation and traditional sprinkler irrigation methods across field plots in a controlled agricultural trial.

## Data Summary

**Drip Irrigation:**
- Number of plots: {len(drip_yields)}
- Mean yield: {drip_mean:.2f} kg/plot
- Median yield: {drip_median:.2f} kg/plot

**Traditional Irrigation:**
- Number of plots: {len(traditional_yields)}
- Mean yield: {trad_mean:.2f} kg/plot
- Median yield: {trad_median:.2f} kg/plot

## Statistical Analysis

A Mann-Whitney U test (non-parametric test for independent samples) was conducted to determine whether yield distributions differ significantly between irrigation methods.

**Test Results:**
- U-statistic: {statistic:.2f}
- p-value: {p_value:.4f}
- Significance level: α = 0.05

## Findings

"""
    
    if p_value < 0.05:
        report += f"The difference in yield distributions is statistically significant (p = {p_value:.4f}). "
        if drip_mean > trad_mean:
            report += f"Drip irrigation demonstrated higher mean yield ({drip_mean:.2f} vs {trad_mean:.2f} kg/plot), suggesting potential efficiency gains of {drip_mean - trad_mean:.2f} kg per plot."
        else:
            report += f"Traditional irrigation demonstrated higher mean yield ({trad_mean:.2f} vs {drip_mean:.2f} kg/plot), suggesting {trad_mean - drip_mean:.2f} kg more per plot."
    else:
        report += f"No statistically significant difference was detected between irrigation methods (p = {p_value:.4f}). Both methods produced comparable yields under the trial conditions."
    
    with open('results/report.md', 'w') as f:
        f.write(report)

if __name__ == '__main__':
    main()
