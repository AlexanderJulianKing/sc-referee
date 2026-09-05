# Data description

Thermal liner comparison in structural firefighting turnout coats. Forty-four professional
firefighters each completed one standardised live-fire training evolution in a purpose-built burn
building on the same day, wearing the liner design assigned to them, and were monitored throughout.
Twenty-two wore the current service-issue liner and twenty-two wore the candidate lighter liner.

## Files

### `heat_strain.csv`

Analysis input. 44 data rows plus one header row. One row per firefighter: the four heat-strain
outcomes recorded for that firefighter during their single evolution, together with their identifier
and the liner design they wore. Every firefighter has a value for every outcome; there are no empty
cells.

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `firefighter_id` | string | — | Participant identifier, `FF-01` through `FF-44`, unique across the file. |
| `liner_group` | string | — | Liner design worn during the evolution. Exactly two values: `liner_current` (current service-issue liner, 22 firefighters) and `liner_candidate` (candidate lighter liner, 22 firefighters). |
| `peak_core_temp_c` | float, 2 decimals | degrees Celsius | Highest core body temperature recorded for that firefighter during the evolution. |
| `peak_heart_rate_bpm` | integer | beats per minute | Highest heart rate recorded for that firefighter during the evolution. |
| `sweat_loss_l` | float, 2 decimals | litres | Total sweat loss over the evolution for that firefighter. |
| `exhaustion_time_min` | float, 1 decimal | minutes | Elapsed time from the start of the evolution until that firefighter reached voluntary exhaustion. |

### `make_data.py`

The seeded generator that produced `heat_strain.csv`. Running it with the fixed seed rewrites the
same CSV byte for byte. It is not part of the analysis.
