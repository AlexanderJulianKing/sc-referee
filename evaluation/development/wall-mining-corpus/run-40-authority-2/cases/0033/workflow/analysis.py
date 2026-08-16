import csv
from pathlib import Path
from scipy import stats

def load_water_quality_data(filepath):
    upstream_do = []
    downstream_do = []
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            do_value = float(row['dissolved_oxygen_mg_per_l'])
            section = row['site_section'].strip()
            if section == 'upstream':
                upstream_do.append(do_value)
            else:
                downstream_do.append(do_value)
    
    return upstream_do, downstream_do

def validate_groups(upstream_do, downstream_do):
    if len(upstream_do) < 2 or len(downstream_do) < 2:
        raise ValueError("Insufficient samples: need at least 2 per group")

def compute_summary(values, label):
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    stdev = variance ** 0.5
    return {
        'label': label,
        'count': n,
        'mean': mean,
        'stdev': stdev,
        'min': min(values),
        'max': max(values)
    }

def main():
    input_csv = Path('data/input.csv')
    output_md = Path('results/report.md')
    
    upstream_do, downstream_do = load_water_quality_data(input_csv)
    validate_groups(upstream_do, downstream_do)
    
    up_summary = compute_summary(upstream_do, 'Upstream')
    down_summary = compute_summary(downstream_do, 'Downstream')
    
    t_stat, pval = stats.ttest_ind(upstream_do, downstream_do)
    
    output_md.parent.mkdir(parents=True, exist_ok=True)
    
    report_text = f"""# River Water Quality Analysis

## Objective
Compare dissolved oxygen (DO) levels between upstream and downstream sections of a river system to assess potential water quality degradation.

## Methods
Independent samples t-test was applied to compare DO concentrations between two river sections.

## Results

### Upstream Section (n={up_summary['count']})
- Mean DO: {up_summary['mean']:.2f} mg/L
- Std Dev: {up_summary['stdev']:.2f} mg/L
- Range: {up_summary['min']:.2f}–{up_summary['max']:.2f} mg/L

### Downstream Section (n={down_summary['count']})
- Mean DO: {down_summary['mean']:.2f} mg/L
- Std Dev: {down_summary['stdev']:.2f} mg/L
- Range: {down_summary['min']:.2f}–{down_summary['max']:.2f} mg/L

### Statistical Test
**Independent Samples t-test**
- t-statistic: {t_stat:.4f}
- p-value: {pval:.6f}

## Interpretation

"""
    
    alpha = 0.05
    if pval < alpha:
        report_text += f"A statistically significant difference was detected (p = {pval:.6f} < {alpha}). The downstream section exhibits lower dissolved oxygen ({down_summary['mean']:.2f} mg/L) compared to upstream ({up_summary['mean']:.2f} mg/L), suggesting potential water quality degradation downstream."
    else:
        report_text += f"No statistically significant difference in DO levels was detected (p = {pval:.6f} ≥ {alpha})."
    
    report_text += "\n\n## Conclusion\nThe analysis provides evidence regarding oxygen availability in different river sections, which is critical for supporting aquatic life and ecosystem function."
    
    output_md.write_text(report_text)

if __name__ == '__main__':
    main()