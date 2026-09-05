# Stone milling and roller milling of wholegrain flour

Sixty-six sub-samples were drawn from the mill streams, 33 per method, all from the same
grain lot, milled on alternating days over three weeks. Five flour properties were
measured and the five together form the family of tests. Each property was compared
between methods with a two-sample Welch t-test on the difference in means.

## Threshold

The family-wide error rate is 5 percent across five tests, so the per-outcome threshold
is the Sidak value:

    1 - 0.05        = 0.950000        chance of no false positive anywhere
    exponent 1/5    = 0.200000        one test's share of that
    0.95 ** 0.2     = 0.989794        chance one test alone stays clean
    1 - 0.989794    = 0.010206        per-test threshold

The threshold is 0.010206, and it assumes exactly five tests. Every p-value below is read
against 0.010206, not against 0.05. Sidak is slightly less strict than dividing 0.05 by
five (0.010000), because it accounts for the tests not all failing at once.

## Results

| Outcome | roller | stone | difference | p | against 0.010206 |
|---|---|---|---|---|---|
| damaged starch (%) | 6.97 | 9.25 | -2.28 | 3.7e-12 | below, difference |
| water absorption (%) | 62.5 | 65.8 | -3.3 | 9.0e-10 | below, difference |
| particle size d50 (um) | 142.8 | 199.7 | -56.9 | 2.2e-10 | below, difference |
| tocopherols (mg/kg) | 38.7 | 43.5 | -4.9 | 0.000354 | below, difference |
| falling number (s) | 332 | 319 | 13 | 0.202438 | above, no difference |

Four of the five properties differ. Only falling number does not, and it would not have
differed at a plain 0.05 level either, so the choice of threshold changes no decision in
this data set.

## What it means for bakers

Stone milling grinds coarser and hits the starch harder at the same time. Median particle
size is about 57 micrometres larger, yet damaged starch is 2.3 percentage points higher.
Damaged starch takes up water, which is what shows up in the farinograph: stone-milled
flour absorbs about 3.3 percentage points more water. In practice that means a wetter
dough at the same flour weight, so a baker moving from roller to stone flour should expect
to add water rather than assume the recipe carries over. Higher damaged starch also feeds
the yeast faster, so watch proof times.

Tocopherols run about 5 mg/kg higher in the stone flour, which fits the gentler separation
of the germ, and is a small nutritional point in favour of stone milling. Falling number
sits near 320 to 330 seconds for both, well clear of the sprout-damage range, so
alpha-amylase activity is not a reason to prefer one mill over the other here.

One caution on scope. All of this comes from a single grain lot on one pair of mills. The
direction of these effects is standard for the two milling actions, but the sizes belong
to this lot, and a baker changing wheat as well as mill should re-check absorption.
