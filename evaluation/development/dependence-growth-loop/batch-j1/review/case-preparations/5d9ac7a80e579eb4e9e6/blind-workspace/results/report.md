# Warming and colony foraging output in *Bombus sylvicola*

## Study

Ten queenright *Bombus sylvicola* colonies from three alpine sites were run through a paired warming assay. Each colony foraged under an ambient chamber setting (about 19 C) and under a warmed setting (about 26 C). Each setting was split across two sessions of two 30-minute trials, and block order was counterbalanced (AW = ambient block first, WA = warmed block first). The outcome is the rate of returning foragers at the nest entrance, in sorties per hour.

The input table `data/input.csv` holds 80 trial rows: 10 colonies x 2 conditions x 4 trials per condition.

## Unit of analysis

The 4 trials a colony contributes within a condition are repeated measurements of the same colony; they replicate the measurement, not the warming manipulation. Every colony is therefore collapsed to one ambient mean and one warmed mean before any test is run, and the inferential comparison uses the 10 colony-level differences - one analyzed observation per independent unit.

## Colony-level means (sorties per hour)

| colony | site | block order | ambient | warmed | warmed - ambient |
| --- | --- | --- | --- | --- | --- |
| C01 | Wheeler Cirque | AW | 22.40 | 19.20 | -3.20 |
| C02 | Wheeler Cirque | WA | 19.60 | 17.10 | -2.50 |
| C03 | Wheeler Cirque | AW | 25.10 | 21.00 | -4.10 |
| C04 | Trapper Basin | WA | 17.80 | 16.00 | -1.80 |
| C05 | Trapper Basin | AW | 23.50 | 19.90 | -3.60 |
| C06 | Trapper Basin | WA | 20.20 | 17.30 | -2.90 |
| C07 | Sundog Pass | AW | 18.30 | 17.60 | -0.70 |
| C08 | Sundog Pass | WA | 24.00 | 20.60 | -3.40 |
| C09 | Sundog Pass | AW | 21.70 | 19.50 | -2.20 |
| C10 | Wheeler Cirque | WA | 26.30 | 21.70 | -4.60 |

- ambient colony means: 21.89 +/- 2.88 SD (n = 10 colonies)
- warmed colony means: 18.99 +/- 1.90 SD (n = 10 colonies)

## Test

Two-sided paired t-test (scipy.stats.ttest_rel) on the 10 colony-level differences (warmed minus ambient).

- mean difference: -2.900 sorties/hour (SD 1.148, SE 0.363)
- 95% confidence interval: -3.721 to -2.079 sorties/hour
- t(9) = -7.989, p = 2.2e-05
- standardized paired effect size dz = -2.53

[selected-result] Paired t-test on colony-level mean foraging rates (n = 10 colonies): warming lowered foraging by 2.900 sorties/hour (95% CI -3.721 to -2.079), t(9) = -7.989, p = 2.2e-05.

## Reading of the result

Every colony (10 of 10) foraged less under the warmed setting; the smallest colony-level drop was 0.70 and the largest 4.60 sorties per hour. The confidence interval excludes zero, so these colonies foraged less under the warmer chamber setting. The trial-to-trial and session-to-session spread inside a colony feeds into the colony means but is not counted as replication of the manipulation; with 10 colonies from 3 collection sites, site effects are not separable from colony identity in this design.
