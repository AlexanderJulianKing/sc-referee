# Data description

## File

`marram_cover.csv` — one CSV file, comma separated, with a header row and 60 data rows.

## What one row is

One row is one 1 m quadrat: a single percentage cover reading taken at one point along the
transect on one dune.

## Survey units

Ten dunes were surveyed along one stretch of coast. Six quadrats were placed on each dune along a
fixed line running from the seaward toe up to the crest, giving 10 x 6 = 60 quadrat rows.

## The two groups

`rabbit_exclusion` splits the dunes into two groups of five:

| Group | Dunes | Quadrats | Meaning |
| --- | --- | --- | --- |
| `fenced` | 5 | 30 | Dune has been fenced against rabbits for three years |
| `unfenced` | 5 | 30 | Dune was left open to rabbits |

Fenced dunes: Braid Hollow, Sandhaven, Nether Ness, Salt Pans, Reddings.
Unfenced dunes: Corrie Links, Kelpie Bank, Whin Head, Tern Bar, Gull Rigg.

## Columns

Columns appear in this order.

| # | Column | Type | Values | Description |
| --- | --- | --- | --- | --- |
| 1 | `dune_name` | text | 10 distinct names, each on 6 rows | Short name of the dune the quadrat sits on |
| 2 | `rabbit_exclusion` | text | `fenced` or `unfenced` | Whether that dune is fenced against rabbits; the same for all six rows of a dune |
| 3 | `quadrat_number` | integer | 1 to 6 | Position of the quadrat along the fixed line, 1 nearest the seaward toe and 6 at the crest |
| 4 | `marram_cover_pct` | integer | 0 to 100 | Estimated percentage cover of marram grass in that quadrat |

## How the values were made

`make_data.py` (standard library only, fixed seed `20260829`) draws each quadrat value as a group
mean plus a whole-dune offset plus quadrat noise:

- group mean 48 percent for fenced dunes, 31 percent for unfenced dunes;
- a per-dune offset drawn with standard deviation 7 percentage points, standing for differences in
  exposure and sand supply, so the six quadrats on one dune share that offset;
- quadrat-to-quadrat variation drawn with standard deviation 9 percentage points;
- each value rounded to a whole number and held inside 0 to 100.

Rerunning `/usr/local/bin/python3 make_data.py` rewrites the same CSV exactly.

## What the file actually contains

| Group | Quadrats | Mean cover (%) | SD (%) | Range (%) |
| --- | --- | --- | --- | --- |
| `fenced` | 30 | 47.6 | 8.8 | 35 to 67 |
| `unfenced` | 30 | 30.3 | 10.0 | 17 to 63 |

Per-dune mean cover ranges from 20.5 percent (Whin Head, unfenced) to 49.8 percent (Braid Hollow
and Reddings, both fenced). No value hit the 0 or 100 limit.
