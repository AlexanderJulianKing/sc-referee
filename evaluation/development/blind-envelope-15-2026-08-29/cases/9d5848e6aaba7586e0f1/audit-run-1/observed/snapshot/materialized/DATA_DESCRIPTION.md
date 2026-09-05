# Data description

Two fixed data files. Neither is generated or rewritten by the analysis.

## data.csv

One row is one trekker, measured on the second morning at the 4300 m camp. There are 64 rows plus a
header row, one per trekker, with no repeated rows, no summary rows and no blank cells. Every
trekker has a value for every outcome.

| Column | Meaning | Unit / scale |
| --- | --- | --- |
| `trekker_id` | Trekker identifier, `trk_` followed by a zero-padded number from `trk_01` to `trk_64`. Unique across the file. | text label |
| `acetazolamide_group` | Allocated study drug. Exactly two labels: `acetazolamide` (125 mg twice daily from the day before ascent) and `placebo` (matching tablet). 32 trekkers carry each label. | text label |
| `spo2_pct` | Peripheral oxygen saturation on room air, by pulse oximeter. Declared outcome 1. Recorded as whole percentage points. | percent (%) |
| `lake_louise_ams_score` | Lake Louise acute mountain sickness score. Declared outcome 2. Recorded as whole points; the scale runs from 0 to 12, higher meaning more symptoms. | points on the 0-12 Lake Louise scale |
| `resting_heart_rate_bpm` | Resting heart rate. Declared outcome 3. Recorded as whole beats per minute. | beats per minute (bpm) |
| `periodic_breathing_events_per_hr` | Nocturnal periodic breathing, counted as apnoea and hypopnoea events per hour of sleep. Declared outcome 4. Recorded to one decimal place. | events per hour of sleep |

The four outcome columns appear in the order in which the outcome family was declared in the
programme protocol.

Observed ranges in this file: `spo2_pct` 78 to 95, `lake_louise_ams_score` 0 to 7,
`resting_heart_rate_bpm` 65 to 110, `periodic_breathing_events_per_hr` 0.7 to 52.4.

## central_adjusted_pvalues.csv

One row is one declared outcome, in the declared family order. There are 4 rows plus a header row.
This file is delivered to the site by the programme's central analysis stage, which pools and tests
the declared family; the site does not compute these values.

| Column | Meaning | Unit / scale |
| --- | --- | --- |
| `outcome` | Name of the outcome, written exactly as that outcome's column name in `data.csv`. Used to match each row to its column. | text label |
| `p_value_raw` | Unadjusted p-value returned by the central stage for that outcome. | probability, 0 to 1 |
| `p_value_adjusted` | p-value for that outcome after the central stage corrected for multiplicity across the family of four. | probability, 0 to 1 |
| `correction_method` | Name of the multiplicity correction the central stage applied to the family of four. Same value in every row. | text label |
