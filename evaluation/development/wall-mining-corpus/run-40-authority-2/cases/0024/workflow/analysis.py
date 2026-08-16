import csv
import statistics
from pathlib import Path
from scipy import stats

def load_and_validate(filepath):
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        records = list(reader)
    
    for record in records:
        record['tasks_completed'] = int(record['tasks_completed'])
        record['days_active'] = int(record['days_active'])
    
    return records

def partition_by_work_mode(records):
    remote = [r for r in records if r['work_mode'] == 'remote']
    onsite = [r for r in records if r['work_mode'] == 'onsite']
    return remote, onsite

def extract_metric(records, metric_name):
    return [int(r[metric_name]) for r in records]

def summary_statistics(values):
    return {
        'count': len(values),
        'average': statistics.mean(values),
        'std': statistics.stdev(values) if len(values) > 1 else 0,
        'minimum': min(values),
        'maximum': max(values),
    }

def generate_report(remote_data, onsite_data):
    remote_tasks = extract_metric(remote_data, 'tasks_completed')
    onsite_tasks = extract_metric(onsite_data, 'tasks_completed')
    
    remote_stats = summary_statistics(remote_tasks)
    onsite_stats = summary_statistics(onsite_tasks)
    
    t_stat, p_val = stats.ttest_ind(remote_tasks, onsite_tasks)
    
    report = []
    report.append("# Work Mode Productivity Analysis\n\n")
    report.append("## Executive Summary\n\n")
    report.append("Analysis of daily task completion rates across remote and in-office employees.\n\n")
    
    report.append("## Remote Workers\n\n")
    report.append(f"**N:** {remote_stats['count']}\n")
    report.append(f"**Mean Tasks:** {remote_stats['average']:.1f}\n")
    report.append(f"**SD:** {remote_stats['std']:.2f}\n")
    report.append(f"**Range:** {remote_stats['minimum']}-{remote_stats['maximum']}\n\n")
    
    report.append("## In-Office Workers\n\n")
    report.append(f"**N:** {onsite_stats['count']}\n")
    report.append(f"**Mean Tasks:** {onsite_stats['average']:.1f}\n")
    report.append(f"**SD:** {onsite_stats['std']:.2f}\n")
    report.append(f"**Range:** {onsite_stats['minimum']}-{onsite_stats['maximum']}\n\n")
    
    report.append("## Statistical Analysis\n\n")
    report.append(f"**t-test result:** t = {t_stat:.4f}, p = {p_val:.4f}\n\n")
    
    if p_val < 0.05:
        report.append("**Conclusion:** Significant difference in productivity between work modes (p < 0.05).\n")
    else:
        report.append("**Conclusion:** No significant difference between work modes (p ≥ 0.05).\n")
    
    return ''.join(report)

def main():
    records = load_and_validate('data/input.csv')
    remote_records, onsite_records = partition_by_work_mode(records)
    report_text = generate_report(remote_records, onsite_records)
    
    Path('results').mkdir(exist_ok=True)
    with open('results/report.md', 'w') as f:
        f.write(report_text)

if __name__ == '__main__':
    main()