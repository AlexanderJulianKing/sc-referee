# Day-14 kimchi brining trial: 2.0% versus 3.0% brining salt

## What was compared, and why

We ran a side-by-side trial of a 2.0 percent and a 3.0 percent brine to see
how brine salt level shifts a napa cabbage kimchi ferment. Forty-four small fermentation containers were filled
from one homogenised batch of shredded cabbage and seasoning, twenty-two
brined at each salt level. Every container was held at 4 degrees Celsius and
opened once, on day 14, for measurement. Five quality attributes were declared
before fermentation started: pH, titratable acidity, lactic acid bacteria
count, firmness, and panel sourness. Each attribute answers a different
practical question about the product, so each is treated here as its own
question.

## The data

`data.csv` has 44 rows plus a header row. **One row is one fermentation
container**, measured a single time on day 14. There are no blank cells.

- `container_id`: container label, `C01` through `C44`, one per row.
- `salt_pct`: brining salt level of that container, either `2.0` or `3.0`
  percent salt in the brine. This is the group column.
- `ph`: pH of the fermented product on day 14, unitless.
- `titratable_acidity_pct`: titratable acidity as percent lactic acid by mass.
- `lab_count_log10_cfu_g`: lactic acid bacteria count, log10 colony forming
  units per gram.
- `firmness_n`: peak penetration force in newtons.
- `sourness_score`: sourness rated by a trained panel on a 1 to 9 scale,
  reported as the panel mean for that container.

## What the analysis did

`analysis.py` reads `data.csv`, splits the containers into the 2.0 percent and
3.0 percent groups, and steps through the five declared outcomes in their
declared order. For each outcome it runs an independent two-sample t-test on
the two groups of containers and prints the group sizes, the group means and
standard deviations, and the p-value. An outcome is called different when its
own p-value falls below 0.05.

## Conclusions, outcome by outcome

1. **pH.** The 2.0 percent containers finished at mean 4.079 (SD 0.094) against
   4.384 (SD 0.094) at 3.0 percent, p = 1.2e-13. Lower salt gives a clearly
   lower final pH.
2. **Titratable acidity.** 0.935 percent lactic acid (SD 0.073) at 2.0 percent
   salt against 0.672 percent (SD 0.062) at 3.0 percent, p = 3.4e-16. The
   low-salt ferments are clearly more acidic.
3. **Lactic acid bacteria count.** 8.083 log10 CFU/g (SD 0.337) against 8.071
   (SD 0.351), p = 0.91. No significant difference; the two brines end up with
   the same population size.
4. **Firmness.** 12.77 N (SD 1.66) at 2.0 percent salt against 13.80 N
   (SD 1.44) at 3.0 percent, p = 0.033. The higher-salt cabbage is firmer.
5. **Panel sourness.** 5.61 (SD 0.94) against 5.85 (SD 1.03), p = 0.44. No
   significant difference in how sour the panel found the two products.

Both salt levels reach a full ferment by day 14. The 2.0 percent brine buys
more acid and a lower pH, and gives up a little firmness, while the panel rated
the two products as equally sour.
