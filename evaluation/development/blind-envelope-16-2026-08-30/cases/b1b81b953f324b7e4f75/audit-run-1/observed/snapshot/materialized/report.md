# Two emollient regimens in childhood atopic dermatitis: week-eight results

## Data

The file `eczema_trial.csv` holds week-eight values for 66 children aged 2 to 11 years with mild to
moderate atopic dermatitis. **One row is one child.** There are no missing values.

| Column | Meaning |
| --- | --- |
| `child_id` | Per-child identifier, `C01` to `C66` |
| `emollient` | Regimen: `ointment` (twice-daily lipid-rich ointment, 33 children) or `lotion` (twice-daily light lotion, 33 children) |
| `severity_pts` | Eczema severity index score, points on a 0 to 72 scale |
| `itch_pts` | Worst itch in the past 24 hours, points on a 0 to 10 numerical rating scale |
| `tewl_gm2h` | Transepidermal water loss on the forearm, grams per square metre per hour |
| `sleep_nights` | Nights with disturbed sleep in the past week, count from 0 to 7 |
| `steroid_g` | Topical corticosteroid used over the eight weeks, grams |

The five outcome columns appear in the order the protocol declared them.

## Methods

Each of the five declared outcomes was compared between the two regimens with a two-sample t-test.
The five outcomes form one pre-declared family, so the complete set of five raw p-values was adjusted
together with the Holm step-down correction, which controls the family-wise error rate at 0.05. Every
conclusion below is taken from the adjusted value, not the raw one. The analysis is in `analysis.py`.

## Results

Group means, raw p-values and Holm-adjusted values, in the declared order:

| # | Outcome | Ointment mean | Lotion mean | Raw p | Adjusted p | Conclusion at family-wise 0.05 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Eczema severity index (points) | 5.80 | 8.60 | 0.0022 | 0.0111 | Significant: severity lower with the ointment |
| 2 | Worst itch in past 24 h (points) | 3.21 | 4.21 | 0.0133 | 0.0400 | Significant: itch lower with the ointment |
| 3 | Transepidermal water loss (g/m^2/h) | 13.51 | 18.25 | 0.0048 | 0.0193 | Significant: water loss lower with the ointment |
| 4 | Nights with disturbed sleep | 1.64 | 2.09 | 0.2478 | 0.4852 | Not significant |
| 5 | Topical corticosteroid used (g) | 21.00 | 24.00 | 0.2426 | 0.4852 | Not significant |

Three of the five declared outcomes separate the regimens after adjustment: severity, itch and water
loss. Disturbed sleep and steroid use do not.

## Robustness check on one questionable water loss measurement

One transepidermal water loss reading is implausibly high: child `C20`, in the lotion group, has a
value of 62.4 g/m^2/h, far outside the range of every other child. Readings like this arise when the
probe is used in a draught before it has equilibrated. The water loss comparison was therefore re-run
once with that single reading excluded, leaving 33 ointment and 32 lotion children. With the reading
excluded the group means are 13.51 (ointment) against 16.88 (lotion), raw p = 0.0003, compared with
the main analysis means of 13.51 against 18.25, raw p = 0.0048 and adjusted p = 0.0193.

**This re-run is a robustness check on one questionable measurement, not an inferential result.** It
is not part of the declared family, it is not adjusted, and it does not change any verdict. The
inferential conclusion for water loss remains the Holm-adjusted main result. What the re-run shows is
that the water loss difference is not an artefact of the single suspect reading: the direction and
size of the difference hold when that reading is dropped.

## Clinical interpretation

In these 66 children over eight weeks, the twice-daily lipid-rich ointment did better than the light
lotion on three of the five declared outcomes. Eczema severity was lower by about 2.8 points on the
0 to 72 index, worst itch was lower by about 1.0 point on the 0 to 10 scale, and transepidermal water
loss was lower by about 4.7 g/m^2/h, all after correcting for testing five outcomes together.

The two outcomes that did not separate are worth noting for counselling families. Nights with
disturbed sleep differed by about half a night per week and topical corticosteroid use by about 3 g
over eight weeks, and neither difference survived the family-wise correction. So this study supports
the ointment for skin-level control and barrier function, but does not demonstrate a sleep benefit or
a steroid-sparing benefit at this sample size. Both differences point in the ointment's favour, and a
larger or longer study would be needed to say whether they are real.

The results come from a single eight-week study in mild to moderate disease, so they do not speak to
severe eczema, to longer-term control, or to how well families keep using a greasier ointment outside
a trial setting.
