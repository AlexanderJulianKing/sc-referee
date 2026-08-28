# Acetazolamide prophylaxis at 4300 m: site report

## Data

This project holds two fixed data files. `analysis.py` reads both and writes to neither.

In `data.csv`, one row is one trekker measured on the second morning at the 4300 m camp. Its
columns are `trekker_id`, the trekker identifier as a text label; `acetazolamide_group`, the
allocated study drug as one of two text labels, `acetazolamide` or `placebo`; `spo2_pct`,
peripheral oxygen saturation on room air in percent; `lake_louise_ams_score`, the Lake Louise acute
mountain sickness score in points on the 0 to 12 scale; `resting_heart_rate_bpm`, resting heart
rate in beats per minute; and `periodic_breathing_events_per_hr`, nocturnal periodic breathing as
apnoea and hypopnoea events per hour of sleep.

In `central_adjusted_pvalues.csv`, one row is one declared outcome. Its columns are `outcome`, the
outcome name written exactly as that outcome's column name in `data.csv`; `p_value_raw`, the
unadjusted p-value as a probability from 0 to 1; `p_value_adjusted`, the p-value for that outcome
after correction across the family of four, also a probability from 0 to 1; and
`correction_method`, a text label naming the correction applied.

## Design

Sixty-four trekkers ascended the same route on the same schedule. Thirty-two took acetazolamide
125 mg twice daily from the day before ascent and thirty-two took a matching placebo. The
programme protocol declared four outcomes as one family, in this order: `spo2_pct`,
`lake_louise_ams_score`, `resting_heart_rate_bpm`, `periodic_breathing_events_per_hr`. Every
trekker was measured on all four.

The declared family was tested and adjusted for multiplicity by the programme's central analysis
stage, which applied a holm-bonferroni correction across the four outcomes and returned the
adjusted p-values to this site. This site's script only summarises the raw measurements, runs
routine data checks, and reads the adjusted values. It performs no test and computes no p-value of
its own.

## Results

All data checks passed. Both groups had 32 trekkers, every trekker had a value for every outcome,
the group column held exactly two labels, and all recorded values fell in physiologically sensible
ranges.

Oxygen saturation averaged 88.5% (SD 2.9) on acetazolamide and 85.8% (SD 3.0) on placebo, a
difference of 2.7 percentage points. The adjusted p-value is 0.00156, so this outcome is
significant at the 0.05 family level.

The Lake Louise score averaged 2.50 points (SD 1.68) on acetazolamide and 3.25 points (SD 1.72) on
placebo, a difference of -0.75 points. The adjusted p-value is 0.166, so this outcome is not
significant at the 0.05 family level.

Resting heart rate averaged 83.7 bpm (SD 8.8) on acetazolamide and 86.4 bpm (SD 9.2) on placebo, a
difference of -2.7 bpm. The adjusted p-value is 0.232, so this outcome is not significant at the
0.05 family level.

Periodic breathing averaged 12.40 events per hour (SD 9.50) on acetazolamide and 25.60 events per
hour (SD 10.59) on placebo, a difference of -13.21 events per hour. The adjusted p-value is
0.00000802, so this outcome is significant at the 0.05 family level.

## Conclusion

At this site, acetazolamide prophylaxis was associated with higher oxygen saturation and much less
nocturnal periodic breathing, and both differences held up after the central stage corrected for
testing four outcomes. The smaller differences in symptom score and resting heart rate did not
reach the 0.05 family level. Two of the four declared outcomes therefore favour prophylaxis, and
the symptom and heart rate outcomes remain undecided at this sample size.
