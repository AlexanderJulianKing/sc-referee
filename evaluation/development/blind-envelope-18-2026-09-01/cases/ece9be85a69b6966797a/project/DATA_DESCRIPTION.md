# data.csv

Seven-day duckweed (common duckweed, *Lemna*) growth assay. Forty-eight culture
vessels were set up from one clonal stock and held in the same growth cabinet.
Twenty-four vessels held standard reference growth medium and twenty-four held
the same medium made up with ten percent treated municipal wastewater effluent.
Each vessel was measured once, at day seven.

**One row is one culture vessel**, carrying its medium assignment and its
day-seven value for each of the five outcomes declared in the assay plan. The
file has 48 data rows plus a header. There are no missing values.

## Columns

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `vessel_id` | text | none | Vessel label, `V01` through `V48`. Unique; identifies the culture vessel. |
| `medium` | text | none | Growth medium the vessel received. Exactly two values: `reference_medium` (standard reference growth medium) and `effluent_10pct` (the same medium made up with ten percent treated municipal wastewater effluent). 24 vessels each. |
| `frond_number_increase` | integer | none (count) | Increase in frond number over the seven days, counted. |
| `total_frond_area_mm2` | number | mm² | Total frond area at day seven, in square millimetres, to one decimal place. |
| `chlorophyll_a_ug_per_g` | number | µg/g fresh mass | Chlorophyll a content at day seven, in micrograms per gram of fresh mass, to one decimal place. |
| `mean_root_length_mm` | number | mm | Mean root length at day seven, in millimetres, to one decimal place. |
| `dry_biomass_mg` | number | mg | Dry biomass at day seven, in milligrams, to two decimal places. |

The outcome columns appear in the order the five outcomes were declared in the
assay plan.

## Provenance

`data.csv` is a fixed authored file. It was written once by `make_data.py`
(seeded, in this staging directory) and is not regenerated or simulated by any
analysis code.
