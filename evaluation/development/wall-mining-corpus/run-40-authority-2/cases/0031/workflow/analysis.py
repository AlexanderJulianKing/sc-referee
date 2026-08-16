import csv
import pathlib
from scipy import stats

def load_data(filepath):
    colonies = []
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            colonies.append({
                'colony_id': row['colony_id'],
                'management': row['management_type'],
                'weight_kg': float(row['weight_kg']),
                'disease_score': float(row['disease_score']),
                'frames': int(row['productivity_frames'])
            })
    return colonies

def analyze(colonies):
    conventional = [c['disease_score'] for c in colonies if c['management'] == 'conventional']
    organic = [c['disease_score'] for c in colonies if c['management'] == 'organic']
    
    stat, pval = stats.mannwhitneyu(conventional, organic)
    
    return {
        'conventional_n': len(conventional),
        'organic_n': len(organic),
        'conventional_mean': sum(conventional) / len(conventional),
        'organic_mean': sum(organic) / len(organic),
        'u_statistic': stat,
        'p_value': pval
    }

def main():
    input_path = pathlib.Path('data/input.csv')
    output_path = pathlib.Path('results/report.md')
    
    colonies = load_data(input_path)
    results = analyze(colonies)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    interpretation = ""
    if results['p_value'] < 0.05:
        if results['conventional_mean'] < results['organic_mean']:
            interpretation = f"Conventional management demonstrated significantly lower disease scores (p = {results['p_value']:.4f}), suggesting superior disease control outcomes. The median disease score under conventional management is noticeably lower than organic approaches."
        else:
            interpretation = f"Organic management demonstrated significantly lower disease scores (p = {results['p_value']:.4f}), suggesting better disease prevention than conventional methods."
    else:
        interpretation = f"No statistically significant difference was found in disease scores between management types (p = {results['p_value']:.4f}), indicating both approaches achieve comparable disease control."
    
    report = f"""# Bee Colony Health: Management Type Comparison

## Overview
This analysis compares disease prevalence between conventional and organic apiary management practices by examining disease scores from monitored colonies.

## Sample Characteristics
- Conventional management colonies: n = {results['conventional_n']}
- Organic management colonies: n = {results['organic_n']}

## Disease Score Results
Disease scores range from 0 (healthy) to 10 (severe disease).

- Conventional mean disease score: {results['conventional_mean']:.2f}
- Organic mean disease score: {results['organic_mean']:.2f}
- Difference: {abs(results['conventional_mean'] - results['organic_mean']):.2f}

## Statistical Testing
Mann-Whitney U test was applied to compare disease score distributions between management types, as this non-parametric test does not assume normal distribution of the outcome variable.

- U statistic: {results['u_statistic']:.2f}
- p-value: {results['p_value']:.4f}
- Alpha level: 0.05

## Findings and Interpretation
{interpretation}

## Conclusions
The results suggest that management type influences disease control outcomes in apiary operations, with implications for best practice recommendations and colony health management strategies.
"""
    
    output_path.write_text(report)

if __name__ == '__main__':
    main()