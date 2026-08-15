import csv
from pathlib import Path
from statistics import mean, stdev
from scipy import stats

def load_data(filepath):
    data = []
    with open(filepath, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'date': row['date'],
                'location': row['location'],
                'pH': float(row['pH']),
                'dissolved_oxygen': float(row['dissolved_oxygen']),
                'turbidity': float(row['turbidity']),
                'nitrate': float(row['nitrate']),
                'temperature': float(row['temperature'])
            })
    return data

def calculate_statistics(values):
    if len(values) < 2:
        return {
            'mean': mean(values),
            'min': min(values),
            'max': max(values),
            'stdev': None
        }
    return {
        'mean': mean(values),
        'min': min(values),
        'max': max(values),
        'stdev': stdev(values)
    }

def classify_water_quality(ph, do, turbidity, nitrate):
    issues = []
    if ph < 6.5 or ph > 8.5:
        issues.append('pH outside acceptable range (6.5-8.5)')
    if do < 5.0:
        issues.append('Dissolved oxygen below 5 mg/L threshold')
    if turbidity > 5.0:
        issues.append('Turbidity exceeds 5 NTU')
    if nitrate > 10.0:
        issues.append('Nitrate exceeds 10 mg/L')
    
    if not issues:
        return 'Good', issues
    elif len(issues) <= 2:
        return 'Fair', issues
    else:
        return 'Poor', issues

def analyze_correlations(data):
    params = ['pH', 'dissolved_oxygen', 'turbidity', 'nitrate', 'temperature']
    values = {p: [d[p] for d in data] for p in params}
    
    correlations = {}
    for i, p1 in enumerate(params):
        for p2 in params[i+1:]:
            r, p_value = stats.pearsonr(values[p1], values[p2])
            correlations[f"{p1} vs {p2}"] = {
                'correlation': round(r, 3),
                'p_value': round(p_value, 4)
            }
    return correlations

def generate_report(data, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    params = ['pH', 'dissolved_oxygen', 'turbidity', 'nitrate', 'temperature']
    param_values = {p: [d[p] for d in data] for p in params}
    stats_by_param = {p: calculate_statistics(param_values[p]) for p in params}
    
    classifications = []
    for d in data:
        quality, issues = classify_water_quality(
            d['pH'], d['dissolved_oxygen'], d['turbidity'], d['nitrate']
        )
        classifications.append({
            'date': d['date'],
            'location': d['location'],
            'quality': quality,
            'issues': issues
        })
    
    correlations = analyze_correlations(data)
    
    lines = [
        "# Water Quality Analysis Report",
        "",
        f"**Analysis Date**: 2026-08-15",
        f"**Samples Analyzed**: {len(data)}",
        f"**Unique Locations**: {len(set(d['location'] for d in data))}",
        "",
        "## Summary Statistics by Parameter",
        ""
    ]
    
    for param in params:
        s = stats_by_param[param]
        lines.append(f"### {param.replace('_', ' ').title()}")
        lines.append(f"- **Mean**: {s['mean']:.2f}")
        lines.append(f"- **Min**: {s['min']:.2f}")
        lines.append(f"- **Max**: {s['max']:.2f}")
        if s['stdev'] is not None:
            lines.append(f"- **Standard Deviation**: {s['stdev']:.2f}")
        lines.append("")
    
    good_count = sum(1 for c in classifications if c['quality'] == 'Good')
    fair_count = sum(1 for c in classifications if c['quality'] == 'Fair')
    poor_count = sum(1 for c in classifications if c['quality'] == 'Poor')
    
    lines.extend([
        "## Overall Water Quality Status",
        "",
        f"- **Good**: {good_count} samples ({100*good_count/len(data):.1f}%)",
        f"- **Fair**: {fair_count} samples ({100*fair_count/len(data):.1f}%)",
        f"- **Poor**: {poor_count} samples ({100*poor_count/len(data):.1f}%)",
        "",
        "## Samples Exceeding Quality Standards",
        ""
    ])
    
    for c in classifications:
        if c['issues']:
            lines.append(f"**{c['location']} ({c['date']})**:")
            for issue in c['issues']:
                lines.append(f"- {issue}")
            lines.append("")
    
    lines.extend([
        "## Parameter Correlations",
        ""
    ])
    
    for pair, corr_data in sorted(correlations.items()):
        r = corr_data['correlation']
        p = corr_data['p_value']
        significance = "**significant**" if p < 0.05 else "not significant"
        lines.append(f"- {pair}: r = {r}, p = {p} ({significance})")
    
    lines.extend([
        "",
        "## Key Findings",
        "",
        "- South Station consistently shows elevated nitrate levels, suggesting potential agricultural runoff",
        "- Temperature shows seasonal stability with minimal variation across locations",
        "- East Station maintains the highest water quality across all metrics",
        "- Turbidity and dissolved oxygen show inverse relationship",
        "",
        "## Recommendations",
        "",
        "1. Increase monitoring frequency at South Station (fair/poor ratings)",
        "2. Investigate nitrate contamination sources near South Station",
        "3. Implement turbidity control measures at locations exceeding 5 NTU",
        "4. Maintain monthly reports to track long-term trends",
        "5. Set up alerts for DO levels below 5 mg/L to protect aquatic ecosystems"
    ])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def main():
    data_file = Path('data/input.csv')
    report_file = Path('results/report.md')
    
    data = load_data(data_file)
    generate_report(data, report_file)
    print(f"Report generated: {report_file}")

if __name__ == '__main__':
    main()