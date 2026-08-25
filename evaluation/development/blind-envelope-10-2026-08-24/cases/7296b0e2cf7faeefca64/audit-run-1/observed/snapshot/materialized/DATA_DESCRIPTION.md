# Data description

## Files

| File | Role |
| --- | --- |
| `make_data.py` | Deterministic seeded generator (fixed seed `20260824`). Running it writes `calves.csv`. |
| `calves.csv` | The analysis input: one record per reindeer calf in the feeding trial. |

## `calves.csv`

Comma-separated, UTF-8, one header row followed by 78 data rows.

**What one row represents:** one first-winter reindeer calf that completed the
ten-week corral supplementary feeding period, with its assigned feed pellet and
its three end-of-period measurements. Each calf appears exactly once. Calves are
fed and measured individually, so rows are separate animals rather than pens or
groups. There are no empty cells.

### Columns

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `calf_id` | text | none | Ear-tag identifier of the calf, formatted `RC-001` through `RC-078`. Unique across the file. |
| `feed_group` | text | none | Which supplementary pellet the calf was fed for the ten weeks. Exactly two values: `pellet_established` (the station's current pellet) and `pellet_new` (the new protein and lichen-substitute blend). 39 calves in each. |
| `daily_gain_g_per_day` | number, 1 decimal | grams per day | Average daily body weight gain over the ten-week feeding period, that is, the calf's total weight change divided by the number of days on feed. Values in this file run from about 156 to about 415. |
| `serum_urea_mmol_l` | number, 2 decimals | millimoles per litre | Serum urea concentration from the blood sample taken at the end of the feeding period. Values in this file run from about 2.1 to about 7.2. |
| `haematocrit_pct` | number, 1 decimal | percent | Haematocrit (packed red cell volume as a percentage of whole blood) from the same end-of-period blood sample. Values in this file run from about 32.6 to about 47.9. |

### How the values were produced

`make_data.py` draws each calf's three measurements from normal distributions
with group-specific means and standard deviations chosen to sit inside the
physiological ranges above. A single per-calf latent condition term (standing in
for entry body condition, appetite and dam quality) is shared across the three
outcomes, so a calf that does well on one measure tends to sit slightly high on
the others. Group allocation is a shuffled balanced split, 39 and 39, so the feed
group is not tied to ear-tag order. Draws are clipped to the plausible bounds
listed above before rounding.
