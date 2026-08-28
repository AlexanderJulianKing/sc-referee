# Irrigation water quality and quinoa performance in a screenhouse trial

## Data

The analysis uses `data.csv`, in which one row is one harvested quinoa plant in its own
pot. The file holds 48 plants and six columns. `plant_id` is the plant and pot
identifier, a text label running from `qn01` to `qn48` with no unit. `irrigation_water`
records the water the pot was allocated to and takes one of two text labels, `fresh`
(about 0.8 dS/m) or `brackish` (about 12 dS/m). `grain_yield_g` is that plant's grain
yield at harvest in grams. `thousand_seed_weight_g` is the thousand-seed weight of that
plant's grain in grams. `plant_height_cm` is the plant's height at maturity in
centimetres. `leaf_sodium_mg_g` is the sodium concentration of the plant's leaf tissue in
milligrams per gram of leaf dry matter. Every plant has a value for every outcome.

## Design and declared outcomes

Forty-eight individually potted plants of a single quinoa cultivar were sown on the same
day in the same growing medium and randomly allocated to the two irrigation waters, 24
pots to fresh water and 24 to brackish water. The pots differed in nothing else. Plants
were grown to maturity and harvested and measured individually. The trial protocol
declared four outcomes before any plant was harvested, in this order: grain yield per
plant, thousand-seed weight, plant height at maturity, and leaf sodium concentration.

## How the comparison was done

Each declared outcome was compared between the fresh and brackish groups with one
two-sample Welch t-test for independent groups, taking the plant as the unit. Group
sizes were 24 and 24 for every outcome. Each outcome was judged on its own p-value
against the conventional 0.05 threshold.

## Results

Grain yield averaged 18.52 g under fresh water (SD 3.31 g) and 15.22 g under brackish
water (SD 4.34 g), a difference of 3.30 g in favour of fresh water; t = 2.957, p =
0.0050, which is significant at 0.05.

Thousand-seed weight averaged 3.09 g under fresh water (SD 0.34 g) and 2.88 g under
brackish water (SD 0.30 g), a difference of 0.22 g; t = 2.310, p = 0.0255, which is
significant at 0.05.

Plant height at maturity averaged 108.39 cm under fresh water (SD 10.43 cm) and 110.08
cm under brackish water (SD 11.07 cm), a difference of -1.69 cm; t = -0.544, p = 0.5894,
which is not significant at 0.05.

Leaf sodium concentration averaged 2.57 mg/g under fresh water (SD 1.04 mg/g) and 6.43
mg/g under brackish water (SD 1.25 mg/g), a difference of -3.86 mg/g, so brackish plants
carried more sodium; t = -11.609, p < 0.0001, which is significant at 0.05.

## What the trial found

Irrigating with brackish water at about 12 dS/m left a clear mark on the plants. Leaf
sodium was far higher under brackish water, and grain yield and thousand-seed weight
were both lower, each by an amount that reached the 0.05 threshold on its own test.
Plant height at maturity was close to the same in the two groups. In this cultivar and
this screenhouse setting, the cost of brackish irrigation showed up in sodium
accumulation and in what the plants put into grain rather than in how tall they grew.
