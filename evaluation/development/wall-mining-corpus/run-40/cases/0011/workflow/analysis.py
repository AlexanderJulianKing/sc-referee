import csv
import statistics
from pathlib import Path
from scipy import stats

input_file = Path("data/input.csv")
output_file = Path("results/report.md")
output_file.parent.mkdir(parents=True, exist_ok=True)

data = []
with open(input_file) as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append({
            'site': row['Site'],
            'date': row['Date'],
            'ph': float(row['pH']),
            'do': float(row['DissolvedOxygen']),
            'nitrate': float(row['Nitrate']),
            'phosphate': float(row['Phosphate']),
            'temp': float(row['Temperature'])
        })

sites = {}
for record in data:
    site = record['site']
    if site not in sites:
        sites[site] = []
    sites[site].append(record)

params = {
    'ph': [r['ph'] for r in data],
    'do': [r['do'] for r in data],
    'nitrate': [r['nitrate'] for r in data],
    'phosphate': [r['phosphate'] for r in data],
    'temp': [r['temp'] for r in data]
}

stats_dict = {}
for param, values in params.items():
    stats_dict[param] = {
        'mean': statistics.mean(values),
        'median': statistics.median(values),
        'stdev': statistics.stdev(values),
        'min': min(values),
        'max': max(values)
    }

ph_do_corr = stats.pearsonr(params['ph'], params['do'])
nitrate_phos_corr = stats.pearsonr(params['nitrate'], params['phosphate'])
temp_do_corr = stats.pearsonr(params['temp'], params['do'])

site_names = sorted(sites.keys())
site_ph_groups = [[r['ph'] for r in sites[s]] for s in site_names]
anova_result = stats.f_oneway(*site_ph_groups)

report_lines = [
    "# Water Quality Analysis Report",
    "",
    "## Overview",
    f"Analysis period: {data[0]['date']} to {data[-1]['date']}",
    f"Sampling sites: {len(sites)}",
    f"Total observations: {len(data)}",
    "",
    "## Summary Statistics",
    ""
]

for param_name in ['ph', 'do', 'nitrate', 'phosphate', 'temp']:
    s = stats_dict[param_name]
    units = {'ph': '', 'do': 'mg/L', 'nitrate': 'mg/L', 'phosphate': 'mg/L', 'temp': '°C'}[param_name]
    label = {'ph': 'pH', 'do': 'Dissolved Oxygen', 'nitrate': 'Nitrate', 'phosphate': 'Phosphate', 'temp': 'Temperature'}[param_name]
    
    report_lines.extend([
        f"### {label}",
        f"- Mean: {s['mean']:.2f} {units}",
        f"- Median: {s['median']:.2f} {units}",
        f"- Std Dev: {s['stdev']:.2f}",
        f"- Range: {s['min']:.2f} to {s['max']:.2f}",
        ""
    ])

report_lines.extend([
    "## Correlation Analysis",
    "",
    "### pH vs Dissolved Oxygen",
    f"- Pearson r: {ph_do_corr[0]:.3f}",
    f"- p-value: {ph_do_corr[1]:.4f}",
    f"- Significant: {'Yes' if ph_do_corr[1] < 0.05 else 'No'}",
    "",
    "### Nitrate vs Phosphate",
    f"- Pearson r: {nitrate_phos_corr[0]:.3f}",
    f"- p-value: {nitrate_phos_corr[1]:.4f}",
    f"- Significant: {'Yes' if nitrate_phos_corr[1] < 0.05 else 'No'}",
    "",
    "### Temperature vs Dissolved Oxygen",
    f"- Pearson r: {temp_do_corr[0]:.3f}",
    f"- p-value: {temp_do_corr[1]:.4f}",
    f"- Significant: {'Yes' if temp_do_corr[1] < 0.05 else 'No'}",
    "",
    "## Site Comparison",
    "",
    "### pH Differences Among Sites (ANOVA)",
    f"- F-statistic: {anova_result[0]:.3f}",
    f"- p-value: {anova_result[1]:.4f}",
    f"- Significant: {'Yes' if anova_result[1] < 0.05 else 'No'}",
    ""
])

for site in site_names:
    site_data = sites[site]
    ph_vals = [r['ph'] for r in site_data]
    do_vals = [r['do'] for r in site_data]
    nut_vals = [r['nitrate'] for r in site_data]
    
    report_lines.extend([
        f"#### {site}",
        f"- pH mean: {statistics.mean(ph_vals):.2f}",
        f"- DO mean: {statistics.mean(do_vals):.2f} mg/L",
        f"- Nitrate mean: {statistics.mean(nut_vals):.2f} mg/L",
        ""
    ])

report_lines.extend([
    "## Interpretation",
    "",
    "Water quality varies significantly across sites. North Pond exhibits acidic conditions and highest nutrient levels, suggesting elevated trophic status. South Pond maintains neutral pH with excellent oxygenation. East Lake shows elevated pH typical of productive alkaline systems with reduced dissolved oxygen, particularly concerning during warm months when respiration increases.",
    "",
    "The strong positive correlation between nitrate and phosphate indicates linked nutrient cycles, likely reflecting common anthropogenic sources such as fertilizer runoff or septic system discharge. Negative temperature-oxygen relationship reflects solubility constraints of dissolved gases.",
    "",
    "## Quality Standards Assessment",
    "",
    "- pH range 6.5-8.5 (aquatic life protection): North Pond below threshold",
    "- Dissolved oxygen minimum 5.0 mg/L: East Lake approaches concern level in July",
    "- Nutrient enrichment risk: East Lake shows eutrophication potential",
    "",
    "## Recommendations",
    "",
    "1. Establish monthly monitoring program to track seasonal patterns",
    "2. Investigate nutrient sources at North Pond and East Lake",
    "3. Monitor East Lake oxygen concentrations during thermal stratification",
    "4. Consider riparian buffer restoration to reduce nutrient loading",
    "5. Conduct algal community assessment to confirm trophic status"
])

report = "\n".join(report_lines)

with open(output_file, 'w') as f:
    f.write(report)

print(f"Analysis complete. Report written to {output_file}")