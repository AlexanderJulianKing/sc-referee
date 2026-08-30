# Data description

## File

`hedge_sections.csv` — 40 data rows plus one header row.

## What one row represents

One row is one surveyed farm hedge section: a 50 metre length of lowland farm hedge, surveyed once
in early winter and measured for all five outcomes. There are 40 sections in total, 20 cut every
year and 20 cut once every three years on rotation. Every section has a value for every outcome, so
there are no missing entries.

## Columns

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `section_id` | text | — | Short per-section identifier, `hs01` to `hs40`, unique to one hedge section. |
| `cut_regime` | text | — | Cutting regime the section is under. Exactly two values: `annual` (cut every year) and `rotational` (cut once every three years). 20 sections each. |
| `berry_mass_gpm` | number | grams per metre of hedge | Declared outcome 1. Autumn berry dry mass. |
| `stem_density_spm` | number | stems per metre of hedge | Declared outcome 2. Woody stem density measured at one metre height. |
| `plant_richness_spp` | integer | species count | Declared outcome 3. Vascular plant species richness in the hedge base. |
| `basal_gap_pct` | number | percent of section length | Declared outcome 4. Basal gap length: the share of the 50 m section with no woody cover below half a metre. |
| `invert_biomass_mgpm` | number | milligrams per metre of hedge | Declared outcome 5. Overwintering invertebrate biomass from a standard beating sample. |

Outcome columns appear in the pre-declared order 1 to 5. Rows are in survey order, so the two
cutting regimes are interleaved rather than blocked.

## Observed ranges in this file

| Column | Minimum | Maximum |
| --- | --- | --- |
| `berry_mass_gpm` | 10.4 | 96.0 |
| `stem_density_spm` | 7.1 | 18.2 |
| `plant_richness_spp` | 7 | 20 |
| `basal_gap_pct` | 3.5 | 32.8 |
| `invert_biomass_mgpm` | 14.7 | 137.5 |
