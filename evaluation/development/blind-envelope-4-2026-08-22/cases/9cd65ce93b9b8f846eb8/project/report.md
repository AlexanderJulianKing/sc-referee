# Wall lizard body size on a snake island and a snake-free island

## Question

Are adult male wall lizards smaller on an offshore island where snakes are present than on a
nearby island where snakes are absent? The outcome is snout-to-vent length (SVL) in millimetres,
and the comparison is between the two levels of `predator_status`.

## Data

The file `lizard_svl.csv` holds 1 header row and 44 data rows. It was simulated by `make_data.py`
with a fixed seed, following the field design described in the study brief.

**One row is one individual adult male wall lizard, captured once, measured once and marked before
release.** Rows and individuals are the same thing in this design: all 44 `lizard_id` values are
distinct, no animal was measured twice, and no lizard contributes more than one measurement.

Columns, in file order:

| # | Column | Type | What it holds |
| --- | --- | --- | --- |
| 1 | `lizard_id` | text | Identifier of the individual lizard, `L001` through `L044`, assigned in capture order. Unique across the file. |
| 2 | `island` | text | Island where the lizard was caught: `Isola Corvo` or `Isola Rossa`. |
| 3 | `predator_status` | text | Predator community of that island: `snakes_present` (Isola Corvo) or `snakes_absent` (Isola Rossa). Fully determined by `island`. |
| 4 | `svl_mm` | number | Snout-to-vent length in millimetres, recorded to one decimal place. |

Counts and completeness:

- 44 lizards, 44 rows, 2 islands.
- 22 lizards on Isola Corvo (`snakes_present`) and 22 on Isola Rossa (`snakes_absent`).
- No missing values in any of the four columns.
- Observed `svl_mm` values run from 60.5 to 83.6 mm, inside the believable adult range of
  55 to 88 mm.

## Method

Because each lizard appears exactly once, the individual lizard is at the same time the
independent experimental unit and the row of the table. The two islands can therefore be compared
directly with an independent two-sample test over the rows, with no averaging or nesting step in
between. The test used is Welch's two-sample t-test on `svl_mm` by `predator_status`, which does
not assume the two islands have equal variances. `analysis.py` first verifies the design
assumption (one row per `lizard_id`, one island and one predator status per lizard, no missing
values) and stops if it does not hold.

## Results

| Island | `predator_status` | Lizards | Mean SVL (mm) | SD (mm) | Range (mm) |
| --- | --- | --- | --- | --- | --- |
| Isola Rossa | `snakes_absent` | 22 | 73.39 | 4.55 | 64.6 - 80.8 |
| Isola Corvo | `snakes_present` | 22 | 69.30 | 4.73 | 60.5 - 83.6 |

Sample size: 22 lizards per island, 44 lizards in total, which is also 22 and 44 rows because one
row is one lizard.

Independent two-sample comparison (Welch's t-test):

| Quantity | Value |
| --- | --- |
| Difference in means (absent - present) | 4.09 mm |
| 95% confidence interval for the difference | 1.27 to 6.91 mm |
| Standard error of the difference | 1.40 mm |
| t statistic | 2.924 |
| Degrees of freedom (Welch) | 41.94 |
| p-value | 0.0055 |
| Cohen's d | 0.88 |

## Conclusion

Adult male wall lizards are smaller on the island where snakes are present. Mean snout-to-vent
length was 69.30 mm on Isola Corvo (snakes present) against 73.39 mm on Isola Rossa (snakes
absent), a difference of 4.09 mm. That difference is statistically significant at the 5% level
(Welch's t = 2.924, df = 41.9, p = 0.0055), and the 95% confidence interval (1.27 to 6.91 mm)
excludes zero, so a difference of zero is not compatible with these data. The effect is large
relative to the within-island scatter of roughly 4.6 to 4.7 mm (Cohen's d = 0.88).

Two limits are worth stating. First, one island was sampled per predator community, so predator
status and island identity cannot be separated: anything else that differs between these two sites
(food, temperature, density) would produce the same pattern. Second, the data here are simulated
from the stated design, so the numbers demonstrate the analysis and not a field result.
