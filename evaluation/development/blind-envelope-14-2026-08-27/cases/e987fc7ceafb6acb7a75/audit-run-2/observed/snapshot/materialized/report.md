# Separating lime and oilseed rape honey by routine physicochemical markers

A two-stage discovery-and-validation analysis of 90 honey samples.

All numbers below are produced by `analysis.py`, run against `honey_markers.csv`.

## 1. Data

`honey_markers.csv` holds one row per honey sample. A row is a single homogenised jar
from one registered producer, analysed once on the full six-marker panel. There are 90
rows and no repeated jars. Every cell is filled.

| Column | Type | Units | What it holds |
| --- | --- | --- | --- |
| `sample_id` | text | none | Laboratory identifier for the jar, `H-001` to `H-090`, unique in the file |
| `floral_origin` | text | none | Declared floral origin, exactly two values: `lime`, `oilseed_rape` |
| `analysis_set` | text | none | Pre-assigned analysis set, exactly two values: `discovery`, `validation` |
| `moisture_pct` | number | percent by mass | Moisture content, rounded to 0.1 |
| `conductivity_ms_per_cm` | number | mS per cm | Electrical conductivity of a 20 percent (w/w) solution, rounded to 0.001 |
| `hmf_mg_per_kg` | number | mg per kg | Hydroxymethylfurfural, rounded to 0.1, right-skewed across samples |
| `diastase_number` | number | Schade units | Diastase activity, rounded to 0.1 |
| `proline_mg_per_kg` | number | mg per kg | Proline content, rounded to the nearest whole unit |
| `free_acidity_meq_per_kg` | number | milliequivalents per kg | Free acidity, rounded to 0.1 |

The six marker columns appear in the order the laboratory declared them: moisture,
conductivity, HMF, diastase, proline, free acidity. That declared order is the outcome
family for this study.

## 2. Design and group sizes

Ninety samples were collected, 45 declared as lime blossom honey and 45 declared as
oilseed rape honey. Each sample is one jar measured once, so the rows are independent of
one another and there is nothing to average within a jar.

Before any measurement, the laboratory split the samples into two analysis sets. That
split is recorded in `analysis_set`, and no measurement influenced it.

| Floral origin | discovery | validation | Total |
| --- | --- | --- | --- |
| `lime` | 23 | 22 | 45 |
| `oilseed_rape` | 23 | 22 | 45 |
| Total | 46 | 44 | 90 |

Both origins appear in both sets in near-equal numbers, so each stage compares 22 or 23
samples per origin.

## 3. Why the analysis runs in two stages

Testing six markers at the usual 5 percent level would give roughly a 1 in 4 chance of
at least one false alarm somewhere in the panel, even if no marker really differed. The
study controls that risk by splitting the work across the two pre-assigned halves.

**Stage one, screening.** Using only the 46 discovery samples, each of the six declared
markers is compared between the two origins with a two-sided Welch two-sample t-test
(the version of the t-test that does not assume the two groups share a variance). Any
marker with an unadjusted p below 0.05 is carried forward. This stage decides *which
markers get looked at again* and nothing else. It produces no finding.

**Stage two, confirmation.** Using only the 44 validation samples, the surviving markers
are re-tested with the same Welch t-test and judged against a Bonferroni-adjusted level:
0.05 divided by the number of markers being confirmed in this stage.

This controls the family-wise error for the study's verdicts because the analysis-set
assignment was fixed before measurement. The validation measurements therefore carry no
information about which markers the discovery half chose to send forward. Whatever the
screen selects, the confirmation stage is a fresh set of tests on data the selection
never touched, and Bonferroni over that fixed number of tests holds the chance of even
one false confirmation at or below 0.05. Put another way, the screen is allowed to guess
freely because its guesses are checked against evidence it never saw.

The trade is that a marker dropped at screening simply exits the study. It is not
declared absent, and it is not given a verdict. It was never tested in the validation
half.

## 4. Stage one: screening table (discovery half only)

Discovery samples: 23 lime, 23 oilseed rape. Welch two-sided t-test, threshold p < 0.05,
unadjusted. **These rows are screening decisions, not findings.**

| Marker | lime mean (SD) | oilseed rape mean (SD) | Difference | p | Screen |
| --- | --- | --- | --- | --- | --- |
| Moisture (%) | 17.252 (1.007) | 17.470 (0.925) | -0.217 | 0.450 | drop |
| Conductivity (mS/cm) | 0.622 (0.091) | 0.147 (0.028) | 0.475 | 2.1e-19 | pass |
| HMF (mg/kg) | 7.265 (5.717) | 5.965 (4.936) | 1.300 | 0.414 | drop |
| Diastase number (Schade) | 25.948 (6.723) | 18.570 (6.335) | 7.378 | 0.00040 | pass |
| Proline (mg/kg) | 472.913 (53.251) | 291.652 (53.878) | 181.261 | 8.1e-15 | pass |
| Free acidity (meq/kg) | 31.848 (5.596) | 19.878 (4.271) | 11.970 | 4.0e-10 | pass |

