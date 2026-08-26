# Rapid versus slow urate-lowering titration: six-month outcomes

## Data

The analysis uses `gout_titration_outcomes.csv`. One row is one adult participant in the
gout titration study, assessed once at the six-month review. There are 58 rows plus a
header row, 29 participants on the rapid schedule and 29 on the slow schedule. Every
participant has a value in every outcome column, so there are no blank cells.

| Column | Meaning | Unit or scale |
| --- | --- | --- |
| `participant_id` | Study identifier for the participant, one per row, format `GT-001` to `GT-058` | identifier, no unit |
| `titration_schedule` | Titration schedule the participant was on: `rapid` (dose increases every two weeks) or `slow` (dose increases every six weeks) | two-level group label |
| `serum_urate_umol_l` | Declared outcome 1: serum urate at the six-month review | micromoles per litre (umol/L) |
| `gout_flares_past_3_months_count` | Declared outcome 2: number of gout flares in the three months before the review | count of flares (whole number) |
| `egfr_ml_min_1_73m2` | Declared outcome 3: estimated glomerular filtration rate | millilitres per minute per 1.73 square metres |
| `crp_mg_l` | Declared outcome 4: C-reactive protein | milligrams per litre (mg/L) |
| `worst_joint_pain_0_10_scale` | Declared outcome 5: worst joint pain in the past week | 0 to 10 numeric rating scale, whole number, 0 = no pain, 10 = worst imaginable |

## Methods

The two schedules were compared on each outcome with a Welch two-sample t-test, the same
test for all five outcomes. Group sizes, group means, the t statistic and the p-value are
produced by `analysis.py`.

The five outcomes declared in the protocol form one outcome family. The family-wise
significance level for that family is the conventional 0.05, meaning the study accepts at
most a 5 percent chance of at least one false positive across all five comparisons. The
Bonferroni correction spreads that family-wise level evenly over the members of the
family, so the per-outcome level is 0.05 divided by 5 outcomes, which is 0.01. That is why
the protocol fixed the per-outcome threshold at 0.01 in advance, before recruitment and
before any data were collected.

The correction arithmetic above is a protocol decision recorded here in the report.
`analysis.py` does none of it: the script takes 0.01 as a fixed given and only compares
each p-value with it.

## Results

Group sizes were 29 rapid and 29 slow for every outcome.

| Declared outcome | Mean, rapid | Mean, slow | Difference (rapid - slow) | t | p | Verdict at 0.01 |
| --- | --- | --- | --- | --- | --- | --- |
| 1. Serum urate (umol/L) | 337.634 | 368.693 | -31.059 | -2.0403 | 0.0464 | not significant |
| 2. Gout flares, past 3 months (count) | 1.103 | 1.690 | -0.586 | -2.3889 | 0.0203 | not significant |
| 3. eGFR (mL/min/1.73m2) | 78.217 | 77.672 | 0.545 | 0.1391 | 0.8898 | not significant |
| 4. C-reactive protein (mg/L) | 3.336 | 3.310 | 0.026 | 0.0545 | 0.9567 | not significant |
| 5. Worst joint pain (0-10 scale) | 3.138 | 3.828 | -0.690 | -1.3575 | 0.1803 | not significant |

None of the five p-values falls below the protocol threshold of 0.01, so no outcome is
declared significant.

Two outcomes, serum urate (p = 0.0464) and flare count (p = 0.0203), fall below 0.05. They
do not clear the 0.01 threshold that the protocol set for this family of five outcomes, so
neither counts as a positive finding here. Reporting them as significant would use a
threshold the protocol did not authorise.

## Conclusion

At the six-month review this study does not show a difference between the rapid and the
slow titration schedule on any of the five declared outcomes. The point estimates lean the
same way on the two urate-related outcomes, with the rapid schedule averaging 31.1 umol/L
lower serum urate and 0.59 fewer flares over three months, but both fall short of the
pre-specified 0.01 threshold, so the study treats them as unconfirmed rather than
established. Kidney function and C-reactive protein look essentially the same in the two
groups. A larger study would be needed to tell whether the urate and flare differences are
real.
