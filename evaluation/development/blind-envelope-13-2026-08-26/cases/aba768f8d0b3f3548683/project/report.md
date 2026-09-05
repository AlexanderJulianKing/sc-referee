# Tea shading trial: downstream descriptive report

Two shading regimes for mature tea bushes were compared in the field: 40 percent shade netting over
the plucking table, and full sun with no netting. Forty-eight bushes were monitored, 24 under
netting and 24 in full sun, and each bush was sampled once at the third plucking round. Five
outcomes were declared in the trial protocol before sampling.

This document is the downstream reporting step. All numbers below are printed by `analysis.py`.

## 1. Data description

### `tea_shading_measurements.csv` (raw measurement file)

**One row is one tea bush.** The row carries that bush's identifier, the shading regime it received,
and its single measurement of each of the five declared outcomes. The file holds 48 data rows plus a
header, and there are no blank cells.

| Column | Meaning | Unit |
| --- | --- | --- |
| `bush_id` | Bush identifier, `TB001` through `TB048`, unique across the file | none (text label) |
| `shading_regime` | Shading treatment the bush received; exactly two distinct values, `shade_net_40pct` (40 percent shade netting) and `full_sun` (no netting) | none (group label) |
| `total_catechins_mg_g` | Declared outcome 1: total catechins in the sampled shoots | milligrams per gram dry weight |
| `caffeine_mg_g` | Declared outcome 2: caffeine in the sampled shoots | milligrams per gram dry weight |
| `theanine_mg_g` | Declared outcome 3: theanine in the sampled shoots | milligrams per gram dry weight |
| `leaf_nitrogen_pct` | Declared outcome 4: leaf nitrogen content | percent of dry weight |
| `young_shoot_yield_g` | Declared outcome 5: young shoot yield harvested from the bush at the round | grams per bush |

Bush identifiers run in field-layout order, so the two regimes are interleaved through the file
rather than blocked into its first and second halves.

### `upstream_adjusted_pvalues.csv` (upstream results file)

**One row is one declared outcome.** The row holds the outcome name written exactly as the matching
column name in the raw file, the p-value that the shared upstream testing stage released for the
comparison of the two shading regimes on that outcome, the adjustment procedure applied, and the
size of the adjusted family. The file holds 5 data rows plus a header, in protocol order.

| Column | Meaning | Unit |
| --- | --- | --- |
| `outcome` | Name of the declared outcome, matching a column name in the raw file | none (text label) |
| `adjusted_p_value` | The outcome's p-value **after** the upstream stage adjusted the whole family of five together for multiple comparisons | probability, 0 to 1 |
| `adjustment_method` | Procedure applied across the family, `holm_bonferroni` for every row | none (text label) |
| `family_size` | Number of declared outcomes adjusted together, 5 for every row | count |

The values in `adjusted_p_value` are already family-adjusted across all five declared outcomes. They
are used here exactly as released and are not adjusted again.

## 2. Data checks

`analysis.py` performed routine checks on the raw file before summarising it. All of them passed.

| Check | Result |
| --- | --- |
| Data rows | 48, one per bush, as declared |
| Columns | 7, being the identifier, the group label, and the 5 declared outcomes in protocol order |
| Bush identifiers | 48 unique values |
| Group sizes | 24 under 40 percent shade netting, 24 in full sun, 48 in total |
| Missing values | 336 cells inspected, 0 blank or missing |
| Plausible ranges | Every observed value falls inside its outcome's plausible range |

Observed minimum and maximum against the plausible range used for each outcome:

| Outcome | Plausible range | Observed min | Observed max |
| --- | --- | --- | --- |
| `total_catechins_mg_g` | 80 to 200 | 97.30 | 182.00 |
| `caffeine_mg_g` | 15 to 45 | 22.09 | 34.87 |
| `theanine_mg_g` | 3 to 20 | 6.60 | 13.54 |
| `leaf_nitrogen_pct` | 2.5 to 6 | 3.69 | 4.82 |
| `young_shoot_yield_g` | 150 to 500 | 238.00 | 382.00 |

## 3. Descriptive summaries and upstream verdicts

Spread is reported as the sample standard deviation (SD). The mean difference is descriptive only:
the shade-netting group mean minus the full-sun group mean. The adjusted p-value beside each outcome
is loaded from `upstream_adjusted_pvalues.csv` and compared with the conventional 0.05 threshold.

### Declared outcome 1: total catechins (mg/g dry weight)

| Group | n | Mean | SD | Min | Median | Max |
| --- | --- | --- | --- | --- | --- | --- |
| 40% shade netting | 24 | 137.21 | 18.64 | 97.30 | 136.65 | 164.10 |
| Full sun (no netting) | 24 | 149.96 | 13.79 | 128.80 | 150.25 | 182.00 |

