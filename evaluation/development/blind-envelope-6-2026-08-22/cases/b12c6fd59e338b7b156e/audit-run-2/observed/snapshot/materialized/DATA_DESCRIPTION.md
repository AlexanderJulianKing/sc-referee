# Data description

## File

`seedlings.csv` — one file, holding every measured seedling. All repeated rows are kept: no
bench-level averaging or other pre-aggregation has been applied. The prompt asks for a single
measured-seedling file, so there is no second summary CSV in this project.

The file was produced by `make_data.py` (Python standard library only, fixed random seed
`20260822`), which can be re-run to reproduce it byte for byte:
`/usr/local/bin/python3 make_data.py`.

## What one row represents

One row is **one measured Scots pine seedling** at the end of its first growing season: its
height and its root-collar diameter, together with the bench it grew on and that bench's
treatment.

Rows are therefore **not independent units**. Seedlings are grouped (clustered) inside benches:
the fifteen seedlings on a bench shared one irrigation valve and one batch of growing medium, so
they are more alike than seedlings picked from different benches. The bench, not the seedling, is
the unit that was assigned to a treatment.

## Units and counts

| Level | Count |
| --- | --- |
| Nursery benches (independent experimental units) | 12 |
| Benches receiving inoculated growing medium | 6 |
| Benches receiving uninoculated growing medium | 6 |
| Seedlings measured per bench | 15 |
| Data rows (measured seedlings) | 180 |
| Rows per treatment group | 90 |

180 data rows plus one header row.

## The two groups

`inoculantTreatment` has exactly two values, and the treatment was applied to a whole bench, so
every seedling on a bench carries the same value:

- **`inoculated`** — bench filled with growing medium carrying the mycorrhizal inoculant.
  Benches 1, 2, 5, 7, 10, 11 (6 benches, 90 seedlings).
- **`uninoculated`** — bench filled with the same growing medium without the inoculant, the
  control. Benches 3, 4, 6, 8, 9, 12 (6 benches, 90 seedlings).

Bench-to-bench variation is real and sizeable, so the bench mean heights of the two groups
overlap even though the group means differ.

## Columns

The file has five columns, in this order.

| Column | Type | Units | Range in this file | Meaning |
| --- | --- | --- | --- | --- |
| `benchNo` | integer | — | 1–12 | Identifier of the nursery bench the seedling grew on. Each bench has its own irrigation valve and is one experimental unit. Appears 15 times, once per seedling on that bench. This is the grouping (cluster) variable. |
| `inoculantTreatment` | text | — | `inoculated`, `uninoculated` | Which growing medium the bench received. Constant within a bench. |
| `seedlingNo` | integer | — | 1–15 | Position number of the seedling within its bench. It is a within-bench label only; seedling 3 on bench 1 has nothing to do with seedling 3 on bench 2. The pair (`benchNo`, `seedlingNo`) uniquely identifies a row. |
| `heightCm` | number, 1 decimal place | centimetres | 18.7–53.1 | Seedling height at the end of the first growing season. This is the primary outcome. |
| `rootCollarDiamMm` | number, 1 decimal place | millimetres | 4.1–8.8 | Stem diameter at the root collar (where stem meets root) for the same seedling. It tracks height: taller seedlings are generally thicker. Secondary measurement. |

## How the values were generated

Simulated values, chosen to be realistic for a first-year container nursery crop:

- Mean height 34 cm on uninoculated benches, 41 cm on inoculated benches (a 7 cm difference built
  into the generator).
- About 4 cm of variation between benches and about 5 cm of variation between seedlings on the
  same bench, drawn from normal distributions. Because only six benches per treatment were drawn,
  the observed group means differ by less than the built-in 7 cm.
- Root-collar diameter is a straight-line function of height (0.12 mm per cm) plus about 0.45 mm
  of measurement noise, held between 4 and 9 mm.

There are no missing values, and every bench has a complete set of fifteen seedlings.
