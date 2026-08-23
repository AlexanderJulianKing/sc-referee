# Nitrogen top-dressing schedule and rice grain yield

## The question

An irrigated rice research station compared two ways of applying nitrogen top-dressing:
`split` (nitrogen given in split doses) and `late` (one single late dose). Does grain
yield per hill differ between the two schedules?

Eighteen bunded paddies took part, nine per schedule. The schedule was applied to a
whole paddy, so **the paddy is the unit that was assigned to a group**. Six hills were
cut from marked positions inside each paddy and threshed separately. Those six hills are
spatial subsamples of one paddy, not eighteen-times-six independent plots.

## The data files

### File 1: `hill_harvest_raw.csv` — the raw field record

**One row is one harvested hill.** 108 data rows.

| Column | Meaning |
| --- | --- |
| `paddy_code` | Which paddy the hill came from, `P-01` to `P-18`. |
| `nitrogen_schedule` | The schedule that paddy received, `split` or `late`. |
| `hill_position` | The marked sampling position inside the paddy, 1 to 6. |
| `hill_grain_yield_g` | Threshed grain yield of that one hill, in grams, to 1 decimal. |

### File 2: `paddy_harvest_summary.csv` — the per-paddy harvest summary

**One row is one paddy.** 18 data rows. The field team prepared this file before analysis.

| Column | Meaning |
| --- | --- |
| `paddy_code` | The paddy identifier, `P-01` to `P-18`, one row each. |
| `nitrogen_schedule` | The schedule that paddy received, `split` or `late`. |
| `hills_sampled` | How many hills were harvested from that paddy. |
| `mean_hill_yield_g` | Mean grain yield per hill for that paddy, in grams, to 1 decimal. |

### How the two files line up

Checked in `analysis.py`, all confirmed:

- Both files list the same 18 paddy codes.
- `nitrogen_schedule` agrees between the files for every paddy.
- `hills_sampled` is 6 for every paddy, and that matches the 6 rows per paddy in File 1.
- Every `mean_hill_yield_g` is that paddy's six hill yields averaged and rounded to one
  decimal place. The largest distance from the exact average is 0.050 g, which is the
  most that rounding to one decimal can move a number.
- Two paddies landed exactly on a half-way value, where the rounding rule decides the
  answer: P-03 has an exact mean of 55.45 g stored as 55.4, and P-07 has an exact mean of
  42.25 g stored as 42.3. The file rounds these two ties in opposite directions. Both
  stored values are valid roundings, and at most 0.05 g is at stake, so this does not
  change any result below.

**The reported statistical test was run on File 2, `paddy_harvest_summary.csv`**, using
its 18 rows, one row per paddy. File 1 was used only to describe the data. No inferential
test was run on the hill-level rows, because hills inside one paddy are subsamples and
treating them as 108 independent observations would overstate the evidence.

## What the hill-level record shows (description only)

- 108 hills were harvested from 18 paddies.
- Every paddy contributed exactly 6 hills (minimum 6, maximum 6). Confirmed.
- Across all 108 hills, yield averaged 44.47 g with a standard deviation of 7.01 g.
- The hills ran from 28.3 g to 62.8 g. Quartiles: 40.18 g, median 43.70 g, 49.40 g.
- Inside a single paddy, hills spread out by about 5.10 g on average (mean of the 18
  within-paddy standard deviations, which ranged from 1.90 g to 8.15 g).
- By schedule, again purely descriptive: `split` hills averaged 41.79 g (SD 5.31 g, range
  31.0 to 53.7 g) and `late` hills averaged 47.14 g (SD 7.51 g, range 28.3 to 62.8 g).

## The comparison between schedules

Run on `paddy_harvest_summary.csv`, one observation per paddy.

| Schedule | Paddies (n) | Mean per-paddy yield | SD across paddies | Range |
| --- | --- | --- | --- | --- |
| `split` | 9 | 41.79 g | 2.29 g | 38.3 to 44.5 g |
| `late` | 9 | 47.13 g | 5.88 g | 39.4 to 55.4 g |

Sample size: **9 paddies per schedule, 18 paddies in total.**

**Difference (late minus split): 5.34 g per hill.**

The test is an independent two-sample t-test, two-sided, comparing the nine `split`
paddies against the nine `late` paddies. It uses the Welch form, which does not assume
the two groups have the same spread. That choice fits the design: the two groups are
separate sets of paddies, and Welch stays correct whether the spreads match or not. Here
they clearly do not, since the `late` paddies vary about two and a half times as much as
the `split` paddies.

| Quantity | Value |
| --- | --- |
| Test statistic | t = 2.54 |
| Degrees of freedom | 10.38 (Welch-Satterthwaite) |
| p-value | 0.0286 |
| 95% confidence interval for the difference | 0.68 g to 10.01 g |

## Conclusion

The single late nitrogen top-dressing produced more grain per hill than the split
schedule. Per-paddy mean yield was 5.34 g per hill higher under `late` (47.13 g) than
under `split` (41.79 g), and that difference is statistically significant at the 5% level
(Welch t = 2.54, df = 10.38, p = 0.0286, n = 9 paddies per schedule, 18 total).

Two limits are worth stating plainly. First, the confidence interval is wide, running
from 0.68 g to 10.01 g per hill, so the size of the gain is not pinned down well by 18
paddies. Second, the `late` paddies varied much more from paddy to paddy than the `split`
paddies did (SD 5.88 g versus 2.29 g), which means the late schedule looks less reliable
across field conditions even though its average was higher. A larger trial would be
needed to say how big the benefit is and how dependably it shows up.
