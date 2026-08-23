# Butterfly abundance on farmland: wildflower-margin routes versus conventional routes

## Data description

The project holds two comma-separated data files. Both describe the same summer of butterfly
transect walks: 22 fixed walking routes, 11 crossing farms in a wildflower-margin scheme and 11
crossing conventionally managed farms, each walked once a week for 18 weeks by the same recorder.

### `weekly_counts.csv` — the weekly file

**One row is one route-week:** a single walk of one route in one week. 22 routes x 18 weeks = 396
data rows plus a header row.

| Column | Type | What it holds |
| --- | --- | --- |
| `route_code` | text | Transect-register code of the route walked, e.g. `UKBMS-0131`. Appears on 18 rows, once per week. |
| `management` | text | Management regime of that route, `wildflower_margin` or `conventional`. The same value on all 18 rows of a route. |
| `survey_week` | integer | Week of the survey season, 1 to 18. Week 1 is the first week walked. |
| `air_temp_c` | decimal | Air temperature in degrees Celsius at the start of that walk. |
| `butterfly_count` | integer | Number of butterflies of all species counted along the route on that walk. |

### `route_summary.csv` — the per-route file

**One row is one route,** summarising that route's whole season. 22 data rows plus a header row, and
nothing else.

| Column | Type | What it holds |
| --- | --- | --- |
| `route_code` | text | Transect-register code of the route. Appears exactly once. The same 22 codes as the weekly file. |
| `management` | text | Management regime of that route, `wildflower_margin` or `conventional`. |
| `weeks_surveyed` | integer | Number of weekly walks contributing to that route's mean. |
| `mean_weekly_count` | decimal | That route's mean butterfly count per walk, rounded to 2 decimal places. |

The per-route file is derived from the weekly file. The script recomputes it and checks the two
agree: all 22 route codes matched, `weeks_surveyed` matched for every route, and the largest gap in
`mean_weekly_count` was 0.0000.

## Methods

The unit that carries a management label is the **route**, not the route-week. Each route stays in
one regime for all 18 walks, so the 396 weekly rows are 18 repeated measures of only 22 independent
units. Treating them as 396 independent observations would inflate the sample size roughly eighteen
fold and shrink the p-value for no extra information, in the same way that weighing one person on
eighteen mornings does not give you eighteen people.

The inferential test was therefore run on the 22 rows of `route_summary.csv`, one value per route:
an independent two-sample comparison of `mean_weekly_count` between the two regimes. The reported
sample size is the number of routes, n = 22.

The primary test is **Welch's independent two-sample t-test**, chosen ahead of looking at the data
because it does not assume the two groups share a variance. Assumption checks are reported alongside
it but were not used to switch tests after the fact. Student's equal-variance t-test and the
rank-based Mann-Whitney U test are reported as supporting results.

The weekly file was used only for descriptive counts, as the protocol directs. No inferential test
was run on the weekly rows.

## Results

**Description, from the weekly file.** All 22 routes have the full 18 weekly walks, 396 route-weeks
in total, with no missing values. Weekly counts ran from 5 to 80 butterflies overall: 5 to 45 on
conventional routes (mean 21.18) and 11 to 80 on wildflower-margin routes (mean 38.60). Air
temperature at the start of a walk ran from 14.0 to 28.0 degrees Celsius, mean 20.98. Averaged
across all routes, counts peaked in survey week 9.

**Per-route means, from the per-route file.**

| Regime | Routes | Mean of route means | SD | Median | Range |
| --- | --- | --- | --- | --- | --- |
| `wildflower_margin` | 11 | 38.60 | 6.62 | 39.44 | 28.83 to 47.72 |
| `conventional` | 11 | 21.18 | 4.67 | 21.89 | 12.56 to 26.17 |

**Two-group test (n = 22 routes).** Wildflower-margin routes averaged 17.42 more butterflies per
walk than conventional routes (95% CI 12.29 to 22.55), a ratio of 1.82 times. Welch's t-test:
t = 7.136, df = 17.98, p = 1.21e-06. Hedges' g = 2.93.

Assumption checks: Levene's equal-variance test W = 3.370, p = 0.081; Shapiro-Wilk on the route
means gave W = 0.924, p = 0.352 for wildflower-margin routes and W = 0.889, p = 0.134 for
conventional routes. Supporting tests agree: Student's t-test t = 7.136, df = 20, p = 6.50e-07;
Mann-Whitney U = 121.0, p = 8.15e-05.

## Conservation interpretation

Routes crossing farms in the wildflower-margin scheme carried close to twice the butterflies of
routes crossing conventional farms, and the confidence interval keeps the whole plausible range of
that gap well above zero. The gap is large next to the spread between routes within either regime,
so it is not a case of one or two unusual routes pulling an average.

Three limits matter before this is read as a claim about what margins do.

1. **This is observational, not a randomised trial.** Farms were not assigned to a regime by the
   charity. Farms that join a wildflower-margin scheme may already differ in hedgerow cover, soil,
   pesticide use, or surrounding landscape, and any of those could carry part of the difference.
2. **One summer, one recorder, 22 routes.** Butterfly numbers swing a lot between years. A single
   season cannot show whether the gap holds up, and the recorder being the same person removes
   between-recorder variation but ties every count to one observer's detection skill.
3. **Air temperature was recorded but not modelled.** It is available in the weekly file as a
   covariate if a later analysis wants it, and the analysis reported here does not adjust for it.

Read within those limits, the result supports wildflower margins as a management option worth
continuing and worth testing properly, ideally with routes assigned to regimes and followed over
several seasons.
