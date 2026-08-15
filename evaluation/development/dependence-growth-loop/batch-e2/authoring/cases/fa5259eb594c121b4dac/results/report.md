# Trail-pheromone arm choice in Lasius niger foragers

## Analysis

Each row of `data/input.csv` is one Y-bridge choice trial. A trial counted
as a success when the focal forager committed to the pheromone-marked arm.
All 20 trials were pooled and submitted to an exact binomial test
(`scipy.stats.binomtest`, two-sided) against the no-preference null p = 0.500.

## Result

- Trials scored: 20
- Choices of the marked arm: 15
- Observed proportion: 0.750
- Mean commitment latency: 60.0 s

[selected-result] Exact binomial test: 15 of 20 trials took the marked arm (proportion 0.750) against a null proportion of 0.500; two-sided p = 0.0414, so the no-preference null is rejected at alpha = 0.05.

## Interpretation

Foragers took the pheromone-marked arm more often than expected under
chance, consistent with trail-pheromone guidance at the bifurcation.
