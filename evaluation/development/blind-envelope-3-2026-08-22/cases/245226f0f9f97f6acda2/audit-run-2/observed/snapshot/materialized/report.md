# Effect of a candidate compound on tumour growth in tumour-bearing rats

## 1. Data description

The single data file is `tumour_volumes.csv`. It holds 120 data rows and one header row, in
comma-separated form, with no missing cells. The values are simulated by `make_data.py` under a fixed
seed. No value came from a live animal.

**One row is one calliper measurement of one animal on one week.** It carries that animal's tumour
volume and body weight for that week, together with the labels identifying the animal, its treatment
group, and its cage. Each of the 24 animals supplies five rows, one per week, so 24 x 5 = 120 rows.

The file has six columns, in this order.

| Column | Type | Description |
| --- | --- | --- |
| `animal_id` | text | Identifier of the animal, which is the experimental unit. `V01` to `V12` for vehicle animals, `T01` to `T12` for treated animals. All 24 values are distinct, and each appears in exactly 5 rows. This column groups the repeated measurements. |
| `treatment_group` | text | The arm the animal was in, `vehicle` or `treated`. Constant within an animal. 60 rows carry each value. |
| `week` | integer | Measurement occasion, 1 to 5, one row per animal per week. Week 1 is the first occasion, week 5 the last. |
| `tumour_volume_mm3` | number | Tumour volume by calliper in cubic millimetres, rounded to one decimal. This is the outcome. Observed range 72.2 to 1208.2. |
| `body_weight_g` | number | Body weight that week in grams, rounded to one decimal. Observed range 257.7 to 309.4. Recorded as a general health and tolerability check, not as an outcome. |
| `cage` | text | Cage the animal was housed in, `cage_01` to `cage_12`. Constant within an animal. Two animals share each cage. |

Column headers are lowercase words joined by underscores.

## 2. The experiment

Twenty-four tumour-bearing rats were studied. Twelve received the candidate compound and twelve
received the vehicle alone. Treatment was assigned at the level of the animal, and each animal
remained in its assigned arm for the whole study. Each animal's tumour was measured by calliper once
a week for five consecutive weeks, with no dropout, so all 24 animals contributed complete
five-measurement series.

Animals were housed two to a cage, in 12 cages. Cages never mixed arms: `cage_01` through `cage_06`
held vehicle animals and `cage_07` through `cage_12` held treated animals. Cage is therefore nested
within treatment group and the two cannot be separated in this design.

Observed group means for tumour volume, in cubic millimetres:

| Week | Vehicle | Treated | Treated minus vehicle |
| --- | --- | --- | --- |
| 1 | 187.8 | 179.8 | -8.0 |
| 2 | 330.9 | 300.9 | -30.0 |
| 3 | 509.0 | 392.3 | -116.7 |
| 4 | 706.0 | 533.3 | -172.8 |
| 5 | 899.6 | 610.5 | -289.1 |

The two arms started at practically the same tumour size and separated steadily thereafter. Mean body
weight was 283.6 g in the vehicle arm and 277.4 g in the treated arm, with a standard deviation near
12.6 g in both, giving no signal of poor tolerability.

## 3. Primary analysis and why it is dependence-aware

The five measurements taken on one animal are not five independent observations. They share whatever
makes that animal's tumour large or small overall: its individual baseline burden and its individual
growth rate. Treating the 120 rows as 120 independent observations would understate the standard
error of the treatment effect and inflate the apparent precision of the study, because the effective
amount of independent information is set by the 24 animals, not by the 120 rows.

The primary analysis is therefore a linear mixed-effects model with a random intercept for each
animal:

```
tumour_volume_mm3 ~ treatment_group + week,  random intercept by animal_id
```

The random intercept is a per-animal offset that the model estimates alongside the fixed effects. It
lets each animal sit systematically above or below the common growth line, which is what induces the
correlation between that animal's five measurements. Once that correlation is in the model, the
standard error of the treatment coefficient reflects the 24 animals that were actually randomised.

The model was fitted by restricted maximum likelihood (REML) in `statsmodels` 0.14.1, with `vehicle`
as the reference level so the treatment coefficient reads as treated minus vehicle. The fit
converged. The reported sample size is **24 animals contributing 120 measurements**.

### Primary result

