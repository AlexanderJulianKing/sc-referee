# Data description

**File:** `trail_midsole_biomechanics.csv`

**What one row is:** one recreational trail runner. Each runner ran a single instrumented
5 km trail time trial in one assigned midsole type, so each runner contributes exactly one
row and one set of measurements. There are 44 rows plus a header row: 22 runners in the
cushioned group and 22 in the standard group. No cell is blank.

## Columns

Columns appear in this order. The five outcome columns follow the order they were declared
in the study protocol.

| Column | Meaning | Unit / scale | Type |
| --- | --- | --- | --- |
| `runner_id` | Identifier for the runner. Values run `R01` through `R44`, one per row, all distinct. | none (label) | text |
| `midsole_group` | Which midsole the runner was assigned. Exactly two distinct values: `cushioned` = high-stack, highly cushioned midsole; `standard` = standard-cushioning midsole. | none (label) | text |
| `ground_contact_time_ms` | Outcome 1. Mean ground contact time over the trial: how long the foot stays on the ground per step, averaged across steps. | milliseconds | number, 1 decimal |
| `vertical_oscillation_cm` | Outcome 2. Mean vertical oscillation over the trial: how far the body's centre of mass moves up and down per step, averaged across steps. | centimetres | number, 1 decimal |
| `cadence_steps_per_min` | Outcome 3. Mean cadence over the trial: steps taken per minute, averaged across the trial. | steps per minute | number, 1 decimal |
| `rpe_borg_6_20` | Outcome 4. Rating of perceived exertion the runner gave after the trial, on the Borg scale, which runs from 6 (no exertion at all) to 20 (maximal exertion). | Borg 6-20 points | whole number |
| `finish_time_s` | Outcome 5. Time the runner took to finish the 5 km trail time trial. | seconds | whole number |

## Observed ranges in this file

These are ranges across all 44 runners together, given so a reader can sanity-check the
values. They are not group comparisons.

| Column | Minimum | Maximum |
| --- | --- | --- |
| `ground_contact_time_ms` | 205.3 | 275.2 |
| `vertical_oscillation_cm` | 7.0 | 11.1 |
| `cadence_steps_per_min` | 162.4 | 182.7 |
| `rpe_borg_6_20` | 10 | 17 |
| `finish_time_s` | 1186 | 1743 |

## Provenance

The values are invented, not collected from real runners. They were produced by
`generate_data.py` in this directory with a fixed random seed, using a simple model in
which each runner has one latent "running quality" level that nudges all five of their
outcomes in physiologically consistent directions (a stronger runner tends to show a
shorter ground contact time, less vertical oscillation, a higher cadence, a lower rating
of perceived exertion, and a faster finish time), plus independent measurement noise on
each outcome. Draws that landed outside a plausible range for recreational trail runners
were redrawn rather than trimmed, so no value sits on an artificial boundary.
