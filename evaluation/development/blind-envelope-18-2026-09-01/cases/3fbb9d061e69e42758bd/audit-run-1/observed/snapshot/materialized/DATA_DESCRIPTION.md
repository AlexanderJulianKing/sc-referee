# data.csv

Sediment cores from a coastal mangrove survey. A twelve-year-old restored stand and an adjacent
undisturbed natural stand of the same species were sampled on the same shoreline during a single
survey. Forty-eight cores were taken to 30 centimetres depth, twenty-four in each stand, and each
core was analysed once in the laboratory.

## What one row represents

One row is one sediment core: its identifier, the stand it came from, and the three laboratory
measurements made on that core. There are 48 rows plus a header row, and no blank values.

## Columns

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `core_id` | text | none | Identifier for the sediment core. Unique across the file. Cores from the restored stand are numbered `R01` through `R24`; cores from the natural stand are numbered `N01` through `N24`. |
| `stand_type` | text | none | Which stand the core came from. Exactly two values: `restored` for the twelve-year-old restored stand, `natural` for the adjacent undisturbed natural stand. Twenty-four rows carry each value. |
| `organic_carbon_pct` | number | percent of dry mass | Sediment organic carbon in the core, as a percentage of dry mass. Recorded to two decimal places. |
| `bulk_density_g_cm3` | number | grams per cubic centimetre | Dry bulk density of the core. Recorded to three decimal places. |
| `total_nitrogen_mg_g` | number | milligrams per gram of dry sediment | Total nitrogen in the core. Recorded to two decimal places. |

The three measurement columns appear in the order the survey plan declared the outcomes: organic
carbon first, then bulk density, then total nitrogen.
