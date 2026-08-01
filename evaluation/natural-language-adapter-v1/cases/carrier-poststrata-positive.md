## Uniform full-partner-roster estimate

Test completion is strongly nonuniform across the visible roster fields. I formed exact poststrata from ancestry, family-history tier, intake site, and collection wave. Every one of the 16 cells has completed assays. Within each ancestry, the completed-partner positive rate in each cell is weighted by that cell's share of all 250 ancestry-specific roster rows. This yields standardized positive rates:

| Ancestry | class_01 | class_02 | class_03 |
|---|---:|---:|---:|
| AFR | 0.04 | 0.12266666666666667 | 0.028000000000000004 |
| EUR | 0.016 | 0.099 | 0.115 |

These rates are corrected with ancestry-matched lot_C42 controls. Lot_C42 sensitivities are `(102/130, 64/150, 120/120)` for AFR and `(112/130, 120/150, 120/120)` for EUR. None-control false-positive rates are `(0, 10/180, 0)` for AFR and `(0, 6/180, 0)` for EUR. The corrected total carrier probabilities are 0.2598187155101562 for the AFR half of the roster and 0.21922360248447206 for the EUR half. Giving every roster row equal weight therefore gives

`0.5 × 0.2598187155101562 + 0.5 × 0.21922360248447206 = 0.23952115899731413`.
