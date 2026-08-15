import csv
from pathlib import Path
from scipy.stats import chi2_contingency
import math

def main():
    input_file = Path('data/input.csv')
    data = []
    with open(input_file) as f:
        for row in csv.DictReader(f):
            data.append(row)
    
    categories = sorted(set(r['category'] for r in data))
    levels = sorted(set(r['satisfaction'] for r in data))
    
    table = []
    for level in levels:
        row = [sum(1 for r in data if r['category'] == c and r['satisfaction'] == level) 
               for c in categories]
        table.append(row)
    
    chi2, p_val, dof, expected = chi2_contingency(table)
    n = sum(sum(r) for r in table)
    min_dim = min(len(levels), len(categories))
    cramers_v = math.sqrt(chi2 / (n * (min_dim - 1))) if (n * (min_dim - 1)) > 0 else 0
    
    headers = ['Satisfaction'] + categories
    sep_parts = ['---'] * len(headers)
    header_row = '| ' + ' | '.join(headers) + ' |'
    sep_row = '| ' + ' | '.join(sep_parts) + ' |'
    
    rows_md = []
    for i, level in enumerate(levels):
        row_data = [level] + [str(table[i][j]) for j in range(len(categories))]
        row_str = '| ' + ' | '.join(row_data) + ' |'
        rows_md.append(row_str)
    
    table_md = header_row + '\n' + sep_row + '\n' + '\n'.join(rows_md)
    
    if cramers_v < 0.1:
        effect_desc = 'negligible'
    elif cramers_v < 0.3:
        effect_desc = 'small'
    elif cramers_v < 0.5:
        effect_desc = 'medium'
    else:
        effect_desc = 'large'
    
    report = f"""# Customer Satisfaction Analysis

## Overview
Chi-square test of independence examining the relationship between product category and customer satisfaction levels.

**Sample size:** {n} responses
**Categories:** {', '.join(categories)}
**Satisfaction levels:** {', '.join(levels)}

## Contingency Table
{table_md}

## Statistical Test Results

### Chi-Square Test of Independence
- Test statistic: χ² = {chi2:.4f}
- P-value: {p_val:.6f}
- Degrees of freedom: {dof}
- Significance level: α = 0.05

### Effect Size Measure
- Cramér's V = {cramers_v:.4f} ({effect_desc})

## Interpretation

"""
    
    if p_val < 0.05:
        report += f"**Statistically significant result** (χ² = {chi2:.4f}, p = {p_val:.6f}). There is evidence of association between product category and satisfaction levels.\n\n"
    else:
        report += f"**Not statistically significant** (χ² = {chi2:.4f}, p = {p_val:.6f}). No strong evidence of association between category and satisfaction.\n\n"
    
    report += f"The effect size (Cramér's V = {cramers_v:.4f}) indicates a {effect_desc} practical relationship. "
    report += "Categories may differ in satisfaction distribution, but the magnitude of difference varies in practical importance."
    
    output_file = Path('results/report.md')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(report)

if __name__ == '__main__':
    main()