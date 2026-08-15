# Sourdough starter acidity study

Twelve sourdough starter jars were kept side by side in a single incubator held at
26 C. Six of the jars were refreshed with wholegrain rye flour and six with white
wheat flour. Apart from the flour, every jar got the same hydration, the same
starting mass and the same 24 h refresh schedule.

At the end of the 24 h window a technician drew four separate aliquots out of each
jar and titrated every aliquot with 0.1 M NaOH to the phenolphthalein endpoint,
writing down the volume of base in millilitres. The four aliquots taken from one jar
are four measurements of the same batch of starter, not four separate batches.

Columns in the file:

- jar_id: label of the starter jar the aliquot came from; R01-R06 are the rye jars
  and W01-W06 are the wheat jars
- flour_type: refresh flour used for that jar, either rye or wheat
- starter_age_d: age of the starter culture, in days, at the time of the refresh
- aliquot: which of the four aliquots from that jar this row records, numbered 1 to 4
- acidity_ml: titratable acidity of that aliquot, in mL of 0.1 M NaOH

One row is: one titration of one aliquot drawn from one starter jar
Independent unit column: jar_id
