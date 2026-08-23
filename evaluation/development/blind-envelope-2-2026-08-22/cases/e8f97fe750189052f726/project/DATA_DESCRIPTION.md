# Data description

## File

`wing_size.csv` — the single data file for this project. It is comma separated, has a header row,
and holds 192 data rows.

`make_data.py` is the generator that produced it. It uses only the Python standard library and a
fixed random seed (20260822), so rerunning it with `/usr/local/bin/python3 make_data.py` rewrites
the identical file.

## What one row represents

One row is one measured adult female fly: a single mounted wing from a single fly, together with the
rearing vial that fly came from, the diet that vial received, and the day the wing was measured.

## Units and counts

- 16 rearing vials, labelled `V01` through `V16`. The vial is the unit that received a diet: each
  vial got a fresh batch of medium, the same number of seeded eggs, and one incubator position, and
  the whole vial was assigned to one diet.
- 12 measured adult female flies were sampled from each vial.
- 16 vials x 12 flies = 192 measured flies, so 192 data rows.

## The two groups

| Group value in `diet` | Medium | Vials | Vial labels | Measured flies |
|---|---|---|---|---|
| `standard` | standard cornmeal-molasses medium | 8 | V01, V03, V05, V07, V09, V11, V13, V15 | 96 |
| `high_sugar` | the same medium with added sucrose | 8 | V02, V04, V06, V08, V10, V12, V14, V16 | 96 |

The two diets alternate across the vial numbering because the vials were spread across incubator
shelves in that order.

## Columns

| Column | Type | Values | Meaning |
|---|---|---|---|
| `vial_id` | text | `V01`–`V16` | The rearing vial the fly developed in. Repeats 12 times, once per fly sampled from that vial. |
| `diet` | text | `standard` or `high_sugar` | The larval diet the whole vial was assigned to. Constant within a vial. |
| `fly_id` | text | `F01`–`F12` | The fly's identifier within its own vial. It is not unique on its own; `vial_id` plus `fly_id` identifies a fly uniquely. |
| `wing_centroid_size_mm` | number | 2.081–2.623 | Wing centroid size in millimetres for the one wing mounted from that fly. Rounded to three decimal places. This is the outcome. |
| `day_after_eclosion` | integer | 3, 4, or 5 | How many days after the fly emerged from the pupal case its wing was measured. Most flies from a vial were scored in one sitting, so the values cluster within a vial. |

## How the values were generated

Each measurement is the sum of three parts:

    wing_centroid_size_mm = diet mean + vial effect + fly-to-fly noise

- Diet means: 2.42 mm for `standard`, 2.31 mm for `high_sugar`.
- Vial effect: one draw per vial from a normal distribution with mean 0 and standard deviation
  0.05 mm, so vials differ from one another.
- Fly-to-fly noise: one draw per fly from a normal distribution with mean 0 and standard deviation
  0.07 mm.

In the file as written, the standard-diet flies average 2.422 mm and the high-sugar flies average
2.305 mm. The spread of the 8 vial means is 0.045 mm within the standard group and 0.037 mm within
the high-sugar group, and the average spread of flies inside a single vial is 0.070 mm.
