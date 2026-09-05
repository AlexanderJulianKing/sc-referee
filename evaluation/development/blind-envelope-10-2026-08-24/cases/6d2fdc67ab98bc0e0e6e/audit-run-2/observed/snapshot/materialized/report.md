# Mid-lactation mineral supplement comparison in dromedary dams

Camel dairy research unit. Ninety-six lactating dromedary dams were fed either the standard mineral
block or an enriched mineral block with added copper, zinc and selenium, forty-eight dams per
regimen. Each dam was measured once, after eight weeks on her assigned regimen.

All numbers below were produced or read by `analysis.py`, which was run against the two CSV files in
this directory.

## Data description

Two data files are used.

### `camel_milk_outcomes.csv` (subject-level table, 96 data rows)

One row is one lactating dam. It carries her identifier, the regimen she was fed, and her single
week-eight value for each of the five declared outcomes. There is no repeated measurement and no
follow-up row: one dam appears exactly once.

| Column | Meaning |
| --- | --- |
| `camel_id` | Unique dam identifier, text. |
| `supplement_group` | Regimen fed to that dam. Exactly two values, `mineral_standard` and `mineral_enriched`. |
| `milk_yield_l_per_day` | Daily milk yield in litres at the week-eight measurement. |
| `milk_fat_pct` | Milk fat content, percent by weight. |
| `milk_protein_pct` | Milk protein content, percent by weight. |
| `body_condition_score` | Body condition score on the one-to-five scale. |
| `plasma_glucose_mmol_l` | Plasma glucose concentration in millimoles per litre. |

### `pipeline_family_results.csv` (upstream results table, 5 data rows)

One row is one declared outcome, in the protocol's declared order. This table was produced earlier by
the unit's upstream statistics pipeline stage, which ran the five two-group comparisons and adjusted
them.

| Column | Meaning |
| --- | --- |
| `outcome_name` | Name of the declared outcome, matching the corresponding column of the subject table. |
| `raw_p_value` | Unadjusted p-value from the upstream stage's two-group comparison for that outcome. |
| `adjusted_p_value` | The same p-value after the upstream stage's family-wide multiplicity adjustment across all five declared outcomes. |

`analysis.py` computes no significance test. It summarises the subject table and reads its verdicts
from the `adjusted_p_value` column of the pipeline table.

## Descriptive summaries

Count, mean and sample standard deviation (SD, divisor n-1) per regimen.

| Outcome | Regimen | n | Mean | SD |
| --- | --- | ---: | ---: | ---: |
| Daily milk yield (L/day) | mineral_standard | 48 | 7.121 | 1.742 |
| Daily milk yield (L/day) | mineral_enriched | 48 | 7.961 | 1.440 |
| Milk fat (%) | mineral_standard | 48 | 3.281 | 0.471 |
| Milk fat (%) | mineral_enriched | 48 | 3.395 | 0.415 |
| Milk protein (%) | mineral_standard | 48 | 3.098 | 0.270 |
| Milk protein (%) | mineral_enriched | 48 | 3.137 | 0.262 |
| Body condition score (1-5) | mineral_standard | 48 | 2.985 | 0.419 |
| Body condition score (1-5) | mineral_enriched | 48 | 3.290 | 0.489 |
| Plasma glucose (mmol/L) | mineral_standard | 48 | 5.336 | 0.645 |
| Plasma glucose (mmol/L) | mineral_enriched | 48 | 5.290 | 0.621 |

The plain difference between the two means above, enriched minus standard, is +0.840 L/day for milk
yield, +0.114 percentage points for milk fat, +0.039 percentage points for milk protein, +0.304
points for body condition score, and -0.046 mmol/L for plasma glucose. These are descriptive
differences only. They are not test statistics and carry no p-value or confidence interval.

## Data quality checks

Every check below passed.

Subject table:

- Row count: 96 rows found, 96 expected.
- Column names and order match the declared schema.
- 96 distinct `camel_id` values across 96 rows.
- `supplement_group` holds exactly the two expected labels, `mineral_enriched` and `mineral_standard`.
- Group sizes: 48 dams on `mineral_standard`, 48 dams on `mineral_enriched`.
- Missing values: 0 empty cells across all columns, so every dam has a value for every outcome.
- Values inside the plausible range declared for each outcome, with 0 values outside in every case:
  milk yield observed 3.42 to 10.74 (plausible 3.00 to 12.00); milk fat observed 2.41 to 4.44
  (plausible 2.00 to 4.50); milk protein observed 2.50 to 3.74 (plausible 2.50 to 4.00); body
  condition observed 2.10 to 4.50 (plausible 1.00 to 5.00); plasma glucose observed 3.72 to 7.15
  (plausible 3.50 to 7.50).

Pipeline results table:

- Row count: 5 rows found, 5 expected, one per declared outcome.
- Rows follow the protocol's declared order.
- Missing values: 0 empty cells.
- All raw and adjusted p-values lie within [0, 1].
- No adjusted p-value falls below its own raw p-value.

## Declared family of five outcomes

The five outcomes are listed in the order declared in the protocol. The raw and adjusted p-values are
taken verbatim from `pipeline_family_results.csv`. The multiplicity adjustment covered the whole
declared family of five outcomes together and was performed upstream, before this project received
the file. Nothing here re-tests or re-adjusts anything. Each verdict is read off the adjusted
p-value at the 0.05 level.

| # | Outcome | Raw p | Adjusted p | Verdict at adjusted p < 0.05 |
| ---: | --- | ---: | ---: | --- |
| 1 | `milk_yield_l_per_day` | 0.011603 | 0.046413 | significant |
| 2 | `milk_fat_pct` | 0.212668 | 0.638003 | not significant |
| 3 | `milk_protein_pct` | 0.472870 | 0.945741 | not significant |
| 4 | `body_condition_score` | 0.001493 | 0.007465 | significant |
| 5 | `plasma_glucose_mmol_l` | 0.720178 | 0.945741 | not significant |

Two of the five declared outcomes are significant on the adjusted values: daily milk yield and body
condition score.

## Conclusion

After eight weeks, dams on the enriched mineral block showed higher daily milk yield and higher body
condition score than dams on the standard block, and both of those outcomes remain significant after
the upstream adjustment across the declared family of five (adjusted p = 0.046413 and 0.007465).
Milk fat, milk protein and plasma glucose showed no significant difference between regimens on the
adjusted values, and their descriptive group means differ only slightly.

Two limits are worth stating plainly. First, each dam was measured once at week eight, so these
results describe the state of the herd at that single time point and say nothing about how the
outcomes moved over the eight weeks. Second, the milk yield result sits close to the 0.05 line
(adjusted p = 0.046413), so it is the less secure of the two positive findings; the body condition
result is farther from the line. Taken together, the data support a modest benefit of the enriched
mineral block on yield and body condition, and give no evidence of an effect on milk composition or
plasma glucose.
