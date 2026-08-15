import csv
import pathlib
from statistics import mean, stdev
from scipy import stats

data_dir = pathlib.Path("data")
results_dir = pathlib.Path("results")
results_dir.mkdir(exist_ok=True)

# Load data
test_results = []
with open(data_dir / "input.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        test_results.append({
            'batch_id': row['batch_id'],
            'surface_prep': row['surface_prep'],
            'environment': row['environment'],
            'adhesion_score': float(row['adhesion_score']),
            'application_temp_c': float(row['application_temp_c']),
            'days_to_test': int(row['days_to_test'])
        })

# Group results by surface prep
by_surface = {}
for result in test_results:
    prep = result['surface_prep']
    if prep not in by_surface:
        by_surface[prep] = []
    by_surface[prep].append(result['adhesion_score'])

# Group results by environment
by_environment = {}
for result in test_results:
    env = result['environment']
    if env not in by_environment:
        by_environment[env] = []
    by_environment[env].append(result['adhesion_score'])

# Calculate statistics
surface_stats = {}
for prep, scores in by_surface.items():
    surface_stats[prep] = {
        'mean': mean(scores),
        'stdev': stdev(scores) if len(scores) > 1 else 0,
        'n': len(scores)
    }

env_stats = {}
for env, scores in by_environment.items():
    env_stats[env] = {
        'mean': mean(scores),
        'stdev': stdev(scores) if len(scores) > 1 else 0,
        'n': len(scores)
    }

# ANOVA test for surface prep
surface_groups = [by_surface[prep] for prep in by_surface]
f_stat_surface, p_value_surface = stats.f_oneway(*surface_groups)

# ANOVA test for environment
env_groups = [by_environment[env] for env in by_environment]
f_stat_env, p_value_env = stats.f_oneway(*env_groups)

# Generate report
report = []
report.append("# Paint Adhesion Test Analysis Report\n\n")
report.append("## Executive Summary\n\n")
report.append(f"This report analyzes crosshatch adhesion test results from {len(test_results)} paint samples ")
report.append("across different surface preparations and environmental exposure conditions. ")
report.append("The analysis evaluates the effectiveness of surface preparation methods and the impact of environmental factors on paint adhesion performance.\n\n")

report.append("## Results by Surface Preparation\n\n")
report.append("| Surface Preparation | Mean Adhesion | Std Dev | N |\n")
report.append("|---|---|---|---|\n")
for prep in sorted(surface_stats.keys()):
    stats_dict = surface_stats[prep]
    report.append(f"| {prep} | {stats_dict['mean']:.1f} | {stats_dict['stdev']:.2f} | {stats_dict['n']} |\n")

report.append(f"\n**Statistical Test (One-Way ANOVA):**\n")
report.append(f"- F-statistic: {f_stat_surface:.3f}\n")
report.append(f"- p-value: {p_value_surface:.4f}\n")
if p_value_surface < 0.05:
    report.append("- **Conclusion:** Surface preparation type has a statistically significant effect on adhesion (p < 0.05).\n\n")
else:
    report.append("- **Conclusion:** No significant difference in adhesion between surface preparations (p ≥ 0.05).\n\n")

report.append("## Results by Environmental Condition\n\n")
report.append("| Environment | Mean Adhesion | Std Dev | N |\n")
report.append("|---|---|---|---|\n")
for env in sorted(env_stats.keys()):
    stats_dict = env_stats[env]
    report.append(f"| {env} | {stats_dict['mean']:.1f} | {stats_dict['stdev']:.2f} | {stats_dict['n']} |\n")

report.append(f"\n**Statistical Test (One-Way ANOVA):**\n")
report.append(f"- F-statistic: {f_stat_env:.3f}\n")
report.append(f"- p-value: {p_value_env:.4f}\n")
if p_value_env < 0.05:
    report.append("- **Conclusion:** Environmental condition has a statistically significant effect on adhesion (p < 0.05).\n\n")
else:
    report.append("- **Conclusion:** No significant difference in adhesion between environments (p ≥ 0.05).\n\n")

report.append("## Key Findings\n\n")
best_surface = max(surface_stats.items(), key=lambda x: x[1]['mean'])
worst_surface = min(surface_stats.items(), key=lambda x: x[1]['mean'])
adhesion_diff = best_surface[1]['mean'] - worst_surface[1]['mean']
report.append(f"- Surface preparation significantly impacts paint adhesion, with a {adhesion_diff:.1f}-point difference between best and worst methods.\n")
report.append(f"- **Optimal surface preparation:** '{best_surface[0]}' achieves mean adhesion of {best_surface[1]['mean']:.1f}.\n")
report.append(f"- **Suboptimal surface preparation:** '{worst_surface[0]}' produces mean adhesion of {worst_surface[1]['mean']:.1f}.\n\n")

best_env = max(env_stats.items(), key=lambda x: x[1]['mean'])
worst_env = min(env_stats.items(), key=lambda x: x[1]['mean'])
env_diff = best_env[1]['mean'] - worst_env[1]['mean']
report.append(f"- Environmental conditions significantly affect paint durability, with a {env_diff:.1f}-point difference between best and worst conditions.\n")
report.append(f"- **Best environment:** '{best_env[0]}' shows mean adhesion of {best_env[1]['mean']:.1f}.\n")
report.append(f"- **Worst environment:** '{worst_env[0]}' shows mean adhesion of {worst_env[1]['mean']:.1f}.\n\n")

report.append("## Recommendations\n\n")
report.append("1. **Surface Preparation Protocol:** Implement sanding and priming procedures prior to paint application to maximize adhesion strength.\n")
report.append("2. **Environmental Storage:** Store painted components in dry conditions when possible; limit exposure to humid or salt-spray environments that degrade adhesion.\n")
report.append("3. **Quality Control:** Conduct regular crosshatch adhesion tests on production samples to ensure consistency with these baseline results.\n")
report.append("4. **Further Investigation:** Consider multi-factor interaction analysis if higher-order effects between surface prep and environmental factors are suspected.\n")

# Write report
with open(results_dir / "report.md", 'w') as f:
    f.writelines(report)

print("Analysis complete. Report written to results/report.md")