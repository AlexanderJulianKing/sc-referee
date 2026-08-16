import csv
import math
from scipy import stats


def main():
    data = []
    with open('data/input.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    neutral_heights = []
    acidic_heights = []
    
    for row in data:
        height = float(row['stem_height_cm'])
        if row['soil_pH'] == 'neutral':
            neutral_heights.append(height)
        else:
            acidic_heights.append(height)
    
    neutral_mean = sum(neutral_heights) / len(neutral_heights)
    acidic_mean = sum(acidic_heights) / len(acidic_heights)
    
    neutral_var = sum((x - neutral_mean) ** 2 for x in neutral_heights) / (len(neutral_heights) - 1)
    acidic_var = sum((x - acidic_mean) ** 2 for x in acidic_heights) / (len(acidic_heights) - 1)
    
    neutral_std = math.sqrt(neutral_var)
    acidic_std = math.sqrt(acidic_var)
    
    t_stat, p_value = stats.ttest_ind(neutral_heights, acidic_heights)
    
    report = f"""# Plant Growth Analysis: Soil pH Effect on Stem Height

## Study Design

This analysis examines the effect of soil pH on plant stem height growth over a 4-week period. Plants were grown under two conditions:
- **Neutral pH soil** (pH ~7): Control condition
- **Acidic soil** (pH ~5): Treatment condition

## Results

### Summary Statistics

**Neutral pH Group:**
- Sample size: {len(neutral_heights)}
- Mean stem height: {neutral_mean:.2f} cm
- Standard deviation: {neutral_std:.2f} cm
- Range: {min(neutral_heights):.2f} - {max(neutral_heights):.2f} cm

**Acidic pH Group:**
- Sample size: {len(acidic_heights)}
- Mean stem height: {acidic_mean:.2f} cm
- Standard deviation: {acidic_std:.2f} cm
- Range: {min(acidic_heights):.2f} - {max(acidic_heights):.2f} cm

### Statistical Comparison

An independent samples t-test was performed to compare stem height between the two soil pH conditions.

**Test Results:**
- t-statistic: {t_stat:.4f}
- p-value: {p_value:.4f}
- Difference in means: {neutral_mean - acidic_mean:.2f} cm

**Interpretation:**
"""
    
    if p_value < 0.05:
        report += f"The difference in stem height between neutral and acidic soil is statistically significant (p = {p_value:.4f}). "
        if neutral_mean > acidic_mean:
            report += "Plants grown in neutral pH soil had significantly taller stems than those in acidic soil."
        else:
            report += "Plants grown in acidic pH soil had significantly taller stems than those in neutral pH soil."
    else:
        report += f"The difference in stem height between neutral and acidic soil is not statistically significant (p = {p_value:.4f}). "
        report += "Soil pH did not have a significant effect on plant stem height in this study."
    
    report += "\n\n## Conclusion\n\n"
    report += "This analysis examined whether soil pH affects plant stem height growth. "
    report += f"The sample of {len(neutral_heights) + len(acidic_heights)} plants was divided into two groups "
    report += "based on soil pH treatment. Stem heights were compared using an independent samples t-test. "
    report += "The results provide evidence about the relationship between soil pH and plant growth in controlled conditions."
    
    with open('results/report.md', 'w') as f:
        f.write(report)


if __name__ == '__main__':
    main()
