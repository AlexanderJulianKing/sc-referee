import csv
from scipy import stats

def main():
    high_maintenance = []
    low_maintenance = []
    
    with open('data/input.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            height = float(row['height_m'])
            park_type = row['park_type']
            
            if park_type == 'high':
                high_maintenance.append(height)
            else:
                low_maintenance.append(height)
    
    high_n = len(high_maintenance)
    high_mean = sum(high_maintenance) / high_n
    high_var = sum((x - high_mean) ** 2 for x in high_maintenance) / (high_n - 1)
    high_std = high_var ** 0.5
    
    low_n = len(low_maintenance)
    low_mean = sum(low_maintenance) / low_n
    low_var = sum((x - low_mean) ** 2 for x in low_maintenance) / (low_n - 1)
    low_std = low_var ** 0.5
    
    t_stat, p_value = stats.ttest_ind(high_maintenance, low_maintenance)
    
    with open('results/report.md', 'w') as f:
        f.write("# Tree Height Comparison: High vs Low-Maintenance Parks\n\n")
        f.write("## Summary Statistics\n\n")
        f.write("### High-Maintenance Parks\n")
        f.write(f"- Sample size: {high_n}\n")
        f.write(f"- Mean height: {high_mean:.2f} m\n")
        f.write(f"- Std deviation: {high_std:.2f} m\n")
        f.write(f"- Min: {min(high_maintenance):.2f} m\n")
        f.write(f"- Max: {max(high_maintenance):.2f} m\n\n")
        f.write("### Low-Maintenance Parks\n")
        f.write(f"- Sample size: {low_n}\n")
        f.write(f"- Mean height: {low_mean:.2f} m\n")
        f.write(f"- Std deviation: {low_std:.2f} m\n")
        f.write(f"- Min: {min(low_maintenance):.2f} m\n")
        f.write(f"- Max: {max(low_maintenance):.2f} m\n\n")
        f.write("## Statistical Test Results\n\n")
        f.write("Independent samples t-test:\n")
        f.write(f"- t-statistic: {t_stat:.4f}\n")
        f.write(f"- p-value: {p_value:.4f}\n")
        f.write(f"- Difference in means: {high_mean - low_mean:.2f} m\n\n")
        f.write("## Interpretation\n\n")
        if p_value < 0.05:
            f.write(f"The difference in mean tree heights between high-maintenance and low-maintenance parks is statistically significant (p = {p_value:.4f}). Trees in well-maintained parks are substantially taller on average, suggesting that maintenance resources directly influence arboreal growth outcomes.\n")
        else:
            f.write(f"There is no statistically significant difference in mean tree heights between the two park types (p = {p_value:.4f}). Maintenance level does not appear to have a measurable effect on tree height in this sample.\n")

if __name__ == '__main__':
    main()