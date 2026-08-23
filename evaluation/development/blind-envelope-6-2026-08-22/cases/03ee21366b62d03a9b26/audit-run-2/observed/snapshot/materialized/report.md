# Effect of a linseed-oil supplement on kit weaning weight in commercial rabbit does

## Aim

To find out whether adding a linseed-oil supplement to the standard pelleted doe ration raises the
body weight of kits at weaning (day 35).

## Design

Fourteen breeding does on a commercial rabbit unit were enrolled in the trial and split into two
feeding groups of seven does each:

- **standard**: the standard pelleted ration (does `D01` to `D07`).
- **supplemented**: the same pelleted ration plus a linseed-oil supplement (does `D08` to `D14`).

Each doe received her assigned ration from mating, through gestation and right through lactation.
Every doe raised one litter. At weaning on day 35 each kit that had survived to that point was taken
off the nest and weighed individually on a bench scale to 0.1 g.

Litter sizes ranged from 6 to 9 weaned kits. On the standard ration the seven litters held 6, 6, 6,
8, 6, 9 and 9 kits; on the supplemented ration they held 9, 8, 9, 6, 6, 9 and 9 kits. Because litter
sizes differ between does, the two groups are unbalanced: 50 weighed kits on the standard ration and
56 on the supplemented ration, 106 weighed kits in total.

## Data description

All measurements sit in one file, `kit_weaning_weights.csv`, with 106 data rows and a header row.

**One row is one weaned kit, weighed individually on day 35.** The row also records which doe raised
that kit, which ration that doe was fed, and how big her litter was.

| Column | Type | What it holds |
| --- | --- | --- |
| `doe_id` | text | Identifier of the breeding doe that raised the kit, `D01` to `D14`. It appears once for each kit in that doe's litter. |
| `diet_group` | text | Ration fed to the doe, either `standard` or `supplemented`. The same value for every kit of a given doe. |
| `litter_size` | integer | Number of kits in that doe's litter weaned and weighed, 6 to 9. It equals the number of rows carrying that `doe_id`. |
| `kit_number` | integer | Position number of the kit inside its own litter, running from 1 up to `litter_size`. It is only a label within the litter. |
| `weaning_weight_g` | number | Body weight of that kit in grams at weaning on day 35, recorded to 0.1 g. |

No values are missing: every one of the 106 rows carries a value in all five columns, because only
kits alive at day 35 were weighed and entered.

## Method

The analysis is in a single script, `analysis.py`, run with Python 3 (pandas, NumPy, SciPy). The
script reads the CSV, checks that the five expected columns are present, that no values are missing,
and that each doe's stated `litter_size` matches how many kit rows she has.

Each individually weighed kit is one replicate. The script summarises weaning weight in each diet
group by number of kits, mean, standard deviation, standard error, minimum, median and maximum, and
then compares the two groups with an independent two-sample t-test (Welch's version, which does not
assume the two groups share a variance) on `weaning_weight_g`. The sample size entering the test for
each group is the total number of weighed kits in it: 50 standard and 56 supplemented. The test is
two-sided at alpha = 0.05, and the difference is expressed as supplemented minus standard, together
with its 95 % confidence interval and Cohen's *d* on the pooled standard deviation.

## Results

Descriptive statistics for weaning weight, one observation per weighed kit:

| Group | Does | Kits (n) | Mean (g) | SD (g) | SEM (g) | Min (g) | Median (g) | Max (g) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | 7 | 50 | 605.7 | 84.7 | 12.0 | 435.7 | 595.1 | 832.8 |
| supplemented | 7 | 56 | 680.6 | 71.2 | 9.5 | 405.5 | 694.4 | 808.4 |

Independent two-sample t-test (Welch), supplemented minus standard:

| Quantity | Value |
| --- | --- |
| n, standard | 50 kits |
| n, supplemented | 56 kits |
| Mean difference | +74.9 g |
| Standard error of the difference | 15.3 g |
| 95 % confidence interval | 44.5 g to 105.2 g |
| t | 4.896 |
| Degrees of freedom | 96.20 |
| p | 0.0000039 (3.94 x 10^-6) |
| Cohen's *d* | 0.96 (pooled SD 77.8 g) |

Kits raised by supplemented does weighed 680.6 g at weaning against 605.7 g for kits raised by does
on the standard ration. That is a gain of 74.9 g, about 12.4 % above the standard-ration mean. The
p-value is far below the 0.05 threshold, so the null hypothesis of equal mean weaning weight is
rejected. The confidence interval puts the gain somewhere between 44.5 g and 105.2 g, so even the
low end of the interval is a worthwhile increase. Cohen's *d* of 0.96 is a large effect by the usual
benchmarks. The supplemented group is also slightly less spread out (SD 71.2 g against 84.7 g).

## Conclusion

Feeding the linseed-oil supplement alongside the standard pelleted ration, from mating through
lactation, raised kit weaning weight by roughly 75 g per kit, a gain of about 12 %. The increase is
statistically significant (p < 0.001) and large enough to matter commercially: with litters of 6 to
9 kits, a 75 g gain per kit adds roughly 450 g to 675 g of weaned biomass per doe. On this evidence
the supplement is worth adopting, and the sensible next step is to check whether the extra weaning
weight carries through to slaughter weight and whether it pays for the cost of the supplement.
