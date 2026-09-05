# Two eight-week hangboard programmes: post-training report

## The data

`data.csv` holds the post-training test session. **One row is one climber**, giving that
climber's training group and their seven post-training outcome values. The file has 34 data
rows, one per climber, with no repeated climbers, no summary rows, and no blank cells.

| Column | Meaning | Unit / scale |
| --- | --- | --- |
| `climber_id` | Climber identifier, unique per row | none (text label) |
| `hangboard_protocol` | Training group: `max_hangs` or `repeaters` | none (text label) |
| `peak_force_n` | Peak finger flexor force on the 20 mm edge | newtons (N) |
| `critical_force_pct` | Critical force, the sustainable force, as a share of that climber's peak force | percent of peak (%) |
| `time_to_failure_s` | Time to failure hanging at 60 percent of peak force | seconds (s) |
| `rate_of_force_development_n_per_s` | Rate of force development over the first 200 ms of the pull | newtons per second (N/s) |
| `resaturation_half_time_s` | Forearm muscle oxygen resaturation half time after failure | seconds (s) |
| `moves_to_failure` | Moves completed to failure on a standard bouldering circuit | count of moves |
| `finger_soreness_0_10` | Self-reported finger soreness during the final training week | rating on a 0 to 10 scale |

## Design and declared outcomes

Thirty-four experienced sport climbers, matched at baseline for climbing grade, each completed
one of two eight-week hangboard programmes on the same 20 mm edge. Seventeen trained with
maximal hangs and long rests (`max_hangs`) and seventeen trained with short repeater hangs
(`repeaters`). All measurements were taken at the same post-training session, and every climber
completed it.

The study protocol declared the outcome family before training began, in this order:
(1) peak finger flexor force, (2) critical force, (3) time to failure, (4) rate of force
development, (5) oxygen resaturation half time, (6) moves to failure, (7) finger soreness.
**Outcomes 1 and 2 are the protocol's primary endpoints.** Outcomes 3 to 7 are secondary.

## How the comparison was done

Each declared outcome was compared between the two groups with one two-sample significance
test. The six laboratory measurements used Welch's two-sample t test, which does not assume the
two groups share a variance. The self-reported soreness rating is an ordinal 0 to 10 score, so
it used the Mann-Whitney U test instead.

The two primary endpoints were handled as a pair. Their two p-values were adjusted together
with the Holm step-down procedure, using `multipletests` from `statsmodels.stats.multitest`,
and the verdict for each primary endpoint rests on its adjusted p-value at the conventional
0.05 threshold. The five secondary outcomes are reported with their plain unadjusted p-values,
each given its own verdict at 0.05.

## Results

Group sizes were 17 in `max_hangs` and 17 in `repeaters`. Values below are mean (SD).

| # | Outcome | `max_hangs` | `repeaters` | p used | Conclusion |
| --- | --- | --- | --- | --- | --- |
| 1 | Peak force (N), *primary* | 520.00 (70.00) | 468.01 (70.00) | 0.0758 (Holm; raw 0.0379) | Not significant |
| 2 | Critical force (% of peak), *primary* | 41.51 (5.01) | 39.01 (5.01) | 0.1554 (Holm; raw 0.1554) | Not significant |
| 3 | Time to failure (s) | 48.01 (12.00) | 43.00 (12.01) | 0.2330 | Not significant |
| 4 | Rate of force development (N/s) | 2100.00 (400.19) | 1860.12 (400.03) | 0.0901 | Not significant |
| 5 | Resaturation half time (s) | 12.40 (3.00) | 14.61 (3.01) | 0.0399 | Significant |
| 6 | Moves to failure | 38.00 (8.11) | 33.12 (8.03) | 0.0873 | Not significant |
| 7 | Finger soreness (0 to 10) | 2.46 (1.28) | 3.51 (1.40) | 0.0371 | Significant |

For the two primary endpoints the p used is the Holm-adjusted value; for the five secondary
outcomes it is the unadjusted value. The maximal-hangs group was higher on peak force by
52.0 N (t = 2.17) and on critical force by 2.5 percentage points (t = 1.46), and neither
cleared 0.05 after the pair was adjusted. Among the secondary outcomes, resaturation half time
was 2.2 s shorter in the maximal-hangs group (t = -2.14) and soreness was 1.05 points lower
(Mann-Whitney U = 83.5). The other three secondary outcomes all favoured maximal hangs by a
margin that did not reach 0.05: time to failure by 5.0 s, rate of force development by 240 N/s,
and moves to failure by 4.9 moves.

## What the study found

Neither of the two pre-declared primary endpoints separated the programmes at the 0.05
threshold once the pair of primary p-values was adjusted together. On peak force the
maximal-hangs group was ahead by about 52 N, but that gap was not large enough to survive the
adjustment. Two secondary outcomes did separate the groups: climbers on maximal hangs
resaturated their forearms faster after failure and reported less finger soreness in the final
training week. The remaining secondary outcomes pointed the same way without reaching the
threshold. On this evidence the two eight-week programmes produced comparable finger strength
and endurance on the primary measures, with the maximal-hangs programme showing an advantage in
recovery and a lower soreness load.
