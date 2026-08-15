# Proglacial stream carbon dataset

The file `data/input.csv` holds one record per proglacial stream in a survey of glaciated headwater catchments in a single mountain range. Twenty-four streams were visited twice during the same melt year, early in the season (June) and late in the season (September). Both visit values sit side by side in the same record, so a stream never occupies more than one line of the file.

One row is: one proglacial stream, carrying its catchment descriptors together with its single June and its single September dissolved organic carbon measurement
Independent unit column: stream_code
One trial is: one row

Columns:

- `stream_code` - unique label for the stream and the catchment it drains; no code repeats anywhere in the file.
- `catchment_area_km2` - drainage area upstream of the sampling point, in square kilometres.
- `glacier_cover_pct` - percentage of the catchment surface still under ice.
- `mean_elev_m` - area-weighted mean elevation of the catchment, in metres.
- `doc_june_mg_per_l` - dissolved organic carbon measured at the June visit, in milligrams per litre.
- `doc_sept_mg_per_l` - dissolved organic carbon measured at the September visit, in milligrams per litre.

The two visits to a stream are repeated measurements of the same unit, so the analysis first subtracts them into one signed change per stream and then tests those twenty-four changes. The paired values are never entered into the test as separate observations, and the number of trials in the test equals the number of streams.

The catchments are hydrologically separate: none drains into another, they were sampled on independent field days, and no site is represented by more than one stream. Coding of the outcome is simply the direction of the seasonal change, positive when September exceeds June.
