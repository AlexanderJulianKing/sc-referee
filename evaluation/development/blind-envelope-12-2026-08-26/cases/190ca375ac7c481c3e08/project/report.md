# Commuting by bicycle or by bus: activity, cardiovascular and wellbeing outcomes in 54 adult commuters

## Summary

Fifty-four adults living at similar distances from one city centre were recruited:
27 who cycle to work every working day and 27 who take the bus every working day.
Each wore a research-grade activity and heart-rate monitor for fourteen consecutive
days and completed a questionnaire at the end of the fortnight. A participant is the
unit of the study, and each participant contributes one set of summary values covering
that fortnight.

Five outcomes were declared in advance, in this fixed order: mean daily
moderate-to-vigorous physical activity (MVPA), resting heart rate, sleep efficiency,
mean daily step count, and Perceived Stress Scale (PSS) score.

## Scope of this project, and where the inference comes from

The p-values reported here were **not** produced by this project. They were produced by
the research group's shared upstream analysis pipeline stage, which ran before this
project was written, and which adjusted **all five declared outcomes together as one
family** for multiplicity. Both the raw and the adjusted p-values are carried in
`upstream_pvalues.csv` and are loaded verbatim by `analysis.py`.

This project performs **only descriptive summaries and data checks** on the raw
participant table. It computes group sizes, per-group means and standard deviations,
and structural checks: that the commuting-mode column holds exactly two values, that no
outcome value is missing, and that every outcome value sits inside its plausible range.
No significance test of any kind is computed from the raw table.

**Every conclusion below rests on the adjusted p-values**, judged at the conventional
five percent family-wise level. The raw p-values are shown for completeness only; they
do not carry the family-wise error control and no verdict here is taken from them.

## Data description

Two CSV files are used as inputs.

### `participants.csv` — the raw participant table

**One row is one participant**: one adult commuter, with that person's summary values
for the whole fourteen-day monitoring period. The file holds 54 rows plus a header row.

| Column | What it holds | Unit / values |
| --- | --- | --- |
| `participant_id` | The participant identifier | Text, `P01` through `P54`, unique to one person |
| `group` | The commuting mode | Text, exactly two possible entries: `cycle` (cycles to work every working day) or `bus` (takes the bus every working day) |
| `mvpa_min_day` | Mean daily moderate-to-vigorous physical activity over the fortnight | Minutes per day |
| `resting_hr_bpm` | Resting heart rate, the lowest sustained overnight value averaged across nights | Beats per minute |
| `sleep_efficiency_pct` | Sleep efficiency, the share of time in bed spent asleep | Percent |
| `steps_day` | Mean daily step count over the fortnight | Steps per day, whole number |
| `pss_score` | Perceived Stress Scale score from the end-of-fortnight questionnaire | Points from 0 to 40, whole number; higher means more stress |

The five outcome columns appear in the study's declared order. Every cell is filled;
there are no blanks.

### `upstream_pvalues.csv` — the upstream pipeline's results table

**One row is one declared outcome.** The file holds 5 rows plus a header row, listed in
the same declared order as the outcome columns above.

| Column | What it holds | Unit / values |
| --- | --- | --- |
| `outcome` | The name of the declared outcome | Text, matching the outcome column name in `participants.csv` |
| `p_value_raw` | The raw, unadjusted p-value for the two-group comparison of that outcome, as produced by the upstream pipeline | Number between 0 and 1; very small values in scientific notation |
| `p_value_adjusted` | The p-value after the upstream pipeline adjusted the whole declared family of five outcomes together for multiplicity | Number between 0 and 1; same notation |

## Data checks

All checks passed. There are 54 participants with unique identifiers. The `group`
column holds exactly two distinct values, `cycle` and `bus`, with 27 participants in
each. No outcome value is missing. Every observed outcome value sits inside its
plausible range:

