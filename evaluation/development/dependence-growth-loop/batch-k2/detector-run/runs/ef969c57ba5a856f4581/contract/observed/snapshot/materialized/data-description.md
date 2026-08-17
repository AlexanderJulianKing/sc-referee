# Night-time noise on resurfaced street segments

data/input.csv is the field record of a porous-asphalt resurfacing programme in
one mid-sized city. Twenty-four residential street segments were resurfaced
during a single construction season. The segments were chosen so that they sit
in different parts of the road network: no two of them share a carriageway, a
junction, or a traffic corridor, and none of them was resurfaced twice.

One row is: one resurfaced street segment, with its week-long night-time noise level before the works and its week-long night-time noise level after the works
Independent unit column: segment_id
One trial is: one row

Columns:

- segment_id: the site label, unique across the file (S01 to S24).
- street_name: the street the segment lies on, given for orientation only.
- resurfaced_length_m: length of carriageway resurfaced, in metres.
- lanes: number of traffic lanes on the segment.
- pre_lnight_db: the L_night noise indicator before resurfacing, in dB(A). The
  logger ran for one full week and the whole week was condensed on site into
  this single energy-averaged figure, so the file stores one number rather than
  the individual nights.
- post_lnight_db: the same indicator for one full week after resurfacing,
  measured with the same logger at the same position on the segment.

Because each week of logging is already averaged into a single number, every
segment supplies exactly one paired row and nothing more, and the number of
rows in the file equals the number of independent sites in the study. Nothing
in the file marks a larger grouping: there is no shared block, contractor
batch, or district column that would tie several rows back to the same site.
Street names are all distinct, and the identifiers do not repeat.
