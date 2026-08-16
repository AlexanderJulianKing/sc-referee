import csv
from pathlib import Path
from scipy import stats

input_file = Path("data/input.csv")
output_file = Path("results/report.md")

output_file.parent.mkdir(parents=True, exist_ok=True)

treatment_scores = []
control_scores = []
treatment_count = 0
control_count = 0

with open(input_file) as f:
    reader = csv.DictReader(f)
    for row in reader:
        group = row["group"].strip()
        score = float(row["effectiveness_score"])
        
        if group == "treatment":
            treatment_scores.append(score)
            treatment_count += 1
        elif group == "control":
            control_scores.append(score)
            control_count += 1

treatment_mean = sum(treatment_scores) / len(treatment_scores) if treatment_scores else 0
treatment_std = (sum((x - treatment_mean) ** 2 for x in treatment_scores) / len(treatment_scores)) ** 0.5 if treatment_scores else 0

control_mean = sum(control_scores) / len(control_scores) if control_scores else 0
control_std = (sum((x - control_mean) ** 2 for x in control_scores) / len(control_scores)) ** 0.5 if control_scores else 0

t_stat, p_value = stats.ttest_ind(treatment_scores, control_scores)

mean_diff = treatment_mean - control_mean
significant = p_value < 0.05

report_content = f"""# Medication Effectiveness Analysis

## Study Design
This randomized controlled trial evaluates a novel antihistamine medication (treatment) against placebo (control) using symptom relief effectiveness scores measured on a 0-100 scale.

## Sample Characteristics
- **Treatment group**: n = {treatment_count}, mean = {treatment_mean:.2f}, SD = {treatment_std:.2f}
- **Control group**: n = {control_count}, mean = {control_mean:.2f}, SD = {control_std:.2f}
- **Total participants**: {treatment_count + control_count}

## Effectiveness Comparison

A two-sample independent t-test was conducted to determine whether medication effectiveness differed significantly between the active drug and placebo groups.

### Statistical Results
- **t-statistic**: {t_stat:.4f}
- **p-value**: {p_value:.4f}
- **Mean difference**: {mean_diff:.2f} points (treatment minus control)
- **Result**: {"Statistically significant" if significant else "Not statistically significant"} (α = 0.05)

## Interpretation
Participants receiving the active medication reported a mean effectiveness score {abs(mean_diff):.2f} points {"higher" if mean_diff > 0 else "lower"} than those receiving placebo. {"This difference achieves statistical significance, suggesting the medication provides genuine therapeutic benefit beyond placebo." if significant else "This difference does not achieve statistical significance, suggesting no clear advantage of the medication over placebo."}

## Clinical Conclusion
Based on the two-sample t-test (t({treatment_count + control_count - 2}) = {t_stat:.2f}, p = {p_value:.4f}), the novel antihistamine {"demonstrates efficacy superior to placebo in symptom relief" if significant else "does not demonstrate efficacy superior to placebo in symptom relief"}. The findings {"support" if significant else "do not support"} clinical adoption of this medication.
"""

with open(output_file, "w") as f:
    f.write(report_content)