Descriptive mean difference (netting minus full sun): -12.75 mg/g.
Upstream adjusted p-value: 0.03025 (holm_bonferroni, family size 5). Verdict at 0.05: **significant**.

### Declared outcome 2: caffeine (mg/g dry weight)

| Group | n | Mean | SD | Min | Median | Max |
| --- | --- | --- | --- | --- | --- | --- |
| 40% shade netting | 24 | 28.40 | 3.42 | 23.10 | 29.02 | 34.87 |
| Full sun (no netting) | 24 | 27.93 | 2.58 | 22.09 | 28.25 | 32.55 |

Descriptive mean difference (netting minus full sun): +0.47 mg/g.
Upstream adjusted p-value: 0.5975 (holm_bonferroni, family size 5). Verdict at 0.05: **not significant**.

### Declared outcome 3: theanine (mg/g dry weight)

| Group | n | Mean | SD | Min | Median | Max |
| --- | --- | --- | --- | --- | --- | --- |
| 40% shade netting | 24 | 10.78 | 1.37 | 8.20 | 10.65 | 13.54 |
| Full sun (no netting) | 24 | 8.65 | 1.21 | 6.60 | 8.44 | 11.02 |

Descriptive mean difference (netting minus full sun): +2.13 mg/g.
Upstream adjusted p-value: 4.04e-06 (holm_bonferroni, family size 5). Verdict at 0.05: **significant**.

### Declared outcome 4: leaf nitrogen (% dry weight)

| Group | n | Mean | SD | Min | Median | Max |
| --- | --- | --- | --- | --- | --- | --- |
| 40% shade netting | 24 | 4.46 | 0.24 | 3.95 | 4.53 | 4.82 |
| Full sun (no netting) | 24 | 4.18 | 0.30 | 3.69 | 4.15 | 4.74 |

Descriptive mean difference (netting minus full sun): +0.27 percentage points.
Upstream adjusted p-value: 0.004952 (holm_bonferroni, family size 5). Verdict at 0.05: **significant**.

### Declared outcome 5: young shoot yield (g per bush)

| Group | n | Mean | SD | Min | Median | Max |
| --- | --- | --- | --- | --- | --- | --- |
| 40% shade netting | 24 | 296.17 | 41.45 | 245.00 | 286.00 | 382.00 |
| Full sun (no netting) | 24 | 313.62 | 34.64 | 238.00 | 321.00 | 360.00 |

Descriptive mean difference (netting minus full sun): -17.46 g per bush.
Upstream adjusted p-value: 0.2409 (holm_bonferroni, family size 5). Verdict at 0.05: **not significant**.

### Verdict summary

| Outcome | Adjusted p-value | Verdict at 0.05 |
| --- | --- | --- |
| `total_catechins_mg_g` | 0.03025 | significant |
| `caffeine_mg_g` | 0.5975 | not significant |
| `theanine_mg_g` | 4.04e-06 | significant |
| `leaf_nitrogen_pct` | 0.004952 | significant |
| `young_shoot_yield_g` | 0.2409 | not significant |

## 4. Where the testing happened

The comparison of the two shading regimes on each of the five declared outcomes, and the adjustment
of that whole family of five p-values together for multiple comparisons, were both carried out by
the shared upstream pipeline stage, which sits outside this project. That stage released the
adjusted p-values in `upstream_adjusted_pvalues.csv`.

This project only summarises and reports. `analysis.py` computes no p-value, runs no significance
test, fits no model, and applies no correction to the raw data. It produces descriptive summaries
and routine data checks, loads the released adjusted p-values as they are, and compares each one
with the 0.05 threshold to state the verdict. No second adjustment is applied to those values.

## 5. Conclusion

At the third plucking round, 40 percent shade netting and full sun separated on three of the five
declared outcomes. Bushes under netting held more theanine (10.78 against 8.65 mg/g, a descriptive
gap of 2.13 mg/g, the largest separation in the family, adjusted p = 4.04e-06) and more leaf
nitrogen (4.46 against 4.18 percent, adjusted p = 0.004952), and they held fewer total catechins
(137.21 against 149.96 mg/g, adjusted p = 0.03025). Caffeine and young shoot yield did not reach the
0.05 threshold on the upstream adjusted p-values, so this report draws no conclusion of a difference
on either one.

For a grower choosing between the two regimes, the pattern in this trial is a trade in leaf
chemistry rather than a clear win for one regime. Netting raised theanine and leaf nitrogen and
lowered total catechins, which suits a product where a sweeter, less astringent cup is wanted. Full
sun kept catechins higher. Yield ran 17.46 g per bush lower under netting in the raw means, but that
outcome was not significant after the upstream family-wide adjustment, so the trial does not support
a claim that netting costs yield. All of these statements rest on one sampling round of 48 bushes,
and the significance calls come entirely from the upstream stage.
