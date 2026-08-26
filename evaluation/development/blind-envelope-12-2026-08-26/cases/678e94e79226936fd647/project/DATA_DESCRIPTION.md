# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Deterministic, seeded Python generator (standard library only, seed 20260826) that writes `urchin_feeding_trial.csv`. Re-running it reproduces the same CSV. |
| `urchin_feeding_trial.csv` | The trial data table: 36 data rows plus one header row. |

## `urchin_feeding_trial.csv`

**One row represents one adult purple sea urchin.** Each of the 36 urchins was
held on its own in a separate flow-through basket in a single raceway for ten
weeks, then measured and dissected once at the end of the trial. The values in a
row are that one animal's end-of-trial measurements. There are 18 urchins on the
fresh macroalgal feed and 18 on the manufactured pellet, and every urchin has a
value in every column; there are no blanks.

Columns, in file order:

| Column | Holds | Unit |
| --- | --- | --- |
| `urchin_id` | Identifier of the individual urchin, `U01` through `U36`. One identifier per basket, unique in the file. | none (text label) |
| `group` | Which finishing feed the urchin received. Exactly two entries occur: `macroalgae` for the chopped fresh macroalgal feed, `pellet` for the manufactured pellet. | none (text label) |
| `gonad_index_pct` | Gonad index: gonad wet mass expressed as a percentage of whole body wet mass. | percent |
| `gonad_colour_b` | Gonad colour, the b\* yellowness coordinate read from a handheld colorimeter. Higher values are more yellow. | unitless |
| `test_diameter_mm` | Test diameter, the widest across-the-shell measurement of the urchin. | millimetres |
| `body_mass_g` | Whole body wet mass of the urchin. | grams |
| `gonad_firmness_n` | Gonad firmness, the peak force recorded in a small probe compression test on the gonad. | newtons |

The five measurement columns appear in the order in which the trial declared its
outcomes: gonad index, gonad colour, test diameter, whole body wet mass, gonad
firmness.

### Value ranges in this file

| Column | Minimum | Maximum |
| --- | --- | --- |
| `gonad_index_pct` | 4.60 | 16.25 |
| `gonad_colour_b` | 25.2 | 44.6 |
| `test_diameter_mm` | 47.5 | 67.9 |
| `body_mass_g` | 67.0 | 126.8 |
| `gonad_firmness_n` | 1.36 | 3.91 |

Numbers are rounded as recorded: gonad index to two decimal places, colour,
diameter and mass to one decimal place, firmness to two decimal places.
