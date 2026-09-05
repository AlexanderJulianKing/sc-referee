# Chemical ripener trial on sugarcane: station report

## Aim and conditions

The station tested whether a chemical ripener applied six weeks before harvest
changes cane yield and quality at harvest. Ninety-six individually tagged stools
of one variety, all in a single uniform field of the same plant crop age, were
used. Forty-eight stools received the ripener application (`ripened`) and
forty-eight received no application (`untreated`). These two ripener conditions
are the only comparison in the trial. Each stool was cut and analysed on its own
at harvest.

## Data

File: `cane_ripener_trial.csv`. One row is one cane stool. There are 96 rows and
no missing cells.

| Column | Meaning |
| --- | --- |
| `stool_id` | Stool tag, `ST001` to `ST096`. |
| `treatment` | Ripener condition: `ripened` or `untreated` (48 stools each). |
| `study_half` | Pre-assigned study half: `discovery` or `validation` (48 stools each). |
| `stalk_height_cm` | Millable stalk height, centimetres. |
| `stalk_fresh_mass_kg` | Stalk fresh mass, kilograms per stalk. |
| `soluble_solids_brix` | Juice soluble solids, degrees Brix. |
| `juice_purity_pct` | Juice purity, percent. |
| `fibre_pct` | Fibre content, percent of fresh cane mass. |
| `recoverable_sugar_kg_per_t` | Estimated recoverable sugar, kilograms per tonne of cane. |

The last six columns are the declared outcome family, in the order fixed in the
trial plan before harvest. The two splits are crossed and balanced, with 24
stools in each of the four condition-by-half cells.

## How the analysis was done

The ninety-six stools were split at random into two equal halves, and that split
was written into the field book before any measurement was taken. The analysis
uses those pre-assigned halves in two stages, and all of it is in `analysis.py`.

**Screening stage.** In the discovery half only (48 stools, 24 per condition),
the two ripener conditions were compared on all six declared outcomes with a
two-sample t-test, screened at 0.05. This stage is screening only. Nothing is
declared on discovery-half evidence.

**Confirmatory stage.** In the validation half only (48 stools, 24 per
condition), only the outcomes that survived the screen were tested, again
comparing the two ripener conditions with a two-sample t-test. Four outcomes were
carried forward, so each survivor was judged against 0.05 divided by 4, that is
**0.0125**. Outcomes that did not survive the screen get no confirmatory verdict.

## Screening result (discovery half, not a conclusion)

| Outcome | Mean ripened | Mean untreated | p | Screen |
| --- | --- | --- | --- | --- |
| `stalk_height_cm` | 297.042 | 278.083 | 0.00189 | survives |
| `stalk_fresh_mass_kg` | 2.007 | 1.839 | 0.05701 | does not survive |
| `soluble_solids_brix` | 20.412 | 19.279 | 0.00578 | survives |
| `juice_purity_pct` | 87.333 | 82.883 | 0.0000308 | survives |
| `fibre_pct` | 12.971 | 13.542 | 0.05262 | does not survive |
| `recoverable_sugar_kg_per_t` | 139.058 | 128.171 | 0.00472 | survives |

Four of the six outcomes survived the screen: `stalk_height_cm`,
`soluble_solids_brix`, `juice_purity_pct` and `recoverable_sugar_kg_per_t`.
`stalk_fresh_mass_kg` and `fibre_pct` were not carried forward and were not
tested again.

## Validation result (the basis for every conclusion)

Confirmatory threshold: 0.05 / 4 = 0.0125.

| Outcome | Mean ripened | Mean untreated | Difference | Validation p | Threshold | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `stalk_height_cm` | 292.833 | 284.417 | +8.417 | 0.18535 | 0.0125 | not confirmed |
| `soluble_solids_brix` | 20.950 | 18.992 | +1.958 | 0.000000184 | 0.0125 | confirmed |
| `juice_purity_pct` | 88.375 | 83.983 | +4.392 | 0.0000878 | 0.0125 | confirmed |
| `recoverable_sugar_kg_per_t` | 141.138 | 125.542 | +15.596 | 0.0000270 | 0.0125 | confirmed |

Every conclusion in this report rests on the validation stage only. Three
outcomes are confirmed: juice soluble solids, juice purity and estimated
recoverable sugar, each higher in the ripened stools. Millable stalk height
survived the screen but was not confirmed in the validation half, so the trial
does not claim a height effect. Stalk fresh mass and fibre content never left the
screening stage, so this trial reports no verdict on them.

## Recommendation

On this trial the ripener improves juice quality and sugar recovery without any
confirmed change in stalk height. Recoverable sugar was about 15.6 kg per tonne
higher in the ripened stools of the validation half. The station can recommend
the ripener at the tested timing of six weeks before harvest where the aim is
sugar recovery and juice quality. Any claim about cane bulk, whether stalk
height, fresh mass or fibre, needs its own trial, because this one confirmed
none of them.
