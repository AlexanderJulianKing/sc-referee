# Sphagnum re-establishment after ditch blocking in drained peat basins

## Design

Each row of `data/input.csv` is one drained peat basin surveyed once in the
2025 growing season. Basins are the independent units: 24 basins, 24 rows,
and no basin appears twice. Ditch treatment was fixed for the whole basin, so
each basin contributes a single yes/no outcome to a single cell of the table.

## Groups

| Ditch treatment | Basins | Re-established | Proportion | Mean area (ha) | Median peat depth (cm) |
| --- | --- | --- | --- | --- | --- |
| blocked | 12 | 9 | 0.750 | 14.58 | 207.5 |
| open | 12 | 3 | 0.250 | 14.25 | 207.5 |

## Test

Fisher's exact test (two-sided) on the 2x2 table of ditch treatment by
Sphagnum re-establishment. Fisher's exact test was chosen over a chi-square
test because several expected cell counts are small.

Contingency table (rows: blocked, open; columns: yes, no): [[9, 3], [3, 9]]

- Sample odds ratio: 9.000
- Two-sided p-value: 0.0391
- Risk difference (blocked minus open): 0.500

## Result

[selected-result] Fisher's exact test on 24 independent peat basins: Sphagnum re-established in 9 of 12 basins with blocked ditches versus 3 of 12 basins with open ditches (sample odds ratio 9.000, two-sided p = 0.0391), a significant difference at alpha = 0.05.

## Notes

Basin area and peat depth are reported only as descriptive balance checks;
neither was entered into the test.
