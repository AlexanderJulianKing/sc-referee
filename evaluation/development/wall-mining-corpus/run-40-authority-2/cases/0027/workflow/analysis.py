import pandas as pd
from pathlib import Path
from scipy import stats

def load_and_validate_data(csv_path):
    data = pd.read_csv(csv_path)
    if data.empty:
        raise ValueError("Input CSV is empty")
    
    required_cols = {'sample_id', 'farm_name', 'zinc_ppm'}
    if not required_cols.issubset(data.columns):
        raise ValueError(f"Missing columns: {required_cols - set(data.columns)}")
    
    return data.dropna(subset=['zinc_ppm'])

def main():
    input_path = Path('data/input.csv')
    output_dir = Path('results')
    output_dir.mkdir(exist_ok=True)
    
    df = load_and_validate_data(input_path)
    
    zinc_farm_a = df[df['farm_name'] == 'Farm_A']['zinc_ppm']
    zinc_farm_b = df[df['farm_name'] == 'Farm_B']['zinc_ppm']
    
    if len(zinc_farm_a) < 2 or len(zinc_farm_b) < 2:
        raise ValueError("Each group requires at least 2 samples")
    
    t_stat, p_val = stats.ttest_ind(zinc_farm_a, zinc_farm_b)
    
    mean_a = zinc_farm_a.mean()
    mean_b = zinc_farm_b.mean()
    
    report = f"""# Zinc Content Analysis: Farm Comparison

## Study Design
Comparison of zinc concentration in vegetable samples from two agricultural farms to assess potential differences in soil contamination or agronomic practices.

## Sample Characteristics
**Farm A**
- N = {len(zinc_farm_a)}
- Mean ± SD: {mean_a:.2f} ± {zinc_farm_a.std():.2f} ppm
- Range: [{zinc_farm_a.min():.2f}, {zinc_farm_a.max():.2f}] ppm

**Farm B**
- N = {len(zinc_farm_b)}
- Mean ± SD: {mean_b:.2f} ± {zinc_farm_b.std():.2f} ppm
- Range: [{zinc_farm_b.min():.2f}, {zinc_farm_b.max():.2f}] ppm

## Statistical Testing
Independent samples t-test comparing mean zinc concentrations:
- t = {t_stat:.4f}
- p = {p_val:.6f}
- α = 0.05

## Findings
{"Statistical evidence supports a significant difference between farms (p < 0.05)." if p_val < 0.05 else "No significant difference detected between farms (p ≥ 0.05)."}

Observed difference in means: {abs(mean_a - mean_b):.2f} ppm ({("Farm A higher" if mean_a > mean_b else "Farm B higher")})
"""
    
    Path('results/report.md').write_text(report)

if __name__ == '__main__':
    main()
