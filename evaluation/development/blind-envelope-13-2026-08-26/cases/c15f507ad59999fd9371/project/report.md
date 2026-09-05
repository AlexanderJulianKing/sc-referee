# Mulberry cultivar comparison for fifth-instar rearing

## Data

The data file is `rearing_trays.csv`: 36 data rows and one header row.

**One row is one rearing tray.** A tray holds one cohort of fifth-instar larvae fed exclusively on
a single mulberry cultivar, and the tray is scored as a unit at spinning. The tray, not the
individual larva, is the unit of observation. Thirty-six trays were reared, 18 on each cultivar.
Every tray has a value in every outcome column; there are no blank cells.

| Column | Meaning | Unit |
| --- | --- | --- |
| `tray_id` | Tray identifier, `T01` through `T36`, in rearing order. One row per identifier. | none (label) |
| `cultivar` | Mulberry cultivar fed to that tray. Exactly two values, `V1` and `S36`. This is the group column. | none (label) |
| `mean_cocoon_weight_g` | Mean weight of a single cocoon for the tray. First declared outcome. | grams |
| `cocoon_shell_ratio_pct` | Cocoon shell ratio, shell weight as a share of whole cocoon weight. Second declared outcome. | percent |
| `larval_duration_h` | Fifth-instar larval duration, from brushing into the fifth instar to spinning. Third declared outcome. | hours |
| `silk_filament_length_m` | Silk filament length reeled per cocoon. Fourth declared outcome. | metres |
| `effective_rearing_rate_pct` | Effective rate of rearing, the share of brushed larvae yielding good cocoons. Fifth declared outcome. | percent |

The five outcome columns appear in the order the trial protocol declared them.

## Method

Each of the five declared outcomes was compared between the two cultivars with the same test: a
two-sample Student t-test (`scipy.stats.ttest_ind`, equal variances assumed), 18 trays per group in
every comparison.

The five outcomes are one declared family, so the family-wise error rate is controlled across all
five together, not outcome by outcome. **The correction was performed by the third-party statistics
package `pingouin` (version 0.5.5), using `pingouin.multicomp` with the Holm step-down method at a
family-wise alpha of 0.05.** All five raw p-values were passed to that call in one batch and
adjusted together as a single family. Every verdict below is taken from the adjusted p-value
`pingouin` returned. No verdict rests on a raw p-value.

## Results

Group sizes are 18 trays for `S36` and 18 trays for `V1` in every comparison.

| Outcome | Mean, S36 | Mean, V1 | t | Raw p | Adjusted p | Verdict at family-wise 0.05 |
| --- | --- | --- | --- | --- | --- | --- |
| `mean_cocoon_weight_g` | 1.9367 | 1.8222 | 2.7585 | 0.009280 | 0.046400 | significant |
| `cocoon_shell_ratio_pct` | 19.9222 | 19.3222 | 1.3494 | 0.186140 | 0.233933 | not significant |
| `larval_duration_h` | 164.5556 | 170.7278 | -2.1701 | 0.037076 | 0.148305 | not significant |
| `silk_filament_length_m` | 1005.2222 | 947.3889 | 2.0405 | 0.049130 | 0.148305 | not significant |
| `effective_rearing_rate_pct` | 93.0222 | 90.8556 | 1.6085 | 0.116966 | 0.233933 | not significant |

Outcome by outcome:

- **Mean single cocoon weight.** S36 trays averaged 1.9367 g against 1.8222 g for V1, a difference
  of about 0.11 g. Raw p = 0.009280, adjusted p = 0.046400. Significant at the family-wise 0.05
  level.
- **Cocoon shell ratio.** S36 averaged 19.9222 percent against 19.3222 percent for V1. Raw
  p = 0.186140, adjusted p = 0.233933. Not significant.
- **Fifth-instar larval duration.** S36 averaged 164.5556 hours against 170.7278 hours for V1, so
  S36 trays spun about 6 hours sooner. Raw p = 0.037076, adjusted p = 0.148305. Not significant
  once the family of five is accounted for: this outcome would have cleared an uncorrected 0.05
  threshold, and does not clear the corrected one.
- **Silk filament length.** S36 averaged 1005.2222 m against 947.3889 m for V1. Raw p = 0.049130,
  adjusted p = 0.148305. Not significant, and the same caution applies as for larval duration: the
  raw value sits just under 0.05 and the adjusted value does not.
- **Effective rate of rearing.** S36 averaged 93.0222 percent against 90.8556 percent for V1. Raw
  p = 0.116966, adjusted p = 0.233933. Not significant.

One of the five outcomes is significant after the family-wise correction.

## Conclusion

The station should plant **S36**, but on a thinner evidence base than the raw p-values suggest.

S36 has the higher or more favourable tray mean on all five outcomes: heavier cocoons, a slightly
higher shell ratio, a shorter fifth instar, longer filament, and a higher effective rearing rate.
Only one of those differences, mean single cocoon weight, survives correction across the declared
family of five. Two others, larval duration and filament length, cleared an uncorrected 0.05
threshold but not the corrected one, so this trial does not establish them.

So the defensible reading is narrow: S36 gives heavier cocoons, and nothing in these 36 trays points
the other way on any declared outcome. That is enough to prefer S36 for planting. It is not enough
to claim a broad advantage in shell ratio, rearing speed, filament length, or rearing rate, and a
larger trial would be needed before quoting gains on those.
