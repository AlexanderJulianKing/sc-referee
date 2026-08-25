# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Seeded Python generator (seed 20260842, NumPy). Running it writes `badger_landscape_data.csv`. Re-running reproduces the same file. |
| `badger_landscape_data.csv` | The study data file. 50 data rows plus one header row, 7 columns, comma separated, UTF-8. |

## What one row represents

One row is one collared adult European badger. Fifty adult badgers were live-trapped,
measured, fitted with GPS collars and tracked for six weeks in late summer. Each row
carries that animal's identifier, its landscape group, and one summary value per outcome
for its whole tracking period. There is no repeated-measures structure in the file: an
animal appears exactly once, and every cell is filled (no missing values).

## Columns of `badger_landscape_data.csv`

Columns appear in this order; the five outcome columns are in the declared study order.

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `animal_id` | text | none | Unique animal identifier. `BDG-P01`…`BDG-P25` are pasture animals, `BDG-A01`…`BDG-A25` are arable animals. 50 distinct values. |
| `mean_nightly_distance_km` | number, 2 decimals | kilometres | Declared outcome 1. The animal's mean distance travelled per night over the tracking period. Range in the file 2.54 to 8.36. |
| `home_range_95_kernel_ha` | number, 1 decimal | hectares | Declared outcome 2. The animal's home range area from a 95 percent kernel estimate. Range in the file 18.9 to 119.1. |
| `body_condition_index` | number, 2 decimals | unitless | Declared outcome 3. The animal's body condition index at capture. Range in the file 0.79 to 1.39. |
| `mean_time_active_hours` | number, 2 decimals | hours | Declared outcome 4. The animal's mean time active per night over the tracking period. Range in the file 3.51 to 9.95. |
| `faecal_cortisol_ng_per_g` | integer | nanograms per gram | Declared outcome 5. The animal's faecal cortisol metabolite concentration. Range in the file 91 to 361. |
| `landscape_type` | text | none | The two-level grouping factor: the dominant landscape the animal lives in. Exactly two distinct values, `pasture` and `arable`, 25 animals each. |

## Row order

Rows are shuffled by the generator's seeded random permutation, so the two landscape
groups are interleaved rather than stacked in blocks. Row order carries no information.
