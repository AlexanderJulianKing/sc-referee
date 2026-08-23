# Carapace length of green turtle hatchlings under two hatchery incubation substrates

## Question

A nesting beach monitoring programme relocated 24 green turtle clutches into a protected hatchery,
12 into native beach sand and 12 into a coarser imported sand used where the natural beach profile
has eroded. The question is whether straight carapace length at emergence differs between the two
incubation substrates.

## Data

One file, `hatchling_carapace.csv`, holding 240 data rows plus a header.

**One row is one measured green turtle hatchling**, recorded before release, labelled by the clutch
it emerged from and by its measurement number within that clutch.

| # | Column | Type | Values | Meaning |
| --- | --- | --- | --- | --- |
| 1 | `clutch_ref` | text | `CL-01` … `CL-24` | Identifier of the relocated clutch the hatchling came from. Repeats on 10 rows. |
| 2 | `substrate` | text | `native`, `imported` | Incubation substrate the clutch was relocated into. Constant within a clutch. |
| 3 | `hatchling_number` | integer | 1 … 10 | Index of the hatchling within its clutch. A label only, not a time order or a size rank. |
| 4 | `carapace_length_mm` | number, 1 decimal | 36.4 … 48.5 in this file | Straight carapace length in millimetres. The outcome. |

Counts: 24 clutches, 12 per substrate, 10 measured hatchlings per clutch, 240 hatchlings in total.
There are no missing values, and every clutch has exactly ten rows numbered 1 to 10.

Substrate was assigned to whole clutches, so the clutch is the independent experimental unit. The
ten rows inside a clutch are siblings from one mother's single clutch, sharing an egg chamber and a
thermal history. Those ten rows are not ten independent draws.

The data are simulated rather than field records. `make_data.py` generates them from a fixed seed
using a two-level structure: each clutch gets its own mean drawn around its substrate mean, and each
hatchling is drawn around its own clutch mean.

## Analysis

**Primary procedure.** A linear mixed-effects model fitted with statsmodels (`MixedLM`, REML):

```
carapace_length_mm ~ substrate + (1 | clutch_ref)
```

The model gives every clutch its own random intercept. That random intercept is what respects the
dependence: instead of pretending the ten siblings are ten separate pieces of evidence, the model
splits the variation into a clutch-to-clutch part and a within-clutch part, and judges the substrate
difference against the clutch-to-clutch part. Substrate enters as a fixed effect at the clutch
level, so the reported coefficient is the difference in mean carapace length between the two
substrates, native minus imported. Think of it as comparing 24 clutch averages rather than 240
tape-measure readings, while still using every reading to pin down where each clutch average sits.

**Supporting check.** A cluster bootstrap, run as a second, independent route to the same interval.
The unit resampled is the whole clutch, never the individual hatchling: within each substrate arm,
12 clutch labels are drawn with replacement from that arm's 12 clutches, and all ten hatchling rows
of a drawn clutch travel with it, so sibling dependence is carried into every resample. In each of
20,000 resamples the difference in mean carapace length (native minus imported) is recomputed over
the resampled rows. The 2.5th and 97.5th percentiles of that distribution give the interval, and the
two-sided p-value is twice the smaller tail mass on the far side of zero.

**Illustrative contrast, not inference.** A plain independent two-sample t-test (Student's, equal
variance) over the 240 raw hatchling rows.

## Results

Mean carapace length by substrate, over the raw hatchling rows:

| Substrate | Clutches | Hatchlings | Mean (mm) | SD (mm) |
| --- | --- | --- | --- | --- |
| native | 12 | 120 | 43.66 | 1.85 |
| imported | 12 | 120 | 40.97 | 2.58 |

The two substrate means differ by 2.69 mm, with native sand higher.

### Primary result: mixed-effects model with a random intercept for clutch

| Quantity | Value |
| --- | --- |
| Effect, native minus imported | +2.69 mm |
| Standard error | 0.80 mm |
| 95% confidence interval | +1.11 to +4.26 mm |
| p-value | 0.00081 |
| Between-clutch SD | 1.93 mm |
| Within-clutch SD | 1.27 mm |
| Intraclass correlation | 0.70 |

Based on 24 clutches and 240 hatchlings.

The intraclass correlation of 0.70 is the reason the clutch structure cannot be ignored: about 70
percent of the variation in carapace length sits between clutches rather than between siblings
inside a clutch. Measuring a tenth hatchling from a clutch already measured nine times adds very
little new information about that clutch.

The p-value and interval above come from a Wald test using a normal reference distribution, which is
mildly optimistic with only 24 clusters. The cluster bootstrap below is reported because it does not
lean on that approximation.

### Supporting cluster bootstrap (20,000 resamples of whole clutches)

| Quantity | Value |
| --- | --- |
| Observed difference, native minus imported | +2.69 mm |
| Bootstrap standard error | 0.78 mm |
| 95% percentile interval | +1.12 to +4.13 mm |
| Two-sided p-value | 0.0012 |

The two clutch-aware routes agree closely, which is what should happen when the balanced design and
the model assumptions are both reasonable.

### Illustrative contrast: naive hatchling-level t-test

**This comparison is not a valid basis for inference in this study.** It treats the ten siblings
within a clutch as ten independent replicates. They are not independent: they share a mother, an egg
chamber and a thermal history, and substrate was assigned to the clutch, not to the hatchling. The
test therefore claims 240 independent units when the design delivered 24, and it borrows precision
the study never had.

| Quantity | Value |
| --- | --- |
| Difference, native minus imported | +2.69 mm |
| Standard error | 0.29 mm |
| 95% confidence interval | +2.12 to +3.26 mm |
| Test statistic | t(238) = 9.28 |
| p-value | 1.1 x 10^-17 |

The point estimate is identical, because the design is balanced. Only the uncertainty changes, and
it changes a great deal. The naive interval is 1.14 mm wide against 3.15 mm for the mixed model, so
the valid interval is 2.8 times wider, and the naive p-value is roughly fourteen orders of magnitude
smaller. The conclusion of this study rests on the clutch-aware procedure alone; the hatchling-level
numbers are shown only to make the size of that inflation visible.

## Conclusion

Green turtle hatchlings incubated in native beach sand emerged with longer straight carapaces than
hatchlings incubated in the coarser imported sand. The estimated difference is 2.69 mm (95% CI 1.11
to 4.26 mm, p = 0.0008) from a mixed-effects model with a random intercept for clutch, across 24
clutches and 240 hatchlings, and a cluster bootstrap over whole clutches gives the same answer (95%
CI 1.12 to 4.13 mm, p = 0.0012). The interval is wide because the study has 24 independent units,
not 240, and because clutches differ a lot from one another.

Two limits are worth stating. The comparison covers only these 24 relocated clutches in one
hatchery, so it says nothing about other beaches or seasons. And the analysis measures the substrate
difference at emergence only; carapace length at release is not by itself a measure of survival
after the hatchlings enter the water.

## Reproducing

```
python3 analysis.py
```

The script reads `hatchling_carapace.csv`, checks the file structure, prints the summaries, fits the
mixed-effects model, runs the cluster bootstrap with a fixed seed (20260822), and prints the naive
contrast last under an explicit warning label. All numbers in this report come from that run.
