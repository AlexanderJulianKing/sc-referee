from pathlib import Path
from scipy import optimize
import csv
import math
import statistics

def read_data(filepath):
    """Load equipment failure times from CSV."""
    records = []
    with open(filepath) as f:
        for row in csv.DictReader(f):
            records.append(float(row['failure_hours']))
    return records

def fit_weibull_mle(failures):
    """Estimate Weibull parameters using maximum likelihood estimation."""
    n = len(failures)
    
    def objective(shape):
        if shape <= 0:
            return 1e10
        scale = (sum(t**shape for t in failures) / n) ** (1/shape)
        loglik = 0
        loglik += n * math.log(shape) - n * shape * math.log(scale)
        for t in failures:
            loglik += (shape - 1) * math.log(t) - (t/scale)**shape
        return -loglik
    
    res = optimize.minimize_scalar(objective, bounds=(0.1, 10), method='bounded')
    shape = res.x
    scale = (sum(t**shape for t in failures) / n) ** (1/shape)
    return shape, scale

def compute_reliability_metrics(failures, shape, scale):
    """Compute reliability statistics and survival probabilities."""
    from math import gamma
    
    mttf = scale * gamma(1 + 1/shape)
    
    metrics = {
        'count': len(failures),
        'min': min(failures),
        'max': max(failures),
        'mean': statistics.mean(failures),
        'median': statistics.median(failures),
        'stdev': statistics.stdev(failures),
        'mttf': mttf,
        'shape': shape,
        'scale': scale,
    }
    
    survival = {}
    for hours in [100, 500, 1000, 2000, 5000]:
        if hours <= max(failures) * 1.5:
            survival[hours] = math.exp(-(hours/scale)**shape)
    
    metrics['survival'] = survival
    return metrics

def generate_markdown_report(metrics):
    """Generate substantive Markdown report with analysis results."""
    report = f"""# Equipment Reliability Analysis Report

## Data Overview

Analysis of {metrics['count']} equipment units tracked to failure in operating hours.

### Descriptive Statistics

| Metric | Value |
|---|---|
| Minimum Failure Time | {metrics['min']:.0f} hours |
| Maximum Failure Time | {metrics['max']:.0f} hours |
| Mean Failure Time | {metrics['mean']:.1f} hours |
| Median Failure Time | {metrics['median']:.1f} hours |
| Standard Deviation | {metrics['stdev']:.1f} hours |

## Weibull Distribution Fit

Failure times were modeled using a Weibull distribution, the standard distributional choice for reliability engineering applications.

### Estimated Parameters

- **Shape Parameter (α)**: {metrics['shape']:.4f}
- **Scale Parameter (β)**: {metrics['scale']:.1f} hours
- **Mean Time To Failure (MTTF)**: {metrics['mttf']:.1f} hours

### Failure Rate Interpretation

"""
    
    if metrics['shape'] < 0.95:
        report += f"The shape parameter {metrics['shape']:.4f} < 1 indicates a **decreasing failure rate**, characteristic of early-life failures (infant mortality phase). Equipment reliability improves with age."
    elif metrics['shape'] <= 1.05:
        report += f"The shape parameter {metrics['shape']:.4f} ≈ 1 indicates a **constant failure rate**, characteristic of random failures during normal operation (exponential model)."
    else:
        report += f"The shape parameter {metrics['shape']:.4f} > 1 indicates an **increasing failure rate**, characteristic of wear-out failures. Equipment becomes less reliable with time."
    
    report += "\n\n## Reliability Projections\n\n"
    report += "Estimated probability that equipment survives to the specified operating hours:\n\n"
    report += "| Operating Hours | Survival Probability | Failure Probability |\n"
    report += "|---|---|---|\n"
    
    for h in sorted(metrics['survival'].keys()):
        s = metrics['survival'][h]
        f = 1 - s
        report += f"| {h:,} | {s:.2%} | {f:.2%} |\n"
    
    report += f"""
## Key Findings

1. **Expected Service Life**: Equipment operated continuously is expected to fail around {metrics['mttf']:.0f} hours on average.

2. **Reliability Trend**: Based on the fitted shape parameter of {metrics['shape']:.4f}, the equipment exhibits a {'wearout characteristic with increasing failure likelihood over time' if metrics['shape'] > 1 else 'random failure characteristic with constant failure probability over time' if abs(metrics['shape'] - 1) < 0.15 else 'burn-in characteristic with improving reliability during initial operation'}.

3. **Practical Implications**: For operational planning, preventive maintenance should be scheduled before the {int(metrics['mttf'] * 0.7)}-{int(metrics['mttf'] * 0.8)} hour mark to minimize unexpected failures.

## Conclusion

The Weibull model provides a precise characterization of equipment failure behavior, enabling data-driven maintenance scheduling and reliability forecasting for this equipment class.
"""
    
    return report

def main():
    data_path = Path('data/input.csv')
    report_path = Path('results/report.md')
    
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    failures = read_data(data_path)
    shape, scale = fit_weibull_mle(failures)
    metrics = compute_reliability_metrics(failures, shape, scale)
    report = generate_markdown_report(metrics)
    
    with open(report_path, 'w') as f:
        f.write(report)

if __name__ == '__main__':
    main()
