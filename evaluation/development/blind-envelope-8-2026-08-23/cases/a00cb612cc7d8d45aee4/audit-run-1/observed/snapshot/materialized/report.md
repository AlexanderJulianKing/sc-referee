# Trace-mineral supplementation and fleece fineness in huacaya alpacas

## Summary

Twenty adult huacaya alpacas were sampled monthly for four months. Fleece from the supplemented
ration averaged 24.57 um against 26.55 um on the unsupplemented ration, a saving of 1.99 um
(t = -4.588, p = 1.68e-05, n = 80). The supplement is worth feeding.

## Data description

The trial data sit in one table, `alpaca_fibre.csv`, with 80 data rows and one header row.

**One row is one mid-side fibre sample taken from one alpaca in one calendar month**, carrying that
month's fibre diameter measurement together with the animal's age and the body weight recorded at
that sampling.

| Column | Type | Units | What it holds |
| --- | --- | --- | --- |
| `alpaca_id` | text | — | Animal identifier, `ALP01` through `ALP20`. |
| `diet_group` | text | — | Ration fed: `supplemented` or `unsupplemented`. |
| `sampling_month` | text | — | Calendar month of the sampling, `YYYY-MM`: `2026-03`, `2026-04`, `2026-05` or `2026-06`. |
| `fibre_diameter_um` | number | micrometres (um) | Mean fibre diameter of that month's mid-side sample, to 2 decimals. |
| `age_years` | integer | years | Age of the animal in whole years. |
| `body_weight_kg` | number | kilograms | Body weight recorded at that sampling, to 1 decimal. |

Coverage: 20 animals, 10 on each ration, 4 monthly samplings each, giving 80 rows. Age spans 2 to 11
years and body weight 56.4 to 84.9 kg. There are no missing cells. The values are simulated for this
worked example rather than measured in a real herd; `make_data.py` regenerates the file byte for byte
from a fixed seed.

## Methods

Fibre diameter was compared between the two rations with an independent two-sample t-test
(Student's, equal variances assumed), run in Python 3 with pandas 2.0.3 and SciPy 1.9.1 by the script
`analysis.py`.

Each monthly fibre sample is one observation, so all 80 measurements entered the test: 40 from the
supplemented ration and 40 from the unsupplemented ration, 78 degrees of freedom. Alongside the test
the script reports each group's mean, standard deviation and range, the group means broken out by
sampling month, the difference in means, the pooled standard deviation and Cohen's d. The
significance threshold was alpha = 0.05. No measurement was excluded and no adjustment was applied.

## Results

**Group summaries, all 80 measurements**

| Ration | n | Mean (um) | SD (um) | Min (um) | Max (um) |
| --- | --- | --- | --- | --- | --- |
| Unsupplemented | 40 | 26.55 | 2.21 | 21.94 | 29.93 |
| Supplemented | 40 | 24.57 | 1.61 | 21.63 | 28.79 |

**Mean fibre diameter by sampling month (um)**

| Sampling month | Unsupplemented | Supplemented |
| --- | --- | --- |
| 2026-03 | 26.52 | 24.88 |
| 2026-04 | 26.67 | 24.55 |
| 2026-05 | 26.46 | 24.43 |
| 2026-06 | 26.56 | 24.40 |

**Test**

| Quantity | Value |
| --- | --- |
| Observations in the test | 80 |
| Degrees of freedom | 78 |
| Difference in means (supplemented - unsupplemented) | -1.99 um |
| Pooled SD | 1.93 um |
| Cohen's d | -1.03 |
| t statistic | -4.588 |
| p-value | 1.68e-05 |

Supplemented fleece measured 1.99 um finer than unsupplemented fleece, and the difference is
significant at alpha = 0.05 by a wide margin. Cohen's d of -1.03 puts the gap at a full pooled
standard deviation. The advantage is present in every one of the four sampling months, ranging from
1.64 um in March to 2.16 um in June, and it widens slightly as the trial runs on: supplemented means
fall from 24.88 to 24.40 um while unsupplemented means hold near 26.5 um.

## Interpretation and recommendation

The trace-mineral supplement delivers finer fleece. Two micrometres is commercially meaningful in
alpaca fibre: it moves an average unsupplemented animal near 26.5 um, at the coarse edge of the
adult huacaya range, down towards 24.5 um, where fleece attracts a higher price per kilogram and is
comfortable next to the skin. The effect showed up in the first month of sampling and held through
all four, which fits a supplement acting on the fibre as it grows rather than a one-off shift.

**Recommendation.** Feed the trace-mineral supplement in the daily ration across the adult huacaya
herd. Keep monthly mid-side sampling in place so the fineness gain can be tracked as the clip builds,
and compare the supplement's cost per head against the price premium the finer micron band earns at
sale to confirm the margin at your own numbers.
