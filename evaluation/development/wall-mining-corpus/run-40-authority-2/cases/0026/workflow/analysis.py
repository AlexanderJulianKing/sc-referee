import csv
import pathlib
from scipy import stats

input_path = pathlib.Path("data/input.csv")
output_path = pathlib.Path("results/report.md")

rows = []
with open(input_path) as infile:
    reader = csv.DictReader(infile)
    for row in reader:
        rows.append(row)

drip_yields = []
flood_yields = []

for row in rows:
    try:
        yield_val = float(row["yield_kg_per_hectare"])
        method = row["irrigation_method"].strip().lower()
        if method == "drip":
            drip_yields.append(yield_val)
        elif method == "flood":
            flood_yields.append(yield_val)
    except (ValueError, KeyError):
        pass

if len(drip_yields) < 2 or len(flood_yields) < 2:
    raise ValueError("Groups must have at least 2 observations each")

drip_mean = sum(drip_yields) / len(drip_yields)
flood_mean = sum(flood_yields) / len(flood_yields)

drip_var = sum((x - drip_mean) ** 2 for x in drip_yields) / len(drip_yields)
flood_var = sum((x - flood_mean) ** 2 for x in flood_yields) / len(flood_yields)

drip_sd = drip_var ** 0.5
flood_sd = flood_var ** 0.5

u_stat, p_val = stats.mannwhitneyu(drip_yields, flood_yields, alternative="two-sided")

output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w") as outfile:
    outfile.write("# Irrigation Method and Crop Yield\n\n")
    outfile.write("## Objective\n\n")
    outfile.write("Compare crop yield between drip and flood irrigation systems in field conditions.\n\n")
    outfile.write("## Data Summary\n\n")
    outfile.write(f"- Drip irrigation plots: n={len(drip_yields)}\n")
    outfile.write(f"- Flood irrigation plots: n={len(flood_yields)}\n\n")
    outfile.write("## Descriptive Statistics\n\n")
    outfile.write(f"| Irrigation Method | Mean (kg/ha) | SD (kg/ha) |\n")
    outfile.write(f"|-------------------|--------------|------------|\n")
    outfile.write(f"| Drip              | {drip_mean:.1f}      | {drip_sd:.1f}      |\n")
    outfile.write(f"| Flood             | {flood_mean:.1f}      | {flood_sd:.1f}      |\n\n")
    outfile.write("## Statistical Analysis\n\n")
    outfile.write(f"Mann-Whitney U test: U = {u_stat:.1f}, p = {p_val:.4f}\n\n")
    if p_val < 0.05:
        outfile.write("**Interpretation:** Yield differs significantly between irrigation methods (p < 0.05).\n")
    else:
        outfile.write("**Interpretation:** No significant yield difference detected between methods (p ≥ 0.05).\n")
    outfile.write(f"\nDrip irrigation produced a yield advantage of {drip_mean - flood_mean:.0f} kg/ha on average.\n")