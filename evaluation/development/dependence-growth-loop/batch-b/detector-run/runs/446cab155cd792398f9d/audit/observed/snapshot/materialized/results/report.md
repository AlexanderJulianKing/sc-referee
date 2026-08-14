# Fernbrook bioretention pilot: interim exceedance screening

## What was measured

Each record in `data/input.csv` is one storm-event grab sample of the
effluent leaving one bioretention cell. A record carries the cell, the
sampled storm, the cell's filter media mix, the antecedent dry period,
and the effluent total phosphorus concentration in mg/L.

- Records analysed: 24
- Cells represented: 8
- Storms represented: 3
- Interim discharge target: 0.100 mg/L; a record counts as
  an exceedance when its concentration is strictly above the target
- Mean effluent total phosphorus: 0.1458 mg/L
- Records above the target: 18 of 24 (share 0.7500)

Records and exceedances by cell:

| cell_id | media_mix | records | exceedances |
| --- | --- | --- | --- |
| BR-01 | sand-compost | 3 | 3 |
| BR-02 | sand-compost | 3 | 0 |
| BR-03 | sand-biochar | 3 | 3 |
| BR-04 | sand-biochar | 3 | 3 |
| BR-05 | sand-biochar | 3 | 0 |
| BR-06 | sand-compost | 3 | 3 |
| BR-07 | sand-biochar | 3 | 3 |
| BR-08 | sand-compost | 3 | 3 |

## Analysis

Every record in the file was supplied as one trial to an exact two-sided
binomial test (`scipy.stats.binomtest`) of the null hypothesis that a
record exceeds the target with probability 0.5, that is,
that exceedance and compliance are equally likely for a record. The test
statistic is the number of records above the target, 18 out of
24 trials.

## Result

The observed exceedance share is 0.7500 (18/24),
against the benchmark share of 0.5. The exact two-sided
binomial p-value is 0.0227. At the 5% level the record-level
exceedance share is therefore distinguishable from the break-even
benchmark, with exceedances outnumbering compliant records.

[selected-result] Exact two-sided binomial test of record-level exceedance of the 0.100 mg/L interim total phosphorus target: 18 of 24 records exceeded (share 0.7500) against a null exceedance probability of 0.5; p = 0.0227.
