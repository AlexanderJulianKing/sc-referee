# Data description

Camel dairy research unit, mid-lactation mineral supplement comparison. Ninety-six lactating
dromedary dams, forty-eight fed the standard mineral block and forty-eight fed an enriched mineral
block with added copper, zinc and selenium. Each dam was measured once, after eight weeks on her
assigned regimen.

Files in this directory:

| File | Rows | What it holds |
| --- | --- | --- |
| `make_data.py` | n/a | Seeded generator that writes both CSV files. Fixed seed 20260824. |
| `camel_milk_outcomes.csv` | 96 data rows plus a header | Subject-level measurements, one row per dam. |
| `pipeline_family_results.csv` | 5 data rows plus a header | Results table handed over by the unit's upstream statistics pipeline stage, one row per declared outcome. |

## `camel_milk_outcomes.csv`

One row is one lactating dam: her identifier, the regimen she was fed, and her single measured value
for each of the five declared outcomes. Every dam has a value for every outcome, so there are no
empty cells.

| Column | Type | Meaning |
| --- | --- | --- |
| `camel_id` | text | Unique dam identifier, `CAM001` through `CAM096`. |
| `supplement_group` | text | Regimen fed to that dam. Exactly two values: `mineral_standard` and `mineral_enriched`. |
| `milk_yield_l_per_day` | number, 2 decimals | Daily milk yield in litres at the week-eight measurement. |
| `milk_fat_pct` | number, 2 decimals | Milk fat content, percent by weight. |
| `milk_protein_pct` | number, 2 decimals | Milk protein content, percent by weight. |
| `body_condition_score` | number, 1 decimal | Body condition score on the one-to-five scale. |
| `plasma_glucose_mmol_l` | number, 2 decimals | Plasma glucose concentration in millimoles per litre. |

Ranges present in the file: milk yield 3.42 to 10.74 L/day, milk fat 2.41 to 4.44 percent, milk
protein 2.50 to 3.74 percent, body condition 2.10 to 4.50, plasma glucose 3.72 to 7.15 mmol/L.

## `pipeline_family_results.csv`

One row is one declared outcome, listed in the protocol's declared order: milk yield, milk fat, milk
protein, body condition score, plasma glucose. The upstream pipeline stage ran the five two-group
comparisons and adjusted all five together as one family before writing this file. The adjusted
column therefore already accounts for the family of five; nothing downstream needs to adjust again.

| Column | Type | Meaning |
| --- | --- | --- |
| `outcome_name` | text | Name of the declared outcome, matching the corresponding column name in the subject table. |
| `raw_p_value` | number, 6 decimals | Unadjusted p-value from the upstream stage's two-group comparison for that outcome. |
| `adjusted_p_value` | number, 6 decimals | The same p-value after the upstream stage's family-wide multiplicity adjustment across all five declared outcomes (Holm step-down). |

## Reproducing the CSV files

    /Users/alexanderking/Desktop/random_stuff/sc-referee-vnext/.venv/bin/python make_data.py

The generator draws from a fixed seed, so both files are reproduced byte for byte. It writes the
subject table first, then derives the pipeline results table from that same subject table, which is
why the p-values in the second file correspond to the data in the first. Values are drawn per dam
with a small shared dam-level term, so milk yield and body condition co-vary mildly, and each drawn
value is held inside the plausible range stated for that outcome.
