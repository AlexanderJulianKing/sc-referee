# Speech in babble with two cochlear implant sound-processing strategies

## Design

Eighteen adult cochlear implant recipients, all with at least one year of device
experience, were tested in a single session. Nine were tested with the established
sound-processing strategy and nine with the newer noise-reduction strategy. Each
recipient completed five different standard sentence lists presented in background
babble, and we scored the percentage of words repeated correctly on each list. That
gives 90 scored lists, five per recipient, with no missing lists.

Strategy was assigned at the level of the recipient, so the recipient is the unit that
distinguishes the two groups. The five lists a recipient completed are repeated measures
on that one person.

## Data description

Two files sit at the project root.

**`sentence_list_scores.csv` (raw scoring sheet), 90 rows.** One row represents one
sentence list scored for one recipient, that is, a single list-level score.

| column | what it holds |
| --- | --- |
| `recipient_id` | Recipient identifier, `CI01` through `CI18`. Appears five times, once per list. |
| `processing_strategy` | Strategy the recipient was tested with: `established` or `noise_reduction`. Same on all five of a recipient's rows. |
| `sentence_list` | Which standard list the row is: `list_1` through `list_5`. |
| `percent_words_correct` | Percentage of words repeated correctly on that list, 0 to 100, one decimal place. |

**`recipient_mean_scores.csv` (per-recipient summary sheet), 18 rows.** One row
represents one recipient, summarising that recipient's five lists.

| column | what it holds |
| --- | --- |
| `recipient_id` | Recipient identifier, `CI01` through `CI18`. Appears exactly once. |
| `processing_strategy` | Strategy for that recipient: `established` or `noise_reduction`. |
| `mean_percent_words_correct` | That recipient's mean percentage of words correct across their five lists, two decimal places. |
| `lists_scored` | How many lists that mean is based on. It is 5 for every recipient here. |

## Method

The group comparison was run on the per-recipient summary sheet,
`recipient_mean_scores.csv`, one row per recipient. We compared the two strategies with
a standard independent two-sample t-test (equal variances assumed) on
`mean_percent_words_correct`. The sample size for the test is the number of recipients
in each group: nine on the established strategy and nine on the noise-reduction
strategy.

The raw scoring sheet was read only for descriptive counts and a consistency check; no
inferential test was run on the list-level rows. Those counts confirmed 90 scored lists,
18 recipients, five distinct sentence lists, exactly five lists per recipient, no missing
scores, and list-level scores spanning 13.2 to 96.2 percent words correct. Each
recipient's summary mean matched the mean of their five raw scores exactly, and
`lists_scored` matched the raw row count for every recipient.

## Result

Recipients on the established strategy scored a mean of 54.41 percent words correct
(SD 11.71, n = 9). Recipients on the noise-reduction strategy scored a mean of 63.00
percent (SD 15.07, n = 9). The difference favours the newer strategy by 8.59 percentage
points, with a 95 percent confidence interval running from -4.89 to 22.08 percentage
points.

The independent two-sample t-test gave t(16) = 1.351, p = 0.196. Cohen's d was 0.64
(pooled SD 13.49).

## Interpretation

Recipients tested with the noise-reduction strategy scored about 8.6 percentage points
higher in babble than those on the established strategy, which is the direction we
hoped for and a difference of a size that would matter in the clinic. The test does not
establish it. At p = 0.196 the result is not statistically significant at the
conventional 5 percent level, and the confidence interval is wide enough to include both
a sizeable advantage for the newer strategy and a modest advantage for the established
one. Two things drive that width: only nine recipients per group, and large differences
between recipients, with per-recipient means running from 31.32 to 82.36 percent.
Sentence-in-babble ability varies a great deal from one implant recipient to another, so
a between-subjects design of this size has limited power. These data are consistent with
a real benefit from the noise-reduction strategy but do not demonstrate one. A larger
group, or a within-subject design in which each recipient is tested on both strategies,
would settle the question better.
