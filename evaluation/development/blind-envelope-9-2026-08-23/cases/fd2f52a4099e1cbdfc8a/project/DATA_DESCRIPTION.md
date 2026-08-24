# Data description

## Files

One data file: `reaction_times.csv`. The study prompt calls for a single CSV, so there is no
separate summary table.

`make_data.py` is the generator that produced it (Python standard library only, fixed seed
`20260823`). Re-running it rewrites `reaction_times.csv` byte for byte.

## What one row represents

One row is **one trial of the visual reaction-time task performed by one volunteer**. It is not a
volunteer and not a group: each volunteer appears on twelve separate rows, one per trial of the
single post-training session.

## Units and counts

| Quantity | Count |
| --- | --- |
| Volunteers (units of randomisation) | 22 |
| Volunteers per group | 11 adaptive, 11 active control |
| Trials per volunteer | 12 |
| Rows in the file | 264 (22 x 12) |

Every volunteer has a complete set of twelve trials. There are no missing cells and no missing
rows.

## The two groups

The `training_regime` column takes exactly two values:

- `adaptive` - the adaptive working-memory training regime, four weeks.
- `active_control` - the active control regime of untimed puzzles, four weeks.

Group is a property of the volunteer, not of the trial: all twelve rows for a given
`volunteer_ref` carry the same `training_regime`. Volunteers were assigned to alternating regimes
down the enrolment list, so odd-numbered references (V01, V03, ... V21) are `adaptive` and
even-numbered references (V02, V04, ... V22) are `active_control`.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `volunteer_ref` | text | Participant reference, `V01` through `V22`. Identifies the volunteer the trial belongs to. Repeats twelve times, once per trial. This is the unit column: rows sharing a `volunteer_ref` are repeated measurements on the same person and are not independent of one another. |
| `training_regime` | text | Which four-week regime the volunteer was assigned to. Two levels: `adaptive`, `active_control`. Constant within a volunteer. |
| `trial_number` | integer | Position of the trial within the volunteer's single session, 1 through 12, in the order the trials were run. |
| `reaction_time_ms` | number | The outcome: reaction time on that trial, in milliseconds, recorded to 0.1 ms. |

## How the values behave

The file holds simulated measurements built to look like real data of this kind.

- Reaction times run from 276 ms to 543 ms, with 255 of the 264 values falling between 310 and
  530 ms.
- The adaptive group mean is 406 ms and the active control group mean is 429 ms, a difference of
  about 23 ms in favour of the adaptive regime.
- Volunteers differ from one another: the standard deviation of the twenty-two personal means is
  about 50 ms.
- Within one volunteer, trials scatter around that person's own average with a standard deviation
  of about 33 ms.

Because the between-volunteer spread is larger than the trial-to-trial spread, two trials from the
same volunteer resemble each other more closely than two trials from different volunteers. Any
analysis that pools the 264 rows as if they were 264 independent observations will therefore
overstate the evidence.
