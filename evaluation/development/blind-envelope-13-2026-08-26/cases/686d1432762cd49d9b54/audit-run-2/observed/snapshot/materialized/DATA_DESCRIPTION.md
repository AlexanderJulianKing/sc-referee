# Data description

File: `penguin_chick_condition.csv`

One row is one Adelie penguin chick, measured once at about 25 days of age. The file
holds 48 chicks (plus a header row): 25 from the near sub-colony and 23 from the far
sub-colony of a single breeding site. Every chick has a value in every column; there
are no blank cells.

## Columns

| Column | Meaning | Unit |
| --- | --- | --- |
| `chick_id` | Identifier for the chick, unique across the file (`AP001`–`AP048`) | none (text label) |
| `sub_colony` | Which sub-colony the chick belongs to. Exactly two values: `near` (adults forage a short distance away) and `far` (adults commute much further) | none (group label) |
| `body_mass_g` | Body mass of the chick | grams (g) |
| `flipper_length_mm` | Flipper length of the chick | millimetres (mm) |
| `haemoglobin_g_dl` | Blood haemoglobin concentration | grams per decilitre (g/dL) |
| `corticosterone_ng_ml` | Plasma corticosterone concentration | nanograms per millilitre (ng/mL) |

The four outcome columns appear in the order declared in the study plan: body mass,
flipper length, haemoglobin, corticosterone.

## Notes

- Values are invented but chosen to be plausible for wild chicks of this age.
- Rows are not sorted by sub-colony; the two groups are interleaved.
- Recorded precision: body mass whole grams, flipper length one decimal place,
  haemoglobin one decimal place, corticosterone two decimal places.
