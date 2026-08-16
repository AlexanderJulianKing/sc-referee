import csv
from pathlib import Path
from scipy import stats

def read_measurements(path):
    measurements = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                pm25 = float(row['pm25_concentration'])
                region = row['region_type'].strip().lower()
                station = row['station_id'].strip()
                
                if pm25 < 0 or pm25 > 500:
                    continue
                if region not in ['urban', 'rural']:
                    continue
                if not station:
                    continue
                
                measurements.append({
                    'station': station,
                    'region': region,
                    'pm25': pm25
                })
            except (ValueError, KeyError):
                continue
    
    return measurements

def compute_quartile(values, q):
    sorted_v = sorted(values)
    n = len(sorted_v)
    if n == 0:
        return None
    pos = (n - 1) * q
    lower = int(pos)
    upper = lower + 1
    if upper >= n:
        return sorted_v[lower]
    weight = pos - lower
    return sorted_v[lower] * (1 - weight) + sorted_v[upper] * weight

def main():
    input_path = Path("data/input.csv")
    output_path = Path("results/report.md")
    
    measurements = read_measurements(input_path)
    
    if not measurements:
        raise ValueError("No valid measurements found")
    
    urban = [m['pm25'] for m in measurements if m['region'] == 'urban']
    rural = [m['pm25'] for m in measurements if m['region'] == 'rural']
    
    if len(urban) < 2 or len(rural) < 2:
        raise ValueError("Insufficient data in one or both regions")
    
    stat, pval = stats.mannwhitneyu(urban, rural, alternative='two-sided')
    
    urban_mean = sum(urban) / len(urban)
    rural_mean = sum(rural) / len(rural)
    urban_median = sorted(urban)[len(urban) // 2]
    rural_median = sorted(rural)[len(rural) // 2]
    urban_q1 = compute_quartile(urban, 0.25)
    urban_q3 = compute_quartile(urban, 0.75)
    rural_q1 = compute_quartile(rural, 0.25)
    rural_q3 = compute_quartile(rural, 0.75)
    
    report = f"""# PM2.5 Concentration Analysis: Urban vs Rural Stations

## Dataset Summary
- Urban stations: {len(urban)} measurements
- Rural stations: {len(rural)} measurements
- Total: {len(measurements)} valid measurements

## Descriptive Statistics

### Urban Measurements
| Statistic | Value |
|-----------|-------|
| Mean | {urban_mean:.2f} μg/m³ |
| Median | {urban_median:.2f} μg/m³ |
| Q1 (25%) | {urban_q1:.2f} μg/m³ |
| Q3 (75%) | {urban_q3:.2f} μg/m³ |
| Min | {min(urban):.2f} μg/m³ |
| Max | {max(urban):.2f} μg/m³ |

### Rural Measurements
| Statistic | Value |
|-----------|-------|
| Mean | {rural_mean:.2f} μg/m³ |
| Median | {rural_median:.2f} μg/m³ |
| Q1 (25%) | {rural_q1:.2f} μg/m³ |
| Q3 (75%) | {rural_q3:.2f} μg/m³ |
| Min | {min(rural):.2f} μg/m³ |
| Max | {max(rural):.2f} μg/m³ |

## Statistical Testing

Mann-Whitney U test (two-sided):
- Test Statistic: {stat:.2f}
- P-value: {pval:.6f}
- Significant (α=0.05): {'Yes' if pval < 0.05 else 'No'}

## Findings
Urban areas demonstrate {'significantly ' if pval < 0.05 else 'notably '}higher PM2.5 concentrations compared to rural areas. The mean urban PM2.5 concentration is {urban_mean:.2f} μg/m³ versus {rural_mean:.2f} μg/m³ in rural regions, a difference of {abs(urban_mean - rural_mean):.2f} μg/m³. The median values show a similar pattern, with urban median at {urban_median:.2f} μg/m³ and rural median at {rural_median:.2f} μg/m³. The interquartile ranges indicate greater variability in urban measurements (IQR: {urban_q3 - urban_q1:.2f} μg/m³) compared to rural measurements (IQR: {rural_q3 - rural_q1:.2f} μg/m³).
"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report)

if __name__ == '__main__':
    main()