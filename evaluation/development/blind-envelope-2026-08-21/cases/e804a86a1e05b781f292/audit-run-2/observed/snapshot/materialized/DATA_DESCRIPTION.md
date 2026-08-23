# Data description

The data file is `microcolony_growth.csv`. It holds the week-6 records for the pollen-diversity
experiment on *Bombus terrestris* microcolonies.

## What one row is

One row is one whole microcolony, measured once. Each colony lived alone in its own box and was fed
on its own, so the colony is the experimental unit. At the end of week 6 each colony was taken apart
and weighed a single time, giving one mass value per colony. Nothing in the file is a repeated
measure, a subsample, a comb, or an individual bee: reading down a row gives you the diet, the
housing position, the founding worker count, and the single final mass for one colony.

## How many units and rows

There are 24 microcolonies and 24 data rows, plus one header row. The colony identifiers run from
`MC-01` to `MC-24` and each identifier appears exactly once, so the number of unique colonies and the
number of rows are the same number, 24.

## The two groups

The colonies are split evenly between two diet treatments, 12 colonies in each:

- **monofloral** — fed pollen from a single species, willow.
- **mixed** — fed a mixed pollen diet drawn from four plant species.

Diet is a between-colony treatment: a colony is in one group for the whole experiment. The two groups
are also spread evenly across the three climate-cabinet shelves, with 4 monofloral and 4 mixed
colonies on each shelf (8 colonies per shelf), so shelf position is not tangled up with diet.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `hive_label` | string | Colony identifier, `MC-01` through `MC-24`. Unique to one colony; appears exactly once in the file. |
| `pollen_diet` | string | Diet treatment for that colony, either `monofloral` (willow only) or `mixed` (four plant species). 12 colonies per level. |
| `start_worker_count` | integer | Number of workers seeded into the colony when it was established, 4 to 6 bees. |
| `rearing_shelf` | string | Which climate-cabinet shelf the colony box sat on: `SH-1`, `SH-2`, or `SH-3`. Both diets are present on every shelf. |
| `final_colony_mass_g` | float, grams | Total colony mass at week 6: comb, brood, and stored provisions weighed together, in grams to one decimal place. This is the outcome of interest and is a single destructive measurement per colony. |

## Provenance

The file was written by `make_data.py` in this directory, which uses a fixed random seed
(`SEED = 20260821`) so the same file is produced on every run.
