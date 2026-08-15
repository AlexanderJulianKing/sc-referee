# Critical thermal maximum of shore limpets in two tidal zones

## Data

Column `ctmax_c` of `data/input.csv` records the critical thermal maximum, in
degrees Celsius, reached by intertidal limpets during a heated-seawater ramp.
Animals were collected from one granite shore platform in two tidal zones and
each animal was ramped on several consecutive days.

| Shore zone | Animals | Measurements | Ramps per animal | Mean CTmax (C) | SD (C) |
| --- | --- | --- | --- | --- | --- |
| Low shore | 6 | 24 | 4 | 33.200 | 0.273 |
| High shore | 6 | 24 | 4 | 35.600 | 0.273 |

## Analysis

Two-sided two-sample Student t-test (pooled variance) comparing `ctmax_c`
between the low-shore and high-shore groups. Every measurement in the file
was entered into the test as one observation of its group.

## Result

High-shore limpets reached a mean CTmax 2.400 C above low-shore limpets.

[selected-result] Two-sample t-test of ctmax_c by shore zone: t(46) = -30.402, p < 0.0001 (low shore 33.200 C, n = 24; high shore 35.600 C, n = 24; difference 2.400 C).

All 48 measurements were treated as independent observations, giving 46
degrees of freedom.
