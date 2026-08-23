# Dietary nitrate and sprint power in trained cyclists

**Status of these data: simulated.** No cyclist was tested and no ergometer was used. The
file `sprint_power.csv` was written by `make_data.py` with a fixed random seed, to look like
the study design described below. Every number in this report is real in the sense that it
was computed by `analysis.py` from that file, and unreal in the sense that the file is
invented. Nothing here supports any claim about dietary nitrate in actual athletes.

## Study design

A sports physiology laboratory tested whether a dietary nitrate supplement improves sprint
power in trained cyclists. Eighteen riders took part: nine randomised to the supplement and
nine to a matched placebo. Each rider completed five maximal seated sprints on a laboratory
ergometer in a single session, separated by fixed rest intervals, and the peak power of
every sprint was recorded.

## Data description

### The file

One data file, `sprint_power.csv`, at the project root. It holds 90 data rows plus one
header line, and 6 columns.

### What one row represents

**One row is one sprint by one rider.** It records a single maximal seated sprint effort in
that rider's session.

A row is **not** a rider. Each of the 18 riders appears on five separate rows, one per
sprint, which is how 18 riders produce 90 rows. Those five rows are repeated efforts by the
same person at successive time points within one session, so they are not independent of
one another. The rider is the independent unit of the experiment, because the rider is what
was randomised to a group.

### Every column

| Column | Type | Units | Varies by | What it holds |
| --- | --- | --- | --- | --- |
| `rider_id` | text | none | rider | Identifier of the cyclist, `RDR01` through `RDR18`. Repeats on that rider's five rows. |
| `supplement_group` | text | none | rider | The arm the rider was randomised to. Exactly two values, `supplement` or `placebo`. Constant across a rider's five rows. |
| `sprint_number` | whole number | none (an order, 1 to 5) | row | Position of this sprint within the rider's session. 1 is the first sprint performed, 5 the last. |
| `peak_power_w` | whole number | watts (W) | row | Peak power recorded during this one sprint. This is the outcome of the study. |
| `body_mass_kg` | number, 1 decimal | kilograms (kg) | rider | The rider's body mass, measured once for the session. Constant across a rider's five rows, so it is a rider-level value stored on every sprint row. |
| `cadence_rpm` | number, 1 decimal | revolutions per minute (rpm) | row | Pedalling cadence achieved during this one sprint. |

### Shape and coverage

* 18 riders, 5 sprints each, 90 rows. The file is balanced: every rider has exactly five
  rows, and no cell is empty.
* 9 riders (45 rows) in `supplement`, 9 riders (45 rows) in `placebo`.
* Values present in the file: `peak_power_w` runs 717 to 1121 W, `body_mass_kg` runs 62.4 to
  88.0 kg, `cadence_rpm` runs 108.0 to 127.5 rpm, `sprint_number` runs 1 to 5.

The raw file is kept exactly as collected. All five rows per rider are still there; no
reduction or aggregation was written back into it.

## Methods

The rider is the independent experimental unit. Randomisation was applied to riders, not to
sprints, and a rider's five sprints are repeated efforts by one person in one session.
Treating the 90 sprint rows as 90 independent observations would count each rider five times
and make the standard error too small.

The analysis therefore proceeds in two steps.

1. **Reduction.** Each rider's five sprints were averaged into that rider's single mean peak
   power. This produced **one value per rider**, 18 values in total. The reduction was done
   inside `analysis.py`; the stored CSV was not changed.
2. **Comparison.** The two groups were compared with an independent two-sample t-test run on
   those rider-level values. **The sample size is 9 riders in the supplement group and 9 in
   the placebo group, 18 riders in total.** It is not 90.

Welch's form of the t-test is the primary result, so equal variance between the two groups
is not assumed. Student's equal-variance form was computed as a sensitivity check only. The
test is two-sided at alpha = 0.05. A 95% confidence interval for the difference in means and
Hedges' g (a standardised difference corrected for small samples) are reported alongside the
p-value.

## Results

Group summaries, computed on the 18 rider-level means:

| Group | Riders | Mean peak power (W) | SD (W) | Lowest rider (W) | Highest rider (W) |
| --- | --- | --- | --- | --- | --- |
| supplement | 9 | 935.73 | 74.07 | 824.60 | 1060.80 |
| placebo | 9 | 879.58 | 61.39 | 729.20 | 939.80 |

Independent two-sample comparison, Welch's t-test on one value per rider:

| Quantity | Value |
| --- | --- |
| Sample size | 9 riders per group (18 riders) |
| Mean difference, supplement minus placebo | +56.16 W |
| 95% confidence interval for the difference | -12.02 W to 124.33 W |
| t statistic | 1.7512 |
| Degrees of freedom | 15.467 |
| p-value (two-sided) | 0.0997 |
| Hedges' g | 0.786 |

Sensitivity check, Student's equal-variance t-test on the same 18 values: t = 1.7512,
df = 16, p = 0.0991. The two forms agree closely, which is expected because the group
variances are similar and the groups are the same size.

## Interpretation

The supplement group's riders averaged 56.2 W more peak power than the placebo group's
riders, 935.7 W against 879.6 W. That difference is **not statistically significant at
alpha = 0.05** (p = 0.0997).

The confidence interval is the more useful summary here. It runs from about 12 W below zero
to about 124 W above it. So these data are consistent with the supplement doing nothing, and
also consistent with it adding a large amount of power. The study cannot tell those apart.
The reason is sample size: 9 riders per group is small, and the riders differ a lot from one
another to begin with. In this file the spread of rider average power is roughly twice the
sprint-to-sprint spread inside a rider, so the between-rider noise dominates.

What the result does not mean:

* It does not show the supplement has no effect. A non-significant p-value with a wide
  interval means the study was underpowered, not that the effect is zero.
* The standardised difference, Hedges' g = 0.79, would count as a moderate-to-large effect
  if it were real. But g is estimated from the same 18 riders and carries the same
  imprecision as the mean difference.
* Running the test on all 90 sprint rows would have produced a much smaller p-value. That
  number would be wrong, because it would treat five efforts by one rider as five
  independent riders.

The honest reading is that this design points in the direction of a benefit but does not
establish one. A larger trial, or a within-rider crossover design where each rider serves as
their own control, would be needed to settle it.

Finally, the reminder from the top: these values are simulated. The two groups were
generated with different average peak power by construction, so the direction of the
difference here is a property of the generator, not evidence about nitrate supplementation.
