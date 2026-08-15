import csv
from pathlib import Path
from statistics import mean, stdev
from scipy import stats

def main():
    input_path = Path("data/input.csv")
    output_path = Path("results/report.md")
    
    data = []
    with open(input_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'field_id': row['field_id'],
                'soil_ph': float(row['soil_ph']),
                'nitrogen_ppm': float(row['nitrogen_ppm']),
                'phosphorus_ppm': float(row['phosphorus_ppm']),
                'potassium_ppm': float(row['potassium_ppm']),
                'yield_kg_per_hectare': float(row['yield_kg_per_hectare'])
            })
    
    if len(data) < 3:
        raise ValueError("Insufficient data points for analysis")
    
    nitrogen = [d['nitrogen_ppm'] for d in data]
    phosphorus = [d['phosphorus_ppm'] for d in data]
    potassium = [d['potassium_ppm'] for d in data]
    yield_values = [d['yield_kg_per_hectare'] for d in data]
    
    yield_mean = mean(yield_values)
    yield_sd = stdev(yield_values)
    nitrogen_mean = mean(nitrogen)
    
    corr_n_yield, p_n = stats.pearsonr(nitrogen, yield_values)
    corr_p_yield, p_p = stats.pearsonr(phosphorus, yield_values)
    corr_k_yield, p_k = stats.pearsonr(potassium, yield_values)
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(nitrogen, yield_values)
    r_squared = r_value ** 2
    
    def strength(corr):
        return "Strong" if abs(corr) > 0.7 else "Moderate" if abs(corr) > 0.4 else "Weak"
    
    report = f"""# Soil Quality and Crop Yield Analysis

## Executive Summary

Analysis of {len(data)} agricultural fields examining the relationship between soil nutrient composition and grain crop productivity across a regional farming area.

## Data Summary

- **Fields Analyzed:** {len(data)}
- **Mean Yield:** {yield_mean:.1f} kg/hectare (SD: {yield_sd:.1f})
- **Nitrogen Level Range:** {min(nitrogen):.1f}–{max(nitrogen):.1f} ppm
- **Mean Soil pH:** {mean([d['soil_ph'] for d in data]):.2f}

## Correlation Analysis

Pearson correlation coefficients between soil macronutrients and crop yield:

| Nutrient | Correlation | p-value | Strength | Significance |
|----------|-------------|---------|----------|--------------|
| Nitrogen (N) | {corr_n_yield:.3f} | {p_n:.4f} | {strength(corr_n_yield)} | {"✓" if p_n < 0.05 else "NS"} |
| Phosphorus (P) | {corr_p_yield:.3f} | {p_p:.4f} | {strength(corr_p_yield)} | {"✓" if p_p < 0.05 else "NS"} |
| Potassium (K) | {corr_k_yield:.3f} | {p_k:.4f} | {strength(corr_k_yield)} | {"✓" if p_k < 0.05 else "NS"} |

## Linear Regression: Nitrogen Predicting Yield

Modeling crop yield as a function of soil nitrogen concentration:

**Model:** Yield = {intercept:.2f} + {slope:.4f} × Nitrogen_ppm

| Parameter | Value | Interpretation |
|-----------|-------|-----------------|
| Slope | {slope:.4f} kg/ha per ppm | Each ppm increase in nitrogen adds {slope:.2f} kg/ha yield |
| Intercept | {intercept:.2f} kg/ha | Baseline yield at zero nitrogen |
| R² | {r_squared:.4f} | Nitrogen explains {r_squared*100:.1f}% of yield variance |
| SE | {std_err:.4f} | Standard error of slope estimate |
| p-value | {p_value:.5f} | Model significance |

## Detailed Field Observations

| Field ID | pH | Nitrogen (ppm) | Phosphorus (ppm) | Potassium (ppm) | Yield (kg/ha) |
|----------|----|----|----|----|---|
"""
    
    for d in data:
        report += f"| {d['field_id']} | {d['soil_ph']:.2f} | {d['nitrogen_ppm']:.1f} | {d['phosphorus_ppm']:.1f} | {d['potassium_ppm']:.1f} | {d['yield_kg_per_hectare']:.0f} |\n"
    
    direction = "positive" if corr_n_yield > 0 else "negative"
    substantial = "substantial" if r_squared > 0.5 else "moderate" if r_squared > 0.25 else "weak"
    
    report += f"""

## Key Findings

1. **Nitrogen-Yield Relationship:** A {direction} correlation of {corr_n_yield:.3f} indicates that soil nitrogen levels show a {strength(corr_n_yield).lower()} association with crop yield.

2. **Model Performance:** The linear regression model explains {r_squared*100:.1f}% of observed yield variation using nitrogen as a single predictor, suggesting {{substantial}} unexplained variance from other factors (soil moisture, temperature, pest pressure).

3. **Practical Implication:** Increasing soil nitrogen by 10 ppm is associated with approximately {slope*10:.0f} kg/hectare change in yield.

4. **Nutrient Hierarchy:** Relative importance of nutrients for yield: {"N > P > K" if corr_n_yield > corr_p_yield > corr_k_yield else "varies by correlation strength"}.

## Conclusion

Soil nitrogen management demonstrates a {direction} and {strength(corr_n_yield).lower()} statistical relationship with crop yield in this dataset. The {substantial} explanatory power of the nitrogen model suggests multi-factor nutrient optimization strategies should be employed for yield maximization.
"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report)
    
    print(f"Report generated: {output_path}")

if __name__ == '__main__':
    main()
