# Cold-brew steeping: grind coarseness and total dissolved solids

## Data

48 total-dissolved-solids (TDS) readings taken from laboratory cold-brew
steeping vessels. Each vessel was loaded with a single grind setting and
sampled at draw times of 6, 12, 18 and 24 hours.

- coarse grind: n = 24, mean TDS = 1.1358 %, SD = 0.0959 %
- fine grind:   n = 24, mean TDS = 1.3879 %, SD = 0.1101 %

## Analysis

Welch two-sample t-test (two-sided, unequal variances) comparing the TDS
readings recorded at the fine grind setting with those recorded at the
coarse setting. Every row of the data file was supplied to the test as one
observation.

Mean difference (fine minus coarse): 0.2521 percentage points
t = 8.456, df = 45.1, p < 0.0001

## Result

[selected-result] Welch two-sample t-test on 48 TDS readings (24 fine, 24 coarse): mean difference fine minus coarse = 0.2521 percentage points, t = 8.456, df = 45.1, p < 0.0001.

## Interpretation

Vessels filled with the fine grind returned higher total dissolved solids
than vessels filled with the coarse grind across the sampled draw times.
