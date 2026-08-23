# Data description: leaf-cutter ant forager loads

## Files

| File | Rows (excl. header) | Purpose |
| --- | --- | --- |
| `forager_loads.csv` | 160 | The study data: one row per intercepted forager. |
| `make_data.py` | n/a | The generator that produced the CSV (fixed seed `20260822`, run with `/usr/local/bin/python3`). |

There is one data file. No summary or aggregated CSV is part of this project.

## What one row represents

One row is **one returning forager that was intercepted on the trail and had its leaf fragment
weighed**. A row is a single worker ant, not a colony and not a repeated measurement of the same
worker: each worker appears exactly once.

## Units and counts

- **Experimental unit: the colony.** The fungicide was delivered through each colony's forage
  supply, so every worker in a colony shares the same exposure, the same queen, and the same fungus
  garden. Treatment was assigned to colonies, never to individual foragers.
- **16 colonies**, labelled `C01` through `C16`, each kept in its own foraging arena.
- **10 foragers weighed per colony**, so every colony contributes exactly 10 rows.
- **160 rows total** (16 colonies x 10 foragers).
- Foragers are **nested within colonies**: the 160 rows are not 160 independent observations of the
  treatment, because the treatment was applied only 16 times.

## The two groups

| `exposure_group` | Colonies | Colony IDs | Foragers | Meaning |
| --- | --- | --- | --- | --- |
| `control` | 8 | C01, C03, C05, C07, C09, C11, C13, C15 | 80 | Unexposed. Normal forage supply. |
| `exposed` | 8 | C02, C04, C06, C08, C10, C12, C14, C16 | 80 | Chronic sublethal fungicide dose in the forage supply. |

The two labels alternate across the colony numbering so that group is not confounded with colony
order. Group is a **colony-level** property: every row from a given colony carries the same label.

## Columns

The CSV has 6 columns, in this order. The same names are used in the analysis script and the report.

| Column | Type | Units / values | Level | Description |
| --- | --- | --- | --- | --- |
| `colony_id` | text | `C01`–`C16` (16 distinct values) | colony | Identifies the colony the forager came from. Appears on 10 rows. This is the grouping factor for the colony random effect. |
| `exposure_group` | text | `control` or `exposed` | colony | Treatment group of the colony. Constant within a colony. |
| `forager_id` | text | `F01`–`F10` | forager | Identifier of the forager **within its colony**. It is not unique on its own: `F01` occurs once in each of the 16 colonies. A forager is uniquely identified by the pair (`colony_id`, `forager_id`). |
| `head_width_mm` | number | millimetres, 2 decimals, observed range 1.59–2.46 | forager | Maximum head capsule width of the worker, the standard body-size measure for polymorphic leaf-cutter workers. |
| `interception_hour` | integer | whole hour of the day, 7–19 | forager | Clock hour at which the forager was intercepted on the trail, on the 24-hour clock. Arena foraging was scored from 07:00 to 19:00. |
| `fragment_mass_mg` | number | milligrams, 1 decimal | forager | **Outcome.** Fresh mass of the leaf fragment the forager was carrying when intercepted. |

Every value is present; there are no missing cells, no duplicated (`colony_id`, `forager_id`) pairs,
and every `fragment_mass_mg` is positive.

## Structure in the numbers

The generator builds three sources of variation into `fragment_mass_mg`, so the nesting is visible
in the data rather than only asserted in the text:

1. **Group difference.** Control colonies are centred on 22.5 mg, exposed colonies on 18.4 mg.
2. **Between-colony variation.** Each colony gets its own offset, drawn with a standard deviation of
   2.2 mg. Colonies genuinely differ: realised colony mean loads run from 13.90 mg (C02) to
   25.25 mg (C11).
3. **Within-colony variation.** Foragers vary around their own colony's level with a standard
   deviation of about 4.0 mg. Part of that spread is a mild body-size effect (2.0 mg of fragment
   mass per mm of head width); the rest is unstructured forager-to-forager noise. The two together
   sum to the stated 4.0 mg, they are not stacked on top of it.

`interception_hour` is drawn independently of everything else and has no effect on fragment mass.

Realised values in the delivered CSV, after rounding to one decimal place:

| Quantity | Target | Realised |
| --- | --- | --- |
| Mean fragment mass, control foragers | 22.5 mg | 22.23 mg |
| Mean fragment mass, exposed foragers | 18.4 mg | 18.42 mg |
| Between-colony SD (within group) | 2.2 mg | 2.44 mg |
| Within-colony SD | 4.0 mg | 4.06 mg |
| Minimum fragment mass | > 0 | 7.0 mg |

The realised figures differ slightly from the targets because they are one finite sample of 16
colonies, which is exactly the sampling variability the analysis has to account for.

## Reproducing the CSV

```
/usr/local/bin/python3 make_data.py
```

The script uses a fixed seed and writes `forager_loads.csv` next to itself, so re-running it
reproduces the delivered file byte for byte. No packages need to be installed; it uses `numpy` and
the standard library only.

SHA-256 of `forager_loads.csv`:
`3a003498f77fa0b8aaccf1eca29bbbd40453b629ef05da25841205c94e4f594d`
