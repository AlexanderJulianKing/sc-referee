# What is in data/input.csv

Every hawkmoth in this study was captured, given a unique mark, measured once,
released once into the Y-tube choice arena, scored, and then let go. No animal
entered the arena a second time, so the file is simply a list of animals, each
with the single choice it made.

One row is: one wild-caught hawkmoth tested a single time in the Y-tube choice arena
Independent unit column: moth_id
One trial is: one row

Columns:

- `moth_id`: the unique mark code painted on the thorax; each code appears once.
- `sex`: female or male, scored from the antennae at capture.
- `forewing_length_mm`: right forewing length in millimetres, measured once at
  capture, before the trial.
- `amber_arm_position`: which arm of the Y held the amber lamp during that
  animal's trial, left or right; the two positions were counterbalanced across
  animals so that a side bias could not masquerade as a colour preference.
- `chosen_spectrum`: the lamp the animal walked toward, amber or white. This is
  the single outcome the analysis counts.

Because one animal supplies exactly one yes/no outcome, the twenty rows are
twenty independent Bernoulli trials and can be fed directly into a procedure
that assumes independent rows.
