# UV-marked nest tubes and first-landing choice in solitary bees

## Design

Twenty wild-caught *Osmia bicornis* females were each tested once, alone, in a
private two-tube arena. Every female contributed exactly one observation: the
tube she landed on first. No female was retested, and no arena hosted more than
one female, so each row of the data file is one independent unit.

## Data summary

- Females analysed: 20
- Distinct female identifiers: 20
- Distinct arenas: 20
- Mean intertegular span: 2.34 mm
- First landings on the UV-marked tube: 15
- First landings on the plain tube: 5

## Analysis

An exact two-sided binomial test (scipy.stats.binomtest) compares the number of
UV-marked first landings with the no-preference expectation of 0.5. Because one
female supplies one Bernoulli outcome, the twenty trials entering the test are
mutually independent and no clustering correction is needed.

- Observed proportion choosing the UV-marked tube: 0.750
- Two-sided exact p-value: 0.041389

[selected-result] Exact two-sided binomial test on 20 independent females: 15 of 20 (0.750) landed first on the UV-marked tube, p = 0.041389 against a null proportion of 0.5, rejecting indifference at the 5% level.

## Interpretation

The data are consistent with a modest attraction to UV-marked tube entrances.
Because the test consumes one observation per bee, its nominal error rate is
the actual error rate; pooling several approaches per bee would have inflated
the trial count without adding independent information.
