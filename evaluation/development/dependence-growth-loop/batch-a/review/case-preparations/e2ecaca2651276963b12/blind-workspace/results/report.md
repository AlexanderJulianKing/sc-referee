# Steam-explosion pretreatment and specific methane yield

## Data

40 feeding-cycle measurements from 10 bench-scale mesophilic digesters, 4
consecutive cycles per digester. Feedstock pretreatment (untreated or
steam_exploded) was assigned to whole digesters, so the digester is the
independent unit and the four cycle yields from one vessel are repeated
measurements of that unit.

## Analysis

Each digester was first collapsed to its mean specific methane yield across
its 4 cycles, giving one analysed value per independent unit (n = 10). The
two pretreatment groups were then compared with an exact two-sided
permutation test on the difference in group means, enumerating all 252 ways
of splitting the 10 digester means into groups of 5 and 5.

## Digester means

| digester | pretreatment | cycles | mean yield (mL CH4 / g VS) |
| --- | --- | --- | --- |
| D01 | untreated | 4 | 218.50 |
| D02 | untreated | 4 | 224.00 |
| D03 | untreated | 4 | 212.75 |
| D04 | untreated | 4 | 229.25 |
| D05 | untreated | 4 | 221.50 |
| D06 | steam_exploded | 4 | 268.00 |
| D07 | steam_exploded | 4 | 255.50 |
| D08 | steam_exploded | 4 | 274.25 |
| D09 | steam_exploded | 4 | 261.75 |
| D10 | steam_exploded | 4 | 249.50 |

## Group comparison

| pretreatment | digesters | mean of digester means | SD |
| --- | --- | --- | --- |
| untreated | 5 | 221.20 | 6.153 |
| steam_exploded | 5 | 261.80 | 9.803 |

Difference (steam_exploded - untreated): 40.60 mL CH4 / g VS.
Cohen's d on digester means: 4.96.
Exact permutation p-value: 0.0079 (2 of 252 splits at least as extreme as
the observed difference).

[selected-result] Steam-explosion pretreatment increased specific methane yield by 40.60 mL CH4 / g VS (261.80 vs 221.20), tested on 10 independent digesters (5 vs 5) with one mean per digester: exact permutation p = 0.0079.

## Note on units

The 40 rows in the input file are not 40 independent observations. All
inference above is based on the 10 digester-level means.
