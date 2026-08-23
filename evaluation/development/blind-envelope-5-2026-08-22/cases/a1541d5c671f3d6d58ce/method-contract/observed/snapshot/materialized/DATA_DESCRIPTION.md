# Data description

## The file

`storage_firmness.csv` is the only data file in this project. The study prompt calls for a single
data file, so there is no second summary CSV.

It has one header line and 84 data rows.

## What one row is

One row is one **bin visit**: a single storage bin opened and sampled on a single sampling date.
A row is not a bin, and it is not a tuber. Each bin appears six times in the file, once per sampling
week, so the same bin's six rows are repeated measurements of that one bin over the storage season.

## Units and counts

- 14 storage bins, all filled from the same graded seed-potato lot.
- 7 bins held under conventional cold air, 7 bins held under a low-oxygen controlled atmosphere.
- 6 sampling times per bin: weeks 4, 8, 12, 16, 20, and 24 after loading (four-week intervals).
- 14 bins x 6 visits = **84 rows**, 42 rows per atmosphere group.
- Every bin has a complete set of six visits. There are no missing values.

## The two groups

The grouping variable is `atmosphere`, with exactly two levels:

| Value | Meaning | Bins | Rows |
| --- | --- | --- | --- |
| `conventional_air` | Conventional cold-air storage | 7 | 42 |
| `low_oxygen_ca` | Low-oxygen controlled atmosphere | 7 | 42 |

Atmosphere is set at the level of the bin, not the visit. All six rows for a given bin carry the
same atmosphere value, because a bin was assigned to one atmosphere at loading and stayed there for
the whole season.

## Columns

Columns appear in the file in this order.

| # | Column | Type | Units | Description |
| --- | --- | --- | --- | --- |
| 1 | `bin_code` | text | none | The store's own bin tag, e.g. `CS1-A01`. Format is `<store house>-<row><bin number>`: `CS1` and `CS2` are the two cold-store houses, `A`/`B` the row, and the two digits the bin position in that row. There are 14 distinct codes, each on exactly 6 rows. This is the identifier of the physical experimental unit. |
| 2 | `atmosphere` | text | none | Storage treatment for the bin. Two values only: `conventional_air` or `low_oxygen_ca`. Constant within a bin. |
| 3 | `storage_week` | integer | weeks since loading | Sampling time. One of 4, 8, 12, 16, 20, 24. |
| 4 | `weight_loss_pct` | number | percent of loading weight | Cumulative weight lost by the bin's contents since it was loaded, as a percentage of loading weight. Recorded to 2 decimal places. It only rises within a bin, because it is measured against the loading weight. Observed range across the file is 0.64 to 8.22 percent: under 1 percent at week 4, and roughly 4 to 9 percent by week 24. |
| 5 | `firmness_newton` | number | newtons (N) | Tuber firmness from a penetrometer reading on the sample drawn at that visit. This is the study outcome. Recorded to 1 decimal place. It falls over the season, from roughly 63 to 69 N at week 4 down to roughly 42 to 48 N (conventional air) or 50 to 55 N (low oxygen) at week 24. |

## How the values were produced

`make_data.py` writes the CSV. It uses only the Python standard library and a fixed random seed
(`20260822`), so re-running it reproduces the same file byte for byte.

Firmness is built as a group-level starting level plus a group-level decline per week, plus a
per-bin offset that holds for all six of that bin's visits, plus small visit-to-visit measurement
noise. The per-bin offset is what makes a bin sit consistently above or below its group's trend, so
the six rows from one bin are related to each other and are not six independent draws. Weight loss
is built the same way, with a per-bin rate, and is held non-decreasing within a bin.

Run it with:

```
/usr/local/bin/python3 make_data.py
```

## Checksum

```
sha256(storage_firmness.csv) = 4a23802c8f72c6458f2253358bd6a0d899e566927002094aafbeeba2df930e67
```
