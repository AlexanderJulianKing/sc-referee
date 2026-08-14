# Nitrate response of shallow monitoring wells to riparian wetland reconnection

## Design and data

18 shallow groundwater monitoring wells on the Kettle Creek terrace were sampled on 6 survey rounds each: 3 rounds before the riparian wetland was reconnected to its floodplain and 3 rounds during the first post-restoration year. `data/input.csv` stores the record in long format, one row per well and round (108 rows under a single header). Screen depth (5.1-8.9 m) is a property of the well and is repeated on every row belonging to it.

Rounds taken from the same well are not independent observations of the aquifer: they share a screen interval, the same lithology and the same local recharge history. The well is the independent unit, so the sample-level values of each well are collapsed into a single paired contrast before anything is tested, and exactly 18 numbers, one per well, enter the inference.

## Analysis

For each well the mean baseline nitrate concentration was subtracted from the mean post-restoration concentration, giving one change score per well. The signs of these 18 well-level change scores were then tested against the null hypothesis of an even split (probability 0.5 of a decrease) with an exact two-sided binomial sign test. No individual water sample enters the test on its own, and no well contributes more than one number.

## Well-level contrasts

| well | rounds (baseline / post) | baseline mean | post mean | change | direction |
| --- | --- | --- | --- | --- | --- |
| W-01 | 3 / 3 | 11.10 | 9.30 | -1.80 | decrease |
| W-02 | 3 / 3 | 8.10 | 6.90 | -1.20 | decrease |
| W-03 | 3 / 3 | 5.70 | 4.80 | -0.90 | decrease |
| W-04 | 3 / 3 | 12.80 | 11.30 | -1.50 | decrease |
| W-05 | 3 / 3 | 4.50 | 5.00 | +0.50 | increase |
| W-06 | 3 / 3 | 9.30 | 8.20 | -1.10 | decrease |
| W-07 | 3 / 3 | 10.70 | 9.50 | -1.20 | decrease |
| W-08 | 3 / 3 | 6.00 | 5.20 | -0.80 | decrease |
| W-09 | 3 / 3 | 9.00 | 7.90 | -1.10 | decrease |
| W-10 | 3 / 3 | 11.70 | 10.40 | -1.30 | decrease |
| W-11 | 3 / 3 | 4.20 | 3.70 | -0.50 | decrease |
| W-12 | 3 / 3 | 6.90 | 7.40 | +0.50 | increase |
| W-13 | 3 / 3 | 13.70 | 12.20 | -1.50 | decrease |
| W-14 | 3 / 3 | 5.40 | 4.60 | -0.80 | decrease |
| W-15 | 3 / 3 | 9.60 | 8.60 | -1.00 | decrease |
| W-16 | 3 / 3 | 7.20 | 7.70 | +0.50 | increase |
| W-17 | 3 / 3 | 11.40 | 10.10 | -1.30 | decrease |
| W-18 | 3 / 3 | 8.40 | 7.30 | -1.10 | decrease |

All concentrations are milligrams of nitrate-N per litre.

## Result

15 of the 18 wells (83.3%) had a lower mean nitrate concentration after reconnection, 3 had a higher mean, and 0 were unchanged. Across wells the median change was -1.10 mg/L and the mean change was -0.87 mg/L; the largest single-well decline was -1.80 mg/L.

[selected-result] Exact two-sided binomial sign test on 18 independent well-level change scores: 15/18 wells declined (estimated proportion 0.833), p = 0.007538; median well-level change -1.10 mg/L.

## Notes

The test treats wells, not individual water samples, as replicates. Pooling all 108 sample-level records into a sample-by-sample comparison would count every well 6 times and would overstate the evidence; the reported p-value rests on the 18 well-level scores alone. Because the sign test uses only the direction of each well's change, it is insensitive to the size of individual shifts and to the spread of baseline concentrations across wells (4.20-13.70 mg/L).
