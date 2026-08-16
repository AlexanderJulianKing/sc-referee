import csv
import os
from scipy import stats

def load_enzyme_data(filepath):
    batches = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            batches.append({
                'batch_id': row['batch_id'],
                'temperature_condition': row['temperature_condition'],
                'reaction_rate': float(row['reaction_rate']),
            })
    return batches

def validate_enzyme_data(batches):
    errors = []
    valid_temps = {'low', 'high'}
    for batch in batches:
        if batch['temperature_condition'] not in valid_temps:
            errors.append(f"Invalid temperature condition: {batch['temperature_condition']}")
        if batch['reaction_rate'] < 0:
            errors.append(f"Negative reaction rate in batch {batch['batch_id']}")
    return errors

def analyze_enzyme_activity(batches):
    low_temp = [b['reaction_rate'] for b in batches if b['temperature_condition'] == 'low']
    high_temp = [b['reaction_rate'] for b in batches if b['temperature_condition'] == 'high']
    
    t_statistic, p_value = stats.ttest_ind(low_temp, high_temp)
    
    low_mean = sum(low_temp) / len(low_temp)
    high_mean = sum(high_temp) / len(high_temp)
    low_std = (sum((x - low_mean) ** 2 for x in low_temp) / len(low_temp)) ** 0.5
    high_std = (sum((x - high_mean) ** 2 for x in high_temp) / len(high_temp)) ** 0.5
    
    return {
        'low_temp_rates': low_temp,
        'high_temp_rates': high_temp,
        'low_mean': low_mean,
        'high_mean': high_mean,
        'low_std': low_std,
        'high_std': high_std,
        't_statistic': t_statistic,
        'p_value': p_value,
    }

def generate_report(results, output_path):
    report_lines = [
        "# Enzyme Activity Analysis: Temperature Effects\n",
        "## Executive Summary\n",
        "This analysis compares enzyme reaction rates under two temperature conditions (20°C and 40°C) across 20 independent reaction batches.\n",
        "## Methods\n",
        "Enzyme kinetics were measured for individual batches at low temperature (20°C, n=10) and high temperature (40°C, n=10). Activity rates were expressed in units per minute. Independent samples t-test was used to assess differences between conditions.\n",
        "## Results\n",
        "**Low Temperature (20°C):**\n",
        f"- Mean activity rate: {results['low_mean']:.2f} units/min\n",
        f"- Standard deviation: {results['low_std']:.2f}\n",
        f"- Sample size: {len(results['low_temp_rates'])}\n",
        "\n**High Temperature (40°C):**\n",
        f"- Mean activity rate: {results['high_mean']:.2f} units/min\n",
        f"- Standard deviation: {results['high_std']:.2f}\n",
        f"- Sample size: {len(results['high_temp_rates'])}\n",
        "\n## Statistical Test\n",
        "**Independent Samples t-test:**\n",
        f"- t-statistic: {results['t_statistic']:.4f}\n",
        f"- p-value: {results['p_value']:.4f}\n",
    ]
    
    if results['p_value'] < 0.05:
        report_lines.append("- **Conclusion:** Enzyme activity rates differ significantly between temperature conditions (p < 0.05).\n")
    else:
        report_lines.append("- **Conclusion:** No significant difference in enzyme activity rates between temperature conditions (p ≥ 0.05).\n")
    
    report_lines.append("\n## Interpretation\n")
    diff = results['high_mean'] - results['low_mean']
    if diff > 0:
        report_lines.append(f"Higher temperatures (40°C) yield {diff:.2f} units/min greater mean activity. This aligns with enzyme kinetics theory, where moderate temperature increases enhance molecular motion and catalytic velocity until protein denaturation occurs.\n")
    else:
        report_lines.append(f"Lower temperatures (20°C) yield {abs(diff):.2f} units/min greater mean activity. This suggests potential suboptimal conditions at the higher temperature, possibly from protein instability or reduced cofactor efficiency.\n")
    
    report = "".join(report_lines)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report)

def main():
    input_file = 'data/input.csv'
    output_file = 'results/report.md'
    
    batches = load_enzyme_data(input_file)
    errors = validate_enzyme_data(batches)
    
    if errors:
        print("Data validation errors:")
        for error in errors:
            print(f"  - {error}")
        return
    
    results = analyze_enzyme_activity(batches)
    generate_report(results, output_file)
    print(f"Analysis complete. Report written to {output_file}")

if __name__ == '__main__':
    main()