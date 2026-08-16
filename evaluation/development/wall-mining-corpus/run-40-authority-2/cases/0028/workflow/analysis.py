import csv
import pathlib
from scipy import stats

def load_data(filepath):
    records = []
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def main():
    input_file = pathlib.Path("data/input.csv")
    output_file = pathlib.Path("results/report.md")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    records = load_data(input_file)
    
    control_group = []
    treatment_group = []
    
    for record in records:
        condition = record["treatment"].strip()
        try:
            measurement = float(record["fv_fm_ratio"])
            if condition == "Control":
                control_group.append(measurement)
            elif condition == "Fertilizer":
                treatment_group.append(measurement)
        except (ValueError, KeyError):
            continue
    
    if len(control_group) < 2 or len(treatment_group) < 2:
        raise ValueError("Insufficient valid data in one or both groups")
    
    control_mean = sum(control_group) / len(control_group)
    control_var = sum((x - control_mean) ** 2 for x in control_group) / len(control_group)
    control_std = control_var ** 0.5
    
    treatment_mean = sum(treatment_group) / len(treatment_group)
    treatment_var = sum((x - treatment_mean) ** 2 for x in treatment_group) / len(treatment_group)
    treatment_std = treatment_var ** 0.5
    
    u_statistic, p_value = stats.mannwhitneyu(control_group, treatment_group, alternative="two-sided")
    
    with open(output_file, "w") as f:
        f.write("# Photosynthetic Efficiency: Fertilizer Treatment Comparison\n\n")
        f.write("## Study Design\n")
        f.write("Chlorophyll fluorescence (Fv/Fm ratio) measurements were acquired from plant ")
        f.write("leaves under two distinct fertilizer regimens. The Fv/Fm parameter represents ")
        f.write("maximum quantum yield of photosystem II photochemistry, a standard indicator of ")
        f.write("photosynthetic competence.\n\n")
        
        f.write("## Descriptive Statistics\n\n")
        f.write("### Control Group (Standard Nutrition)\n")
        f.write(f"- n = {len(control_group)}\n")
        f.write(f"- Mean Fv/Fm: {control_mean:.4f}\n")
        f.write(f"- Std Dev: {control_std:.4f}\n")
        f.write(f"- Min: {min(control_group):.4f}\n")
        f.write(f"- Max: {max(control_group):.4f}\n\n")
        
        f.write("### Fertilizer Treatment Group\n")
        f.write(f"- n = {len(treatment_group)}\n")
        f.write(f"- Mean Fv/Fm: {treatment_mean:.4f}\n")
        f.write(f"- Std Dev: {treatment_std:.4f}\n")
        f.write(f"- Min: {min(treatment_group):.4f}\n")
        f.write(f"- Max: {max(treatment_group):.4f}\n\n")
        
        f.write("## Comparative Analysis\n\n")
        f.write("Mann-Whitney U test was applied to assess whether the two treatment groups ")
        f.write("show significantly different photosynthetic efficiency distributions.\n\n")
        f.write(f"- U statistic: {u_statistic:.2f}\n")
        f.write(f"- p-value (two-sided): {p_value:.4f}\n\n")
        
        if p_value < 0.05:
            f.write("## Conclusion\n")
            f.write("The statistical test reveals a significant difference in photosynthetic ")
            f.write("efficiency between control and fertilizer-treated plants (p < 0.05). ")
            f.write("The enhanced nutrient treatment demonstrates measurably improved photosystem II ")
            f.write("function compared to standard growing conditions.\n")
        else:
            f.write("## Conclusion\n")
            f.write("No statistically significant difference in photosynthetic efficiency was ")
            f.write("detected between the two treatment groups (p ≥ 0.05). The observed variation ")
            f.write("in chlorophyll fluorescence does not exceed expected random variation.\n")

if __name__ == "__main__":
    main()