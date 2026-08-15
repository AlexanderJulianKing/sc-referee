# Copper amendment and single-cell-protein titer in methanotroph bench runs

## Data

- Source file: `data/input.csv`
- Rows read: 20
- Independent vessels: 20
- Vessels appearing more than once: none

| medium | vessels | mean titer (g/L) | sd (g/L) |
| --- | ---: | ---: | ---: |
| baseline | 10 | 5.000 | 0.258 |
| cu_amended | 10 | 5.700 | 0.298 |

## Analysis

Each 2-L bioreactor was inoculated once, run to harvest once, and assayed
once, so the ten baseline titers and the ten copper-amended titers are ten
independent observations per arm. The arms were compared with a Welch
two-sample t-test (unequal variances, two-sided).

## Result

- Mean difference (cu_amended minus baseline): 0.700 g/L
- Standard error of the difference: 0.1247 g/L
- Welch t statistic: 5.612
- Welch-Satterthwaite df: 17.64
- Two-sided p-value: 2.71e-05
- Hedges' g: 2.404

[selected-result] Welch two-sample t-test on 20 independent vessels (one titer per vessel): copper amendment raised final single-cell-protein titer by 0.700 g/L (t = 5.612, df = 17.64, two-sided p = 2.71e-05, Hedges' g = 2.404).

## Notes

The vessel is both the unit of randomization and the unit of analysis: no
vessel is counted twice, and no within-vessel replicate measurements enter
the test. The seed-density column is recorded for provenance and was not
used in the comparison.
