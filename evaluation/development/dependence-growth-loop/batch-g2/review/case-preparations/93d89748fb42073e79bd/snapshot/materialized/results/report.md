# Spectral choice in nocturnal hawkmoths: a single-trial Y-tube assay

## Design

Twenty wild-caught hawkmoths were released one at a time into a Y-tube choice
arena with an amber (590 nm) lamp at the end of one arm and a cool-white lamp at
the end of the other. A moth was scored the moment it crossed a line 20 cm into
one arm, and it was then retired from the study. Every row of `data/input.csv`
is therefore one animal and one trial: the independent unit and the observation
are the same thing, and no moth contributes twice.

## Cohort

| quantity | value |
| --- | --- |
| trials (rows) | 20 |
| distinct moth identifiers | 20 |
| mean forewing length (mm) | 18.16 |
| shortest / longest forewing (mm) | 16.5 / 20.0 |

## Analysis

With one Bernoulli outcome per moth, the number of amber choices is binomial
with n = 20, and the null hypothesis of no spectral preference fixes the success
probability at 0.500. The two-sided exact binomial test
(`scipy.stats.binomtest`) is applied to the raw count; no normal approximation
and no clustering correction are needed, because there is nothing to cluster.

Amber was chosen in 16 of 20 trials (proportion 0.800).

[selected-result] Two-sided exact binomial test of no spectral preference: 16 of 20 hawkmoths chose the amber arm (proportion 0.800 against a null of 0.500), p = 0.011818, so the preference for amber is statistically significant at alpha = 0.05.

## Balance checks (descriptive only)

| stratum | amber choices | trials |
| --- | --- | --- |
| amber lamp on the left arm | 8 | 10 |
| amber lamp on the right arm | 8 | 10 |
| female | 9 | 10 |
| male | 7 | 10 |

The counterbalanced lamp positions produced the same amber count, so the result
is not an artefact of a side bias. The sex strata are reported for completeness
and are not tested.
