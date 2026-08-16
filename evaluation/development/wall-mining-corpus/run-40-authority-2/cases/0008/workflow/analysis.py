import csv
from pathlib import Path
from scipy import stats


def load_seed_data(csv_path):
    heritage_weights = []
    modern_weights = []
    
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            weight = float(row['weight_mg'])
            if row['variety'] == 'Heritage':
                heritage_weights.append(weight)
            else:
                modern_weights.append(weight)
    
    return heritage_weights, modern_weights


def compute_statistics(values):
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std = variance ** 0.5
    return mean, std, min(values), max(values)


def generate_report(heritage_weights, modern_weights, t_stat, p_value):
    h_mean, h_std, h_min, h_max = compute_statistics(heritage_weights)
    m_mean, m_std, m_min, m_max = compute_statistics(modern_weights)
    
    significance = "is" if p_value < 0.05 else "is not"
    
    report = f"""# Seed Weight Analysis: Heritage vs Modern Bean Varieties

## Overview

This analysis compares seed weights between heritage and modern bean varieties to evaluate morphological differences in commercial cultivars.

## Sample Information

- Heritage variety samples: {len(heritage_weights)}
- Modern variety samples: {len(modern_weights)}
- Total seeds analyzed: {len(heritage_weights) + len(modern_weights)}

## Descriptive Results

### Heritage Variety
- Mean: {h_mean:.2f} mg
- Std Dev: {h_std:.2f} mg
- Range: {h_min:.2f}–{h_max:.2f} mg

### Modern Variety
- Mean: {m_mean:.2f} mg
- Std Dev: {m_std:.2f} mg
- Range: {m_min:.2f}–{m_max:.2f} mg

## Statistical Analysis

An independent samples t-test was conducted to evaluate whether mean seed weights differ between the two varieties.

**Test Results:**
- t-statistic: {t_stat:.4f}
- p-value: {p_value:.4f}
- Mean difference: {h_mean - m_mean:.2f} mg

## Conclusion

The mean seed weight for heritage beans ({h_mean:.2f} mg) {significance} significantly different from modern beans ({m_mean:.2f} mg) at α = 0.05.
"""
    return report


def main():
    input_path = Path("data/input.csv")
    output_path = Path("results/report.md")
    output_path.parent.mkdir(exist_ok=True)
    
    heritage_weights, modern_weights = load_seed_data(input_path)
    t_stat, p_value = stats.ttest_ind(heritage_weights, modern_weights)
    
    report = generate_report(heritage_weights, modern_weights, t_stat, p_value)
    output_path.write_text(report)


if __name__ == "__main__":
    main()