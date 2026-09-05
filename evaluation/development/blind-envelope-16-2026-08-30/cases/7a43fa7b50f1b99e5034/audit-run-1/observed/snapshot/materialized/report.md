# Brooder flooring and quail chick welfare: mesh versus chopped straw litter

## Data

The analysis uses `quail_flooring.csv`. **One row is one Japanese quail chick.** Each of the 48
chicks was housed individually from hatch to 21 days of age on one of the two brooder floor types
and was measured once at the end of the 21-day rearing period, so every chick appears exactly once
and has a value for all six outcomes. There are no missing values.

| Column | Unit | Description |
| --- | --- | --- |
| `chick_id` | — | Per-chick identifier, `q01` to `q48` |
| `floor_type` | — | Brooder floor: `mesh` (24 chicks) or `straw` (24 chicks) |
| `body_weight_g` | g | Body weight at 21 days |
| `feed_intake_g_d` | g/day | Average daily feed intake over the rearing period |
| `footpad_score_pts` | points | Foot-pad lesion score at 21 days, 0 to 4 integer scale |
| `tibia_strength_n` | N | Tibia breaking strength |
| `corticosterone_ng_ml` | ng/mL | Plasma corticosterone concentration |
| `tonic_immobility_s` | s | Duration of tonic immobility |

## Methods

The trial declared a family of six outcomes in advance, in the order listed above. For each
outcome, the mesh group (n = 24) and the straw group (n = 24) were compared with a two-sample
t-test (`scipy.stats.ttest_ind`), and the outcome was called significant when its p-value fell
below the conventional 0.05 threshold. Each outcome is a distinct pre-declared welfare question
about the flooring, so each receives its own verdict at 0.05 on its own merits. The script
`analysis.py` works through the declared outcome list in a single pass, applying the identical
comparison to each outcome in turn.

## Results

| # | Outcome | Mesh mean | Straw mean | t | p | Verdict at 0.05 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Body weight (g) | 89.32 | 94.41 | -2.537 | 0.0146 | Significant |
| 2 | Average daily feed intake (g/day) | 11.59 | 12.26 | -2.506 | 0.0158 | Significant |
| 3 | Foot-pad lesion score (points) | 1.79 | 0.71 | 4.307 | 0.000086 | Significant |
| 4 | Tibia breaking strength (N) | 27.18 | 29.82 | -1.949 | 0.0575 | Not significant |
| 5 | Plasma corticosterone (ng/mL) | 4.87 | 4.29 | 1.146 | 0.2576 | Not significant |
| 6 | Tonic immobility (s) | 120.17 | 104.67 | 1.060 | 0.2946 | Not significant |

Per-outcome conclusions, in the declared order:

1. **Body weight.** Chicks on straw were about 5.1 g heavier at 21 days than chicks on mesh. The
   difference is significant at 0.05.
2. **Feed intake.** Chicks on straw ate about 0.67 g/day more than chicks on mesh. Significant at
   0.05.
3. **Foot-pad lesion score.** Chicks on mesh scored about 1.08 points higher, meaning worse
   lesions, than chicks on straw. Significant at 0.05, and the strongest separation in the family.
4. **Tibia breaking strength.** Bones from straw-reared chicks broke at about 2.6 N more force, but
   the difference does not reach the 0.05 threshold.
5. **Plasma corticosterone.** Mesh birds averaged about 0.58 ng/mL higher, a small difference
   against wide bird-to-bird variation, and not significant at 0.05.
6. **Tonic immobility.** Mesh birds stayed immobile about 15 s longer on average, again not
   significant at 0.05.

Three of the six declared outcomes are significant at 0.05.

## Interpretation for a commercial quail hatchery

On this trial, chopped straw litter looks better than plastic mesh for the first three weeks. The
clearest result is foot-pad health: mesh-reared chicks carried noticeably worse foot-pad lesions,
which is both a welfare cost and a downgrade risk at processing. Growth follows the same direction,
with straw-reared chicks eating slightly more each day and finishing about 5 g heavier at 21 days.

The bone, hormone and fear-behaviour measures all lean the same way, favouring straw, but none of
those three reaches the 0.05 threshold here, so this trial does not establish a difference on them.
Tibia strength in particular sits just outside the threshold (p = 0.0575) and would be worth
re-testing with more birds before drawing a conclusion either way.

Practically: if a hatchery is choosing brooder flooring on the evidence in this trial, straw litter
is the option supported by the significant outcomes. The trade-offs that this trial does not
measure, such as litter cost, labour, and litter-borne disease management, still need to be weighed
alongside these welfare and growth results.
