# Cold plasma treatment duration for raw almond kernels

Sixty lots of raw almond kernels from one harvest were treated at a single power setting, thirty lots
for two minutes and thirty lots for five minutes, then held four weeks in ambient storage and sampled
once each. This report compares the two treatment durations on the five outcomes the protocol declared
in advance, in the declared order.

## Data description

The analysis reads one file, `almond_plasma_lots.csv`: 60 data rows plus a header row, 7 columns, no
empty cells.

**One row is one almond lot.** It carries that lot's identifier, the plasma exposure duration applied
to it, and its single post-storage measurement on each of the five declared outcomes.

| Column | Type | Units / values | Meaning |
| --- | --- | --- | --- |
| `lot_id` | text | `LOT-001` … `LOT-060` | Lot identifier, unique across the 60 rows |
| `plasma_group` | text | exactly `plasma_2min` or `plasma_5min`, 30 lots each | Cold plasma exposure duration applied to the lot |
| `surrogate_log_reduction` | number | log colony forming units per gram | Log reduction of the non-pathogenic Salmonella surrogate on the kernel surface |
| `peroxide_value_meq_kg` | number | milliequivalents of oxygen per kilogram of oil | Peroxide value of the extracted kernel oil after storage |
| `colour_l_star` | number | CIE L\* scale | Kernel surface lightness, higher is lighter |
| `moisture_pct` | number | percent by mass | Kernel moisture content after storage |
| `rancid_odour_score` | number | 0 to 6 scale | Trained sensory panel rancid odour score, higher is more rancid |

The script confirmed 60 rows, 30 lots per group, and zero missing cells in the five analysed columns.

## Group summaries

Mean and standard deviation per group, n = 30 in each group.

| Outcome | `plasma_2min` mean (SD) | `plasma_5min` mean (SD) | Difference (5 min minus 2 min) |
| --- | --- | --- | --- |
| `surrogate_log_reduction` | 1.651 (0.384) | 2.399 (0.462) | +0.748 |
| `peroxide_value_meq_kg` | 1.426 (0.432) | 2.050 (0.586) | +0.623 |
| `colour_l_star` | 55.793 (1.915) | 56.260 (2.586) | +0.467 |
| `moisture_pct` | 4.861 (0.398) | 4.696 (0.453) | -0.165 |
| `rancid_odour_score` | 1.330 (0.673) | 1.917 (0.856) | +0.587 |

## Multiplicity control

The protocol declared a family of five outcomes, so the family size is 5. The script derives that
count from the list of declared outcomes it tests, rather than from a number typed in by hand, and
computes the Sidak per-comparison level for an overall family level of 0.05:

    per-comparison alpha = 1 - (1 - 0.05)^(1/5) = 0.010206

Every outcome below is judged against that computed threshold of 0.010206, not against 0.05.

## Outcome-by-outcome results

Each outcome was compared between the two groups with a two-sided Welch two-sample t-test for
independent samples. Results in the declared order:

| # | Outcome | Welch t | p-value | Verdict vs 0.010206 |
| --- | --- | --- | --- | --- |
| 1 | `surrogate_log_reduction` | -6.820 | 6.81e-09 | significant |
| 2 | `peroxide_value_meq_kg` | -4.688 | 1.95e-05 | significant |
| 3 | `colour_l_star` | -0.794 | 0.430461 | not significant |
| 4 | `moisture_pct` | 1.496 | 0.140148 | not significant |
| 5 | `rancid_odour_score` | -2.950 | 0.004660 | significant |

Three of the five declared outcomes cleared the Sidak per-comparison threshold. Outcomes 3 and 4 fall
well short of both the corrected threshold and an uncorrected 0.05 level.

## Conclusion

The five-minute exposure buys real extra kill: the surrogate log reduction rises by 0.748 log CFU/g on
average, from 1.651 to 2.399, and this is the strongest effect in the family. It costs something too.
Peroxide value rises by 0.623 meq O2/kg oil and the trained-panel rancid odour score rises by 0.587
points, both significant against the corrected threshold, so the longer exposure leaves the kernels
more oxidised and more rancid-smelling after four weeks of storage. Kernel lightness and moisture
content are statistically indistinguishable between the two durations, so appearance and drying are
not the deciding factors.

Whether to adopt five minutes therefore depends on how much extra log reduction the process needs and
how much quality loss the product can absorb. If the hazard analysis calls for more than about 1.7 log
of surface reduction, five minutes is the only one of the two durations that delivers it on average,
and the quality penalty at these magnitudes stays in the low end of the rancid odour scale (mean 1.917
out of 6). If two minutes already meets the required reduction, the longer treatment is not worth
adopting, because it adds oxidation and rancid odour with no compensating gain on the other declared
outcomes. This single-harvest, single-power-setting study cannot say how the trade-off shifts across
harvests, power settings, or storage times beyond four weeks.
