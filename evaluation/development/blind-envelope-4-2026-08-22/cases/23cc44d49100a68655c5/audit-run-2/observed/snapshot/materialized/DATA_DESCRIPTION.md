# Data description

## File

`cuttlefish_strike_latency.csv` — the single data file for this study. It holds 120 data rows
plus one header row.

The file is synthetic. It was produced by `make_data.py`, which uses only the Python standard
library and a fixed random seed, so re-running the script reproduces the file exactly.

## What one row is

One row is **one prey-presentation trial on one cuttlefish**. It records how long that animal took
to make its first tentacle strike in that trial. Each animal contributes six rows, one per trial
day, so rows within an animal are repeated measurements on the same individual and are not
independent of each other.

## Units and counts

| Quantity | Count |
|---|---|
| Animals (independent units) | 20 |
| Trials per animal | 6 |
| Data rows (trials in total) | 120 |
| Animals per housing group | 10 enriched, 10 bare |
| Rows per housing group | 60 enriched, 60 bare |

The 20 animals are the independent units. The 120 rows are not.

## The two groups

Juvenile common cuttlefish were housed individually in one of two conditions.

- **enriched** — holding tanks with sand, rock and artificial weed. Animals `CF-01` through `CF-10`.
- **bare** — holding tanks without that structure. Animals `CF-11` through `CF-20`.

Housing is fixed for an animal: every one of an animal's six rows carries the same `housing` value.

## Columns

Columns appear in the CSV in the order listed here.

| # | Column | Type | Description |
|---|---|---|---|
| 1 | `animal_ref` | text | Identifier for the individual cuttlefish, `CF-01` through `CF-20`. Repeats across the animal's six rows. This is the grouping key for the repeated measurements. |
| 2 | `housing` | text | Housing condition of that animal, either `enriched` or `bare`. Constant within an animal. |
| 3 | `trial_number` | integer | Which prey presentation this row is, 1 through 6 within an animal. Trials were run on separate days. |
| 4 | `strike_latency_s` | number | Outcome. Latency from prey presentation to the first tentacle strike, in seconds, recorded to one decimal place. |

There are no missing values. Every animal has a complete set of trials 1 through 6.

## How the values were generated

Each animal was given its own baseline level, drawn around its group mean, and each trial was then
drawn around that animal's own level:

- group means: 9.6 s for enriched, 14.2 s for bare
- between-animal standard deviation: 3.5 s (temperament differences between individuals)
- within-animal standard deviation: 2.5 s (trial-to-trial variation for the same individual)

Latencies were held above 1 second and below 30 seconds by redrawing the trial-level noise, and
rounded to one decimal place. The random seed was picked from a scan of candidate seeds so that the
two realised group means land close to the 9.6 s and 14.2 s figures the study specifies. Apart from
that choice of seed, the values are a plain draw from the model above; no individual value was
edited by hand.

## What the file actually contains

These are descriptive figures for the delivered file, not analysis results.

| | enriched | bare |
|---|---|---|
| Rows | 60 | 60 |
| Mean `strike_latency_s` | 9.56 s | 14.22 s |
| Standard deviation across rows | 3.37 s | 4.45 s |
| Minimum | 2.6 s | 3.8 s |
| Maximum | 17.2 s | 23.4 s |
| Standard deviation of the 10 animal means | 2.68 s | 3.89 s |

Animal mean latencies span 5.35 s to 21.37 s, and the average spread of the six trials within a
single animal is 2.40 s. Individual animals differ from each other by more than trials on the same
animal differ, which is why the animal has to be carried through the analysis rather than ignored.

No values sit near the 1 s or 30 s recording limits, so the truncation used during generation did
not pile values up at either bound.
