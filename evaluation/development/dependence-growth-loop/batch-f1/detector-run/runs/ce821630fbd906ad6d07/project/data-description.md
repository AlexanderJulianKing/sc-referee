# Zebra finch song-tempo recordings

Twelve hand-raised male zebra finches were assigned at day 30 to one of two
rearing diets: a protein-supplemented mix (`supplemented`) or the standard
seed mix (`control`), six birds per diet. The diet was fixed once per bird
and never changed afterwards.

Between days 95 and 98 each bird was recorded alone in a sound-attenuated
chamber on four consecutive nights. For every night, an automatic
segmentation pass counted the complete song bouts and measured the average
syllable rate of that night's song.

The table is stored long: each bird appears four times, once per night. The
four records belonging to one bird are repeated measurements of the same
animal, not four separate animals.

One row is: one night of song recording from one bird
Independent unit column: bird_id

Columns

- bird_id: identifier of the bird (ZF-01 through ZF-17). The bird is what was
  assigned to a diet and the only level at which the records can be treated
  as independent of one another.
- diet_group: rearing diet of that bird, either `supplemented` or `control`.
  Constant across the bird's four rows.
- recording_night: 1 to 4, the consecutive night on which the recording was
  made.
- bout_count: number of complete song bouts detected that night.
- syllable_rate_per_s: mean syllables per second across that night's bouts.
- chamber_temp_c: air temperature in the recording chamber, degrees Celsius.

Any comparison between the two diets has to reduce each bird to a single
number first, for example the mean of its four nightly syllable rates. The 48
stored rows are 12 independent birds measured four times each, not 48
independent observations, and nightly values from the same bird overlap in
range with values from birds on the other diet even where the bird averages
do not.
