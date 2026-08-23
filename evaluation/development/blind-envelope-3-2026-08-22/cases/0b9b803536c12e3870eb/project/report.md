# Maximal handgrip strength after eight weeks of heavy or moderate resistance training

## Data description

The project contains one comma-separated data file, `grip_strength.csv`, with one header row and
104 data rows. **One row is one maximal handgrip trial performed by one volunteer.** Each of the
26 volunteers completed four trials in a single testing session, so each volunteer contributes four
rows to the file. The file therefore holds several rows per volunteer. The comparison between the
two programmes does not use those rows directly: it first reduces each volunteer to a single value,
the average of that volunteer's four trials, and compares the programmes using **one value per
volunteer**.

The file has six columns.

| Column | Type | What it holds |
| --- | --- | --- |
| `volunteer_id` | text | Identifier for the volunteer: `H01`–`H13` in the heavy group, `M01`–`M13` in the moderate group. The same value repeats on all four of that volunteer's rows. |
| `programme` | text | The training programme the volunteer followed, `heavy` or `moderate`. Constant within a volunteer. |
| `trial_number` | integer | Which of the four trials in the testing session the row records: 1, 2, 3 or 4, in the order performed. |
| `peak_force_kg` | number | Peak handgrip force on that trial, in kilograms, to one decimal place. This is the outcome variable. |
| `sex` | text | Volunteer's sex, `female` or `male`. Constant within a volunteer. |
| `body_mass_kg` | number | Volunteer's body mass in kilograms, to one decimal place. Measured once, so constant within a volunteer. |

The values in the file are simulated rather than measured. They were produced by `make_data.py`
using the fixed seed `20260867`, so the file can be regenerated exactly.

## Training programmes

Twenty-six healthy adult volunteers took part, thirteen in each group. One group followed a
twice-weekly heavy resistance programme; the other followed a three-times-weekly moderate load
programme. Each volunteer trained on one programme only, so the volunteer is the unit that was
assigned to a group. The two groups had the same sex split, seven male and six female volunteers
each. Mean body mass was 74.1 kg (SD 10.7) in the heavy group and 68.8 kg (SD 12.6) in the moderate
group. Body mass was recorded for description only and was not used in the comparison.

## Testing session

After eight weeks of training, every volunteer attended one testing session and performed four
maximal handgrip trials separated by short rests. The peak force of each trial was recorded in
kilograms. Across all 104 trials, peak force ranged from 28.8 to 55.1 kg.

Two features of the session matter for the analysis. First, the four trials of one volunteer are
repeated measurements on the same person, so they are not four independent observations. In these
data the average trial-to-trial standard deviation within a volunteer was 1.74 kg, while volunteers
differed from each other by roughly 6.6 kg (standard deviation of the per-volunteer means). People
differed from one another far more than a person's own trials differed from one another. Second,
mean peak force drifted slightly downward across the session: 43.02 kg on trial 1, 42.04 kg on
trial 2, 42.03 kg on trial 3 and 41.53 kg on trial 4, consistent with mild fatigue. Averaging the
four trials applies the same drift to every volunteer, so it does not favour either group.

## Methods

The analysis is implemented in `analysis.py` at the root of the project and was run with Python 3
(pandas 2.0.3, SciPy 1.9.1).

1. **Read the trial-level file.** The script checks that all six expected columns are present, that
   no peak force value is missing, and that each volunteer appears under exactly one programme. It
   confirms 104 rows, 26 volunteers and exactly four trials per volunteer.
2. **Reduce each volunteer to one value.** The four trials belonging to a volunteer are averaged
   into a single mean peak force for that volunteer. This is the step that makes the two groups
   comparable as independent samples: after it, one row is one volunteer, and the rows are
   independent of one another. It also means the sample size entering the test is the number of
   volunteers, 13 per group, and not the number of trials, 52 per group. Treating the 104 trials as
   104 independent observations would count each volunteer four times and would badly overstate the
   precision of the comparison.
3. **Summarise.** Per-programme means, standard deviations, standard errors, minima and maxima are
   computed from the per-volunteer values.
4. **Compare the two programmes.** An independent two-sample *t*-test (Welch's, which does not
   assume the groups share a variance) was applied to the per-volunteer mean peak forces, two-sided,
   with alpha set at 0.05. A 95% confidence interval for the difference in means and Hedges' *g*
   were computed alongside the test. The two groups' spreads were in fact very similar, so the
   pooled-variance test gives the same result to five decimal places; Welch's test was used because
   it is the safer default when group variances are not known to be equal.

## Results

Per-volunteer mean peak force, computed from each volunteer's four trials:

| Programme | n (volunteers) | Mean (kg) | SD (kg) | SEM (kg) | Min (kg) | Max (kg) |
| --- | --- | --- | --- | --- | --- | --- |
| Heavy | 13 | 44.03 | 6.60 | 1.83 | 33.12 | 53.15 |
| Moderate | 13 | 40.28 | 6.55 | 1.82 | 29.55 | 48.08 |

The sample size in each group is 13 volunteers. The 104 rows in the data file are 104 trials, not
104 observations for the test.

The heavy group's mean was 3.75 kg higher than the moderate group's. The independent two-sample
*t*-test on the per-volunteer means gave *t* = 1.455 with 24.0 degrees of freedom (Welch) and
**p = 0.159** (two-sided). The 95% confidence interval for the difference in means ran from
−1.57 kg to +9.07 kg. The standardised difference was Hedges' *g* = 0.55.

At alpha = 0.05 the null hypothesis of no difference between the programmes is not rejected.

## Conclusion

The volunteers who followed the twice-weekly heavy resistance programme recorded a higher mean peak
grip force than those on the three-times-weekly moderate load programme, 44.03 kg against 40.28 kg,
a difference of 3.75 kg in favour of the heavy programme. That difference is not statistically
significant at the 0.05 level (p = 0.159), and the 95% confidence interval includes zero, so these
data do not establish that either programme produced greater grip strength. The interval is wide,
running from a 1.6 kg disadvantage to a 9.1 kg advantage for the heavy programme, which is what
13 volunteers per group buys against a between-volunteer standard deviation of about 6.6 kg: the
study cannot distinguish a moderate real benefit of heavy training from no benefit at all. The
point estimate leans toward the heavy programme and the standardised effect is moderate
(*g* = 0.55), but that is a direction to test in a larger study, not a finding.

Two limits are worth stating plainly. The values analysed here are simulated, so the numbers
describe the simulation and not any real training effect. And with no pre-training measurement in
the file, the comparison is of post-training grip strength between groups; it cannot separate a
training response from any strength difference that existed before the eight weeks began.
