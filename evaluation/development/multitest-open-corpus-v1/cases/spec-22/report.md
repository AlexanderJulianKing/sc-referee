# Vitamin D supplementation in care home residents

Ninety-six residents were randomised to a weekly vitamin D supplement (n = 48) or matching
placebo (n = 48) for six months. Five outcomes were fixed in advance. For each outcome the
script (`analysis.py`) ran the assumption checks first, chose a test from the result, and
then corrected the whole panel of five together with Holm-Bonferroni at a family-wide alpha
of 0.05. Significance is taken only from the adjusted values.

## Assumption checks and test choice

| Outcome | Shapiro-Wilk placebo | Shapiro-Wilk vit D | Levene | Test chosen |
|---|---:|---:|---:|---|
| Serum 25-OH vitamin D | 0.483 | 0.920 | 0.085 | Student t |
| Parathyroid hormone | 0.727 | 0.814 | 0.109 | Student t |
| Grip strength | 0.276 | 0.959 | 0.931 | Student t |
| Timed up-and-go | 0.689 | 0.398 | 0.625 | Student t |
| Falls in six months | 0.0003 | <0.0001 | 0.222 | Mann-Whitney U |

Four outcomes passed both checks and were tested with a Student t-test. Falls is a small
count with a floor at zero, and it failed the normality check in both arms, so it was tested
with Mann-Whitney U. Variances were comparable in every case, though the serum
25-OH vitamin D result is the closest call: the arm SDs differ (15.0 vs 20.0 nmol/L) and
Levene returns p = 0.085, which passes at 0.05 but not by a wide margin.

## Results

| Outcome | Placebo | Vitamin D | Test | Raw p | Holm p |
|---|---:|---:|---|---:|---:|
| Serum 25-OH vitamin D (nmol/L) | 41.0 | 76.0 | Student t | 8.0e-16 | 4.0e-15 |
| Parathyroid hormone (pmol/L) | 6.40 | 5.11 | Student t | 0.0050 | 0.020 |
| Grip strength (kg) | 18.20 | 19.60 | Student t | 0.265 | 0.591 |
| Timed up-and-go (s) | 16.84 | 15.47 | Student t | 0.197 | 0.591 |
| Falls in six months | 1.42 | 1.10 | Mann-Whitney U | 0.247 | 0.591 |

## Conclusions

Two of the five conclusions survive correction. Supplementation raised serum 25-OH vitamin D
by 35 nmol/L, which confirms that the dose and adherence were adequate, and it lowered
parathyroid hormone by 1.29 pmol/L, the expected downstream response to better vitamin D
status.

Nothing functional survives. Grip strength was 1.4 kg higher and timed up-and-go 1.4 s faster
in the supplemented arm, and falls were about 23 percent lower, but all three have adjusted
p-values of 0.59. The differences are in the direction the trial hoped for, yet the study
cannot distinguish them from chance at this size. A trial powered on falls rather than on
biochemistry would be needed to settle the functional question.
