# Housing enrichment and welfare in a research ferret colony

## Question and design

We asked whether housing our adult ferrets in enriched pens improves their
welfare compared with the standard pens we have used until now. Forty adult
animals from the colony were allocated to two housing conditions and stayed in
them for eight weeks. Twenty lived in enriched pens fitted with tunnels, digging
substrate, raised platforms and a set of novel objects that we rotated through
the pens. The other twenty lived in standard pens with bedding and a nest box
and nothing else. Housing condition is the only grouping factor, and it has two
levels: `enriched` and `standard`.

Before the animals were moved, the welfare assessment plan declared four
outcomes and fixed the order in which we would examine them: daily active time,
faecal corticosterone metabolite concentration, body mass change over the eight
weeks, and stereotypic behaviour bouts per hour. Each ferret contributes one
summary value per outcome for the whole eight-week period, so there is no
repeated measurement within an animal to account for.

## Data description

All of the analysis reads a single file, `ferret_welfare.csv`. It holds 40 data
rows under one header row. **One row is one ferret**: that animal's colony
identifier, its four eight-week welfare summary values, and the housing
condition it lived under during those eight weeks. Each of the 40 ferrets
appears exactly once, and every cell is filled. There are no missing values.

| # | Column | Unit | What it holds |
| --- | --- | --- | --- |
| 1 | `animal_id` | none | Colony identifier for the ferret, `FRT-01` through `FRT-40`, unique across the file. |
| 2 | `daily_active_time_min` | minutes per day | Declared outcome 1. Mean daily active time from the animal's accelerometer collar, averaged over the eight weeks. |
| 3 | `faecal_corticosterone_ng_per_g` | nanograms per gram | Declared outcome 2. The animal's faecal corticosterone metabolite concentration for the eight-week period. |
| 4 | `body_mass_change_g` | grams | Declared outcome 3. End mass minus start mass across the eight weeks. Negative values mean the animal lost mass. |
| 5 | `stereotypic_bouts_per_hour` | bouts per hour | Declared outcome 4. Stereotypic behaviour bouts per hour of observation, averaged over the eight weeks. |
| 6 | `housing_condition` | none | The grouping factor. Exactly two values, `enriched` and `standard`. |

The values in this file are invented for a worked example. They are not records
from a real colony.

## Per-group summary

Twenty ferrets are in each housing condition. Spread is given as the standard
deviation of the animals within that condition.

| Declared outcome | Group | Ferrets | Mean | SD |
| --- | --- | --- | --- | --- |
| 1. Daily active time (min/day) | enriched | 20 | 209.61 | 37.93 |
| 1. Daily active time (min/day) | standard | 20 | 166.80 | 34.02 |
| 2. Faecal corticosterone (ng/g) | enriched | 20 | 85.35 | 25.61 |
| 2. Faecal corticosterone (ng/g) | standard | 20 | 119.81 | 22.59 |
| 3. Body mass change (g) | enriched | 20 | 52.00 | 25.18 |
| 3. Body mass change (g) | standard | 20 | 45.55 | 30.90 |
| 4. Stereotypic bouts (per hour) | enriched | 20 | 0.71 | 0.67 |
| 4. Stereotypic bouts (per hour) | standard | 20 | 1.74 | 0.64 |

## The overall screen

We did not go straight to comparing the outcomes one at a time. The plan called
for a single overall screening quantity first, and the analysis script computes
it before any per-outcome comparison is run.

The screening quantity asks one question: taken as a family, how far apart are
the two housing conditions across all four outcomes at once? The four outcomes
are recorded in units that cannot be added together, so each one is first put on
a common scale. For each outcome we take the difference between the two group
means and divide it by that outcome's own pooled standard deviation. That gives
four unit-free separations, each saying how many standard deviations of animal
variation separate the enriched pens from the standard pens on that measure. The
four are then combined into one number by taking their root mean square, which
is their typical size regardless of direction. Because it is on the standard
deviation scale, the number reads the way an effect size does: roughly 0.2 is
small, 0.5 is medium, 0.8 is large.

Two points matter about how this number was produced. First, it comes from the
raw measurements through ordinary arithmetic on the outcome columns: means,
standard deviations, a division and a root mean square. No statistical test was
run, no p-value was computed and no significance threshold was consulted at this
step. Second, the cutoff the number had to clear was fixed in advance, at 0.40,
and is written into the analysis script as a constant.

For this colony the four standardised separations were +1.19 for daily active
time, -1.43 for faecal corticosterone, +0.23 for body mass change and -1.57 for
stereotypic bouts. Their root mean square is **1.22**, which is above the
**0.40** cutoff. The screen therefore cleared.

Clearing the screen is what allowed the per-outcome comparisons to be performed
and reported at all. Had the overall value come in below 0.40, the analysis
would have stopped there: the script would have reported that the study stops at
the overall screen, and no per-outcome test, p-value or verdict would have been
computed or written down. The two paths are separate branches in the script and
print visibly different output, so a reader can see which one ran.

## Conclusions by declared outcome

Each outcome was compared between the two housing conditions with the standard
two-group significance test, Welch's two-sample t-test, judged at the
conventional 0.05 threshold. The outcomes are reported in the order the welfare
assessment plan declared them.

**1. Daily active time.** Ferrets in enriched pens were active for about 43
minutes more per day on average (209.61 against 166.80 minutes per day),
t = 3.76, p = 0.0006. This difference is significant at the 0.05 threshold.
Enrichment increased how much the animals moved.

**2. Faecal corticosterone.** Ferrets in enriched pens had lower corticosterone
metabolite concentrations, averaging 85.35 ng/g against 119.81 ng/g in standard
pens, t = -4.51, p = 0.00006. This difference is significant at the 0.05
threshold, and points in the direction we would want: less physiological stress
under enrichment.

**3. Body mass change.** The two housing conditions barely differed. Ferrets in
enriched pens gained 52.00 g on average over the eight weeks and those in
standard pens gained 45.55 g, a gap of about 6 g against animal-to-animal
spreads of 25 to 31 g. t = 0.72, p = 0.47. This difference is not significant at
the 0.05 threshold, and we found no evidence that enrichment changed body mass
over eight weeks.

**4. Stereotypic bouts.** Ferrets in enriched pens showed fewer stereotypic
bouts, 0.71 per hour against 1.74 per hour in standard pens, t = -4.95,
p = 0.00002. This difference is significant at the 0.05 threshold and is the
largest separation of the four outcomes.

Overall, three of the four declared outcomes separated the two housing
conditions, all three in the direction of better welfare under enrichment. Body
mass change did not. On this evidence I would recommend moving the colony to
enriched pens, while noting that the benefit shows up in activity, stress
physiology and stereotypy rather than in growth.
