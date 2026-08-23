# Coral endosymbiont density survey, Tavuni back-reef system

Twelve tagged colonies of the massive coral *Porites lobata* were surveyed in a
single week: six colonies in the sheltered lagoon and six on the adjacent
forereef slope. Divers chipped four small nubbins (finger-sized fragments) off
each tagged colony, always from the upper, light-exposed surface. Each nubbin
was airbrushed in the field lab and its Symbiodiniaceae (endosymbiont) cells
were counted on a haemocytometer, then scaled to the nubbin's surface area.
The question of interest is whether lagoon colonies host denser endosymbiont
populations than forereef colonies.

One row is: one nubbin chipped from a tagged coral colony, together with the endosymbiont density counted for that nubbin
Independent unit column: colony_id

Columns

- `colony_id`: tag code of the coral colony the nubbin came from. Twelve
  colonies were tagged (LG-01 to LG-06 in the lagoon, FR-01 to FR-06 on the
  forereef) and each one supplied four nubbins, so each code appears on four
  rows.
- `reef_zone`: habitat of the colony, either `lagoon` or `forereef`. This is a
  property of the colony, so it is identical across a colony's four rows.
- `nubbin_code`: label of the individual nubbin within its colony (N1 to N4).
- `depth_m`: water depth of the tagged colony in metres. Also a colony-level
  property, repeated on the colony's four rows.
- `symbiont_density_e6_per_cm2`: endosymbiont cells per square centimetre of
  nubbin surface, expressed in millions of cells. This is the only genuinely
  nubbin-specific measurement.

Nubbins taken from the same colony share the same genotype, the same light and
flow history and the same handling batch, so their densities are much more
alike than densities from different colonies.
