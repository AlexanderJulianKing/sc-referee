# Methane flux in intact versus drained peat bogs

## Design

Twelve peat bogs, each in a separate catchment, were surveyed once during a single midsummer
campaign: six bogs with an intact water table and six bogs drained by historic ditching. Every
bog contributes exactly one closed-chamber flux measurement, so each row of data/input.csv is
one independent unit. Rows read: 12; distinct bog identifiers: 12.

## Group summaries

| Hydrology | Bogs | Mean CH4 flux (mg m-2 h-1) | SD (mg m-2 h-1) |
| --- | --- | --- | --- |
| intact | 6 | 3.200 | 0.228 |
| drained | 6 | 2.700 | 0.313 |

## Test

Two-sided two-sample Student t-test with pooled variance on the bog-level flux values. No bog
is measured twice, so the twelve observations enter the test as twelve independent draws.

- Difference in means (intact minus drained): 0.500 mg m-2 h-1
- Pooled SD: 0.274 mg m-2 h-1
- Standardised effect size (difference / pooled SD): 1.826
- t(10) = 3.1623, p = 0.01012

[selected-result] Intact bogs emitted more methane than drained bogs: mean flux 3.200 vs 2.700 mg m-2 h-1 (difference 0.500), pooled two-sample t-test t(10) = 3.1623, two-sided p = 0.01012, standardised effect size 1.826.

## Reading the result

At the conventional 5 percent level the difference is statistically significant: in this sample
the drained bogs emit about 16 percent less methane than the intact bogs. The test assumes
independent, approximately normal, equal-variance groups. Independence holds by construction
because every bog identifier appears on exactly one row; normality and equal variance are
assumed rather than demonstrated at six bogs per group.
