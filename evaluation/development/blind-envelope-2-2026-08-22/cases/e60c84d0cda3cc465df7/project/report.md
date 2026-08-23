# Chronic sublethal fungicide exposure and forager load size in leaf-cutter ants

## Why load size matters

A leaf-cutter forager does not eat the leaf it carries. It carries substrate for the fungus garden
that feeds the whole colony, so every fragment coming down the trail is an investment decision made
on the colony's behalf. The size of that fragment sits at the end of a long chain: the worker has to
find and evaluate a leaf, cut it with her mandibles, judge how much she can carry back at a
worthwhile speed, and be recruited to a patch worth returning to. Cutting is metabolically expensive
and mandible wear accumulates over a worker's foraging life, so load size responds to muscle power,
mandible condition, recruitment quality, and the colony's own assessment of how much substrate the
garden needs. That is why load size is a more sensitive readout of colony condition than survival
counts. A worker under mild chronic stress usually keeps walking the trail, but she brings back less
per trip, and the garden's substrate input falls before any ant dies. A fungicide delivered through
the forage supply is a plausible source of exactly this kind of stress, both directly on the workers
and indirectly through the cultivar the colony depends on.

## Data description

The single data file is `forager_loads.csv`. It has 160 rows plus a header.

**One row is one returning forager that was intercepted on the trail and had its leaf fragment
weighed.** A row is an individual worker ant, not a colony and not a repeated weighing of the same
worker. Each worker appears exactly once. There are 16 colonies and 10 weighed foragers per colony,
so **each colony contributes exactly ten rows** (16 x 10 = 160).

The file has six columns:

| Column | Type | Units or values | Level | What it is |
| --- | --- | --- | --- | --- |
| `colony_id` | text | `C01` to `C16`, 16 distinct values | colony | The colony the forager came from. Each value appears on 10 rows. This is the grouping factor for the colony random effect. |
| `exposure_group` | text | `control` or `exposed` | colony | Treatment group. Constant within a colony: every row from a colony carries the same label. |
| `forager_id` | text | `F01` to `F10` | forager | Identifier of the forager within its colony. Not unique on its own, since `F01` occurs once in each of the 16 colonies. A forager is uniquely identified by the pair (`colony_id`, `forager_id`). |
| `head_width_mm` | number | millimetres, 2 decimals, range 1.59 to 2.46 | forager | Maximum head capsule width, the standard body-size measure for polymorphic leaf-cutter workers. |
| `interception_hour` | integer | whole hour, 7 to 19 | forager | Clock hour at which the forager was intercepted, 24-hour clock. Arena foraging was scored from 07:00 to 19:00. |
| `fragment_mass_mg` | number | milligrams, 1 decimal | forager | **Outcome.** Fresh mass of the leaf fragment the forager was carrying when intercepted. |

Every cell is present, there are no missing values, no duplicated (`colony_id`, `forager_id`) pairs,
and every fragment mass is positive. The analysis script re-checks all of this before fitting
anything.

Group membership is balanced at the colony level: 8 control colonies (C01, C03, C05, C07, C09, C11,
C13, C15) and 8 exposed colonies (C02, C04, C06, C08, C10, C12, C14, C16), contributing 80 weighed
foragers each.

## Design and unit of analysis

**The colony is the unit that received the treatment.** Each queenright colony was kept in its own
foraging arena, and the fungicide was delivered through that colony's forage supply. Every worker in
a colony therefore shares the same exposure, the same queen, and the same fungus garden. Treatment
was assigned 16 times, once per colony, and never to an individual forager.

The 160 weighed foragers are consequently not 160 independent observations of the treatment. Ten
foragers from the same colony are ten looks at one treated unit. Two things follow. First, ten
foragers from one colony resemble each other more than they resemble foragers from another colony,
because they share a garden, a queen, and an arena. Second, any analysis that counts each forager as
an independent replicate of the fungicide is answering a question about 160 units that only ever
existed for 16.

**The primary analysis therefore models colony as a random effect.** A linear mixed-effects model of
`fragment_mass_mg` on `exposure_group` with a random intercept for `colony_id` splits the total
variation into a between-colony part and a within-colony part, and it prices the exposure effect
against the between-colony part, which is the level at which the treatment was actually applied. The
model was fitted by restricted maximum likelihood (REML) with `statsmodels` 0.14.1.

Because the design is balanced (exactly 10 foragers in each of 16 colonies), the REML variance
components have an exact closed form. The script computes that closed form independently and
compares it to the fitted model. The two agree to three decimal places on every quantity reported
below, which confirms the optimiser reached the true optimum rather than stopping early.

## Primary result: mixed-effects model

Descriptive picture first. Mean fragment mass was 22.23 mg for control foragers and 18.42 mg for
exposed foragers. At the colony level, the 16 independent units, mean load ran from 19.27 to
25.25 mg across the eight control colonies and from 13.90 to 21.67 mg across the eight exposed
colonies. The two ranges overlap, which is the first sign that colony-to-colony variation is
substantial.

**Estimated exposure effect (exposed minus control): -3.816 mg**

| Quantity | Value |
| --- | --- |
| Model-estimated control mean | 22.231 mg |
| Exposure effect (exposed minus control) | **-3.816 mg** |
| Standard error | 1.261 mg |
| 95% confidence interval (Wald z) | **[-6.287, -1.345] mg** |
| Wald z statistic | -3.027 |
| p-value (Wald z, two-sided) | **0.00247** |

Variance components from the same model:

