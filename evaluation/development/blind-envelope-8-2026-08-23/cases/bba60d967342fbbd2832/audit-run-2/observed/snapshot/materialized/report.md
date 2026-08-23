# Biochar amendment and earthworm body mass in contaminated soil

## Summary

Earthworms held for eight weeks in biochar-amended contaminated soil weighed 488.16 mg on
average, against 427.62 mg for worms held in the same soil without the amendment. The
difference of 60.54 mg is highly significant (independent two-sample t-test, t = 5.183,
df = 118, p = 9.13e-07, n = 120 worms).

## Data description

### File

`earthworm_body_mass.csv`, at the project root. 120 data rows plus a header row.

### What one row represents

**One row is one individual earthworm that was removed from a soil mesocosm at week 8 and
weighed.** The row carries that worm's body mass and gut-cleared status, together with the
identity, treatment and sampling-day soil moisture of the mesocosm it came from. Ten worms
were weighed per mesocosm and twelve mesocosms were run, giving 120 rows.

### Columns

The file has six columns, in this order.

| Column | Type | Units | Description |
|---|---|---|---|
| `mesocosm_id` | text | — | Identifier of the soil mesocosm the worm came from. Twelve values, `MES01` through `MES12`. |
| `treatment` | text | — | Amendment applied to that mesocosm: `biochar` or `control`. |
| `worm_id` | text | — | Unique identifier for the weighed worm, formed as `<mesocosm_id>-W<nn>` with `nn` running 01-10 (for example `MES03-W07`). All 120 values are distinct. |
| `body_mass_mg` | number | milligrams (mg) | Body mass of that worm at week 8, recorded to 0.1 mg. Observed range 320.7 to 598.3 mg. |
| `gut_cleared` | text | — | Whether the worm was gut-cleared before weighing: `yes` or `no`. 109 rows `yes`, 11 rows `no`. |
| `soil_moisture_pct` | number | percent (%) | Gravimetric soil moisture recorded for that worm's mesocosm on the sampling day, to 0.1 %. Observed range 23.6 to 28.6 %, mean 25.99 %. |

There are no missing values in any column.

### Groups

| Group | Meaning | Mesocosms | Worms weighed |
|---|---|---|---|
| `biochar` | Contaminated soil with a biochar amendment | 6 (MES02, MES04, MES06, MES07, MES11, MES12) | 60 |
| `control` | The same contaminated soil, unamended | 6 (MES01, MES03, MES05, MES08, MES09, MES10) | 60 |

Mesocosms were allocated to the two groups at random, so the treatment labels do not follow
the mesocosm numbering order.

## Methods

Twelve soil mesocosms were prepared from the same contaminated soil. Six received a biochar
amendment and six were left unamended. Each mesocosm was stocked with earthworms and held for
eight weeks, after which ten worms were removed from each mesocosm and weighed individually to
0.1 mg. Soil moisture was recorded for each mesocosm on the sampling day.

Body mass was compared between the two treatments with an **independent two-sample t-test**
assuming equal variances (Student's t). Every weighed worm entered the test as one observation,
so the sample size for the comparison is the 120 rows of the data file: 60 worms in the biochar
group and 60 in the control group. Alongside the test we report each group's mean, standard
deviation and standard error, the difference in means with its 95 % confidence interval, and
Cohen's *d* computed on the pooled standard deviation. The significance threshold was
alpha = 0.05, two-sided.

The analysis is implemented in `analysis.py` (Python 3, pandas 2.0.3, SciPy 1.9.1) and runs
end to end from the CSV with `python3 analysis.py`. `gut_cleared` and `soil_moisture_pct` are
reported descriptively and are not used as covariates.

## Results

### Group summary of body mass

| Group | n (worms) | Mean (mg) | SD (mg) | SEM (mg) | Range (mg) |
|---|---|---|---|---|---|
| biochar | 60 | 488.16 | 54.85 | 7.08 | 347.1 - 598.0 |
| control | 60 | 427.62 | 71.95 | 9.29 | 320.7 - 598.3 |

### Test of the treatment effect

| Quantity | Value |
|---|---|
| Sample size entering the test | 120 worms |
| Mean difference (biochar - control) | 60.54 mg |
| 95 % confidence interval for the difference | 37.41 to 83.67 mg |
| Pooled SD | 63.98 mg |
| t | 5.1831 |
| Degrees of freedom | 118 |
| p-value | 9.13 x 10^-7 |
| Cohen's *d* | 0.946 |

The null hypothesis of equal mean body mass is rejected at alpha = 0.05.

### Supporting descriptives

Gut-cleared status was `yes` for 109 of the 120 weighed worms and `no` for the remaining 11.
Sampling-day soil moisture ranged from 23.6 % to 28.6 % with a mean of 25.99 %, comfortably
inside the range these assays are run at, so moisture was not a limiting factor in either arm.

## Interpretation

Biochar amendment raised earthworm body mass by 60.54 mg, a 14.2 % increase over the control
mean of 427.62 mg. The effect is large by the usual conventions (Cohen's *d* = 0.95, close to
one pooled standard deviation) and the confidence interval excludes zero by a wide margin: even
the lower bound of 37.41 mg is an 8.8 % gain. The p-value of 9.13 x 10^-7 leaves no doubt that
the two groups differ.

Body mass at week 8 is a standard condition endpoint in these assays, so the result reads as a
clear improvement in earthworm condition when biochar is added to this contaminated soil. The
direction matches the expected mechanism: biochar sorbs organic and metallic contaminants,
lowering the fraction that is bioavailable to soil fauna, which shows up as better growth over
an eight-week exposure. Worms in both arms spanned a similar upper range (maxima of 598.0 and
598.3 mg), so the amendment appears to lift the bulk of the distribution rather than to create
a few unusually large individuals; the control group's larger spread (SD 71.95 mg against
54.85 mg) is consistent with more variable performance under unrelieved contaminant pressure.

Practical read for colleagues running this assay: at these dose and exposure settings biochar
delivers a body-mass benefit worth roughly 60 mg per adult worm, and the effect is strong
enough to be picked up without a large assay. Sensible follow-ups are a dose-response series
across biochar application rates, a longer exposure to see whether the gain holds or widens,
and paired contaminant measurements in tissue and pore water to confirm reduced bioavailability
as the mechanism behind the growth response.
