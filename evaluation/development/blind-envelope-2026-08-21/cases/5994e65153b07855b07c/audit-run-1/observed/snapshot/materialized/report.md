# Harvest titer under two fed-batch feeding strategies

## Data description

All results below come from `harvest_titer.csv`, which has one header row and 60 data rows.

**What a single row is.** A row is one protein A HPLC assay of one harvest sample. It is not a
bioreactor run. At the end of each 14-day campaign the operator drew five separate samples from
that reactor's harvest pool and assayed each sample once, so each run supplies five rows that all
describe the same harvested material.

**Columns in the file:**

| Column | What it holds |
|---|---|
| `fermenter_run` | Label of the bioreactor run the sample came from. Twelve distinct values: `RUN-A1` through `RUN-A6` on the standard feed and `RUN-B1` through `RUN-B6` on the enriched feed. The label repeats on all five rows belonging to a run. |
| `feed_strategy` | The feeding schedule used for that run, either `standard` or `enriched`. It is fixed for the whole run, so it is constant across the run's five rows. |
| `sample_replicate` | Which of the five harvest samples the row reports: `S1` to `S5`. The labels are meaningful only inside a run; `S1` in one reactor has nothing to do with `S1` in another. |
| `harvest_viability_pct` | Viable cell percentage measured at harvest, one reading per run. Because it is a run-level measurement it is written identically on all five rows of that run, and it must not be read as five separate measurements. |
| `titer_g_per_l` | Measured antibody titer in g/L for that one assay, to three decimals. This is the outcome, and it is the only column that changes from row to row within a run. |

## Design

Twelve independent 2 L bioreactors were run, six on the standard feed schedule and six on the
enriched feed schedule. Each run was a separate inoculation into a separate vessel followed by a
separate 14-day fed-batch campaign. The feed schedule was set for the whole campaign, which makes
the fermenter run the unit that was assigned to a treatment group and therefore the experimental
unit for this comparison. Sampling five times from a single harvest pool multiplies the number of
rows in the file but does not add process replication: it only tells us how repeatable the HPLC
assay is on material that has already been made.

## How the comparison was done

The five rows within a run are repeat assays of the same harvest, so they are not independent
observations of a feeding strategy. Treating them as if they were would give the test 30 values
per group when only 6 independent campaigns were performed per group, and the extra rows would
carry analytical noise rather than process variability.

The analysis therefore has two steps. First, the five assays of each run were averaged into a
single per-run mean titer, carrying that run's feed strategy along, which turns 60 assay rows into
12 run-level values. Second, those run-level values were compared between the two feed schedules
with an independent two-sample t-test (`scipy.stats.ttest_ind`). The test saw 6 numbers against 6
numbers, one per bioreactor run, and nothing else.

**What entered the test, exactly.** The input to `ttest_ind` was two arrays of per-run mean
`titer_g_per_l`. The first held the six enriched-feed run means (RUN-B1 to RUN-B6) and the second
held the six standard-feed run means (RUN-A1 to RUN-A6). No assay-level row was passed to the
test, and no run contributed more than one number to it.

## Results

Per-run mean titers, each the average of that run's five assays:

| Run | Feed | Mean titer (g/L) | Within-run assay SD (g/L) |
|---|---|---|---|
| RUN-A1 | standard | 3.592 | 0.140 |
| RUN-A2 | standard | 2.849 | 0.077 |
| RUN-A3 | standard | 2.854 | 0.059 |
| RUN-A4 | standard | 2.938 | 0.061 |
| RUN-A5 | standard | 2.554 | 0.056 |
| RUN-A6 | standard | 3.251 | 0.048 |
| RUN-B1 | enriched | 3.971 | 0.087 |
| RUN-B2 | enriched | 3.617 | 0.082 |
| RUN-B3 | enriched | 3.478 | 0.074 |
| RUN-B4 | enriched | 3.240 | 0.059 |
| RUN-B5 | enriched | 3.361 | 0.044 |
| RUN-B6 | enriched | 3.776 | 0.031 |

Group summaries, computed on those run-level values:

| Group | N (runs) | Mean titer (g/L) | SD across runs (g/L) |
|---|---|---|---|
| standard | 6 | 3.006 | 0.363 |
| enriched | 6 | 3.574 | 0.271 |

The enriched schedule delivered 0.568 g/L more titer on average than the standard schedule.

Two-sample t-test on the per-run means: t = 3.0667 on 10 degrees of freedom, p = 0.0119.

**Sample size claimed.** N = 6 per group, 12 in total. That N counts bioreactor runs, not assay
rows. The file contains 30 assay rows per group, but those 30 rows come from 6 independent
campaigns, and 6 is the number the test used and the number this result rests on.

## Assay noise versus process variability

The within-run standard deviations in the table above run from 0.031 to 0.140 g/L, with a pooled
value of 0.073 g/L, which is roughly 2% of a typical titer here. The standard deviation across the
12 run-level means is 0.426 g/L, close to six times larger. The HPLC assay is the small source of
spread in this data set and the reactor campaign is the large one, which is a second reason not to
let assay replicates stand in for runs: they measure the wrong thing at the wrong scale.

## Interpretation and limits

On this data set the enriched feed schedule produced higher harvest titer than the standard
schedule, and the difference is statistically significant at the conventional 5% level
(p = 0.0119). The evidence is six campaigns per arm, so the estimate of the difference is not
tightly pinned down; a confirmation set of runs would narrow it. Nothing here separates which part
of the enriched schedule is responsible, and `harvest_viability_pct` was recorded but not used as a
covariate in this comparison.

## Reproducing this

Run `analysis.py` in the same directory as `harvest_titer.csv`. It reads the CSV, prints the
per-run mean table, the group means and standard deviations, the run counts, the within-run assay
standard deviations, and the t statistic and p-value quoted above. Every number in this report was
taken from that output.
