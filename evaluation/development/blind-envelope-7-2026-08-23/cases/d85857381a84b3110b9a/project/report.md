# Wash validation: peracetic acid vs. standard chlorine wash

**Bagged leaf salad line, June 2026 production**
Prepared by the plant food safety microbiologist

## Purpose

We ran a routine validation to see whether the peracetic acid wash under evaluation
lowers aerobic plate count on finished bagged leaf salad compared with our standard
chlorine-based wash.

## Data description

All results are in one file, `pack_plate_counts.csv`, 100 data rows plus a header.

**One row is one sealed retail pack, pulled at random off the line from one production
batch and plated on its own.**

| Column | What it holds |
| --- | --- |
| `batch_id` | Identifier for the production batch the pack came from, `B01` to `B20`. |
| `wash_treatment` | The wash that batch received: `chlorine` or `peracetic_acid`. |
| `pack_id` | Identifier for the individual retail pack, e.g. `B01-P3`. |
| `production_date` | Date the batch was produced (`YYYY-MM-DD`). |
| `aerobic_plate_count_log_cfu_g` | Aerobic plate count for that pack, log10 CFU/g. |

## Design

Twenty production batches were made over four production weeks, 1 June to 26 June 2026,
one batch per production day. Ten batches were washed in the standard chlorine wash and
ten in the peracetic acid wash. The two washes were balanced within each week and the
running order was shuffled inside each week. Five sealed retail packs were pulled at
random from each finished batch and each pack was plated separately, giving 100 pack
results. Counts ran from 2.86 to 5.81 log CFU/g.

## Method

The wash is applied to a whole batch, so the batch is the unit that was assigned to a
treatment. The five packs from a batch are repeat measurements of that one batch, not
five independent trials of the wash. Before any comparison, therefore, the five pack
results from each batch were combined into a single batch-level mean log count. That
reduction is done in one named step of `analysis.py` (`reduce_packs_to_batches`), which
the main flow calls once, and the comparison is run on exactly the table it returns.

The comparison is a standard independent two-sample t-test of the difference in mean
log count between the two washes. The sample size for that test is the number of
batches per wash: **10 chlorine batches and 10 peracetic acid batches**.

Packs within a batch scattered by about 0.29 log units on average, so combining five of
them into one batch value trims most of the pack-to-pack plating noise.

## Result

| Wash | Batches | Mean batch log count (log10 CFU/g) | SD |
| --- | --- | --- | --- |
| Chlorine (standard) | 10 | 4.762 | 0.519 |
| Peracetic acid | 10 | 4.041 | 0.484 |

Difference (chlorine minus peracetic acid): **0.721 log CFU/g**, 95% confidence interval
0.250 to 1.193 log CFU/g.

Independent two-sample t-test: **t(18) = 3.214, p = 0.0048**, n = 10 batches per wash.

## Interpretation and recommendation

The peracetic acid wash gave a mean aerobic plate count about 0.72 log CFU/g lower than
the standard chlorine wash, roughly a five-fold reduction in counts on finished product,
and the difference is clear against the batch-to-batch variation we saw (p = 0.0048).
The confidence interval runs from 0.25 to 1.19 log, so the size of the benefit is not
pinned down tightly; the honest reading is a real but moderately sized improvement. That
said, twenty batches over four weeks is a short window, and this trial measured aerobic
plate count only, not pathogen control or shelf life.

**Recommendation:** proceed to an extended line trial of the peracetic acid wash, running
it as the standard wash on one line for a full quarter while continuing routine aerobic
plate count monitoring, and add shelf-life panels and the usual pathogen verification
before any plant-wide changeover. Confirm the peracetic acid concentration, contact time,
and rinse steps used here are written into the sanitation SOP so the trial condition is
the one that carries forward.
