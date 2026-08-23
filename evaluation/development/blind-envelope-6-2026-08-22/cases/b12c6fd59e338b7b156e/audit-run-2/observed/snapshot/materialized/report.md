# Does a mycorrhizal inoculant improve first-year height of Scots pine seedlings?

## Aim

A forest nursery wants to know whether adding a mycorrhizal inoculant to the growing medium makes
container-grown Scots pine seedlings taller by the end of their first season. The outcome is
seedling height in centimetres (`heightCm`). The comparison is inoculated growing medium against
the same medium without the inoculant.

## Nursery layout

Twelve nursery benches were used. Each bench has its own irrigation valve and was filled with one
batch of growing medium, so a bench is a single self-contained growing environment. Six benches
were given inoculated medium (benches 1, 2, 5, 7, 10, 11) and six were given uninoculated medium
(benches 3, 4, 6, 8, 9, 12). At the end of the first season, fifteen seedlings were measured on
each bench: 12 x 15 = 180 measured seedlings, 90 per treatment.

The important structural point is this. The treatment was applied to a **bench**, not to a
seedling. Every seedling on a bench shared one valve and one batch of medium. So the study has
**12 independent units**, six per treatment, and each unit was measured fifteen times. The 180
seedling rows are 180 measurements, not 180 independent pieces of evidence about the inoculant.

The data bear this out. Bench mean heights inside a single treatment arm are spread widely:

| Treatment | Bench mean heights (cm) | SD of bench means (cm) |
| --- | --- | --- |
| inoculated | 36.18, 36.33, 36.44, 37.79, 38.90, 44.97 | 3.37 |
| uninoculated | 28.29, 28.77, 33.56, 36.93, 37.27, 38.33 | 4.43 |

The two arms overlap: the three highest uninoculated benches (36.93, 37.27, 38.33 cm) sit above
the three lowest inoculated benches (36.18, 36.33, 36.44 cm). Any honest analysis has to carry
that bench-to-bench spread through to the final uncertainty.

## Observed difference

| Treatment | Benches | Seedlings | Mean height (cm) | SD of seedling heights (cm) |
| --- | --- | --- | --- | --- |
| inoculated | 6 | 90 | 38.436 | 5.971 |
| uninoculated | 6 | 90 | 33.860 | 6.173 |

Difference (inoculated minus uninoculated): **4.576 cm**. Because the design is balanced (fifteen
seedlings on every bench), this is also exactly the difference between the two arms' average bench
means.

## The resampling procedure, and why benches are resampled

The primary inference uses a **cluster bootstrap** written from first principles in `analysis.py`.
A bootstrap is a way of asking "if this study were repeated, how much would the answer wobble?" by
rebuilding the study many times out of the data already in hand. The word *cluster* means the
rebuilding is done in whole blocks.

One resample works like this:

1. Inside the inoculated arm, draw 6 benches at random **with replacement** from the 6 inoculated
   benches. A bench can be drawn twice or not at all.
2. Do the same inside the uninoculated arm with its 6 benches.
3. When a bench is drawn, **all fifteen of its seedlings come along as an intact block**. A bench
   drawn twice contributes its fifteen seedlings twice. Seedlings are never picked individually
   and never mixed across benches.
4. Recompute the difference in mean height between the two arms of the rebuilt study.

This is repeated **10,000 times** with a fixed random seed (`20260822`), so the numbers below are
reproducible by re-running the script. Drawing separately within each arm keeps every resample
faithful to the real design: six benches per arm, every time.

**Why benches and not seedlings.** Resampling seedlings would treat each of the 90 seedlings per
arm as its own draw from the population, which is the same as claiming 90 independent observations
per arm. There are 6. Seedlings on one bench are more alike than seedlings from different benches,
because they shared a valve and a medium batch, and that shared bench effect is real and large
here (bench means range from 28.29 to 44.97 cm). Resampling seedlings would let that shared effect
average away as if it were 90 separate accidents instead of 6, which would shrink the estimated
uncertainty far below the truth. Resampling whole benches keeps the bench as the thing that varies,
which matches the thing that was actually randomised.

**The interval.** Across the 10,000 resamples, the differences had a mean of 4.613 cm and a
standard deviation (the bootstrap standard error) of 2.064 cm. The 95% confidence interval is the
2.5th to 97.5th percentile of that distribution:

> **95% CI for the height difference: [0.84, 8.84] cm**

**The p-value.** The bootstrap distribution is centred on what was observed, so on its own it
describes wobble, not a "no effect" world. Subtracting its mean shifts it to be centred on zero
while keeping the same bench-level variability, which turns it into a reference distribution for
"the inoculant does nothing." The two-sided p-value is the share of shifted resamples that land at
least as far from zero as the observed 4.576 cm. That happened in 233 of 10,000 resamples:

