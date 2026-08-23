# Does a live daphnia supplement speed larval growth in common frogs?

## Aim

The breeding centre wants to know whether adding live daphnia to its standard flake diet makes
common frog (*Rana temporaria*) tadpoles grow faster. Growth is measured as snout-vent length in
millimetres after six weeks of rearing. The question is whether the supplemented group is longer
than the standard group, and by how much.

## Rearing design

Sixteen rearing bins were stocked from a single pooled clutch. Each bin was assigned to one of
two diets:

- `standard_flake`: the centre's standard flake diet, 8 bins.
- `flake_plus_daphnia`: the same flake diet plus live daphnia, 8 bins.

Bins are labelled `B01` through `B16`, and the diets alternate along that sequence, which is the
order the rack was filled: odd-numbered bins got the standard diet, even-numbered bins got the
supplement.

After six weeks, 12 tadpoles were netted from each bin, photographed against a scale, and
measured. That is 192 measured tadpoles, balanced at 12 per bin with nothing missing. Water
temperature was recorded once per bin and ranged from 17.5 to 19.9 degrees Celsius.

The important structural point is that **the diet was given to bins, not to individual
tadpoles**. All 12 tadpoles in a bin shared one container, one batch of food, and one water
temperature. So the bin is the independent experimental unit, and the study has 16 units, 8 per
diet, rather than 192.

## The two data files

The study data sit in two CSV files that describe the same 192 measurements at two different
levels.

`tadpole_measurements.csv` is the raw file. One row is one measured tadpole. It has 192 data
rows, 12 for each of the 16 bins.

`bin_summary.csv` is the per-bin file. One row is one rearing bin. It has exactly 16 data rows,
one for each bin, 8 per diet.

The summary file is **derived from** the raw file and adds no new measurements. For each bin,
`mean_snout_vent_length_mm` is the arithmetic mean of that bin's 12 raw `snout_vent_length_mm`
values, and `n_tadpoles_measured` is how many raw rows went into that mean, which is 12 for every
bin. Grouping the raw file by `bin_label` and averaging reproduces the summary file. The analysis
script checks this on every run: the bin labels, diets, and counts match exactly, and the largest
gap between a stored bin mean and a recomputed one is 0.000033 mm, which is the rounding to four
decimal places in the stored file and nothing more.

Because the summary file is a rewriting of the raw file, the two are **not** two independent
sources of evidence. The summary file has one row per treated unit. The raw file has 12 rows per
treated unit, and those 12 rows are repeated measures from inside one bin.

## Data description

### `tadpole_measurements.csv`

**One row represents one measured tadpole**, netted from one bin at the six-week mark. 192 data
rows plus a header.

| Column | Type | What it holds |
| --- | --- | --- |
| `bin_label` | text | Which rearing bin the tadpole came from, `B01` to `B16`. Appears on exactly 12 rows. |
| `diet_treatment` | text | The bin's diet, `standard_flake` or `flake_plus_daphnia`. A bin-level value, so it is identical on all 12 rows of a bin. |
| `tadpole_no` | integer | Which of that bin's 12 netted tadpoles the row is, 1 to 12. A label within the bin only; `tadpole_no` 3 in `B01` and in `B02` are different animals. |
| `snout_vent_length_mm` | number | The measured snout-vent length in millimetres, to 0.01 mm. This is the response variable. Observed range 11.15 to 19.69 mm. |
| `water_temp_c` | number | The bin's water temperature in degrees Celsius, to 0.1. Measured once per bin, so it repeats on all 12 rows of a bin. Observed range 17.5 to 19.9 C. |

### `bin_summary.csv`

**One row represents one rearing bin**, which is one unit that was assigned a diet. Exactly 16
data rows plus a header.

| Column | Type | What it holds |
| --- | --- | --- |
| `bin_label` | text | The bin identifier, `B01` to `B16`. Each appears exactly once, so this is the file's unique key. It matches `bin_label` in the raw file. |
| `diet_treatment` | text | The bin's diet, `standard_flake` or `flake_plus_daphnia`. Matches the raw file's value for that bin. |
| `mean_snout_vent_length_mm` | number | The mean of that bin's 12 raw `snout_vent_length_mm` values, in millimetres, written to four decimal places. Observed range 13.0975 to 17.5142 mm. |
| `n_tadpoles_measured` | integer | How many tadpoles went into that mean. It is 12 for every bin here. |

## Method

