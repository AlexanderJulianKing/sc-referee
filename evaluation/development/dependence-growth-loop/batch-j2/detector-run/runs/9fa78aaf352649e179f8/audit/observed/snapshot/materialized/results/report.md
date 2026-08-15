# Routine metabolic rate of juvenile Atlantic salmon on a beta-glucan diet

## Design and data

The file data/input.csv contains 46 overnight respirometry sessions recorded on
12 recirculating tanks: 6 fed the control ration and 6 fed the same ration with a
beta-glucan supplement. Each tank was measured on three or four separate nights, so the
46 rows are repeated sessions rather than 46 independent observations. Diet was
randomised to whole tanks, and each tank ran on its own water loop, feeder and biofilter,
so the tank is the independent experimental unit.

## Analysis

Sessions were averaged within each tank before any test was run, so every tank
contributes exactly one value (mass-specific oxygen uptake, MO2, in mg O2 kg^-1 h^-1) to
the comparison. The two diets were then compared with a two-sided exact Mann-Whitney U
test on the 12 tank means (6 control vs 6 beta-glucan). The individual session rows were
never entered into the test.

## Tank-level summary

| tank | diet | sessions | mean MO2 (mg O2 kg^-1 h^-1) |
| --- | --- | --- | --- |
| T01 | control | 4 | 209.75 |
| T02 | beta-glucan | 4 | 228.75 |
| T03 | control | 4 | 198.20 |
| T04 | beta-glucan | 4 | 212.30 |
| T05 | control | 3 | 219.30 |
| T06 | beta-glucan | 4 | 241.25 |
| T07 | control | 4 | 205.10 |
| T08 | beta-glucan | 4 | 224.40 |
| T09 | control | 4 | 215.60 |
| T10 | beta-glucan | 3 | 233.10 |
| T11 | control | 4 | 202.45 |
| T12 | beta-glucan | 4 | 237.90 |

## Result

Averaged over tanks, MO2 was 229.62 mg O2 kg^-1 h^-1 on the beta-glucan diet and 208.40
on the control diet; the tank medians were 230.9 and 207.4, a median difference of 23.5
mg O2 kg^-1 h^-1. The exact Mann-Whitney U test on the 12 tank means gives U = 34.0,
p = 0.008658, rank-biserial correlation 0.889.

[selected-result] Tanks fed the beta-glucan supplement had higher routine oxygen uptake than control tanks (two-sided exact Mann-Whitney U on 6 vs 6 tank means, U = 34.0, p = 0.008658, rank-biserial 0.889).

## Notes

Tanks T05 and T10 each lost one night to a chiller fault; the unbalanced session counts
change the precision of those two tank means but not the number of independent units,
which stays at one per tank. A rank test was preferred to a t test because six tanks per
diet give little leverage for judging normality.
