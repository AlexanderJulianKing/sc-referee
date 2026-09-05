# Firm tofu: calcium sulfate versus glucono-delta-lactone

## Data

`data.csv` holds one row per tofu block, and nothing else. A single row is one finished block,
measured the day after pressing. The columns are:

- `block_id` — identifier for the block, `blk_01` through `blk_60`, in production run order (no unit).
- `coagulant` — the coagulant used, either `caso4` (calcium sulfate) or `gdl` (glucono-delta-lactone) (no unit).
- `yield_g_per_100g` — tofu yield, grams of pressed tofu per 100 g of dry soybeans.
- `hardness_n` — hardness at 30 percent compression, in newtons.
- `syneresis_pct` — liquid released after 24 hours of refrigerated storage, as a percentage of block weight.
- `whiteness_index` — whiteness index of the block surface, unitless on a 0 to 100 scale.
- `protein_g_per_100g` — protein content, grams per 100 g of fresh tofu.
- `ph` — pH of the pressed block, unitless.

## Design

Sixty tofu blocks were made in a pilot plant, each from its own 500 g batch of the same soybean
lot on the same equipment. Thirty blocks were coagulated with calcium sulfate and thirty with
glucono-delta-lactone; every other process setting was held constant. The block is the
experimental subject, so the two groups contain 30 independent blocks each.

The outcome family was declared in the study plan, in this order, before any block was made:
yield, hardness, syneresis, whiteness index, protein content, and pH.

## How the comparison was done

`analysis.py` reads `data.csv`, counts the blocks in each group, and then works through the six
declared outcomes in the declared order, doing the same steps for each one: it takes the mean and
standard deviation within each coagulant group, then compares the two groups with a two-sample
Welch t-test, which does not assume the two groups share a variance. Each outcome is a separate
quality question, so each one gets its own verdict at the conventional 0.05 threshold, read
directly from that outcome's own p-value.

## Results

Values below are calcium sulfate first, then lactone, as mean (standard deviation).

**Yield.** 242.4 (15.0) versus 262.9 (15.0) g per 100 g dry soybeans, a difference of -20.5.
Welch t = -5.297, p = 0.000002, so the difference is significant: lactone blocks yield more.

**Hardness.** 4.14 (0.60) versus 3.05 (0.60) N, a difference of 1.09. Welch t = 7.067,
p < 0.000001, so the difference is significant: calcium sulfate blocks are firmer.

**Syneresis.** 5.98 (1.50) versus 8.02 (1.50) percent of block weight, a difference of -2.03.
Welch t = -5.246, p = 0.000002, so the difference is significant: lactone blocks release more
liquid in storage.

**Whiteness index.** 78.3 (1.6) versus 79.9 (1.6) on the 0 to 100 scale, a difference of -1.6.
Welch t = -3.906, p = 0.000248, so the difference is significant: lactone blocks are slightly
whiter.

**Protein content.** 15.63 (0.90) versus 15.41 (0.90) g per 100 g fresh tofu, a difference of
0.22. Welch t = 0.950, p = 0.345956, so the difference is not significant at the 0.05 threshold.

**pH.** 6.09 (0.15) versus 5.60 (0.15), a difference of 0.49. Welch t = 12.703, p < 0.000001, so
the difference is significant: lactone blocks are more acidic.

## What the study found

The two coagulants gave clearly different blocks on five of the six declared outcomes. Calcium
sulfate produced firmer, less acidic blocks that held their liquid better in refrigerated storage.
Glucono-delta-lactone produced a higher yield per 100 g of dry soybeans and a slightly whiter
surface, at the cost of softer blocks with more syneresis and a lower pH. Protein content was the
one outcome where the two coagulants did not differ at the 0.05 threshold, at about 15.4 to 15.6 g
per 100 g of fresh tofu in both groups.
