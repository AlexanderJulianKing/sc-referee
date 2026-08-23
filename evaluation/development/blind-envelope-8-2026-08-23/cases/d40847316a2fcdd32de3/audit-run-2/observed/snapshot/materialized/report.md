# Prescribed burning and nitrogen enrichment in termite mound soil

## Data

The analysis uses one table, `termite_mound_soil_nitrogen.csv`: a header row plus 112 data rows.

**One row is one soil core.** It records the total soil nitrogen measured in that single core,
along with the mound the core came from, how far from the mound base and how deep it was taken, and
the soil pH of that core. A row is not a mound. Eight rows share each mound, and those eight cores
are spatial subsamples of the same mound rather than eight independent observations.

Fourteen mounds were sampled, eight cores each, so 112 rows. Seven mounds sit in a block burned two
years before sampling and seven in an adjacent unburned block. The burn label is a property of the
mound, so all eight cores from a mound carry the same label. The design is balanced: 7 mounds per
block, 8 cores per mound. There are no missing values.

| # | Column | Type | Units | Varies at | Description |
|---|---|---|---|---|---|
| 1 | `mound_id` | text | — | mound | Mound identifier, `MND01`–`MND14`. Groups the 8 rows belonging to one mound. |
| 2 | `burn_block` | text | — | mound | `burned` or `unburned`. Constant across a mound's 8 rows. |
| 3 | `core_number` | integer | — | core | Which of the mound's 8 cores this row is, 1–8. A label only; it does not encode direction or collection order, and the same number in two mounds refers to two unrelated cores. |
| 4 | `total_nitrogen_pct` | decimal | percent by mass | core | Total soil nitrogen in the core. This is the study outcome. |
| 5 | `mound_height_m` | decimal | metres | mound | Height of the mound above surrounding ground. Constant across a mound's 8 rows, so the file holds 14 distinct heights repeated 8 times each, not 112 independent heights. |
| 6 | `core_distance_cm` | decimal | centimetres | core | Distance from the mound base out to the coring point. |
| 7 | `sample_depth_cm` | integer | centimetres | core | Depth of the core: 10, 20, or 30 cm. |
| 8 | `soil_ph` | decimal | pH units | core | Soil pH measured in that core. |

The values are invented for this exercise. They are not measurements from a real field campaign.

## Methods

The mound is the independent unit of the study. The eight cores at a mound share that mound's own
nitrogen level and local soil conditions, so they are correlated with each other. Any procedure that
counts them as 112 independent observations will report a standard error that is too small.

The primary inference is therefore a **cluster bootstrap written for this analysis, in which whole
mounds are drawn with replacement**. The procedure, in full:

1. **Effect estimate.** Compute the mean of `total_nitrogen_pct` over all cores in each block and
   take the difference, burned minus unburned. Because every mound contributes exactly 8 cores, this
   pooled-core difference equals the difference of the two blocks' average mound means.
2. **Resampling for the interval.** Repeat 10,000 times. Within the burned block, draw 7 mound
   identifiers with replacement from the 7 burned mounds; independently, within the unburned block,
   draw 7 with replacement from the 7 unburned mounds. Drawing is **stratified by block**, so each
   replicate keeps 7 mounds per block and the contrast stays estimable. When a mound is drawn, all
   eight of its cores come with it; individual cores are never drawn on their own, so the
   within-mound correlation is carried into every replicate untouched. Recompute the burned-minus-
   unburned difference from the pooled cores of the drawn mounds and store it.
3. **Uncertainty.** The bootstrap standard error is the standard deviation of the 10,000 stored
   differences. The 95% confidence interval is the 2.5th and 97.5th percentiles of that
   distribution.
4. **p-value.** Repeat the identical resampling under a null of no block difference. Each block's
   core values are first shifted by that block's own mean, so after shifting the two blocks share a
   common mean by construction while every mound keeps its own deviation and its internal core
   spread. Ten thousand further whole-mound replicates are drawn from these centred values, and the
   two-sided p-value is `(1 + number of null differences with |difference| >= |observed|) / (10,001)`.

