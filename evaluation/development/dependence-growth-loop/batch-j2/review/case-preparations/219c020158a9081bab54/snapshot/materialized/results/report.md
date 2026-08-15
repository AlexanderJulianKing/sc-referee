# Berth 7 coating trial: four-year corrosion rates

Source table: `data/input.csv` - 48 ultrasonic gauge readings from 12 pilings.

## What was surveyed

Twelve steel sheet pilings at Berth 7 were re-gauged after four years in
service. Alternate pilings along the berth carry one of two protective
coating systems. Every piling was gauged in the same four depth bands
(0.5 m, 1.5 m, 3.0 m and 5.0 m below mean sea level), and each gauge
reading is converted to a mean annual thickness loss in micrometres per
year.

## Reading-level summary

| coating system | readings | mean rate (um/yr) | sd (um/yr) |
| --- | ---: | ---: | ---: |
| coal_tar_epoxy | 24 | 62.40 | 6.63 |
| glassflake_polyester | 24 | 48.40 | 6.19 |

## Piling-level means

| piling | coating system | readings | mean rate (um/yr) |
| --- | --- | ---: | ---: |
| PIL-01 | coal_tar_epoxy | 4 | 54.40 |
| PIL-03 | coal_tar_epoxy | 4 | 58.40 |
| PIL-05 | coal_tar_epoxy | 4 | 60.40 |
| PIL-07 | coal_tar_epoxy | 4 | 62.40 |
| PIL-09 | coal_tar_epoxy | 4 | 66.40 |
| PIL-11 | coal_tar_epoxy | 4 | 72.40 |
| PIL-02 | glassflake_polyester | 4 | 40.40 |
| PIL-04 | glassflake_polyester | 4 | 44.40 |
| PIL-06 | glassflake_polyester | 4 | 46.40 |
| PIL-08 | glassflake_polyester | 4 | 50.40 |
| PIL-10 | glassflake_polyester | 4 | 52.40 |
| PIL-12 | glassflake_polyester | 4 | 56.40 |

## Test

Two-sample Student t test (equal variances assumed), one observation per
gauge reading, comparing coal_tar_epoxy against glassflake_polyester.

[selected-result] Two-sample t test on 48 gauge readings: coal_tar_epoxy mean 62.40 um/yr vs glassflake_polyester mean 48.40 um/yr, difference 14.00 um/yr, t(46) = 7.56, p < 0.001, significant at alpha = 0.05.

All 48 rows were entered into the test as separate observations.
