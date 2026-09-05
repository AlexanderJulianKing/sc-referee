# Data description

## File

`lichen_biomonitoring.csv` — one file, comma separated, with a header row and 64 data rows.

## What one row represents

One row is one sampled lime tree. Each tree is one subject. A row holds that tree's identifier,
the setting it stands in, and the six declared outcome values from the single composite lichen
thallus sample taken from its trunk at the standard height, together with the trunk cover reading
from the fixed survey quadrat on that same trunk.

Sixty-four mature lime trees of similar age and girth were sampled: 32 in the `roadside` setting
and 32 in the `park_interior` setting. Every tree has a value in every column. There are no
missing cells, no repeated trees, and no extra rows.

## Columns

Columns appear in this order. The six outcome columns are in the order the survey plan declared
them.

| Column | Type | Unit | Recorded to | Description |
| --- | --- | --- | --- | --- |
| `tree_id` | text | — | — | Tree identifier: the prefix `LT` (lime tree) plus a zero-padded two-digit serial number, `LT01` through `LT64`. Unique for every row. |
| `setting` | text | — | — | Group column. Exactly two distinct values: `roadside` for a tree standing within 15 m of the busy arterial road, and `park_interior` for a tree standing inside large parkland at least 300 m from any road carrying traffic. |
| `nitrogen_pct` | number | percent of dry mass | 0.01 | Declared outcome 1. Nitrogen content of the thallus sample. |
| `sulfur_pct` | number | percent of dry mass | 0.001 | Declared outcome 2. Sulfur content of the thallus sample. |
| `lead_mg_kg` | number | mg per kg dry mass | 0.1 | Declared outcome 3. Lead concentration in the thallus sample. |
| `zinc_mg_kg` | number | mg per kg dry mass | 0.1 | Declared outcome 4. Zinc concentration in the thallus sample. |
| `chla_phaeo_ratio` | number | unitless ratio | 0.01 | Declared outcome 5. Chlorophyll a to phaeophytin ratio, a vitality index. Lower values mean more degraded pigment. |
| `lichen_cover_pct` | number | percent of quadrat area | 1 | Declared outcome 6. Lichen cover on the trunk as a percentage of the fixed survey quadrat area, recorded as a whole percent. |

## Ranges present in the file

These are file-wide ranges across all 64 trees, given so a reader can check the CSV parsed
correctly. They are not a comparison between the two settings.

| Column | Minimum | Maximum |
| --- | --- | --- |
| `nitrogen_pct` | 0.58 | 2.03 |
| `sulfur_pct` | 0.031 | 0.134 |
| `lead_mg_kg` | 2.2 | 10.3 |
| `zinc_mg_kg` | 21.8 | 97.4 |
| `chla_phaeo_ratio` | 0.49 | 1.43 |
| `lichen_cover_pct` | 9 | 49 |

## Notes

- Row order follows the tree identifier, `LT01` upward. The two settings are interleaved in that
  order rather than blocked, so a reader must use the `setting` column and never row position to
  tell the groups apart.
- The values are fixed and committed in the CSV. Nothing in the file is recomputed at analysis
  time.
- `make_data.py` in this directory is the generator that produced the committed CSV. It is a
  build-time helper, not part of the analysis.
