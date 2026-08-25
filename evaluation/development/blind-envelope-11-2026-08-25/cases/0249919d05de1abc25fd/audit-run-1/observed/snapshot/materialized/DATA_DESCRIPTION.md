# Data description: greenhouse cucumber grafting trial

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Seeded Python generator that produces the CSV below. Fixed seed, so re-running it reproduces the same file exactly. Requires NumPy. |
| `cucumber_grafting_trial.csv` | The trial record sheet. 60 data rows plus one header row, 10 columns, no missing cells. |

## What one row represents

One row is one cucumber plant, measured over the full twelve-week production
cycle. Sixty plants of a single commercial variety were raised in one glasshouse
compartment under identical climate control and irrigation: 30 grafted onto a
vigorous interspecific squash rootstock and 30 grown on their own roots. Every
plant was measured individually, so each row carries that plant's identifier,
its eight declared cycle-end outcome measurements, and the propagation method it
belongs to. Rows appear in bench recording order, so the two propagation methods
are interleaved rather than blocked.

## Columns of `cucumber_grafting_trial.csv`

Columns appear in this order. Outcome columns 2 through 9 are the eight declared
outcomes in their declared order.

| # | Column | Type | Unit | Meaning |
| --- | --- | --- | --- | --- |
| 1 | `plant_id` | text | none | Plant label, `CU-001` through `CU-060`. Unique, one per row. |
| 2 | `marketable_yield_kg` | number, 2 decimals | kilograms | Total mass of marketable fruit harvested from that plant across the cycle. |
| 3 | `marketable_fruit_count` | whole number | count | Number of marketable fruits harvested from that plant across the cycle. |
| 4 | `mean_fruit_mass_g` | number, 1 decimal | grams | Average fresh mass of that plant's marketable fruit. |
| 5 | `stem_diameter_mm` | number, 1 decimal | millimetres | Stem diameter measured 20 cm above the graft union (the equivalent height on self-rooted plants). |
| 6 | `leaf_chlorophyll_index` | number, 1 decimal | unitless | Leaf chlorophyll reading from a handheld meter, taken on that plant. |
| 7 | `root_dry_mass_g` | number, 1 decimal | grams | Dry mass of the plant's root system, weighed after the cycle ended. |
| 8 | `soluble_solids_brix` | number, 1 decimal | degrees Brix | Soluble solids content of that plant's fruit. |
| 9 | `days_to_first_harvest` | whole number | days | Days from planting to the plant's first harvested fruit. |
| 10 | `propagation_method` | text | none | Grouping factor with exactly two values: `grafted` (squash rootstock) or `self_rooted` (own roots). 30 rows each. |

## Value ranges as recorded

Observed minimum and maximum across all 60 rows, for orientation only.

| Column | Minimum | Maximum |
| --- | --- | --- |
| `marketable_yield_kg` | 3.66 | 7.98 |
| `marketable_fruit_count` | 14 | 27 |
| `mean_fruit_mass_g` | 239.0 | 337.4 |
| `stem_diameter_mm` | 8.6 | 14.2 |
| `leaf_chlorophyll_index` | 34.5 | 54.2 |
| `root_dry_mass_g` | 7.0 | 33.5 |
| `soluble_solids_brix` | 2.6 | 4.2 |
| `days_to_first_harvest` | 35 | 49 |

## Notes on how the file was built

`make_data.py` draws each plant's measurements from per-group normal
distributions centred on the levels set out in the trial plan. Each plant also
carries a single latent vigour term that feeds into several traits at once, so a
vigorous individual tends to set more fruit, carry a thicker stem, build more
root and reach first harvest slightly earlier. Marketable yield is computed from
that plant's fruit number and mean fruit mass with a small amount of weighing and
grading slack added, which is how the harvest total relates to its parts in a real
record sheet. Counts and day figures are stored as whole numbers; the remaining
outcomes are rounded to the precision the corresponding instrument reports.
