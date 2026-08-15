import csv
import statistics
from pathlib import Path
from scipy import stats

def analyze_noise_data():
    """Analyze office background noise levels across locations and times."""
    
    input_file = Path("data/input.csv")
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    
    # Read data
    data = []
    with open(input_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'timestamp': row['timestamp'],
                'location': row['location'],
                'noise_db': float(row['noise_db']),
                'hour': int(row['hour'])
            })
    
    # Organize by location
    by_location = {}
    for record in data:
        loc = record['location']
        if loc not in by_location:
            by_location[loc] = []
        by_location[loc].append(record)
    
    # Calculate statistics by location
    location_stats = {}
    for loc, records in by_location.items():
        levels = [r['noise_db'] for r in records]
        location_stats[loc] = {
            'mean': statistics.mean(levels),
            'stdev': statistics.stdev(levels) if len(levels) > 1 else 0,
            'min': min(levels),
            'max': max(levels),
            'count': len(levels)
        }
    
    # Analyze by hour of day
    by_hour = {}
    for record in data:
        h = record['hour']
        if h not in by_hour:
            by_hour[h] = []
        by_hour[h].append(record['noise_db'])
    
    hour_stats = {}
    for hour in sorted(by_hour.keys()):
        levels = by_hour[hour]
        hour_stats[hour] = {
            'mean': statistics.mean(levels),
            'count': len(levels)
        }
    
    # Linear regression on hour trend
    hours = sorted(by_hour.keys())
    means = [hour_stats[h]['mean'] for h in hours]
    slope, intercept, r_value, p_value, std_err = stats.linregress(hours, means)
    
    # Identify high-noise outliers (> mean + 2*stdev)
    all_levels = [r['noise_db'] for r in data]
    overall_mean = statistics.mean(all_levels)
    overall_stdev = statistics.stdev(all_levels)
    threshold = overall_mean + 2 * overall_stdev
    outliers = [r for r in data if r['noise_db'] > threshold]
    
    # Write report
    report_path = output_dir / "report.md"
    with open(report_path, 'w') as f:
        f.write("# Office Noise Level Analysis Report\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"Analysis of {len(data)} noise measurements across {len(by_location)} office locations. ")
        f.write(f"Overall mean noise level: {overall_mean:.1f} dB (SD: {overall_stdev:.1f}). ")
        f.write(f"Detected {len(outliers)} high-noise events.\n\n")
        
        f.write("## Noise Levels by Location\n\n")
        for loc in sorted(by_location.keys()):
            stats_dict = location_stats[loc]
            f.write(f"### {loc}\n\n")
            f.write(f"- Mean: {stats_dict['mean']:.1f} dB\n")
            f.write(f"- Std Dev: {stats_dict['stdev']:.1f} dB\n")
            f.write(f"- Range: {stats_dict['min']:.1f} - {stats_dict['max']:.1f} dB\n")
            f.write(f"- Measurements: {stats_dict['count']}\n\n")
        
        f.write("## Hourly Trend Analysis\n\n")
        f.write(f"Linear regression: Mean noise = {intercept:.2f} + {slope:.4f} × hour\n")
        f.write(f"R² = {r_value**2:.3f}, p-value = {p_value:.4f}\n\n")
        
        if slope > 0:
            trend_dir = "increase"
        elif slope < 0:
            trend_dir = "decrease"
        else:
            trend_dir = "remain stable"
        
        trend_sig = "statistically significant" if p_value < 0.05 else "not statistically significant"
        f.write(f"Noise levels **{trend_dir}** through the day. The trend is {trend_sig}.\n\n")
        
        f.write("### Hourly Means\n\n")
        for hour in sorted(hour_stats.keys()):
            f.write(f"Hour {hour:02d}:00 - {hour_stats[hour]['mean']:.1f} dB (n={hour_stats[hour]['count']})\n")
        
        f.write("\n## Outlier Detection\n\n")
        f.write(f"Threshold for high-noise events: > {threshold:.1f} dB\n")
        f.write(f"Events detected: {len(outliers)}\n\n")
        if outliers:
            f.write("| Timestamp | Location | Level (dB) |\n")
            f.write("|-----------|----------|------------|\n")
            for outlier in outliers[:10]:
                f.write(f"| {outlier['timestamp']} | {outlier['location']} | {outlier['noise_db']:.1f} |\n")
            if len(outliers) > 10:
                f.write(f"| ... and {len(outliers) - 10} more | | |\n")
        else:
            f.write("No high-noise events detected.\n")
        
        f.write("\n## Recommendations\n\n")
        if slope > 0.05:
            f.write("- Investigate sources of increasing noise throughout the day\n")
        if len(outliers) > len(data) * 0.05:
            f.write("- Implement noise reduction measures in high-noise periods\n")
        
        noisiest = max(location_stats.items(), key=lambda x: x[1]['mean'])
        f.write(f"- Focus acoustic treatment on {noisiest[0]} (highest mean: {noisiest[1]['mean']:.1f} dB)\n")

if __name__ == '__main__':
    analyze_noise_data()