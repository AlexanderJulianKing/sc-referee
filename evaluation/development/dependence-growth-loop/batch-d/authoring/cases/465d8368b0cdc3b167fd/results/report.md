# Marsh helleborine recovery in restored dune slacks

## Design

Each row of `data/input.csv` is one restored dune slack, walked once during the
2025 flowering season. No slack contributes more than one row, so the 24 rows
are 24 independent units and a row-independent test is appropriate.

## Analysis

Presence or absence of marsh helleborine (*Epipactis palustris*) was
cross-tabulated against restoration method, and the resulting 2 x 2 table was
assessed with Fisher's exact test (two-sided).

## Counts

| Restoration method | Present | Absent | Slacks | Detection rate |
| --- | --- | --- | --- | --- |
| Deep topsoil inversion | 9 | 3 | 12 | 75.0% |
| Turf stripping | 3 | 9 | 12 | 25.0% |

## Result

- Sample odds ratio (inversion vs stripping): 9.00
- Difference in detection rate: 0.500
- Fisher's exact test, two-sided: p = 0.0391

[selected-result] Fisher's exact test on 24 independently restored dune slacks: marsh helleborine was present at 9 of 12 inversion slacks and 3 of 12 turf-stripped slacks (sample odds ratio 9.00, two-sided p = 0.0391), a statistically significant advantage for deep topsoil inversion at the 5% level.

## Reading the result

With one survey per slack there is no within-site replication to inflate the
count of independent observations: each of the 24 sites contributes exactly one
Bernoulli outcome to the table. The effect is estimated from a small sample, so
the interval around the odds ratio is wide even though the two-sided p-value
falls below 0.05.
