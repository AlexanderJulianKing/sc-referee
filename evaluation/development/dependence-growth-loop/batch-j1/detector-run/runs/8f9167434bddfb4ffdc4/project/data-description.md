# What this table records

The single-cell-protein pilot line ran twenty bench fermentations. Each run
used one 2-liter methanotroph bioreactor: the vessel was filled with one of two
growth media, inoculated once, fed simulated biogas for 96 hours, harvested
once, assayed once for crude protein, and then stripped and retired. No vessel
was reused, and no vessel was sampled or assayed more than once.

One row is: one bioreactor vessel, run once from inoculation to harvest, together with its single end-of-run protein titer
Independent unit column: vessel_id

Columns:

- vessel_id: the vessel label. It is unique across the file, so the twenty
  labels correspond to twenty distinct pieces of hardware and twenty rows.
- medium: which growth medium that vessel received, either "baseline" or
  "cu_amended" (the copper-supplemented formulation). The medium was chosen
  vessel by vessel before inoculation, ten vessels per medium.
- seed_od600: optical density of the inoculum at 600 nm at the moment of
  seeding, kept as a provenance record of how heavily the vessel was started.
- final_titer_g_per_l: crude protein measured in the harvested broth, in grams
  per liter, from the single end-of-run assay for that vessel.

Because treatment assignment, the run itself, and the measurement all happen at
the level of the vessel, and because each vessel shows up exactly once, the
twenty rows are twenty independent observations: ten under the baseline medium
and ten under the copper-amended medium. Comparing the two media therefore
means comparing two independent groups of ten vessels.
