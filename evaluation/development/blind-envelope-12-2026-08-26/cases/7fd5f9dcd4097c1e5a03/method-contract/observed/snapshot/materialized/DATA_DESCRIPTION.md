# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Deterministic seeded generator (seed `20260826`, Python standard library only). Running it writes `panel_data.csv` next to itself, with the same values every time. |
| `panel_data.csv` | The sensory panel data table used as the analysis input. UTF-8, comma separated, one header row and 60 data rows. |

## `panel_data.csv`

### What one row represents

One row is one consumer panellist: a single trained-naive panellist who tasted
exactly one of the two oat drink formulations, blind under red light, in the
single session, together with the five ratings that panellist gave for that
sample immediately after tasting. A panellist appears in exactly one row and
contributes ratings for exactly one formulation. The panellist is the unit of
the study, so the 60 rows are 60 different people: 30 who tasted the current
formulation and 30 who tasted the reformulation.

### Columns

Columns appear in this order, with the five outcome columns in the declared
sensory-plan order. There are no blank cells: every panellist has a value in
every outcome column.

| Column | Holds | Unit / scale |
| --- | --- | --- |
| `panellist_id` | Panellist identifier | Text code `P01` through `P60`, one per panellist, unique across the file |
| `group` | Which formulation this panellist tasted | Text, exactly two possible entries: `current` (current formulation) and `reformulation` (reformulated enzyme treatment) |
| `overall_liking` | Overall liking of the sample | Nine-point hedonic scale, whole numbers 1 to 9 (1 = dislike extremely, 9 = like extremely) |
| `sweetness` | Sweetness intensity | Unstructured line scale scored 0 to 100, read to one decimal place (0 = none, 100 = extremely intense) |
| `thickness` | Thickness in the mouth | Unstructured line scale scored 0 to 100, read to one decimal place (0 = very thin, 100 = very thick) |
| `cereal_off_note` | Cereal off-note intensity | Unstructured line scale scored 0 to 100, read to one decimal place (0 = none, 100 = extremely intense) |
| `purchase_intent` | Purchase intent for the sample | Seven-point scale, whole numbers 1 to 7 (1 = definitely would not buy, 7 = definitely would buy) |

### Value conventions

- `overall_liking` and `purchase_intent` are box scales, so their values are
  whole numbers only and sit at the scale ends when a panellist rates at the
  top or bottom box.
- `sweetness`, `thickness` and `cereal_off_note` come from ruled line scales, so
  their values carry one decimal place and can fall anywhere from 0.0 to 100.0.

### Counts in the file as written

| Group | Rows |
| --- | --- |
| `current` | 30 |
| `reformulation` | 30 |
| Total | 60 |
