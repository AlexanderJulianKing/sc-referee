# Data description: `pack_plate_counts.csv`

## What the file holds

One CSV file records the aerobic plate count results from the wash validation trial run
on the bagged leaf salad line.

**One row is one sealed retail pack, pulled at random off the line from one production
batch and tested on its own.**

- 20 production batches of bagged leaf salad, made over four production weeks
  (Monday to Friday, 1 June 2026 through 26 June 2026, one batch per production day).
- 5 sealed retail packs sampled per batch, each plated separately.
- 20 x 5 = **100 data rows**, plus one header row (101 lines in the file).

## The two groups

The grouping variable is `wash_treatment`, applied at the batch level. Every pack in a
batch carries the wash its batch received.

| `wash_treatment` | Meaning | Batches | Packs |
| --- | --- | --- | --- |
| `chlorine` | Plant's standard chlorine-based wash (incumbent) | 10 | 50 |
| `peracetic_acid` | Peracetic acid wash under evaluation | 10 | 50 |

The washes were alternated across the production schedule, with the two washes balanced
within each of the four weeks and the running order shuffled inside each week.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `batch_id` | text | Identifier for the production batch the pack came from, `B01` through `B20`. Twenty distinct values, each appearing on 5 rows. |
| `wash_treatment` | text | Which wash that batch received: `chlorine` or `peracetic_acid`. Constant within a batch. |
| `pack_id` | text | Identifier for the individual retail pack, formed as batch id plus pack number, e.g. `B01-P3`. Unique across the file; 100 distinct values. |
| `production_date` | date (`YYYY-MM-DD`) | Date the batch was produced. Constant within a batch; 20 distinct dates, one per batch. |
| `aerobic_plate_count_log_cfu_g` | number, 2 decimals | Aerobic plate count for that single pack, expressed as base-ten log colony-forming units per gram (log10 CFU/g). This is the outcome measured. |

## Observed values

`aerobic_plate_count_log_cfu_g` ranges from 2.86 to 5.81 log CFU/g across the 100 packs.
Batch mean log counts average 4.76 log CFU/g for the chlorine wash and 4.04 log CFU/g for
the peracetic acid wash. Batch means scatter by about 0.5 log units within a wash group,
and packs within the same batch scatter by about 0.29 log units.

## Structure worth noting for analysis

The five packs from one batch are not independent observations of the wash: they share a
batch, a production date, and a single wash application. The experimental unit is the
batch, not the pack.

## Provenance

The file was written by `make_data.py` in this directory (Python standard library only,
fixed random seed `20260845`), and is committed as plain text. Re-running
`/usr/local/bin/python3 make_data.py` reproduces it byte for byte.
