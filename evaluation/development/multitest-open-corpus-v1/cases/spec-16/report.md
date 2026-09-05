# Grazing intensity and grassland birds

Fifty-six paddocks on one mixed-grass prairie ranch were surveyed during a single
breeding season, 28 under light cattle grazing and 28 under heavy grazing. Every
paddock got the same point-count protocol. Five outcomes were recorded: bird species
richness, nest density, vegetation height, litter depth, and bare ground.

## How the testing was done

The five outcomes were treated as one family, and the multiplicity correction was done
upstream of this report rather than inside the reporting script. That upstream step read
`data.csv`, ran a Welch two-sample t-test on each of the five outcomes, and applied the
**Holm-Bonferroni** step-down correction to the complete set of five raw p-values at a
family-wide level of 0.05. Its output is **`pvalues_adjusted.csv`**, one row per
outcome, carrying the two group means, the raw p-value, the Holm-adjusted p-value, and
the name of the correction method.

`analysis.py` reads `data.csv` for the descriptive statistics and takes all inference
from `pvalues_adjusted.csv`. Significance is decided from the adjusted p-value column
alone; the reporting script never recomputes a raw p-value.

## Results

| Outcome | Light (mean, SD) | Heavy (mean, SD) | Holm-adjusted p |
|---|---|---|---|
| Bird species richness | 9.75 (2.56) | 7.46 (2.43) | 0.0021 |
| Nest density (per ha) | 2.35 (0.85) | 1.62 (0.72) | 0.0021 |
| Vegetation height (cm) | 38.50 (8.01) | 21.69 (6.49) | 6.8e-11 |
| Litter depth (cm) | 3.20 (1.00) | 1.90 (0.80) | 5.9e-06 |
| Bare ground (%) | 11.02 (4.95) | 23.99 (8.00) | 1.5e-08 |

All five outcomes remain significant after correction over the full family of five.

## What this means for grazing management

The habitat structure differences are large and survive correction easily. Heavy
grazing cut mean vegetation height by 16.8 cm and litter depth by 1.3 cm, and more than
doubled bare ground, from 11% to 24%. The bird responses track that structural loss:
2.3 fewer species per paddock and about a third fewer nests per hectare under heavy
grazing.

Because the habitat variables and the bird variables move together, the sensible
management reading is that stocking rate acts on birds through the cover it leaves
behind. Paddocks held near the light-grazing structure, roughly 35 cm or more of
standing vegetation with bare ground under about 15%, carried the richer bird
communities. Deferred or rotational stocking that leaves residual cover on part of the
ranch each breeding season is the practical lever. These are single-season, single-ranch
observations, so the size of the effect elsewhere is untested even though its direction
here is clear.
