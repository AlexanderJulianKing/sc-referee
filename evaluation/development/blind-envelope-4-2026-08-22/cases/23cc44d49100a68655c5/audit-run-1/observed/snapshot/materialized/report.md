# Structural enrichment and strike latency in juvenile common cuttlefish

## Question

Does structural enrichment of the holding tank change hunting motivation in juvenile common
cuttlefish? Hunting motivation is measured here as latency to first tentacle strike after a prey
presentation, in seconds. A shorter latency means the animal struck sooner.

## Data

The single data file is `cuttlefish_strike_latency.csv`. It holds 120 data rows and one header row.

**One row is one prey-presentation trial on one cuttlefish**, recording how long that animal took
to make its first tentacle strike in that trial.

Columns, in the order they appear in the file:

| # | Column | Type | Description |
|---|---|---|---|
| 1 | `animal_ref` | text | Identifier for the individual cuttlefish, `CF-01` through `CF-20`. Repeats across that animal's six rows, and is the grouping key for the repeated measurements. |
| 2 | `housing` | text | Housing condition of the animal, either `enriched` or `bare`. Constant within an animal. |
| 3 | `trial_number` | integer | Which prey presentation this row is, 1 through 6 within an animal. Trials were run on separate days. |
| 4 | `strike_latency_s` | number | Outcome. Latency from prey presentation to first tentacle strike, in seconds, recorded to one decimal place. |

**Counts.** The dataset contains **20 animals** and **120 trials**, six trials per animal. Ten
animals were housed in enriched holdings (sand, rock and artificial weed) and ten in bare holdings,
with 60 trial rows in each housing group. There are no missing values; every animal has a complete
set of trials 1 through 6.

Each animal was housed individually and assigned to one housing condition, so **the animal is the
independent experimental unit**. The six rows within an animal are repeated behavioural trials on
the same individual and are not independent of one another. That is why the analysis below carries
the animal through the model rather than treating the 120 rows as 120 independent observations.

Descriptive figures for the delivered file:

| | enriched | bare |
|---|---|---|
| Animals | 10 | 10 |
| Trial rows | 60 | 60 |
| Mean `strike_latency_s` | 9.56 s | 14.22 s |
| SD across trial rows | 3.37 s | 4.45 s |
| Minimum | 2.6 s | 3.8 s |
| Maximum | 17.2 s | 23.4 s |
| SD of the 10 animal means | 2.68 s | 3.89 s |

## Analysis

**Primary (inferential).** A linear mixed-effects model fitted to the 120 trial-level rows:

```
strike_latency_s ~ housing + (1 | animal_ref)
```

Housing is the fixed effect of interest, coded with `bare` as the reference level, so the housing
coefficient is the enriched-minus-bare difference in seconds. The random intercept for `animal_ref`
is what accounts for the repeated-measures structure: it lets each animal have its own baseline
level, so trials on the same animal are not counted as independent evidence. The model was fitted
with REML in statsmodels 0.14.1, and the p-value is a Wald z-test on the fixed effect.

**Secondary (sensitivity check only).** A plain independent two-sample comparison of means over the
raw trial-level rows, described in its own section below.

Everything reported here comes from `analysis.py`, which reads the CSV and prints these numbers.

## Results

### Primary result: mixed-effects model with a random effect for the animal

| Quantity | Value |
|---|---|
| Housing effect (enriched minus bare) | **−4.66 s** |
| Standard error | **1.49 s** |
| z | −3.12 |
| **p-value** | **0.0018** |
| 95% confidence interval | −7.58 s to −1.73 s |
| Animals (groups) | **20** |
| Trials (rows) | **120** |

The negative sign means enriched animals struck **sooner**. On the model's estimate, an
enriched-housed animal strikes about 4.66 seconds earlier than a bare-housed one.

The model also splits the variation in latency into two parts:

| Source | Estimated SD |
|---|---|
| Between animals (random intercept) | 3.18 s |
| Within an animal, trial to trial (residual) | 2.52 s |

The intraclass correlation is 0.61. In plain terms: about 61 percent of the leftover variation in
strike latency is a stable difference between individual animals rather than trial-to-trial noise.
Two trials on the same cuttlefish are strongly alike, which is exactly why the repeated rows cannot
be treated as independent.

### Secondary sensitivity check: row-level two-sample comparison

**This is a secondary sensitivity check, not the inferential result.**

| Quantity | Value |
|---|---|
| Rows compared | 60 enriched vs 60 bare |
| Group means | 9.56 s vs 14.22 s |
| Difference (enriched minus bare) | −4.66 s |
| Standard error (Welch) | 0.72 s |
| t (Welch) | −6.46, df = 109.87 |
| p (Welch) | 2.9 × 10⁻⁹ |
| t (Student, equal variances) | −6.46, df = 118, p = 2.4 × 10⁻⁹ |

**This row-level comparison ignores the repeated-measures structure of the data.** It treats the
120 trial rows as 120 independent observations, when in fact they are six repeated trials on each
of 20 animals. It is shown only to demonstrate that the direction of the effect is not an artefact
of the modelling choice, and it is **not** the basis for this study's conclusion.

The two analyses agree on the point estimate, both giving −4.66 s, because the design is balanced:
every animal has the same six trials. They disagree sharply on precision. The naive standard error
of 0.72 s is about half the model-based standard error of 1.49 s, so the naive test claims roughly
twice the certainty it is entitled to, and its p-value is smaller by about six orders of magnitude.
That inflation is the direct consequence of counting 120 correlated trials as 120 independent
animals. The mixed model's standard error is the one to believe.

## Conclusion

Stated from the primary mixed-effects model with the animal-level random effect: structural
enrichment shortened latency to first tentacle strike. Juvenile common cuttlefish in enriched
holdings struck 4.66 seconds sooner than bare-housed animals (SE 1.49 s, 95% CI −7.58 s to
−1.73 s, p = 0.0018), based on 20 animals and 120 trials. Read as hunting motivation, animals in
enriched holdings were quicker to attack prey.

Two limits on that conclusion are worth keeping in view. First, the study rests on 20 animals, ten
per housing condition; the six trials per animal sharpen the estimate of each animal's own level
but do not add independent animals. Second, the p-value comes from a Wald z-test, which treats the
sample as large; with 20 groups this is somewhat anti-conservative, so the true p-value is a little
larger than 0.0018. Neither point changes the direction or the rough size of the effect, and the
confidence interval excludes zero comfortably.
