import csv
from pathlib import Path
from statistics import mean, stdev
from scipy import stats

input_file = Path("data/input.csv")
output_file = Path("results/report.md")
output_file.parent.mkdir(parents=True, exist_ok=True)

records = []
with open(input_file) as f:
    reader = csv.DictReader(f)
    for row in reader:
        records.append({
            'site': row['site'],
            'date': row['date'],
            'ph': float(row['ph']),
            'do_mg_l': float(row['do_mg_l']),
            'turbidity': float(row['turbidity']),
            'nitrate': float(row['nitrate'])
        })

sites = {}
for rec in records:
    site = rec['site']
    if site not in sites:
        sites[site] = []
    sites[site].append(rec)

report = ["# Water Quality Analysis Report\n\n"]
report.append(f"**Analysis Date:** 2026-08-15  \n")
report.append(f"**Total Samples:** {len(records)}  \n")
report.append(f"**Monitoring Sites:** {len(sites)}\n\n")

report.append("## Site Statistics\n\n")

all_ph = []
all_do = []
all_turb = []
all_nit = []

for site_name in sorted(sites.keys()):
    measurements = sites[site_name]
    
    ph_vals = [m['ph'] for m in measurements]
    do_vals = [m['do_mg_l'] for m in measurements]
    turb_vals = [m['turbidity'] for m in measurements]
    nit_vals = [m['nitrate'] for m in measurements]
    
    all_ph.extend(ph_vals)
    all_do.extend(do_vals)
    all_turb.extend(turb_vals)
    all_nit.extend(nit_vals)
    
    report.append(f"### {site_name}\n\n")
    report.append("| Parameter | Mean | StdDev | Min | Max |\n")
    report.append("|-----------|------|--------|-----|-----|\n")
    
    params = [('pH', ph_vals), ('DO (mg/L)', do_vals), ('Turbidity (NTU)', turb_vals), ('Nitrate (mg/L)', nit_vals)]
    for pname, vals in params:
        avg = mean(vals)
        sd = stdev(vals) if len(vals) > 1 else 0.0
        report.append(f"| {pname} | {avg:.2f} | {sd:.2f} | {min(vals):.2f} | {max(vals):.2f} |\n")
    
    report.append("\n")

report.append("## Overall Analysis\n\n")

report.append(f"**pH Range:** {min(all_ph):.2f} to {max(all_ph):.2f} (mean: {mean(all_ph):.2f})\n\n")
report.append(f"**Dissolved Oxygen:** mean {mean(all_do):.2f} mg/L (range: {min(all_do):.2f}–{max(all_do):.2f})\n\n")
report.append(f"**Turbidity:** mean {mean(all_turb):.2f} NTU (range: {min(all_turb):.2f}–{max(all_turb):.2f})\n\n")
report.append(f"**Nitrate:** mean {mean(all_nit):.2f} mg/L (range: {min(all_nit):.2f}–{max(all_nit):.2f})\n\n")

report.append("## Correlation Matrix\n\n")

corr_ph_do, pval_ph_do = stats.pearsonr(all_ph, all_do)
corr_do_turb, pval_do_turb = stats.pearsonr(all_do, all_turb)
corr_nit_turb, pval_nit_turb = stats.pearsonr(all_nit, all_turb)

report.append(f"| Variables | Correlation | P-value |\n")
report.append(f"|-----------|-------------|----------|\n")
report.append(f"| pH ↔ DO | {corr_ph_do:.3f} | {pval_ph_do:.4f} |\n")
report.append(f"| DO ↔ Turbidity | {corr_do_turb:.3f} | {pval_do_turb:.4f} |\n")
report.append(f"| Nitrate ↔ Turbidity | {corr_nit_turb:.3f} | {pval_nit_turb:.4f} |\n\n")

report.append("## Quality Flags\n\n")

low_do_threshold = 5.0
high_nit_threshold = 10.0

concern_sites = []
for site_name, measurements in sites.items():
    mean_do = mean([m['do_mg_l'] for m in measurements])
    mean_nit = mean([m['nitrate'] for m in measurements])
    
    flags = []
    if mean_do < low_do_threshold:
        flags.append("low DO")
    if mean_nit > high_nit_threshold:
        flags.append("high nitrate")
    
    if flags:
        concern_sites.append(f"{site_name}: {', '.join(flags)}")

if concern_sites:
    report.append("Flagged sites:\n\n")
    for concern in concern_sites:
        report.append(f"- {concern}\n")
else:
    report.append("No sites exceed threshold criteria.\n")

with open(output_file, 'w') as f:
    f.writelines(report)

print("Report generated successfully.")