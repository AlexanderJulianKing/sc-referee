import csv
from pathlib import Path
from statistics import mean, stdev
from collections import defaultdict

def read_water_quality_data(filepath):
    data = []
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'date': row['date'],
                'station': row['station'],
                'pH': float(row['pH']),
                'dissolved_oxygen': float(row['dissolved_oxygen']),
                'temperature': float(row['temperature']),
                'turbidity': float(row['turbidity']),
                'nitrates': float(row['nitrates'])
            })
    return data

def calculate_site_statistics(data):
    by_station = defaultdict(lambda: defaultdict(list))
    
    for record in data:
        station = record['station']
        by_station[station]['pH'].append(record['pH'])
        by_station[station]['dissolved_oxygen'].append(record['dissolved_oxygen'])
        by_station[station]['temperature'].append(record['temperature'])
        by_station[station]['turbidity'].append(record['turbidity'])
        by_station[station]['nitrates'].append(record['nitrates'])
    
    stats = {}
    for station, measurements in by_station.items():
        stats[station] = {}
        for param, values in measurements.items():
            stats[station][param] = {
                'mean': mean(values),
                'stdev': stdev(values) if len(values) > 1 else 0,
                'min': min(values),
                'max': max(values),
                'n': len(values)
            }
    
    return stats

def identify_concerns(stats):
    concerns = []
    
    for station, measurements in stats.items():
        ph_mean = measurements['pH']['mean']
        do_mean = measurements['dissolved_oxygen']['mean']
        turbidity_mean = measurements['turbidity']['mean']
        nitrates_mean = measurements['nitrates']['mean']
        
        if ph_mean < 6.5 or ph_mean > 8.5:
            concerns.append(f"{station}: pH {ph_mean:.2f} outside neutral range (6.5-8.5)")
        
        if do_mean < 5.0:
            concerns.append(f"{station}: Dissolved oxygen {do_mean:.2f} mg/L below 5.0 threshold")
        
        if turbidity_mean > 5.0:
            concerns.append(f"{station}: Turbidity {turbidity_mean:.2f} NTU elevated")
        
        if nitrates_mean > 10.0:
            concerns.append(f"{station}: Nitrates {nitrates_mean:.2f} mg/L exceeds 10 mg/L guideline")
    
    return concerns

def generate_markdown_report(stats, concerns, output_path):
    report = []
    report.append("# River Water Quality Analysis Report")
    report.append("")
    report.append("## Executive Summary")
    report.append("")
    report.append(f"This report presents water quality monitoring results from {len(stats)} river stations.")
    report.append(f"A total of {sum(s['pH']['n'] for s in stats.values())} measurements were analyzed")
    report.append("across multiple parameters including pH, dissolved oxygen, temperature, turbidity, and nitrates.")
    report.append("")
    
    if concerns:
        report.append(f"**{len(concerns)} water quality concerns were identified.**")
    else:
        report.append("**No significant water quality concerns identified.**")
    report.append("")
    
    report.append("## Detailed Measurements by Station")
    report.append("")
    
    for station in sorted(stats.keys()):
        report.append(f"### {station}")
        report.append("")
        report.append("| Parameter | Mean | Std Dev | Min | Max | N |")
        report.append("|-----------|------|---------|-----|-----|---|")
        
        measurements = stats[station]
        for param in ['pH', 'dissolved_oxygen', 'temperature', 'turbidity', 'nitrates']:
            s = measurements[param]
            report.append(f"| {param} | {s['mean']:.2f} | {s['stdev']:.2f} | {s['min']:.2f} | {s['max']:.2f} | {s['n']} |")
        report.append("")
    
    report.append("## Water Quality Concerns")
    report.append("")
    
    if concerns:
        for concern in concerns:
            report.append(f"- {concern}")
    else:
        report.append("No concerns identified. All parameters within acceptable ranges.")
    report.append("")
    
    report.append("## Quality Guidelines Reference")
    report.append("")
    report.append("- **pH**: 6.5-8.5 (neutral to slightly basic)")
    report.append("- **Dissolved Oxygen**: ≥5.0 mg/L (supports aquatic life)")
    report.append("- **Turbidity**: <5.0 NTU (clear water preferred)")
    report.append("- **Nitrates**: <10.0 mg/L (agricultural runoff indicator)")
    report.append("")
    
    report.append("## Recommendations")
    report.append("")
    if concerns:
        report.append("1. Investigate identified concerns at specific stations")
        report.append("2. Increase monitoring frequency in affected areas")
        report.append("3. Review land-use practices upstream of problem stations")
    else:
        report.append("1. Continue routine monitoring to maintain water quality")
        report.append("2. Conduct seasonal analysis to identify temporal patterns")
    report.append("")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(report))

def main():
    input_file = Path('data/input.csv')
    output_file = Path('results/report.md')
    
    data = read_water_quality_data(input_file)
    stats = calculate_site_statistics(data)
    concerns = identify_concerns(stats)
    
    generate_markdown_report(stats, concerns, output_file)
    print(f"Report generated: {output_file}")

if __name__ == '__main__':
    main()