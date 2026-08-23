# Enrichment and stress hormone in shelter cats

## Data description

The data file is `shelter_cat_fgm.csv`. It has one header line and 144 data lines.

**One row is one cat on one morning.** A row holds that morning's faecal sample result plus that
morning's food record. A row is not a cat and it is not a group. Every cat was sampled on six
consecutive mornings, so **each cat appears on six rows** of the file.

Columns, in file order:

| # | Column | Type | What it holds |
| --- | --- | --- | --- |
| 1 | `cat_ref` | text | The cat's shelter intake code, e.g. `A26-1041`. Unique per cat, repeated on that cat's six rows. 24 distinct values. |
| 2 | `husbandry_group` | text | The cat's arm: `enrichment` or `usual_husbandry`. Cats were assigned as whole animals, so this is the same on all six of a cat's rows. |
| 3 | `sample_day` | integer | Which of the six consecutive sampling mornings this row is, 1 to 6. |
| 4 | `food_intake_pct` | number, 1 decimal | Food eaten that morning as a percentage of the ration offered. Range in the file: 40.6 to 100.0. |
| 5 | `fgm_ng_per_g` | number, 1 decimal | The outcome: faecal glucocorticoid metabolite concentration in nanograms per gram of dry faeces. Higher means more stress load. Range in the file: 65.4 to 255.1. |

There are no missing values. Counts: 24 cats (12 enrichment, 12 usual husbandry), 6 mornings each,
144 rows (72 per group).

The 144 rows are **not** 144 independent observations. The independent unit is the cat, because the
cat is what was assigned to a group. The six rows from one cat are repeated measures on the same
animal and are correlated. In these data the between-cat spread is large (per-cat mean FGM runs from
77.0 to 228.9 ng/g) while a cat's own day-to-day wobble is small (median within-cat SD 11.4 ng/g).

## Primary analysis

Because each cat supplies six correlated samples, the inference is dependence-aware. The model is a
linear mixed model fitted by REML:

```
fgm_ng_per_g ~ husbandry_group,  random intercept for each cat (groups = cat_ref)
```

The random intercept gives every cat its own baseline level, so the group comparison is not fooled
by the fact that some cats are simply high-FGM animals throughout.

Fitted on 24 cats and 144 samples, with `usual_husbandry` as the reference level:

| Quantity | Value |
| --- | --- |
| Group contrast, enrichment minus usual husbandry | **-63.25 ng/g** |
| Standard error | 11.22 ng/g |
| 95% confidence interval | -85.25 to -41.25 ng/g |
| z | -5.635 |
| p | 1.75e-08 |
| Model intercept (usual husbandry mean) | 174.41 ng/g |
| Between-cat variance (random intercept) | 722.91 (SD 26.89 ng/g) |
| Residual within-cat variance | 198.22 (SD 14.08 ng/g) |
| Intraclass correlation (ICC) | 0.785 |
| Cats / samples | 24 / 144 |

**Headline result:** cats on the enrichment protocol had FGM concentrations about 63.2 ng/g lower
than cats on usual husbandry (95% CI 41.2 to 85.2 ng/g lower), against a usual-husbandry mean of
174.4 ng/g. That is a drop of roughly 36 percent.

The ICC of 0.785 says that about 79 percent of the variation in FGM sits between cats rather than
between mornings within a cat. Cats are consistently themselves.

As an internal check, collapsing each cat to its own mean and running a two-sample t-test on those
24 independent numbers gives the same estimate (-63.25 ng/g, SE 11.22, t = -5.635, p = 1.17e-05).
That agreement is expected here because the design is balanced, and it confirms the mixed model is
treating the cat as the unit.

## Secondary sensitivity check (not the inferential result)

A plain Welch two-sample t-test on all 144 rows, treating each row as an independent observation:

- mean difference -63.25 ng/g, SE 4.92 ng/g, 95% CI -72.97 to -53.53
- t = -12.864, df 140.5, **p = 1.63e-25**

**Caveat.** This p-value is far too small and must not be read as the study result. The test assumes
144 independent observations, but the study randomised only 24 cats. With six samples per cat and an
ICC of 0.785, the design effect is 1 + (m - 1) x ICC = 4.92, so the 144 rows carry only about 29
rows' worth of independent information, close to the 24 cats actually assigned. Ignoring that
inflates the effective sample size, shrinks the standard error from 11.22 to 4.92 ng/g, and turns a
p of about 1.8e-08 into 1.6e-25. The point estimate is unaffected (both give -63.25 ng/g); only the
uncertainty is wrong. The mixed model above is the inferential result.

## Welfare interpretation

The enrichment protocol was associated with a substantially lower stress-hormone load in these
simulated shelter cats: about 63 ng/g lower FGM, roughly a third below the usual-husbandry level,
with the confidence interval excluding zero by a wide margin. The lower bound of the interval, a
41 ng/g reduction, is still a meaningful drop, so even the cautious reading supports the protocol.
Food intake ran higher in the enrichment group as well (mean 77.0 percent of the ration offered
versus 67.8 percent), which points the same way, though intake was not modelled here and should not
be treated as a tested result.

Two limits are worth stating. First, the data are simulated, so this demonstrates the analysis, not
a real welfare finding. Second, with 12 cats per arm the estimate is based on 24 animals; the
interval is correspondingly wide, and a larger study would be needed to pin down the size of the
benefit.
