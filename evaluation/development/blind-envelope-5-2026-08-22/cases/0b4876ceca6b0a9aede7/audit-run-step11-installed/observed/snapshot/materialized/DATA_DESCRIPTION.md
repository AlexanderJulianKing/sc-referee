# Data description

## File

`harvest_fillet_omega3.csv` — the harvest sampling table for the grow-out feed
comparison. Comma-separated, one header row plus 120 data rows.

There is only one data file. The study prompt calls for a single data file, so no
separate summary table was produced.

## What one row represents

One row is **one individual measured fish**: a single salmon netted from one sea
cage at harvest, weighed whole and then sampled for fillet omega-3 content. Each
fish appears exactly once.

## Units and counts

- 10 sea cages, all stocked from the same smolt batch.
- Each cage was assigned whole to one of the two feeds: 5 cages per feed.
- 12 fish were netted at random from each cage and measured individually.
- 10 cages x 12 fish = **120 measured fish = 120 data rows**.
- 60 fish came from the 5 standard-feed cages and 60 from the 5 algal-oil cages.

The cage is the unit that received a feed. The fish is the unit that was measured.

## The two groups

| Value in `feed` | Feed | Cages | Cage IDs | Fish |
|---|---|---|---|---|
| `standard` | Standard high-fishmeal grow-out feed | 5 | HVR-P01, HVR-P04, HVR-P07, HVR-P09, HVR-P12 | 60 |
| `algal_oil` | Reformulated feed with more algal oil | 5 | HVR-P02, HVR-P05, HVR-P08, HVR-P11, HVR-P14 | 60 |

Both feeds were fed over the final six months before harvest.

## Columns

Columns appear in the file in this order.

| # | Column | Type | Units | Description |
|---|---|---|---|---|
| 1 | `cage_id` | text | — | Pen label of the sea cage the fish was netted from, in site-pen form `HVR-Pnn` (site code HVR plus the pen number on the walkway). 10 distinct values. Every fish in a cage shares this label. |
| 2 | `feed` | text | — | Which feed that cage received. Exactly two values: `standard` or `algal_oil`. Constant within a cage, because feed was assigned to whole cages. |
| 3 | `fish_number` | integer | — | Sequence number of the fish within its own cage sample, 1 to 12. It is a within-cage label only, not a farm-wide fish ID: `fish_number` 3 in HVR-P01 and `fish_number` 3 in HVR-P02 are different fish. The pair (`cage_id`, `fish_number`) is unique across the file. |
| 4 | `harvest_weight_kg` | number, 2 decimals | kilograms | Whole-body harvest weight of that fish, roughly 4.0 to 6.5 kg. |
| 5 | `omega3_mg_per_g` | number, 2 decimals | mg per g wet fillet | The outcome: EPA plus DHA content of that fish's fillet, in milligrams per gram of wet fillet. |

## Observed ranges in the file

| Group | Fish | `omega3_mg_per_g` range | `harvest_weight_kg` range |
|---|---|---|---|
| `standard` | 60 | 8.12 to 13.92 | 4.16 to 6.34 |
| `algal_oil` | 60 | 10.87 to 16.50 | 4.00 to 6.42 |

There are no missing values in any column.

## How the file was generated

`make_data.py` (Python standard library only, fixed seed `20260822`) writes
`harvest_fillet_omega3.csv`. Fillet omega-3 is built from a feed-level mean, a
per-cage offset that creates drift between cages on the same feed, a mild
positive slope on harvest weight (heavier fish carry slightly fatter fillets),
and fish-level variation within each cage. Re-running the script reproduces the
same file byte for byte.
