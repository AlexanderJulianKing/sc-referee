# Data description

## What one row represents

`data.csv` holds one row per animal. Each row is a single captive bred juvenile
bearded dragon from one hatch cohort, housed alone in its own vivarium for
twelve weeks under one of two ultraviolet B lamp types, with all five declared
outcomes measured once at the end of week twelve. There are 40 rows plus a
header row. There are no repeated rows, no summary rows, and no blank cells.

## Columns

The columns appear in this order: identifier, lamp group, then the five declared
outcomes in the order they were declared in the trial protocol.

| Column | Meaning | Unit | Type |
| --- | --- | --- | --- |
| `dragon_id` | Animal identifier, prefix `bd_` followed by a zero-padded two digit number, `bd_01` through `bd_40`. Unique for every row. | none | text |
| `lamp_type` | Ultraviolet B lamp the animal was housed under for the twelve weeks. Exactly two labels: `cfl` for the compact fluorescent lamp and `t5_ho` for the linear T5 high output lamp. | none | text |
| `plasma_25ohd3_nmol_l` | Plasma 25-hydroxyvitamin D3 at end of week twelve. Reported to one decimal place. | nmol/L | number |
| `plasma_ionised_calcium_mmol_l` | Plasma ionised calcium at end of week twelve. Reported to two decimal places. | mmol/L | number |
| `body_mass_gain_g` | Body mass gained over the twelve week period. Reported to one decimal place. | g | number |
| `snout_vent_length_gain_mm` | Snout to vent length gained over the twelve week period. Reported to one decimal place. | mm | number |
| `humeral_cortical_thickness_ratio` | Radiographic humeral cortical thickness ratio, cortical width divided by total bone width. Unitless, reported to three decimal places. | none (ratio) | number |

## Completeness

Every animal has a value for every outcome. There are no missing values and no
missing group labels. Twenty animals carry the `cfl` label and twenty carry the
`t5_ho` label.
