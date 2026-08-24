# Adaptive working-memory training and sustained attention: reaction-time results

## What we did

Twenty-two healthy adult volunteers completed four weeks of training. Eleven were assigned to the
adaptive working-memory regime and eleven to an active control regime of untimed puzzles. After
training, every volunteer sat one session of a simple visual reaction-time task and completed
twelve trials. Nobody dropped out and no trial was lost, so the data set holds 264 trials: 22
volunteers x 12 trials, 132 trials in each group.

## The data

One file, `reaction_times.csv`, with 264 rows and four columns.

**One row is one trial of the reaction-time task performed by one volunteer.** A row is not a
volunteer and not a group. Each volunteer occupies twelve rows, one for each trial of their single
post-training session.

| Column | Type | What it holds |
| --- | --- | --- |
| `volunteer_ref` | text | The volunteer's participant reference, `V01` through `V22`. Twelve rows share each reference, one per trial. |
| `training_regime` | text | The four-week regime the volunteer was assigned to: `adaptive` or `active_control`. It is a property of the volunteer, so it is the same on all twelve of that volunteer's rows. |
| `trial_number` | integer | Which trial this is within the volunteer's session, 1 through 12, in the order the trials were run. |
| `reaction_time_ms` | number | The outcome: reaction time on that trial in milliseconds, recorded to 0.1 ms. |

The volunteer, not the trial, is the unit we randomised. That matters for the analysis, because the
twelve trials of one person are repeated measurements on that person and are not independent of one
another.

## Descriptive summary

| Group | Volunteers | Trials | Mean reaction time | SD of trials |
| --- | --- | --- | --- | --- |
| `adaptive` | 11 | 132 | 406.21 ms | 58.35 ms |
| `active_control` | 11 | 132 | 429.43 ms | 56.64 ms |

The adaptive group averaged 23.22 ms faster. Two spreads sit behind that number and they pull in
different directions. Volunteers differ a lot from each other: the standard deviation of the 22
personal averages is 49.89 ms. Within a single volunteer, trials scatter far less, with an average
within-person standard deviation of 32.86 ms. In plain terms, most of the variation in the file is
variation between people rather than variation between one trial and the next.

## Primary analysis

We fitted a linear mixed-effects model (REML) with reaction time as the outcome, training regime as
the fixed effect, and a random intercept for the volunteer:

    reaction_time_ms ~ training_regime + (1 | volunteer_ref)

The random intercept gives each volunteer their own baseline speed. Think of it as letting the model
know that the twelve numbers under `V07` are twelve looks at one person, not twelve separate people.
Without it, the analysis would count each volunteer's personal quirk twelve times over.

Result, with `active_control` as the reference level:

| Quantity | Value |
| --- | --- |
| Estimated difference (`adaptive` minus `active_control`) | -23.22 ms |
| Standard error | 21.17 ms |
| z | -1.097 |
| p (Wald) | 0.2728 |
| 95% confidence interval | -64.72 ms to 18.28 ms |

Variance components: between volunteers 2370.87 (SD 48.69 ms), residual within volunteer 1134.85
(SD 33.69 ms). The intraclass correlation is 0.676, meaning about 68 percent of the total variance
sits between volunteers. That is a strong within-person clustering and it is exactly why the trials
cannot be treated as 264 independent observations.

**Conclusion.** The adaptive group was faster on average by about 23 ms, but with 11 volunteers per
group that estimate is not distinguishable from no effect (p = 0.27). The confidence interval runs
from 65 ms faster to 18 ms slower, so this study is consistent with a worthwhile benefit and also
consistent with none. We do not claim an effect of the adaptive regime on reaction time. The study
is small at the level that counts, which is 22 volunteers rather than 264 trials.

## Secondary sensitivity check (not the reported inferential result)

For comparison only, we also ran a Welch two-sample t-test across all 264 individual trial rows:
mean difference -23.22 ms, SE 7.08 ms, t = -3.281, df = 261.77, p = 0.001177, 95% CI -37.16 ms to
-9.28 ms.

**This test treats the trials as independent and therefore overstates the evidence.** The twelve
trials from one volunteer are repeated measurements on the same person, so the effective sample size
is nearer 22 than 264. The inflation is visible in the standard error, which falls from 21.17 ms in
the primary model to 7.08 ms here, roughly a factor of three, and turns a p of 0.27 into a p of
0.001. The point estimate is the same in both, because the design is balanced; only the uncertainty
differs. The mixed-effects model above is the reported result of this study. This t-test is a
sensitivity check and nothing more.

## Reproducing

`analysis.py` at the project root is the only analysis script. It reads `reaction_times.csv`, prints
the counts and summaries, fits the mixed-effects model, and prints the sensitivity check. Every
number in this report comes from that run.
