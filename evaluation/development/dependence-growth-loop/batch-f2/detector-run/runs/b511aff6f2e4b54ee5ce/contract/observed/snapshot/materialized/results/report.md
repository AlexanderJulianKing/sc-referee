# Canopy misting and leaf stomatal conductance

Question: after a 90-second canopy misting pulse, does stomatal conductance
on a coffee shrub leaf go up or down? Each leaf was read once before and
once after the pulse, and the two readings were subtracted.

## Counts

- Leaf readings in `data/input.csv`: 20
- Leaves with higher conductance after misting: 16
- Leaves with lower conductance after misting: 4
- Leaves with no change (dropped from the test): 0

## Summary values (mmol m-2 s-1)

| Quantity | Value |
| --- | --- |
| Mean pre-mist conductance | 157.35 |
| Mean post-mist conductance | 169.65 |
| Mean within-leaf change | 12.30 |
| Median within-leaf change | 15.50 |

## Test

Exact two-sided binomial sign test (scipy.stats.binomtest) applied to the 20
leaf readings, with each leaf reading supplied as one independent trial and
a null success probability of 0.5 (a leaf is equally likely to rise or fall).

[selected-result] Exact two-sided binomial sign test over 20 leaf readings: 16 of 20 (80.00%) rose after misting, p = 0.0118 against p0 = 0.5, so the 50/50 null is rejected at alpha = 0.05.

## Reading the numbers

The test statistic is the count of rising leaves, 16 out of 20 trials. Under
the null the two-sided exact tail probability is 0.0118, and the observed
rise fraction is 0.80.
