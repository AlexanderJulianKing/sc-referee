# Mycelial ingrowth in intact-canopy versus canopy-gap spruce stands

## Data

The file holds 24 rows, one per surveyed stand: 12 intact-canopy and
12 canopy-gap. Each stand contributed a single pooled four-bag ingrowth
composite, so every stand supplies exactly one analysed measurement and no
stand appears twice in the file.

| canopy_state | stands | mean (mg) | SD (mg) | median (mg) |
| --- | --- | --- | --- | --- |
| intact | 12 | 41.000 | 4.899 | 41.000 |
| gap | 12 | 28.000 | 4.899 | 28.500 |

## Analysis

Welch's two-sided two-sample t-test on stand-level mycelial dry mass,
comparing intact-canopy stands with canopy-gap stands. The independent
unit is the stand, and each stand enters the test exactly once.

## Result

[selected-result] Welch's two-sample t-test on 12 intact-canopy stands versus 12 canopy-gap stands: mean difference 13.000 mg (intact minus gap), 95% CI [8.85, 17.15] mg, SE 2.000 mg, t = 6.5000, df = 22.00, two-sided p < 0.0001; mycelial ingrowth is higher in intact-canopy stands.

Cohen's d = 2.654, using a pooled SD of 4.899 mg.

The two groups happen to share the same sample SD, so the Welch correction
returns the equal-variance degrees of freedom.
