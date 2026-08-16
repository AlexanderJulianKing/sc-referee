import csv
from pathlib import Path
from scipy import stats

# Read data
data_file = Path("data/input.csv")
samples = []

with open(data_file) as f:
    reader = csv.DictReader(f)
    for row in reader:
        samples.append(row)

# Parse and organize by region
industrial_mercury = []
pristine_mercury = []

for sample in samples:
    try:
        mercury = float(sample["mercury_ug_kg"])
        region = sample["region"].strip()
        
        # Quality control: reject invalid measurements
        if mercury < 0 or mercury > 10000:
            continue
        
        if region == "Industrial":
            industrial_mercury.append(mercury)
        elif region == "Pristine":
            pristine_mercury.append(mercury)
    except (ValueError, KeyError):
        continue

# Statistical comparison
stat, p_value = stats.mannwhitneyu(industrial_mercury, pristine_mercury, alternative='two-sided')

# Generate report
report = Path("results/report.md")
report.parent.mkdir(parents=True, exist_ok=True)

with open(report, "w") as f:
    f.write("# Coastal Sediment Mercury Analysis\n\n")
    f.write("## Study Objective\n")
    f.write("Compare mercury concentrations in marine sediment samples between industrial and pristine coastal regions to assess pollution impact.\n\n")
    
    f.write("## Sample Summary\n")
    f.write(f"- Industrial region: {len(industrial_mercury)} samples\n")
    f.write(f"- Pristine region: {len(pristine_mercury)} samples\n")
    f.write(f"- Total valid samples: {len(industrial_mercury) + len(pristine_mercury)}\n\n")
    
    f.write("## Descriptive Statistics\n\n")
    f.write("### Industrial Coast (Mercury in µg/kg)\n")
    ind_mean = sum(industrial_mercury) / len(industrial_mercury)
    f.write(f"- Mean: {ind_mean:.2f}\n")
    f.write(f"- Median: {sorted(industrial_mercury)[len(industrial_mercury)//2]:.2f}\n")
    f.write(f"- Range: {min(industrial_mercury):.2f} – {max(industrial_mercury):.2f}\n\n")
    
    f.write("### Pristine Coast (Mercury in µg/kg)\n")
    pris_mean = sum(pristine_mercury) / len(pristine_mercury)
    f.write(f"- Mean: {pris_mean:.2f}\n")
    f.write(f"- Median: {sorted(pristine_mercury)[len(pristine_mercury)//2]:.2f}\n")
    f.write(f"- Range: {min(pristine_mercury):.2f} – {max(pristine_mercury):.2f}\n\n")
    
    f.write("## Statistical Analysis\n\n")
    f.write("Mann-Whitney U test was used to compare mercury concentrations between the two regions.\n\n")
    f.write(f"- Test statistic: {stat:.1f}\n")
    f.write(f"- P-value: {p_value:.6f}\n")
    f.write(f"- Significance level: α = 0.05\n\n")
    
    if p_value < 0.05:
        f.write("**Result:** The difference in mercury concentrations between regions is statistically significant (p < 0.05).\n\n")
    else:
        f.write("**Result:** No statistically significant difference detected (p ≥ 0.05).\n\n")
    
    f.write("## Interpretation\n")
    f.write(f"The industrial coastal region shows a mean mercury concentration of {ind_mean:.2f} µg/kg, ")
    f.write(f"approximately {ind_mean/pris_mean:.1f}× higher than the pristine region ({pris_mean:.2f} µg/kg). ")
    f.write("This pattern is consistent with accumulation from industrial discharge and atmospheric deposition in developed coastal areas.\n")