# Winter supplementary feed pellet trial in first-winter reindeer calves

Seventy-eight first-winter reindeer calves completed a ten-week corral supplementary feeding
period at the husbandry research station, 39 on the station's established pellet and 39 on a new
pellet with a different protein and lichen-substitute blend. Calves were fed and measured
individually. The protocol declared three outcomes in advance, in this order: average daily body
weight gain, serum urea concentration, and haematocrit. All numbers below come from `analysis.py`
run on `calves.csv`.

## Data description

The analysis input is `calves.csv`: comma-separated, UTF-8, one header row and 78 data rows.

**One row is one calf.** Each row holds a single first-winter reindeer calf that completed the
ten-week feeding period, the pellet it was fed, and its three end-of-period measurements. Each calf
appears exactly once, and there are no empty cells.

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `calf_id` | text | none | Ear-tag identifier of the calf, `RC-001` through `RC-078`, unique across the file. |
| `feed_group` | text | none | Pellet the calf was fed for the ten weeks. Exactly two values: `pellet_established` and `pellet_new`. |
| `daily_gain_g_per_day` | number | grams per day | Average daily body weight gain over the feeding period (total weight change divided by days on feed). |
| `serum_urea_mmol_l` | number | millimoles per litre | Serum urea concentration in the blood sample taken at the end of the feeding period. |
| `haematocrit_pct` | number | percent | Haematocrit, packed red cell volume as a percentage of whole blood, from the same end-of-period blood sample. |

The script confirmed the group sizes in the file: 39 calves on `pellet_established` and 39 on
`pellet_new`, 78 in total.

## Group summaries

Mean and standard deviation for each outcome, by feed group.

| Outcome | `pellet_established` (n = 39) | `pellet_new` (n = 39) |
| --- | --- | --- |
| Average daily gain (g/day) | 270.82 +/- 54.07 | 293.07 +/- 53.73 |
| Serum urea (mmol/L) | 4.22 +/- 0.87 | 4.86 +/- 0.94 |
| Haematocrit (%) | 38.25 +/- 3.58 | 39.26 +/- 3.15 |

## Per-outcome results

Each declared outcome was compared between the two feed groups with a two-sample t-test for
independent samples (Welch form, which does not assume equal group variances). The threshold is
0.05. Differences are stated as new pellet minus established pellet. The outcomes appear in the
order the protocol declared them.

**1. Average daily body weight gain (g/day).** Difference +22.25 g/day, t = 1.823, p = 0.072.
Not significant at 0.05.

**2. Serum urea concentration (mmol/L).** Difference +0.65 mmol/L, t = 3.146, p = 0.002.
Significant at 0.05.

**3. Haematocrit (%).** Difference +1.01 percentage points, t = 1.326, p = 0.189.
Not significant at 0.05.

| # | Outcome | Difference (new - established) | t | p | Verdict at 0.05 |
| --- | --- | --- | --- | --- | --- |
| 1 | Average daily gain (g/day) | +22.25 | 1.823 | 0.072 | not significant |
| 2 | Serum urea (mmol/L) | +0.65 | 3.146 | 0.002 | significant |
| 3 | Haematocrit (%) | +1.01 | 1.326 | 0.189 | not significant |

## Conclusion

The station should not switch to the new pellet on the strength of this trial. The outcome that
matters most for husbandry, average daily gain, favoured the new pellet by 22.25 g/day, but that
difference was not significant at 0.05 (p = 0.072). Haematocrit was also not significantly
different (p = 0.189), so the two pellets look alike on that measure.

The one significant result was serum urea, which was 0.65 mmol/L higher on the new pellet
(p = 0.002). Both group means, 4.22 and 4.86 mmol/L, sit inside the normal range for the species,
so this is a signal about protein handling rather than a health problem: it is consistent with the
new pellet delivering more protein than the calves put into growth. Paying for a higher-protein
pellet is only worth it if the extra protein turns into weight, and this trial did not show that it
does.

A practical next step is to repeat the comparison with more calves, since the growth difference
points in the new pellet's favour and a larger trial would settle whether it is real.
