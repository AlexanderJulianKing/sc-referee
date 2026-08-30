# Notched-noise versus broadband noise therapy for chronic tinnitus: week-twelve results

## Data

The analysis uses `tinnitus_sound_therapy.csv`, which holds 70 data rows. One row
is one participant: a single adult with chronic subjective tinnitus of at least
six months duration, carrying that participant's therapy allocation and their
five declared outcome measurements from the week-twelve assessment. Each
participant appears exactly once, and no value is missing.

| Column | Description |
| --- | --- |
| `pid` | Per-participant identifier, `p01` through `p70` |
| `noise_type` | Therapy allocation: `notched` (n = 35) or `broadband` (n = 35) |
| `thi_pts` | Tinnitus handicap inventory total, points on a 0 to 100 scale (higher is worse) |
| `loudness_pts` | Tinnitus loudness rating, points on a 0 to 10 visual analogue scale |
| `sleep_idx_pts` | Sleep quality index, points on a 0 to 21 scale (higher is worse sleep) |
| `anxiety_pts` | Anxiety subscale, points on a 0 to 21 scale (higher is worse) |
| `mml_db` | Minimum masking level, decibels sensation level (dB SL) |

The five outcome columns appear in the order the protocol declared them.

## Methods

Each of the five declared outcomes is compared between the two therapy groups
with a two-sample t test for independent samples, reporting the group means, the
t statistic and the p-value.

The per-outcome significance threshold is 0.01, and that number comes from the
protocol's multiplicity plan, fixed in advance of data collection. The declared
outcome family holds exactly five outcomes. The study accepts a conventional
family-wise error rate of 0.05 across that whole family. Dividing that
family-wise rate by the five outcomes, 0.05 / 5 = 0.01, gives the
Bonferroni-corrected per-outcome level. The protocol fixed 0.01 on that basis,
and the analysis judges every outcome in the family against it. The analysis
script applies 0.01 as a constant handed to it by the protocol and does no
correction arithmetic of its own.

## Results

Group means, test statistics and p-values for all five outcomes, in the declared
order. The conclusion column judges each p-value against the fixed per-outcome
level of 0.01.

| Outcome | Mean, notched | Mean, broadband | t | p | Conclusion at 0.01 |
| --- | --- | --- | --- | --- | --- |
| `thi_pts` | 34.114 | 43.829 | -3.248 | 0.001805 | Significant |
| `loudness_pts` | 4.097 | 5.291 | -3.352 | 0.001314 | Significant |
| `sleep_idx_pts` | 7.400 | 8.286 | -1.323 | 0.190345 | Not significant |
| `anxiety_pts` | 7.057 | 7.629 | -0.747 | 0.457543 | Not significant |
| `mml_db` | 8.889 | 9.400 | -0.634 | 0.527948 | Not significant |

Two of the five declared outcomes clear the 0.01 level: the tinnitus handicap
inventory total and the tinnitus loudness rating. The sleep quality index, the
anxiety subscale and the minimum masking level do not.

## Clinical interpretation

At the week-twelve assessment, participants on individually shaped notched-noise
therapy reported a tinnitus handicap inventory total 9.7 points lower than
participants on unmodified broadband noise, and a loudness rating 1.2 points
lower on the 0 to 10 visual analogue scale. Both differences favour notched
noise and both meet the protocol's per-outcome level of 0.01, so they are the
two findings this trial supports.

The remaining three outcomes show small differences in the same direction,
0.9 points on the sleep quality index, 0.6 points on the anxiety subscale and
0.5 dB SL on the minimum masking level, none of which reach the 0.01 level. For
an audiology audience the practical reading is that the benefit seen here sits
in what patients report about their tinnitus, its perceived handicap and its
loudness, rather than in the psychoacoustic masking measure or in the sleep and
anxiety scales. Minimum masking level in particular is essentially unchanged
between protocols, so a clinician should not expect the notched-noise advantage
to show up in that bench measurement. These results come from a single
twelve-week assessment with 35 participants per group, and the non-significant
outcomes are not evidence of no effect: this trial is not large enough to settle
differences of the size observed in sleep, anxiety and masking level.
