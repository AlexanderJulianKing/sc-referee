# Data description

## File

`hares.csv` — 64 data rows plus one header row, comma separated, no missing values.

## What one row represents

One row is one adult European hare, live-trapped once in late winter on farmland,
measured and sampled at the trap site, then released. Each hare appears exactly
once. There are 64 hares: 32 caught on mixed farmland carrying uncropped fallow
strips and 32 caught on intensively cropped arable land with no fallow. Every
hare has a value for all five outcomes.

## Columns

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `hare_id` | text | — | Short per-hare identifier, `H01` through `H64`, unique to one trapped hare. |
| `landscape` | text | — | Landscape the hare was caught in. Exactly two values: `mixed_farmland` (mixed farmland with uncropped fallow strips, 32 hares) and `intensive_arable` (intensively cropped arable land with no fallow, 32 hares). |
| `body_mass_kg` | number | kilograms | Body mass at capture, to two decimals. Observed values run from 2.80 to 4.40 kg. |
| `hind_foot_mm` | integer | millimetres | Hind foot length, measured to the nearest millimetre. Observed values run from 132 to 153 mm. |
| `cortisol_ng_g` | number | nanograms per gram dry faeces | Faecal cortisol metabolite concentration, to one decimal. Right-skewed; observed values run from 40.8 to 349.3 ng/g. |
| `haemoglobin_g_dl` | number | grams per decilitre | Blood haemoglobin concentration, to one decimal. Observed values run from 10.8 to 15.7 g/dl. |
| `egg_count_epg` | integer | eggs per gram of faeces | Gastrointestinal nematode egg count. Strongly right-skewed with some hares at zero; observed values run from 0 to 921 epg. |

The five outcome columns appear in the order the study declared them: body mass,
hind foot length, faecal cortisol metabolites, blood haemoglobin, nematode egg
count.

## Notes

- Rows are stored in trapping order, so the two landscape groups are interleaved
  rather than blocked.
- All columns are complete: there are no blank cells, no `NA` codes and no
  sentinel values standing in for missing measurements. A `0` in
  `egg_count_epg` is a real count of zero eggs, not a missing value.
