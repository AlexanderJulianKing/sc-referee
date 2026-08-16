import csv
import math
from scipy import stats

def load_data(filepath):
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def is_valid(record):
    try:
        score = float(record.get('test_score', ''))
        method = record.get('teaching_method', '').strip()
        return 0 <= score <= 100 and method in ('traditional', 'online')
    except (ValueError, AttributeError):
        return False

def compute_stats(values):
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std = math.sqrt(variance)
    return mean, std

def main():
    records = load_data('data/input.csv')
    valid = [r for r in records if is_valid(r)]
    
    if not valid:
        raise ValueError("No valid records found in input data")
    
    traditional_scores = [float(r['test_score']) for r in valid if r['teaching_method'] == 'traditional']
    online_scores = [float(r['test_score']) for r in valid if r['teaching_method'] == 'online']
    
    if len(traditional_scores) < 2 or len(online_scores) < 2:
        raise ValueError("Each group requires minimum 2 observations")
    
    t_statistic, p_value = stats.ttest_ind(traditional_scores, online_scores)
    
    trad_mean, trad_std = compute_stats(traditional_scores)
    online_mean, online_std = compute_stats(online_scores)
    diff = abs(trad_mean - online_mean)
    
    sig_status = "statistically significant" if p_value < 0.05 else "not statistically significant"
    higher_method = "traditional" if trad_mean > online_mean else "online"
    
    report = f"""# Teaching Method Effectiveness Analysis

## Study Objective
Compare student test performance outcomes between traditional classroom instruction and online learning delivery modalities.

## Methodology
Cross-sectional examination of standardized test scores from {len(valid)} students enrolled in equivalent courses delivered via two instructional methods.

## Sample Characteristics
- Traditional classroom enrollment: {len(traditional_scores)} students
- Online learning enrollment: {len(online_scores)} students
- Total sample size: {len(valid)} students

## Descriptive Findings

### Traditional Classroom Instruction
- Mean test score: {trad_mean:.2f} / 100
- Standard deviation: {trad_std:.2f}
- Sample size: {len(traditional_scores)}

### Online Learning Delivery
- Mean test score: {online_mean:.2f} / 100
- Standard deviation: {online_std:.2f}
- Sample size: {len(online_scores)}

## Statistical Hypothesis Testing
An independent samples t-test was conducted to evaluate differences in mean test performance between instruction methods.

**Test Results:**
- Absolute mean difference: {diff:.2f} points
- t-statistic: {t_statistic:.4f}
- p-value: {p_value:.4f}
- Decision criterion: α = 0.05

## Statistical Conclusion
The observed performance difference of {diff:.2f} points (with the {higher_method} method showing higher achievement) is **{sig_status}** at the 0.05 significance level. This indicates that instructional delivery mode {'does' if p_value < 0.05 else 'does not'} substantially influence student test performance in this academic context.

## Interpretation
The findings suggest that {'traditional classroom instruction may provide' if p_value < 0.05 and trad_mean > online_mean else 'online learning may provide' if p_value < 0.05 else 'both delivery modalities appear comparable in terms of'} measurably {'superior' if p_value < 0.05 else 'equivalent'} learning outcomes.
"""
    
    with open('results/report.md', 'w') as f:
        f.write(report)

if __name__ == '__main__':
    main()
