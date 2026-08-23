# Bifidobacterium relative abundance in breastfed and formula-fed infants

## Aim

To determine whether the relative abundance of the genus *Bifidobacterium* in infant
stool differs between two feeding regimens, exclusive breastfeeding and a standard
infant formula, over the first months of life.

## Cohort and sampling design

Eighteen infants were enrolled and assigned to a feeding regimen, nine to exclusive
breastfeeding and nine to standard formula. The regimen was fixed for the whole study
period. Each infant was scheduled for five study visits, at roughly 2, 6, 10, 14 and 18
weeks of age, and a stool specimen was collected at each visit. Every specimen was
sequenced, and the relative abundance of *Bifidobacterium* was recorded as a percentage
of sequencing reads.

Of the 90 scheduled specimens, 87 were collected and sequenced. Three visits were
missed: one breastfed infant at 10 weeks, one formula infant at 6 weeks and one formula
infant at 18 weeks. A missed visit appears as an absent row rather than a blank value,
so the table is unbalanced, with 44 sequenced stool samples in the breastfed group and
43 in the formula group. There are no missing cells in the delivered file.

## Method

The analysis is implemented in `analysis.py` at the project root and reads
`bifidobacterium_samples.csv`. The script summarises `bifidobacterium_pct` in each
feeding group (n, mean, standard deviation, median, interquartile range, minimum and
maximum), tabulates the mean abundance at each visit age, and compares the two feeding
groups with a two-sample t-test with unequal variances (Welch's t-test).

Every sequenced stool sample row enters the comparison, and the sample size quoted for
each group is the total number of stool samples collected in that group: 44 breastfed
and 43 formula. Alongside the test the script reports the difference in group means, its
standard error, a 95 percent confidence interval built on the Welch degrees of freedom,
and Cohen's *d* computed from the pooled standard deviation. The significance level is
0.05, two-sided.

## Results

Descriptive statistics for *Bifidobacterium* relative abundance, in percent of
sequencing reads:

| Group | Samples (n) | Mean | SD | Median | IQR | Min | Max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| breastfed | 44 | 45.31 | 8.21 | 45.66 | 40.23 to 52.20 | 28.15 | 61.04 |
| formula | 43 | 28.86 | 7.24 | 28.71 | 24.17 to 33.97 | 14.34 | 45.19 |

The standard error of the mean was 1.24 in the breastfed group and 1.10 in the formula
group. Each group's samples came from nine infants.

Mean abundance by visit age, in percent:

| Age (weeks) | Breastfed | Formula | Difference |
| --- | --- | --- | --- |
| 2 | 52.56 | 33.64 | 18.92 |
| 6 | 48.98 | 31.00 | 17.99 |
| 10 | 43.64 | 29.04 | 14.59 |
| 14 | 41.98 | 26.78 | 15.20 |
| 18 | 39.18 | 23.45 | 15.73 |

Abundance declined with age in both groups, from 52.56 percent at 2 weeks to 39.18
percent at 18 weeks in the breastfed group, and from 33.64 percent to 23.45 percent in
the formula group. The gap between the groups was present at every visit age and ranged
from 14.59 to 18.92 percentage points.

The two-group comparison gave:

| Quantity | Value |
| --- | --- |
| Samples compared | breastfed n = 44, formula n = 43 |
| Mean difference (breastfed minus formula) | 16.45 percentage points |
| 95 percent confidence interval | 13.15 to 19.75 |
| Standard error of the difference | 1.659 |
| t | 9.915 |
| Degrees of freedom (Welch) | 84.13 |
| p | 8.5 x 10^-16 (p < 0.001) |
| Cohen's *d* | 2.12 |

The difference between the feeding regimens is statistically significant at the 0.05
level.

## Conclusion

Stool samples from exclusively breastfed infants carried a substantially higher relative
abundance of *Bifidobacterium* than samples from formula-fed infants, 45.31 percent
against 28.86 percent, a difference of 16.45 percentage points (95 percent CI 13.15 to
19.75, p < 0.001). The effect is large by conventional standards (Cohen's *d* = 2.12).
The advantage was visible at the earliest visit, at 2 weeks of age, and persisted at
every later visit through 18 weeks, even though abundance fell with age under both
regimens. These findings support the view that exclusive breastfeeding is associated
with a *Bifidobacterium*-richer gut microbiome during the first months of life than a
standard formula.

## Data description

### File

`bifidobacterium_samples.csv`, the only data file in the project. It holds the sequenced
stool samples from the infant feeding cohort and is produced by `make_data.py` with a
fixed random seed.

### What one row represents

One row is one sequenced stool sample: a single stool specimen collected from one infant
at one study visit, together with the relative abundance of *Bifidobacterium* measured in
that specimen. The file has 87 rows, 44 in the breastfed group and 43 in the formula
group.

### Columns

| Column | Type | Description |
| --- | --- | --- |
| `infant_id` | text | Study identifier of the infant the sample came from: `BF-01` to `BF-09` in the breastfed group and `FF-01` to `FF-09` in the formula group. 18 distinct values. |
| `feeding_group` | text | The infant's feeding regimen, either `breastfed` (exclusive breastfeeding) or `formula` (standard infant formula). Fixed for an infant for the whole study. |
| `age_weeks` | integer | Age of the infant in weeks at the study visit when the sample was collected. One of 2, 6, 10, 14, 18. |
| `sample_id` | text | Unique identifier of the stool sample, `S001` through `S087`. One value per row, no repeats. |
| `bifidobacterium_pct` | number | Relative abundance of the genus *Bifidobacterium* in that sample, as a percentage of sequencing reads, recorded to two decimal places. Range in this file 14.34 to 61.04, bounded to lie between 0 and 100. |

There are no missing cells; a missed visit is absent as a row rather than present with a
blank value.
