# Algal-oil supplementation and day-60 grade-out in individually reared juvenile cod

## Design

Each row of `data/input.csv` is one juvenile Atlantic cod held alone in its own
flow-through chamber for the entire 60-day trial. Chambers were stocked with one
fish each, fed independently, and weighed once at day 60, so `chamber_id` is
unique across the file and every fish contributes exactly one measurement. No
fish was weighed twice and no chamber held more than one fish, so the 24 rows
are 24 independent units.

## Analysis

The pre-specified endpoint is grade-out: whether a fish reaches the 12.0 g
transfer target by day 60. The 2x2 table of diet by grade-out was tested with
Fisher's exact test (two-sided). Each fish supplies a single Bernoulli outcome
and the cell counts are small, so an exact conditional test is the natural
choice.

## Results

| Diet | Chambers | Reached 12.0 g | Grade-out rate | Mean day-60 mass (g) |
| --- | --- | --- | --- | --- |
| algal_oil | 12 | 9 | 75.0% | 12.87 |
| baseline | 12 | 3 | 25.0% | 11.16 |

Sample odds ratio (algal-oil vs. baseline grade-out): 9.000

[selected-result] Fisher's exact test on the 2x2 diet-by-grade-out table (n = 24 chambers, one fish per chamber): 9 of 12 algal-oil fish versus 3 of 12 baseline fish reached the 12.0 g transfer target, odds ratio 9.000, two-sided p = 0.0391, so the diets differ significantly at alpha = 0.05.

## Notes

Day-60 mass is summarised only for description; the test uses the dichotomised
grade-out outcome. With 12 chambers per diet the p-value is exact, so no
distributional assumption about mass is needed.
