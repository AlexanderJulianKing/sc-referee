# What this dataset records

Each line of data/input.csv describes one laboratory oviposition assay of a
single mated Drosophila suzukii female (spotted-wing drosophila). A female was
released alone into her own small arena that held two fruit options side by
side: one intact ripening raspberry and one wounded, overripe raspberry. She was
then watched for 24 hours, and the fruit that received her very first egg was
written down. When the 24 hours were over the female was removed and never
tested again.

The columns are:

- female_id: the code for the individual female that was tested. Every code in
  the file appears exactly once.
- cohort: which of the two rearing batches, A or B, the female came from.
- age_days: how many days old the female was on the day she was assayed.
- arena_id: the code for the arena she was tested in. Each arena hosted exactly
  one female, so arena and female never get mixed together.
- wing_length_mm: the length of the female's wing in millimetres, used here as a
  simple measure of body size.
- latency_min: the number of minutes between release into the arena and the
  moment she laid her first egg.
- total_eggs_24h: the total number of eggs she laid across the whole 24 hour
  window, counted on both fruits together.
- first_egg_substrate: which fruit got her first egg, written as "ripe" for the
  intact ripening raspberry or "overripe" for the wounded overripe one.

Because every female was tested once and only once, in her own arena, the file
contains exactly one measurement per animal. Nothing in the file is a repeated
reading of an animal that already appears somewhere else, so the rows can be
counted as separate replicates without any further grouping.

One row is: one complete 24 hour two-choice oviposition assay of a single mated Drosophila suzukii female, tested once in her own arena
Independent unit column: female_id
