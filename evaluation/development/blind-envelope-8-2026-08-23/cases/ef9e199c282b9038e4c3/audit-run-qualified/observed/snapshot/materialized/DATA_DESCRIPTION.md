# Data description

## File

`zebra_finch_song_bouts.csv` is the single data file for this project. It sits at the project root
and has a header row plus 168 data rows.

The file was produced by `make_data.py` (Python standard library only, fixed seed `20260823`).
The values are synthetic but were drawn to match the study design and the plausible ranges given
for adult zebra finch song.

## What one row represents

One row is **one recorded song bout from one bird**: a single performance, with the measurements
taken from that performance. A row is not a bird. Each bird contributes 12 rows, so the rows within
a bird are repeated measures of the same individual and are not independent of one another.

## Units and counts

- 14 birds (adult males, housed individually), identified `BRD01` through `BRD14`.
- 12 song bouts recorded per bird, after six weeks of housing.
- 14 x 12 = **168 data rows**, one per bout. The design is balanced: every bird has exactly 12 rows,
  and every bird appears in exactly one condition.
- There are no missing cells.

## The two groups

`noise_condition` splits the birds into two housing groups of 7 birds each:

| value   | meaning                                                        | birds | rows |
|---------|----------------------------------------------------------------|-------|------|
| `noise` | room with playback of chronic low-frequency, traffic-like noise | 7     | 84   |
| `quiet` | quiet room                                                     | 7     | 84   |

Condition is a property of the **bird**, not of the bout. It is constant across all 12 rows of a
bird. The group assignment therefore gives 7 independent units per group, not 84.

Birds in the noise group: BRD02, BRD04, BRD06, BRD07, BRD10, BRD12, BRD13.
Birds in the quiet group: BRD01, BRD03, BRD05, BRD08, BRD09, BRD11, BRD14.

## Columns

The file has 8 columns, in this order.

| column | type | unit | varies by | description |
|--------|------|------|-----------|-------------|
| `bird_id` | text | none | bird | Identifier of the individual bird, `BRD01`-`BRD14`. Repeats on the 12 rows belonging to that bird. This is the grouping variable for the repeated measures. |
| `noise_condition` | text | none | bird | Housing condition, either `noise` or `quiet`. Constant within a bird. |
| `bout_number` | integer | none | row | Which of the bird's 12 recorded bouts this row is, 1 through 12, in the order they were recorded. Restarts at 1 for each bird, so it is unique only in combination with `bird_id`. |
| `bout_duration_s` | number | seconds | row | Duration of the song bout. The outcome measure of the study. Values run from 0.87 to 3.90 s, within the plausible 0.8-4.2 s range. |
| `motif_count` | integer | count of motifs | row | Number of song motifs contained in the bout. Ranges from 1 to 8 and tracks bout duration closely, since a longer bout holds more motifs. |
| `peak_frequency_khz` | number | kilohertz (kHz) | row | Peak frequency of the bout. Values run from 2.79 to 5.25 kHz. Each bird has its own characteristic level with bout-to-bout variation around it. |
| `recording_time` | text | clock time, `HH:MM`, 24-hour | row | Time of day the bout was recorded. All recordings fall in the morning window 07:40 to 11:46. Within a bird the 12 times increase across the recording session, a few minutes apart. |
| `age_days` | integer | days | bird | Age of the bird in days at the time of recording, 238 to 851. Constant across the bird's 12 rows, so it is a bird-level attribute repeated on every bout. |

## Structure that matters for analysis

Three of the eight columns (`bird_id`, `noise_condition`, `age_days`) carry bird-level information
and repeat unchanged down each bird's block of 12 rows. Only `bout_number`, `bout_duration_s`,
`motif_count`, `peak_frequency_khz`, and `recording_time` change from bout to bout.

Bout duration was generated with two separate sources of spread: a stable offset for each bird
(individual finches have characteristic song lengths) and bout-to-bout variation within a bird of
about 0.35 s. The 168 rows therefore hold far fewer than 168 independent pieces of information about
the housing condition; the number of independent units for the condition comparison is 14.
