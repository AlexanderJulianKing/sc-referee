# Leaf thermal tolerance screen: what is in data/input.csv

The file records a heat-tolerance screen of two field-grown coffee cultivars,
Catuai and Obata, at a single research farm. Twelve shrubs were sampled, six per
cultivar. From each shrub, four leaves were cut, one from each of four canopy
positions (sun_upper, sun_mid, shade_mid, shade_lower). Every leaf went through
the same chlorophyll-fluorescence temperature ramp, and `tcrit_c` records the
critical temperature in degrees Celsius at which basal fluorescence begins to
rise steeply. Because four leaves come from each shrub, the file holds 48 rows
but only 12 shrubs; the four leaves sharing a shrub_id share that shrub's
genotype, soil, water status, and microclimate.

Columns:

- leaf_id: unique label for the individual leaf that was measured (L001-L048)
- shrub_id: label of the shrub the leaf was cut from (S01-S12)
- cultivar: Catuai or Obata
- block: field block the shrub grows in (north_slope or valley_floor)
- canopy_layer: canopy position the leaf came from
- tcrit_c: critical temperature of that leaf, in degrees Celsius

One row is: one leaf cut from one coffee shrub and put through a single temperature ramp
Independent unit column: shrub_id
