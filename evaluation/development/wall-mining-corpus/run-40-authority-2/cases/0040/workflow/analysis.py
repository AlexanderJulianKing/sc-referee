import csv
from pathlib import Path
from scipy import stats

def main():
    input_path = Path("data/input.csv")
    output_path = Path("results/report.md")
    
    # Read water treatment data
    samples = []
    with open(input_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append({
                "sample_id": row["sample_id"],
                "method": row["treatment_method"],
                "chlorine_ppm": float(row["residual_cl2_ppm"])
            })
    
    # Extract residual chlorine by treatment method
    standard_cl2 = [s["chlorine_ppm"] for s in samples if s["method"] == "Standard"]
    advanced_cl2 = [s["chlorine_ppm"] for s in samples if s["method"] == "Advanced"]
    
    # Validate measurements fall within acceptable range
    standard_valid = [x for x in standard_cl2 if 0 < x < 5]
    advanced_valid = [x for x in advanced_cl2 if 0 < x < 5]
    
    # Perform statistical test
    t_stat, p_value = stats.ttest_ind(standard_valid, advanced_valid)
    
    # Calculate summary statistics
    def summarize(values):
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return {
            "count": len(values),
            "mean": mean,
            "stdev": variance ** 0.5,
            "minimum": min(values),
            "maximum": max(values)
        }
    
    stats_standard = summarize(standard_valid)
    stats_advanced = summarize(advanced_valid)
    
    # Generate markdown report
    report_md = f"""# Water Treatment Efficiency Study: Residual Chlorine Comparison

## Study Overview
This analysis compares residual chlorine concentrations achieved by two water treatment methods (Standard and Advanced) to evaluate relative disinfection performance.

## Data Collection
Water samples were collected from treatment plant outlets and analyzed for residual chlorine using standard photometric methods. All measurements are reported in milligrams per liter (ppm).

## Findings

### Standard Treatment
- **Sample count**: {stats_standard['count']}
- **Mean chlorine**: {stats_standard['mean']:.3f} ppm
- **Std. deviation**: {stats_standard['stdev']:.3f} ppm
- **Min–Max**: {stats_standard['minimum']:.3f}–{stats_standard['maximum']:.3f} ppm

### Advanced Treatment
- **Sample count**: {stats_advanced['count']}
- **Mean chlorine**: {stats_advanced['mean']:.3f} ppm
- **Std. deviation**: {stats_advanced['stdev']:.3f} ppm
- **Min–Max**: {stats_advanced['minimum']:.3f}–{stats_advanced['maximum']:.3f} ppm

### Comparison
- **Mean difference (Advanced − Standard)**: {stats_advanced['mean'] - stats_standard['mean']:.3f} ppm
- **Relative increase**: {((stats_advanced['mean'] / stats_standard['mean']) - 1) * 100:.1f}%

## Statistical Testing

An independent-samples t-test was performed to assess whether mean residual chlorine differs significantly between treatment methods.

**Test Statistics:**
- t-value: {t_stat:.4f}
- p-value: {p_value:.6f}
- α-level: 0.05

## Conclusion

{'The Advanced treatment method produces significantly higher residual chlorine levels than Standard (p < 0.05), indicating superior disinfection capability.' if p_value < 0.05 else 'No significant difference in residual chlorine levels was observed between treatment methods (p ≥ 0.05).'}

The results suggest the Advanced method {'maintains more consistent chlorine protection' if stats_advanced['stdev'] < stats_standard['stdev'] else 'introduces greater variability in residual chlorine'} compared to the Standard approach.
"""
    
    # Write report to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report_md)

if __name__ == "__main__":
    main()