# Kilda Sound kelp growline seeding-density trial

## Data
Source: data/input.csv
Blade records: 40
Growlines: 8
Blade records per growline: 5

## Per-growline means
L01  sparse  mean = 2.10 cm/day  (n = 5)
L02  sparse  mean = 2.30 cm/day  (n = 5)
L03  sparse  mean = 2.00 cm/day  (n = 5)
L04  sparse  mean = 2.60 cm/day  (n = 5)
L05  dense   mean = 1.70 cm/day  (n = 5)
L06  dense   mean = 1.50 cm/day  (n = 5)
L07  dense   mean = 1.90 cm/day  (n = 5)
L08  dense   mean = 1.30 cm/day  (n = 5)

## Method
Response: elongation_cm_per_day (blade elongation rate).
Groups: seeding_density, sparse versus dense.
Test: two-sample Student t-test with a pooled variance estimate
(scipy.stats.ttest_ind, equal_var=True) over the 40 blade records.

## Group summaries
sparse: n = 20, mean = 2.25 cm/day, sd = 0.240 cm/day
dense:  n = 20, mean = 1.60 cm/day, sd = 0.233 cm/day
Mean difference (sparse - dense): 0.65 cm/day

## Result
t(38) = 8.691, p < 1e-08

[selected-result] Two-sample Student t-test over 40 blade elongation records from 8 growlines: sparse-seeded blades elongated 0.65 cm/day faster on average than dense-seeded blades (2.25 versus 1.60 cm/day), t(38) = 8.691, p < 1e-08.