The comparison between diets is an **independent two-sample t-test run on the 16 rows of
`bin_summary.csv`**, using `mean_snout_vent_length_mm` as the response and `diet_treatment` as the
grouping variable. Each bin contributes exactly one number, so the two samples are 8 values
against 8 values, and **the reported sample size is the number of bins, n = 16**.

Welch's version of the test is the primary result, because it does not assume the two diets share
the same variance. The equal-variance (Student) t-test and a Mann-Whitney U test are reported
alongside it as sensitivity checks on the same 16 bin-level values, to show the conclusion does
not hinge on one procedure's assumptions.

The raw tadpole file is used **only descriptively**: to count the tadpoles measured, confirm that
the summary file matches it, and report how much lengths vary inside a bin. No group comparison is
run on the 192 tadpole rows. Testing those rows as if they were 192 independent observations would
treat 12 tadpoles from one bin as 12 separately treated animals, which would shrink the standard
error and produce a p-value that the design does not support.

All numbers below come from running `analysis.py` with Python 3 (pandas 2.0.3, scipy 1.9.1).

## Results

Descriptives from the raw file (192 rows, no testing on them):

| Quantity | Value |
| --- | --- |
| Tadpoles measured | 192 (96 per diet) |
| Bins | 16 (12 tadpoles each, min 12, max 12) |
| Snout-vent length range | 11.15 to 19.69 mm |
| Within-bin SD of length | mean 1.230 mm across bins (range 0.625 to 1.698 mm) |
| Water temperature range | 17.5 to 19.9 C |

Group descriptives at the unit of analysis, the 16 per-bin means:

| Diet | Bins | Mean of bin means | SD | SE | Range of bin means |
| --- | --- | --- | --- | --- | --- |
| `standard_flake` | 8 | 14.9023 mm | 1.0041 | 0.3550 | 13.0975 to 16.3925 mm |
| `flake_plus_daphnia` | 8 | 16.3567 mm | 1.1321 | 0.4003 | 14.0708 to 17.5142 mm |

Primary test, Welch independent two-sample t-test on the 16 bin means:

| Quantity | Value |
| --- | --- |
| Sample size | n = 16 bins (8 supplemented, 8 standard) |
| Difference, supplement minus standard | 1.4544 mm |
| Standard error of the difference | 0.5350 mm |
| 95% confidence interval | 0.3054 to 2.6034 mm |
| t | 2.7184 |
| Degrees of freedom | 13.803 |
| p | 0.0168 |
| Hedges g | 1.2851 (Cohen d 1.3592) |

Sensitivity checks on the same 16 values:

| Test | Result |
| --- | --- |
| Student equal-variance t-test | t = 2.7184, df = 14, p = 0.0166 |
| Mann-Whitney U test | U = 55.0, p = 0.0148 |

## Conclusion

Bins fed the flake diet plus live daphnia produced tadpoles that were longer on average than bins
fed flake alone. The estimated gain is **1.45 mm** of snout-vent length after six weeks, about a
10 percent increase over the standard-diet mean of 14.90 mm. With the bin as the unit and n = 16
bins, the difference is statistically significant at the conventional 5 percent level
(p = 0.0168), and the equal-variance and rank-based checks agree closely (p = 0.0166 and
p = 0.0148).

Two limits are worth stating plainly.

First, the confidence interval is wide: the data are compatible with a gain anywhere from about
0.31 mm to about 2.60 mm. Sixteen bins is a small study, and bins vary a lot among themselves.
The SD of the bin means is roughly 1.0 to 1.1 mm in each group, and the two groups overlap, with
the best standard-diet bin at 16.39 mm sitting above three of the eight supplemented bins. So the
direction of the effect is reasonably clear, but its size is not pinned down well. Anyone planning
to act on the exact number should treat 1.45 mm as a rough central estimate, not a settled value.

Second, temperature was recorded but not adjusted for. It ranged from 17.5 to 19.9 C across bins
and could contribute to the bin-to-bin spread. The protocol asks only for the two-group
comparison, so this analysis does not model it, and the estimate above should be read as the
overall difference between the two diets as they were actually run on this rack.

Within those limits, the study supports the supplement. Adding live daphnia to the flake diet is
associated with faster larval growth, and a follow-up with more bins, rather than more tadpoles
per bin, would be the way to tighten the estimate. More tadpoles per bin would refine each bin's
mean, but the precision of the comparison is set by how many bins there are.
