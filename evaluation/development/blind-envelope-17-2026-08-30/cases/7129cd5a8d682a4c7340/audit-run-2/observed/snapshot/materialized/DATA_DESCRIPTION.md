# Data description

Two committed CSV files. The values in both are fixed on disk and are not regenerated at run time.

## `vanilla_curing_pods.csv` — raw pod-level measurements

One row is one cured vanilla pod, measured individually at the end of curing. There are 72 rows plus
a header row: 36 pods cured by the traditional sun-and-sweat method and 36 cured by the hot-water
blanch plus oven-assisted method, all from a single green harvest lot. Every pod has a value for
every outcome; there are no missing cells.

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `pod_id` | text | — | Pod identifier, prefix `VP` plus a zero-padded three-digit serial (`VP001`–`VP072`). Unique across the file. |
| `curing_method` | text | — | Group label. Exactly two distinct values: `traditional` (sun-and-sweat curing over about three months) and `oven_assisted` (hot-water blanch followed by oven-assisted curing over about six weeks). |
| `vanillin_g_per_100g` | number | g / 100 g dry mass | Declared outcome 1. Vanillin content of the cured pod, reported to 2 decimal places. |
| `moisture_pct` | number | percent by mass | Declared outcome 2. Moisture content of the cured pod, reported to 1 decimal place. |
| `p_hydroxybenzaldehyde_mg_per_100g` | number | mg / 100 g dry mass | Declared outcome 3. p-hydroxybenzaldehyde content of the cured pod, reported to 1 decimal place. |
| `bend_force_n` | number | newtons | Declared outcome 4. Pod flexibility, measured as the force required to bend the pod. Reported to 2 decimal places. A larger value means a stiffer, less flexible pod. |
| `surface_lightness_l_star` | number | CIE L\* coordinate (dimensionless, 0 = black, 100 = white) | Declared outcome 5. Surface colour lightness of the cured pod, reported to 2 decimal places. |

Columns 3 to 7 are the five outcome variables of the declared outcome family, in the order fixed in
the study plan before curing began.

## `adjusted_pvalues.csv` — upstream pipeline statistics output

One row is one declared outcome variable. There are 5 rows plus a header row, given in the declared
outcome order. This file is the output of the laboratory's earlier processing stage, which performed
the family-wise adjustment across the complete five-outcome family. It carries only the adjusted
values; unadjusted p-values and test statistics are not part of this file.

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `outcome` | text | — | Name of the declared outcome variable. Uses exactly the same names as the outcome column headers of `vanilla_curing_pods.csv`. |
| `adjusted_p_value` | number | probability, 0 to 1 | The already-adjusted p-value for that outcome, adjusted by the upstream stage for the complete five-outcome family. Written to three significant figures, so small values appear in scientific notation (for example `5.66e-07`). |

Row order in this file matches the declared outcome order: `vanillin_g_per_100g`, `moisture_pct`,
`p_hydroxybenzaldehyde_mg_per_100g`, `bend_force_n`, `surface_lightness_l_star`.
