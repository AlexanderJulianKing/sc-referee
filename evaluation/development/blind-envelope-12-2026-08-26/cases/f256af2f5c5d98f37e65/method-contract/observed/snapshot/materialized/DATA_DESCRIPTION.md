# Data description

## Files

### `make_data.py`

Deterministic seeded Python generator (standard library only, fixed seed `20260826`). Running it
writes `runoff_bays.csv` next to itself. Re-running it reproduces the same file byte for byte.

### `runoff_bays.csv`

The monitoring table. Comma separated, one header row, 36 data rows, no missing values and no
blank cells.

**What one row represents:** one individual parking bay in the municipal car park, together with
the four outcomes measured from that bay's own collection sump after the single heavy summer storm.
The bay is the unit of the study, so each bay appears exactly once and every value on the row
belongs to that one bay and that one storm.

**Columns**, in file order:

| Column | Holds | Unit |
| --- | --- | --- |
| `bay_id` | Bay identifier, `BAY-01` through `BAY-36`, unique across the file. Numbering follows the bays' physical order across the car park, starting at the entrance. | none (text label) |
| `group` | Surface type of the bay. Exactly two possible entries: `asphalt` for the conventional dense asphalt bays and `permeable` for the permeable concrete block paving over a gravel reservoir. 18 bays carry each entry. | none (text label) |
| `tss_mg_l` | Total suspended solids in the runoff collected from the bay's sump. | milligrams per litre (mg/L) |
| `zinc_ug_l` | Total zinc in the runoff collected from the bay's sump. | micrograms per litre (µg/L) |
| `peak_volume_l` | Peak runoff volume leaving the bay during the storm. | litres (L) |
| `runoff_temp_c` | Runoff temperature at peak flow. | degrees Celsius (°C) |

The four outcome columns appear in the declared monitoring order: total suspended solids, total
zinc, peak runoff volume, runoff temperature.

## How the values were produced

The two surfaces are interleaved bay by bay across the car park, so odd-numbered bays are asphalt
and even-numbered bays are permeable. Both surfaces therefore see the same traffic and the same
weather.

Suspended solids, zinc and peak volume are drawn from lognormal distributions, which are skewed and
strictly positive, the usual shape for storm water quality and volume data. Within a bay, solids and
zinc share a common bay-level "dirtiness" term, so a bay that collects more grit also collects more
metal instead of the two readings being drawn independently. Runoff temperature is drawn from a
normal distribution.

`BAY-01` and `BAY-02`, the two bays nearest the car park entrance, take the heaviest turning
movements and the most tracked-in street grit. Their solids and zinc values are raised accordingly,
which is why they read dirtier than the rest of their own surface group.

Every value is rounded to one decimal place and held inside a plausible reportable range for this
storm: 8 to 280 mg/L for solids, 12 to 210 µg/L for zinc, 15 to 360 L for peak volume, and 13 to
29 °C for temperature.
