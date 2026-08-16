import csv
import os
from scipy import stats

def load_data(filepath):
    plants = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            plants.append({
                'plant_id': row['plant_id'],
                'watering_schedule': row['watering_schedule'],
                'height_cm': float(row['height_cm']),
                'days_elapsed': int(row['days_elapsed'])
            })
    return plants

def validate_data(plants):
    valid = []
    for plant in plants:
        if plant['height_cm'] > 0 and plant['days_elapsed'] > 0:
            if plant['watering_schedule'] in ['daily', 'weekly']:
                valid.append(plant)
    return valid

def split_groups(plants):
    daily_group = [p['height_cm'] for p in plants if p['watering_schedule'] == 'daily']
    weekly_group = [p['height_cm'] for p in plants if p['watering_schedule'] == 'weekly']
    return daily_group, weekly_group

def analyze(daily_heights, weekly_heights):
    daily_mean = sum(daily_heights) / len(daily_heights)
    daily_std = (sum((x - daily_mean) ** 2 for x in daily_heights) / len(daily_heights)) ** 0.5
    
    weekly_mean = sum(weekly_heights) / len(weekly_heights)
    weekly_std = (sum((x - weekly_mean) ** 2 for x in weekly_heights) / len(weekly_heights)) ** 0.5
    
    t_stat, p_value = stats.ttest_ind(daily_heights, weekly_heights)
    
    return {
        'daily_mean': daily_mean,
        'daily_std': daily_std,
        'daily_n': len(daily_heights),
        'weekly_mean': weekly_mean,
        'weekly_std': weekly_std,
        'weekly_n': len(weekly_heights),
        't_statistic': t_stat,
        'p_value': p_value
    }

def write_report(stats_results, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("# Plant Growth Analysis: Watering Schedule Comparison\n\n")
        
        f.write("## Summary\n")
        f.write("This analysis compares plant stem height between two watering schedules: daily and weekly.\n\n")
        
        f.write("## Daily Watering Group\n")
        f.write(f"- Sample size: {stats_results['daily_n']}\n")
        f.write(f"- Mean height: {stats_results['daily_mean']:.2f} cm\n")
        f.write(f"- Standard deviation: {stats_results['daily_std']:.2f} cm\n\n")
        
        f.write("## Weekly Watering Group\n")
        f.write(f"- Sample size: {stats_results['weekly_n']}\n")
        f.write(f"- Mean height: {stats_results['weekly_mean']:.2f} cm\n")
        f.write(f"- Standard deviation: {stats_results['weekly_std']:.2f} cm\n\n")
        
        f.write("## Statistical Test\n")
        f.write("Independent samples t-test:\n")
        f.write(f"- t-statistic: {stats_results['t_statistic']:.4f}\n")
        f.write(f"- p-value: {stats_results['p_value']:.4f}\n\n")
        
        if stats_results['p_value'] < 0.05:
            f.write("**Conclusion:** The difference in mean plant height between daily and weekly watering schedules is statistically significant (p < 0.05).\n")
        else:
            f.write("**Conclusion:** There is no statistically significant difference in mean plant height between the two watering schedules (p >= 0.05).\n")

def main():
    data = load_data('data/input.csv')
    valid_data = validate_data(data)
    daily_heights, weekly_heights = split_groups(valid_data)
    
    results = analyze(daily_heights, weekly_heights)
    write_report(results, 'results/report.md')
    
    print("Analysis complete. Report written to results/report.md")

if __name__ == '__main__':
    main()