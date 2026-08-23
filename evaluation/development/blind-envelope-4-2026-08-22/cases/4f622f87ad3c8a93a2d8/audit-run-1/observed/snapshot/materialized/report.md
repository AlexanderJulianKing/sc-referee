# Deficit irrigation and apple flesh firmness at harvest

## Question

Does a summer deficit-irrigation schedule change apple flesh firmness at harvest,
compared with the standard schedule?

Sixteen mature trees of one cultivar were used in the research orchard. Eight were kept
on the standard irrigation schedule and eight were put on the deficit schedule for the
eight weeks before harvest. At harvest, eight fruit were picked from around the canopy of
each tree and each fruit was tested individually with a penetrometer, giving 128
individually tested fruit. Every fruit is a replicate in this comparison, so the trial is
well powered for the effect size of interest.

## Data

The single data file is `apple_firmness.csv`: 1 header row and 128 data rows. Values are
simulated for this project, with realistic levels and scatter, and are reproducible from
`make_data.py` (fixed seed).

**One row is one individual apple, picked at harvest and tested once with a
penetrometer.**

| # | Column | Type | Values | Meaning |
| --- | --- | --- | --- | --- |
| 1 | `tree_code` | text | `T-01` ... `T-16` | Identifier of the tree the fruit was picked from. |
| 2 | `irrigation` | text | `standard`, `deficit` | Summer irrigation schedule applied for the eight weeks before harvest. |
| 3 | `fruit_position` | integer | 1 ... 8 | Label for the sampling slot around the canopy. It is not a physical measurement and carries no order. |
| 4 | `firmness_N` | number, 1 decimal | 54.4 to 77.7 | Flesh firmness of that fruit in newtons, from the penetrometer. |

Fruit per schedule: 64 `standard`, 64 `deficit`. Overall firmness range in the file:
54.4 to 77.7 N.

## Method

`analysis.py` reads all 128 rows of the fruit table and compares mean `firmness_N`
between the two levels of `irrigation` with an independent two-sample t-test
(`scipy.stats.ttest_ind`), applied directly to the fruit rows.

## Results

Fruit tested: **128** (64 standard, 64 deficit).

| irrigation | fruit | mean firmness (N) | SD (N) | min (N) | max (N) |
| --- | --- | --- | --- | --- | --- |
| standard | 64 | 62.36 | 5.54 | 54.4 | 77.7 |
| deficit | 64 | 68.51 | 3.81 | 58.4 | 76.5 |

Independent two-sample t-test, deficit minus standard:

| quantity | value |
| --- | --- |
| difference in means | +6.15 N |
| t statistic | 7.320 |
| degrees of freedom | 126 |
| p-value | 2.58e-11 |

## Conclusion

Deficit irrigation firmed the fruit. Fruit from deficit-irrigation trees were 6.15 N
firmer on average than fruit from standard-irrigation trees, 68.51 N against 62.36 N,
and the difference is highly significant (t(126) = 7.32, p = 2.58e-11). Withholding
water over the eight weeks before harvest raised flesh firmness by about six newtons,
a change large enough to matter for storage and handling decisions in this cultivar.
