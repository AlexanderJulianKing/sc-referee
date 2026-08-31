# Curing method and cured-pod quality in vanilla: laboratory analysis note

## Aim and methods compared

The aim was to compare two curing methods for green vanilla pods from a single harvest lot.
Seventy-two green pods were split evenly between the two methods:

- **traditional** — sun-and-sweat curing over about three months (36 pods);
- **oven_assisted** — a hot-water blanch followed by oven-assisted curing over about six weeks
  (36 pods).

Curing method is the only comparison in the study. Each cured pod is one subject and was analysed
individually at the end of curing.

## Data

Two committed CSV files hold fixed values on disk; nothing is generated at run time.

### `vanilla_curing_pods.csv` — raw pod-level measurements

One row is one cured vanilla pod, measured individually at the end of curing. 72 rows.

| Column | Description |
| --- | --- |
| `pod_id` | Pod identifier, `VP001`–`VP072`. |
| `curing_method` | Group label, either `traditional` or `oven_assisted`. |
| `vanillin_g_per_100g` | Declared outcome 1. Vanillin content, g per 100 g dry mass. |
| `moisture_pct` | Declared outcome 2. Moisture content, percent by mass. |
| `p_hydroxybenzaldehyde_mg_per_100g` | Declared outcome 3. p-hydroxybenzaldehyde content, mg per 100 g dry mass. |
| `bend_force_n` | Declared outcome 4. Pod flexibility as the force to bend the pod, newtons. A larger value means a stiffer pod. |
| `surface_lightness_l_star` | Declared outcome 5. Surface colour lightness, CIE L\* coordinate. |

### `adjusted_pvalues.csv` — upstream pipeline statistics output

One row is one declared outcome variable, in the declared outcome order. 5 rows.

| Column | Description |
| --- | --- |
| `outcome` | Name of the declared outcome, using exactly the same names as the outcome columns of the raw file. |
| `adjusted_p_value` | The already-adjusted p-value for that outcome, adjusted for the complete five-outcome family. |

## How the analysis was done

The five outcomes above were declared as one outcome family, in that fixed order, in the study plan
before curing began. The family-wise adjustment across all five outcomes was performed by the
upstream pipeline stage that wrote `adjusted_pvalues.csv`.

`analysis.py` therefore ran no statistical test and computed no p-value of its own. It did two
things. First it summarised and checked the raw file: per group and per outcome it reported the
number of pods, mean, standard deviation, minimum and maximum, and it confirmed that both curing
methods were present with 36 pods each, that no cell was missing, that every outcome cell parsed as
a number, and that every value sat inside a physically sensible range. All nine checks passed.
Second, it read the adjusted p-values from `adjusted_pvalues.csv` and took every verdict from those
loaded values, comparing each to the conventional 0.05 threshold.

Descriptive summaries from the raw file (mean, with standard deviation in brackets; n = 36 per
group):

| Outcome | traditional | oven_assisted |
| --- | --- | --- |
| `vanillin_g_per_100g` | 1.733 (0.335) | 2.059 (0.352) |
| `moisture_pct` | 28.133 (2.590) | 23.850 (3.447) |
| `p_hydroxybenzaldehyde_mg_per_100g` | 94.858 (22.707) | 105.558 (21.095) |
| `bend_force_n` | 2.622 (0.624) | 3.370 (0.724) |
| `surface_lightness_l_star` | 26.792 (1.829) | 26.096 (1.687) |

## Results

Outcomes are given in the declared order. The p-value shown for each is the adjusted value loaded
from `adjusted_pvalues.csv`; the verdict compares it to 0.05.

1. **`vanillin_g_per_100g`** — traditional 1.733, oven_assisted 2.059 (difference +0.326 g per 100 g).
   Adjusted p = 0.000434. **Significant.**

2. **`moisture_pct`** — traditional 28.133, oven_assisted 23.850 (difference -4.283 percentage
   points). Adjusted p = 5.66e-07. **Significant.**

3. **`p_hydroxybenzaldehyde_mg_per_100g`** — traditional 94.858, oven_assisted 105.558 (difference
   +10.700 mg per 100 g). Adjusted p = 0.0841. **Not significant.**

4. **`bend_force_n`** — traditional 2.622, oven_assisted 3.370 (difference +0.748 N). Adjusted
   p = 5.29e-05. **Significant.**

5. **`surface_lightness_l_star`** — traditional 26.792, oven_assisted 26.096 (difference -0.696 L\*
   units). Adjusted p = 0.0979. **Not significant.**

## Conclusion

In this harvest lot, oven-assisted curing gave pods with more vanillin, less residual moisture and a
higher bend force, and all three of those differences held up after the family-wise adjustment
across the five declared outcomes. The p-hydroxybenzaldehyde content was higher and the surface was
slightly darker under oven-assisted curing, but neither of those differences met the 0.05 threshold
on the adjusted values, so this study does not establish them. The short oven-assisted route
produces a drier, firmer, more vanillin-rich cured pod than the three-month sun-and-sweat route.
