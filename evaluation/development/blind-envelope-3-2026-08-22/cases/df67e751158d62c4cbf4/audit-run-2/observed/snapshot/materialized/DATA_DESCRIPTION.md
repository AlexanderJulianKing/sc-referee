# Data description: eggshell quality trial (limestone vs oyster-shell calcium)

## File

`eggshell_quality.csv` — 216 data rows plus one header row (217 lines total), comma separated,
UTF-8, no missing values.

The file is produced by `make_data.py` (fixed seed `20260822`). The values are invented for this
project; re-running the generator reproduces the file byte for byte.

## What one row represents

One row is **one sampled hen and the single freshly laid egg measured from her** at the end of the
trial. Each row therefore carries one shell-thickness measurement and one egg-weight measurement.

## Units and counts

| Level | Count |
|---|---|
| House | 1 |
| Floor pens | 18 (9 per diet) |
| Hens housed per pen | about 40 |
| Hens caught at random and sampled per pen | 12 |
| Eggs measured (one per sampled hen) | 216 |
| Rows in the file | 216 |

The design is balanced: every pen contributes exactly 12 rows, and each diet contributes
9 pens x 12 hens = 108 measured eggs.

## The two groups

The `diet` column splits the file into the two calcium sources compared in the trial:

- `limestone` — limestone calcium source, pens `P01` through `P09`, 108 rows.
- `oyster_shell` — oyster-shell calcium source, pens `P10` through `P18`, 108 rows.

Diet was assigned at the pen level, so all 12 rows sharing a `pen_id` share the same `diet` value.

## Columns

| Column | Type | Units | Description |
|---|---|---|---|
| `pen_id` | text | — | Identifier of the floor pen the hen was housed in. Format `Pnn`, values `P01`–`P18`. 18 distinct values, 12 rows each. |
| `diet` | text | — | Calcium source fed to that pen for the whole trial. Two values: `limestone`, `oyster_shell`. |
| `hen_id` | text | — | Identifier of the individual sampled hen. Format `Pnn-Hkk`, where `Pnn` repeats the pen and `Hkk` runs `H01`–`H12` within the pen. 216 distinct values, one per row. |
| `shell_thickness_mm` | number | millimetres | Shell thickness of the measured egg, rounded to 4 decimal places. Observed range 0.3143 to 0.4200. |
| `egg_weight_g` | number | grams | Weight of the same measured egg, rounded to 2 decimal places. Observed range 53.11 to 71.85. |

Header names are lowercase words joined by underscores, and the identifier column is named after
the pen (`pen_id`).

## Values as generated

| Quantity | limestone | oyster_shell |
|---|---|---|
| Eggs measured | 108 | 108 |
| Mean shell thickness (mm) | 0.3529 | 0.3707 |
| SD of shell thickness across all eggs in the diet (mm) | 0.0207 | 0.0213 |
| SD of the 9 pen means (mm) | 0.0084 | 0.0118 |
| Mean egg weight (g) | 61.40 | 62.12 |

Averaged over all 18 pens, the hen-to-hen standard deviation of shell thickness inside a pen is
0.0191 mm. The generator draws thickness as a diet mean (0.355 mm limestone, 0.372 mm oyster shell)
plus a pen offset (SD 0.010 mm) plus a hen offset (SD 0.018 mm); egg weight is drawn as 62 g plus a
pen offset (SD 1.2 g) plus a hen offset (SD 3.2 g).
