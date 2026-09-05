# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Deterministic seeded Python generator (seed `20260826`, standard library only). Running it writes `voice_outcomes.csv`. Re-running it reproduces the same file byte for byte. |
| `voice_outcomes.csv` | The analysis input table: end-of-week voice measurements for the 46 telephone operators. |

## `voice_outcomes.csv`

One row is one telephone operator: that operator's identifier, the working
condition the operator was assigned to for the full working week, and that
operator's five end-of-week voice measurements. Each operator appears exactly
once. The file has a header row and 46 data rows, 23 operators in each working
condition. Every cell is filled; there are no blanks and no missing-value
codes.

Columns, in file order:

| Column | Type | Unit / values | What it holds |
| --- | --- | --- | --- |
| `operator_id` | text | `OP-01` … `OP-46` | Identifier of the operator. Unique within the file; the numbering follows enrolment order. |
| `group` | text | exactly two values: `open_plan`, `treated_booth` | The working condition the operator spent the week in. `open_plan` is the ordinary open-plan workstation; `treated_booth` is the acoustically treated booth with sound-absorbing panels. |
| `mpt_s` | number | seconds, one decimal | Outcome 1, maximum phonation time: how long the operator could sustain a vowel on one breath. Values in the file run from 13.3 to 23.4 s. Longer is healthier. |
| `jitter_pct` | number | percent, two decimals | Outcome 2, jitter: cycle-to-cycle variation in vocal fold frequency. Values in the file run from 0.30 to 1.28 percent. Lower is healthier. |
| `sff_hz` | number | hertz, one decimal | Outcome 3, speaking fundamental frequency, the average pitch of the operator's speaking voice. Values in the file run from 107.5 to 224.7 Hz. The pooled range is broad because the workforce includes women (typically about 170–225 Hz) and men (typically about 100–145 Hz). |
| `vfi_total` | integer | points on a 0–76 scale | Outcome 4, Vocal Fatigue Index total score. Values in the file run from 6 to 39. Higher means more vocal fatigue. |
| `dryness_vas` | integer | points on a 0–100 visual analogue scale | Outcome 5, self-rated throat dryness at the end of the shift. Values in the file run from 11 to 64. Higher means a drier throat. |

The five outcome columns appear in the order the study protocol declares them:
maximum phonation time, jitter, speaking fundamental frequency, Vocal Fatigue
Index total, throat dryness.

## Notes on how the values were made

`make_data.py` draws each operator's values from fixed distributions with a
single fixed seed, so the table is reproducible. Two structural features of the
workforce are built into the draws:

- Each operator gets one shared latent "vocal robustness" value, so an
  operator who does well on one outcome tends to do well on the others. The
  outcome columns are therefore correlated within an operator, as they are in
  real voice data.
- Operator sex is used only to place `sff_hz` in the right range (about
  15 women and 8 men per condition, matching the workforce). Sex is not
  recorded as a column in the CSV.

Values are clipped to the plausible instrument ranges given in the study
description, and a few operators sit near those extremes. Half-way-through
measurements were taken by the nurse but are not part of this table; the CSV
holds the end-of-week measurements only.