| Component | Variance | Standard deviation |
| --- | --- | --- |
| Between colonies (random intercept) | 4.538 mg² | 2.130 mg |
| Within colonies (residual, forager to forager) | 18.186 mg² | 4.265 mg |

The intraclass correlation is 0.200, so about a fifth of the total variance in load size sits
between colonies and four fifths sits between foragers within a colony. Colonies genuinely differ,
which is why the colony term belongs in the model.

**One honest qualification on the p-value.** `MixedLM` reports a Wald z test, which assumes the
number of clusters is effectively infinite. There are 16 colonies. Referring the same statistic to a
t distribution with 14 degrees of freedom (16 colonies minus 2 estimated group means) gives a 95%
interval of [-6.520, -1.112] mg and p = 0.00905. Both versions are reported so that the conclusion
does not depend on which reference distribution is chosen. The effect clears the 5% level either
way, and the small-sample version is the more conservative of the two.

**Conclusion, based on this model and only on this model.** Chronic sublethal fungicide exposure
reduced the fresh mass of carried leaf fragments by about 3.8 mg per forager, roughly a 17%
reduction against the control mean of 22.2 mg. The confidence interval is consistent with a
reduction anywhere from about 1.3 mg to about 6.3 mg, so the direction of the effect is well
supported while its exact size is not tightly pinned down by 16 colonies.

### Secondary sensitivity check (not the inferential result)

For comparison only, a plain Welch two-sample t-test was run on the 160 individual forager records,
ignoring colony membership entirely.

| Quantity | Value |
| --- | --- |
| n control foragers / n exposed foragers | 80 / 80 |
| Mean, control foragers | 22.231 mg |
| Mean, exposed foragers | 18.415 mg |
| Difference (exposed minus control) | -3.816 mg |
| Standard error | 0.745 mg |
| 95% confidence interval | [-5.288, -2.345] mg |
| t statistic (158.00 df) | -5.122 |
| p-value | 8.71 x 10⁻⁷ |

**This is a sensitivity check, not the inferential result of the study, and no conclusion above or
below rests on it.** It ignores the nesting of foragers within colonies and so treats 160 foragers
as 160 independent observations of a treatment that was applied 16 times. It overstates the number
of independent observations by a factor of ten. The consequence is visible in the numbers: the point
estimate is identical (-3.816 mg, as it must be in a balanced design), but the standard error drops
from 1.261 mg to 0.745 mg, the primary standard error being 1.69 times the naive one, and the
p-value falls by more than three orders of magnitude, from 0.0025 to 0.0000009. That extra apparent
precision is manufactured by the wrong denominator. It is not evidence. The check is included
because it makes the cost of ignoring the design explicit, and because a reader who has seen only
the row-level number would badly overstate how certain this study is.

## Biological interpretation

A 3.8 mg reduction on a 22.2 mg baseline is a meaningful loss of substrate delivery. Leaf-cutter
colonies run a continuous supply chain into the fungus garden, and a persistent 17% shortfall per
trip has to be met either by more trips, which costs worker time and lifespan, or by a smaller
garden, which costs colony growth. Neither compensation is free. The mechanism is not identified
here. Reduced load size is compatible with direct sublethal effects on the worker (weaker cutting
musculature, faster mandible wear, altered load-size decision rules) and equally compatible with an
indirect route through the cultivar, where a stressed fungus garden changes what the colony demands
and how recruitment is tuned. Distinguishing those would need garden-side measurements this study
did not take.

The 2.13 mg between-colony standard deviation is itself informative. Colonies differ substantially
in baseline load size regardless of treatment, which is exactly why the colony was the right unit to
randomise and the right term to model. It is also why 16 colonies, rather than 160 foragers, set the
real precision of this experiment.

## Caveats

- **A single fungicide at a single dose.** One compound at one chronic sublethal level was tested.
  Nothing here generalises to other fungicides, other doses, or realistic field mixtures where
  several agrochemicals arrive together.
- **Laboratory arenas.** Colonies foraged in individual arenas on a supplied forage stream. Trail
  length, patch choice, competition, weather, and predation risk are all absent, and every one of
  them shapes load-size decisions in the field. Effect sizes measured in arenas need not carry over
  to foraging trails outdoors.
- **A single sampling season.** All weighing came from one season, so seasonal shifts in colony
  demand, worker age structure, and garden condition are unsampled.
- **Sixteen colonies.** The design is correctly analysed at the colony level, and that leaves 14
  degrees of freedom for the treatment comparison. The direction of the effect is clear; its
  magnitude carries a wide interval, and a replication would be needed to narrow it.
- **Ten foragers per colony, one weighing each.** Loads were sampled once per worker across a single
  daytime window. Foragers were intercepted between 07:00 and 19:00, and no within-day pattern was
  modelled.
- **Head width was recorded but not adjusted for.** Worker body size varies within a colony and
  affects load size. The reported effect is the total effect of exposure on load size, which is the
  quantity of interest, and it has not been decomposed into a body-size pathway and a residual one.
- **Observational scope of the outcome.** Fragment fresh mass was measured. Substrate quality,
  garden growth, and colony fitness were not, so the link from smaller loads to colony-level
  consequences is inferred from leaf-cutter biology rather than demonstrated in these data.

## Reproducing the analysis

```
/usr/local/bin/python3 analysis.py
```

The script reads `forager_loads.csv` from its own directory, prints the design summary, the primary
mixed model with its convergence check, and the secondary row-level sensitivity test, in that order.
It was run with statsmodels 0.14.1, pandas 2.0.3, scipy 1.9.1, and numpy 1.24.4. Every number in
this report is taken from that printed output.
