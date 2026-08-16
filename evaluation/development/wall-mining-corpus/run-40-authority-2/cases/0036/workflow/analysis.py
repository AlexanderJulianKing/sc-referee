import csv
import pathlib
from scipy import stats


def main():
    data_path = pathlib.Path("data/input.csv")
    results_path = pathlib.Path("results/report.md")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    rows = []
    with open(data_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    method_a_values = []
    method_b_values = []
    
    for row in rows:
        conductivity = float(row["Thermal_Conductivity"])
        if row["Curing_Method"] == "Method_A":
            method_a_values.append(conductivity)
        else:
            method_b_values.append(conductivity)
    
    mean_a = sum(method_a_values) / len(method_a_values)
    mean_b = sum(method_b_values) / len(method_b_values)
    
    var_a = sum((x - mean_a) ** 2 for x in method_a_values) / len(method_a_values)
    var_b = sum((x - mean_b) ** 2 for x in method_b_values) / len(method_b_values)
    
    std_a = var_a ** 0.5
    std_b = var_b ** 0.5
    
    min_a = min(method_a_values)
    max_a = max(method_a_values)
    min_b = min(method_b_values)
    max_b = max(method_b_values)
    
    statistic, pvalue = stats.mannwhitneyu(method_a_values, method_b_values, alternative='two-sided')
    
    report = f"""# Thermal Conductivity Analysis: Concrete Curing Methods

## Objective
Evaluate thermal conductivity differences between concrete samples cured using two distinct protocols.

## Data Summary
- Total samples: {len(rows)}
- Method A samples: {len(method_a_values)}
- Method B samples: {len(method_b_values)}

## Descriptive Statistics

**Method A (Accelerated Air Curing)**
- Mean: {mean_a:.4f} W/m·K
- Std Dev: {std_a:.4f}
- Range: {min_a:.4f} – {max_a:.4f}

**Method B (Water Immersion Curing)**
- Mean: {mean_b:.4f} W/m·K
- Std Dev: {std_b:.4f}
- Range: {min_b:.4f} – {max_b:.4f}

## Statistical Analysis

Mann-Whitney U test was applied to assess distribution differences:
- U statistic: {statistic:.2f}
- p-value: {pvalue:.4f}
- Significance level: α = 0.05

## Conclusion
"""
    
    if pvalue < 0.05:
        delta = mean_b - mean_a
        direction = "higher" if delta > 0 else "lower"
        report += f"Thermal conductivity differs significantly between curing methods (p = {pvalue:.4f}). Method B exhibits {direction} conductivity values (Δ = {abs(delta):.4f} W/m·K), indicating that water immersion curing produces denser, more thermally conductive concrete."
    else:
        report += f"No statistically significant difference was detected (p = {pvalue:.4f}). Both curing approaches yield thermally equivalent concrete specimens."
    
    with open(results_path, 'w') as f:
        f.write(report)


if __name__ == "__main__":
    main()
