# Leaf-disc necrosis under contrasting soil moisture regimes

## Data

24 leaf discs from 8 chestnut saplings (3 discs per sapling) were scored 96 h after inoculation as `necrotic` or `intact`.

| moisture regime | necrotic | intact | discs | necrotic fraction |
| --- | --- | --- | --- | --- |
| saturated | 9 | 3 | 12 | 0.750 |
| drained | 3 | 9 | 12 | 0.250 |

## Analysis

Each scored leaf disc contributes one observation to the 2 x 2 table of moisture regime
by necrosis outcome. The table is evaluated with Fisher's exact test (two-sided) as
implemented in scipy.stats.fisher_exact.

## Result

Sample odds ratio (saturated vs drained) = 9.000; two-sided p = 0.0391.

[selected-result] Fisher's exact test across the 24 inoculated leaf discs gives a two-sided p = 0.0391 with a sample odds ratio of 9.000, indicating a significant association between soil moisture regime and leaf-disc necrosis at alpha = 0.05.
