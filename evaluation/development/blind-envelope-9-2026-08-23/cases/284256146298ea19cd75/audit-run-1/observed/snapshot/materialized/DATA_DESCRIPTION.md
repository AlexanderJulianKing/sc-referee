# Data description

## File

One CSV file: `newt_body_mass.csv`. It was produced by `make_data.py`, which uses only the Python
standard library and a fixed random seed, so re-running the script reproduces the same file.

There is no second summary CSV. The survey produced a single table of weighed animals.

## What one row represents

One row is one adult male smooth newt, bottle-trapped in one pond and weighed once on the spot
before release. A row is a single animal weighing, not a pond.

## Units and counts

- 15 ponds on working farms, coded `PND-01` through `PND-15`.
- 5 adult male newts trapped and weighed in each pond.
- 75 rows of data, plus one header row (76 lines in the file).
- Group sizes: 8 ponds with a fenced grass buffer strip, contributing 40 rows; 7 ponds with
  livestock access to the water's edge, contributing 35 rows.

Every pond contributes exactly five rows, one per weighed newt. No pond is missing, and no cell in
the table is blank.

## The two groups

The grouping variable is the state of the pond margin.

- `buffered` — the pond is ringed by a fenced grass buffer strip that keeps stock off the margin.
  8 ponds: PND-01, PND-03, PND-04, PND-07, PND-08, PND-10, PND-13, PND-14.
- `unfenced` — livestock can reach the water's edge. 7 ponds: PND-02, PND-05, PND-06, PND-09,
  PND-11, PND-12, PND-15.

Every newt in a pond carries that pond's group label, so the label is fixed at pond level and does
not vary from newt to newt within a pond.

## Columns

The file has four columns, in this order.

| Column | Type | Description |
| --- | --- | --- |
| `pond_code` | text | The pond the newt was caught in. Values run `PND-01` to `PND-15`. This is the survey unit; it repeats on five consecutive rows, one for each newt weighed in that pond. |
| `buffer_strip` | text | Condition of the pond margin. Exactly two values: `buffered` (fenced grass buffer strip) and `unfenced` (livestock access to the water's edge). Constant within a pond. |
| `newt_number` | integer | Which of the five captured newts this row is, numbered 1 to 5 within its own pond. It is a within-pond capture label, not an animal identity that carries across ponds. Numbers restart at 1 for each pond. |
| `body_mass_g` | number | Body mass of that newt in grams, recorded to two decimal places on a field balance that reads to the centigram. |

## Ranges in the recorded data

- `body_mass_g` runs from 1.79 g to 4.29 g across all 75 rows.
- Mean mass is 3.37 g in the buffered ponds and 2.87 g in the unfenced ponds.
- Pond averages run from 2.17 g to 3.81 g. The spread between pond averages is 0.61 g, and the
  average spread among the five newts within a single pond is 0.49 g.

## How the values were generated

`make_data.py` draws an average mass for each pond, then draws each of that pond's five newts
around that pond average. Two spread settings control the picture: 0.55 g between pond averages and
0.50 g between newts caught in the same pond. Ponds with a buffer strip get 0.50 g added to their
average, on a base of 2.75 g for ponds with livestock access. A draw landing outside 1.60 g to
4.40 g, the plausible range for an adult male smooth newt, is redrawn rather than trimmed to the
edge, so masses do not pile up at the limits. Values are then rounded to the centigram to match what
a field balance would report.
