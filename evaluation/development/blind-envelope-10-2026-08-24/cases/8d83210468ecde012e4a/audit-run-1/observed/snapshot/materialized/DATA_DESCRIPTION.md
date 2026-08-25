# Data description

Winter wheat fungicide programme trial, one site, 144 individually tagged plants.

## Files

### `make_data.py`

Deterministic seeded generator (fixed seed `20260824`, NumPy `default_rng`). Running it with the
project interpreter rewrites `wheat_fungicide_trial.csv` with identical contents.

### `wheat_fungicide_trial.csv`

144 data rows plus one header row. **One row is one tagged wheat plant**, holding that plant's
fungicide programme, its pre-assigned study half, and its six end-of-season measurements. Every cell
is filled; there are no missing values and no repeated measurements per plant.

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `plant_id` | text | — | Field tag of the plant, `WW-001` to `WW-144`, unique, in field walking order |
| `program_group` | text | — | Fungicide programme the plant received. Exactly two values: `single_spray` (one spray at flag leaf emergence) and `two_spray` (an earlier stem extension spray added to that flag leaf spray). 72 plants per value |
| `stage_split` | text | — | Study half the plant was allocated to in advance, before any measurement. Exactly two values: `discovery` and `validation`. 72 plants per value, and 36 plants from each programme inside each half |
| `grain_yield_g` | number | grams per plant | Grain harvested from that plant, 2 decimal places |
| `tgw_g` | number | grams | Thousand grain weight for that plant's grain sample, 1 decimal place |
| `septoria_severity_pct` | number | percent leaf area | Septoria tritici blotch severity assessed on that plant's flag leaf, 1 decimal place |
| `green_canopy_days` | number | days | Green canopy duration for that plant, 1 decimal place |
| `plant_height_cm` | number | centimetres | Height of that plant at maturity, 1 decimal place |
| `spike_count` | integer | count | Number of fertile spikes on that plant |

Observed spans in the file: grain yield 8.72 to 25.56 g, thousand grain weight 37.0 to 48.9 g,
septoria severity 0.4 to 53.5 percent, green canopy duration 21.8 to 43.3 days, plant height 66.7 to
97.8 cm, fertile spikes 2 to 7.

## How the values were produced

Each simulated plant carries two hidden traits: a vigour term (establishment, tillering, soil) and a
disease pressure term (inoculum and canopy microclimate at that plant). The six recorded outcomes are
built from those two traits plus a programme effect, so measurements on the same plant move together
the way field measurements do: more vigorous plants are taller, carry more spikes and yield more;
more diseased plants keep less green canopy and yield less; plants carrying many spikes have slightly
lighter individual grains. Programme effects were placed on some outcomes and not others, and the
same pattern was generated in both study halves, since the `stage_split` allocation is drawn
independently of every measured value.
