# Mycorrhizal inoculant in spring wheat

Spring wheat was sown with or without a commercial arbuscular mycorrhizal inoculant on
one field with uniform soil. Eighty one-metre row sections were harvested as sampling
units, 40 per treatment, and six outcomes were recorded: grain yield, thousand-kernel
weight, grain protein, root colonisation, shoot phosphorus, and fertile tiller count.

## The label-shuffling procedure

Testing six outcomes at once means six chances to find a difference that is only noise,
so the threshold has to account for the whole family. Instead of a packaged correction,
multiplicity was handled by shuffling the treatment labels.

The idea is simple. First, compute the Welch t-statistic for each of the six outcomes
using the real "none" and "inoculated" labels. Then pretend the labels never meant
anything: shuffle them across all 80 sections, recompute all six statistics, and write
down only the single largest absolute statistic from that shuffle. Repeating this many
times builds up a picture of how big the biggest of six statistics gets when the
inoculant does nothing at all. An outcome's family-wise adjusted p-value is the share of
shuffles whose recorded maximum was at least as extreme as that outcome's real
statistic. Because every outcome is judged against the same distribution of maxima, one
threshold covers the whole family.

The procedure used **5000 shuffles** with the random seed fixed at **4711**, so the
numbers below reproduce exactly on a rerun. An outcome counts as significant only when
its adjusted p-value is below 0.05. For reference, the 95th percentile of the 5000
shuffled maxima was |t| = 2.74, which is the effective critical value the family imposes.

## Results

| Outcome | None | Inoculated | t | Adjusted p | Verdict |
|---|---|---|---|---|---|
| Grain yield (g/section) | 267.99 | 285.00 | 1.69 | 0.4546 | not significant |
| Thousand-kernel weight (g) | 38.20 | 39.40 | 1.71 | 0.4412 | not significant |
| Grain protein (%) | 11.80 | 12.10 | 1.36 | 0.6922 | not significant |
| Root colonisation (%) | 18.00 | 41.01 | 10.09 | 0.0000 | significant |
| Shoot phosphorus (% DM) | 0.280 | 0.330 | 4.06 | 0.0008 | significant |
| Fertile tillers | 122.00 | 128.03 | 1.46 | 0.6226 | not significant |

Root colonisation was never matched by any of the 5000 shuffled maxima, so its adjusted
p-value is reported as 0.0000; strictly it is below 1/5000.

## Interpretation

Two outcomes survive: the inoculant established, and the plants took up more phosphorus.
Root colonisation rose from 18% to 41% of roots, and shoot phosphorus from 0.28% to 0.33%
of dry matter. That is a coherent pair. The product did what it is supposed to do
biologically, and the symbiosis moved phosphorus into the shoot.

The four agronomic outcomes did not survive. Grain yield was 17 g per section higher
under inoculation, about 6%, which would matter commercially if it were real, but its
statistic (t = 1.69) sits well inside the range the shuffles produce by chance for the
largest of six tests. The same holds for thousand-kernel weight, protein, and tillers.
Taken one at a time, yield and kernel weight would each look borderline at the 0.05 level;
judged against the whole family of six, neither stands.

So the honest summary is that establishment is demonstrated and yield benefit is not.
This was one field with uniform soil, and soil phosphorus status is the usual reason
inoculants pay or fail to pay. A trial across fields differing in available phosphorus,
powered on yield as the single primary outcome, is the sensible next step.
