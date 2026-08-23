# Environmental enrichment and recognition memory in adult rats

## Data description

The data file is `data.csv`. It has one header line and 144 data rows.

**One row is one novel-object recognition test run by one rat on one day.** A row is not an
animal. Each of the 18 rats was tested eight times, on separate days with a different object pair
each time, so **every rat appears on eight rows** of the file. The eight rows belonging to a rat are
not independent of one another, because they come from the same animal.

- Test runs (rows): 144
- Rats (animals): 18, nine enriched and nine standard
- Rows per housing group: 72 enriched, 72 standard
- No missing values, no duplicate `rat_id` + `run_number` pairs, all 18 rats have all eight runs

Columns, in file order:

| # | Column | Type | Units / values | What it holds |
| --- | --- | --- | --- | --- |
| 1 | `rat_id` | text | `BN-101` to `BN-118` | The animal code. Repeats on the eight rows belonging to that rat. 18 distinct values. |
| 2 | `housing` | text | `enriched` or `standard` | The housing condition. Assigned to the whole animal, so it is the same on all eight of a rat's rows. |
| 3 | `run_number` | integer | 1 to 8 | Which of that rat's eight test sessions this row is. `rat_id` plus `run_number` identifies a row. |
| 4 | `exploration_time_s` | number, 1 decimal | seconds, 15.0 to 45.0 | Total time the rat spent exploring both objects on that run. Observed mean 30.08 s. |
| 5 | `discrimination_index` | number, 3 decimals | proportion, 0 to 1 | The outcome. Share of that run's exploration time spent on the novel object. 0.5 means no preference; higher means more time on the novel object. Observed run values run 0.496 to 0.666 for standard rats and 0.575 to 0.786 for enriched rats. |

## Methods

Housing was assigned to whole animals, not to individual test runs, so **the rat is the independent
experimental unit** and the 144 runs are not 144 independent observations.

The analysis therefore works in two steps, both in `analysis.py`:

1. **Reduce to the animal.** Average each rat's eight discrimination-index values into that rat's
   single mean. This turns 144 rows into 18 values, one per rat.
2. **Compare the groups.** Run an independent two-sample t-test (Welch's version, which does not
   assume the two groups share a variance) on the difference in means of those 18 per-animal values.

The data file itself is left at run level with all eight runs per rat. The reduction happens only
inside the analysis.

## Results

Sample size: **18 rats** (9 enriched, 9 standard). The values below are per-animal means, so the
spread is variation between animals, not between runs.

| Housing | n (rats) | Mean discrimination index | SD | Min | Max |
| --- | --- | --- | --- | --- | --- |
| enriched | 9 | 0.6792 | 0.0328 | 0.6295 | 0.7380 |
| standard | 9 | 0.5786 | 0.0261 | 0.5491 | 0.6212 |

Difference in means (enriched minus standard): **0.1006**, standard error 0.0140, 95% confidence
interval 0.0709 to 0.1304.

Welch's independent two-sample t-test: **t = 7.195, df = 15.24, p = 2.83e-06**.

## Interpretation

Rats in enriched housing spent a larger share of their exploration time on the novel object than
rats in standard housing. The gap averages about 0.10 on the discrimination-index scale, roughly
0.68 against 0.58. The test is significant at the 0.05 level, and the confidence interval keeps the
difference between about 0.07 and 0.13, so the direction of the effect is clear across that range.

Two limits are worth stating. The p-value describes 18 animals, not 144 runs. Counting each run as
its own observation would inflate the apparent sample size, because runs within a rat share the same
animal. And with nine rats per group the difference rests on a small number of independent units, so
the width of the interval, not the p-value alone, is the honest summary of how precisely the effect
is pinned down.