> **Resampling p-value: p = 0.0234** (computed as (233 + 1) / (10,000 + 1); the +1 form avoids
> reporting an exact zero, which 10,000 resamples cannot support, so the smallest value this
> procedure could report is 1/10,001 ≈ 0.0001)

## The seedling-level test, shown only for contrast

A plain Welch two-sample t-test run across all 180 individual seedling rows gives t = 5.054,
p = 0.0000011 (1.07e-06).

**This is displayed only for contrast and is not valid for inference here.** It counts the 180
seedlings as if they were 180 independent observations. They are not: the treatment was assigned to
12 benches, so there are 12 independent units. The test therefore credits the study with far more
information than it has, and its p-value is roughly twenty thousand times smaller than the
bench-level one (1.1e-06 against 0.023). No conclusion about the inoculant should rest on it. It is
included here to show how large the distortion is when clustering is ignored: same data, same
observed 4.58 cm difference, wildly different apparent strength of evidence.

## Conclusion

Seedlings grown in inoculated medium were **4.58 cm taller on average** than those in uninoculated
medium (95% CI [0.84, 8.84] cm; cluster bootstrap over benches, p = 0.023). The interval excludes
zero, so the data support a real positive effect of the inoculant on first-year height, but the
interval is wide: the data are consistent with anything from a barely noticeable 0.8 cm gain to a
substantial 8.8 cm gain. The direction is reasonably clear; the size is not pinned down.

**Limits on how far this goes.**

- **Only six benches per arm.** All the uncertainty here rests on six independent units per
  treatment. A percentile cluster bootstrap with so few clusters is known to give intervals that
  are somewhat too narrow, meaning the true coverage is likely below the stated 95% and the real
  p-value is likely somewhat larger than 0.023. The result should be read as moderate evidence, not
  as settled.
- **One nursery, one season, one species.** Nothing here speaks to later years, other species,
  other media, or other sites.
- **Height only.** Root-collar diameter was recorded but was not analysed; it is a secondary
  measurement and no claim is made about it.
- **Simulated data.** These values come from `make_data.py`, not from a real nursery, so the
  numbers illustrate the design and the analysis rather than establishing a horticultural fact.

## Data description

**File.** `seedlings.csv` — one file, one row per measured seedling, all repeated rows kept. No
bench-level averaging or other pre-aggregation was applied. 180 data rows plus one header row.

**What one row represents.** One row is **one measured Scots pine seedling** at the end of its
first growing season: its height and its root-collar diameter, together with the bench it grew on
and that bench's treatment. Rows are not independent units — the fifteen seedlings on a bench are
grouped inside that bench, and the bench is what was assigned to a treatment.

**Columns**, in file order:

| Column | Type | Units | Range in this file | Meaning |
| --- | --- | --- | --- | --- |
| `benchNo` | integer | — | 1–12 | Identifier of the nursery bench the seedling grew on. Each bench has its own irrigation valve and is one independent experimental unit. Appears 15 times, once per seedling on that bench. This is the grouping (cluster) variable used by the bootstrap. |
| `inoculantTreatment` | text | — | `inoculated`, `uninoculated` | Which growing medium the bench received. Constant within a bench. 6 benches (90 seedlings) per value. |
| `seedlingNo` | integer | — | 1–15 | Position number of the seedling within its bench. A within-bench label only: seedling 3 on bench 1 has no connection to seedling 3 on bench 2. The pair (`benchNo`, `seedlingNo`) uniquely identifies a row. |
| `heightCm` | number, 1 decimal | centimetres | 18.7–53.1 | Seedling height at the end of the first growing season. **Primary outcome.** |
| `rootCollarDiamMm` | number, 1 decimal | millimetres | 4.1–8.8 | Stem diameter at the root collar (where stem meets root) for the same seedling. Tracks height: taller seedlings are generally thicker. Secondary measurement, not analysed in this report. |

There are no missing values, and every bench has a complete set of fifteen seedlings.

## Reproducing this

```
/usr/local/bin/python3 make_data.py   # regenerates seedlings.csv (seed 20260822)
/usr/local/bin/python3 analysis.py    # prints every number in this report (seed 20260822)
```

`analysis.py` is the single analysis script at the project root. It uses pandas for data handling
and `scipy.stats.ttest_ind` for the illustrative-contrast t-test only; the cluster bootstrap is
hand-written, with the resampling loop coded directly rather than taken from a library.
