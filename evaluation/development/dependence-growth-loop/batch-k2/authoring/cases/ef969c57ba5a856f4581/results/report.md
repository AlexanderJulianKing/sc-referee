# Night-time street noise before and after porous asphalt resurfacing

## What was measured

Residential street segments spread across one mid-sized city were resurfaced
with porous low-noise asphalt during a single construction season. The
segments are separate sites: no two of them share a carriageway, a junction,
or a traffic corridor. For each segment the night-time noise indicator
L_night was logged for one full week before the works and for one full week
afterwards, and each week of logging was condensed on site into a single
energy-averaged dB(A) figure. Every segment therefore contributes exactly one
paired row, and the number of analysed rows equals the number of independent
segments.

## How it was analysed

The change for a segment is post_lnight_db minus pre_lnight_db, so a negative
change means a quieter street at night. Only the sign of that change was
tested, with an exact two-sided sign test (scipy.stats.binomtest, null
probability 0.5). The test treats each segment as one Bernoulli trial, which
is legitimate here because the segments are independent sites and none of
them is entered twice. Segments with no change at all would have been dropped
before the test; none had to be.

## Numbers

Segments analysed: 24
Quieter after resurfacing: 18
Louder after resurfacing: 6
Unchanged: 0
Share quieter: 0.750
Segments reaching the 1.0 dB reduction target: 15

Change in L_night, dB(A), post minus pre:
  mean: -1.179
  median: -1.450
  minimum: -3.400
  maximum: 1.600

## Result

[selected-result] Exact two-sided sign test on 24 independent street segments, one paired row each: 18 of 24 segments were quieter after porous asphalt resurfacing (share 0.750, p = 0.022656), with a median change of -1.450 dB(A).

## What it does and does not say

The sign test uses only the direction of change, so it supports the claim
that quieter nights are the usual outcome of resurfacing rather than a claim
about how many decibels are gained; the median change of -1.450 dB(A) and the
15 segments that reached the 1.0 dB target describe the size of the
effect descriptively. Because every segment appears exactly once, the 24
trials in the test are 24 independent sites, not 24 measurements taken on a
smaller number of streets. The programme had no untreated control streets, so
a city-wide change in night-time traffic over the season is not separated
from the effect of the resurfacing itself.
