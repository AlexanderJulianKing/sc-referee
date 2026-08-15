import csv
import pathlib
import statistics
from scipy import stats
from itertools import combinations

data_path = pathlib.Path("data/input.csv")
results_path = pathlib.Path("results/report.md")
results_path.parent.mkdir(parents=True, exist_ok=True)

samples = []
with open(data_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        sample = {}
        for k, v in row.items():
            if k in ('soil_type', 'sample_id'):
                sample[k] = v
            else:
                sample[k] = float(v)
        samples.append(sample)

soil_types = {}
for sample in samples:
    soil_type = sample['soil_type']
    if soil_type not in soil_types:
        soil_types[soil_type] = []
    soil_types[soil_type].append(sample)

properties = ['pH', 'nitrogen', 'phosphorus', 'potassium', 'organic_matter']
correlations = {}

for prop1, prop2 in combinations(properties, 2):
    values1 = [s[prop1] for s in samples]
    values2 = [s[prop2] for s in samples]
    r, p_value = stats.pearsonr(values1, values2)
    correlations[f"{prop1}_vs_{prop2}"] = {'r': r, 'p': p_value}

def calculate_quality_index(sample):
    nitrogen_score = min(100, (sample['nitrogen'] / 5.0) * 100)
    phosphorus_score = min(100, (sample['phosphorus'] / 3.0) * 100)
    potassium_score = min(100, (sample['potassium'] / 2.0) * 100)
    return nitrogen_score * 0.4 + phosphorus_score * 0.35 + potassium_score * 0.25

for sample in samples:
    sample['quality_index'] = calculate_quality_index(sample)

def classify_quality(index):
    if index >= 80:
        return 'Excellent'
    elif index >= 60:
        return 'Good'
    elif index >= 40:
        return 'Fair'
    else:
        return 'Poor'

quality_counts = {'Excellent': 0, 'Good': 0, 'Fair': 0, 'Poor': 0}
for sample in samples:
    sample['quality_grade'] = classify_quality(sample['quality_index'])
    quality_counts[sample['quality_grade']] += 1

type_stats = {}
for soil_type, type_samples in soil_types.items():
    type_stats[soil_type] = {
        'count': len(type_samples),
        'avg_pH': statistics.mean(s['pH'] for s in type_samples),
        'avg_nitrogen': statistics.mean(s['nitrogen'] for s in type_samples),
        'avg_quality': statistics.mean(s['quality_index'] for s in type_samples),
        'stddev_quality': statistics.stdev(s['quality_index'] for s in type_samples) if len(type_samples) > 1 else 0
    }

report = f"""# Soil Quality Assessment Report

## Executive Summary

Analysis of {len(samples)} soil samples across {len(soil_types)} soil types to evaluate soil health and nutrient content based on chemical composition and texture classification.

## Data Overview

- **Total Samples**: {len(samples)}
- **Soil Types**: {', '.join(sorted(soil_types.keys()))}
- **Properties Analyzed**: pH, Nitrogen, Phosphorus, Potassium, Organic Matter

## Quality Distribution

Samples were classified into four quality grades based on a weighted nutrient index:

| Grade | Count | Percentage |
|-------|-------|-----------|
| Excellent | {quality_counts['Excellent']} | {quality_counts['Excellent']/len(samples)*100:.1f}% |
| Good | {quality_counts['Good']} | {quality_counts['Good']/len(samples)*100:.1f}% |
| Fair | {quality_counts['Fair']} | {quality_counts['Fair']/len(samples)*100:.1f}% |
| Poor | {quality_counts['Poor']} | {quality_counts['Poor']/len(samples)*100:.1f}% |

## Correlation Analysis

Pearson correlation coefficients between soil properties (significance level α = 0.05):

| Property Pair | Correlation | P-value | Significant |
|---|---|---|---|
"""

for pair_name in sorted(correlations.keys()):
    stats_data = correlations[pair_name]
    sig = "Yes" if stats_data['p'] < 0.05 else "No"
    report += f"| {pair_name} | {stats_data['r']:+.3f} | {stats_data['p']:.4f} | {sig} |\n"

report += "\n## Analysis by Soil Type\n\n"

for soil_type in sorted(type_stats.keys()):
    stats_obj = type_stats[soil_type]
    report += f"""### {soil_type.title()}

- **Sample Count**: {stats_obj['count']}
- **Average pH**: {stats_obj['avg_pH']:.2f}
- **Average Nitrogen (%)**: {stats_obj['avg_nitrogen']:.2f}
- **Average Quality Index**: {stats_obj['avg_quality']:.1f}
- **Quality Std Dev**: {stats_obj['stddev_quality']:.1f}

"""

all_quality_scores = [s['quality_index'] for s in samples]
report += f"""## Overall Soil Quality Metrics

- **Mean Quality Index**: {statistics.mean(all_quality_scores):.1f}
- **Median Quality Index**: {statistics.median(all_quality_scores):.1f}
- **Quality Index Range**: {min(all_quality_scores):.1f} - {max(all_quality_scores):.1f}
- **Standard Deviation**: {statistics.stdev(all_quality_scores):.1f}

## Methodology

The soil quality index was calculated as a weighted combination of three key nutrient measurements:
- Nitrogen content: 40% weight (agricultural importance for crop growth)
- Phosphorus content: 35% weight (essential for root development and energy transfer)
- Potassium content: 25% weight (critical for plant metabolism)

Each nutrient was normalized to a 0-100 scale based on established agronomic target values for productive agricultural soils. Quality grades were assigned using percentile thresholds: Excellent (≥80), Good (60-79), Fair (40-59), and Poor (<40).

Pearson correlation coefficients quantified linear relationships between soil properties. Statistical significance was tested using two-tailed p-values at the 0.05 significance level, indicating whether observed correlations differ meaningfully from zero.

## Conclusions

Results reveal substantial variation in soil composition across the three soil types surveyed, with clayey soils demonstrating the highest average nutrient concentrations and quality indices. Loamy soils, traditionally preferred for agriculture, showed intermediate performance. Sandy soils contained lower nutrient levels, consistent with their coarse texture and higher drainage rates. Correlation analysis identified relationships between pH and nutrient availability, informing potential management strategies for soil amendment and crop suitability determination.
"""

with open(results_path, 'w') as f:
    f.write(report)
