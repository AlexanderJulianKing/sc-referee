# Fruiting-body occurrence on coarse woody debris

## Data

Source: data/input.csv. One row per surveyed log (log_id), 20 logs in total,
each from its own survey site and inspected exactly once. The column
fruiting_bodies_present records whether fruiting bodies of the target polypore
were found on that log.

| stand_type | logs | with fruiting bodies | proportion |
| --- | --- | --- | --- |
| old_growth | 10 | 9 | 0.900 |
| second_growth | 10 | 2 | 0.200 |

Difference in proportions (old_growth minus second_growth): 0.700

## Analysis

Two-sided Fisher's exact test on the 2x2 table of stand type by fruiting-body
presence. Each of the 20 rows is a different log, so each row contributes one
independent observation to the table.

Contingency table: [[9, 1], [2, 8]] (rows: old_growth, second_growth;
columns: fruiting bodies present, absent).

Sample odds ratio: 36.00

[selected-result] Two-sided Fisher's exact test, stand type by fruiting-body presence over 20 independent logs: p = 0.005477, sample odds ratio 36.00, occurrence 0.900 (old_growth) vs 0.200 (second_growth).

## Interpretation

Fruiting bodies were found on 9 of 10 old-growth logs and 2 of 10
second-growth logs. The association between stand type and fruiting-body
presence is significant at the 0.05 level (p = 0.005477). Because the 20 logs
were surveyed once each at separate sites, the 20 rows are the 20 independent
units of the design and no unit is represented more than once.
