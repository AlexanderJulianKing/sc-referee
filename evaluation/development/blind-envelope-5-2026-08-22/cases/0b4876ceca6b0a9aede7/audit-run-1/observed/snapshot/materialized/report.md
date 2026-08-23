# Fillet omega-3 at harvest: standard feed vs. reformulated algal-oil feed

## Data description

The analysis reads one comma-separated data file, `harvest_fillet_omega3.csv`. It has a header row
and 120 data rows.

**One row is one individual measured fish.** It is a single salmon netted from one sea cage at
harvest, weighed whole, and then sampled for the omega-3 content of its fillet. Each fish appears
exactly once.

The file has five columns, in this order.

| # | Column | Type | Units | What it holds |
|---|---|---|---|---|
| 1 | `cage_id` | text | — | Pen label of the sea cage the fish came from, written in site-pen form `HVR-Pnn`. Ten distinct labels. |
| 2 | `feed` | text | — | The feed that cage received: `standard` (high-fishmeal) or `algal_oil` (reformulated, higher algal oil). |
| 3 | `fish_number` | integer | — | The fish's sequence number within its own cage sample, 1 to 12. |
| 4 | `harvest_weight_kg` | number | kg | Whole-body harvest weight of that fish, 4.00 to 6.42 kg in this file. |
| 5 | `omega3_mg_per_g` | number | mg/g wet fillet | The outcome: EPA plus DHA in that fish's fillet, in milligrams per gram of wet fillet. |

Ten sea cages from a single smolt batch were used, five per feed, with twelve fish netted at random
from each cage. There are no missing values.

## Methods

Fillet omega-3 content was compared between the two feeds with an independent two-sample t-test on
the difference in group means, assuming equal variances. Every measured fish was entered into the
test as a separate observation, so 120 fish contributed to the comparison, 60 per feed. The test was
two-sided at alpha = 0.05. Group means, standard deviations, the difference in means with its 95%
confidence interval, and Cohen's d were computed alongside the test. The analysis was run in Python
with pandas and SciPy (`scipy.stats.ttest_ind`); it is reproducible by running `analysis.py`.

## Results

Sample size entered into the test: **120 measured fish** (60 standard, 60 algal oil).

| Feed | Fish | Mean omega-3 (mg/g) | SD | SE | Range |
|---|---|---|---|---|---|
| `standard` | 60 | 10.679 | 1.073 | 0.139 | 8.12 to 13.92 |
| `algal_oil` | 60 | 13.416 | 1.171 | 0.151 | 10.87 to 16.50 |

The algal-oil feed gave a mean fillet omega-3 content **2.737 mg/g higher** than the standard feed,
a 25.6 percent increase, with a 95 percent confidence interval of 2.331 to 3.143 mg/g.

- t = 13.345 on 118 degrees of freedom
- **p = 2.5 x 10^-25**
- Cohen's d = 2.44

The feed effect is significant at alpha = 0.05.

Harvest weights were closely matched between the groups (standard 5.194 kg, SD 0.477; algal oil
5.117 kg, SD 0.470), so the two sets of fish went to harvest at the same size.

## Interpretation for the production team

The reformulated algal-oil feed raises fillet omega-3 content. Fish on the algal-oil feed carried
about 2.7 mg of EPA plus DHA more per gram of wet fillet than fish on the standard high-fishmeal
feed, a gain of roughly a quarter over the standard product, and the effect is large relative to the
spread among individual fish. A 200 g portion off the algal-oil fish delivers about 2.68 g of EPA
plus DHA, against about 2.14 g from the standard fish, which is a real difference on a nutrition
panel.

The gain did not cost growth. The two groups reached the same harvest weight, so the reformulated
feed lifts the omega-3 claim without trading away size at harvest.

Recommendation: adopt the reformulated algal-oil feed for the final six-month grow-out phase, and
update the omega-3 figure used in product specifications to reflect the higher level measured here.
