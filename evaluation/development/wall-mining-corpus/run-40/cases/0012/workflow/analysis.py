import csv
import math
from pathlib import Path
from scipy import stats

def load_observations(filepath):
    observations = {}
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            month = row["Month"]
            species = row["Species"]
            count = int(row["Count"])
            if month not in observations:
                observations[month] = {}
            observations[month][species] = count
    return observations

def compute_shannon_index(counts):
    total = sum(counts)
    if total == 0:
        return 0
    proportions = [c / total for c in counts]
    return -sum(p * math.log(p) for p in proportions if p > 0)

def analyze_monthly_dynamics(observations):
    months = sorted(observations.keys(), key=lambda m: ["January", "February", "March", "April", "May", "June"].index(m.split()[0]) if m.split()[0] in ["January", "February", "March", "April", "May", "June"] else 0)
    metrics = {}
    
    for month in months:
        counts = list(observations[month].values())
        total = sum(counts)
        richness = len(counts)
        diversity = compute_shannon_index(counts)
        metrics[month] = {
            "total": total,
            "richness": richness,
            "diversity": diversity
        }
    
    return months, metrics

def perform_trend_analysis(month_sequence, values):
    x_vals = list(range(len(values)))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_vals, values)
    return {"slope": slope, "r_squared": r_value ** 2, "p_value": p_value}

def build_markdown_report(observations, months, monthly_metrics):
    species_aggregate = {}
    for month_data in observations.values():
        for species, count in month_data.items():
            species_aggregate[species] = species_aggregate.get(species, 0) + count
    
    ranked_species = sorted(species_aggregate.items(), key=lambda x: x[1], reverse=True)
    grand_total = sum(species_aggregate.values())
    
    report_lines = []
    report_lines.append("# Avian Community Monitoring Report\n")
    report_lines.append("## Executive Summary\n")
    report_lines.append(f"Survey duration: {months[0]} through {months[-1]}\n")
    report_lines.append(f"Total individual birds recorded: {grand_total}\n")
    report_lines.append(f"Number of species observed: {len(ranked_species)}\n\n")
    
    report_lines.append("## Species Composition\n\n")
    report_lines.append("| Species | Individuals | Percentage |\n")
    report_lines.append("|---------|-------------|------------|\n")
    for species, count in ranked_species:
        percentage = (count / grand_total) * 100
        report_lines.append(f"| {species} | {count} | {percentage:.1f}% |\n")
    
    report_lines.append("\n## Temporal Variation\n\n")
    report_lines.append("| Month | Count | Richness | Shannon Index |\n")
    report_lines.append("|-------|-------|----------|---------------|\n")
    for month in months:
        metrics = monthly_metrics[month]
        report_lines.append(f"| {month} | {metrics['total']} | {metrics['richness']} | {metrics['diversity']:.3f} |\n")
    
    totals = [monthly_metrics[m]["total"] for m in months]
    trend = perform_trend_analysis(months, totals)
    
    report_lines.append("\n## Population Trend Analysis\n\n")
    report_lines.append(f"Linear regression slope: {trend['slope']:.3f} birds/month\n")
    report_lines.append(f"Coefficient of determination (R²): {trend['r_squared']:.4f}\n")
    report_lines.append(f"P-value: {trend['p_value']:.4f}\n\n")
    
    if trend['p_value'] < 0.05:
        direction = "increasing" if trend['slope'] > 0 else "decreasing"
        report_lines.append(f"**Finding:** A statistically significant {direction} trend is present (α = 0.05).\n")
    else:
        report_lines.append("**Finding:** No statistically significant linear trend detected.\n")
    
    report_lines.append("\n## Community Diversity\n\n")
    diversity_vals = [monthly_metrics[m]["diversity"] for m in months]
    report_lines.append(f"Mean Shannon diversity: {sum(diversity_vals) / len(diversity_vals):.3f}\n")
    report_lines.append(f"Minimum diversity: {min(diversity_vals):.3f} ({months[diversity_vals.index(min(diversity_vals))]})\n")
    report_lines.append(f"Maximum diversity: {max(diversity_vals):.3f} ({months[diversity_vals.index(max(diversity_vals))]})\n")
    
    return "".join(report_lines)

input_path = Path("data/input.csv")
observations = load_observations(input_path)
months, monthly_metrics = analyze_monthly_dynamics(observations)
report_content = build_markdown_report(observations, months, monthly_metrics)

output_path = Path("results/report.md")
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w") as report_file:
    report_file.write(report_content)