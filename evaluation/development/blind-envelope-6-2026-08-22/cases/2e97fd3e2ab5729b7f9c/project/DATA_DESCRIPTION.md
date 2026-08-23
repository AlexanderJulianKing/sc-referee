# Data description

## Files

| File | Contents |
| --- | --- |
| `kelp_blades.csv` | Raw blade measurements, one row per measured blade. 140 data rows plus one header row. |
| `make_data.py` | Generator that produced `kelp_blades.csv` (Python standard library only, fixed seed `20260822`). Rerunning it rewrites the same file. |

There is no second summary CSV. The per-dropper-line averages are not stored on
disk; `analysis.py` computes them from the raw file at run time.

## What one row represents

One row is **one measured blade of sugar kelp on one dropper line**. It is not a
dropper line and it is not a farm. Ten rows share a dropper line, because ten
blades were haphazardly selected and measured on each line after five months in
the water.

## Units and counts

- Longlines: 1. All dropper lines hang from the same longline.
- Dropper lines (the experimental units): **14**.
- Seeding-density groups: **2**, with 7 dropper lines each.
  - `standard` — the farm's standard seeding density, dropper lines `L01`–`L07`.
  - `reduced` — a reduced seeding density meant to give each plant more light,
    dropper lines `L08`–`L14`.
- Measured blades per dropper line: **10**.
- Total data rows: 14 x 10 = **140**.

The 140 blades are repeated measurements inside 14 lines, so blades on the same
line are not independent of one another. The dropper line is the unit that was
assigned a seeding density, and so the dropper line is the unit of replication.

## Columns of `kelp_blades.csv`

All five columns are present in every row; there are no missing values.

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `dropper_line` | text | none | Identifier of the dropper line the blade grew on. 14 distinct values, `L01` through `L14`. Repeats 10 times, once per measured blade on that line. |
| `seeding_density` | text | none | Seeding-density treatment applied to that whole dropper line. Two values: `standard` and `reduced`. Constant within a dropper line. |
| `blade_number` | integer | none | Index of the blade within its dropper line, 1 through 10, in the order the blades were measured. It is a within-line label only and carries no meaning across lines. |
| `blade_length_cm` | number, 1 decimal | centimetres | Length of the measured blade at harvest, five months after deployment. |
| `blade_wet_mass_g` | number, 1 decimal | grams | Wet mass of the same blade, measured immediately after it was taken from the water. Wet mass tracks blade length, so the two columns are strongly related and should not be treated as independent pieces of evidence. |

## How the values were generated

`make_data.py` draws each dropper line a line mean, then draws each blade around
that line mean, which is what makes blades on one line resemble each other:

- Grand mean blade length: 96 cm at standard density, 118 cm at reduced density.
- Variation between dropper lines (spread of the line means): about 15 cm.
- Variation between blades within one line: about 22 cm.
- Wet mass: about 5 g plus 2.4 g for every centimetre of blade length, plus
  about 18 g of extra scatter.
- Lengths are floored at 15 cm and masses at 5 g so no value is negative.

These are simulated values for a self-contained example project. They are not
measurements from a real seaweed farm, and the numbers should not be read as
evidence about any real cultivar, site, or season.
