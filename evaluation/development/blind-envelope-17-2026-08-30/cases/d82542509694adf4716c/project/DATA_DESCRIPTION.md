# Data description

File: `parrot_diet_data.csv`

One row is one adult African grey parrot: a single bird, individually housed, sampled and
scored once by the attending veterinarian at the end of the twelve-week feeding period. The
file holds 48 rows plus a header row, one row per bird, 24 birds on each diet. Every bird has
a value in every column; there are no missing cells and no extra rows.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `bird_id` | text | Bird identifier: the prefix `AGP` plus a two-digit zero-padded serial number, `AGP01` through `AGP48`. Unique for each bird. |
| `diet` | text | Group column. Exactly two values: `pellet` for the complete extruded pelleted diet, `seed` for the continued seed-based diet with fresh produce. |
| `plasma_retinol_ug_dl` | number, 1 decimal | Plasma retinol (vitamin A) at week twelve, in micrograms per decilitre. |
| `body_mass_g` | integer | Body mass at week twelve, in grams. |
| `plasma_calcium_mmol_l` | number, 2 decimals | Plasma total calcium at week twelve, in millimoles per litre. |
| `feather_condition_score` | integer | Feather condition score at week twelve on a 0 to 20 scale, higher meaning better plumage. |

The four outcome columns appear in the declared order of the study protocol: retinol, body
mass, calcium, feather condition score. Values are rounded to the precision a veterinary
laboratory report or a clinical score sheet would carry.

## Provenance

Values are fixed and committed to the CSV. They were produced once by `make_data.py`, which
draws each bird's outcomes from the per-group distributions stated in the study protocol and
rounds them for reporting. The generator is kept only for provenance; nothing reads the data
at run time except the analysis.
