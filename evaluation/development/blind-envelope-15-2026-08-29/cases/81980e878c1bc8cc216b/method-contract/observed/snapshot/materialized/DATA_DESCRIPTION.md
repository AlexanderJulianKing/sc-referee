# Data description

`data.csv` holds the scored results of a whole-organism toxicology screen in the nematode
*Caenorhabditis elegans*.

## What one row represents

One row is one age-synchronised assay plate. Each plate was seeded and scored on its own, and the
value in each outcome column is the average across the worms scored on that plate. There are 60
rows: 30 plates exposed from the first larval stage to 100 micromolar of the candidate neuroactive
agrochemical in the growth medium, and 30 carrier-only control plates. Nothing else differed
between plates. There is exactly one row per plate, no repeated rows, no summary rows, and no
empty cells.

## Columns

Columns appear in this order. The eight outcome columns follow the order in which the outcomes
were declared in the screen protocol.

| Column | Meaning | Unit |
| --- | --- | --- |
| `plate_id` | Plate identifier, `plate_01` through `plate_60`, in scoring order | none |
| `exposure` | Exposure group: `exposed` (100 uM compound) or `control` (solvent carrier only) | none |
| `mean_lifespan_d` | Declared outcome 1. Mean lifespan of the worms on the plate | days (d) |
| `total_brood_size_eggs` | Declared outcome 2. Total brood size | eggs per worm |
| `pumping_rate_pumps_per_min` | Declared outcome 3. Pharyngeal pumping rate | pumps per minute |
| `thrashing_rate_bends_per_min` | Declared outcome 4. Thrashing rate in liquid | body bends per minute |
| `body_length_um` | Declared outcome 5. Body length at day four of adulthood | micrometres (um) |
| `age_at_first_egg_h` | Declared outcome 6. Age at the first egg laid, measured from the fourth larval stage | hours (h) |
| `defecation_interval_s` | Declared outcome 7. Defecation cycle interval | seconds (s) |
| `crawling_speed_um_per_s` | Declared outcome 8. Mean crawling speed on the plate | micrometres per second (um/s) |

## Notes on values

- Every plate has a value for every outcome, so all 60 rows are complete.
- Readouts are rounded as the laboratory records them: lifespan, age at first egg, and defecation
  interval to one decimal place; brood size, pumping rate, thrashing rate, body length, and
  crawling speed to whole units.
- Group assignment is spread across the plate numbering rather than blocked, so `exposed` and
  `control` rows are interleaved.
- `data.csv` is a fixed data file. Downstream code should read it and never write to it.
