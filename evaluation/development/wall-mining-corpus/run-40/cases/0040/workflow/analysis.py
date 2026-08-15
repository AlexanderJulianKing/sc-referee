import csv
from pathlib import Path
from statistics import mean, stdev
from scipy import stats

def main():
    data_file = Path('data/input.csv')
    report_file = Path('results/report.md')
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    samples = []
    with open(data_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append({
                'plot_id': row['Plot_ID'],
                'ph': float(row['pH']),
                'nitrogen': float(row['Nitrogen_ppm']),
                'phosphorus': float(row['Phosphorus_ppm']),
                'potassium': float(row['Potassium_ppm']),
                'organic_matter': float(row['Organic_Matter_percent']),
                'texture': row['Soil_Texture']
            })
    
    optimal_ranges = {
        'ph': (6.0, 7.5),
        'nitrogen': (20, 40),
        'phosphorus': (15, 30),
        'potassium': (150, 250),
        'organic_matter': (3.0, 6.0)
    }
    
    summary_stats = {}
    for nutrient in ['ph', 'nitrogen', 'phosphorus', 'potassium', 'organic_matter']:
        values = [s[nutrient] for s in samples]
        summary_stats[nutrient] = {
            'mean': mean(values),
            'stdev': stdev(values) if len(values) > 1 else 0.0,
            'min': min(values),
            'max': max(values)
        }
    
    normality = {}
    for nutrient in ['nitrogen', 'phosphorus', 'potassium']:
        values = [s[nutrient] for s in samples]
        if len(values) >= 3:
            _, p_val = stats.shapiro(values)
            normality[nutrient] = p_val
    
    problem_plots = []
    for sample in samples:
        issues = []
        if sample['nitrogen'] < optimal_ranges['nitrogen'][0]:
            issues.append(f"N {sample['nitrogen']:.1f} ppm")
        if sample['phosphorus'] < optimal_ranges['phosphorus'][0]:
            issues.append(f"P {sample['phosphorus']:.1f} ppm")
        if sample['potassium'] < optimal_ranges['potassium'][0]:
            issues.append(f"K {sample['potassium']:.1f} ppm")
        if sample['ph'] < optimal_ranges['ph'][0] or sample['ph'] > optimal_ranges['ph'][1]:
            issues.append(f"pH {sample['ph']:.2f}")
        
        if issues:
            problem_plots.append((sample['plot_id'], issues))
    
    texture_dist = {}
    for sample in samples:
        t = sample['texture']
        texture_dist[t] = texture_dist.get(t, 0) + 1
    
    report_text = f"""# Soil Quality Assessment Report

## Executive Summary

Soil analysis of {len(samples)} plots reveals current nutrient status and identifies management priorities. {len(problem_plots)} plots ({100*len(problem_plots)/len(samples):.0f}%) require targeted intervention.

## Overview

| Metric | Value |
|--------|-------|
| Total plots sampled | {len(samples)} |
| Plots needing treatment | {len(problem_plots)} |
| Soil texture types | {len(texture_dist)} |

### Soil Texture Distribution

"""
    
    for texture in sorted(texture_dist.keys()):
        count = texture_dist[texture]
        pct = 100.0 * count / len(samples)
        report_text += f"- **{texture.capitalize()}**: {count} plots ({pct:.1f}%)\n"
    
    report_text += "\n## Nutrient Profile\n"
    
    for nutrient in ['ph', 'nitrogen', 'phosphorus', 'potassium', 'organic_matter']:
        stats_val = summary_stats[nutrient]
        low, high = optimal_ranges[nutrient]
        label = nutrient.replace('_', ' ').title()
        
        report_text += f"\n### {label}\n"
        report_text += f"- **Mean**: {stats_val['mean']:.2f} ± {stats_val['stdev']:.2f}\n"
        report_text += f"- **Observed range**: {stats_val['min']:.2f} to {stats_val['max']:.2f}\n"
        report_text += f"- **Optimal range**: {low} to {high}\n"
        
        out_of_opt = sum(1 for s in samples 
                        if s[nutrient] < low or s[nutrient] > high)
        report_text += f"- **Outside optimal**: {out_of_opt} plots\n"
    
    report_text += "\n## Statistical Distribution\n\n"
    report_text += "Shapiro-Wilk normality test (α = 0.05):\n\n"
    
    for nutrient in ['nitrogen', 'phosphorus', 'potassium']:
        p = normality.get(nutrient, 0)
        status = "Normal" if p > 0.05 else "Non-normal"
        report_text += f"- **{nutrient.capitalize()}**: p = {p:.4f} ({status})\n"
    
    report_text += "\n## Plots Requiring Action\n\n"
    
    if problem_plots:
        for plot_id, issues in problem_plots:
            report_text += f"- **{plot_id}**: {', '.join(issues)}\n"
    else:
        report_text += "All plots currently meet nutrient targets.\n"
    
    report_text += "\n## Management Plan\n\n"
    
    n_low = sum(1 for s in samples if s['nitrogen'] < optimal_ranges['nitrogen'][0])
    p_low = sum(1 for s in samples if s['phosphorus'] < optimal_ranges['phosphorus'][0])
    k_low = sum(1 for s in samples if s['potassium'] < optimal_ranges['potassium'][0])
    om_low = sum(1 for s in samples if s['organic_matter'] < optimal_ranges['organic_matter'][0])
    
    has_action = False
    if n_low > 0:
        report_text += f"- Apply nitrogen fertilizer to {n_low} plots\n"
        has_action = True
    if p_low > 0:
        report_text += f"- Apply phosphate fertilizer to {p_low} plots\n"
        has_action = True
    if k_low > 0:
        report_text += f"- Apply potassium fertilizer to {k_low} plots\n"
        has_action = True
    if om_low > 0:
        report_text += f"- Add compost or organic mulch to {om_low} plots\n"
        has_action = True
    
    if not has_action:
        report_text += "- Continue current management practices\n"
        report_text += "- Implement annual monitoring program\n"
    
    report_text += "\n## Methods\n\n"
    report_text += "Soil samples collected from 0–6 inch depth using standard spatial grid sampling. "
    report_text += "Nutrient targets follow Cooperative Extension guidelines for vegetable and grain production. "
    report_text += "Normality tested at p > 0.05 under Shapiro-Wilk procedure."
    
    report_file.write_text(report_text)

if __name__ == '__main__':
    main()