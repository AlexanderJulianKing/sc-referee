# Sourdough acidification data

Eight fermentation vessels were built for this bakery trial: four with
wholemeal rye flour and four with strong wheat flour. All eight were fed on the
same schedule from the same mother culture and held in one 26 C proofing
cabinet. Thirty-six hours after the final build, a calibrated probe measured pH
at four separate locations in each vessel's dough, so every vessel contributes
four readings to the file.

Columns:

- `vessel_id`: label of the fermentation vessel the reading came from (V01 to V08).
- `flour_type`: the flour that vessel was built with, either `rye` or `wheat`.
- `sample_point`: which of the four dough locations inside that vessel was probed (p1 to p4).
- `ph_36h`: the pH recorded at that location, 36 hours after the final build.

The file is 32 data rows plus a header. Values are plain ASCII, pH recorded to
two decimal places.

One row is: one pH reading taken at one dough location inside one fermentation vessel
Independent unit column: vessel_id
