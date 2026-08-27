# Edible coating on fresh-cut mango: day-eight shelf-life report

## Data

The analysis reads one file, `mango_coating_shelf_life.csv`, at the project root.

One row is one retail pack of mango slices, measured once on day eight of storage. Each pack
appears exactly once. There are 60 data rows plus a header row, and no blank cells.

| # | Column | Units | What it holds |
|---|--------|-------|---------------|
| 1 | `pack_id` | none | Pack identifier, `PK-01` through `PK-60`, unique per row |
| 2 | `coating` | none | Group label, either `coated` or `uncoated` |
| 3 | `firmness_n` | newtons | Slice firmness by penetrometer, 1 decimal place |
| 4 | `browning_index` | unitless, 0 to 100 | Surface browning from image analysis, higher means more browning, 1 decimal place |
| 5 | `tss_brix` | degrees Brix | Total soluble solids in the expressed juice, 1 decimal place |
| 6 | `weight_loss_pct` | percent | Pack weight lost over storage, as a percent of starting pack weight, 2 decimal places |
| 7 | `aerobic_count_log10_cfu_per_g` | log10 CFU/g | Mesophilic aerobic plate count on a base-10 log scale, 2 decimal places |

Columns 3 through 7 are the five pack-level outcomes the laboratory declared before the trial,
listed here in that declared order.

## Design and group sizes

Sixty retail packs were prepared on the same day from the same fruit batch. Thirty packs were
dipped in a chitosan and ascorbic acid edible coating before packing, and thirty packs were
packed uncoated. All sixty packs were stored at 5 degrees Celsius and assessed individually on
day eight. The same five measurements were taken on every pack. Group sizes are 30 coated and
30 uncoated, 60 packs in total.

## The gated design

The analysis runs in two stages, and the second stage is gated behind the first.

Stage 1 computes one overall screening number from all five outcome columns at once. It is the
largest absolute standardised difference between the two group means across the five outcomes.
A standardised difference is the gap between the two group means measured in units of the
pooled within-group spread, so it puts newtons, Brix, and log counts on one common ruler. The
screen uses only elementary array arithmetic on the outcome columns: group means, group
spreads, a difference, a ratio, an absolute value, and a maximum. It uses no statistical test,
no p-value, and no model. The screen passes when the screening number is at least 0.5.

Stage 2 compares the two coating groups on each of the five declared outcomes. **No per-outcome
comparison is performed or reported unless the overall screen passes first.** If the screen does
not pass, the script stops at the end of Stage 1, states that the screen did not pass, and
produces no per-outcome results at all.

## Stage 1 result: the overall screen

| Outcome | Mean coated | Mean uncoated | Absolute standardised difference |
|---------|-------------|---------------|----------------------------------|
| Slice firmness (N) | 18.723 | 11.080 | 3.599 |
| Surface browning index | 18.953 | 38.047 | 3.705 |
| Total soluble solids (Brix) | 14.970 | 15.057 | 0.069 |
| Pack weight loss (%) | 4.054 | 4.710 | 0.515 |
| Aerobic plate count (log10 CFU/g) | 3.426 | 5.023 | 2.889 |

**Screening number = 3.705**, the largest of the five values above, driven by the surface
browning index. The threshold is 0.5.

**Screen outcome: PASSED.** The gate opens, so the per-outcome branch below is the branch that
ran.

---

## Stage 2 result: per-outcome comparisons (screen passed branch)

Each of the five pre-declared outcomes was compared between the coated and uncoated groups with
a two-sample Welch t-test, which does not assume the two groups share the same variance. The
five outcomes are one pre-declared family, and the protocol requires complete-family control of
the family-wise error rate, so the Holm step-down procedure was applied across all five raw
p-values at a family-wise alpha of 0.05. Holm keeps the chance of any false positive anywhere in
the family at 5 percent, the way a single test keeps it at 5 percent on its own. Verdicts below
use the Holm-adjusted p-values. Differences are coated minus uncoated.

| Outcome | Mean coated | Mean uncoated | Difference | t | df | Raw p | Holm p | Verdict |
|---------|-------------|---------------|-----------|---|----|-------|--------|---------|
| Slice firmness (N) | 18.72 | 11.08 | +7.64 | 13.94 | 50.7 | 5.6e-19 | 2.3e-18 | Significant |
| Surface browning index | 18.95 | 38.05 | -19.09 | -14.35 | 52.7 | 7.8e-20 | 3.9e-19 | Significant |
| Total soluble solids (Brix) | 14.97 | 15.06 | -0.09 | -0.27 | 57.7 | 0.789 | 0.789 | Not significant |
| Pack weight loss (%) | 4.05 | 4.71 | -0.66 | -1.99 | 56.9 | 0.051 | 0.102 | Not significant |
| Aerobic plate count (log10 CFU/g) | 3.43 | 5.02 | -1.60 | -11.19 | 53.5 | 1.3e-15 | 3.8e-15 | Significant |

### Conclusions

Three of the five declared outcomes separate the two groups after family-wise correction.

- **Firmness.** Coated packs were firmer by 7.64 N on average, 18.72 N against 11.08 N. This is
  a large effect and it survives correction with a wide margin.
- **Browning.** Coated packs browned far less, 18.95 against 38.05 on the 0 to 100 index, a
  difference of 19.09 index points in the direction the coating is meant to help.
- **Microbial load.** Coated packs carried 1.60 fewer log10 CFU/g, 3.43 against 5.02, which is
  about a 40-fold lower count on the raw colony-count scale.
- **Weight loss.** Coated packs lost 0.66 percentage points less weight, 4.05 percent against
  4.71 percent. This one is marginal. Its raw p-value of 0.051 sits right on the conventional
  0.05 line, and after Holm correction the adjusted p-value is 0.102, so it does not clear the
  family-wise bar. Read it as suggestive and unresolved, not as evidence of no effect. A larger
  trial would be needed to settle it.
- **Total soluble solids.** The two groups are effectively the same, 14.97 against 15.06 Brix, a
  gap of 0.09 Brix with a raw p-value of 0.789. The coating does not appear to change sugar
  content at day eight.

Taken together, the coating held firmness, held back browning, and lowered microbial counts on
day eight, left soluble solids alone, and showed a weight-loss advantage too small to confirm at
this sample size.

### Scope and limits

These results come from one batch of fruit prepared on one day and assessed at one time point,
so they speak to day eight under 5 degrees Celsius storage for this batch. They do not establish
a time course, and they do not separate the chitosan from the ascorbic acid, since the two were
applied together as a single coating. The values in the CSV are simulated, not measurements from
a real laboratory, as recorded in `DATA_DESCRIPTION.md`.
