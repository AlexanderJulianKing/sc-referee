# Data description

Community physiotherapy service evaluation of two eight-week programmes for adults with chronic
non-specific low back pain: a supervised motor-control exercise programme and a structured walking
programme of matched contact time. Sixty-four adults took part, thirty-two in each programme, and
every one of them completed a single end-of-programme assessment day.

## Files

| File | Role | Rows | Columns |
| --- | --- | --- | --- |
| `back_pain_outcomes.csv` | The analysis input. End-of-programme outcome table, one row per participant. | 64 data rows plus a header row | 6 |
| `make_data.py` | The deterministic seeded generator that writes `back_pain_outcomes.csv`. Standard library only, fixed seed, so re-running it reproduces the CSV exactly. | n/a | n/a |

## `back_pain_outcomes.csv`

**What one row represents:** one participant, at their single end-of-programme assessment. The row
holds that person's identifier, the programme they were allocated to, and their four declared
outcome measurements taken on that assessment day. A participant appears exactly once. There are no
repeated measures and no follow-up rows, so 64 rows means 64 people. Every participant has a value
in every outcome column; the file contains no blank cells.

**Columns**, in file order:

| # | Column | Type | Unit / range | What it holds |
| --- | --- | --- | --- | --- |
| 1 | `participant_id` | text | `P001` to `P064` | The participant identifier. Unique across the file; carries no clinical meaning and no group information. |
| 2 | `group` | text | exactly two values: `motor_control`, `walking` | The eight-week programme the participant was allocated to. `motor_control` is the supervised motor-control exercise programme; `walking` is the structured walking programme of matched contact time. 32 participants carry each value. |
| 3 | `pain_nrs` | integer | 0 to 10 points on the numerical rating scale | Declared outcome 1. Average pain intensity over the past week on a 0 to 10 numerical rating scale, where 0 is no pain and 10 is the worst pain imaginable. Higher means more pain. |
| 4 | `rmdq_score` | integer | 0 to 24 points | Declared outcome 2. Roland-Morris disability questionnaire score, the count of the 24 items endorsed. Higher means more disability. |
| 5 | `daily_steps` | integer | steps per day | Declared outcome 3. Average daily step count over the final week of the programme, from a waist-worn counter. Higher means more walking. Typical values in this population run from about 2500 to 14000 steps per day. |
| 6 | `sts_reps` | integer | repetitions in 30 seconds | Declared outcome 4. Number of sit-to-stand repetitions completed in thirty seconds. Higher means better lower-limb function. Typical values run from about 6 to 20 repetitions. |

Outcome columns 3 to 6 appear in the order the service's evaluation plan declared them: pain, then
disability, then step count, then sit-to-stand repetitions.

## A note on one step count value

Participant `P046`, in the walking programme, has a `daily_steps` value of 39,784. That is far above
anything an adult with chronic low back pain reaches on foot in a day, and above the roughly 2500 to
14000 range the rest of the cohort sits in. It is the pattern a waist-worn counter produces when it
is worn during a car journey or left attached to something else that moves. The value is recorded in
the file as it came off the counter. Every other field for that participant is an ordinary
measurement.

## Reproducing the CSV

```
python make_data.py
```

`make_data.py` writes `back_pain_outcomes.csv` into its own directory. The seed is fixed at
20260826, and the generator draws only from Python's standard-library `random` module, so the output
is identical on every run.
