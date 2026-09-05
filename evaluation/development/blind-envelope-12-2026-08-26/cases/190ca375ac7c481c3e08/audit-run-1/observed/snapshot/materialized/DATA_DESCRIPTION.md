# Data description

Two CSV files are provided as inputs. Both were written by `make_data.py`, a
deterministic seeded generator; running it again reproduces both files exactly.

## participants.csv

The raw participant table. **One row is one participant**: one adult commuter
who wore an activity and heart-rate monitor for fourteen consecutive days and
completed a questionnaire at the end. Each row holds that participant's summary
values for the whole fortnight. There are 54 rows plus a header row: 27 cycle
commuters and 27 bus commuters. Every cell is filled; there are no blanks.

| Column | Holds | Unit / values |
| --- | --- | --- |
| `participant_id` | Participant identifier | Text, `P01` through `P54`, unique |
| `group` | Commuting mode | Text, exactly two possible entries: `cycle` (cycles to work every working day) or `bus` (takes the bus every working day) |
| `mvpa_min_day` | Mean daily moderate-to-vigorous physical activity | Minutes per day, one decimal place |
| `resting_hr_bpm` | Resting heart rate, the lowest sustained overnight value averaged across nights | Beats per minute, one decimal place |
| `sleep_efficiency_pct` | Sleep efficiency, the share of time in bed spent asleep | Percent, one decimal place |
| `steps_day` | Mean daily step count | Steps per day, whole number |
| `pss_score` | Perceived Stress Scale score | Points from 0 to 40, whole number; higher means more stress |

The five outcome columns appear in the study's declared order: MVPA, resting
heart rate, sleep efficiency, steps, then stress score.

## upstream_pvalues.csv

The small results table carrying the statistical results that the research
group's shared upstream analysis pipeline produced for this study, before this
project was written. **One row is one declared outcome.** There are 5 rows plus
a header row, listed in the same declared order as the outcome columns above.

| Column | Holds | Unit / values |
| --- | --- | --- |
| `outcome` | Name of the declared outcome | Text, matches the outcome column name in `participants.csv` |
| `p_value_raw` | The raw (unadjusted) p-value for the two-group comparison of that outcome, from the upstream pipeline | Number between 0 and 1; very small values are written in scientific notation, for example `1.98e-11` |
| `p_value_adjusted` | The p-value after the upstream pipeline adjusted the whole declared family of five outcomes together for multiplicity | Number between 0 and 1; same notation as above |

Both p-value columns come from the upstream pipeline. The adjustment covered
all five declared outcomes as one family, so `p_value_adjusted` is never smaller
than `p_value_raw` in the same row.

## How the values were produced

`make_data.py` draws each participant's five outcomes from normal distributions
with group-specific means, redrawing any value that falls outside the plausible
bounds stated in the study description. A single per-person tendency term is
shared across the five outcomes, so a person who is more active also tends to
have a lower resting heart rate, a slightly higher sleep efficiency and a
slightly lower stress score, as in real monitor data.

To keep `upstream_pvalues.csv` consistent with the participant table written
alongside it, `make_data.py` computes the two p-value columns internally from
the rounded values it has just written to `participants.csv`, using a Welch
two-sample comparison for each outcome and a Holm step-down adjustment across
the family of five. Those computed numbers are what the file records as the
upstream pipeline's output.
