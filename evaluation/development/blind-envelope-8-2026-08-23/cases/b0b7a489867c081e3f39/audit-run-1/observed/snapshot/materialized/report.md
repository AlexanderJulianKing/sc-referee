# Seagrass condition inside and outside a boat-mooring exclusion zone

A coastal survey team compared maximum seagrass leaf length in water closed to anchoring against
adjacent water open to mooring. This report describes the survey data, the comparison applied to it,
the numerical results, and what those results mean for management of the exclusion zone.

## Data description

The project holds one data file, `seagrass_survey.csv`: comma separated, one header row and 96 data
rows. There are no missing values in any column.

**What one row represents.** One row is one sampled dive point inside one seagrass meadow. It carries
the maximum leaf length of the single shoot measured at that point, together with the water depth and
the sediment type recorded at that same point.

**Columns.**

| column | type | units | description |
|--------|------|-------|-------------|
| `meadow_id` | text | — | Identifier of the surveyed meadow, `MDW01` through `MDW12`. |
| `zone` | text | — | Mooring status recorded for the point. Two values: `protected` (inside the exclusion zone, anchoring prohibited) and `open` (adjacent water open to mooring). |
| `point_number` | integer | — | Which of the eight sampling points this row is, numbered 1 to 8. |
| `leaf_length_cm` | number | centimetres | Maximum leaf length: the longest leaf on the one shoot measured at this point. Recorded to 0.1 cm. |
| `depth_m` | number | metres | Water depth at the sampling point. Recorded to 0.01 m. |
| `sediment_type` | text | — | Sediment recorded at the sampling point. |

**Layout.** Twelve meadows were surveyed. Divers placed eight haphazard sampling points in each meadow
and measured the longest leaf on one shoot at each point, giving 12 x 8 = 96 rows. Meadows `MDW01`
through `MDW06` lie inside the exclusion zone and are labelled `protected`; `MDW07` through `MDW12` lie
in adjacent water and are labelled `open`. Each zone therefore contributes 48 sampled points.

**Ranges and levels.** Maximum leaf length runs from 25.0 to 84.3 cm. Water depth runs from 1.50 to
6.00 m, with a mean of 3.92 m. Sediment type takes five values: `medium_sand` (24 points),
`muddy_sand` (24), `silt` (18), `fine_sand` (15) and `shell_gravel` (15).

## Methods

The response variable is maximum leaf length in centimetres (`leaf_length_cm`). The grouping variable
is `zone`.

Every sampled point in the table entered the comparison as one observation, giving n = 96 (48
protected, 48 open). The two zones were compared with an independent two-sample t-test assuming equal
variances, evaluated two-sided at alpha = 0.05. Alongside the test the analysis reports each zone's
mean, standard deviation and range, the difference in means with a 95 percent confidence interval, and
Cohen's *d* computed from the pooled standard deviation.

The analysis is implemented in `analysis.py` (Python, pandas and SciPy) and is reproduced by running
`python3 analysis.py` from the project root.

## Results

Sample size entering the comparison: **n = 96** sampled points.

| zone | n | mean (cm) | sd (cm) | min (cm) | max (cm) |
|------|---|-----------|---------|----------|----------|
| `protected` | 48 | 63.43 | 10.25 | 44.20 | 84.30 |
| `open` | 48 | 48.01 | 10.16 | 25.00 | 72.50 |

Maximum leaf length averaged **63.43 cm** at protected points and **48.01 cm** at points open to
mooring, a difference of **15.42 cm** in favour of the protected zone (95 percent CI 11.28 to 19.55 cm).

Independent two-sample t-test: **t(94) = 7.40, p = 5.66 x 10^-11**. The result is significant at
alpha = 0.05.

The standardised effect size is **Cohen's *d* = 1.51** (pooled sd = 10.21 cm), a large effect: leaf
length in the protected zone sits roughly one and a half standard deviations above leaf length in the
open zone.

## Interpretation

Seagrass inside the boat-mooring exclusion zone carries substantially longer leaves than seagrass in
adjacent water open to mooring. The 15.4 cm advantage amounts to about a 32 percent increase over the
48.0 cm open-zone mean, and the confidence interval keeps the advantage well above 11 cm across its
whole range. An effect of this size is ecologically meaningful, not merely detectable. Longer leaves
mean greater canopy height and leaf area, which in turn support higher primary production, more
sediment trapping and stabilisation, and better shelter and nursery habitat for fish and invertebrates.

The pattern is what a marine ecologist would expect where anchoring pressure has been removed. Anchors
and mooring chains scour the seabed, cut rhizomes and clear patches of canopy, and the repeated
disturbance keeps meadows in a cropped, early-recovery state. Removing that pressure lets the canopy
grow out. The two zones sit in adjacent water and span comparable depths (mean 3.69 m protected, 4.15 m
open) and the same set of sediment types, so habitat setting does not offer an obvious alternative
explanation for a gap of this magnitude.

### Management implication

The exclusion zone is working, and the evidence supports keeping it in place and enforcing it. Two
practical steps follow. First, protect the gain already made: maintain the anchoring prohibition and
back it with visible marker buoys and routine patrols, since an unenforced boundary delivers no benefit.
Second, extend the approach: install fixed environmentally friendly moorings, which hold vessels on a
single anchored point rather than dragging chain across the meadow, in the adjacent open areas where
boat traffic concentrates, and consider widening the exclusion zone to cover the most heavily used
meadows there. Resurveying the same twelve meadows on a fixed schedule would track whether the
protected canopy continues to gain and whether managed mooring narrows the gap in the open zone.
