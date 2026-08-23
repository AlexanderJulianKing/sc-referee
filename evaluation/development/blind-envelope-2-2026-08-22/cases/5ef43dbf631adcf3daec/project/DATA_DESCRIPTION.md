# Data description: greenhouse tomato mycorrhiza trial

## File

`greenhouse_tomato_yield.csv` — a plain comma-separated file with one header row and 48 data rows.
It is the only data file in this project. It was produced by `make_data.py` (Python standard library
only, fixed random seed `20260822`), so re-running that script reproduces the same file.

## What one row is

**One row is one whole tomato plant.** Each plant grew alone in its own pot, with its own substrate,
was watered and fertilised on its own, and was harvested once at the end of the season. Every plant
contributes exactly one row and appears exactly once. There is no repeated measurement of a plant,
and no plant shares a pot, tray, or block with any other plant.

Because treatment was applied to the individual plant at transplanting and the yield was measured on
that same individual plant, the plant is both the treated unit and the measured unit. So the number
of rows, the number of measurements, and the number of experimental units are all the same number.

## Counts

| Quantity | Value |
| --- | --- |
| Data rows (excluding header) | 48 |
| Plants (experimental units) | 48 |
| Rows per plant | 1 |
| Inoculated plants | 24 |
| Control plants | 24 |

## The two groups

The `treatment` column holds exactly two values:

- `inoculated` — 24 plants whose seedlings received the arbuscular mycorrhizal fungus inoculum at
  transplanting.
- `control` — 24 plants left uninoculated, otherwise handled identically.

Plants were assigned to a group at random at transplanting. Pot positions on the benches were
randomised at the start and re-randomised weekly; the `bench_position` column records the final
position of each pot, and every plant sits in its own slot.

## Columns

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `plant_id` | text | — | Unique label for the plant, `P01` through `P48`. Each label appears exactly once. |
| `treatment` | text | — | Inoculation group: `inoculated` or `control`. |
| `bench_position` | text | — | Final position of the pot, written as bench and slot, e.g. `B3-08`. Benches `B1`–`B4`, slots `01`–`12`, one plant per slot, 48 slots for 48 plants. |
| `height_cm_at_first_flower` | number | centimetres | Height of the plant, measured once when its first flower opened. One decimal place. |
| `marketable_fruit_count` | whole number | fruits | How many marketable fruits that plant produced over the whole harvest period. |
| `marketable_yield_g` | whole number | grams | The outcome. Cumulative fresh mass of marketable fruit from that plant, summed over the whole harvest period and recorded at the end of the season, rounded to the nearest gram. |

## How the values were generated

The values are simulated, not measured. `make_data.py` draws each plant's yield from a normal
distribution: mean 1820 g for controls and 2260 g for inoculated plants, with a standard deviation of
330 g among plants within each group. Height at first flower is drawn the same way (61 cm control,
65 cm inoculated, standard deviation 6 cm). Fruit count is that plant's yield divided by a per-plant
average single-fruit mass drawn around 118 g, rounded to a whole fruit, so counts and yields hang
together the way they would in a real harvest record.

The realised numbers in the file differ a little from those target settings, exactly as a real sample
of 24 plants would. As generated, the control group averages 1783.7 g with a standard deviation of
419.2 g, and the inoculated group averages 2146.6 g with a standard deviation of 380.8 g.
