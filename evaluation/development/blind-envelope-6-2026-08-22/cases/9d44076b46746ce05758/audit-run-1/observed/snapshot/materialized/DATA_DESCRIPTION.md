# Data description

River valley amenity lighting and foraging activity of lesser horseshoe bats
(*Rhinolophus hipposideros*).

## Survey in brief

Twelve maternity roosts were surveyed. Six sit in valleys where a newly lit
amenity footpath now runs past the roost exit, and six sit in valleys that
remain dark. One static ultrasonic detector was placed at each roost and left
in position for eight consecutive suitable nights. Each detector returned one
activity total per night, together with the nightly minimum temperature.

Twelve roosts x eight nights gives 96 detector-nights in total: 48 in the dark
group and 48 in the lit group.

## Files

| File | Rows (excluding header) | What it holds |
| --- | --- | --- |
| `bat_activity.csv` | 96 | One row per detector-night. This is the analysis file. |
| `roost_summary.csv` | 12 | One row per roost. A convenience summary of the same data. |
| `make_data.py` | n/a | Script that produced both CSVs (fixed seed, standard library only). |

## `bat_activity.csv`

One row is one detector-night: the activity recorded by one detector at one
roost on one night. There are 96 rows.

| Column | Type | Units / values | Meaning |
| --- | --- | --- | --- |
| `roost_code` | text | `R01`-`R12` | Anonymised code for the maternity roost where the detector stood. Twelve distinct codes, each appearing on eight rows. |
| `lighting_condition` | text | `dark` or `lit` | Lighting group of the valley. `lit` means an amenity footpath light now runs past the roost exit; `dark` means the valley has no such lighting. Six roosts (48 rows) in each group. |
| `night_index` | integer | 1-8 | Position of the night within that roost's eight consecutive survey nights. 1 is the first night of deployment, 8 the last. |
| `min_temp_c` | decimal | degrees Celsius, one decimal place | Minimum air temperature recorded over that night at that roost. Values run from 4.8 to 13.0. |
| `bat_passes` | integer | whole counts | Number of lesser horseshoe bat passes logged by the detector over that night. Values run from 91 to 453. |

Group totals in the file: dark 48 detector-nights, mean 206.2 passes per night;
lit 48 detector-nights, mean 133.3 passes per night.

## `roost_summary.csv`

One row is one roost, summarising that roost's eight detector-nights. There
are 12 rows. Nothing here is new information; every value is derived from
`bat_activity.csv`.

| Column | Type | Units / values | Meaning |
| --- | --- | --- | --- |
| `roost_code` | text | `R01`-`R12` | Roost identifier, matching `bat_activity.csv`. |
| `lighting_condition` | text | `dark` or `lit` | Lighting group of that roost's valley. |
| `nights_surveyed` | integer | nights | Number of detector-nights contributed by the roost. Eight for every roost. |
| `total_passes` | integer | whole counts | Sum of `bat_passes` across the roost's eight nights. |
| `mean_passes_per_night` | decimal | passes per night, one decimal place | Mean of `bat_passes` across the roost's eight nights. |
| `min_passes` | integer | whole counts | Lowest nightly total at that roost. |
| `max_passes` | integer | whole counts | Highest nightly total at that roost. |
| `mean_min_temp_c` | decimal | degrees Celsius, one decimal place | Mean of `min_temp_c` across the roost's eight nights. |

## Notes on the values

Roosts differ a lot in size, so busy roosts record high totals on every night
and small roosts record low totals on every night; nightly means per roost span
roughly 107 to 365 passes. Within a roost, totals move up and down with the
weather, and colder nights carry fewer passes than mild ones.
