# Chitin harvest survey for strain MX-7

Twelve bench-scale bioreactors were inoculated with the filamentous fungus
strain MX-7. Six vessels were run on a lignin-rich substrate blend and six on a
starch-rich blend; the blend was fixed for the whole run of a vessel. Every
vessel was sampled on the same five days after inoculation (days 3, 6, 9, 12
and 15), and the chitin content of the harvested dry biomass was measured for
each sample.

One row is: one harvest sample drawn from one bioreactor on one harvest day
Independent unit column: vessel_id

Columns

- vessel_id: label of the bioreactor the sample came from, BR-01 through BR-12. Each vessel contributes five rows, one per harvest day.
- substrate: the substrate blend fed to that vessel, either lignin_blend or starch_blend. Vessels BR-01 to BR-06 ran on the lignin blend and BR-07 to BR-12 on the starch blend.
- harvest_day: number of days after inoculation at which the sample was drawn (3, 6, 9, 12 or 15).
- chitin_mg_per_g: measured chitin content of the harvested dry biomass, in milligrams per gram.

The substrate blend was assigned to whole vessels rather than to individual
samples, so the five rows sharing a vessel_id are repeated measurements of the
same culture rather than separate cultures. Vessels differ noticeably from one
another in their overall chitin level, while the five samples from a single
vessel sit close together.
