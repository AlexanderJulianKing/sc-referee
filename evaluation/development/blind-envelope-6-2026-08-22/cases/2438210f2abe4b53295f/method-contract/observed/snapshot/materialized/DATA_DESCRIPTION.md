# Data description

## Files

The study produces **one** data file:

| File | Level | Rows (excluding header) |
| --- | --- | --- |
| `snail_weights.csv` | one weighed snail | 280 |

There is no separate per-enclosure summary file. The per-enclosure aggregation is a
step inside `analysis.py`, so that the aggregated table used for the two-group test is
produced by the analysis rather than stored alongside the raw measurements.

`make_data.py` generates `snail_weights.csv` with a fixed random seed (`20260822`) using
only the Python standard library. Re-running it reproduces the file exactly.

## `snail_weights.csv`

### What one row represents

One row is **one individual snail, weighed once at the end of the twelve-week feeding
period**. Each snail belongs to exactly one enclosure, and each enclosure belongs to
exactly one feed group. Every weighed snail is kept as its own row; nothing is averaged
or de-duplicated in the file.

### Units and counts

- **14 enclosures** (outdoor mesh pens), stocked at equal density.
- **7 enclosures on standard feed**, **7 enclosures on feed with added calcium carbonate**.
- **20 snails collected and weighed per enclosure.**
- 14 x 20 = **280 rows**.
- The 20 rows sharing an `enclosure_ref` are repeated measurements from the same pen.
  They are not 20 independent replicates of the feed treatment; the enclosure is the
  unit that received the feed.

### Columns

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `enclosure_ref` | text | none | Identifier of the outdoor mesh enclosure the snail came from. Values `ENC-01` through `ENC-14`. Exactly 20 rows carry each value. This is the level at which feed was assigned. |
| `calcium_level` | text | none | Feed group of the enclosure. Two values: `standard` (standard feed) and `added_calcium` (standard feed plus calcium carbonate). Constant within an enclosure. `ENC-01, 03, 05, 07, 09, 11, 13` are `standard`; `ENC-02, 04, 06, 08, 10, 12, 14` are `added_calcium`. |
| `snail_no` | integer | none | Sequence number of the snail within its enclosure, 1 to 20. It is a within-enclosure label only. It is not a farm-wide snail ID, and the same number appears once in every enclosure. |
| `live_weight_g` | number | grams (g) | Live weight of the individual snail at the end of week twelve, rounded to 2 decimal places. Observed range in this file: 3.56 to 16.36 g. |
| `shell_diameter_mm` | number | millimetres (mm) | Greatest shell diameter of the same snail, rounded to 1 decimal place, recorded in the same session as the weight. It tracks live weight (heavier snails have wider shells). Recorded only within the measurable range 26.0 to 38.0 mm; 5 of the 280 snails fell outside that range and are recorded at the nearest limit (3 at 26.0 mm, 2 at 38.0 mm). |

### Completeness

There are no missing values, no blank cells, and no duplicate `enclosure_ref` +
`snail_no` pairs. All 280 rows have all five fields populated.
