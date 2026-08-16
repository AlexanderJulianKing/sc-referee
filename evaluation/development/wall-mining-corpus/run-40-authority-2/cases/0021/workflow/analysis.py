import csv
from pathlib import Path
from scipy import stats

def main():
    measurements = {}
    with open('data/input.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            treatment = row['treatment'].strip()
            if treatment not in measurements:
                measurements[treatment] = []
            measurements[treatment].append(float(row['fv_fm']))
    
    if len(measurements) != 2:
        raise ValueError(f"Expected exactly 2 treatment groups, found {len(measurements)}")
    
    treatments = sorted(measurements.keys())
    group1 = measurements[treatments[0]]
    group2 = measurements[treatments[1]]
    
    t_stat, p_value = stats.ttest_ind(group1, group2)
    
    mean1 = sum(group1) / len(group1)
    mean2 = sum(group2) / len(group2)
    sd1 = (sum((x - mean1) ** 2 for x in group1) / len(group1)) ** 0.5
    sd2 = (sum((x - mean2) ** 2 for x in group2) / len(group2)) ** 0.5
    
    Path('results').mkdir(exist_ok=True)
    with open('results/report.md', 'w') as f:
        f.write('# Plant Photosynthetic Efficiency Analysis\n\n')
        f.write('## Objective\n')
        f.write('To compare photosynthetic efficiency of plants grown under control and drought stress conditions.\n\n')
        f.write('## Descriptive Statistics\n\n')
        f.write(f'**{treatments[0].capitalize()} Group**\n')
        f.write(f'- N = {len(group1)}\n')
        f.write(f'- Mean Fv/Fm = {mean1:.4f}\n')
        f.write(f'- SD = {sd1:.4f}\n')
        f.write(f'- Range = {min(group1):.4f} to {max(group1):.4f}\n\n')
        f.write(f'**{treatments[1].capitalize()} Group**\n')
        f.write(f'- N = {len(group2)}\n')
        f.write(f'- Mean Fv/Fm = {mean2:.4f}\n')
        f.write(f'- SD = {sd2:.4f}\n')
        f.write(f'- Range = {min(group2):.4f} to {max(group2):.4f}\n\n')
        f.write('## Statistical Analysis\n\n')
        f.write('An independent samples t-test compared photosynthetic efficiency between treatment groups.\n\n')
        f.write(f'- t-statistic = {t_stat:.4f}\n')
        f.write(f'- p-value = {p_value:.6f}\n\n')
        f.write('## Interpretation\n\n')
        sig = 'statistically significant' if p_value < 0.05 else 'not statistically significant'
        f.write(f'The difference between groups is {sig} (p = {p_value:.4f}).\n\n')
        if mean1 > mean2:
            pct_diff = 100 * (mean1 - mean2) / mean2
            f.write(f'The {treatments[0]} group demonstrated higher photosynthetic efficiency ({mean1:.4f} vs {mean2:.4f}, a {pct_diff:.1f}% increase).')
        else:
            pct_diff = 100 * (mean2 - mean1) / mean1
            f.write(f'The {treatments[1]} group demonstrated higher photosynthetic efficiency ({mean2:.4f} vs {mean1:.4f}, a {pct_diff:.1f}% increase).')

if __name__ == '__main__':
    main()