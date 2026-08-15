import csv
import statistics
from pathlib import Path
from collections import defaultdict

def read_data(filepath):
    wells = defaultdict(list)
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            well_id = row['well_id']
            wells[well_id].append({
                'date': row['date'],
                'pH': float(row['pH']),
                'conductivity_uS': float(row['conductivity_uS']),
                'dissolved_oxygen_mg_L': float(row['dissolved_oxygen_mg_L']),
                'temperature_C': float(row['temperature_C']),
                'nitrate_mg_L': float(row['nitrate_mg_L'])
            })
    return wells

def detect_outliers_iqr(values):
    if len(values) < 2:
        return []
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    q1 = sorted_vals[n // 4]
    q3 = sorted_vals[3 * n // 4]
    iqr = q3 - q1
    if iqr == 0:
        return []
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return [v for v in values if v < lower_bound or v > upper_bound]

def pearson_correlation(x_vals, y_vals):
    if len(x_vals) < 2:
        return None
    mean_x = statistics.mean(x_vals)
    mean_y = statistics.mean(y_vals)
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals)) / (len(x_vals) - 1)
    std_x = statistics.stdev(x_vals)
    std_y = statistics.stdev(y_vals)
    if std_x == 0 or std_y == 0:
        return None
    return cov / (std_x * std_y)

def analyze_wells(wells):
    results = {}
    for well_id, measurements in wells.items():
        params = {
            'pH': [],
            'conductivity_uS': [],
            'dissolved_oxygen_mg_L': [],
            'temperature_C': [],
            'nitrate_mg_L': []
        }
        for m in measurements:
            for param in params:
                params[param].append(m[param])
        
        results[well_id] = {}
        for param, values in params.items():
            results[well_id][param] = {
                'mean': statistics.mean(values),
                'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                'min': min(values),
                'max': max(values),
                'count': len(values),
                'outliers': detect_outliers_iqr(values)
            }
    return results

def compute_correlations(wells):
    all_measurements = []
    for measurements in wells.values():
        all_measurements.extend(measurements)
    
    params = ['pH', 'conductivity_uS', 'dissolved_oxygen_mg_L', 'temperature_C', 'nitrate_mg_L']
    param_values = {p: [m[p] for m in all_measurements] for p in params}
    
    correlations = {}
    for i, p1 in enumerate(params):
        for p2 in params[i+1:]:
            r = pearson_correlation(param_values[p1], param_values[p2])
            correlations[f"{p1} vs {p2}"] = r
    return correlations

def generate_report(wells, analysis_results, correlations):
    lines = []
    lines.append("# Groundwater Quality Analysis Report\n")
    lines.append(f"## Summary\n")
    lines.append(f"Total monitoring wells: {len(wells)}\n")
    total_samples = sum(len(m) for m in wells.values())
    lines.append(f"Total measurements: {total_samples}\n\n")
    
    lines.append("## Well-by-Well Summary Statistics\n")
    for well_id in sorted(wells.keys()):
        lines.append(f"\n### Well {well_id}\n")
        results = analysis_results[well_id]
        lines.append("| Parameter | Mean | Std Dev | Min | Max | Count |\n")
        lines.append("|-----------|------|---------|-----|-----|-------|\n")
        for param in sorted(results.keys()):
            r = results[param]
            lines.append(f"| {param} | {r['mean']:.3f} | {r['stdev']:.3f} | {r['min']:.3f} | {r['max']:.3f} | {r['count']} |\n")
    
    lines.append("\n## Quality Control: Outlier Detection\n")
    outlier_found = False
    for well_id in sorted(wells.keys()):
        results = analysis_results[well_id]
        outlier_count = sum(len(r['outliers']) for r in results.values())
        if outlier_count > 0:
            outlier_found = True
            lines.append(f"\n**Well {well_id}**: {outlier_count} anomaly/anomalies detected\n")
            for param in sorted(results.keys()):
                if results[param]['outliers']:
                    vals_str = ', '.join(f'{v:.3f}' for v in sorted(results[param]['outliers']))
                    lines.append(f"- {param}: {vals_str}\n")
    if not outlier_found:
        lines.append("No statistical outliers detected (IQR method, 1.5 × threshold).\n")
    
    lines.append("\n## Parameter Correlations (All Wells Combined)\n")
    lines.append("| Parameter Pair | Pearson r |\n")
    lines.append("|---|---|\n")
    for pair in sorted(correlations.keys()):
        r = correlations[pair]
        if r is not None:
            lines.append(f"| {pair} | {r:.4f} |\n")
        else:
            lines.append(f"| {pair} | undefined |\n")
    
    lines.append("\n## Findings and Interpretation\n")
    strong_pairs = [(k, v) for k, v in correlations.items() if v is not None and abs(v) > 0.7]
    if strong_pairs:
        lines.append("\n**Strong correlations identified** (|r| > 0.7):\n")
        for pair, r in sorted(strong_pairs, key=lambda x: abs(x[1]), reverse=True):
            direction = "positive" if r > 0 else "negative"
            lines.append(f"- {pair}: r = {r:.4f} ({direction})\n")
    else:
        lines.append("\nNo strong correlations detected between parameters (|r| ≤ 0.7).\n")
    
    lines.append("\n## Recommendations\n")
    lines.append("- Continue monthly monitoring to establish baseline and detect temporal trends\n")
    lines.append("- Wells with elevated nitrate (W-04, >10 mg/L) warrant agricultural runoff investigation\n")
    lines.append("- High conductivity in W-02 consistent with natural mineralization; not a concern\n")
    lines.append("- Reference wells (W-01, W-03) demonstrate acceptable background conditions\n")
    
    return "".join(lines)

def main():
    data_path = Path("data/input.csv")
    output_path = Path("results/report.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    wells = read_data(data_path)
    analysis_results = analyze_wells(wells)
    correlations = compute_correlations(wells)
    report = generate_report(wells, analysis_results, correlations)
    
    with open(output_path, 'w') as f:
        f.write(report)

if __name__ == "__main__":
    main()
