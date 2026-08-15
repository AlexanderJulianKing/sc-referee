# Thermal arm choice in juvenile cave salamanders

## Analysis

Each release in the Y-maze is scored for the arm the animal first entered (warm
or cool). Every scored release is entered as one independent Bernoulli trial and
the pooled counts are submitted to an exact two-sided binomial test against the
no-preference null of p = 0.5 (scipy.stats.binomtest).

## Data summary

- Scored releases: 20
- Warm-arm choices: 15
- Cool-arm choices: 5
- Proportion warm: 0.750
- Mean first-choice latency: 62.0 s

## Result

[selected-result] Exact two-sided binomial test, 15 warm-arm choices in 20 scored releases, null p = 0.5: proportion warm = 0.750, p = 0.0414.

The pooled releases depart from indifference at the conventional 5% threshold,
so the assay is reported as evidence of a warm-arm preference.
