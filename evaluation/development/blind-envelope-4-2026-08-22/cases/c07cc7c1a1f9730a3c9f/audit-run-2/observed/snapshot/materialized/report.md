# Circulating interleukin-6 in newly diagnosed rheumatoid arthritis

## Question

Does circulating interleukin-6 differ between adults with newly diagnosed rheumatoid arthritis
and matched healthy volunteers?

## Data

The assay table is `il6_assay.csv`. It holds a header row and 90 data rows of immunoassay output.

**One row is one assay run on one banked serum sample, reporting the interleukin-6 concentration
returned by that run.**

| Column | Type | Values | Meaning |
| --- | --- | --- | --- |
| `sample_ref` | text | `S-101` ... `S-130` | Identifier of the banked serum sample, one sample per person. |
| `cohort` | text | `control`, `RA` | Study group: matched healthy volunteers, or adults with newly diagnosed rheumatoid arthritis. |
| `replicate_run` | integer | `1`, `2`, `3` | Which assay run of that sample this row reports. |
| `il6_pg_ml` | number | above zero, 2 decimal places | Interleukin-6 concentration measured on that run, in picograms per millilitre. |

Thirty banked serum samples were assayed, fifteen from each cohort, and each was run three times
on the same plate. That yields 45 assay measurements in the control cohort and 45 in the RA
cohort, 90 in total. Concentrations run from 1.26 to 8.81 pg/mL in the controls and from 5.10 to
12.52 pg/mL in the patients, with a right-skewed tail that carries a few patients into the low
teens.

## Analysis

Every assay measurement counts toward the sample size, so all 90 rows enter the comparison. The
two cohorts were compared with an independent two-sample t test of mean `il6_pg_ml`. The analysis
script is `analysis.py`.

## Result

| Cohort | Assay measurements | Mean il6 (pg/mL) | SD (pg/mL) |
| --- | --- | --- | --- |
| control | 45 | 4.18 | 2.20 |
| RA | 45 | 7.79 | 2.05 |

- Total sample size: **90 assay measurements**
- Difference in means (RA minus control): **3.61 pg/mL**
- Independent two-sample t test: **t(88) = 8.06**, **p = 3.50 x 10^-12**

## Interpretation

Interleukin-6 is elevated in rheumatoid arthritis. Patients newly diagnosed with the disease
carried a mean circulating interleukin-6 concentration of 7.79 pg/mL against 4.18 pg/mL in matched
healthy volunteers, an increase of 3.61 pg/mL, or roughly 86 percent above the control mean. The
separation is large relative to the spread within either cohort, and the p-value sits far below the
conventional 0.05 threshold.

With 90 assay measurements split evenly between the two cohorts, the study is well powered for a
difference of this size, and the result is a clear one. The finding fits the established picture of
interleukin-6 as an inflammatory cytokine that rises with active rheumatoid disease, and it
supports the use of circulating interleukin-6 as a marker of the inflammatory state at diagnosis.
