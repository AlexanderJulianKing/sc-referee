# Sap flow in street trees planted in conventional versus structural-soil pits

## Design

We planted 20 street trees of one species, all from the same nursery batch, along
comparable roads in a single city. Ten went into conventional compacted planting
pits, the standard street specification, and ten into engineered structural-soil
pits built to hold more water. Pit design was fixed at planting and never changed,
so the tree is the unit that was assigned to a group.

Each tree carries a sap flow sensor. For six months of the growing season, April
through September, we took the mean daily sap flow over a settled mid-month week.
That gives six monthly readings per tree and 120 rows. The design is balanced:
every tree has all six months and nothing is missing.

## Data description

The single data file is `sap_flow.csv`. **One row is one tree in one month**: the
mean daily sap flow for a single street tree during one month's measurement week.

| Column | Type | What it holds |
| --- | --- | --- |
| `tree_id` | text | Identifier of the street tree, `T01`-`T20`. The independent unit; six rows share each value. |
| `pit_design` | text | Pit design for that tree, `conventional` or `structural_soil`. Constant across its six rows. |
| `measurement_month` | text | Month of the measurement week: `April` through `September`. |
| `mean_daily_sap_flow_l_per_day` | number | Outcome. Mean daily sap flow that week, litres per day, to 0.1 L/day. |

Values run from 4.0 to 28.5 L/day. Row-level means are 13.77 L/day for
conventional pits and 18.68 L/day for structural soil.

## Method

The six readings from one tree are repeated measures on that tree, not six
independent trees. Our primary inference therefore comes from a linear
mixed-effects model of `mean_daily_sap_flow_l_per_day` on `pit_design` with a
random intercept for each tree, so each tree's own baseline is estimated and set
aside before the pit designs are compared. It was fitted by REML in statsmodels,
and the treatment estimate, standard error, and p-value come from that model.

As a clearly secondary sensitivity check only, we also ran a plain independent
two-sample t-test across all 120 rows. That test assumes 120 independent
observations, which this study does not have, and it is not the study's finding.

## Result

**Sample size: 20 trees, the independent units, contributing 120 monthly
observations.**

Primary analysis, mixed-effects model with a per-tree random effect. Trees in
structural-soil pits moved **4.91 L/day more** than trees in conventional pits
(SE 2.16 L/day; 95% CI 0.68 to 9.14; z = 2.28; **p = 0.023**). Between-tree
standard deviation is 4.68 L/day and within-tree residual standard deviation is
2.85 L/day, an intraclass correlation of 0.73, so roughly three quarters of the
variation sits between trees rather than within them.

Secondary sensitivity check only, not the study's finding. The row-level
two-sample t-test gives the same 4.91 L/day difference but t(118) = 5.07,
p = 0.0000015. Its degrees of freedom count 120 readings as 120 trees, so its
p-value is far smaller than the evidence supports.

## Interpretation

Street trees in engineered structural-soil pits used about 5 litres more water
per day than trees in conventional compacted pits, roughly a third above the
conventional average of 13.8 L/day. The mixed model supports this at p = 0.023,
and the confidence interval of 0.68 to 9.14 L/day is wide: the effect is credible
in direction but loosely pinned in size, which is what 10 trees per group buys.
The gap between the two p-values is itself the lesson. Adding months does not add
trees. With an intraclass correlation of 0.73, most of what the extra rows
contribute repeats information the tree already gave, so an analysis counting
them as independent reports far more certainty than 20 planted trees justify.

*Analysis script: `analysis.py`.*
