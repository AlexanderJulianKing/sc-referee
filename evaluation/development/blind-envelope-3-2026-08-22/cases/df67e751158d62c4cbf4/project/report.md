# Dietary calcium source and eggshell thickness in laying hens

## Data description

The analysis uses a single comma-separated file, `eggshell_quality.csv`, holding 216 data rows plus a
header row. There are no missing values.

**A single row is one sampled hen and the one freshly laid egg measured from her**, so each row
carries one shell-thickness reading and one egg-weight reading for that bird.

| Column | Type | Units | Description |
|---|---|---|---|
| `pen_id` | text | — | Identifier of the floor pen the hen was housed in. Values `P01`–`P18`, 12 rows each. |
| `diet` | text | — | Calcium source fed to that pen. Two values: `limestone`, `oyster_shell`. |
| `hen_id` | text | — | Identifier of the sampled hen, formatted `Pnn-Hkk` with `Hkk` running `H01`–`H12`. 216 distinct values, one per row. |
| `shell_thickness_mm` | number | millimetres | Shell thickness of the measured egg. Observed range 0.3143 to 0.4200. |
| `egg_weight_g` | number | grams | Weight of the same measured egg. Observed range 53.11 to 71.85. |

## Housing and diets

The trial was run in one laying house holding eighteen floor pens, each stocked with about forty
hens. Nine pens were fed a diet in which the supplemental calcium was supplied as limestone and nine
pens were fed a diet in which it was supplied as oyster shell. The two diets were otherwise the same,
and each pen stayed on its assigned calcium source for the whole trial. Pens `P01` through `P09`
received the limestone diet and pens `P10` through `P18` received the oyster-shell diet.

At the end of the trial, twelve hens were caught at random from each pen. One freshly laid egg from
each sampled hen was collected, and its shell thickness and weight were recorded. That gives 12 hens
per pen, 108 measured eggs per diet, and 216 measured eggs in total. The design is balanced: every
pen contributed exactly twelve eggs.

## Methods

Shell thickness was compared between the two calcium sources with an independent two-sample t-test
assuming equal variances. Each measured egg contributed one observation to the test, so the analysis
was carried out on 216 observations, 108 per diet. Group means, standard deviations and standard
errors were computed on the same per-egg basis. Egg weight was summarised by diet for description.
All computation was done in `analysis.py` using pandas 2.0.3 and SciPy 1.9.1 under Python 3.9, and
the two-sample test used `scipy.stats.ttest_ind` with `equal_var=True`. Significance was judged at
the conventional 5 percent level.

## Results

Shell thickness by dietary calcium source:

| Diet | Eggs measured | Mean (mm) | SD (mm) | SEM (mm) |
|---|---|---|---|---|
| limestone | 108 | 0.3529 | 0.0207 | 0.0020 |
| oyster_shell | 108 | 0.3707 | 0.0213 | 0.0020 |

Eggs from hens on the oyster-shell diet had thicker shells than eggs from hens on the limestone diet.
The difference in means was +0.0178 mm in favour of the oyster-shell source, which is a 5.0 percent
increase over the limestone mean. The independent two-sample t-test on the full set of measured eggs
gave t = 6.224 on 214 degrees of freedom, p = 2.53e-09, with a total sample size of n = 216 measured
eggs (108 per diet). The difference is significant at the 5 percent level and well beyond it.

Egg weight was similar on the two diets, averaging 61.40 g (SD 3.29) on limestone and 62.12 g
(SD 2.80) on oyster shell, so the shell-thickness advantage was not accompanied by any large shift in
egg size.

## Conclusion

Feeding oyster shell rather than limestone as the supplemental calcium source improved eggshell
thickness in this house. Shells averaged 0.0178 mm thicker on the oyster-shell diet, a 5.0 percent
gain, and the effect was highly significant (t = 6.224, df = 214, p = 2.53e-09, n = 216 measured
eggs). Egg weight was essentially unchanged, so the benefit shows up as shell quality rather than egg
size. On this evidence, oyster shell is the preferable calcium source for shell thickness in laying
hen diets of this type.
