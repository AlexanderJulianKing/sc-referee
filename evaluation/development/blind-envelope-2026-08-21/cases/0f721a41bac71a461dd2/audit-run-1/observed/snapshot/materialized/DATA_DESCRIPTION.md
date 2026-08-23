# Data description

The file `nestling_mass.csv` holds the day-12 measurements from the supplementary-feeding
experiment in the great tit (*Parus major*) nestbox population.

## What one row is

One row is one nestling, weighed and measured once on day 12 after hatching. A row carries the
chick's own two measurements (mass and tarsus length) together with the nestbox it came from, the
feeding treatment that box received, and the date its brood hatched.

## Units and counts

- 16 nestboxes (broods) entered the study.
- Each of those boxes held exactly 4 surviving nestlings on day 12.
- The file therefore has 64 data rows, plus one header row.
- Every chick appears once; there are no repeat weighings.
- The four chicks in a box share the same `nest_tag`, `food_treatment`, and `hatch_date`, because
  treatment was applied to whole broods at the box and the whole brood hatched on one date.
- Hatch dates run from 2026-04-22 to 2026-05-06.
- Ring numbers run from A1201 to A1264, in the order the rows appear.
- Rows are ordered nest by nest, following the field notebook, and the nest tags are the box
  numbers actually used in the plot, so the numbering has gaps (NB-01, NB-02, ... NB-23).

## The two groups

| Group | Meaning | Nestboxes | Nestlings (rows) |
|---|---|---|---|
| `supplemented` | A mealworm feeder was placed within 5 m of the box from hatching onward | 8 | 32 |
| `control` | No feeder; the box was left unsupplemented | 8 | 32 |

## Columns

| Column | Type | Description |
|---|---|---|
| `nest_tag` | string | Identifier of the nestbox the chick came from, written as `NB-` plus a two-digit box number (for example `NB-04`). Sixteen distinct tags; four rows share each tag. |
| `food_treatment` | string | The feeding treatment the box received: `supplemented` or `control`. Constant within a nestbox. |
| `chick_ring` | string | The ring number of the individual nestling (for example `A1201`). Unique across the whole file, so it identifies the row. |
| `hatch_date` | date (ISO, `YYYY-MM-DD`) | The date the brood hatched. Constant within a nestbox. |
| `mass_g_day12` | number (grams, 1 decimal place) | Body mass of the nestling on day 12 after hatching. This is the outcome of interest. |
| `tarsus_mm` | number (millimetres, 1 decimal place) | Tarsus length of the same nestling on day 12, recorded as a measure of skeletal size. |

## Provenance

The file was produced by `make_data.py` in this directory, using a fixed random seed
(`SEED = 20260421`) so the values reproduce exactly. Re-running `python3 make_data.py` overwrites
`nestling_mass.csv` with the identical file.
