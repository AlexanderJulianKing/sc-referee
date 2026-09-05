# Data description

**File:** `green_roof_survey.csv`

**What one row represents:** one surveyed green roof. Each of the 44 extensive green
roofs in the city survey appears exactly once, visited once in late summer, with all
five declared outcome variables measured on that visit. There are no repeated visits
and no missing values, so the table is 44 rows by 7 columns with every cell filled.

## Columns

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `roof_id` | text | none | Short identifier for the roof, `GR01` through `GR44`, following survey visit order. Unique per row. |
| `substrate_depth` | text | none | Substrate depth class the roof was built to. Exactly two values: `shallow` (growing substrate about 60 mm, 22 roofs) and `deep` (about 120 mm, 22 roofs). |
| `plant_richness_count` | integer | count of species | Vascular plant species richness: number of vascular plant species recorded on the roof. |
| `veg_cover_pct` | number | percent | Vegetation cover as a percentage of the roof area. |
| `substrate_moisture_pct` | number | percent | Substrate volumetric moisture during the survey week, as a percentage. |
| `temp_reduction_c` | number | degrees Celsius | Midday surface temperature reduction measured against the adjacent bare roof membrane. Positive values mean the vegetated surface was cooler. |
| `invert_abundance_count` | integer | count of individuals | Flying invertebrate abundance from a standard 30 minute sticky-trap catch. |

The five outcome columns appear in the order the survey declared them in advance:
species richness, vegetation cover, substrate moisture, temperature reduction, then
invertebrate abundance.

## Notes

- `substrate_depth` is the grouping variable, and the two depth classes are balanced
  at 22 roofs each.
- Roof identifiers are not sorted by depth class, because they follow the order roofs
  were visited rather than how they were built.
- All measurements are per roof and cross-sectional. Nothing in the table is paired,
  repeated, or aggregated across roofs.
