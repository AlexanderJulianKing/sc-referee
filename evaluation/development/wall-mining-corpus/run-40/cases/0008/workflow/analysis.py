import csv
import statistics
from pathlib import Path
from datetime import datetime
from scipy.stats import linregress

def main():
    input_path = Path("data/input.csv")
    output_path = Path("results/report.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    measurements = {}
    with input_path.open() as f:
        for row in csv.DictReader(f):
            site = row['site']
            if site not in measurements:
                measurements[site] = []
            measurements[site].append({
                'week': int(row['week']),
                'ph': float(row['ph']),
                'do': float(row['dissolved_oxygen_mg_l']),
                'turbidity': float(row['turbidity_ntu']),
                'nitrate': float(row['nitrate_mg_l'])
            })
    
    sites = sorted(measurements.keys())
    
    with output_path.open('w') as f:
        f.write("# Water Quality Monitoring Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"Sites monitored: {', '.join(sites)}\n")
        f.write("Monitoring period: 52 weeks\n\n")
        
        f.write("## Detailed Analysis\n\n")
        
        for site in sites:
            data = sorted(measurements[site], key=lambda x: x['week'])
            write_site_analysis(f, site, data)
        
        f.write("## Quality Standards\n\n")
        f.write("- pH: 6.5–8.5\n")
        f.write("- Dissolved Oxygen: ≥5.0 mg/L\n")
        f.write("- Turbidity: ≤1.0 NTU\n")
        f.write("- Nitrate: ≤10 mg/L\n\n")
        
        compliance = compute_compliance(measurements)
        f.write("## Compliance Results\n\n")
        for site in sites:
            pct = compliance[site]
            f.write(f"- {site}: {pct:.1f}% compliant\n")

def write_site_analysis(f, site, data):
    f.write(f"### {site}\n\n")
    
    f.write("#### Descriptive Statistics\n\n")
    f.write("| Metric | pH | DO (mg/L) | Turbidity (NTU) | Nitrate (mg/L) |\n")
    f.write("|--------|----|----|----|---------|\n")
    
    for metric, func in [("Mean", statistics.mean), ("Median", statistics.median)]:
        row = f"| {metric} |"
        for key in ['ph', 'do', 'turbidity', 'nitrate']:
            vals = [d[key] for d in data]
            row += f" {func(vals):.2f} |"
        f.write(row + "\n")
    
    f.write("\n#### Trend Analysis\n\n")
    
    for label, key in [("pH", 'ph'), ("Dissolved Oxygen", 'do'), ("Nitrate", 'nitrate')]:
        values = [d[key] for d in data]
        x = list(range(len(values)))
        slope, intercept, r_value, p_value, stderr = linregress(x, values)
        
        direction = "increasing" if slope > 0 else "decreasing"
        sig = "p<0.05" if p_value < 0.05 else "p≥0.05"
        f.write(f"- {label}: {direction} trend (slope={slope:.4f}, {sig})\n")
    
    f.write("\n")

def compute_compliance(measurements):
    standards = {
        'ph': (6.5, 8.5),
        'do': (5.0, float('inf')),
        'turbidity': (0, 1.0),
        'nitrate': (0, 10.0)
    }
    
    results = {}
    for site, data in measurements.items():
        compliant = 0
        total = 0
        
        for record in data:
            for param, (min_v, max_v) in standards.items():
                total += 1
                if min_v <= record[param] <= max_v:
                    compliant += 1
        
        results[site] = 100 * compliant / total if total > 0 else 0
    
    return results

if __name__ == "__main__":
    main()