| Quantity | Value |
| --- | --- |
| Treatment effect, treated minus vehicle | **-123.31 mm3** |
| Standard error | 27.99 mm3 |
| 95% confidence interval | -178.16 to -68.45 mm3 |
| z statistic | -4.406 |
| **p-value** | **1.05e-05** |
| Week coefficient | 144.63 mm3 per week (p = 1.37e-121) |
| Between-animal variance | 2873.4 mm3^2 (SD 53.6 mm3) |
| Residual variance | 9130.9 mm3^2 (SD 95.6 mm3) |
| Intraclass correlation | 0.239 |

The study's inferential conclusion is this coefficient and this p-value. Averaged over the five
weeks, tumours in treated animals were about 123 mm3 smaller than in vehicle animals, and the
evidence against no difference is strong (p = 1.05e-05).

The intraclass correlation of 0.239 says that roughly a quarter of the leftover variation in tumour
volume, after accounting for group and week, sits between animals rather than within them. That is
the dependence the model is there to handle.

### Caveats on the primary model

Three features of this model should be read alongside the estimate.

First, the model assumes one common growth slope for both arms and a treatment effect that is a
constant offset in mm3 at every week. The observed group difference is not constant: it is -8.0 mm3
at week 1 and -289.1 mm3 at week 5. The -123.31 mm3 coefficient is best read as an average shift
across the five weeks, not as the effect at any one week. A model with a group-by-week interaction, or
one with a per-animal random slope, would describe the widening separation more faithfully. That
model was not the pre-specified primary analysis and is not substituted here.

Second, because the growth curves diverge and the fitted model holds the slopes parallel, part of that
divergence lands in the residual term. The residual SD of 95.6 mm3 is accordingly larger than the
measurement-to-measurement variation the design intended, and the between-animal SD of 53.6 mm3
captures only the intercept-scale share of the animal-level variation.

Third, cage is completely confounded with treatment group, so no cage effect can be estimated and any
cage-level influence cannot be separated from the treatment effect.

## 4. Secondary sensitivity check, not the inferential result

As a supporting check only, the final-week volumes were compared between arms with a plain two-sample
Welch t-test, treating the rows as independent.

| Quantity | Value |
| --- | --- |
| Week analysed | 5, final week only |
| Rows used | 24 (12 vehicle, 12 treated) |
| Vehicle mean (SD) | 899.6 (123.8) mm3 |
| Treated mean (SD) | 610.5 (154.1) mm3 |
| Difference, treated minus vehicle | -289.06 mm3 |
| Welch 95% confidence interval | -407.69 to -170.43 mm3 |
| Welch t statistic | -5.067 (df 21.02) |
| p-value | 5.10e-05 |

**This is a sensitivity analysis, not the study's conclusion.** It points the same way as the primary
model, which is reassuring, but it answers a narrower question. It uses only the 24 week-5 rows and
discards weeks 1 to 4, so it says nothing about the growth trajectory, and its larger point estimate
of -289.06 mm3 is not in conflict with the primary -123.31 mm3: the first is the gap at the last time
point and the second is the average gap over all five.

One point of housekeeping: because this check uses exactly one row per animal, the rows it treats as
independent are in fact independent, so it does not commit the pseudoreplication error that a t-test
on all 120 rows would. Its limitation is the discarded data and the missing time structure, not a
broken independence assumption.

## 5. Conclusion

In this simulated preclinical experiment, the candidate compound was associated with smaller tumour
volumes than vehicle. The dependence-aware primary analysis, a random-intercept mixed model on 24
animals contributing 120 measurements, estimates the treated minus vehicle difference at -123.31 mm3
(95% CI -178.16 to -68.45, p = 1.05e-05). The final-week two-sample check agrees in direction and
significance and is offered as support only. The estimate should be read as an average across weeks
1 to 5, and a study intending to quantify the widening separation over time would need a model that
allows the two arms to differ in slope.

## 6. Reproducing these numbers

```
/usr/local/bin/python3 analysis.py
```

run from the project folder. The script reads `tumour_volumes.csv`, prints the design summary, then
the primary mixed model clearly labelled as the inferential result, then the secondary final-week
check clearly labelled as a sensitivity analysis. All figures in this report are taken from that
output. Environment: Python 3.9 with pandas 2.0.3, scipy 1.9.1, statsmodels 0.14.1.
