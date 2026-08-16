import csv
import statistics
from pathlib import Path
from scipy import stats

def load_samples(input_file):
    """Load water quality samples from CSV."""
    samples = []
    with open(input_file, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append(row)
    return samples

def parse_measurements(samples):
    """Extract nitrate measurements by facility."""
    upstream = []
    downstream = []
    
    for sample in samples:
        facility = sample['facility'].strip()
        nitrate_level = float(sample['nitrate_ppm'])
        
        if facility == 'Upstream':
            upstream.append(nitrate_level)
        elif facility == 'Downstream':
            downstream.append(nitrate_level)
    
    return upstream, downstream

def compute_statistics(values):
    """Calculate descriptive statistics."""
    if not values:
        return None
    return {
        'count': len(values),
        'mean': statistics.mean(values),
        'stdev': statistics.stdev(values) if len(values) > 1 else 0.0,
        'min': min(values),
        'max': max(values),
        'median': statistics.median(values)
    }

def generate_report(upstream, downstream, statistic, p_value):
    """Create markdown report."""
    stats_up = compute_statistics(upstream)
    stats_down = compute_statistics(downstream)
    
    report = "# Water Quality Comparison Report\n\n"
    report += "## Overview\n"
    report += "Analysis of nitrate contamination across two treatment facilities.\n\n"
    
    report += "## Sample Sizes\n"
    report += f"- Upstream facility: {stats_up['count']} samples\n"
    report += f"- Downstream facility: {stats_down['count']} samples\n\n"
    
    report += "## Upstream Facility Statistics\n"
    report += f"- Mean: {stats_up['mean']:.2f} ppm\n"
    report += f"- Median: {stats_up['median']:.2f} ppm\n"
    report += f"- Std Dev: {stats_up['stdev']:.2f} ppm\n"
    report += f"- Range: [{stats_up['min']:.2f}, {stats_up['max']:.2f}]\n\n"
    
    report += "## Downstream Facility Statistics\n"
    report += f"- Mean: {stats_down['mean']:.2f} ppm\n"
    report += f"- Median: {stats_down['median']:.2f} ppm\n"
    report += f"- Std Dev: {stats_down['stdev']:.2f} ppm\n"
    report += f"- Range: [{stats_down['min']:.2f}, {stats_down['max']:.2f}]\n\n"
    
    report += "## Hypothesis Test (Mann-Whitney U)\n"
    report += f"- U statistic: {statistic:.2f}\n"
    report += f"- p-value: {p_value:.4f}\n"
    report += f"- Significance level: α = 0.05\n\n"
    
    report += "## Conclusion\n"
    if p_value < 0.05:
        diff = stats_down['mean'] - stats_up['mean']
        direction = "higher" if diff > 0 else "lower"
        report += f"The downstream facility shows significantly {direction} nitrate levels "
        report += f"than the upstream facility (p = {p_value:.4f}). "
        report += f"Mean difference: {abs(diff):.2f} ppm.\n"
    else:
        report += f"No statistically significant difference in nitrate levels between "
        report += f"the two facilities was detected (p = {p_value:.4f}).\n"
    
    return report

def main():
    input_path = Path('data/input.csv')
    output_path = Path('results/report.md')
    
    samples = load_samples(input_path)
    upstream, downstream = parse_measurements(samples)
    
    statistic, p_value = stats.mannwhitneyu(upstream, downstream, alternative='two-sided')
    
    report = generate_report(upstream, downstream, statistic, p_value)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

if __name__ == '__main__':
    main()
