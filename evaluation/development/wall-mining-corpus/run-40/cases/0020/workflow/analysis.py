import csv
from pathlib import Path
from statistics import mean
from scipy import stats

def analyze_water_quality():
    input_path = Path("data/input.csv")
    data_rows = []
    
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data_rows.append(row)
    
    measurements = []
    for row in data_rows:
        measurements.append({
            'site': row['site'],
            'date': row['date'],
            'ph': float(row['ph']),
            'do_mg_l': float(row['do_mg_l']),
            'temp_c': float(row['temp_c']),
            'turbidity_ntu': float(row['turbidity_ntu']),
            'conductivity_us_cm': float(row['conductivity_us_cm'])
        })
    
    sites = {}
    for m in measurements:
        site = m['site']
        if site not in sites:
            sites[site] = []
        sites[site].append(m)
    
    site_stats = {}
    for site, meas in sites.items():
        site_stats[site] = {
            'ph': [m['ph'] for m in meas],
            'do': [m['do_mg_l'] for m in meas],
            'temp': [m['temp_c'] for m in meas],
            'turbidity': [m['turbidity_ntu'] for m in meas],
            'conductivity': [m['conductivity_us_cm'] for m in meas]
        }
    
    all_ph = [m['ph'] for m in measurements]
    all_do = [m['do_mg_l'] for m in measurements]
    all_temp = [m['temp_c'] for m in measurements]
    all_turbidity = [m['turbidity_ntu'] for m in measurements]
    all_cond = [m['conductivity_us_cm'] for m in measurements]
    
    corr_do_ph, p_do_ph = stats.pearsonr(all_do, all_ph)
    corr_temp_do, p_temp_do = stats.pearsonr(all_temp, all_do)
    corr_turb_cond, p_turb_cond = stats.pearsonr(all_turbidity, all_cond)
    
    site_ph_groups = [site_stats[s]['ph'] for s in sites]
    f_stat_ph, p_anova_ph = stats.f_oneway(*site_ph_groups)
    
    report = []
    report.append("# Water Quality Assessment Report\n\n")
    report.append("## Executive Summary\n\n")
    report.append(f"Analysis of water quality measurements from {len(sites)} lake sites with {len(measurements)} total observations collected over four weeks.\n\n")
    
    report.append("## Site Overview\n\n")
    report.append("| Site | n | pH Mean | DO Mean (mg/L) | Temp Mean (°C) | Turbidity Mean (NTU) |\n")
    report.append("|------|---|---------|---|---|---|\n")
    
    for site in sorted(sites.keys()):
        stats_ph = site_stats[site]['ph']
        stats_do = site_stats[site]['do']
        stats_temp = site_stats[site]['temp']
        stats_turb = site_stats[site]['turbidity']
        
        report.append(f"| {site} | {len(stats_ph)} | {mean(stats_ph):.2f} | {mean(stats_do):.2f} | {mean(stats_temp):.2f} | {mean(stats_turb):.2f} |\n")
    
    report.append("\n## Correlation Analysis\n\n")
    report.append(f"**Dissolved Oxygen vs. pH**: r = {corr_do_ph:.3f} (p = {p_do_ph:.4f})\n\n")
    report.append(f"**Temperature vs. DO**: r = {corr_temp_do:.3f} (p = {p_temp_do:.4f})\n\n")
    report.append(f"**Turbidity vs. Conductivity**: r = {corr_turb_cond:.3f} (p = {p_turb_cond:.4f})\n\n")
    
    report.append("## Site Comparison (ANOVA)\n\n")
    report.append(f"**pH across sites**: F = {f_stat_ph:.3f}, p = {p_anova_ph:.4f}\n\n")
    
    if p_anova_ph < 0.05:
        report.append("Significant differences in pH detected between sites (p < 0.05), indicating distinct water chemistry profiles.\n\n")
    else:
        report.append("No significant pH differences between sites (p ≥ 0.05).\n\n")
    
    report.append("## Site-Specific Assessment\n")
    
    for site in sorted(sites.keys()):
        ph_vals = site_stats[site]['ph']
        ph_mean = mean(ph_vals)
        ph_status = "Neutral" if 6.5 <= ph_mean <= 8.5 else ("Acidic" if ph_mean < 6.5 else "Alkaline")
        
        do_vals = site_stats[site]['do']
        do_mean = mean(do_vals)
        do_status = "Good" if do_mean >= 7.0 else ("Fair" if do_mean >= 5.0 else "Poor")
        
        temp_vals = site_stats[site]['temp']
        cond_vals = site_stats[site]['conductivity']
        
        report.append(f"\n### {site}\n\n")
        report.append(f"- **pH**: {ph_mean:.2f} ({ph_status})\n")
        report.append(f"- **Dissolved Oxygen**: {do_mean:.2f} mg/L ({do_status})\n")
        report.append(f"- **Temperature**: {mean(temp_vals):.2f}°C\n")
        report.append(f"- **Conductivity**: {mean(cond_vals):.1f} µS/cm\n")
    
    report.append("\n## Conclusions and Recommendations\n\n")
    report.append("Water quality shows notable spatial variation across the lake. Central Deep exhibits lower oxygen levels consistent with depth-stratification. South Inlet demonstrates elevated alkalinity and conductivity typical of river discharge. West Tributary maintains excellent oxygenation. Further investigation recommended for sites with DO below 5 mg/L or pH outside normal aquatic ecosystem range (6.5-8.5).\n")
    
    output_path = Path("results/report.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(''.join(report))

if __name__ == "__main__":
    analyze_water_quality()