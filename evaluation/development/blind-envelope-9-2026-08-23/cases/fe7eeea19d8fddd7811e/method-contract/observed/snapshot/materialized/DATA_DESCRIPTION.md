# Data description

## The file

One data file: `home_bp_readings.csv`. It has a header row and 168 data rows.

## What one row is

**One row is one morning blood-pressure reading: one adult on one day.**

Each adult measured their own morning seated systolic blood pressure at home on seven
consecutive days, using the same validated upper-arm monitor. So each adult contributes
seven rows, one per day.

24 adults x 7 days = 168 rows.

## The units

The unit taking part in the study is the adult participant. There are **24 participants**,
coded `PT01` through `PT24`. Each one appears in seven rows of the file.

## The two groups

Every participant was assigned to one of two twelve-week programmes, and stayed in that
one programme:

| Programme value | What it means | Participants | Rows |
|---|---|---|---|
| `walking` | Structured supervised walking programme | 12 | 84 |
| `leaflet` | Printed lifestyle leaflet only | 12 | 84 |

The `walking` participants are PT01, PT03, PT05, PT06, PT08, PT09, PT13, PT17, PT19,
PT20, PT21 and PT22. The remaining twelve are `leaflet`.

## The columns

The file has four columns, in this order.

| Column | Type | What it holds |
|---|---|---|
| `participant_code` | text | Short code for the adult who took the reading, `PT01` to `PT24`. Repeats seven times, once per measurement day. |
| `programme` | text | The twelve-week programme that adult was assigned to. Two values only: `walking` or `leaflet`. Constant across all seven of an adult's rows. |
| `day` | whole number | Which of the seven consecutive measurement days this reading came from, numbered 1 to 7. |
| `systolic_bp_mmhg` | whole number | The morning seated systolic blood pressure for that adult on that day, in millimetres of mercury (mmHg). Recorded to the nearest whole mmHg, as the monitor reports it. |

There are no missing values. Every one of the 24 participants has a complete set of
seven days, and every cell is filled.

## What the numbers look like

| | walking | leaflet |
|---|---|---|
| Readings (rows) | 84 | 84 |
| Mean systolic (mmHg) | 133.9 | 138.4 |
| SD across those rows (mmHg) | 10.1 | 9.6 |

The walking group averages about 4.5 mmHg lower than the leaflet group.

Across all 168 readings the values run from 116 to 159 mmHg, and 138 of the 168 sit
inside 124 to 150 mmHg.

Two different sources of spread show up in the file:

- **Day to day, inside one person.** The average standard deviation of one adult's seven
  readings is about 4.7 mmHg. This is the ordinary morning-to-morning wobble plus
  measurement noise.
- **Between different people.** The standard deviation of the 24 per-adult averages is
  about 9.2 mmHg. People differ from one another more than one person differs from
  themselves across a week, so the seven readings from a given adult sit close together
  around that adult's own usual level.

## How the file was made

`make_data.py` writes `home_bp_readings.csv`. It uses only the Python standard library
and a fixed random seed, so re-running it reproduces the identical file.

The generator draws one true morning level for each adult (a normal draw around that
adult's programme mean, with a between-person SD of 9.5 mmHg), then draws that adult's
seven daily readings around their own level with a within-person SD of 5.0 mmHg, and
rounds each reading to a whole mmHg. That two-stage draw is what makes an adult's seven
readings resemble each other more than they resemble other adults' readings.

Run it with:

```
python3 make_data.py
```
