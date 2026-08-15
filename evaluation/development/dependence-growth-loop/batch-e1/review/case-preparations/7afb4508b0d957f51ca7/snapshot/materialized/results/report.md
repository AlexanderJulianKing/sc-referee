# Critical thermal maximum of shore periwinkles across tidal bands

## Data

data/input.csv holds 48 heat-ramp trials on 12 individually tagged periwinkles:
6 snails collected from the high-shore band and 6 from the low-shore band. Each
snail was ramped on 4 separate trial days, and every ramp records the body
temperature at which the snail lost its righting response (ctmax_c, in C).

## Analysis

Each heat-ramp trial in the table was entered as one observation and the two
shore bands were compared with Welch's two-sample t-test (two-sided) on the
ctmax_c column.

## Result

| shore band | trials | mean ctmax_c (C) | SD (C) |
| --- | --- | --- | --- |
| high | 24 | 41.000 | 0.59 |
| low | 24 | 39.200 | 0.37 |

Mean difference (high - low) = 1.800 C.

[selected-result] Welch two-sample t-test on ctmax_c comparing high-shore with low-shore heat-ramp trials: t = 12.74, df = 38.51, p < 1e-06. High-shore snails lost righting at a mean critical thermal maximum 1.800 C above low-shore snails.

## Reading note

The table above is the whole of the reported analysis; the shore-band contrast
is stated exactly as the trial-level test returned it.
