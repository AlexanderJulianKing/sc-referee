# Mycorrhizal inoculant and fruit sweetness in potted highbush blueberry

## What we did

We wanted to know whether a mycorrhizal inoculant applied at planting changes the sweetness of the
fruit. We grew 24 highbush blueberry bushes in identical pots under one polytunnel. Twelve bushes
got the inoculant at planting and twelve got nothing. At harvest the technician picked five separate
berry clusters from each bush and read the juice of each cluster on a refractometer, recording
soluble solids in degrees Brix. That gives 120 cluster readings in all.

## The data

One file, `blueberry_brix_clusters.csv`, holding all 120 cluster readings with no processing applied.

**One row is one berry cluster from one bush: a single refractometer reading.** A row is not a bush.
Each bush contributes five rows, one for each cluster we picked from it.

| Column | What it holds |
| ------ | ------------- |
| `bush_label` | The pot label of the bush the cluster came from, `BB-01` through `BB-24`. This is the experimental unit. Each label appears in exactly five rows. |
| `treatment` | The inoculation treatment that bush got at planting: `inoculated` or `uninoculated`. It is fixed for a bush, so all five rows for a bush carry the same value. |
| `cluster_number` | Which of that bush's five picked clusters the reading came from, 1 to 5. It is a label within the bush only; cluster 3 on one bush has nothing to do with cluster 3 on another. |
| `soluble_solids_brix` | The refractometer reading on that cluster's juice, in degrees Brix, to one decimal place. This is the outcome we measured. |

The file has 120 data rows plus a header, covering 24 bushes with five clusters each and no missing
readings. Individual cluster readings ran from 10.1 to 15.1 degrees Brix.

## How we analysed it

We applied the inoculant to whole bushes, one decision per bush, so **the bush is the experimental
unit**. The five clusters we picked off a bush are subsamples of that bush, not independent
observations. Clusters from the same bush bore this out: the spread between clusters on one bush was
about 0.34 degrees Brix, while bush means within a treatment group spread by about 1.00 degrees Brix.
Clusters on the same bush really do resemble each other more than clusters on different bushes.

Treating those 120 cluster readings as 120 independent observations would count each bush five times
over and make the study look far more precise than it is. So before comparing anything we **averaged
each bush's five cluster readings into one value per bush**, which turned 120 cluster rows into 24
bush values. The comparison of the two treatments used those per-bush values only.

**The sample size for the comparison is 24 bushes: 12 inoculated and 12 uninoculated.**

We compared the two groups with Welch's two-sample t test, which does not assume the two groups share
the same variance.

## What we found

| Group | Bushes | Mean Brix | SD |
| ----- | ------ | --------- | -- |
| Inoculated | 12 | 12.63 | 1.22 |
| Uninoculated | 12 | 12.18 | 0.77 |

The inoculated bushes averaged 0.45 degrees Brix higher than the uninoculated ones. The 95 percent
confidence interval on that difference runs from -0.42 to +1.32 degrees Brix, and the test gives
t = 1.08 on 18.5 degrees of freedom, p = 0.29.

## What we take from it

This trial does not show that the inoculant changes fruit sweetness. The inoculated bushes came out
sweeter on average, but the difference is small next to how much the bushes varied among themselves,
and the confidence interval comfortably includes no difference at all.

The interval is also wide. It is consistent with the inoculant doing nothing, and equally consistent
with it adding something over a degree Brix, which would matter commercially. With 12 bushes per
group and bush-to-bush variation near 1.0 degrees Brix, this study was never going to settle a
difference of this size. Picking more clusters per bush would not have helped much either, since the
cluster-to-cluster spread was already the smaller of the two sources of variation. Anyone wanting to
resolve an effect this size should plan on more bushes per group rather than more clusters per bush.

One caution on scope: all 24 bushes sat under a single polytunnel in one season, so we cannot
separate the treatment from anything particular to that tunnel or that year.
