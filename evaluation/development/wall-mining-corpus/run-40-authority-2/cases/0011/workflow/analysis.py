import csv
import statistics
from scipy import stats

def load_cognitive_data(filepath):
    records = []
    with open(filepath, 'r') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            records.append({
                'id': row['participant_id'],
                'group': row['exercise_status'],
                'latency': float(row['response_time_ms'])
            })
    return records

def main():
    records = load_cognitive_data('data/input.csv')
    
    active_times = [r['latency'] for r in records if r['group'] == 'Exercise']
    sedentary_times = [r['latency'] for r in records if r['group'] == 'NoExercise']
    
    if len(active_times) < 2 or len(sedentary_times) < 2:
        raise ValueError("Insufficient data in one or both groups")
    
    mean_active = statistics.mean(active_times)
    sd_active = statistics.stdev(active_times)
    mean_sedentary = statistics.mean(sedentary_times)
    sd_sedentary = statistics.stdev(sedentary_times)
    
    t_stat, p_val = stats.ttest_ind(active_times, sedentary_times)
    
    sig_marker = "p < .05" if p_val < 0.05 else "p >= .05"
    effect_direction = "faster" if mean_active < mean_sedentary else "slower"
    
    report = f"""# Cognitive Processing Speed by Exercise Status

## Objective
To evaluate whether regular physical exercise is associated with faster cognitive processing, as indicated by response latencies in a computerized reaction time test.

## Methodology
Participants completed a standardized cognitive test measuring reaction time to visual stimuli. Participants were classified into two groups based on self-reported exercise frequency.

## Sample Characteristics
- Exercise group (≥3 times per week): {len(active_times)} participants
- No-exercise group (<1 time per week): {len(sedentary_times)} participants

## Descriptive Statistics

| Group | N | Mean (ms) | SD (ms) |
|-------|---|-----------|---------|
| Exercise | {len(active_times)} | {mean_active:.2f} | {sd_active:.2f} |
| No-Exercise | {len(sedentary_times)} | {mean_sedentary:.2f} | {sd_sedentary:.2f} |
| Difference | — | {abs(mean_active - mean_sedentary):.2f} | — |

## Statistical Analysis

Independent samples t-test comparing response latencies between groups:

- **t-statistic**: {t_stat:.3f}
- **p-value**: {p_val:.4f}
- **Significance level**: {sig_marker}
- **Degrees of freedom**: {len(active_times) + len(sedentary_times) - 2}

## Results

The exercise group demonstrated {effect_direction} response times (M = {mean_active:.1f} ms, SD = {sd_active:.1f}) compared to the no-exercise group (M = {mean_sedentary:.1f} ms, SD = {sd_sedentary:.1f}).

The independent samples t-test {"revealed a statistically significant difference between groups" if p_val < 0.05 else "did not reveal a statistically significant difference between groups"} ({sig_marker}).

## Interpretation

{"The results provide evidence that regular exercise is associated with improved cognitive processing speed, supporting the hypothesis that physical activity enhances executive function." if p_val < 0.05 and mean_active < mean_sedentary else "No statistically significant association between exercise status and cognitive processing speed was detected in this sample."}

## Conclusion

{"Regular physical exercise shows a measurable association with faster cognitive response times, consistent with neuroscientific literature on aerobic fitness benefits." if p_val < 0.05 and mean_active < mean_sedentary else "Further investigation with larger samples or additional cognitive measures may be warranted to clarify the relationship between exercise and processing speed."}
"""
    
    with open('results/report.md', 'w') as f:
        f.write(report)

if __name__ == '__main__':
    main()