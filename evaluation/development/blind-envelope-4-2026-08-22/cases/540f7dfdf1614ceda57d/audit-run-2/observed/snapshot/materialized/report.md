# Bulking agent and the carbon to nitrogen ratio of finished compost

## Question

A municipal composting facility tested two bulking agents for green waste:
shredded wood chip and chopped straw. Sixteen full-scale windrows were built,
eight per agent, and every windrow was managed identically for twelve weeks.
The question is which bulking agent leaves the lower carbon to nitrogen ratio
in the finished compost.

## Data description

The raw file is `compost_cores.csv`. It holds a header row plus **80 data
rows**. **One raw row is one core sample: a single core taken from one point
along one windrow and analysed on its own.** At the end of the twelve-week run,
five cores were taken from evenly spaced points along each of the 16 windrows,
which gives 16 x 5 = 80 core rows.

The file has four columns, in this order.

| # | Column | Type | Description |
| --- | --- | --- | --- |
| 1 | `windrow_id` | text | Identifier of the windrow the core came from. Values `W01` through `W16`, repeated on the 5 rows belonging to that windrow. |
| 2 | `bulking_agent` | text | The bulking agent that windrow was built with. Two values: `woodchip` (W01-W08) and `straw` (W09-W16). Constant within a windrow. |
| 3 | `core_number` | integer | Position label of the core within its windrow, `1` through `5`, following the evenly spaced sampling points along the pile. It is a label, not a measurement. |
| 4 | `c_to_n_ratio` | decimal | Carbon to nitrogen ratio of the finished compost in that core, to one decimal place. This is the outcome. |

`windrow_id` together with `core_number` identifies a row uniquely. There are no
missing values, the design is balanced at 5 cores per windrow and 8 windrows per
group, and the core-level ratios run from 11.0 to 23.2.

**Values entering the statistical comparison: 16.** The 80 core rows are not 80
independent observations. The five cores from a windrow are spatial subsamples
of the same pile, taken because material in a windrow is not perfectly mixed. A
whole windrow was built with one bulking agent, so **the windrow is the unit of
analysis and the core-level rows are the sampling detail sitting behind each
windrow value.** Before the group comparison, each windrow's five cores were
averaged into one representative value, and the comparison used those 16
per-windrow values.

## Method

1. Read the 80 core rows and check the design: four expected columns, no missing
   values, unique `windrow_id` + `core_number`, one bulking agent per windrow.
2. Average the five cores of each windrow into a single per-windrow mean ratio,
   giving 16 values.
3. Compare the two agents with an independent two-sample t-test on those 16
   per-windrow values. Welch's version is the primary test because it does not
   assume the two groups share a variance. The pooled-variance version is
   reported alongside it as a sensitivity check.

Everything is in `analysis.py` at the project root, run with Python 3, pandas
and scipy.

## Results

Per-windrow mean carbon to nitrogen ratio, one value per windrow:

| windrow_id | bulking_agent | cores | windrow mean |
| --- | --- | --- | --- |
| W01 | woodchip | 5 | 17.98 |
| W02 | woodchip | 5 | 18.86 |
| W03 | woodchip | 5 | 19.72 |
| W04 | woodchip | 5 | 19.14 |
| W05 | woodchip | 5 | 17.00 |
| W06 | woodchip | 5 | 19.90 |
| W07 | woodchip | 5 | 16.56 |
| W08 | woodchip | 5 | 19.02 |
| W09 | straw | 5 | 16.66 |
| W10 | straw | 5 | 17.02 |
| W11 | straw | 5 | 16.90 |
| W12 | straw | 5 | 12.52 |
| W13 | straw | 5 | 14.88 |
| W14 | straw | 5 | 15.32 |
| W15 | straw | 5 | 14.74 |
| W16 | straw | 5 | 13.40 |

Group summaries over those per-windrow values:

| bulking_agent | n (windrows) | mean ratio | SD | min | max |
| --- | --- | --- | --- | --- | --- |
| woodchip | 8 | 18.5 | 1.2 | 16.6 | 19.9 |
| straw | 8 | 15.2 | 1.7 | 12.5 | 17.0 |

**Sample size: 8 windrows in the woodchip group, 8 windrows in the straw group,
16 windrows in total.** The 80 core rows stand behind these 16 values; they are
not the sample size for the test.

- Mean ratio, woodchip: **18.5** (18.523)
- Mean ratio, straw: **15.2** (15.180)
- Difference (woodchip minus straw): **3.3** (3.343)
- Welch's two-sample t-test: **t = 4.596, df = 12.92, p = 0.00051**
- 95 percent confidence interval for the difference: **1.77 to 4.92**
- Pooled-variance t-test (sensitivity check): t = 4.596, df = 14, p = 0.00042

The two tests agree closely, so the result does not hinge on the equal-variance
assumption.

## Conclusion

**Chopped straw leaves the lower carbon to nitrogen ratio.** Straw windrows
finished at a mean ratio of 15.2 against 18.5 for wood-chip windrows, a
difference of 3.3 ratio units in favour of straw. With the windrow as the unit
of analysis and 8 windrows per group, the difference is statistically
significant at the 5 percent level (Welch t = 4.596, df = 12.92, p = 0.00051),
and the 95 percent confidence interval for the difference, 1.77 to 4.92, does
not include zero.

Two limits are worth stating. The comparison rests on 16 windrows, so the
confidence interval is wide: the data are consistent with a gap anywhere from
under 2 to nearly 5 ratio units. And the trial ran at one facility over one
twelve-week period, so it does not by itself establish how the two agents would
compare under different feedstock, weather, or turning regimes.
