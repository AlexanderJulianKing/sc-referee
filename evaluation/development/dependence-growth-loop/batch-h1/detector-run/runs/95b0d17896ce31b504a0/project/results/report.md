# Circling direction at nest departure in solitary mason bees

## Design

Each of the 23 bees in `data/input.csv` occupied its own meadow patch and
contributes exactly one row. The 305 scored departures are not analysed
individually: within a bee the departures are collapsed to a single majority
call (clockwise or counterclockwise), so the analysed sample is one call per
bee.

## Analysis

Exact two-sided binomial test (`scipy.stats.binomtest`) of the number of
clockwise-majority bees against a no-bias expectation of 0.5, alpha = 0.05.

## Result

- Clockwise-majority bees: 17 of 23 (0.739)
- Counterclockwise-majority bees: 6
- Exact two-sided p-value: 0.0347

[selected-result] Exact two-sided binomial test on one majority-direction call per bee: 17/23 bees (0.739) circled clockwise more often than counterclockwise, p = 0.0347; the 50:50 no-bias null is rejected at alpha = 0.05.

The bees, not the individual departures, are the replicated units, so the
test statistic rests on 23 independent observations.
