# Bedding material and turkey welfare at twelve weeks

## Design

Sixty commercial turkey poults of the same hatch and strain were reared to twelve weeks of age.
Feeding, stocking density, and ventilation were identical for all birds. The only difference between
the two groups was the floor bedding: 30 birds were reared on chopped straw and 30 birds on softwood
shavings. Each bird was measured individually at the end of the rearing period, so the bird is the
unit of analysis and the two groups are independent.

Six bird-level outcomes were declared before the trial began, in this order: live body weight, breast
yield, footpad dermatitis score, hock burn score, tibia ash content, and plasma corticosterone.

## Data

The analysis reads `turkey_bedding.csv`. One row is one bird, measured once at twelve weeks. The file
has a header row and 60 data rows, with no blank cells.

| Column | What it holds |
| --- | --- |
| `bird_id` | Unique bird identifier, `T001` through `T060`. |
| `bedding` | Bedding group: `chopped_straw` or `softwood_shavings`, 30 birds each. |
| `body_weight_kg` | Live body weight at twelve weeks, in kilograms. |
| `breast_yield_pct` | Breast muscle yield as a percentage of carcass weight. |
| `footpad_score` | Footpad dermatitis score, whole number 0 to 4; 0 is no lesion, 4 is most severe. |
| `hock_burn_score` | Hock burn score, whole number 0 to 2; 0 is no lesion, 2 is most severe. |
| `tibia_ash_pct` | Tibia ash content, percent of dry defatted bone. |
| `plasma_cort_ng_per_ml` | Plasma corticosterone at slaughter, in nanograms per millilitre. |

## Method

For each declared outcome in turn, the two bedding groups were compared with a two-sample t-test that
does not assume equal group variances (Welch's test). The script reports the mean of each group, the
difference between them (straw minus shavings), and the p-value. An outcome is declared significantly
affected by bedding when its p-value is below 0.05.

## Results

Group means, the straw-minus-shavings difference, and the p-value for each declared outcome, in the
declared order:

| Outcome | Chopped straw | Softwood shavings | Difference | p-value | Conclusion |
| --- | --- | --- | --- | --- | --- |
| Live body weight (kg) | 12.60 | 13.40 | -0.80 | 0.0006 | Significantly affected by bedding |
| Breast yield (% of carcass) | 27.10 | 27.15 | -0.05 | 0.8987 | Not significantly affected by bedding |
| Footpad dermatitis score (0-4) | 2.53 | 1.27 | +1.27 | 0.00003 | Significantly affected by bedding |
| Hock burn score (0-2) | 0.70 | 0.50 | +0.20 | 0.2844 | Not significantly affected by bedding |
| Tibia ash (% dry defatted bone) | 48.20 | 49.20 | -1.00 | 0.0462 | Significantly affected by bedding |
| Plasma corticosterone (ng/mL) | 3.60 | 2.40 | +1.20 | 0.0016 | Significantly affected by bedding |

Conclusion drawn for each outcome:

1. **Live body weight.** Birds on softwood shavings were 0.80 kg heavier at twelve weeks than birds on
   chopped straw. Bedding significantly affected body weight.
2. **Breast yield.** The two groups differed by 0.05 percentage points, which is a difference of almost
   nothing. Bedding did not significantly affect breast yield.
3. **Footpad dermatitis score.** Birds on chopped straw scored 1.27 points higher on the 0 to 4 scale,
   the largest effect in the family. Bedding significantly affected footpad dermatitis.
4. **Hock burn score.** Birds on chopped straw scored 0.20 points higher on the 0 to 2 scale, but the
   groups overlapped too much for that gap to clear the threshold. Bedding did not significantly
   affect hock burn.
5. **Tibia ash.** Birds on softwood shavings had 1.00 percentage point more ash in the tibia. The
   p-value of 0.0462 sits just under the threshold. Bedding significantly affected tibia ash.
6. **Plasma corticosterone.** Birds on chopped straw had corticosterone 1.20 ng/mL higher at slaughter.
   Bedding significantly affected plasma corticosterone.

## Welfare interpretation

The picture that comes out of these six comparisons favours softwood shavings. The clearest welfare
signal is footpad dermatitis: birds on chopped straw carried noticeably worse footpad lesions, and
footpad lesions are painful and limit how freely a bird moves. Plasma corticosterone, a stress hormone
measured in the blood at slaughter, was also higher in the straw group, which points the same way.
Straw-reared birds were lighter at twelve weeks and had slightly less mineral in the tibia, so the
bone-strength and growth measures line up with the lesion and stress measures rather than cutting
against them.

Two outcomes showed no significant effect. Breast yield was essentially identical, so the carcass value
of the bird did not depend on the bedding. Hock burn leaned the same direction as footpad dermatitis,
with straw birds scoring higher on average, but the difference in this flock was not large enough to
call.

Taken together, the results support softwood shavings over chopped straw for growing turkeys on
welfare grounds, with the footpad result carrying the most weight because it measures a lesion the
bird lives with every day. These are single-flock results from birds reared under one set of housing
conditions, so confirming them in a second flock would strengthen the case before a producer changes
bedding.
