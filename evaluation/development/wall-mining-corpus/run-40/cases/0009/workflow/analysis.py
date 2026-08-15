import csv
from pathlib import Path
from statistics import mean, stdev
from scipy import stats

input_path = Path('data/input.csv')
output_path = Path('results/report.md')

records = []
with open(input_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        records.append({
            'tank': int(row['tank_id']),
            'ph': float(row['ph']),
            'temp_c': float(row['temperature_c']),
            'oxygen_mg_l': float(row['dissolved_oxygen_mg_l']),
            'ammonia_ppm': float(row['ammonia_ppm'])
        })

by_tank = {}
for rec in records:
    tid = rec['tank']
    if tid not in by_tank:
        by_tank[tid] = []
    by_tank[tid].append(rec)

tank_stats = {}
for tid, measurements in by_tank.items():
    phs = [m['ph'] for m in measurements]
    temps = [m['temp_c'] for m in measurements]
    oxygens = [m['oxygen_mg_l'] for m in measurements]
    ammonias = [m['ammonia_ppm'] for m in measurements]
    
    tank_stats[tid] = {
        'n': len(measurements),
        'ph_mean': mean(phs),
        'ph_std': stdev(phs) if len(phs) > 1 else 0.0,
        'temp_mean': mean(temps),
        'temp_std': stdev(temps) if len(temps) > 1 else 0.0,
        'o2_mean': mean(oxygens),
        'nh3_mean': mean(ammonias),
    }

violation_counts = {}
for tid in tank_stats:
    violations = []
    s = tank_stats[tid]
    if not (7.0 <= s['ph_mean'] <= 7.5):
        violations.append('pH out of range')
    if s['o2_mean'] < 6.0:
        violations.append('Low dissolved oxygen')
    if s['nh3_mean'] > 0.5:
        violations.append('High ammonia')
    violation_counts[tid] = violations

all_phs = [m['ph'] for m in records]
all_temps = [m['temp_c'] for m in records]
all_oxygens = [m['oxygen_mg_l'] for m in records]
all_ammonias = [m['ammonia_ppm'] for m in records]

r_ph_temp, p_ph_temp = stats.pearsonr(all_phs, all_temps)
r_o2_nh3, p_o2_nh3 = stats.pearsonr(all_oxygens, all_ammonias)

output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, 'w') as f:
    f.write('# Aquaculture System Water Quality Report\n\n')
    f.write(f'Analyzed {len(records)} measurements from {len(tank_stats)} production tanks.\n\n')
    
    f.write('## Tank Status Overview\n\n')
    for tid in sorted(tank_stats.keys()):
        s = tank_stats[tid]
        f.write(f'### Tank {tid}\n')
        f.write(f'- Measurement count: {s["n"]}\n')
        f.write(f'- pH: {s["ph_mean"]:.2f} ± {s["ph_std"]:.2f}\n')
        f.write(f'- Temperature: {s["temp_mean"]:.1f} ± {s["temp_std"]:.1f} °C\n')
        f.write(f'- Dissolved oxygen: {s["o2_mean"]:.2f} mg/L\n')
        f.write(f'- Ammonia: {s["nh3_mean"]:.3f} ppm\n')
        if violation_counts[tid]:
            f.write(f'- Alerts: {", ".join(violation_counts[tid])}\n')
        else:
            f.write(f'- Status: All parameters within target ranges\n')
        f.write('\n')
    
    f.write('## Parametric Relationships\n\n')
    f.write(f'**pH vs Temperature:** r = {r_ph_temp:+.3f}, p-value = {p_ph_temp:.4f}\n')
    if p_ph_temp < 0.05:
        f.write('  → Statistically significant correlation detected.\n')
    f.write('\n')
    f.write(f'**Dissolved Oxygen vs Ammonia:** r = {r_o2_nh3:+.3f}, p-value = {p_o2_nh3:.4f}\n')
    if p_o2_nh3 < 0.05:
        f.write('  → Statistically significant relationship present.\n')
    f.write('\n')
    
    f.write('## Recommendations\n\n')
    problem_tanks = [t for t in violation_counts if violation_counts[t]]
    if problem_tanks:
        f.write(f'Tanks {problem_tanks} require immediate attention.\n')
    else:
        f.write('All tanks operating within acceptable parameters.\n')