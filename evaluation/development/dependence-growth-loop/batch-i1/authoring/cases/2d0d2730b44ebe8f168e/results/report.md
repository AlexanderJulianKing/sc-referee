# Free chlorine residual before and after main relining

## Data

Each row of `data/input.csv` is one hydrant flush event recorded during the
cement-mortar relining programme: the free chlorine residual measured at the
hydrant before the upstream main was relined, and the residual measured at
the same hydrant after relining.

## Analysis

The two readings attached to a flush event form a natural pair, so the
post-minus-pre gain was analysed with a two-sided paired t-test
(`scipy.stats.ttest_rel`) over the 36 event-level pairs.

## Result

- Flush events analysed: 36
- Mean pre-reline residual: 0.750 mg/L
- Mean post-reline residual: 1.050 mg/L
- Mean gain (post - pre): 0.300 mg/L
- Standard deviation of gains: 0.100 mg/L
- Paired t(35) = 18.000, p < 0.0001

[selected-result] Paired t-test on 36 flush-event pairs: mean free chlorine gain after relining = 0.300 mg/L (SD 0.100 mg/L), t(35) = 18.000, p < 0.0001.

## Reading

Relining is associated with a mean free chlorine residual gain of about
0.30 mg/L per flush event, and the paired test rejects the no-change null
at the conventional 5 percent level.
