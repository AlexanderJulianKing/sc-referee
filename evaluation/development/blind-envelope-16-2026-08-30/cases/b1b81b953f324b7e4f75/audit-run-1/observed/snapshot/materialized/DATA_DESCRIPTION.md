# Data description: eczema_trial.csv

Randomised clinical study of two emollient regimens in children aged 2 to 11 years with mild to
moderate atopic dermatitis. Children were assessed at baseline and again after eight weeks; the file
holds the week-eight values.

**One row represents one child.** There are 66 rows plus a header row: 33 children on the lipid-rich
ointment and 33 children on the light lotion. Every cell is filled, so there are no missing values.

## Columns

| Column | Type | Unit / scale | Meaning |
| --- | --- | --- | --- |
| `child_id` | text | none | Per-child identifier, `C01` through `C66`. One row per identifier, no repeats. |
| `emollient` | text | none | Treatment group. Exactly two values: `ointment` (twice-daily lipid-rich ointment, 33 children) and `lotion` (twice-daily light lotion, 33 children). |
| `severity_pts` | number | points, 0 to 72 scale | Eczema severity index score at week eight. Recorded to one decimal place. |
| `itch_pts` | integer | points, 0 to 10 numerical rating scale | Worst itch in the past 24 hours at week eight. |
| `tewl_gm2h` | number | grams per square metre per hour | Transepidermal water loss measured on the forearm at week eight. Recorded to one decimal place. |
| `sleep_nights` | integer | nights, 0 to 7 | Number of nights with disturbed sleep in the week before the week-eight visit. |
| `steroid_g` | number | grams | Total topical corticosteroid used over the eight weeks. Recorded to one decimal place. |

The five outcome columns appear in the order the protocol declared them: severity, itch, water loss,
sleep, steroid use.

## Data quality note

One transepidermal water loss reading is implausibly high: child `C20` has `tewl_gm2h` of 62.4, far
outside the range of every other child in the file. Readings like this arise when the probe is used
in a draught before it has equilibrated. The child's other five values are ordinary, and the row is
complete, so nothing is missing.
