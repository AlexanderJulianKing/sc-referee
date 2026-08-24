# Home blood pressure after two twelve-week programmes

## What we did

Our community health service ran two twelve-week programmes for adults with mildly raised blood
pressure. Twenty-four adults took part. Twelve were assigned to a structured supervised walking
programme, and twelve were given a printed lifestyle leaflet only.

At the end of the twelve weeks, each adult measured their own morning seated systolic blood
pressure at home on seven consecutive days, using the same validated upper-arm monitor. That gives
us 168 morning readings in total.

## The data

All the measurements sit in one file, `home_bp_readings.csv`. It has a header row and 168 data
rows.

**One row is one morning blood-pressure reading: one adult, on one day.**

The file has four columns, in this order.

| Column | Type | What it holds |
|---|---|---|
| `participant_code` | text | Short code for the adult who took the reading, `PT01` to `PT24`. |
| `programme` | text | The twelve-week programme that adult was assigned to. Two values only: `walking` or `leaflet`. |
| `day` | whole number | Which of the seven consecutive measurement days the reading came from, numbered 1 to 7. |
| `systolic_bp_mmhg` | whole number | The morning seated systolic blood pressure for that reading, in millimetres of mercury (mmHg), to the nearest whole mmHg as the monitor reports it. |

Nothing is missing. Every cell is filled, and the readings run from 116 to 159 mmHg.

## How we analysed it

We compared morning systolic blood pressure between the two programmes with an independent
two-sample t-test on `systolic_bp_mmhg`. Every measured row entered the comparison as its own
observation, so the test ran on all 168 readings: 84 in the walking arm and 84 in the leaflet arm.
The analysis is in `analysis.py`.

## Results

| Group | Readings | Mean systolic (mmHg) | SD (mmHg) | Range (mmHg) |
|---|---|---|---|---|
| walking | 84 | 133.90 | 10.15 | 116 to 154 |
| leaflet | 84 | 138.44 | 9.58 | 118 to 159 |

The walking group measured 4.54 mmHg lower than the leaflet group (95% CI 1.53 to 7.54 mmHg
lower). The independent two-sample t-test gives t = -2.978 on 166 degrees of freedom,
p = 0.0033, with a pooled SD of 9.87 mmHg and Cohen's d = -0.46.

## What we conclude

Morning systolic blood pressure was lower after the supervised walking programme than after the
leaflet, by about 4.5 mmHg. The difference is statistically significant at the conventional 5%
level, and the confidence interval places the true reduction somewhere between roughly 1.5 and
7.5 mmHg. A reduction of this size is worth having in adults with mildly raised blood pressure,
and it supports offering the supervised walking programme rather than the leaflet alone.
