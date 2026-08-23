# On-farm sugar beet trial: added biological seed coating vs standard treated seed

Regional agronomy report, single season, one growing region.

## Design

Thirty-four commercial sugar beet fields took part, each on a different farm. Seventeen fields
were drilled with seed carrying the standard fungicidal treatment only, and seventeen with seed
carrying the standard fungicidal treatment plus an added biological coating. Whole fields were
allocated to a treatment; nothing was split within a field.

The field is the experimental unit. Each field was drilled with one seed treatment and harvested
whole by the contractor, and its delivered clean root weight was read once off the weighbridge
tickets and divided by the drilled area. Each field therefore contributes exactly one yield
figure and appears exactly once in the data. The sample size is 17 fields on standard seed and
17 fields on the biological coating, 34 fields in all.

## Data description

The analysis reads one committed data file, `sugar_beet_field_yields.csv`: 34 rows plus a header.

**One row is one whole commercial field**, on its own farm, with its single season-end harvest
figure. Rows and fields are one to one. There are no repeat measurements, subsamples or split
plots, and no missing values.

| Column | What it holds |
|---|---|
| `field_id` | Identifier for the field in the regional trial numbering, `SB-101` to `SB-134`. One per farm, unique in the file. |
| `seed_treatment` | The seed treatment that field was drilled with: `standard` or `biological`. |
| `field_area_ha` | Drilled area of the field in hectares. An agronomic covariate recorded for context; 6.0 to 26.6 ha, mean 13.5. |
| `clean_root_yield_t_ha` | The outcome. Delivered clean root yield for the whole field in tonnes per hectare, from the weighbridge tickets. |

## Method

An independent two-sample t-test (Student, pooled variance) on `clean_root_yield_t_ha` between
the two levels of `seed_treatment`, with each field's single harvest figure as one observation.
Because whole fields were allocated and each field was weighed once, the 34 observations are
independent of one another and the two groups contain different fields, which is what this test
assumes. Group means and standard deviations are reported alongside the test. A Welch version,
which does not assume the two groups share a variance, is reported as a robustness check.

## Result

| Seed treatment | Fields | Mean yield (t/ha) | SD (t/ha) | Range (t/ha) |
|---|---|---|---|---|
| standard | 17 | 61.07 | 7.26 | 51.7 to 75.5 |
| biological | 17 | 66.93 | 7.06 | 55.5 to 79.9 |

The biological coating group yielded 5.86 t/ha more on average than the standard group
(95% confidence interval 0.86 to 10.86 t/ha).

Independent two-sample t-test: **t(32) = 2.385, p = 0.023**.

The Welch check gives essentially the same answer (t = 2.385, df = 32.0, p = 0.023), which is no
surprise given how close the two standard deviations are.

## Interpretation for growers

Across these 34 farms the fields drilled with the added biological seed coating delivered about
5.9 t/ha more clean root than the fields on standard treated seed, and a difference that large is
unlikely to be chance alone at the usual 5% threshold. The caution sits in the width of the
interval: the data are consistent with a gain as small as about 0.9 t/ha or as large as about
10.9 t/ha, so one season gives the direction with reasonable confidence but pins the size down
only loosely. Field-to-field spread was large, around 7 t/ha in both groups, which is normal on
farm and reflects soil type, drilling date and rainfall rather than the seed. Growers weighing
the coating should set the low end of that interval against the extra seed cost, and repeat
across a second season before drawing firm conclusions about the size of the benefit.
