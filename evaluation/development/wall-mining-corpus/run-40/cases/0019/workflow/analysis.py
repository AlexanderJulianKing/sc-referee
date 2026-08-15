import csv
import pathlib
from statistics import mean, stdev, median
from scipy.stats import f_oneway

def main():
    input_path = pathlib.Path("data/input.csv")
    output_path = pathlib.Path("results/report.md")
    
    species_measurements = {}
    with open(input_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            species = row["species"]
            diameter = float(row["diameter_microns"])
            if species not in species_measurements:
                species_measurements[species] = []
            species_measurements[species].append(diameter)
    
    summary_stats = {}
    for species in sorted(species_measurements.keys()):
        values = species_measurements[species]
        summary_stats[species] = {
            "n": len(values),
            "mean": mean(values),
            "median": median(values),
            "stdev": stdev(values),
            "min": min(values),
            "max": max(values)
        }
    
    measurement_groups = [species_measurements[s] for s in sorted(species_measurements.keys())]
    f_stat, p_val = f_oneway(*measurement_groups)
    
    with open(output_path, "w") as f:
        f.write("# Pollen Grain Morphometry Analysis\n\n")
        
        f.write("## Overview\n\n")
        f.write("Pollen grain diameter measurements from four plant species were analyzed ")
        f.write("using one-way ANOVA to determine if pollen size differs significantly among taxa.\n\n")
        
        f.write("## Results by Species\n\n")
        for species in sorted(summary_stats.keys()):
            s = summary_stats[species]
            f.write(f"### {species}\n\n")
            f.write(f"| Statistic | Value |\n")
            f.write(f"|-----------|-------|\n")
            f.write(f"| N | {s['n']} |\n")
            f.write(f"| Mean (μm) | {s['mean']:.2f} |\n")
            f.write(f"| Median (μm) | {s['median']:.2f} |\n")
            f.write(f"| Std Dev (μm) | {s['stdev']:.2f} |\n")
            f.write(f"| Min (μm) | {s['min']:.2f} |\n")
            f.write(f"| Max (μm) | {s['max']:.2f} |\n\n")
        
        f.write("## ANOVA Test Results\n\n")
        f.write(f"- F-statistic: {f_stat:.3f}\n")
        f.write(f"- P-value: {p_val:.2e}\n\n")
        
        f.write("## Interpretation\n\n")
        if p_val < 0.001:
            f.write("The p-value (p < 0.001) indicates highly significant differences in pollen ")
            f.write("diameter among species. Pollen size is a diagnostic morphological character ")
            f.write("distinguishing these taxa.\n")
        elif p_val < 0.05:
            f.write("The p-value (p < 0.05) indicates significant differences in pollen diameter ")
            f.write("among species.\n")
        else:
            f.write("No significant differences in pollen diameter were detected among species ")
            f.write("(p ≥ 0.05).\n")

if __name__ == "__main__":
    main()