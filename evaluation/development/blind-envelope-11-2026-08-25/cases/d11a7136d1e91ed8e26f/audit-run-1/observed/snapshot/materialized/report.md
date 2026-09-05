# Tap-water quality on an estate with lead service pipes: filtered against unfiltered kitchen taps

## The question and the design

The estate still has lead service pipes, and about half the occupied households had a
certified point-of-use filter fitted at the kitchen tap during last year's programme. I
wanted to know whether the households with a filter are getting measurably better water
at the tap than the households without one. Our public health laboratory sampled 44
occupied households on a single morning, all under the same standing-time protocol, so
the sampling conditions are as close to identical across households as we can manage in
the field. Twenty-two households had a filter fitted and twenty-two did not. Filter
status is the grouping factor, with those two levels and nothing else. Each household
contributes one set of measurements, and the sampling plan named four outcomes before
any visit took place: first-draw lead, lead after a two-minute flush, first-draw copper,
and first-draw turbidity. I report them here in that declared order.

## Data description

The data file is `tap_water_survey.csv`. It has one header row and 44 data rows. **One
row is one occupied household**, and it holds the four tap-water readings taken at that
household's kitchen tap on the single sampling morning, plus the household's identifier
and its filter status. Every cell is filled in. There are no missing values and no
negative values.

Every column in the file, in file order:

| Column | What it holds |
| --- | --- |
| `household_id` | The household label, `HH-001` through `HH-044`. One per row, no repeats. |
| `first_draw_lead_ug_l` | Lead in the first draw from the kitchen tap, in micrograms per litre, reported to 0.1. |
| `flushed_lead_ug_l` | Lead in the sample taken after the tap ran for two minutes, in micrograms per litre, reported to 0.1. |
| `first_draw_copper_mg_l` | Copper in that same first draw, in milligrams per litre, reported to 0.001. |
| `first_draw_turbidity_ntu` | Turbidity of that same first draw, in nephelometric turbidity units, reported to 0.01. |
| `filter_status` | The grouping factor, with exactly two values: `filtered` (a certified point-of-use filter was fitted at the kitchen tap the previous year) and `unfiltered` (no filter). |

The four measurement columns sit in the file in the order the sampling plan declared
them.

## What the two groups look like

Counts, means, and spread (sample standard deviation) within each group:

| Outcome | Group | Households | Mean | Standard deviation |
| --- | --- | --- | --- | --- |
| First-draw lead (ug/L) | filtered | 22 | 4.082 | 2.434 |
| First-draw lead (ug/L) | unfiltered | 22 | 11.555 | 2.635 |
| Flushed lead (ug/L) | filtered | 22 | 1.109 | 1.063 |
| Flushed lead (ug/L) | unfiltered | 22 | 3.395 | 0.992 |
| First-draw copper (mg/L) | filtered | 22 | 0.278 | 0.142 |
| First-draw copper (mg/L) | unfiltered | 22 | 0.549 | 0.141 |
| First-draw turbidity (NTU) | filtered | 22 | 0.290 | 0.211 |
| First-draw turbidity (NTU) | unfiltered | 22 | 0.410 | 0.126 |

The turbidity spread in the filtered group is wider than in the unfiltered group. Two
filtered households were sampled where disturbed sediment left the first draw visibly
cloudy, and those readings are genuine measured values, so I have kept them in as
measured.

## How I judged significance

All four outcomes were declared together in the same sampling plan, so I treat them as
one family of comparisons rather than four separate studies. That matters because the
more comparisons you run, the easier it becomes for one of them to look impressive by
chance alone. To keep the chance of any false alarm anywhere in the family at the
conventional 5 percent, I used the Sidak correction: with a family of 4 declared
outcomes, the threshold each single comparison has to beat is

    1 - (1 - 0.05) ** (1 / 4) = 0.012741

The analysis script derives that number from the family size rather than carrying it as
a typed-in constant. Every conclusion below was judged against that per-comparison
threshold of 0.012741, not against 0.05. Each comparison itself is a two-sample Welch
t-test of the filtered households against the unfiltered households, which is the
standard test for a continuous measurement across two groups and does not require the
two groups to have equal spread.

## Conclusions, in the declared order

1. **First-draw lead.** Filtered households averaged 4.08 ug/L and unfiltered households
   11.56 ug/L. The p-value is 2.4e-12, far below the 0.012741 threshold, so this is a
   significant difference. First-draw lead is roughly three times higher where no filter
   is fitted, and this is the clearest signal in the survey.

2. **Lead after a two-minute flush.** Filtered households averaged 1.11 ug/L and
   unfiltered households 3.40 ug/L. The p-value is 4.3e-09, below the threshold, so this
   is also significant. Flushing brings both groups down a long way, but the gap between
   them survives the flush.

3. **First-draw copper.** Filtered households averaged 0.278 mg/L and unfiltered
   households 0.549 mg/L. The p-value is 1.3e-07, below the threshold, so this is
   significant too. Copper is roughly twice as high where no filter is fitted.

4. **First-draw turbidity.** Filtered households averaged 0.290 NTU and unfiltered
   households 0.410 NTU. The p-value is 0.027. That sits above the 0.012741 threshold, so
   within this declared family I do not call the turbidity difference significant. The
   means do differ in the expected direction, and the p-value would have cleared an
   uncorrected 0.05 cut, but the family correction is the standard I set before the data
   came in and I am holding to it. The two sediment-affected filtered households widen
   that group's spread and make the comparison less decisive.

Taken together, the three chemistry outcomes point the same way: households on this
estate without a point-of-use filter are drinking water with substantially more lead and
copper in it, both in the first draw and after flushing. Turbidity does not reach the
same standard of evidence here, and I would not report it as a difference on the strength
of this survey.
