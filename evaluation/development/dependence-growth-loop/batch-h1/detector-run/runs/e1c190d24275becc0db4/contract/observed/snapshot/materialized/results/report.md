# Nest-cavity choice in Temnothorax colonies

## Design

Each field-collected colony was offered a single two-way choice between a
narrow-entrance cavity and a wide-entrance cavity. A colony was assayed once
and contributes exactly one row, so the rows entering the test are mutually
independent; no colony is counted twice.

- Rows analysed: 20
- Distinct colonies (colony_id): 20
- Maximum rows contributed by any one colony: 1

## Analysis

Exact two-sided binomial test (scipy.stats.binomtest) on the number of
colonies choosing the narrow cavity, against a no-preference null of p = 0.5.

- Colonies choosing narrow: 15 of 20
- Observed proportion choosing narrow: 0.7500
- Exact two-sided p-value: 0.041389

[selected-result] Exact two-sided binomial test: 15 of 20 colonies chose the narrow cavity (proportion 0.7500), p = 0.041389 against the no-preference null of 0.5; at alpha = 0.05 the null of no cavity preference is rejected.

## Choice by source woodlot (descriptive only)

| source woodlot | narrow | wide | colonies | proportion narrow |
| --- | --- | --- | --- | --- |
| Alder Ridge | 4 | 1 | 5 | 0.800 |
| Bracken Hollow | 4 | 1 | 5 | 0.800 |
| Quarry Copse | 4 | 1 | 5 | 0.800 |
| Sedge Knoll | 3 | 2 | 5 | 0.600 |

Woodlot tallies are descriptive; they are not tested. The single test above
uses one observation per colony, which is the independent unit of this study.
