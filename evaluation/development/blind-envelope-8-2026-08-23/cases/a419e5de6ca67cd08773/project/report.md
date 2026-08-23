# Protein-supplemented straw substrate raises oyster-mushroom flush yield

Production trial write-up. Data: `flush_yields.csv`. Analysis: `analysis.py`.

## The data

The grower ran fourteen independent growing chambers. Seven were filled with straw substrate plus a
protein-rich additive (`supplemented`), and seven with the grower's usual straw substrate
(`standard`). Every chamber kept its substrate for the whole run. Each chamber was harvested over
four successive weekly flushes, and each harvest was weighed on its own.

**One row is one flush from one chamber**: the weight harvested from a single chamber in a single
weekly flush, together with the chamber air temperature recorded at that flush and the number of
days since that chamber was spawned. Fourteen chambers times four flushes gives 56 rows. Rows are
sorted by `chamber_id`, then by `flush_number`.

| column | type | units | what it holds |
|---|---|---|---|
| `chamber_id` | text | — | Identifier of the growing chamber, `CH01` through `CH14`. |
| `substrate` | text | — | Which substrate filled the chamber: `supplemented` or `standard`. |
| `flush_number` | integer | — | Which flush the row records, `1` through `4`, in harvest order. |
| `flush_yield_g` | number, 1 decimal | grams | Harvested mushroom weight from that chamber in that flush. |
| `air_temp_c` | number, 1 decimal | degrees Celsius | Chamber air temperature at that flush. |
| `days_from_spawn` | integer | days | Days from spawning that chamber to that flush. |

There are no missing values. Flush yields run from 770.9 g to 1855.4 g. Air temperature ran from
19.3 C to 23.4 C, and flushes were harvested between 19 and 46 days after spawning.

Yield falls with each successive flush, as expected for this crop. Pooled over all fourteen
chambers, the flush means are 1536.9 g (flush 1), 1321.9 g (flush 2), 1189.8 g (flush 3) and
1049.2 g (flush 4).

## Methods

The trial question is whether the supplemented substrate produces heavier flushes than the standard
substrate. Every recorded flush is a harvest event with its own weight, so each of the 56 rows is a
replicate and all 56 enter the comparison: 28 supplemented flushes against 28 standard flushes.

The two groups were compared with an independent two-sample t-test on `flush_yield_g`, using the
pooled-variance (Student) form, two-sided, at the 0.05 level. Analysis was run in Python with pandas
2.0.3 and SciPy 1.9.1 (`scipy.stats.ttest_ind`). `air_temp_c` and `days_from_spawn` were recorded for
context and were not used in the test.

## Results

| group | n (flushes) | mean flush yield (g) | SD (g) |
|---|---|---|---|
| supplemented | 28 | 1399.2 | 245.6 |
| standard | 28 | 1149.8 | 183.3 |

Supplemented flushes averaged **249.4 g heavier** than standard flushes, a **21.7 % lift** over the
standard mean.

- t(54) = 4.306
- p = 7.05 x 10^-5 (two-sided)

The difference is significant at the 0.05 level, and comfortably so.

The advantage holds at every point in the run rather than coming from one flush:

| flush | supplemented mean (g) | standard mean (g) | difference (g) |
|---|---|---|---|
| 1 | 1701.2 | 1372.7 | 328.5 |
| 2 | 1424.1 | 1219.6 | 204.5 |
| 3 | 1305.5 | 1074.2 | 231.3 |
| 4 | 1165.9 | 932.6 | 233.3 |

## Interpretation and recommendation

Supplementing the straw substrate with the protein-rich additive raised flush yield by roughly
250 g per flush, about a fifth more mushroom per harvest. The gain shows up in the first flush and
persists through the fourth, so the additive is not simply pulling yield forward into an early
harvest and leaving less for later; the whole run is lifted. The usual decline from flush 1 to flush
4 is present in both groups and is unchanged in shape.

Over four flushes the extra yield adds up to roughly 1.0 kg per chamber (4 x 249.4 g).

**Recommendation.** Adopt the supplemented substrate for production, provided the additive costs
less than the value of about 1.0 kg of extra mushroom per chamber per run. At that break-even the
decision turns purely on the additive's price and the handling time to mix it in, since the yield
side of the ledger is clear. Suggested next step: run one production block on the supplemented
recipe and track the additive cost per chamber alongside the harvest weights, so the margin can be
confirmed at commercial scale before the whole facility is switched over.
