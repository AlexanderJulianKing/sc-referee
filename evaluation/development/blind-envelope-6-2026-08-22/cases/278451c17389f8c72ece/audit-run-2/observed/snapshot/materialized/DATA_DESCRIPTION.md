# Data description

## File

`lettuce_harvest.csv` — the harvest record for the butterhead lettuce nutrient
formulation trial. 120 data rows plus one header row.

## What one row represents

One row is one harvested lettuce head: a single plant, cut at one plant position
in one nutrient-film gutter, weighed fresh on the day of harvest.

## Scale of the trial

- 10 nutrient-film growing gutters, each with its own reservoir and dosing line.
- 12 plant positions along every gutter, numbered from the dosing end.
- 10 x 12 = 120 harvested heads, and therefore 120 rows.

## Groups compared

| Formulation label  | Description                        | Gutters                 | Harvested heads |
|--------------------|------------------------------------|-------------------------|-----------------|
| `standard`         | Standard nutrient formulation      | G01, G03, G05, G07, G09 | 60              |
| `raised_potassium` | Formulation with raised potassium  | G02, G04, G06, G08, G10 | 60              |

The two formulations are interleaved across the glasshouse rather than banked at
one end.

## Columns

| Column                  | Type            | Units / values                              | Meaning                                                                 |
|-------------------------|-----------------|---------------------------------------------|-------------------------------------------------------------------------|
| `gutter_code`           | text            | `G01` … `G10`                                | Identifier of the nutrient-film gutter the head was grown in.            |
| `formulation`           | text (2 levels) | `standard`, `raised_potassium`               | Nutrient formulation dosed to that gutter's reservoir.                   |
| `position_along_gutter` | integer         | 1 … 12                                       | Plant position along the gutter, counted from the dosing end (1) to the far end (12). |
| `head_fresh_mass_g`     | number          | grams, recorded to 0.1 g                     | Fresh mass of the cut head at harvest.                                   |
| `harvest_date`          | date            | `2026-06-15` or `2026-06-16` (ISO `YYYY-MM-DD`) | Morning on which that gutter was cut. G01–G05 were cut on 15 June, G06–G10 on 16 June. |

## Notes on the recorded values

- Head fresh mass runs about 244 g on average under the standard formulation and
  about 277 g under the raised-potassium formulation.
- Head-to-head variation within a gutter is roughly 30 g, and gutter mean masses
  differ from one another by roughly 25 g.
- Heads at the far end of a gutter tend to run a little lighter than heads near
  the dosing end, consistent with nutrient depletion along the channel.
- There are no missing values; every one of the 120 plant positions was cut and
  weighed.

## Reproducing the file

`make_data.py` writes `lettuce_harvest.csv`. It uses only the Python standard
library and a fixed random seed, so re-running it reproduces the same file
byte for byte:

```
python3 make_data.py
```
