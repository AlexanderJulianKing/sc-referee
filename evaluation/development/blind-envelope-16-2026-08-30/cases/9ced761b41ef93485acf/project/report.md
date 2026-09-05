# Rhizobial seed inoculation of chickpea: screenhouse experiment

## Data

The analysis uses `chickpea_inoculation.csv`. One row is one harvested chickpea plant, that is,
one pot: the row carries that plant's identifier, its seed treatment, and its measured value for
each of the seven declared outcomes. There are 60 rows, 30 plants per seed treatment, and no
missing values.

| Column | Unit | Description |
| --- | --- | --- |
| `plant_id` | none | Per-plant identifier, `P01` through `P60` |
| `inoculation` | none | Seed treatment: `inoculated` (rhizobial slurry) or `uninoculated` |
| `shoot_dw_g` | g/plant | Shoot dry weight |
| `root_dw_g` | g/plant | Root dry weight |
| `nodule_no` | count/plant | Number of root nodules |
| `nodule_dw_mg` | mg/plant | Dry weight of all nodules on the plant |
| `shoot_n_pct` | % of dry matter | Shoot nitrogen concentration |
| `pod_no` | count/plant | Number of pods |
| `seed_yield_g` | g/plant | Seed yield |

The seven outcome columns appear in the order the experiment declared them in advance.

## Methods

Sixty individually potted chickpea plants were harvested at pod fill, 30 grown from seed treated
with a commercial rhizobial slurry and 30 grown from untreated seed. Every plant was measured for
every outcome.

Each of the seven pre-declared outcomes was compared between the two seed treatments with a
standard two-sample t-test on the plant-level values (`scipy.stats.ttest_ind`, 30 plants per
group). Each outcome was declared in advance as its own agronomic question about inoculation, so
each is decided on its own merits at the conventional threshold of alpha = 0.05. The script
`analysis.py` reads the CSV, hands the data and the declared outcome list to a single reusable
testing step, and states the verdicts from the results that step returns.

## Results

Group means, t statistic, p-value and verdict for each outcome, in the declared order:

| # | Outcome | Inoculated | Uninoculated | Difference | t | p | Verdict at 0.05 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Shoot dry weight (g/plant) | 9.433 | 7.684 | +1.748 | 3.709 | 4.679e-04 | Significant |
| 2 | Root dry weight (g/plant) | 2.603 | 2.216 | +0.387 | 2.907 | 5.155e-03 | Significant |
| 3 | Nodule number (count/plant) | 40.867 | 11.800 | +29.067 | 11.984 | 2.498e-17 | Significant |
| 4 | Nodule dry weight (mg/plant) | 185.000 | 54.003 | +130.997 | 10.518 | 4.611e-15 | Significant |
| 5 | Shoot nitrogen concentration (%) | 3.119 | 2.599 | +0.520 | 6.000 | 1.364e-07 | Significant |
| 6 | Pod number (count/plant) | 26.733 | 23.733 | +3.000 | 2.115 | 3.870e-02 | Significant |
| 7 | Seed yield (g/plant) | 8.190 | 7.440 | +0.750 | 1.569 | 0.122 | Not significant |

Per-outcome conclusions:

1. **Shoot dry weight.** Inoculated plants averaged 9.433 g against 7.684 g untreated, a gain of
   1.748 g per plant (p = 4.679e-04). Significant.
2. **Root dry weight.** 2.603 g against 2.216 g, a gain of 0.387 g per plant (p = 5.155e-03).
   Significant.
3. **Nodule number.** 40.867 nodules against 11.800, a gain of 29.067 nodules per plant
   (p = 2.498e-17). Significant.
4. **Nodule dry weight.** 185.000 mg against 54.003 mg, a gain of 130.997 mg per plant
   (p = 4.611e-15). Significant.
5. **Shoot nitrogen concentration.** 3.119 % against 2.599 %, a gain of 0.520 percentage points
   (p = 1.364e-07). Significant.
6. **Pod number.** 26.733 pods against 23.733, a gain of 3.000 pods per plant (p = 3.870e-02).
   Significant.
7. **Seed yield.** 8.190 g against 7.440 g, a difference of 0.750 g per plant (p = 0.122). Not
   significant.

Six of the seven declared outcomes are significant at 0.05.

## Interpretation

The seed treatment did what a rhizobial inoculant is meant to do. Nodulation responded most
strongly: inoculated plants carried about three and a half times as many nodules and about three
and a half times the nodule mass of plants from untreated seed. Shoot nitrogen concentration rose
by about half a percentage point of dry matter, which is the expected signature of nitrogen
fixation feeding the shoot rather than of any change in soil supply.

That extra nitrogen showed up in growth. Shoot dry weight rose by roughly 1.7 g per plant, about
23 % over the untreated mean, and root dry weight by about 0.4 g per plant. These are moderate
responses next to the nodulation effect, which is the usual pattern: the plant has to convert
fixed nitrogen into biomass before the gain becomes visible.

On the yield side the picture is weaker. Pod number rose by 3.0 pods per plant, and seed yield per
plant was 0.75 g higher for inoculated plants but not distinguishable from the untreated group in
this experiment. For a pulse crop agronomy audience, the practical reading is that the inoculant
established a functioning symbiosis and improved plant nitrogen status and vegetative growth in
these screenhouse pots, while the return in harvestable seed under these conditions was small. Pot
volume restricts root growth and the plants were harvested at pod fill, so a field trial carried
through to maturity is the right place to test whether the growth advantage converts into yield.
