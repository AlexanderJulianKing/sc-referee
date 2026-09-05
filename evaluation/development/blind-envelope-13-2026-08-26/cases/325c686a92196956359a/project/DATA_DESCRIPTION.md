# Data description

File: `elephant_enrichment_welfare.csv`

## What one row represents

One row is one captive Asian elephant. Each elephant took part in exactly one of the two
enrichment programmes, was observed over a single four-week block, and the whole block was
summarised into one value per outcome. The file holds 34 elephants (34 data rows plus a header
row), 17 on each programme, drawn from several facilities. There are no repeated measures and no
blank cells: every elephant has a value in every outcome column.

## Columns

Columns appear in this order. The two identifier columns come first, then the six outcomes in the
order they were declared in the study protocol.

| Column | Meaning | Unit |
| --- | --- | --- |
| `animal_id` | Study identifier for the individual elephant. Format `EL-<facility code>-<number>`; unique across the file. | none (text label) |
| `enrichment_group` | Which enrichment programme the elephant was on. Exactly two distinct values: `scatter_feeding` (forage dispersed unpredictably through the habitat during the day) and `fixed_station` (forage presented at set points and set times). | none (text label) |
| `stereotypic_behaviour_pct` | Stereotypic behaviour, such as weaving or pacing, counted as a share of scan samples in which it was seen. | percent of scan samples |
| `daily_walking_distance_km` | Mean distance walked per day over the observation block. | kilometres per day |
| `night_recumbent_rest_min` | Mean time per night spent lying down at rest. | minutes per night |
| `faecal_glucocorticoid_metabolites_ng_per_g` | Mean concentration of faecal glucocorticoid metabolites, a stress-hormone breakdown product measured in dung. | nanograms per gram of dry faeces |
| `feeding_bout_duration_min` | Mean total time per day spent in feeding bouts, summed across all bouts in the day. | minutes per day |
| `social_proximity_pct` | Social proximity, counted as the share of scan samples in which the elephant was within one body length of another elephant. | percent of scan samples |

## Provenance

The measurements are invented for this exercise, not collected from real animals. They were
produced by `make_data.py` in this directory with a fixed random seed, drawing each outcome from a
normal distribution around a per-programme mean and clipping to a plausible range for captive
Asian elephants. Decimal precision matches how each measure is usually reported: whole minutes for
the two duration columns, one decimal for the percentage and hormone columns, two decimals for
walking distance.
