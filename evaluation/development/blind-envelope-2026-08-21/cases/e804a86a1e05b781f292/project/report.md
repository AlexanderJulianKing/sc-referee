# Pollen diversity and six-week microcolony growth in *Bombus terrestris*

## Data description

All results below come from a single file, `microcolony_growth.csv`.

**What one row is.** One row of the file is one whole microcolony, recorded once. Each colony was
kept alone in its own box and fed on its own, and it was taken apart and weighed a single time at the
end of week 6. A row is therefore not a comb, not a bee, and not a repeated weighing: it is the
complete record for one colony, holding that colony's diet, its shelf position, the number of workers
it started with, and its one final mass. The file has a header row and 24 data rows, one for each of
the 24 colonies.

**Columns.**

| Column | Type | What it holds |
| --- | --- | --- |
| `hive_label` | string | The colony identifier, `MC-01` through `MC-24`. Each label belongs to one colony and appears exactly once in the file. |
| `pollen_diet` | string | The diet that colony was given for the whole experiment: `monofloral` (willow pollen only) or `mixed` (pollen from four plant species). |
| `start_worker_count` | integer | How many workers were seeded into the colony when it was set up, 4 to 6 bees. |
| `rearing_shelf` | string | Which climate-cabinet shelf the colony box sat on: `SH-1`, `SH-2`, or `SH-3`. |
| `final_colony_mass_g` | number, grams | The colony's total mass at week 6 (comb, brood and stored provisions weighed together), to one decimal place. This is the outcome of interest, and it is one destructive measurement per colony. |

## Design

I set up 24 queenright microcolonies from commercial stock and assigned each one to a diet: 12
colonies received willow pollen only (monofloral) and 12 received a mixed diet drawn from four plant
species. Diet was assigned per colony and each colony was housed and fed on its own, so the colony
is both the unit that was assigned to a treatment and the unit that was measured. There was no shared
feeding, no pooling of boxes, and no repeated weighing.

The 24 boxes were spread across three shelves of the climate cabinet, with 8 colonies per shelf and
both diets present on every shelf, so shelf position is not confounded with diet. Shelf and starting
worker count are recorded in the file but were not used in the comparison reported here.

## What entered the test

The script first checks that no value of `hive_label` occurs twice, then prints the number of rows
alongside the number of distinct colony labels. Both are 24, which confirms that the rows of the file
are the colonies, one apiece.

The comparison used the `final_colony_mass_g` column, split by `pollen_diet`. Exactly one mass value
per colony entered the test: 12 masses from the monofloral colonies and 12 masses from the mixed-diet
colonies, 24 values in all. Nothing was averaged, expanded, or dropped beforehand, and no colony
contributed more than one number.

**N = 24 colonies**, counted as whole microcolonies, not as bees, weighings, or boxes on a shelf.
Within that total, n = 12 colonies in the monofloral group and n = 12 colonies in the mixed group.

## Results

Colonies on the mixed pollen diet were heavier at week 6 than colonies on willow pollen alone.

| Diet | Colonies (n) | Mean final mass (g) | SD (g) |
| --- | --- | --- | --- |
| monofloral | 12 | 51.41 | 12.29 |
| mixed | 12 | 71.43 | 15.43 |

The mixed-diet colonies averaged 20.02 g more than the monofloral colonies. A two-sample t-test
(`scipy.stats.ttest_ind`, monofloral versus mixed, equal variances assumed, 22 degrees of freedom)
gave t = -3.5167 with p = 0.0019. The sign is negative simply because the monofloral group was
entered first and is the lighter group.

Both groups were widely spread, as expected for microcolonies: the standard deviations, 12.29 g and
15.43 g, are roughly a quarter of the group means, and individual colony masses ran from 35.0 g to
93.3 g. The difference between diets is large enough to stand out against that spread.

## Interpretation and limits

Over six weeks, microcolonies fed pollen from four plant species accumulated about 20 g more comb,
brood and provisions than microcolonies fed willow pollen alone, and the difference is unlikely to be
sampling noise (p = 0.0019). Because diet was assigned per colony and each colony was measured once,
the test is at the level at which the treatment was applied.

Two limits are worth stating. First, the study rests on 24 colonies from commercial stock, 12 per
diet, so the estimate of the difference is not precise, and a single experiment on one bumblebee
source should not be read as a general statement about all pollen mixtures. Second, the comparison
reported here ignores shelf and starting worker count. The design balances diets across shelves, so
shelf is not expected to bias the diet contrast, but any residual shelf effect or effect of founding
worker number sits inside the within-group variation rather than being modelled.
