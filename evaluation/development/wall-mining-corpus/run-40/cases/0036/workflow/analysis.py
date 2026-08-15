import csv
from pathlib import Path
from statistics import mean, stdev, median

def load_data(filepath):
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'batch_id': row['batch_id'],
                'material_type': row['material_type'],
                'contamination_percent': float(row['contamination_percent']),
                'batch_date': row['batch_date'],
                'batch_size_kg': float(row['batch_size_kg'])
            })
    return data

def calculate_material_statistics(data):
    materials = {}
    for record in data:
        mat = record['material_type']
        if mat not in materials:
            materials[mat] = []
        materials[mat].append(record['contamination_percent'])
    
    stats_by_material = {}
    for mat, values in materials.items():
        stats_by_material[mat] = {
            'mean': mean(values),
            'median': median(values),
            'stdev': stdev(values) if len(values) > 1 else 0.0,
            'min': min(values),
            'max': max(values),
            'count': len(values)
        }
    return stats_by_material

def identify_nonconforming(data, threshold=3.0):
    return [r for r in data if r['contamination_percent'] > threshold]

def generate_report(data, material_stats, nonconforming, threshold):
    report = "# Recycled Material Contamination Analysis\n\n"
    report += "## Executive Summary\n\n"
    report += f"Analysis of {len(data)} material batches processed in January-February 2026.\n"
    compliance_rate = (len(data) - len(nonconforming)) / len(data) * 100
    report += f"Overall contamination compliance rate: {compliance_rate:.1f}%\n\n"
    
    report += "## Quality Metrics by Material Type\n\n"
    for mat in sorted(material_stats.keys()):
        s = material_stats[mat]
        report += f"### {mat}\n"
        report += f"- Sample count: {s['count']}\n"
        report += f"- Mean contamination: {s['mean']:.2f}%\n"
        report += f"- Median contamination: {s['median']:.2f}%\n"
        report += f"- Standard deviation: {s['stdev']:.2f}%\n"
        report += f"- Range: {s['min']:.2f}% to {s['max']:.2f}%\n\n"
    
    report += "## Non-Conforming Batches\n\n"
    report += f"Quality threshold: {threshold}% contamination\n"
    report += f"Non-conforming batches: {len(nonconforming)}\n\n"
    
    if nonconforming:
        report += "| Batch ID | Material | Contamination | Date | Size (kg) |\n"
        report += "|----------|----------|---------------|------|----------|\n"
        for r in sorted(nonconforming, key=lambda x: x['contamination_percent'], reverse=True):
            report += f"| {r['batch_id']} | {r['material_type']} | {r['contamination_percent']:.1f}% | {r['batch_date']} | {r['batch_size_kg']:.0f} |\n"
    else:
        report += "All batches passed contamination threshold.\n"
    
    report += "\n## Recommendations\n\n"
    worst_mat = max(material_stats.items(), key=lambda x: x[1]['mean'])
    report += f"1. {worst_mat[0]} shows highest average contamination ({worst_mat[1]['mean']:.2f}%). "
    report += "Review input material sourcing and sorting equipment settings.\n"
    report += f"2. Implement enhanced QC procedures for batches approaching {threshold}% threshold.\n"
    report += "3. Continue current procedures for compliant material streams.\n"
    
    return report

def main():
    data_path = Path('data/input.csv')
    report_path = Path('results/report.md')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = load_data(data_path)
    material_stats = calculate_material_statistics(data)
    threshold = 3.0
    nonconforming = identify_nonconforming(data, threshold)
    
    report = generate_report(data, material_stats, nonconforming, threshold)
    report_path.write_text(report)

if __name__ == '__main__':
    main()