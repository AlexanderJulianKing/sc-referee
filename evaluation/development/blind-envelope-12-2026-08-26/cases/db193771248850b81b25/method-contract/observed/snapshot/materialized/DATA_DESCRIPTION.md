# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Deterministic seeded generator (fixed seed `20260826`, standard-library `random`). Running it rewrites `carcass_rinse_data.csv` byte for byte. |
| `carcass_rinse_data.csv` | The analysis input table. 48 data rows plus one header row, 6 columns, comma separated, no missing values. |

## `carcass_rinse_data.csv`

**One row represents one sampled broiler carcass.** The carcass is the unit of the
study. Forty-eight carcasses were sampled across a single production day at one
poultry processing plant, twenty-four from the conventional air chilling line
and twenty-four from the chlorinated-water immersion chilling line, alternating
between the two lines through the day. Each carcass was rinsed once in a
standard whole-bird rinse, and all three microbiological outcomes in that row
were measured from that single rinse. The temperature in that row was measured
on the same carcass at the end of chilling. No carcass appears twice, and every
carcass has a value in every outcome column.

### Columns, in file order

| Column | Type | Unit | What it holds |
| --- | --- | --- | --- |
| `carcass_id` | text | none | Carcass identifier, `C01` through `C48`. Unique across the file; one identifier per row. |
| `group` | text | none | Chilling method for that carcass. Exactly two possible entries: `air` (conventional air chilling) and `immersion` (immersion chilling in chlorinated water). 24 rows each. |
| `campylobacter_log_cfu` | number | log10 CFU per mL of rinse | Campylobacter count in the whole-bird rinse, on the base-ten logarithm scale. Values in this file run from 0.40 to 4.04. |
| `aerobic_log_cfu` | number | log10 CFU per mL of rinse | Total aerobic count in the whole-bird rinse, on the base-ten logarithm scale. Values in this file run from 2.00 to 5.55. |
| `ecoli_log_cfu` | number | log10 CFU per mL of rinse | Generic *Escherichia coli* count in the whole-bird rinse, on the base-ten logarithm scale. Values in this file run from 0.69 to 3.20. |
| `surface_temp_c` | number | degrees Celsius | Carcass surface temperature recorded at the end of chilling. Values in this file run from 0.4 to 6.0. |

The four outcome columns appear in the order the sampling plan declared them:
Campylobacter, total aerobic count, generic *E. coli*, surface temperature.

### How the values were produced

`make_data.py` draws each carcass from a normal distribution whose mean depends
on the chilling method of that carcass. The three microbiological counts on a
single carcass share one per-carcass contamination term, so a dirtier bird reads
higher on all three plates, and each count then adds its own independent
plating noise. Surface temperature is drawn independently of the counts. Every
drawn value is clamped to a plausible reporting range for that measurement, so
a small number of values sit exactly at a reporting floor (0.40 for
Campylobacter, 2.00 for the aerobic count, 0.4 degrees Celsius for temperature).
Counts are written to two decimal places and temperature to one.

The generated values are synthetic. They are not measurements from a real plant.