Difference is lime minus oilseed rape.

Four markers pass the screen: conductivity, diastase number, proline, free acidity. Two
are dropped: moisture and HMF. The two dropped markers leave the study here and receive
no verdict of any kind.

## 5. Stage two: confirmation table (validation half only)

Validation samples: 22 lime, 22 oilseed rape. Four markers are being confirmed in this
stage, so k = 4 and the adjusted level is

> **alpha_adj = 0.05 / 4 = 0.0125**

A marker is confirmed only if its validation p-value falls below 0.0125. Confidence
intervals are given at the matching 98.75 percent level, so each interval excludes zero
exactly when its marker is confirmed.

| Marker | lime mean (SD) | oilseed rape mean (SD) | Difference | 98.75% CI | Welch t (df) | p | Verdict at 0.0125 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Conductivity (mS/cm) | 0.645 (0.096) | 0.155 (0.034) | 0.490 | [0.431, 0.548] | 22.48 (26.3) | 1.1e-18 | **CONFIRMED** |
| Diastase number (Schade) | 21.032 (6.732) | 21.627 (5.039) | -0.595 | [-5.291, 4.100] | -0.33 (38.9) | 0.742 | not confirmed |
| Proline (mg/kg) | 487.727 (61.162) | 302.227 (57.878) | 185.500 | [138.639, 232.361] | 10.33 (41.9) | 4.3e-13 | **CONFIRMED** |
| Free acidity (meq/kg) | 32.009 (5.671) | 20.750 (4.270) | 11.259 | [7.296, 15.223] | 7.44 (39.0) | 5.4e-09 | **CONFIRMED** |

Standardised effect sizes (Hedges' g, lime minus oilseed rape) for the markers taken to
confirmation: conductivity 6.66, proline 3.06, free acidity 2.20, diastase number -0.10.

Moisture and HMF do not appear in this table. They failed the screen, so they were never
tested in the validation half and have no row here.

## 6. Conclusions

Every statement here rests on the validation half. No discovery p-value is offered as
evidence that a marker differs.

1. **Electrical conductivity separates the two declared origins.** In the validation
   half, lime honey averaged 0.645 mS/cm and oilseed rape honey 0.155 mS/cm, a
   difference of 0.490 mS/cm (98.75% CI 0.431 to 0.548, p = 1.1e-18, below the adjusted
   level of 0.0125). The standardised effect is very large.

2. **Proline content separates the two declared origins.** Lime averaged 488 mg/kg
   against 302 mg/kg for oilseed rape, a difference of 186 mg/kg (98.75% CI 139 to 232,
   p = 4.3e-13).

3. **Free acidity separates the two declared origins.** Lime averaged 32.0 meq/kg
   against 20.8 meq/kg, a difference of 11.3 meq/kg (98.75% CI 7.3 to 15.2,
   p = 5.4e-09).

4. **Diastase number is not confirmed.** It passed the screen in the discovery half
   (p = 0.00040) but did not repeat in the validation half: the difference there was
   -0.6 Schade units, with a 98.75% interval from -5.3 to 4.1 and p = 0.742. This is the
   case the two-stage design exists to catch. Reporting the discovery result on its own
   would have announced a difference that the independent half does not support.
   Diastase number is reported here as screened in and not confirmed.

5. **Moisture and HMF have no verdict.** Both failed screening in the discovery half and
   were not carried into confirmation. The study neither confirms a difference nor
   establishes their absence for these two markers; they were not taken to the stage
   that issues verdicts.

Three of the six declared markers are confirmed separators at a family-wise error rate
of 0.05: conductivity, proline, and free acidity. Together they give the laboratory an
independently confirmed basis for flagging a declared floral origin that does not match
its physicochemical profile.

## 7. Limitations

- Group sizes are 22 to 23 per origin in each stage. The confirmation stage has enough
  power for the large differences seen here, but a genuine small difference could easily
  fail to confirm at the 0.0125 level. "Not confirmed" is not the same as "no
  difference."
- The Welch t-test compares means. HMF is right-skewed, so its screening test leans on
  the central limit theorem at 23 samples per group rather than on normally distributed
  values. HMF was dropped at screening in any case, so no verdict depends on that
  approximation.
- Floral origin here is the origin *declared* by the producer, not an independently
  verified botanical origin. The study shows these markers separate the two declared
  populations; it does not on its own establish that any single out-of-range jar is
  mislabelled.
- The comparison covers two floral origins from one region. Nothing here extends to
  other origins, other regions, or other seasons.
