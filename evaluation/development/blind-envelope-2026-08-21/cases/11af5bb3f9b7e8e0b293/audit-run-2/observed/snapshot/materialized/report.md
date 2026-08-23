# Warming and calcification in *Acropora millepora*: results from the 8-week nubbin trial

## Data description

All numbers below come from `nubbin_calcification.csv`, which holds 70 data rows plus a header.

**One row is one nubbin.** A nubbin is a single fragment cut from a wild parent colony, held for
eight weeks under that colony's assigned thermal regime, and weighed by buoyant weight at the start
and at the end. A row is a measured fragment, not a colony and not a tank. Five rows share each
parent colony, because five nubbins were cut from every colony, and those five fragments are clones
of one another. Rows carrying the same `parent_colony` label are therefore not independent
observations of the treatment.

The file has five columns:

| Column | What it holds |
|---|---|
| `parent_colony` | Label of the wild colony the nubbin was cut from, `COL-A` through `COL-N`. Fourteen distinct labels, each appearing in exactly 5 rows. This is the shared-genotype grouping variable. |
| `thermal_regime` | The temperature the nubbin experienced: `ambient` (27 degrees C) or `heated` (29 degrees C). Constant within a parent colony, because the regime was assigned to whole colonies. |
| `nubbin_code` | The nubbin's identifier inside its own colony, `n1` through `n5`. It repeats across colonies, so a fragment is identified only by the pair (`parent_colony`, `nubbin_code`). |
| `initial_weight_g` | Buoyant weight of the nubbin in grams at the start of the run, to 2 decimals. Observed range 4.50 to 11.96 g. |
| `calcification_rate` | The outcome: net calcification over the eight weeks, in mg CaCO3 per gram of skeleton per day, to 3 decimals. Observed range 0.504 to 1.453. |

Rows are ordered colony by colony, COL-A through COL-N, and within a colony by nubbin code.

## Design and the unit of replication

We collected 14 wild parent colonies of *Acropora millepora* and assigned each colony as a whole to
one of two thermal regimes: 7 colonies to ambient seawater at 27 degrees C, and 7 colonies to a
sustained +2 degree treatment at 29 degrees C. From each colony we cut 5 nubbins, and all five
experienced whatever regime their parent had been assigned. After eight weeks we measured
calcification on all 70 nubbins by buoyant weight.

The randomisation happened at the colony level, so the parent colony is the independent
experimental unit and **the study's sample size is N = 14 colonies, 7 per group.** The 70 nubbins
are repeated measures within those 14 units. This distinction matters a great deal in this dataset:
the fitted between-colony variance in calcification rate (0.0633) is more than thirteen times the
within-colony residual variance (0.0047). Genotype, not thermal regime, is the dominant source of
spread here, and five clonal fragments from one colony tell us very little more about the treatment
effect than one fragment would.

Descriptively, the ambient nubbins averaged 0.931 mg CaCO3 g^-1 day^-1 (SD 0.304, 35 nubbins) and
the heated nubbins averaged 0.745 (SD 0.169, 35 nubbins).

## Primary inferential result: linear mixed-effects model

Our inferential analysis is a linear mixed-effects model fitted by REML in statsmodels, predicting
`calcification_rate` from `thermal_regime` with a random intercept for `parent_colony`. All 70
nubbin rows enter the model, grouped into the 14 parent colonies (5 observations per group). The
random intercept absorbs each genotype's own baseline, so the treatment contrast is judged against
variation among colonies rather than against the much smaller variation among clone-mates.

The heated regime was associated with a change of **-0.186 mg CaCO3 g^-1 day^-1** relative to
ambient (SE 0.135, z = -1.37, **p = 0.170**, 95% CI -0.451 to 0.080). The point estimate is a
reduction of about 20 percent of the ambient mean, which is biologically the direction we expected,
but the interval comfortably includes zero. With 14 colonies and this much genotypic spread, the
experiment simply does not resolve an effect of this size. We do not claim that warming reduced
calcification in this trial.

## Supporting check: colony-level t-test

As a check that the conclusion is not an artefact of the mixed-model machinery, we collapsed each
parent colony to its own mean calcification rate and compared the resulting 14 numbers with a
two-sample t-test, **7 ambient colony means against 7 heated colony means**. One value per
independent unit, so the degrees of freedom are the ones the design actually earned.

The ambient colonies averaged 0.931 (SD 0.317, n = 7 colonies) and the heated colonies averaged
0.745 (SD 0.167, n = 7 colonies), a difference of -0.186. The test gives t = -1.37 on 12 degrees of
freedom, **p = 0.195**. This agrees closely with the mixed model, which is what one expects with a
balanced design and five nubbins in every colony, and it supports the same conclusion.

## Sensitivity illustration only: the 70-row t-test

For completeness we also ran a two-sample t-test across all 70 individual nubbin rows, 35 against
35, as though each fragment were an independent observation. That test returns t = -3.16 on 68
degrees of freedom, p = 0.0024.

**This is a sensitivity illustration and is not a result of this study.** It is reported only to
show how far the analysis moves when the shared-genotype structure is ignored. The five nubbins in a
colony are clones and the thermal regime was never assigned at the nubbin level, so this test claims
68 degrees of freedom where the design provides 12. That is pseudoreplication: it treats repeated
measurement of the same 14 experimental units as if it were 70 units, and the resulting p-value is
anticonservative by a factor of about 70 to 80 relative to the two honest analyses. No conclusion
in this report rests on it, and the figure should not be cited as evidence of a warming effect.

## Which N belongs to which analysis

| Analysis | Data that entered it | N | Status |
|---|---|---|---|
| Mixed-effects model (primary) | 70 nubbin rows, grouped into 14 parent colonies | 14 independent units, 70 measurements | Inferential result: -0.186, SE 0.135, p = 0.170 |
| Colony-mean t-test (support) | 14 colony means, 7 per regime | 7 per group, 12 df | Confirmatory: t = -1.37, p = 0.195 |
| Row-wise t-test (sensitivity) | 70 nubbin rows treated as independent | 35 per group, 68 df (unearned) | Illustration only: p = 0.0024, not a basis for any conclusion |

**The sample size of this study is 14 parent colonies, 7 per thermal regime.**

## Conclusion

Over eight weeks at +2 degrees C, mean net calcification in *A. millepora* was about 0.19 mg CaCO3
g^-1 day^-1 lower than at ambient, but neither the mixed-effects model (p = 0.170) nor the
colony-level t-test (p = 0.195) separates that difference from zero at the 14-colony scale of this
experiment. Genotype dominated the variation in calcification, and a trial with more parent
colonies, rather than more fragments per colony, would be needed to resolve an effect of this
magnitude.

## Reproducing these numbers

`analysis.py` reads `nubbin_calcification.csv` and prints all three analyses in the order given
above. Every number in this report is taken from that script's output.
