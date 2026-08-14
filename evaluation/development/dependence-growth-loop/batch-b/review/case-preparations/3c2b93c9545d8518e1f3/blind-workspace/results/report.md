# Slope aspect and daily melt at Kessel Glacier ablation stakes

## Data

Table `data/input.csv` holds 48 melt readings taken with a folding rule at
ablation stakes drilled into the glacier surface. Each reading gives the
surface lowering `ablation_mm` measured on one survey day, together with the
aspect of the slope the stake sits on.

| slope_aspect | n | mean ablation_mm | sd ablation_mm |
| --- | --- | --- | --- |
| north | 24 | 12.000 | 2.513 |
| south | 24 | 21.500 | 3.367 |

## Analysis

Welch's two-sample t-test (two-sided, unequal variances) on `ablation_mm`,
contrasting south-facing against north-facing readings. Each row of the table
supplied one observation to the test, so the two samples held 24 values each.

## Result

[selected-result] Welch's two-sample t-test on 48 stake-day readings gives mean ablation_mm of 21.500 mm on south-facing slopes against 12.000 mm on north-facing slopes, a gap of 9.500 mm (t = 11.079, df = 42.554, p < 0.0001).

The melt gap of 9.500 mm per day between the two aspects is far larger than the
spread within either group (sd 3.367 mm south, 2.513 mm north).
