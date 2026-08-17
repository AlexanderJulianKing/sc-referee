# Alkaline pretreatment and steady-state methane yield in pilot anaerobic digesters

## Data

`data/input.csv` holds 60 weekly monitoring records from 12 independently fed pilot digesters, covering run weeks 4-8. Each digester kept the same feedstock pretreatment for the entire campaign, so the weekly records belonging to one digester are repeated measurements of that reactor and are not independent of one another.

## Analysis

Each reactor was first collapsed to a single steady-state summary value: the arithmetic mean of its weekly specific methane yields. The resulting 12 reactor-level means -- one analysed value per independent unit -- were then compared between the two pretreatments with a two-sided exact Mann-Whitney U test. The rank-biserial correlation is reported as the effect size.

## Reactor-level summaries

| reactor | pretreatment | weeks used | mean CH4 yield (NL/g VS) |
| --- | --- | --- | --- |
| R01 | control | 5 | 198.60 |
| R02 | alkaline | 5 | 231.40 |
| R03 | control | 5 | 205.40 |
| R04 | alkaline | 5 | 242.60 |
| R05 | control | 5 | 212.00 |
| R06 | alkaline | 5 | 258.40 |
| R07 | control | 5 | 219.80 |
| R08 | alkaline | 5 | 266.00 |
| R09 | control | 5 | 236.20 |
| R10 | alkaline | 5 | 274.20 |
| R11 | control | 5 | 248.00 |
| R12 | alkaline | 5 | 287.40 |

## Group summaries

| pretreatment | reactors | mean | median | min | max |
| --- | --- | --- | --- | --- | --- |
| control | 6 | 220.00 | 215.90 | 198.60 | 248.00 |
| alkaline | 6 | 260.00 | 262.20 | 231.40 | 287.40 |

All yields are given in NL CH4 per g volatile solids fed.

## Result

[selected-result] Two-sided exact Mann-Whitney U test on 12 reactor-level mean methane yields (6 control vs 6 alkaline reactors, one value per reactor): U = 33.0, p = 0.0152, rank-biserial correlation = 0.833; alkaline-pretreated reactors reached a higher steady-state yield (median 262.20 vs 215.90 NL CH4 per g VS, difference in group means 40.00 NL/g VS).

The comparison is made at the reactor level because pretreatment was applied to reactors, not to weekly samples; the 60 weekly records support the reactor means but do not enlarge the sample size for this claim.
