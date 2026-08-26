# Data description

## Files

### `make_data.py`

Deterministic seeded Python generator (`numpy`, fixed seed `20260826`). Running it writes
`juice_quality.csv` into the same directory. Re-running it reproduces the identical file.

### `juice_quality.csv`

The analysis input. One header row and 44 data rows, comma separated, UTF-8.

**What one row represents:** one bottle of cloudy pear juice from the trial batch, opened once
after 28 days of dark storage at 4 degrees Celsius and measured. Each bottle appears exactly once,
so the row is the unit of the study. Twenty-two rows carry the thermal pasteurisation treatment and
twenty-two carry the high-pressure processing treatment, for 44 rows in total. Every row has a
value in every column; there are no blank cells.

**Columns, in file order:**

| Column | Holds | Unit / values |
| --- | --- | --- |
| `bottle_id` | Bottle label, unique across the whole trial, assigned in one sequential filling run | Text, `B001` through `B044` |
| `group` | Which process the bottle received | Text, exactly two possible entries: `thermal_pasteurisation` or `high_pressure_processing` |
| `ascorbic_acid_mg_100ml` | Ascorbic acid (vitamin C) content of the juice after storage | Milligrams per 100 millilitres, 2 decimal places |
| `cloud_stability_pct` | Share of the initial turbidity still suspended after the fixed centrifugation step | Percent, 1 decimal place |
| `browning_index` | Absorbance of the clarified juice at 420 nanometres | Unitless optical reading, 3 decimal places |
| `plate_count_log_cfu` | Total aerobic plate count of the bottle contents | Base-ten logarithm of colony forming units per millilitre, 2 decimal places |

The four outcome columns appear in the order the trial declared them: ascorbic acid, cloud
stability, browning index, plate count.

**Observed ranges in the generated file:**

| Column | Thermal pasteurisation (n = 22) | High-pressure processing (n = 22) |
| --- | --- | --- |
| `ascorbic_acid_mg_100ml` | 11.85 to 20.88 | 23.20 to 29.82 |
| `cloud_stability_pct` | 57.5 to 77.6 | 81.1 to 94.7 |
| `browning_index` | 0.242 to 0.410 | 0.054 to 0.158 |
| `plate_count_log_cfu` | 0.65 to 2.55 | 0.82 to 3.03 |

All values sit inside the plausible working range the trial stated for each measurement, with
bottle-to-bottle variation inside each treatment.
