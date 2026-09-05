# Steeping regime trial: conventional two-step steep versus extended air-rest steep

## Data

The analysis reads `malting_lots.csv`, which holds 48 data rows and one header row, with no blank
cells.

One row is one micro-malting lot: a single 5 kg lot of spring malting barley, one variety and one
harvest year, all lots drawn from the same grain bulk. Each lot was steeped under the regime named
in its row, then germinated and kilned under conditions identical for every lot, then analysed in
the laboratory. Each lot appears exactly once, and the five outcome columns are that lot's
laboratory results.

Columns:

| Column | Units | Description |
|---|---|---|
| `lot_id` | — | Lot identifier, `LOT-001` through `LOT-048`, unique to the row |
| `steep_regime` | — | Group column, exactly two values: `two_step` and `extended_air_rest` |
| `friability_pct` | percent | Friability of the finished malt, declared outcome 1 |
| `fine_extract_pct_dry` | percent, dry basis | Fine grind extract on a dry basis, declared outcome 2 |
| `fan_mg_per_l` | mg/L | Free amino nitrogen in the laboratory wort, declared outcome 3 |
| `diastatic_power_wk` | degrees Windisch-Kolbach | Diastatic power, declared outcome 4 |
| `beta_glucan_mg_per_l` | mg/L | Beta-glucan in the laboratory wort, declared outcome 5 |

## Design

Forty-eight lots of 5 kg each were prepared from the same grain bulk and randomly allocated to one
of two steeping regimes, 24 lots per regime:

| Steeping regime | Lots |
|---|---|
| `two_step` (conventional two-step steep) | 24 |
| `extended_air_rest` (extended air-rest steep) | 24 |

Germination and kilning were identical for every lot, so the steeping regime is the only condition
that differs between the two groups.

## Method

Five malt-quality outcomes were declared before the trial began, in the order listed above. Each
outcome is a continuous laboratory measurement, and each is compared between the two regimes with a
two-sample Welch t-test, which does not assume the two regimes share the same variance. For each
outcome the analysis reports the two group means, the difference (extended air-rest minus two-step),
and the p-value. An outcome is declared significantly affected by steeping regime when its p-value
is below 0.05.

## Results

| # | Outcome | Mean, `two_step` | Mean, `extended_air_rest` | Difference | p-value | Verdict at p < 0.05 |
|---|---|---|---|---|---|---|
| 1 | `friability_pct` | 82.99 | 87.00 | +4.01 | 0.000071 | Significant |
| 2 | `fine_extract_pct_dry` | 81.20 | 81.22 | +0.02 | 0.943 | Not significant |
| 3 | `fan_mg_per_l` | 158.04 | 167.67 | +9.62 | 0.042 | Significant |
| 4 | `diastatic_power_wk` | 248.04 | 274.08 | +26.04 | 0.000089 | Significant |
| 5 | `beta_glucan_mg_per_l` | 184.92 | 125.00 | -59.92 | 0.000000054 | Significant |

The difference column is the extended air-rest mean minus the two-step mean, so a positive value
means the extended air-rest steep gave the higher result.

## Conclusions

**1. Friability.** The extended air-rest steep raised friability by 4.01 percentage points, from
82.99 to 87.00 percent (p = 0.000071). Friability is significantly affected by steeping regime.
The malt from the extended air-rest steep is the better modified of the two.

**2. Fine extract, dry basis.** The two regimes gave essentially the same fine extract, 81.20
against 81.22 percent, a difference of 0.02 percentage points (p = 0.943). Fine extract is not
significantly affected by steeping regime. On this outcome the two regimes are interchangeable.

**3. Free amino nitrogen.** The extended air-rest steep gave 9.62 mg/L more FAN, 167.67 against
158.04 mg/L (p = 0.042). FAN is significantly affected by steeping regime. The p-value sits just
below the 0.05 threshold, so this is the weakest of the significant results in the family.

**4. Diastatic power.** The extended air-rest steep raised diastatic power by 26.04 degrees
Windisch-Kolbach, from 248.04 to 274.08 (p = 0.000089). Diastatic power is significantly affected
by steeping regime, with the extended air-rest steep giving the higher enzyme potential.

**5. Beta-glucan.** The extended air-rest steep lowered wort beta-glucan by 59.92 mg/L, from 184.92
to 125.00 mg/L (p = 0.000000054). Beta-glucan is significantly affected by steeping regime. This is
the largest effect in the declared family, and lower beta-glucan is the desirable direction for
wort separation.

Taken together, four of the five declared outcomes were significantly affected by steeping regime,
and in each case the extended air-rest steep moved the outcome in the direction the maltings would
prefer: more friable malt, more free amino nitrogen, higher diastatic power, and less beta-glucan.
Fine extract was unchanged.
