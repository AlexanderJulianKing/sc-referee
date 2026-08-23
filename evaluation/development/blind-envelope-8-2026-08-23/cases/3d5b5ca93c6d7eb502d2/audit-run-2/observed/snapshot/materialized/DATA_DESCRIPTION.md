# Data description

## File

`growth_rates.csv` — the single data file for this project. It holds a header row plus 96 data
rows. The file was produced by `make_data.py` (Python standard library only, fixed random seed
`20260823`); re-running that script reproduces the file byte for byte.

## What one row represents

One row is **one assay run of one evolved lineage**: a single measurement of maximum growth rate
taken from that lineage's frozen stock in one well of one plate-reader run.

## Units and counts

- 16 independent evolved lineages, `LIN01` through `LIN16`.
- Each lineage was assayed 6 times on the same frozen stock on the same plate reader, so the table
  holds 6 rows per lineage. The repeated rows within a lineage are technical replicates of the same
  biological sample.
- 16 lineages x 6 assay runs = **96 data rows**.
- The 96 assay runs sit in 96 distinct wells spread over 2 plates, 48 wells per plate. All six runs
  of a given lineage sit on the same plate. Each plate carries four inhibitor-evolved and four
  plain-medium lineages, so plate does not track selection regime.

## The two groups

`selection_regime` splits the lineages into the two arms of the evolution experiment:

| Value | Meaning | Lineages | Rows |
|---|---|---|---|
| `inhibitor` | Evolved for 30 days in medium containing a sub-inhibitory efflux-pump inhibitor | LIN01–LIN08 (8) | 48 |
| `plain` | Evolved for 30 days in plain medium | LIN09–LIN16 (8) | 48 |

A lineage belongs to exactly one regime, and every row of a lineage carries that same regime label.

## Columns

| Column | Type | Units | Description |
|---|---|---|---|
| `lineage_id` | text | — | Identifier of the independently evolved lineage the assayed stock came from. Values `LIN01`–`LIN16`. Appears in 6 rows, one per assay run. |
| `selection_regime` | text | — | Which arm of the evolution experiment the lineage was propagated in: `inhibitor` or `plain`. Constant within a lineage. |
| `replicate_run` | integer | — | Which of the lineage's six assay runs this row is, numbered 1–6. Run numbering restarts at 1 for each lineage. |
| `growth_rate_per_h` | number | per hour (h⁻¹) | Maximum growth rate measured in this assay run, from the steepest part of the growth curve. Range in the file 0.4446 to 0.8165. Rounded to 4 decimal places. |
| `plate_id` | text | — | Identifier of the assay plate the run was read on: `PLT01` or `PLT02`. |
| `well` | text | — | Well position of this run on its plate, as a row letter A–D plus a zero-padded column number 01–12 (for example `C07`). Unique within a plate; well layout was randomised. |
| `final_od600` | number | optical density units at 600 nm | Optical density at 600 nm reached at the end of the assay run, that is, the plateau of the growth curve. Range in the file 0.779 to 1.093. Rounded to 3 decimal places. |

## Value ranges in the file

| Group | Rows | Mean `growth_rate_per_h` |
|---|---|---|
| `inhibitor` | 48 | 0.5582 |
| `plain` | 48 | 0.6878 |

Per-lineage mean growth rates run from 0.506 to 0.606 h⁻¹ among the inhibitor-evolved lineages and
from 0.631 to 0.779 h⁻¹ among the plain-medium lineages.

## Provenance

These are simulated values, invented to match the study design and the growth-rate ranges given in
the study brief. They are not measurements from a real laboratory experiment.
