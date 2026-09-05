# Data description

## Files

### `make_data.py`

Deterministic, seeded Python generator (seed `20260844`, NumPy `default_rng`). Running it with the
project interpreter writes `trout_feeding_trial.csv` next to the script. Re-running it reproduces
the same file byte for byte.

### `trout_feeding_trial.csv`

The study data for the twelve-week rainbow trout feeding trial. Comma separated, one header row and
80 data rows, UTF-8, no missing cells.

**One row is one individually tagged juvenile rainbow trout**: its diet group and the five outcomes
measured on that fish at the end of the twelve-week trial. Forty fish carry the conventional
fishmeal-based diet and forty carry the insect-meal replacement diet. Rows are ordered by fish tag,
so the forty fishmeal fish come first and the forty insect-meal fish follow.

Columns, in file order:

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `fish_tag` | text | none | Identifier of the individual fish, from the tagging list (`RBT-1001` through `RBT-1080`). Unique across all 80 rows. |
| `final_body_mass_g` | number | grams | Declared outcome 1. Body mass of the fish weighed at the end of the twelve weeks. Recorded to 0.1 g. |
| `specific_growth_rate_pct_per_day` | number | percent of body mass per day | Declared outcome 2. Specific growth rate of the fish over the twelve-week trial. Recorded to two decimals. |
| `feed_conversion_ratio` | number | unitless | Declared outcome 3. Feed eaten by that fish divided by the mass it gained, from the tagged feeding records. Recorded to two decimals. Lower values mean the fish converted feed more efficiently. |
| `fillet_lipid_pct` | number | percent of wet mass | Declared outcome 4. Lipid content of the fillet sampled from that fish. Recorded to one decimal. |
| `hepatosomatic_index_pct` | number | percent of body mass | Declared outcome 5. Liver mass of that fish expressed as a percent of its body mass. Recorded to two decimals. |
| `diet` | text | none | The diet group the fish was fed. Exactly two distinct values: `fishmeal` (conventional fishmeal-based diet) and `insect_meal` (diet with a large share of the fishmeal replaced by insect meal). Forty rows each. |

The five outcome columns appear in the order the outcomes were declared in the trial plan.

## How the values were made

Each fish is drawn from its own diet group's typical level for every outcome, with individual
scatter around that level. Within a fish the five outcomes share one latent growth-performance
draw, so a fish that is heavier also tends to grow faster, convert feed more efficiently (lower
feed conversion ratio), and carry slightly more fillet lipid. On top of that shared part each
outcome carries its own independent scatter. Values are rounded as a hatchery record sheet would
round them.
