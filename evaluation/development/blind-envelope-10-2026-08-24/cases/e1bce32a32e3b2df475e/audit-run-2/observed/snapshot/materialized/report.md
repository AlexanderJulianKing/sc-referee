# Passive back-support exoskeleton in grocery order picking

## Data description

The analysis uses one data file, `exo_picking_trial.csv`. **One row is one order picker**,
measured once on a single standardised mixed-case picking round during one full shift. Each
picker appears exactly once. There are 100 pickers, 50 in the exoskeleton group and 50 in the
control group. Every cell is filled; there are no blanks.

| Column | Type | Meaning |
| --- | --- | --- |
| `picker_id` | text | Identifier for the order picker, `P001` to `P100`, each used once. |
| `exo_group` | text | Group the picker was in. Exactly two values: `exoskeleton` (wore the passive back-support exoskeleton for the shift) and `control` (same shift pattern, no exoskeleton). |
| `peak_lumbar_compression_n` | integer | Highest lumbar spine compression force recorded during the round, in newtons. |
| `borg_exertion_score` | integer | Borg rating of perceived exertion at the end of the round, on the 6 to 20 scale. Higher means harder perceived work. |
| `round_time_min` | number, one decimal | Time to complete the standardised round, in minutes. |
| `picking_errors` | integer count | Number of picking errors (wrong item, wrong quantity, wrong location) made during the round. |
| `shoulder_discomfort_score` | integer | Shoulder discomfort reported at the end of the shift, on a 0 to 10 scale where 0 is no discomfort. |

The last five columns are the five outcomes the protocol declared in advance, listed here in
that declared order.

## Significance threshold

The five declared outcomes form one family. They were all named in the protocol before data
collection, they are all measured on the same 100 pickers, and they are all read together to
answer the one question the study asks. The study-level significance for that family is the
conventional 0.05.

Testing five outcomes at 0.05 each would let the chance of at least one false positive across
the family run well above 0.05. The Bonferroni correction divides the family level by the
number of outcomes: 0.05 / 5 = 0.01. That is where the per-outcome level of 0.01 comes from,
and it is why the protocol fixed 0.01 in advance, before any data were collected. Each outcome
is judged against 0.01, and 0.01 is the threshold the analysis script applies.

## Method

Each outcome was compared between the exoskeleton group and the control group with a two-group
significance test for independent samples (Welch's t-test, which does not assume the two groups
have equal variances). Group means and standard deviations are reported for every outcome.

## Group summaries

Mean (standard deviation), 50 pickers per group.

| Outcome | Exoskeleton | Control | Difference (exo minus control) |
| --- | --- | --- | --- |
| Peak lumbar compression (N) | 3510.04 (584.17) | 3887.10 (597.58) | -377.06 |
| Borg exertion score (6-20) | 13.00 (1.96) | 14.04 (2.15) | -1.04 |
| Round completion time (min) | 29.32 (4.51) | 29.86 (5.12) | -0.54 |
| Picking errors (count) | 2.60 (1.76) | 3.28 (1.95) | -0.68 |
| Shoulder discomfort (0-10) | 4.46 (1.68) | 3.62 (1.86) | +0.84 |

## Results

The five declared outcomes in declared order, each judged against the protocol threshold of
0.01.

| # | Outcome | t | df | p | Verdict against 0.01 |
| --- | --- | --- | --- | --- | --- |
| 1 | Peak lumbar compression (N) | -3.190 | 97.95 | 0.0019 | Significant |
| 2 | Borg exertion score | -2.530 | 97.18 | 0.0130 | Not significant |
| 3 | Round completion time (min) | -0.559 | 96.46 | 0.5772 | Not significant |
| 4 | Picking errors | -1.831 | 97.01 | 0.0702 | Not significant |
| 5 | Shoulder discomfort | 2.368 | 97.00 | 0.0199 | Not significant |

One of the five outcomes clears the 0.01 threshold: peak lumbar compression. Pickers wearing
the exoskeleton peaked 377 N lower on average, about 10 percent below the control mean.

Two outcomes sit between 0.01 and 0.05 and therefore do not clear the threshold this study
fixed. Perceived exertion was 1.04 Borg points lower in the exoskeleton group (p = 0.0130), and
shoulder discomfort was 0.84 points higher in the exoskeleton group (p = 0.0199). Both point in
directions worth watching, but neither meets the declared bar, so neither is a finding of this
study.

Round completion time and picking errors show no meaningful separation. The exoskeleton group
finished 0.54 minutes faster (p = 0.5772) and made 0.68 fewer errors (p = 0.0702), both well
short of the threshold.

## Conclusion

The evidence for a rollout is narrow. The exoskeleton lowered peak lumbar compression, the one
outcome that clears the protocol threshold, and that is the load the device is built to
reduce. Nothing in the data suggests it slows pickers down or makes them less accurate.

Against that, the shoulder discomfort mean moved the wrong way, and the size of that shift
(0.84 points on a 0 to 10 scale) is the kind of load transfer a passive back support can
produce. It did not clear 0.01 here, so this study does not establish it, but it also does not
rule it out, and a single measurement per picker cannot say what happens over weeks of wear.

A sensible next step is a limited rollout to one picking area, paired with a longer follow-up
that tracks shoulder discomfort repeatedly rather than once, before committing the whole
distribution centre. A full rollout on one significant outcome from a single-shift study would
be getting ahead of the evidence.
