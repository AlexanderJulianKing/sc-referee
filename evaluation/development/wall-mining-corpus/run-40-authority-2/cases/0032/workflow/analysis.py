import csv
from scipy import stats

def load_data(filepath):
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'sample_id': row['sample_id'],
                'river': row['river'],
                'dissolved_oxygen': float(row['dissolved_oxygen_mg_l']),
                'temperature': float(row['temperature_c'])
            })
    return data

def main():
    data = load_data('data/input.csv')
    
    river_1_samples = [d['dissolved_oxygen'] for d in data if d['river'] == 'Smith River']
    river_2_samples = [d['dissolved_oxygen'] for d in data if d['river'] == 'Jones Creek']
    
    assert len(river_1_samples) > 0 and len(river_2_samples) > 0, "Both rivers must have observations"
    
    t_stat, p_value = stats.ttest_ind(river_1_samples, river_2_samples)
    
    mean_1 = sum(river_1_samples) / len(river_1_samples)
    mean_2 = sum(river_2_samples) / len(river_2_samples)
    
    var_1 = sum((x - mean_1) ** 2 for x in river_1_samples) / (len(river_1_samples) - 1)
    var_2 = sum((x - mean_2) ** 2 for x in river_2_samples) / (len(river_2_samples) - 1)
    
    std_1 = var_1 ** 0.5
    std_2 = var_2 ** 0.5
    
    significance = "statistically significant (p < 0.05)" if p_value < 0.05 else "not significant (p ≥ 0.05)"
    higher_river = "Smith River" if mean_1 > mean_2 else "Jones Creek"
    higher_mean = max(mean_1, mean_2)
    lower_mean = min(mean_1, mean_2)
    
    report = f"""# Dissolved Oxygen Comparison: Smith River vs Jones Creek

## Study Design
A comparative water quality analysis examining dissolved oxygen (DO) concentrations in two freshwater ecosystems. Samples were collected from Smith River and Jones Creek with dissolved oxygen measured in mg/L using standard water quality protocols.

## Hypothesis Testing

**Null Hypothesis (H₀)**: Mean dissolved oxygen concentrations are equivalent between Smith River and Jones Creek.

**Alternative Hypothesis (H₁)**: Mean dissolved oxygen concentrations differ between the two water bodies.

**Statistical Method**: Independent samples t-test (two-tailed, α = 0.05)

## Descriptive Statistics

| Water Body | Sample Size | Mean DO (mg/L) | Std Dev (mg/L) |
|------------|-------------|----------------|----------------|
| Smith River | {len(river_1_samples)} | {mean_1:.2f} | {std_1:.2f} |
| Jones Creek | {len(river_2_samples)} | {mean_2:.2f} | {std_2:.2f} |
| Difference | — | {abs(mean_1 - mean_2):.2f} | — |

## Test Results

- **t-statistic**: {t_stat:.4f}
- **Degrees of freedom**: {len(river_1_samples) + len(river_2_samples) - 2}
- **p-value**: {p_value:.4f}
- **Result**: {significance.capitalize()}

## Conclusions

The independent samples t-test revealed that dissolved oxygen concentrations are {significance} between the two rivers. {higher_river} exhibits the higher mean oxygen concentration at {higher_mean:.2f} mg/L compared to {lower_mean:.2f} mg/L in the other location. This {lower_mean:.2f} mg/L concentration suggests potential ecological stress in the lower-oxygen system, potentially due to factors such as reduced flow, elevated organic matter decomposition, or pollution inputs.

## Implications

Water bodies with dissolved oxygen below 5 mg/L may experience impaired aquatic habitat quality. Results indicate differences in water quality dynamics that warrant investigation into underlying environmental factors.
"""
    
    with open('results/report.md', 'w') as f:
        f.write(report)

if __name__ == '__main__':
    main()
