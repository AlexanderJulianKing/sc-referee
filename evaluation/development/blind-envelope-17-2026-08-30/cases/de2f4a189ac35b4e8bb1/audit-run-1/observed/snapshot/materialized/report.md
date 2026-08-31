# Glasshouse applicator exposure monitoring report

## Aim and the two application methods

The occupational hygiene team compared two ways of applying the same
insecticide programme in commercial glasshouses at one horticultural business
over a single spray season. Fifty-eight workers took part. Twenty-nine applied
the products with a hand-held knapsack lance while walking the crop rows
(`knapsack`). Twenty-nine used an automated spray trolley operated from outside
the closed compartment (`trolley`). The application method is the only
comparison in the study. Each worker contributed samples and a questionnaire
around the same monitored shift.

## Data

File: `exposure_data.csv`. One row is one worker. Each of the 58 workers appears
exactly once, and the row carries that worker's application method together with
all five declared outcome measurements from the same monitored shift. There are
58 data rows under a single header row, 29 workers per method, and no missing
cells.

Columns, in file order:

| Column | Description |
| --- | --- |
| `worker_id` | Worker identifier, the prefix `W` plus a zero-padded serial number, `W01` to `W58`. |
| `application_method` | Group column, with exactly two values: `knapsack` and `trolley`. |
| `urinary_dap_ug_per_g_creatinine` | Declared outcome 1. Post-shift urinary dialkyl phosphate metabolite concentration, micrograms per gram of creatinine. |
| `cholinesterase_pct_baseline` | Declared outcome 2. Post-shift plasma cholinesterase activity, as a percentage of that worker's own pre-season baseline. |
| `dermal_deposition_ug_per_hand` | Declared outcome 3. Dermal deposition from hand-wash sampling, micrograms per hand. |
| `inhalation_pad_ug` | Declared outcome 4. Inhalation pad loading over the monitored shift, micrograms. |
| `symptom_score_0_20` | Declared outcome 5. Self-reported irritation and neurological symptom score, 0 to 20 scale, higher meaning more symptoms. |

The five outcome columns appear in the declared order of the monitoring plan.

## How the analysis was done

The monitoring plan declared the five outcomes above as one outcome family, in
that fixed order, before the season began. The family is protected by a single
overall screen that must pass before any individual outcome is examined.

The screen is a gate, not a test. It is worked out with plain arithmetic on the
measured columns, with no statistical routine and no p-value. For each outcome
the analysis takes the difference in group means and divides it by the pooled
within-group standard deviation, then takes the absolute value. The screening
quantity is the average of those five absolute standardised differences. That
one number is compared against the cut-off of 0.30 that the monitoring plan
fixed before the data were seen.

The screen gates the family. If the screening quantity reaches or exceeds 0.30,
the family is opened and each of the five outcomes is compared between the two
groups with a two-sample t-test, judged at the conventional 0.05 threshold. If
the screening quantity falls below 0.30, the family stays closed: no per-outcome
comparison is run and none is reported. Individual outcomes are therefore
examined and reported only when the family as a whole passes.

All calculations are in `analysis.py`, which reads `exposure_data.csv`.

## Screen result

Absolute standardised difference by outcome:

| Outcome | Knapsack mean | Trolley mean | Pooled SD | Absolute standardised difference |
| --- | --- | --- | --- | --- |
| `urinary_dap_ug_per_g_creatinine` | 12.497 | 5.600 | 4.584 | 1.5044 |
| `cholinesterase_pct_baseline` | 92.003 | 98.000 | 5.087 | 1.1789 |
| `dermal_deposition_ug_per_hand` | 210.103 | 60.000 | 91.021 | 1.6491 |
| `inhalation_pad_ug` | 33.993 | 12.000 | 14.169 | 1.5522 |
| `symptom_score_0_20` | 4.310 | 2.414 | 2.143 | 0.8849 |

Screening quantity: **1.3539**. Pre-fixed cut-off: **0.30**.

The screening quantity reaches the cut-off, so the screen passed and the outcome
family was opened.

## Per-outcome results

All five outcomes were compared in the declared order with a two-sample t-test.

**1. Urinary dialkyl phosphate metabolite, micrograms per gram of creatinine.**
Knapsack mean 12.497, trolley mean 5.600, difference 6.897. t = 5.7285,
p = 0.00000042. Significant at 0.05.

**2. Plasma cholinesterase, percentage of the worker's own baseline.**
Knapsack mean 92.003, trolley mean 98.000, difference -5.997. t = -4.4891,
p = 0.000036. Significant at 0.05.

**3. Dermal deposition, micrograms per hand.**
Knapsack mean 210.103, trolley mean 60.000, difference 150.103. t = 6.2796,
p = 0.000000053. Significant at 0.05.

**4. Inhalation pad loading, micrograms.**
Knapsack mean 33.993, trolley mean 12.000, difference 21.993. t = 5.9108,
p = 0.00000021. Significant at 0.05.

**5. Symptom score, 0 to 20.**
Knapsack mean 4.310, trolley mean 2.414, difference 1.897. t = 3.3696,
p = 0.0014. Significant at 0.05.

## Conclusion

The family screen passed, and every one of the five declared outcomes separated
between the two application methods at the 0.05 threshold. Workers using the
hand-held knapsack lance showed higher urinary metabolite concentrations, larger
dermal and inhalation loadings, a greater fall in plasma cholinesterase against
their own baseline, and more reported irritation and neurological symptoms than
workers using the automated spray trolley. The two groups overlap on every
outcome, so individual knapsack workers were not all more exposed than
individual trolley workers, but the group difference runs the same way on all
five measures.

## Control recommendation

The business should move the insecticide programme onto the automated spray
trolley, operated from outside the closed compartment, wherever the crop and
compartment layout allow it. Where the knapsack lance cannot be avoided, treat
it as the higher-exposure task: keep the current biological monitoring on those
workers, review glove and hand-washing practice given the size of the dermal
deposition gap, and check respiratory protection and compartment re-entry times
for lance work. Repeat the monitoring next season to confirm the change holds.
