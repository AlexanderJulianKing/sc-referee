# Bone-density supplement study: report

## What we did

Thirty post-menopausal women attending our outpatient bone health service completed one of two
twelve-month supplement regimes. Fifteen took combined vitamin D and calcium, and fifteen took
vitamin D alone. At the end of the twelve months each woman had a single lumbar spine scan, and the
radiographer read areal bone mineral density (aBMD, in grams per square centimetre) separately at
four vertebral levels of that one spine: L1, L2, L3 and L4.

That gives 30 women x 4 levels = 120 vertebral-level readings in total.

## Data description

The project holds two CSV files. They describe the same measurements at two different levels of
detail, and they agree with each other numerically.

### File 1: `vertebral_level_readings.csv`

**One row is one vertebral level of one woman's scan** (for example, the L3 reading for BD-07).
There are 120 data rows and a header row. Each woman appears on exactly four rows.

| Column | Type | What it holds |
| --- | --- | --- |
| `patient_ref` | text | Study code of the woman the reading came from, `BD-01` to `BD-30`. Appears 4 times, once per vertebral level. |
| `supplement_regime` | text | The regime that woman took: `vitamin_d_calcium` or `vitamin_d_only`. The same value on all 4 of her rows. |
| `vertebral_level` | text | Which lumbar vertebra was read: `L1`, `L2`, `L3` or `L4`. |
| `bmd_g_per_cm2` | number | Areal bone mineral density at that vertebral level, in g/cm^2, to 3 decimal places. Values in this dataset run from 0.738 to 1.193. |

### File 2: `patient_summary.csv`

**One row is one woman.** There are 30 data rows and a header row, and each woman appears exactly
once. This is the file at the level of the study's independent unit.

| Column | Type | What it holds |
| --- | --- | --- |
| `patient_ref` | text | Study code of the woman, `BD-01` to `BD-30`. Unique in this file. |
| `supplement_regime` | text | The regime she took: `vitamin_d_calcium` or `vitamin_d_only`. |
| `mean_bmd_g_per_cm2` | number | Her mean aBMD across her vertebral levels, in g/cm^2, to 4 decimal places. |
| `n_levels` | integer | How many vertebral-level readings went into that mean. It is 4 for every woman; no scan had an unreadable level. |

`patient_summary.csv` is derived from `vertebral_level_readings.csv`: each woman's
`mean_bmd_g_per_cm2` is the arithmetic mean of her four `bmd_g_per_cm2` values, rounded to 4 decimal
places, and `n_levels` counts those rows. The analysis script re-derives the summary from the level
file and confirms it. Every woman matched across the two files, every `n_levels` value matched the
row count, and the largest gap between a stored mean and a freshly recomputed one was 0.000050
g/cm^2, which is exactly what rounding to 4 decimal places can produce and no more.

## Which file the comparison was run on, and why

The woman is the independent experimental unit here. Each woman was put on one regime as a whole,
and her four readings all come from a single scan of a single spine. Those four readings are four
looks at the same woman, so they are not four independent observations. Treating the 120 readings as
120 independent data points would inflate the sample size roughly fourfold and make the comparison
look far more certain than the study can support.

So the regime comparison was run on `patient_summary.csv` only, where each woman contributes one
number and enters the comparison exactly once. The sample size for the comparison is **30 women, 15
per regime**. The vertebral-level file was used only for descriptive counts and for checking that
the two files agree. No group test was run on it.

## Descriptive results

From the level file (counts and description only, no group test):

- 120 readings, 4 per woman for all 30 women, 60 readings per regime.
- Pooling both regimes, mean aBMD by level was L1 0.9664, L2 0.9703, L3 0.9985 and L4 1.0060 g/cm^2,
  with standard deviations near 0.087 at every level. That rising pattern from L1 to L4 is the usual
  lumbar picture and is not a treatment effect.
- No missing values in either file.

Per-woman mean aBMD, which is what the comparison uses:

| Regime | n women | Mean (g/cm^2) | SD | Min | Max |
| --- | --- | --- | --- | --- | --- |
| `vitamin_d_calcium` | 15 | 1.0117 | 0.0664 | 0.9045 | 1.1020 |
| `vitamin_d_only` | 15 | 0.9589 | 0.0923 | 0.8180 | 1.1695 |

## Comparison of the two regimes

Primary test: Welch two-sample t-test on the 30 per-woman means. Welch was chosen because it does
not assume the two groups share a variance, and the vitamin D only group is visibly more spread out.

- Difference, combined regime minus vitamin D alone: **+0.0528 g/cm^2**
- 95% confidence interval for that difference: **-0.0076 to +0.1132 g/cm^2**
- t = 1.797, df = 25.44, **p = 0.0841**
- Hedges' g = 0.639

Supporting checks, all on the same 30 women:

- Shapiro-Wilk on the per-woman means gave W = 0.906, p = 0.118 for the combined regime and
  W = 0.907, p = 0.122 for vitamin D alone. Neither group shows a departure from normality that this
  sample size can detect.
- Levene's test gave W = 0.097, p = 0.757, so the unequal-variance allowance in Welch's test is a
  precaution rather than a rescue.
- A rank-based Mann-Whitney U test as a sensitivity check gave U = 155.0, p = 0.0815, which agrees
  closely with the t-test.

## What I take from this

Women on the combined vitamin D and calcium regime averaged 0.053 g/cm^2 higher lumbar aBMD than
women on vitamin D alone. That is a difference worth caring about clinically if it is real, and the
standardised effect size of 0.64 is moderate. But at 15 women per arm the result does not reach
statistical significance at the 5% level (p = 0.084), and the confidence interval runs from a small
deficit of 0.008 to a substantial advantage of 0.113 g/cm^2. The data are consistent with a real
benefit of the size we hoped for, and also with no benefit at all.

I would not report this as a demonstrated effect. The point estimate points the way we expected, and
the study is underpowered to settle the question. A larger trial, sized on the per-woman standard
deviation seen here (about 0.08 g/cm^2), is the sensible next step.

One caution for anyone reusing these data. It is tempting to analyse all 120 vertebral-level
readings as though they were 120 independent measurements, which would give a much smaller p-value.
That analysis would be wrong. The extra rows carry information about how one spine varies from L1 to
L4, not about how many women were studied, and the number of women is what the regime comparison
rests on.

## How to reproduce

```
python3 analysis.py
```

`analysis.py` is the only analysis script in the project. It reads both CSVs, prints the descriptive
counts, runs the two-file consistency check, and runs the single regime comparison on the per-woman
file. Every number quoted above comes from its output.
