# Trail midsole comparison: cushioned versus standard

## Data

**File:** `trail_midsole_biomechanics.csv`

**What one row is:** one recreational trail runner. Each runner ran a single instrumented
5 km trail time trial in one assigned midsole type, so each runner contributes exactly one
row and one set of measurements. The file holds 44 runners, 22 in the cushioned group and
22 in the standard group. No cell is blank.

**Columns**, in the order they appear. The five outcome columns follow the order in which
they were declared in the study protocol.

| Column | Meaning | Unit / scale |
| --- | --- | --- |
| `runner_id` | Identifier for the runner, `R01` through `R44`, one per row. | none (label) |
| `midsole_group` | Assigned midsole: `cushioned` = high-stack, highly cushioned; `standard` = standard cushioning. | none (label) |
| `ground_contact_time_ms` | Outcome 1. Mean ground contact time over the trial: how long the foot stays on the ground per step. | milliseconds |
| `vertical_oscillation_cm` | Outcome 2. Mean vertical oscillation over the trial: how far the centre of mass moves up and down per step. | centimetres |
| `cadence_steps_per_min` | Outcome 3. Mean cadence over the trial: steps per minute. | steps per minute |
| `rpe_borg_6_20` | Outcome 4. Rating of perceived exertion given after the trial, on the Borg scale from 6 (none) to 20 (maximal). | Borg 6-20 points |
| `finish_time_s` | Outcome 5. Time taken to finish the 5 km trail time trial. | seconds |

## How the outcomes were tested

Each of the five declared outcomes was compared between the two midsole groups with the
same two-sample t-test (22 runners per group in every comparison). The five outcomes form
one declared family, so the five raw p-values were collected and passed together, as a
single family, to the multiple-comparison routine
`statsmodels.stats.multitest.multipletests`. The routine was called with the family of
five p-values and no method argument, so **the family of five outcomes was adjusted
together using the library routine's default behaviour**. Every verdict below is taken
from the adjusted p-value at the conventional 0.05 threshold. No verdict is taken from a
raw p-value.

## Results

| Outcome | Cushioned mean (n = 22) | Standard mean (n = 22) | t | Raw p | Adjusted p | Verdict (adjusted, alpha = 0.05) |
| --- | --- | --- | --- | --- | --- | --- |
| `ground_contact_time_ms` | 249.782 | 244.877 | 0.9278 | 0.3588 | 0.8324 | not significant |
| `vertical_oscillation_cm` | 9.341 | 9.245 | 0.2962 | 0.7685 | 0.8612 | not significant |
| `cadence_steps_per_min` | 171.595 | 173.364 | -1.0486 | 0.3004 | 0.8324 | not significant |
| `rpe_borg_6_20` | 13.409 | 13.773 | -0.7220 | 0.4743 | 0.8547 | not significant |
| `finish_time_s` | 1414.955 | 1434.591 | -0.4889 | 0.6274 | 0.8612 | not significant |

Outcome by outcome:

- **Ground contact time.** Cushioned 249.782 ms, standard 244.877 ms, a difference of about
  4.9 ms. Raw p = 0.3588, adjusted p = 0.8324, not significant.
- **Vertical oscillation.** Cushioned 9.341 cm, standard 9.245 cm, a difference of about
  0.1 cm. Raw p = 0.7685, adjusted p = 0.8612, not significant.
- **Cadence.** Cushioned 171.595 steps/min, standard 173.364 steps/min, a difference of
  about 1.8 steps/min. Raw p = 0.3004, adjusted p = 0.8324, not significant.
- **Rating of perceived exertion.** Cushioned 13.409 points, standard 13.773 points, a
  difference of about 0.4 points. Raw p = 0.4743, adjusted p = 0.8547, not significant.
- **5 km finish time.** Cushioned 1414.955 s, standard 1434.591 s, a difference of about
  19.6 s. Raw p = 0.6274, adjusted p = 0.8612, not significant.

## Conclusion

None of the five declared outcomes separated the two midsole types once the family of five
was adjusted together. Every raw p-value was already above 0.05 before adjustment, and all
five adjusted p-values sit above 0.83, so the result does not depend on how strict the
adjustment is. The group means differ only slightly, and the differences run in mixed
directions: runners in the cushioned shoe showed slightly longer ground contact and
slightly more vertical oscillation, while runners in the standard shoe showed slightly
higher cadence but a slightly higher rating of perceived exertion and a slightly slower
finish time.

On this evidence, these 44 runners give no support for a difference between the high-stack
cushioned midsole and the standard-cushioning midsole on any of the five declared
outcomes. That is not the same as showing the two shoes are equivalent: with 22 runners per
group, only fairly large differences would be detectable, and the study was not designed as
an equivalence test. A larger sample, or a within-runner design in which each runner tests
both shoes, would be needed to detect small effects.
