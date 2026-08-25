# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Seeded Python generator (seed 20260825). Running it writes `mini_silo_fermentation.csv`. Repeated runs give an identical file. |
| `mini_silo_fermentation.csv` | The study data. 60 data rows plus one header row. |

## What one row represents

One row is one laboratory mini-silo: a single sealed vessel packed on the day the
trial started, stored at a constant temperature, and opened after ninety days.
The row holds that silo's treatment label and its five fermentation measurements
taken at opening. Sixty mini-silos were packed from one homogenised batch of
wilted grass at the same density, thirty with a lactic acid bacteria inoculant
applied at packing and thirty left untreated. Each silo appears exactly once, and
every silo has a value for every outcome, so there are no missing cells.

## Columns of `mini_silo_fermentation.csv`

Columns appear in this order, and the five outcome columns are in the declared
protocol order.

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `silo_id` | text | none | Identifier for the mini-silo, `S01` through `S60`. Unique across rows. |
| `treatment` | text | none | The treatment factor, with exactly two values: `inoculated` (lactic acid bacteria inoculant applied at packing) and `untreated` (no inoculant). Thirty rows of each. |
| `dry_matter_loss_percent` | number, 2 decimals | percent of the dry matter packed | Outcome 1. Dry matter lost over the ninety days of storage. |
| `silage_ph` | number, 2 decimals | none (pH is a unitless scale) | Outcome 2. pH of the silage measured at opening. |
| `lactic_acid_g_per_kg_dm` | number, 1 decimal | grams per kilogram of dry matter | Outcome 3. Lactic acid concentration at opening. |
| `ammonia_n_percent_of_total_n` | number, 2 decimals | percent of total nitrogen | Outcome 4. Ammonia nitrogen at opening, expressed as a share of total nitrogen. |
| `aerobic_stability_hours` | number, 1 decimal | hours | Outcome 5. Hours from opening until the silage warmed two degrees above ambient. |

All five outcomes are continuous measurements, and none of the recorded values is
negative.

## How the values were produced

`make_data.py` draws each silo's measurements from a seeded random number
generator. Each silo gets one hidden "fermentation quality" draw that pushes all
five of its measurements together, because a silo that ferments well tends to
lose less dry matter, sit at a lower pH, hold more lactic acid, carry less
ammonia nitrogen, and stay cool longer after opening. The rest of each
measurement is independent noise. Dry matter loss, pH, and lactic acid are drawn
on the measured scale. Ammonia nitrogen and aerobic stability are drawn on a log
scale, which keeps them positive and gives them the long right tail those two
assays show in real silage work. Values are then rounded to normal laboratory
precision.
