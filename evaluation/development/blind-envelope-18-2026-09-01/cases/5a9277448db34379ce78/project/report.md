# Thickened liquids after stroke: mildly thick versus moderately thick

## What was compared and why

Stroke patients who have trouble swallowing are put on thickened liquids to make
swallowing safer. Thicker liquids are easier to control in the mouth and throat,
but they are also less pleasant to drink, which may slow meals down and cut how
much a patient drinks and eats. We wanted to know whether moving from a mildly
thick to a moderately thick liquid buys a safer swallow, and what it costs at
the table.

Seventy-two consecutive inpatients with post-stroke swallowing difficulty took
part, thirty-six on each protocol, for fourteen days each. The same speech and
language therapy team assessed every patient. Six outcomes were declared in the
protocol before any data were collected, and each one is its own clinical
question.

## The data

`data.csv` holds one row per patient: 72 data rows plus a header. Every cell is
filled. The columns are:

- `patient_id` - identifier, `PT01` to `PT72`, in admission order.
- `liquid_thickness` - the protocol the patient was on, either `mildly_thick`
  or `moderately_thick`.
- `penetration_aspiration_score` - outcome 1, the penetration-aspiration scale
  score at bedside swallow assessment, an ordered score from 1 to 8 where lower
  is safer.
- `mealtime_duration_min` - outcome 2, minutes taken to finish a meal.
- `daily_oral_fluid_intake_ml` - outcome 3, millilitres drunk by mouth in a day.
- `meal_completion_pct` - outcome 4, the percentage of the served meal finished.
- `weight_change_kg` - outcome 5, weight change over the fourteen days, negative
  for weight lost.
- `coughing_episodes_per_meal` - outcome 6, coughing episodes during a meal.

## What the analysis did

`analysis.py` reads `data.csv` and walks through the six declared outcomes in
order. For each one it splits the patients by `liquid_thickness`, reports the
group sizes, means and standard deviations, and compares the groups with a Welch
two-sample t-test. Each outcome is judged on its own p-value against the usual
0.05 threshold.

## Results, outcome by outcome

1. **Penetration-aspiration score.** Mildly thick 4.11 (SD 1.01), moderately
   thick 2.36 (SD 1.10); p = 1.1e-09. Significant. Swallows were safer on the
   moderately thick protocol by about 1.75 points.
2. **Mealtime duration.** Mildly thick 28.52 min (SD 7.05), moderately thick
   30.34 min (SD 5.34); p = 0.221. Not significant. Meals ran about two minutes
   longer on the thicker liquid.
3. **Daily oral fluid intake.** Mildly thick 1206.14 mL (SD 237.55), moderately
   thick 1151.69 mL (SD 162.04); p = 0.260. Not significant.
4. **Meal completion.** Mildly thick 71.73% (SD 10.58), moderately thick 71.62%
   (SD 11.73); p = 0.966. Not significant.
5. **Weight change.** Mildly thick -0.38 kg (SD 0.96), moderately thick -0.29 kg
   (SD 0.91); p = 0.660. Not significant. Both groups lost a little weight.
6. **Coughing episodes per meal.** Mildly thick 3.39 (SD 0.99), moderately thick
   1.33 (SD 0.89); p = 1.1e-13. Significant. Patients on the moderately thick
   protocol coughed about two fewer times per meal.

## Conclusion

On the two swallow safety outcomes the moderately thick protocol came out
clearly ahead. On mealtime duration, fluid intake, meal completion and weight
change the groups landed close together and no difference reached the 0.05
threshold.
