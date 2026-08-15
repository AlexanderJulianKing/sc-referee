# Fouling inspection log: moored sensor housings

Eighteen oceanographic sensor housings were deployed on their own moorings across
the Kelso Bank shelf array for one summer. Nine carry the yard-standard epoxy
finish and nine carry an experimental silicone-hydrogel topcoat, assigned before
deployment; a housing keeps its coating for the whole season. A diver visited each
housing once a month, four times in all, and photographed the same shoulder panel;
an image analyst later scored the percentage of that panel covered by biofilm.

Columns:

- housing_id: label of the physical housing (H01 through H18). Each housing sits on
  its own mooring and is the independently deployed thing being studied.
- coating: the finish that housing carries, either epoxy_control or
  silicone_hydrogel. Constant within a housing.
- month_index: which monthly inspection this row records, 0 through 3.
- water_temp_c: water temperature in degrees Celsius measured at that inspection.
- biofilm_cover_pct: percentage of the photographed panel covered by biofilm at
  that inspection.

The file is in long format, so the four rows sharing a housing_id are four repeated
looks at the same mooring rather than four separate moorings. They describe how
fast that one housing fouled; they do not add four independent cases to a
comparison between coatings. Anything compared across coatings has to be built from
one summary value per housing.

One row is: one monthly dive inspection of one moored sensor housing
Independent unit column: housing_id
