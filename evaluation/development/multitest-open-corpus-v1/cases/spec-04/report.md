# Long cold sourdough fermentation versus a commercial yeast process

## Design

Seventy loaves were baked, 35 by a long cold sourdough fermentation and 35 by the
standard commercial yeast process, from one flour lot in one oven. Each loaf is an
independent bake and contributes one row. Six quality outcomes were compared between
processes with Welch's two-sample t-test.

## Correction

Six tests were run, so the six raw p-values were held together as one family and put
through a single **Holm-Bonferroni step-down** correction (`multipletests(...,
method='holm')` from statsmodels) at a family-wide level of five percent. Holm controls
the family-wise error rate, meaning the chance of making even one false claim anywhere
across the six. The family is all six quality outcomes, no subsets and no separate
passes. Every verdict below reads the adjusted p-value.

## Results

| Outcome | Yeast | Sourdough | Raw p | Holm p | Verdict |
|---|---|---|---|---|---|
| specific_volume_ml_g | 4.381 | 3.946 | 1.1e-04 | 2.1e-04 | significant |
| crumb_hardness_n | 4.041 | 3.966 | 0.761 | 0.761 | not significant |
| staling_rate_n_per_day | 1.168 | 0.788 | 1.6e-07 | 4.7e-07 | significant |
| ph_final | 5.543 | 4.404 | 9.6e-40 | 5.8e-39 | significant |
| phytate_mg_100g | 217.6 | 134.2 | 2.8e-12 | 1.1e-11 | significant |
| sensory_sourness | 1.954 | 5.817 | 1.5e-30 | 7.3e-30 | significant |

Five of the six differences survive correction. Crumb pH and panel sourness separate
the two processes almost completely, which is the expected signature of organic acid
production during a long cold ferment and is really a manipulation check rather than a
finding. On top of that, sourdough loaves lost about 0.44 mL/g of specific volume,
staled about a third more slowly (0.79 versus 1.17 N per day), and retained 38 percent
less phytate (134 versus 218 mg per 100 g).

Day-1 crumb hardness is the one outcome that does not separate the processes: 4.04 N
for yeast against 3.97 N for sourdough, raw p = 0.76. The four margins that matter are
wide enough that Holm's step-down barely moves them; the smallest of them, specific
volume, goes from 1.1e-04 raw to 2.1e-04 adjusted and stays comfortably significant.

## Reading

The trade is volume for keeping quality and mineral availability. Sourdough gives up
about ten percent of specific volume, which a consumer sees as a denser loaf, and buys
back a slower staling rate and a large cut in phytate, which is the compound that binds
iron and zinc in wholegrain bread. Since day-1 hardness is the same and the staling
rate differs, the two processes start at the same crumb firmness and diverge across the
five days; shelf life, not fresh texture, is where sourdough wins. The sourness score
near 5.9 out of 10 is a product decision rather than a defect, but it does mean the two
loaves are not interchangeable on the same shelf.
