# Data description

## File

`hatchling_carapace.csv` — one file, 240 data rows plus a header row (241 lines total).

## What one row is

**One row is one measured green turtle hatchling**, identified by which clutch it came from and its
measurement number within that clutch.

## Units and counts

| Level | Count |
| --- | --- |
| Clutches (independent units) | 24 |
| Clutches per substrate | 12 |
| Hatchlings measured per clutch | 10 |
| Hatchlings (rows) | 240 |

The clutch is the independent unit. The ten rows inside a clutch are siblings from one mother's
single clutch, sharing an egg chamber and a thermal history, so those rows are not independent of
each other.

## The two groups

The grouping variable is `substrate`, the incubation medium the clutch was relocated into inside the
protected hatchery:

- `native` — native beach sand. 12 clutches, 120 hatchlings.
- `imported` — the coarser imported sand used where the natural beach profile has eroded. 12
  clutches, 120 hatchlings.

Substrate is assigned at the clutch level, so every hatchling in a clutch has the same substrate
value. The two substrates are interleaved across clutch numbers rather than blocked (native clutches
are CL-03, CL-04, CL-05, CL-07, CL-08, CL-11, CL-12, CL-16, CL-17, CL-18, CL-22 and CL-23; the other
twelve are imported).

## Columns

Columns appear in this order.

| # | Column | Type | Values | Meaning |
| --- | --- | --- | --- | --- |
| 1 | `clutch_ref` | text | `CL-01` … `CL-24` | Identifier of the relocated clutch the hatchling came from. Repeats on 10 rows. |
| 2 | `substrate` | text | `native`, `imported` | Incubation substrate of that clutch. Constant within a clutch. |
| 3 | `hatchling_number` | integer | 1 … 10 | Index of the hatchling within its clutch. It is a label only, not a time order or a size rank. |
| 4 | `carapace_length_mm` | number, 1 decimal | 36.4 … 48.5 in this file | Straight carapace length in millimetres, measured before release. The outcome. |

There are no missing values. Every clutch has exactly ten rows, numbered 1 to 10.

## How the values were made

The data are simulated, not field records. `make_data.py` generates them with the Python standard
library only and a fixed seed (20260822), so re-running it reproduces the same CSV byte for byte.

The generator uses a two-level structure:

1. Each clutch gets its own mean, drawn around the substrate mean with a between-clutch standard
   deviation of 1.8 mm. This stands in for mothers differing in size and egg quality.
2. Each hatchling is drawn around its own clutch mean with a within-clutch standard deviation of
   1.2 mm.

Substrate means used: 43.6 mm for native sand, 41.2 mm for imported sand. Lengths are rounded to one
decimal place, and the few draws that would fall outside 36.0-49.0 mm are redrawn so the file stays
inside a believable range.
