# Data description

## File

`faecal_egg_counts.csv` — one comma-separated file, header row plus 60 data rows.

## What one row is

One row is **one counting slide**: a single McMaster egg count read from one goat's faecal sample.
A row is not a goat and it is not an independent animal-level measurement.

Each goat gave one faecal sample 14 days after treatment, and the same technician counted that one
sample three separate times on three slides. So each goat appears on three rows that differ only in
`slide_replicate` and in the slide-to-slide counting variation of `post_treatment_epg`. The
`pre_treatment_epg` value is a single pre-treatment count for the goat, repeated identically on all
three of that goat's rows.

## Units and counts

- Experimental units: 20 yearling dairy goats from one herd, randomised individually to a drench.
- Rows in the file: 60 (20 goats x 3 counting slides per goat).
- Distinct goats per row: 3 rows per goat.
- 10 goats per group, so 30 rows per group.

## The two groups

`drench_group` splits the 20 goats into two treatment arms of 10 goats each:

| Value | Meaning | Goats | Rows |
|---|---|---|---|
| `benzimidazole` | received the benzimidazole drench | 10 | 30 |
| `macrocyclic_lactone` | received the macrocyclic lactone drench | 10 | 30 |

## Columns

| Column | Type | Description |
|---|---|---|
| `goat_tag` | text | Ear-tag identifier of the goat, formatted as year of birth plus animal number (for example `25-037`). 20 distinct values, each appearing on exactly 3 rows. This is the animal-level identifier that links the three slides from the same sample. |
| `drench_group` | text | Treatment arm the goat was randomised to: `benzimidazole` or `macrocyclic_lactone`. Constant across a goat's three rows. |
| `slide_replicate` | integer | Which of the three counting slides this row is: 1, 2, or 3. It labels a laboratory repeat of the same faecal sample, not a repeat sample and not a repeat animal. |
| `pre_treatment_epg` | integer | The goat's pre-treatment faecal egg count in eggs per gram, taken before drenching. One value per goat, repeated identically on that goat's three rows. Range in this file: 850 to 2200. |
| `post_treatment_epg` | integer | The egg count in eggs per gram read from this particular slide, 14 days after treatment. This is the outcome. It varies slightly between the three slides of the same goat because of counting variation. Range in this file: 50 to 700. |

## Counting scale

Counts come from the McMaster technique with a counting factor of 25 eggs per gram, so every value in
`pre_treatment_epg` and `post_treatment_epg` is a whole number and a multiple of 25.

## Group summaries (post-treatment, across all 60 slide readings)

| Group | Rows | Goats | Min | Max | Mean | SD |
|---|---|---|---|---|---|---|
| `benzimidazole` | 30 | 10 | 275 | 700 | 494.2 | 140.1 |
| `macrocyclic_lactone` | 30 | 10 | 50 | 250 | 154.2 | 57.3 |

## How the file was made

`make_data.py` (Python standard library only, fixed seed 20260822) draws a pre-treatment count and a
goat-level post-treatment level for each goat, then adds small independent slide-to-slide counting
noise to produce the three slide readings, rounding every count to the nearest multiple of 25.
Re-running it reproduces the file exactly.
