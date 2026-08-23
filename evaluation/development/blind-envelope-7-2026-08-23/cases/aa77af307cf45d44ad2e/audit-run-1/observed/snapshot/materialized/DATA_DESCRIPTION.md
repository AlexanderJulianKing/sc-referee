# Data description

## File

`unit_thresholds.csv` — the single data file for this project. Plain text, comma
separated, one header line followed by 175 data lines. It is committed as a
static file; `make_data.py` is the generator that produced it (fixed seed,
Python standard library only) and is kept only for provenance.

## What one row is

One row is **one well-isolated single unit** recorded from primary auditory
cortex in one anaesthetised gerbil. Every row carries that unit's response
threshold at its own characteristic frequency. A unit appears exactly once.

## Units of observation

- 14 animals, each identified by `animal_id` (`G01`–`G14`).
- 7 animals reared in the quiet colony room, 7 reared in continuous moderate
  broadband noise from weaning.
- 175 recorded units in total: 89 from quiet-reared animals, 86 from
  noise-reared animals.
- Units per animal ranges from 9 to 16.

| animal_id | rearing_condition | units |
|---|---|---|
| G01 | quiet | 10 |
| G02 | quiet | 10 |
| G03 | quiet | 16 |
| G04 | quiet | 15 |
| G05 | quiet | 15 |
| G06 | quiet | 13 |
| G07 | quiet | 10 |
| G08 | noise | 9 |
| G09 | noise | 16 |
| G10 | noise | 10 |
| G11 | noise | 13 |
| G12 | noise | 16 |
| G13 | noise | 12 |
| G14 | noise | 10 |

## The two groups

`rearing_condition` takes exactly two values:

- `quiet` — animal reared in the quiet colony room from weaning to adulthood.
- `noise` — animal reared in continuous moderate-level broadband noise from
  weaning to adulthood.

The condition is a property of the animal, so every unit from a given animal
carries the same value.

## Columns

| column | type | description |
|---|---|---|
| `animal_id` | text | Identifier of the gerbil the unit was recorded from. Values `G01`–`G14`. |
| `rearing_condition` | text | Acoustic rearing condition of that animal: `quiet` or `noise`. |
| `unit_id` | text | Identifier of the single unit within its animal, formatted `<animal_id>-uNN`, numbered in recording order from `u01`. Unique across the whole file. |
| `cf_threshold_db_spl` | number | Response threshold of the unit at its characteristic frequency, in decibels sound pressure level (dB SPL), recorded to one decimal place. |

## Ranges actually present

- `cf_threshold_db_spl`, quiet-reared units: 7.6 to 41.6 dB SPL.
- `cf_threshold_db_spl`, noise-reared units: 14.2 to 50.4 dB SPL.
- No missing values in any column.
