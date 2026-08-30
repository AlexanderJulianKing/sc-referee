# Shelter provision for juvenile European lobsters: 60 day hatchery trial

## Data

File: `lobster_shelter_trial.csv`. One row is one individually reared juvenile European lobster
from a single settlement cohort, followed for 60 days. The file holds 72 rows, 36 animals per
shelter type, with no missing values.

| Column | Units | Meaning |
| --- | --- | --- |
| `lobster_id` | none | Identifier for the individual animal, `L01` to `L72` |
| `shelter_type` | none | Rearing shelter: `crushed_shell` or `plastic_tube` |
| `carapace_increment_mm` | mm | Declared outcome 1: carapace length increment over 60 days |
| `mass_gain_g` | g | Declared outcome 2: wet mass gain over 60 days |
| `moult_count` | count | Declared outcome 3: moults completed in the period |
| `shelter_time_s` | s | Declared outcome 4: sheltering time in one ten minute observation |
| `haemolymph_protein_g_l` | g/L | Declared outcome 5: end of trial haemolymph total protein |

## Methods

Each of the five declared outcomes was compared between the two shelter types with an independent
two-sample t-test (`scipy.stats.ttest_ind`), giving one raw p-value per outcome.

The five declared outcomes form a single pre-declared family and were adjusted together as one
family at a family-wise level of 0.05. The adjustment was carried out by the third-party
statistics package **pingouin** (version 0.5.5), using `pingouin.multicomp` with the Holm
step-down procedure, which was handed the complete set of five raw p-values in one call. Every
significance verdict below is taken from the adjusted values pingouin returned; no verdict comes
from a raw p-value.

## Results

Outcomes are listed in the declared order.

| # | Outcome | Mean, crushed shell | Mean, plastic tube | Raw p | Adjusted p | Verdict at family-wise 0.05 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `carapace_increment_mm` | 4.801 | 3.899 | 0.00207 | 0.00620 | Significant |
| 2 | `mass_gain_g` | 2.150 | 1.720 | 0.00061 | 0.00243 | Significant |
| 3 | `moult_count` | 2.361 | 2.167 | 0.24934 | 0.31329 | Not significant |
| 4 | `shelter_time_s` | 402.056 | 465.972 | 0.00044 | 0.00218 | Significant |
| 5 | `haemolymph_protein_g_l` | 40.989 | 39.008 | 0.15664 | 0.31329 | Not significant |

Per-outcome conclusions, in the declared order:

1. Carapace increment differs between shelter types. Animals on crushed shell grew about 0.90 mm
   more over the 60 days.
2. Mass gain differs between shelter types. Animals on crushed shell gained about 0.43 g more.
3. Moult count shows no difference that survives the family-wise correction (means 2.36 against
   2.17).
4. Sheltering time differs between shelter types. Animals with plastic tubes spent about 64
   seconds more of the ten minute observation sheltering.
5. Haemolymph protein shows no difference that survives the family-wise correction (means
   40.99 g/L against 39.01 g/L).

## Interpretation for a stock enhancement hatchery

On this cohort, crushed shell substrate went with faster growth on both size measures, while
moulded plastic tubes went with more time spent sheltering. Moult count and end of trial
haemolymph protein did not separate the two shelter types once the whole declared family of five
outcomes was corrected together, so this trial gives no evidence that the shelter type changes
moult frequency or nutritional condition as measured here.

A hatchery whose release target is size at release has a reason from these data to prefer crushed
shell substrate. A hatchery that instead wants juveniles to shelter more, for example if
post-release predation is the binding constraint, would read the sheltering result in favour of
tube shelters. These are the two ends of a trade-off within one 60 day trial on 72 animals from a
single cohort, and nothing here measures survival after release, so the choice should not be
settled on this trial alone.
