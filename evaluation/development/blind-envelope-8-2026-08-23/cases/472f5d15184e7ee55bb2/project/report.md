# Tube-weaning feeding protocols in preterm infants: comparison of milk transfer rate

## Summary

Twenty-six preterm infants approaching discharge were observed on one of two tube-weaning feeding
protocols, thirteen infants per protocol, over six consecutive oral feeding sessions each. Averaging each
infant's six sessions into one value per infant, mean milk transfer rate was 2.296 ml/min on the standard
protocol and 2.800 ml/min on the new protocol. The difference of 0.504 ml/min (95% CI 0.226 to 0.781) was
statistically significant on an independent two-sample t-test with 13 infants per group
(Welch t = 3.752, df = 23.82, p = 0.00099).

## Data description

The raw data file is `feeding_sessions.csv`. It contains a header row and 156 data rows.

**One row is one observed oral feeding session for one infant.** A row is not an infant. Each infant was
observed over six consecutive feeding sessions, so each infant contributes six rows, and 26 infants x 6
sessions = 156 rows. The six rows belonging to an infant are successive time points on the same baby.

The file has 7 columns:

| Column | Type | Units | Constant within an infant? | Meaning |
| --- | --- | --- | --- | --- |
| `infant_id` | text | none | Yes | Identifier of the infant, `INF01` to `INF26`. This column marks the independent unit; it repeats across that infant's six rows. |
| `protocol` | text | none | Yes | Feeding protocol the infant was on: `standard` or `new`. A property of the infant, not of the session. |
| `session_number` | integer | count (1-6) | No | Which of the six consecutive feeding sessions this row records. Session 1 is the earliest. |
| `transfer_rate_ml_per_min` | number | millilitres per minute | No | Rate of milk transfer during that session. This is the study outcome. Observed range in the file: 1.30 to 3.83. |
| `pma_weeks` | number | weeks | No (creeps up ~0.1/session) | Postmenstrual age of the infant at that session, one decimal place. Observed range: 34.0 to 38.8. |
| `birth_weight_g` | integer | grams | Yes | Weight at birth, a fixed baseline trait identical across that infant's six rows. Observed range: 1110 to 2285. |
| `volume_taken_ml` | number | millilitres | No | Total volume of milk taken during that session. Observed range: 16.9 to 81.3. |

Groups are balanced and non-overlapping: 13 infants (78 rows) on `standard` and 13 infants (78 rows) on
`new`. All six rows for a given infant carry the same `protocol` value, so no infant appears in both
groups. There are no missing values; every infant has all six sessions and every cell is filled.

## Methods

**Unit of analysis.** The independent experimental unit is the infant, not the feeding session. The 156
rows are six repeated observations on each of 26 independent infants, so they are not 156 independent
observations. Treating rows as independent would inflate the apparent sample size six-fold and produce a
p-value that is far too small.

**Reduction before comparison.** The six sessions belonging to each infant were therefore reduced to a
single summary value per infant before any group comparison was carried out. The summary value is the
arithmetic mean of that infant's six `transfer_rate_ml_per_min` values. In `analysis.py` this reduction is
performed by its own named step, the function `reduce_sessions_to_infants()`, which takes the raw
session-level table and hands back a table with exactly one row per infant (26 rows). Infant-level traits
(`protocol`, `birth_weight_g`) are constant within an infant and were carried through unchanged.

**Comparison.** The two-group comparison was run on exactly the table returned by that reduction step, so
every row entering the test is one independent infant. **The sample size is the number of infants:
n = 13 on the standard protocol and n = 13 on the new protocol.** It is not 78 sessions per group.

The test is an independent (unpaired) two-sample t-test on the infant mean transfer rates, Welch's
version, which does not assume equal variances in the two groups. Student's equal-variance t-test was run
as a sensitivity check. A 95% confidence interval for the difference in means was computed on the Welch
standard error, and the standardised effect size is reported as Cohen's d with the small-sample
(Hedges' g) correction.

Software: Python 3, pandas 2.0.3, scipy 1.9.1. The full analysis is in `analysis.py`; running
`python3 analysis.py` reproduces every number below.

## Results

Infant-level summary of mean transfer rate, one value per infant (n = 26 infants):

| Protocol | Infants (n) | Mean transfer rate (ml/min) | SD between infants (ml/min) | Min | Max |
| --- | --- | --- | --- | --- | --- |
| standard | 13 | 2.296 | 0.327 | 1.747 | 2.688 |
| new | 13 | 2.800 | 0.357 | 2.105 | 3.393 |

The average within-infant standard deviation across an infant's six sessions was 0.300 ml/min, which is
smaller than the 0.327 to 0.357 ml/min spread between infants within a protocol group. Infants differ from
one another more than an individual infant's sessions differ among themselves, which is the reason the
sessions cannot be treated as independent.

Two-group comparison on the 26 infant means:

| Quantity | Value |
| --- | --- |
| Difference in means (new - standard) | 0.504 ml/min |
| 95% confidence interval for the difference | 0.226 to 0.781 ml/min |
| Test statistic, Welch two-sample t-test | t = 3.752 |
| Degrees of freedom | 23.82 |
| p-value | 0.00099 |
| Sensitivity check, Student two-sample t-test | t = 3.752, df = 24, p = 0.00098 |
| Cohen's d (pooled SD 0.342) | 1.471 |
| Hedges' g | 1.425 |

Because the design is balanced (every infant has exactly six sessions), the group means happen to be
numerically the same whether computed over infants or over raw sessions. The standard errors are not the
same, and only the infant-level analysis is reported here.

## Interpretation

Infants on the new tube-weaning protocol transferred milk faster than infants on the standard protocol,
by about 0.50 ml/min on average. With 13 infants per group the difference is unlikely to be chance
variation (p = 0.00099), and the confidence interval places the true difference somewhere between roughly
0.23 and 0.78 ml/min. Relative to a standard-protocol mean of 2.30 ml/min, that is an improvement of
about 22%, with a plausible range of about 10% to 34%. The standardised effect is large (Hedges' g = 1.43),
though with only 13 infants per group that effect-size estimate is itself imprecise.

**Clinical implication.** A gain of half a millilitre per minute means an infant takes a given feed
volume noticeably faster. On a 45 ml feed, the observed group means work out to about 19.6 minutes on the
standard protocol against about 16.1 minutes on the new one, roughly three and a half minutes saved per
feed. Faster and more efficient oral feeding is the milestone that typically gates removal of the feeding
tube, so the new protocol is a reasonable candidate for wider use in the unit and warrants a larger
prospective trial powered on discharge-relevant endpoints such as days to full oral feeding and length of
stay.

**Limitations.** These are synthetic data generated for this exercise, so the findings carry no real
clinical weight. Even taken at face value, the study is small (26 infants), the outcome is a single
physiological rate rather than a discharge endpoint, and no adjustment was made for baseline differences
in birth weight or postmenstrual age. Averaging the six sessions discards the mild improvement in transfer
rate across sessions; a mixed-effects model with a random intercept per infant would use that structure
rather than collapse it, and would be the natural next step if session-level trajectories are of interest.
