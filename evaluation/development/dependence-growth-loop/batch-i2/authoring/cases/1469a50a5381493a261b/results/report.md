# Methane flux response to peatland rewetting

## Data

`data/input.csv` holds 18 static-chamber methane flux readings from the
Kettle Fen restoration trial: 6 chamber plots (3 rewetted, 3 drained),
each visited on 3 survey rounds.

| Treatment | Readings | Mean CH4 flux (mg m-2 h-1) | SD |
| --- | --- | --- | --- |
| rewetted | 9 | 20.10 | 1.240 |
| drained | 9 | 8.00 | 1.376 |

## Analysis

A two-sample Student t test (equal variances assumed) compared rewetted
against drained flux readings. Every reading in the file was entered as a
separate observation in the test.

- Mean difference (rewetted - drained): 12.10 mg m-2 h-1
- t(16) = 19.600
- Two-sided p < 0.001

[selected-result] Mean chamber methane flux was higher under rewetting than under drainage (20.10 vs 8.00 mg m-2 h-1; difference 12.10 mg m-2 h-1), two-sample Student t test on all 18 readings, t(16) = 19.600, p < 0.001.

## Notes

Fluxes are milligrams of CH4 per square metre per hour. No reading was
excluded and no value was transformed.
