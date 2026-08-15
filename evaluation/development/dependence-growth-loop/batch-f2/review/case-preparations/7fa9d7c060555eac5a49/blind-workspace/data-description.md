# What is in data/input.csv

The file records a single outdoor mesocosm experiment run over one summer
season at a freshwater field station. Twenty-four garden ponds of roughly one
thousand litres were filled from the same source water, stocked once with a
founder population of Daphnia pulex, and assigned to one of two canopy
treatments: "shaded", in which a floating duckweed mat was left to cover the
surface, or "open", in which the mat was skimmed off each week. At the close
of the season every pond was scored a single time, as "persisted" if a
reproducing Daphnia population was still present and "collapsed" otherwise.

One row is: one outdoor mesocosm pond, with its assigned canopy treatment and its single end-of-season persistence outcome
Independent unit column: pond_id
One trial is: one row

Columns:

- pond_id: the pond label; unique across the file, so each pond appears once
- canopy: the assigned treatment, either "shaded" or "open"
- volume_l: working volume of the pond in litres
- stocking_density_per_l: founder Daphnia stocked per litre at the start
- mean_surface_temp_c: mean surface temperature over the season, degrees Celsius
- outcome: "persisted" or "collapsed" at the end-of-season scoring

The ponds stood apart from one another, were filled and stocked separately,
and never exchanged water, so the 24 rows are 24 independent units and no pond
supplies more than one outcome. Volume, stocking density and mean surface
temperature are recorded as context; they describe the pond as a whole and are
not repeated measurements within a pond.