The random number generator is seeded (`numpy.random.default_rng(20260823)`), so re-running
`analysis.py` reproduces every number below exactly. The script also asserts, before analysing, that
each mound has exactly 8 cores and carries exactly one burn label.

The comparison in the Illustrative contrast section below is a plain two-sample Welch t-test on all
112 core rows, computed with `scipy.stats.ttest_ind(..., equal_var=False)`.

## Primary result (dependence-aware)

Mounds analysed: **14** (7 burned, 7 unburned). Cores: **112** (56 per block).

| Block | Mean of mound means | SD across mounds | Range of mound means |
|---|---|---|---|
| burned | 0.1632 | 0.0373 | 0.1100 – 0.2228 |
| unburned | 0.2148 | 0.0334 | 0.1742 – 0.2522 |

| Quantity | Value |
|---|---|
| Effect (burned − unburned) | **−0.0516** percent nitrogen by mass |
| Bootstrap standard error | 0.0176 |
| 95% percentile confidence interval | **[−0.0863, −0.0177]** |
| Bootstrap p-value (two-sided) | **0.0029** (28 of 10,000 null replicates at least as extreme) |

Burned-block mounds hold about 0.052 percentage points less total soil nitrogen than unburned-block
mounds, roughly a quarter lower than the unburned mean of 0.215 percent. The interval excludes zero
across its whole width, though it is wide: the data are consistent with a shortfall anywhere from
about 0.018 to about 0.086 percentage points.

## Illustrative contrast (not a valid inference for this design)

A plain two-sample Welch t-test over all 112 core rows gives:

| Quantity | Value |
|---|---|
| Effect (burned − unburned) | −0.0516 |
| Naive standard error | 0.0076 |
| t | −6.769 |
| p | 6.82 × 10⁻¹⁰ |

**This row-level comparison is not a valid inference for this design.** It treats the eight
correlated cores from each mound as eight independent observations, so it acts as though the study
has 112 independent units when it has 14. Its standard error is understated: 0.0076 against the
cluster bootstrap's 0.0176, meaning the honest standard error is about 2.3 times larger. Its p-value
is correspondingly anti-conservative, smaller than the defensible one by about seven orders of
magnitude. It is reported here only as a contrast, to show how much apparent precision comes from
counting subsamples as independent replicates.

**The dependence-aware cluster bootstrap is the study's conclusion:** effect −0.0516, 95% CI
[−0.0863, −0.0177], p = 0.0029.

## Interpretation

Soil nitrogen in termite mounds in the burned block averages lower than in the adjacent unburned
block, and the difference survives inference that respects the mound as the unit. The point estimate
is a shortfall of 0.052 percent nitrogen by mass against an unburned average of 0.215 percent.

Three limits are worth stating plainly. First, 7 mounds per block is a small number of independent
units, which is why the confidence interval spans a nearly fivefold range of effect sizes even
though the point estimate is clear. Second, the two blocks are adjacent but not randomised at the
mound level within a single homogeneous area, so any pre-existing difference between the blocks is
confounded with the burn; this analysis compares blocks, and cannot separate the burn from whatever
else distinguishes them. Third, the mound-level spread is substantial in both blocks (SD 0.037 and
0.033, against a between-block difference of 0.052), and the two blocks' mound means overlap, so
individual mounds in the burned block can and do exceed individual mounds in the unburned block.

The available covariates in the file (`mound_height_m`, `core_distance_cm`, `sample_depth_cm`,
`soil_ph`) were not used. The protocol specifies a two-group comparison of `total_nitrogen_pct`
between the levels of `burn_block`, and adding covariates after seeing the data would not be a
pre-specified analysis.

## Reproducing

```
python3 analysis.py
```

Requires `pandas`, `numpy`, and `scipy`. The script reads `termite_mound_soil_nitrogen.csv` from the
same directory and prints every number in this report, including the explicit warning about the
row-level comparison.
