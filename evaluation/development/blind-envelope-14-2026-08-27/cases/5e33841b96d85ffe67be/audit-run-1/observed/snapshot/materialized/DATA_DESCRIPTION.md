# Data description

File: `ors_trial.csv`

## What one row represents

One row is one child. Each child is a single participant admitted to the paediatric ward
with acute watery gastroenteritis, aged six to thirty-six months, allocated to one of the two
oral rehydration solutions and followed for the first forty-eight hours after admission. All
of that child's recorded outcomes sit on that one row. No child appears twice, and there are
no repeated-measure rows.

The file has a header row and 84 data rows: 42 children on each solution. Every cell is
filled; there are no blanks and no missing-value codes.

## Columns

Columns appear in this order. The six outcome columns are in the order the protocol declared
them.

| # | Column | Type | Unit | Meaning |
|---|--------|------|------|---------|
| 1 | `child_id` | text | none | Participant identifier, `C001` through `C084`, assigned in order of admission. Unique across the file. |
| 2 | `solution` | text | none | Group column. Exactly two values: `glucose_based` (standard glucose-based reduced-osmolarity solution) and `rice_based` (rice-based solution). |
| 3 | `diarrhoea_duration_h` | integer | hours | Declared outcome 1 (primary). Hours from admission until diarrhoea stopped. Recorded to the nearest hour. |
| 4 | `stool_output_g_per_kg_24h` | decimal | g/kg | Declared outcome 2 (primary). Total stool output over the first 24 hours, per kilogram of admission body weight. Recorded to one decimal place. |
| 5 | `ors_intake_ml_per_kg_24h` | integer | mL/kg | Declared outcome 3. Total rehydration solution taken over the first 24 hours, per kilogram of admission body weight. Recorded to the nearest millilitre per kilogram. |
| 6 | `vomiting_episodes_24h` | integer | count | Declared outcome 4. Number of vomiting episodes during the first 24 hours. Whole numbers from 0 to 7. |
| 7 | `weight_change_pct_48h` | decimal | percent | Declared outcome 5. Body weight at 48 hours as a percentage change from admission weight. Positive means weight gained. Recorded to one decimal place. |
| 8 | `serum_sodium_mmol_per_l_24h` | integer | mmol/L | Declared outcome 6. Serum sodium measured at 24 hours after admission. Reported by the laboratory as a whole number. |

## Observed value ranges in this file

These are the spans across all 84 children, both groups pooled. They are given so a reader can
check the file loaded correctly, not as results.

| Column | Minimum | Maximum |
|--------|---------|---------|
| `diarrhoea_duration_h` | 28 | 92 |
| `stool_output_g_per_kg_24h` | 28.1 | 128.1 |
| `ors_intake_ml_per_kg_24h` | 55 | 193 |
| `vomiting_episodes_24h` | 0 | 7 |
| `weight_change_pct_48h` | -1.2 | 5.5 |
| `serum_sodium_mmol_per_l_24h` | 131 | 144 |

## How the file was made

The values are synthetic, produced by `generate_data.py` in this directory with a fixed random
seed. Each child carries a hidden severity level that feeds every outcome, so that a child with
a longer illness also tends to show heavier stool output, higher intake, more vomiting, and less
weight gain. Group assignment used permuted blocks of four, two children per solution in each
block. No statistical comparison between the two groups was carried out while building the file.
