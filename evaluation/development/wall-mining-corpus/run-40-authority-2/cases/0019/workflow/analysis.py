import csv
from pathlib import Path
from scipy import stats

input_file = Path("data/input.csv")
output_file = Path("results/report.md")

rows = []
with open(input_file) as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

high_light_diameters = []
low_light_diameters = []

for row in rows:
    seedling_id = row["seedling_id"].strip()
    if not seedling_id:
        continue
    
    condition = row["light_condition"].strip().lower()
    if condition not in ["high", "low"]:
        continue
    
    try:
        diameter = float(row["stem_diameter_mm"])
    except (ValueError, KeyError):
        continue
    
    if diameter < 0:
        continue
    
    if condition == "high":
        high_light_diameters.append(diameter)
    else:
        low_light_diameters.append(diameter)

statistic, p_value = stats.ttest_ind(high_light_diameters, low_light_diameters)

output_file.parent.mkdir(parents=True, exist_ok=True)

high_mean = sum(high_light_diameters) / len(high_light_diameters)
low_mean = sum(low_light_diameters) / len(low_light_diameters)
total_n = len(high_light_diameters) + len(low_light_diameters)

with open(output_file, "w") as f:
    f.write("# Seedling Stem Development Under Different Light Intensities\n\n")
    f.write("## Objective\n\n")
    f.write("Evaluate whether light intensity affects seedling stem diameter in a controlled growth chamber.\n\n")
    f.write("## Methods\n\n")
    f.write("Seedlings were randomly assigned to either high (400 μmol m⁻² s⁻¹) or low (100 μmol m⁻² s⁻¹) light conditions. After 30 days, stem diameter was measured at 5 cm above the soil surface.\n\n")
    f.write("## Results\n\n")
    f.write(f"**Group Statistics**\n\n")
    f.write(f"- High light: n = {len(high_light_diameters)}, mean = {high_mean:.2f} mm (SD = {(sum((x - high_mean)**2 for x in high_light_diameters) / (len(high_light_diameters) - 1))**0.5:.2f})\n")
    f.write(f"- Low light: n = {len(low_light_diameters)}, mean = {low_mean:.2f} mm (SD = {(sum((x - low_mean)**2 for x in low_light_diameters) / (len(low_light_diameters) - 1))**0.5:.2f})\n\n")
    f.write(f"**Statistical Test**\n\n")
    f.write(f"Independent samples t-test: t({total_n - 2}) = {statistic:.4f}, p = {p_value:.4f}\n\n")
    f.write("## Conclusion\n\n")
    if p_value < 0.05:
        f.write(f"High light intensity significantly increased seedling stem diameter compared to low light intensity (p < 0.05). The mean stem diameter was {high_mean - low_mean:.2f} mm larger under high light conditions.\n")
    else:
        f.write(f"No significant difference in stem diameter was detected between light conditions (p ≥ 0.05).\n")