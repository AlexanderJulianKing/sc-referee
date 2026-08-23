# Data description

## File

`salt_in_moisture.csv` — titration measurements of salt-in-moisture content for a
seasonal comparison of two starter cultures used in a semi-hard raw-milk cheese.
The file is produced by `make_data.py` (Python standard library only, fixed random
seed 20260837).

## What one row represents

One row is a single titration measurement: one reading of salt-in-moisture on the
composite sample taken from one production vat's wheel-set after ninety days of
ripening.

## Units and counts

- 16 production vats, made over one season (make dates 2025-04-08 to 2025-09-20,
  roughly one vat every eleven days, with the two cultures alternating through the
  make calendar).
- 1 composite sample per vat, drawn from that vat's wheel-set at ninety days.
- 3 titration readings per composite sample.
- 48 data rows in total (16 x 3), plus one header row.

## The two groups

`CultureType` splits the vats into two groups of equal size:

| CultureType | Vats | Titration measurements | VatCodes |
|---|---|---|---|
| Traditional | 8 | 24 | V01, V03, V05, V07, V09, V11, V13, V15 |
| Commercial | 8 | 24 | V02, V04, V06, V08, V10, V12, V14, V16 |

- **Traditional** — the traditional house culture. Salt-in-moisture centres near
  4.25 percent.
- **Commercial** — a defined commercial culture. Salt-in-moisture centres near
  4.70 percent.

## Columns

| Column | Type | Description |
|---|---|---|
| `VatCode` | text | Identifier of the production vat, `V01` through `V16`. Each code appears in three rows, one per titration reading of that vat's composite sample. |
| `CultureType` | text | Starter culture used for the vat. Either `Traditional` or `Commercial`. Constant within a vat. |
| `MakeDate` | date, `YYYY-MM-DD` | Date the vat was made. Constant within a vat. |
| `ReplicateNo` | integer | Which of the three titration readings on that vat's composite sample this row holds. Takes the values 1, 2, and 3. |
| `SaltInMoisturePct` | number, 2 decimal places | Measured salt-in-moisture content, in percent, from the laboratory's titration method. Observed range 3.85 to 5.09. |

## How the values were generated

`make_data.py` draws a true salt-in-moisture level for each vat from a normal
distribution centred on its culture mean (4.25 percent Traditional, 4.70 percent
Commercial) with a standard deviation of 0.30 percentage points, reflecting
vat-to-vat brining differences. The three readings for a vat are then drawn around
that vat's level with a standard deviation of 0.07 percentage points, reflecting the
repeatability of the titration method on one sample. Values are written rounded to
two decimal places.

Realised summary statistics:

| CultureType | Measurements | Mean | SD | Min | Max |
|---|---|---|---|---|---|
| Traditional | 24 | 4.23 | 0.24 | 3.85 | 4.60 |
| Commercial | 24 | 4.70 | 0.28 | 4.10 | 5.09 |
