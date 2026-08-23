# Data description

## Origin of the data

These values are **simulated**, not measured. No cyclist was tested and no ergometer was
used. `make_data.py` in this same folder creates the file with Python's standard library
and a fixed random seed (2899), so re-running it reproduces `sprint_power.csv` exactly.
The values were built to look like the study described in the project prompt, and they
should be read as stand-in data for that design, never as real laboratory measurements.

## The file

| File | Rows of data | Columns |
| --- | --- | --- |
| `sprint_power.csv` | 90 (plus one header line) | 6 |

There is only one data file. No second summary file is produced at this stage, because the
study calls for the raw table to be kept exactly as collected. Every one of the five sprints
per rider is still present as its own row.

## What one row represents

**One row is one sprint by one rider.** It is a single maximal seated sprint effort on the
laboratory ergometer, recorded as part of that rider's one session.

A row is **not** a rider. Each rider appears on five separate rows, one for each of the five
sprints in their session. Those five rows are repeated efforts by the same person at
successive time points in the session, so they are not independent of one another. The
riders are the independent units of the experiment.

## How many units and rows

* **18 riders**, with identifiers `RDR01` through `RDR18`.
* **5 sprints per rider**, numbered 1 to 5 in the order they were performed.
* **90 rows** of data in total (18 riders x 5 sprints). The file is balanced: every rider
  has exactly five rows, and no cell is empty.

## The two groups

Riders were split into two groups of equal size by the randomised allocation simulated in
the generator. The group is recorded in the `supplement_group` column.

| Group label | Riders | Rows | Meaning |
| --- | --- | --- | --- |
| `supplement` | 9 | 45 | Received the dietary nitrate supplement |
| `placebo` | 9 | 45 | Received the matched placebo |

A rider belongs to one group only, and that label is repeated on all five of that rider's
rows. The group assignment landed as follows:

* `placebo`: RDR02, RDR03, RDR07, RDR08, RDR12, RDR13, RDR15, RDR16, RDR18
* `supplement`: RDR01, RDR04, RDR05, RDR06, RDR09, RDR10, RDR11, RDR14, RDR17

## Every column

| Column | Type | Units | Varies by | Description |
| --- | --- | --- | --- | --- |
| `rider_id` | text | none | rider | Identifier of the cyclist, formatted `RDR01` to `RDR18`. Repeats on the five rows belonging to that rider. |
| `supplement_group` | text | none | rider | Which arm the rider was randomised to. Exactly two values: `supplement` or `placebo`. Constant across a rider's five rows. |
| `sprint_number` | whole number | none (an order, 1 to 5) | row | Position of this sprint within the rider's session. 1 is the first sprint performed, 5 the last. Sprints were separated by fixed rest intervals. |
| `peak_power_w` | whole number | watts (W) | row | Peak power recorded during this one sprint. This is the outcome of the study. |
| `body_mass_kg` | number, 1 decimal | kilograms (kg) | rider | The rider's body mass, measured once for the session. Constant across a rider's five rows, so it is a rider-level value stored on every sprint row. |
| `cadence_rpm` | number, 1 decimal | revolutions per minute (rpm) | row | Pedalling cadence achieved during this one sprint. |

## Ranges actually present in the file

These are the values in `sprint_power.csv` as generated, given here so a reader can check the
file against this description.

| Column | Lowest | Highest |
| --- | --- | --- |
| `sprint_number` | 1 | 5 |
| `peak_power_w` | 717 | 1121 |
| `body_mass_kg` | 62.4 | 88.0 |
| `cadence_rpm` | 108.0 | 127.5 |

## Structure built into the simulated values

Stated so a reader knows what patterns are present by construction. These are properties of
the generator, not findings.

* Differences between riders are large and persistent: a rider's own level of peak power
  carries across all five of their sprints. In the generated file the spread of rider
  average power (standard deviation about 72 W) is roughly twice the sprint-to-sprint
  spread within a rider (about 38 W).
* Peak power drifts down slightly across the five sprints, standing in for fatigue building
  up over the session.
* Heavier riders tend to produce more absolute power, so `body_mass_kg` and `peak_power_w`
  are positively related.
* Cadence also drifts down slightly across the five sprints.
* The two groups were generated with different average peak power, the supplement group
  higher. The generator's seed was chosen only so that the group averages in the file land
  near the averages the study description names (placebo near 880 W, supplement near 935 W)
  and so the spread of power covers the stated range. No test statistic or p-value was
  computed while choosing it, and no analysis existed at that point.
