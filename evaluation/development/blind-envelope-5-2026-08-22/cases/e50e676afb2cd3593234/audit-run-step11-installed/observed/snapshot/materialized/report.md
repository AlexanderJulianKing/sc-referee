# A high-protein breakfast lowers the mid-morning glucose peak in prediabetes

## Data description

The analysis uses one comma-separated data file, `breakfast_glucose_mornings.csv`. It holds 337
lines: one header line and 336 data rows, with no missing cells.

**One row is one volunteer on one study morning** — a single breakfast eaten at home and the two
glucose readings recorded around it. A row is not a person and not a per-person summary. Twenty-four
volunteers each ate their assigned breakfast on 14 consecutive mornings, giving 24 x 14 = 336
person-mornings.

The file has five columns, in this order:

| # | Column | Type | Values here | What it holds |
|---|---|---|---|---|
| 1 | `volunteer_code` | text | 24 codes, `PDB-101` to `PDB-124` | Anonymised participant label. Appears on 14 rows, one per morning. |
| 2 | `breakfast_arm` | text | `refined_cereal`, `high_protein` | Randomised breakfast assignment. Fixed for a volunteer across all 14 of their rows. |
| 3 | `study_day` | integer | 1 to 14 | Which of the 14 consecutive study mornings the row records for that volunteer. |
| 4 | `fasting_glucose_mmol_l` | decimal, 1 dp | 5.2 to 6.9 | Fasting glucose that morning, measured before the breakfast, in mmol/L. |
| 5 | `peak_glucose_mmol_l` | decimal, 1 dp | 6.8 to 10.4 | Outcome. Highest glucose reached in the two hours after that morning's breakfast, from the continuous glucose sensor, in mmol/L. |

Rows are sorted by `volunteer_code`, then by `study_day`. Twelve volunteers were randomised to the
refined-cereal breakfast and twelve to the high-protein breakfast, giving 168 mornings in each arm.

## Methods

Twenty-four adults with prediabetes were randomised to one of two breakfasts: a refined-cereal
breakfast (the comparison) or a high-protein breakfast (the intervention). Each volunteer ate the
assigned breakfast at home on 14 consecutive mornings while wearing a continuous glucose sensor. The
outcome is the peak glucose reached in the two hours after the meal, in mmol/L. Fasting glucose was
recorded each morning before the meal.

The two breakfasts were compared on peak glucose with an independent two-sample t-test of the
difference in means, using the Welch form, which does not assume the two arms share a variance. Every
morning in the table was passed into the comparison as a separate observation, so the analysed sample
size is 336 mornings. Two-sided p-values and 95% confidence intervals are reported. The analysis was
run with Python 3, pandas 2.0.3 and SciPy 1.9.1; the script is `analysis.py`.

## Results

The analysis covers 336 mornings, 168 in each arm.

| Breakfast arm | Mornings | Mean peak glucose (mmol/L) | SD | SE | Range |
|---|---|---|---|---|---|
| `refined_cereal` | 168 | 9.38 | 0.53 | 0.041 | 8.1 to 10.4 |
| `high_protein` | 168 | 7.85 | 0.42 | 0.032 | 6.8 to 8.8 |

The high-protein breakfast produced a mean peak glucose 1.53 mmol/L lower than the refined-cereal
breakfast (95% CI 1.43 to 1.63 mmol/L; SE of the difference 0.052). Welch's independent two-sample
t-test gives t = 29.30 on 317.2 degrees of freedom, p = 3.0e-92. The difference in peak glucose
between the two breakfasts is statistically significant at the 5 percent level.

Fasting glucose, measured before the meal, was close to identical in the two arms (refined cereal
mean 6.05, SD 0.35; high protein mean 6.00, SD 0.38), as expected for a reading taken before the
breakfast is eaten.

## Clinical interpretation

Swapping a refined-cereal breakfast for a high-protein breakfast lowers the mid-morning glucose peak
by about 1.5 mmol/L in adults with prediabetes. That is a large shift for a single meal change. It
moves the average morning peak from 9.4 mmol/L, which is in the range where post-meal excursions
start to matter for people whose glucose control is already impaired, down to 7.8 mmol/L, which sits
comfortably lower. The whole confidence interval, 1.43 to 1.63 mmol/L, lies well above the roughly
0.5 mmol/L change usually treated as clinically worth having, so the benefit is not a borderline one.

The effect appeared without any change to fasting glucose, which was the same in both arms. The
breakfast is acting on the post-meal excursion itself rather than on the overnight baseline, which is
what a protein-for-refined-carbohydrate swap is expected to do: less rapidly absorbed starch reaching
the gut at once, and a slower rise afterwards.

For practice, this supports offering a high-protein breakfast as a straightforward first dietary step
for adults with prediabetes. It is a single, cheap, once-a-day change, volunteers sustained it across
14 consecutive mornings at home rather than in a clinic, and it delivers a reduction in mid-morning
glucose of a size worth having.
