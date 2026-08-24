# Data description

## Files

The study uses a single data file: `vibration_runs.csv`. The prompt for this project calls for one
CSV, so there is no second summary table.

The file was written by `make_data.py` (Python standard library only, fixed random seed `20260823`).
Re-running that script reproduces the same file exactly.

## What one row represents

One row is **one instrumented field run by one operator**: the whole-body vibration measurement
recorded at the seat pan during a single day's run over the cultivated ground.

A row is *not* an operator. Each operator contributes six rows, one per run, so the rows are not
independent of one another.

## Size

| Quantity | Value |
| --- | --- |
| Rows (field runs) | 120 |
| Units (operators) | 20 |
| Runs per operator | 6 (every operator has all six; the design is balanced) |
| Header rows | 1 |

## The two groups

Seat type is fixed for an operator: an operator drove machines fitted with one seat type only, so
seat type never varies within an operator. Group sizes in terms of the unit of analysis:

| `seat_type` | Operators | Rows | Operator codes |
| --- | --- | --- | --- |
| `air_suspension` | 10 | 60 | OP-01, OP-04, OP-06, OP-07, OP-08, OP-09, OP-13, OP-17, OP-18, OP-19 |
| `mechanical` | 10 | 60 | OP-02, OP-03, OP-05, OP-10, OP-11, OP-12, OP-14, OP-15, OP-16, OP-20 |

The effective sample size for comparing seats is **20 operators (10 per group)**, not 120 runs.

## Columns

The file has four columns, in this order.

| Column | Type | Values | Meaning |
| --- | --- | --- | --- |
| `operator_code` | text | `OP-01` … `OP-20` | Staff code of the tractor operator. This is the unit of analysis, and the clustering variable: the six rows sharing a code are repeated measurements on the same person and machine. Zero-padded to two digits. |
| `seat_type` | text | `air_suspension` or `mechanical` | The seat fitted to the machine that operator drove. `air_suspension` is the air-suspension seat, `mechanical` the standard mechanical seat. Constant within an operator. |
| `run_number` | integer | 1 … 6 | Numbers the field run within that operator, in the order the runs were carried out on different days. It restarts at 1 for each operator, so it is only meaningful together with `operator_code`. It is not a date and not a run identifier that is unique across the file. |
| `vibration_total_value_ms2` | number, 2 decimal places | 0.41 to 1.43 in this file | The outcome: the vibration total value measured at the seat pan for that run, in metres per second squared (m/s²). The units are carried in the column name. Field instruments report to two decimal places, so the stored values are rounded to match. |

There are no missing values, no duplicate `operator_code` + `run_number` pairs, and no extra
identifier or date columns.

## How the values behave

The measurements were generated from a two-level model, which is what makes the repeated runs on one
operator resemble each other. Think of it as each operator sitting at their own personal level, with
each day's run wobbling a little around that level:

- Seat means: 1.05 m/s² for `mechanical`, 0.80 m/s² for `air_suspension`, a difference of
  0.25 m/s² in favour of the air-suspension seat.
- Operator-to-operator spread around the seat mean: standard deviation 0.18 m/s².
- Run-to-run spread within one operator: standard deviation 0.10 m/s².

Realised in this particular file:

| Statistic | `air_suspension` | `mechanical` |
| --- | --- | --- |
| Mean over rows (m/s²) | 0.792 | 1.099 |
| Standard deviation over rows (m/s²) | 0.175 | 0.175 |
| Standard deviation of the 10 operator means (m/s²) | 0.156 | 0.161 |

The mean within-operator standard deviation across all 20 operators is 0.091 m/s². The realised gap
between the two seat means is 0.307 m/s², a little wider than the 0.25 m/s² built into the model,
which is ordinary sampling variation with only ten operators per group.

Because most of the spread sits between operators rather than between runs, treating the 120 rows as
120 independent observations would understate the uncertainty in the seat comparison.
