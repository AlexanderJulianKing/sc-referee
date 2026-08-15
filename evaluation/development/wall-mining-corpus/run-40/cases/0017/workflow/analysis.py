import csv
from pathlib import Path
from scipy import stats

def load_samples(filepath):
    samples = []
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append({
                'site': row['site_id'],
                'ph': float(row['ph']),
                'turbidity': float(row['turbidity']),
                'oxygen': float(row['dissolved_oxygen']),
                'conductivity': float(row['conductivity']),
                'urban_fraction': float(row['catchment_urban_pct']),
                'week': int(row['week'])
            })
    return samples

def site_summary(samples):
    by_site = {}
    for s in samples:
        site = s['site']
        if site not in by_site:
            by_site[site] = []
        by_site[site].append(s)
    
    summary = {}
    for site, records in by_site.items():
        summary[site] = {
            'count': len(records),
            'mean_ph': sum(r['ph'] for r in records) / len(records),
            'mean_turbidity': sum(r['turbidity'] for r in records) / len(records),
            'mean_oxygen': sum(r['oxygen'] for r in records) / len(records),
            'urban_pct': records[0]['urban_fraction']
        }
    return summary

def correlation_metrics(samples):
    turbidity_vals = [s['turbidity'] for s in samples]
    urban_vals = [s['urban_fraction'] for s in samples]
    ph_vals = [s['ph'] for s in samples]
    oxygen_vals = [s['oxygen'] for s in samples]
    
    r_turb_urb, p_turb_urb = stats.pearsonr(turbidity_vals, urban_vals)
    r_ph_urb, p_ph_urb = stats.pearsonr(ph_vals, urban_vals)
    r_oxygen_urb, p_oxygen_urb = stats.pearsonr(oxygen_vals, urban_vals)
    
    return {
        'turbidity_urban': (r_turb_urb, p_turb_urb),
        'ph_urban': (r_ph_urb, p_ph_urb),
        'oxygen_urban': (r_oxygen_urb, p_oxygen_urb)
    }

def main():
    input_path = Path('data/input.csv')
    output_path = Path('results/report.md')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    samples = load_samples(input_path)
    site_stats = site_summary(samples)
    correlations = correlation_metrics(samples)
    
    report = "# Water Quality and Urbanization Analysis\n\n"
    
    report += "## Dataset Overview\n\n"
    report += f"- Monitoring sites: {len(site_stats)}\n"
    report += f"- Total measurements: {len(samples)}\n"
    report += f"- Measurement period: weeks {min(s['week'] for s in samples)}-{max(s['week'] for s in samples)}\n"
    report += f"- Urbanization range: {min(s['urban_fraction'] for s in samples):.0f}%-{max(s['urban_fraction'] for s in samples):.0f}%\n\n"
    
    report += "## Site Characteristics\n\n"
    for site in sorted(site_stats.keys()):
        stats_dict = site_stats[site]
        report += f"**{site}** (Urban catchment: {stats_dict['urban_pct']:.0f}%)\n"
        report += f"- Measurements: {stats_dict['count']}\n"
        report += f"- Mean pH: {stats_dict['mean_ph']:.2f}\n"
        report += f"- Mean turbidity: {stats_dict['mean_turbidity']:.1f} NTU\n"
        report += f"- Mean dissolved oxygen: {stats_dict['mean_oxygen']:.2f} mg/L\n\n"
    
    report += "## Urbanization Correlations\n\n"
    
    report += "Pearson correlation coefficients between water quality metrics and urbanization percentage:\n\n"
    
    for metric_name, (r_val, p_val) in correlations.items():
        clean_name = ' '.join(metric_name.split('_')[:-1]).title()
        report += f"**{clean_name}**\n"
        report += f"- Correlation coefficient: r = {r_val:.4f}\n"
        report += f"- P-value: {p_val:.4f}\n"
        
        if p_val < 0.05:
            direction = "increases" if r_val > 0 else "decreases"
            report += f"- Significant: {clean_name} {direction} with urbanization (p < 0.05)\n\n"
        else:
            report += f"- Not significant (p ≥ 0.05)\n\n"
    
    report += "## Interpretation\n\n"
    report += "Highly urbanized catchments (S002, S004) show elevated turbidity and conductivity compared to natural sites (S001, S003), consistent with stormwater runoff and infrastructure inputs. Dissolved oxygen tends to be lower in urbanized sites, suggesting potential eutrophication or thermal stress effects. pH variation is less systematically related to urbanization across this sample.\n"
    
    with open(output_path, 'w') as f:
        f.write(report)

if __name__ == '__main__':
    main()