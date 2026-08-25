# Data description

## Files

| File | Role |
| --- | --- |
| `make_data.py` | Deterministic seeded generator (seed `20260824`). Running it rewrites the CSV below with identical contents. |
| `sorghum_nitrogen_plants.csv` | The analysis input: the plant-level field sample. |

## `sorghum_nitrogen_plants.csv`

Grain sorghum sampled at physiological maturity on a single uniform field site at
one agronomy station, under two nitrogen fertiliser rates. Seventy-two
individually tagged plants were harvested and measured one plant at a time:
36 at 60 kg N/ha and 36 at 120 kg N/ha.

**One row is one harvested sorghum plant.** Each row carries that plant's tag,
the nitrogen rate it was grown under, and its four agronomic measurements. Each
outcome was measured once on that plant. The file has 72 data rows plus a header
row, and no empty cells.

### Columns

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `plant_id` | text | none | Tag on the individual plant, `SB001` through `SB072`. Unique across the file. |
| `n_rate_group` | text | none | Nitrogen fertiliser rate the plant was grown under. Exactly two values: `n60` (60 kg N/ha, 36 plants) and `n120` (120 kg N/ha, 36 plants). |
| `grain_yield_g` | number, 1 decimal | grams per plant | Clean, dried grain harvested from that plant. Observed range 43.7 to 103.1. |
| `panicle_length_cm` | number, 1 decimal | centimetres | Length of that plant's panicle (the grain head). Observed range 20.4 to 32.2. |
| `stem_brix_pct` | number, 1 decimal | degrees Brix | Sugar content of the juice pressed from that plant's stem. Observed range 8.4 to 17.9. |
| `plant_height_cm` | number, 1 decimal | centimetres | Height of that plant from soil surface to the panicle tip. Observed range 129.4 to 194.1. |

Rows are stored in plant-tag order, so the 36 `n60` plants come first and the
36 `n120` plants follow.

### How the values were produced

`make_data.py` draws each outcome from a normal distribution whose mean and
spread depend on the nitrogen rate, then clips values to the plausible
agronomic window for that measurement and rounds to one decimal place. Every
plant also carries a hidden vigour term that is shared by all four of its
outcomes, so within a group a plant that is taller also tends to carry a longer
panicle and set more grain, the way real field plants do. Measurement noise is
drawn independently for each outcome on top of that shared term.
