# Rise height of sourdough starters: rye versus spelt flour

## Data

`data/input.csv` holds 48 timed rise readings from 12 fermentation jars.
Each jar contributed 4 readings, taken at hours 6, 12, 18, 24 after feeding.

| flour_type | jars | readings | mean rise (mm) | sd (mm) |
| --- | ---: | ---: | ---: | ---: |
| rye | 6 | 24 | 20.00 | 3.16 |
| spelt | 6 | 24 | 27.00 | 3.16 |

## Analysis

Every one of the 48 rows was entered as a separate observation in a two-sided,
equal-variance two-sample Student t-test comparing rise height between the two
flour types (rye minus spelt). The group summaries above use the same 48 rows.

## Result

[selected-result] Two-sample t-test over 48 rise readings: rye minus spelt = -7.00 mm, t(46) = -7.67, p < 0.001, Cohen's d = -2.21.

Rye jars measured about 7 mm lower than spelt jars across the 24-hour window,
and at the level of individual readings the gap is flagged as highly significant.
