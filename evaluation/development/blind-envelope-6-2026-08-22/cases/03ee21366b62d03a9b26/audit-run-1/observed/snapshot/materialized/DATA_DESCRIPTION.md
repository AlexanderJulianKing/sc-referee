# Data description

## File

`kit_weaning_weights.csv` — one CSV holding every individually weighed kit in the doe-nutrition
trial. It is produced by `make_data.py` (Python standard library only, fixed seed `20260822`), so
re-running that script reproduces the file exactly.

## What one row represents

**One row is one weaned kit weighed individually at day 35.** The row also carries the doe that
raised the kit, the diet that doe received, and the size of that doe's litter.

## Units and counts

| Level | Count |
| --- | --- |
| Breeding does (litters) | 14 |
| Does on the standard ration | 7 |
| Does on the supplemented ration | 7 |
| Weighed kits (rows in the CSV) | 106 |
| Kits in the standard group | 50 |
| Kits in the supplemented group | 56 |
| Litter sizes observed | 6 to 9 kits |

Each doe raises exactly one litter, so "doe" and "litter" name the same unit. Litter sizes differ
between does, which is why the two groups do not have the same number of kit rows.

## The two groups

`diet_group` splits the does into the two arms of the trial:

- **standard** — the standard pelleted ration. Does `D01` through `D07`, litter sizes
  6, 6, 6, 8, 6, 9, 9, giving 50 weighed kits.
- **supplemented** — the same pelleted ration plus a linseed-oil supplement, fed from mating
  through lactation. Does `D08` through `D14`, litter sizes 9, 8, 9, 6, 6, 9, 9, giving
  56 weighed kits.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `doe_id` | text | Identifier of the breeding doe that raised the kit, `D01` to `D14`. Repeats once per kit in that doe's litter. |
| `diet_group` | text | Diet fed to the doe: `standard` or `supplemented`. Constant within a doe. |
| `litter_size` | integer | Number of kits in that doe's litter that survived to weaning and were weighed, 6 to 9. Constant within a doe, and equal to the number of rows carrying that `doe_id`. |
| `kit_number` | integer | Sequence number of the kit inside its own litter, 1 up to `litter_size`. It labels kits within a litter and carries no meaning across litters. |
| `weaning_weight_g` | number | Individual body weight of the kit in grams at weaning (day 35), recorded to 0.1 g. |

## Ranges in the file

| Group | Kits | Mean weaning weight (g) | SD (g) | Min (g) | Max (g) |
| --- | --- | --- | --- | --- | --- |
| standard | 50 | 605.7 | 84.7 | 435.7 | 832.8 |
| supplemented | 56 | 680.6 | 71.2 | 405.5 | 808.4 |

## Missing data

None. Every row has a value in every column; only kits alive at day 35 were weighed and entered.
