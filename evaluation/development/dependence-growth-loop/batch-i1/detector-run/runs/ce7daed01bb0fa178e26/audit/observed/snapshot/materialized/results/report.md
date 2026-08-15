# Stomatal conductance under a biochar soil amendment

## Data

Source file: data/input.csv (12 leaf-level records).

Steady-state stomatal conductance (mmol m-2 s-1) was logged on potted
greenhouse sunflowers, two leaves per plant, in a single growth run.

## Analysis

Each leaf record was entered as one observation and the two amendment groups
were compared with a two-sided Mann-Whitney U test evaluated against the exact
null distribution (no tied conductance values occur in the file).

## Group summaries

| amendment | leaf records | plants | mean | median |
| --- | --- | --- | --- | --- |
| biochar | 6 | 3 | 159.87 | 160.95 |
| control | 6 | 3 | 115.15 | 115.15 |

Difference in group means (biochar - control): 44.72 mmol m-2 s-1.

## Result

[selected-result] Exact two-sided Mann-Whitney U test on the 12 leaf records (6 biochar vs 6 control): U = 35.0, p = 0.004329, median conductance 160.95 vs 115.15 mmol m-2 s-1.

Conductance ranked higher under biochar than under the control amendment;
only one biochar-control leaf pair is out of rank order.
