# Single-seed emergence trial for sagebrush-steppe restoration

Twenty-four nursery pots were filled from one batch of screened field soil, and
each pot received exactly one sulphur buckwheat (Eriogonum umbellatum) seed.
Every seed came from a different wild maternal plant, so no maternal plant is
represented twice. Half of the seeds were coated in a clay-and-compost pellet
before sowing; the other half were sown bare. All pots shared the same watering
schedule and were scored a single time, on day 28, for whether a seedling had
broken the soil surface.

Columns:

- pot_id: unique label for the pot (P01 through P24).
- maternal_plant_id: the wild plant that supplied the seed; every pot has a
  different one.
- seed_treatment: "pelleted" if the seed carried the clay-and-compost coating,
  "bare" otherwise.
- seed_mass_mg: mass of the sown seed in milligrams, weighed before sowing.
- emerged_by_day28: 1 if a seedling had emerged by day 28, 0 if not.

Each pot holds one seed, receives one treatment, and yields one yes/no outcome,
so nothing in the file is a repeated measurement of the same pot, seed, or
maternal plant. The comparison of interest is the emergence rate of pelleted
versus bare seed.

One row is: one nursery pot holding a single sown seed, scored once for seedling emergence at day 28
Independent unit column: pot_id
One trial is: one row
