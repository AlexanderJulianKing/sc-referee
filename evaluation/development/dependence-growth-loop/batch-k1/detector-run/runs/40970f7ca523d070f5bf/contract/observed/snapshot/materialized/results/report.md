# Urea-supplemented leaf discs are cut preferentially in a two-choice arena

## Design

Leafcutter (*Atta cephalotes*) colonies were excavated from 26 separate
forest plots and housed individually. Each colony ran the two-choice foraging
arena exactly once: one urea-supplemented leaf tray and one untreated leaf
tray, both weighed before and after a six-hour foraging window. One row of
`data/input.csv` is one colony, and each colony contributes exactly one
outcome to the test, so the analyzed observations are not repeated
measurements of the same nest.

## Analysis

Each colony was scored as a single Bernoulli trial: "prefers urea" if that
colony removed more urea-supplemented leaf mass than untreated leaf mass.
The 26 colony-level outcomes were compared with an exact two-sided binomial
test (`scipy.stats.binomtest`) against a no-preference null share of 0.50.
No colony produced a tie, so no trial was discarded.

## Result

- Colonies assayed: 26
- Colonies cutting more urea-supplemented leaf: 20 (76.9%)
- Colonies cutting more untreated leaf: 6
- Median within-colony mass difference (urea minus plain): 50.7 mg
- Exact two-sided binomial p-value: 0.009355

[selected-result] Exact two-sided binomial test on one outcome per colony: 20 of 26 colonies (76.9%) cut more urea-supplemented leaf tissue, median within-colony difference 50.7 mg, p = 0.009355 against the 0.50 no-preference null, so the no-preference null is rejected at alpha = 0.05.

## Notes and limits

Colony mass and forager count were recorded but not modelled; the test uses
only the direction of each colony's preference, so the magnitude of a
preference is not weighted. The design speaks only to the six-hour foraging
window that was sampled.
