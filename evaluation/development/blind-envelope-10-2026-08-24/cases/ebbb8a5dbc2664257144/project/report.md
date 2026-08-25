# Thermal liner comparison: heat strain in structural firefighting turnout coats

## Data

The analysis input is `heat_strain.csv`. One row is one firefighter: the four heat-strain outcomes
recorded for that firefighter during their single standardised live-fire training evolution, together
with their identifier and the liner design they wore. The file holds 44 data rows and one header row,
with no empty cells.

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `firefighter_id` | string | none | Participant identifier, `FF-01` through `FF-44`, unique across the file. |
| `liner_group` | string | none | Liner design worn during the evolution. Exactly two values: `liner_current` and `liner_candidate`. |
| `peak_core_temp_c` | float | degrees Celsius | Highest core body temperature recorded during the evolution. |
| `peak_heart_rate_bpm` | integer | beats per minute | Highest heart rate recorded during the evolution. |
| `sweat_loss_l` | float | litres | Total sweat loss over the evolution. |
| `exhaustion_time_min` | float | minutes | Time from the start of the evolution to voluntary exhaustion. |

Forty-four professional firefighters took part. Twenty-two wore the current service-issue liner
(`liner_current`) and twenty-two wore the candidate lighter liner (`liner_candidate`). All evolutions
were run in the same purpose-built burn building on the same day.

## Method

Each of the four outcomes declared in the study protocol was compared between the two liner groups
with an independent-samples two-sided Student t-test, and judged against the conventional 0.05
threshold. The four outcomes are reported below in the order the protocol declared them. All numbers
in this report were produced by `analysis.py`.

## Group summaries

Means and standard deviations by liner group, n = 22 per group.

| Outcome | `liner_current` mean (SD) | `liner_candidate` mean (SD) |
| --- | --- | --- |
| `peak_core_temp_c` (degC) | 38.921 (0.301) | 38.640 (0.281) |
| `peak_heart_rate_bpm` (bpm) | 182.409 (8.215) | 176.591 (7.968) |
| `sweat_loss_l` (L) | 1.140 (0.239) | 1.069 (0.221) |
| `exhaustion_time_min` (min) | 19.405 (3.910) | 21.609 (4.102) |

## Results by declared outcome

### 1. Peak core body temperature (`peak_core_temp_c`)

Firefighters in the candidate liner peaked 0.281 degC lower than those in the current liner
(38.640 degC against 38.921 degC). t = 3.202, p = 0.0026. The difference is **significant** at the
0.05 threshold.

### 2. Peak heart rate (`peak_heart_rate_bpm`)

Firefighters in the candidate liner peaked 5.818 bpm lower than those in the current liner
(176.591 bpm against 182.409 bpm). t = 2.384, p = 0.0217. The difference is **significant** at the
0.05 threshold.

### 3. Total sweat loss (`sweat_loss_l`)

Firefighters in the candidate liner lost 0.072 L less than those in the current liner (1.069 L
against 1.140 L). t = 1.035, p = 0.3068. The difference is **not significant** at the 0.05 threshold.

### 4. Time to voluntary exhaustion (`exhaustion_time_min`)

Firefighters in the candidate liner lasted 2.205 minutes longer than those in the current liner
(21.609 min against 19.405 min). t = -1.825, p = 0.0752. The difference is **not significant** at the
0.05 threshold.

## Conclusion

The candidate lighter liner performed better than the current service-issue liner on the two measures
taken at peak. Peak core body temperature was lower by 0.281 degC and peak heart rate was lower by
5.818 bpm, and both differences cleared the 0.05 threshold. On the other two declared outcomes the
liners were not separated at that threshold. Sweat loss was slightly lower in the candidate group, by
0.072 L, and time to voluntary exhaustion was slightly longer, by 2.205 minutes, but neither
difference reached significance.

For the fire service, the reading is that the candidate liner lowers the peak physiological load a
firefighter carries through a standardised evolution, which is the part of heat strain most directly
tied to heat illness during a working fire. It does not show a measurable change in how much fluid a
firefighter loses, or in how long they can keep working before voluntary exhaustion. A move to the
candidate liner would be justified on the peak core temperature and peak heart rate results, with
hydration and work-cycle policy left as they stand, since neither of those two outcomes shifted.