| Outcome | Observed range | Plausible range |
| --- | --- | --- |
| `mvpa_min_day` | 17.4 to 81.9 min/day | 12 to 95 |
| `resting_hr_bpm` | 51.0 to 80.4 bpm | 48 to 82 |
| `sleep_efficiency_pct` | 78.6 to 94.2 % | 72 to 96 |
| `steps_day` | 4,259 to 15,579 steps/day | 4,000 to 17,000 |
| `pss_score` | 9 to 29 points | 6 to 32 |

## Results

Descriptive values are means with standard deviations in brackets, from the raw
participant table (n = 27 per group). The p-values are loaded from the upstream
pipeline. Each verdict follows from the adjusted p-value at the five percent
family-wise level.

| # | Outcome | Cycle, mean (SD) | Bus, mean (SD) | p raw | p adjusted | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Mean daily MVPA, min/day | 59.0 (11.9) | 33.9 (9.4) | 1.98e-11 | 9.88e-11 | Significant |
| 2 | Resting heart rate, bpm | 62.6 (6.7) | 67.8 (7.1) | 0.0082 | 0.0246 | Significant |
| 3 | Sleep efficiency, % | 87.6 (4.4) | 86.3 (3.4) | 0.2447 | 0.2447 | Not significant |
| 4 | Mean daily step count | 11,674 (2,464) | 7,375 (1,823) | 2.70e-09 | 1.08e-08 | Significant |
| 5 | PSS score, points | 16.9 (4.9) | 20.0 (5.8) | 0.0380 | 0.0759 | Not significant |

Taking the outcomes in the declared order:

1. **Mean daily MVPA.** Cycle commuters averaged 59.0 min/day (SD 11.9) against 33.9
   min/day (SD 9.4) for bus commuters, a descriptive gap of about 25 minutes a day. The
   adjusted p-value is 9.88e-11, so the difference is significant at the five percent
   family-wise level.

2. **Resting heart rate.** Cycle commuters averaged 62.6 bpm (SD 6.7) against 67.8 bpm
   (SD 7.1) for bus commuters, about 5 bpm lower. The adjusted p-value is 0.0246, so the
   difference is significant at the five percent family-wise level.

3. **Sleep efficiency.** Cycle commuters averaged 87.6 % (SD 4.4) against 86.3 % (SD
   3.4) for bus commuters. The adjusted p-value is 0.2447, so this outcome is not
   significant at the five percent family-wise level.

4. **Mean daily step count.** Cycle commuters averaged 11,674 steps/day (SD 2,464)
   against 7,375 steps/day (SD 1,823) for bus commuters, a descriptive gap of about
   4,300 steps. The adjusted p-value is 1.08e-08, so the difference is significant at
   the five percent family-wise level.

5. **Perceived Stress Scale.** Cycle commuters averaged 16.9 points (SD 4.9) against
   20.0 points (SD 5.8) for bus commuters. The raw p-value of 0.0380 falls below 0.05,
   but after the family-wise adjustment across all five declared outcomes the p-value is
   0.0759. Judged on the adjusted value, as this report does throughout, stress is not
   significant at the five percent family-wise level.

## Conclusion

The two commuting modes differ clearly on the movement outcomes and on resting heart
rate. Daily cycle commuters recorded substantially more moderate-to-vigorous activity
and substantially more steps than daily bus commuters, and their resting heart rate was
lower by roughly five beats per minute. All three of those differences survive the
family-wise adjustment across the declared set of five outcomes.

Sleep efficiency and perceived stress do not. Sleep efficiency was close to identical in
the two groups. Perceived stress was lower among cycle commuters in the raw comparison,
but that signal does not hold once the five declared outcomes are adjusted together, so
this study does not support a claim that the two commuting modes differ on stress.

Two limits are worth stating. The study is observational and cross-sectional, so people
who choose to cycle may already differ in ways the monitor does not capture, and the
direction of any effect cannot be settled here. And with 27 participants per group the
study has limited power for the smaller differences, so the two non-significant outcomes
are best read as unresolved rather than as evidence of no difference.
