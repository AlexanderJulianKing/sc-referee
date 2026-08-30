# Green roof survey: does substrate depth matter?

## Data

The analysis uses `green_roof_survey.csv`. One row is one surveyed green roof: each of
the 44 extensive green roofs in the city was visited once in late summer and measured
for all five outcomes on that visit. There are no missing values.

| Column | What it holds |
| --- | --- |
| `roof_id` | Short roof identifier, `GR01` to `GR44`, in survey visit order |
| `substrate_depth` | Depth class: `shallow` (about 60 mm, 22 roofs) or `deep` (about 120 mm, 22 roofs) |
| `plant_richness_count` | Vascular plant species richness, count of species |
| `veg_cover_pct` | Vegetation cover, percent of roof area |
| `substrate_moisture_pct` | Substrate volumetric moisture in the survey week, percent |
| `temp_reduction_c` | Midday surface temperature reduction against the adjacent bare membrane, degrees Celsius |
| `invert_abundance_count` | Flying invertebrate catch from a standard 30 minute sticky trap, count of individuals |

## Methods

The survey declared five outcome variables in advance, in the order listed above. Each
one was declared as its own ecological question about substrate depth, so each is
compared between the two depth classes on its own merits.

For every outcome the two groups are compared with a two-sample Student's t-test for
independent groups (`scipy.stats.ttest_ind`), the standard test for continuous
measurements from two separate sets of subjects. The 22 shallow roofs and the 22 deep
roofs are independent roofs, so nothing is paired. Significance is decided at the
conventional 0.05 threshold. All five comparisons are produced by `analysis.py`.

## Results

Group means, test statistic, p-value and verdict, in the declared outcome order.

| Outcome | Mean, shallow (n=22) | Mean, deep (n=22) | t | p | Verdict at 0.05 |
| --- | --- | --- | --- | --- | --- |
| `plant_richness_count` | 7.95 | 12.86 | -8.152 | 3.44e-10 | Significant |
| `veg_cover_pct` | 63.33 | 80.23 | -7.780 | 1.14e-09 | Significant |
| `substrate_moisture_pct` | 10.87 | 17.42 | -10.377 | 3.68e-13 | Significant |
| `temp_reduction_c` | 6.26 | 6.84 | -1.116 | 0.271 | Not significant |
| `invert_abundance_count` | 33.18 | 37.27 | -0.851 | 0.400 | Not significant |

Per outcome:

- **Plant species richness.** Deep roofs carried about 4.9 more vascular plant species
  than shallow roofs (12.86 against 7.95). Significant.
- **Vegetation cover.** Deep roofs were about 16.9 percentage points greener (80.23
  percent against 63.33 percent). Significant.
- **Substrate moisture.** Deep roofs held about 6.6 percentage points more moisture in
  the survey week (17.42 percent against 10.87 percent). Significant.
- **Surface temperature reduction.** Deep roofs cooled the surface about 0.58 degrees
  Celsius more than shallow roofs (6.84 against 6.26), and the roof-to-roof scatter is
  wide enough that this difference is not significant.
- **Flying invertebrate abundance.** Deep roofs caught about 4.1 more individuals per
  trap (37.27 against 33.18), again not significant against a very wide spread of
  catches.

## Interpretation for the city green infrastructure team

Going from roughly 60 mm to roughly 120 mm of growing substrate is associated with a
clearly richer and greener roof that stays damper through late summer. Those three
outcomes separate the two depth classes sharply in this survey.

The two outcomes the team may care about for climate and biodiversity targets behave
differently. Both midday surface cooling and sticky-trap invertebrate catch were a
little higher on the deeper roofs, but in both cases the difference is small next to
how much individual roofs differ from each other, and neither reaches the 0.05
threshold here. On this evidence, specifying deeper substrate can be justified on
vegetation and moisture grounds; it should not be sold on a promised gain in midday
cooling or in flying insect catch, which this survey did not demonstrate.

Two limits are worth stating plainly. This is a one-visit cross-sectional survey, so it
shows association between depth class and outcome, not proof that depth caused the
difference; older, better-maintained, or better-sited roofs may also tend to be the
deeper ones. And a non-significant result here means this survey did not show a
difference, not that the difference is zero, especially for the two outcomes with the
widest roof-to-roof scatter.
