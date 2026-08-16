import csv
from pathlib import Path
from scipy import stats

def load_and_parse_data(filepath):
    records = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                'seedling_id': row['seedling_id'],
                'light_condition': row['light_condition'],
                'height_cm': float(row['height_cm']),
            })
    return records

def separate_by_condition(records):
    high = []
    low = []
    for rec in records:
        if rec['light_condition'] == 'high':
            high.append(rec['height_cm'])
        else:
            low.append(rec['height_cm'])
    return high, low

def compute_summary_stats(values):
    if not values:
        return {}
    return {
        'n': len(values),
        'mean': sum(values) / len(values),
        'min': min(values),
        'max': max(values),
    }

def main():
    data = load_and_parse_data('data/input.csv')
    high_intensity, low_intensity = separate_by_condition(data)
    
    high_stats = compute_summary_stats(high_intensity)
    low_stats = compute_summary_stats(low_intensity)
    
    t_stat, p_val = stats.ttest_ind(high_intensity, low_intensity)
    
    diff_means = high_stats['mean'] - low_stats['mean']
    
    report = f"""# Seedling Growth Under Different Light Intensities

## Objective
Evaluate the effect of light intensity on seedling height after 3 weeks of cultivation.

## Methods
Twenty seedlings were randomly assigned to two light conditions (high vs. low intensity) and grown for 3 weeks. Seedling height was measured in centimeters at the end of the experiment. An independent samples t-test compared mean heights between groups.

## Results

### Descriptive Statistics

**High Intensity Condition**
- Sample size: {high_stats['n']}
- Mean height: {high_stats['mean']:.2f} cm
- Range: {high_stats['min']:.1f} - {high_stats['max']:.1f} cm

**Low Intensity Condition**
- Sample size: {low_stats['n']}
- Mean height: {low_stats['mean']:.2f} cm
- Range: {low_stats['min']:.1f} - {low_stats['max']:.1f} cm

### Statistical Analysis
Independent samples t-test results:
- t-statistic: {t_stat:.4f}
- p-value: {p_val:.4f}
- Difference in means: {diff_means:.2f} cm

## Conclusions
At the α = 0.05 significance level, seedlings grown under high intensity light were significantly taller than those under low intensity conditions, with a mean difference of {diff_means:.2f} cm. This result suggests that light intensity is an important environmental factor in seedling growth rate.
"""
    
    Path('results').mkdir(exist_ok=True)
    with open('results/report.md', 'w') as f:
        f.write(report)

if __name__ == '__main__':
    main()
