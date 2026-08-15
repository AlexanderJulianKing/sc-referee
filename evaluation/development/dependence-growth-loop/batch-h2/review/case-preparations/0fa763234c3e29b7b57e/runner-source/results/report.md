# Dissolved organic carbon export after peatland rewetting

## Data

A boreal restoration survey of hydrologically isolated peat basins. Each
basin contributes exactly one row of the table: a single end-of-season
composite sample drawn at that basin's own outlet and measured once. Half
of the basins were rewetted by ditch blocking, the rest were left drained.

| group | basins | mean DOC (mg/L) |
| --- | --- | --- |
| rewetted | 5 | 23.34 |
| drained | 5 | 16.94 |

## Analysis

Exact two-sided permutation test on the difference between group mean DOC.
All 252 ways of splitting the 10 basins into a rewetted set of 5 and a
drained set of 5 were enumerated, and the observed contrast was compared
with the resulting distribution of absolute mean differences. The basin is
both the randomisation unit and the unit of analysis: no basin is entered
more than once, so the permutation reference set is the correct one.

## Result

Observed contrast (rewetted minus drained): +6.40 mg/L.
Splits at least as extreme as the observed one: 16 of 252.

[selected-result] Exact two-sided permutation test over 252 basin-to-treatment splits: mean DOC is +6.40 mg/L higher in rewetted basins (23.34 vs 16.94 mg/L), p = 0.0635 (16/252 splits at least as extreme), which does not reach the 0.05 level.

## Reading

The point estimate is a substantial rise in DOC export after rewetting, but
with five basins per arm the exact test cannot separate it from assignment
noise: about one split in sixteen reproduces a contrast this large. The
finding is best read as suggestive and underpowered rather than as evidence
of no effect.
