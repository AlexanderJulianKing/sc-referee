# Cover-class composition of restored foredunes, 2024 shoreline survey

## Data

- Source file: `data/input.csv`
- Independent units: 100 restoration sites, one row per site (site identifiers verified unique).
- Response: `cover_class`, one end-of-season classification per site.

## Observed versus reference composition

| Cover class | Sites | Observed share | Reference share | Expected sites | Chi-square contribution |
| --- | --- | --- | --- | --- | --- |
| sparse | 48 | 0.480 | 0.60 | 60.0 | 2.4000 |
| patchy | 39 | 0.390 | 0.30 | 30.0 | 2.7000 |
| closed | 13 | 0.130 | 0.10 | 10.0 | 0.9000 |

## Test

Pearson chi-square goodness-of-fit test of the 100 site classifications against the 2019 regional reference composition.

- Chi-square statistic: 6.0000
- Degrees of freedom: 2
- p-value: 0.049787
- Effect size (Cohen's w): 0.2449
- Decision at alpha = 0.05: reject the reference composition.

[selected-result] Chi-square goodness-of-fit on 100 independent restoration sites (one classification per site): chi-square(2) = 6.0000, p = 0.049787, Cohen's w = 0.2449; the 2024 cover-class composition (48 sparse / 39 patchy / 13 closed) differs from the 2019 reference composition of 0.60 / 0.30 / 0.10 at alpha = 0.05.

## Notes

Every site contributes exactly one classification, so the tallied counts are 100 independent observations. The columns `shore_marker_km`, `foredune_width_m` and `sand_ph` describe the sites and were not used by this test.
