import csv
from scipy import stats

def main():
    with open("data/input.csv", "r") as f:
        reader = csv.DictReader(f)
        records = list(reader)
    
    field_a_phosphorus = []
    field_b_phosphorus = []
    
    for record in records:
        phos_level = float(record["phosphorus_mg_kg"])
        if record["field"] == "A":
            field_a_phosphorus.append(phos_level)
        elif record["field"] == "B":
            field_b_phosphorus.append(phos_level)
    
    def remove_statistical_outliers(measurements):
        if len(measurements) < 2:
            return measurements
        avg = sum(measurements) / len(measurements)
        variance = sum((x - avg) ** 2 for x in measurements) / len(measurements)
        std_deviation = variance ** 0.5
        cutoff = 3 * std_deviation
        return [x for x in measurements if abs(x - avg) <= cutoff]
    
    field_a_filtered = remove_statistical_outliers(field_a_phosphorus)
    field_b_filtered = remove_statistical_outliers(field_b_phosphorus)
    
    u_statistic, p_value = stats.mannwhitneyu(field_a_filtered, field_b_filtered, alternative='two-sided')
    
    a_mean = sum(field_a_filtered) / len(field_a_filtered)
    b_mean = sum(field_b_filtered) / len(field_b_filtered)
    a_min, a_max = min(field_a_filtered), max(field_a_filtered)
    b_min, b_max = min(field_b_filtered), max(field_b_filtered)
    
    report = f"""# Soil Phosphorus Comparison Between Agricultural Fields

## Overview

This analysis evaluates soil phosphorus concentrations across two adjacent agricultural fields to inform fertilization decisions.

## Dataset Summary

- Field A: {len(field_a_filtered)} valid measurements (originally {len(field_a_phosphorus)})
- Field B: {len(field_b_filtered)} valid measurements (originally {len(field_b_phosphorus)})
- Validation: Measurements deviating beyond 3 standard deviations from field mean excluded

## Results by Field

### Field A Phosphorus Levels
- Mean: {a_mean:.2f} mg/kg
- Range: {a_min:.2f}–{a_max:.2f} mg/kg
- Sample count: {len(field_a_filtered)}

### Field B Phosphorus Levels
- Mean: {b_mean:.2f} mg/kg
- Range: {b_min:.2f}–{b_max:.2f} mg/kg
- Sample count: {len(field_b_filtered)}

## Statistical Comparison

The Mann-Whitney U test (non-parametric test) was applied to compare phosphorus distributions.

**Test Output:**
- U statistic: {u_statistic:.1f}
- P-value: {p_value:.4f}
- Significance threshold: α = 0.05

### Key Finding

"""
    
    if p_value < 0.05:
        report += f"A statistically significant difference exists (p = {p_value:.4f}). "
        if a_mean > b_mean:
            report += f"Field A has substantially higher phosphorus ({a_mean:.2f} mg/kg) than Field B ({b_mean:.2f} mg/kg)."
        else:
            report += f"Field B has substantially higher phosphorus ({b_mean:.2f} mg/kg) than Field A ({a_mean:.2f} mg/kg)."
    else:
        report += f"No statistically significant difference detected (p = {p_value:.4f}). Phosphorus levels are similar between fields."
    
    report += "\n\n## Agricultural Implications\n\n"
    report += "- The field with lower phosphorus may require targeted phosphate fertilization.\n"
    report += "- Consider balanced nutrient management based on field-specific requirements.\n"
    report += "- Repeat testing annually to track phosphorus dynamics and fertilizer response.\n"
    
    with open("results/report.md", "w") as f:
        f.write(report)
    
    print("Analysis complete: results/report.md")

if __name__ == "__main__":
    main()
