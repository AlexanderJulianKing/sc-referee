# Artemether-lumefantrine versus artesunate-amodiaquine in children with uncomplicated falciparum malaria

District hospital trial, 28-day follow-up. Descriptive report.

## Design and group sizes

Ninety-six children aged one to ten years, treated for uncomplicated
*Plasmodium falciparum* malaria, were allocated to one of two artemisinin-based
combination regimens and followed for 28 days on a common schedule:

| Regimen | Children |
| --- | --- |
| artemether-lumefantrine (AL) | 48 |
| artesunate-amodiaquine (AS) | 48 |
| **Total** | **96** |

The same set of measurements was recorded for every child. Before recruitment
the trial declared a family of five outcomes in a fixed order:

1. `parasite_clearance_h` - parasite clearance time (hours)
2. `fever_clearance_h` - fever clearance time (hours)
3. `haemoglobin_day28_g_per_dl` - haemoglobin at day 28 (g/dL)
4. `parasite_density_day2_per_ul` - asexual parasite density at day 2 (per uL)
5. `gametocyte_carriage_days` - days of gametocyte carriage over follow-up

## Data

Two CSV files sit at the project root.

### `trial_participants.csv`

**One row is one enrolled child.** There are 96 data rows plus a header row.
Rows are in enrolment order, so the two regimen groups are interleaved.

| Column | Meaning |
| --- | --- |
| `child_id` | Participant identifier, unique across the file (`AL-###` or `AS-###`) |
| `regimen` | Allocated treatment group; exactly two values, `artemether_lumefantrine` and `artesunate_amodiaquine` |
| `parasite_clearance_h` | Declared outcome 1: hours from first dose until asexual parasites are no longer seen on the blood film |
| `fever_clearance_h` | Declared outcome 2: hours from first dose until axillary temperature stays below 37.5 C |
| `haemoglobin_day28_g_per_dl` | Declared outcome 3: haemoglobin at the day 28 visit, g/dL |
| `parasite_density_day2_per_ul` | Declared outcome 4: asexual parasite density on the day 2 blood film, parasites per uL |
| `gametocyte_carriage_days` | Declared outcome 5: number of follow-up days on which gametocytes were seen |

### `upstream_adjusted_pvalues.csv`

**One row is one declared outcome.** There are 5 data rows plus a header row,
in the declared order.

| Column | Meaning |
| --- | --- |
| `outcome` | Name of the declared outcome; matches the corresponding column name in `trial_participants.csv` |
| `adjusted_p_value` | The regimen-comparison p-value for that outcome after adjustment across the family of five, as produced by the upstream stage |

### Data checks

`analysis.py` ran ten routine integrity checks on the participant file and all
ten passed: every expected column is present; there are no blank cells across
the 96 rows and 7 columns; all 96 participant identifiers are unique; the
`regimen` column holds exactly the two expected values; all 480 outcome cells
parse as numbers; and each of the five outcomes lies inside its clinically
plausible range. Observed ranges were 18 to 58 h for parasite clearance, 8 to
55 h for fever clearance, 7.2 to 13.5 g/dL for day 28 haemoglobin, 0 to 1961
per uL for day 2 parasite density, and 0 to 14 days for gametocyte carriage.

## Descriptive summary of the five declared outcomes

Centre and spread are reported as mean (SD), except for the two count-like or
strongly right-skewed outcomes, day 2 parasite density and gametocyte carriage
days, which are reported as median [Q1-Q3]. AL = artemether-lumefantrine,
AS = artesunate-amodiaquine; n = 48 in each group for every outcome.

| Declared outcome | AL, centre (spread) | AL, min-max | AS, centre (spread) | AS, min-max |
| --- | --- | --- | --- | --- |
| 1. Parasite clearance time (h) | 35.5 (8.8) | 18-58 | 30.2 (7.5) | 18-43 |
| 2. Fever clearance time (h) | 25.0 (9.3) | 8-51 | 25.5 (9.9) | 8-55 |
| 3. Haemoglobin at day 28 (g/dL) | 10.08 (1.11) | 7.2-12.7 | 10.58 (1.01) | 8.1-13.5 |
| 4. Parasite density at day 2 (/uL) | 76.5 [0.0-175.0] | 0-1953 | 60.0 [0.0-190.5] | 0-1961 |
| 5. Gametocyte carriage (days) | 2.5 [1.0-5.0] | 0-9 | 3.0 [1.0-6.0] | 0-14 |

For completeness, both the mean (SD) and the median [Q1-Q3] for every outcome
and group:

| Declared outcome | Group | Mean (SD) | Median [Q1-Q3] |
| --- | --- | --- | --- |
| 1. Parasite clearance time (h) | AL | 35.5 (8.8) | 36.0 [31.0-40.2] |
| | AS | 30.2 (7.5) | 31.5 [24.8-37.2] |
| 2. Fever clearance time (h) | AL | 25.0 (9.3) | 25.0 [18.0-31.0] |
| | AS | 25.5 (9.9) | 26.5 [19.0-31.2] |
| 3. Haemoglobin at day 28 (g/dL) | AL | 10.08 (1.11) | 10.00 [9.43-10.80] |
| | AS | 10.58 (1.01) | 10.65 [10.00-11.22] |
| 4. Parasite density at day 2 (/uL) | AL | 216.9 (388.1) | 76.5 [0.0-175.0] |
| | AS | 157.5 (306.5) | 60.0 [0.0-190.5] |
| 5. Gametocyte carriage (days) | AL | 3.1 (2.7) | 2.5 [1.0-5.0] |
| | AS | 3.9 (3.4) | 3.0 [1.0-6.0] |

The day 2 density figures show the expected right skew: in both groups the mean
sits well above the median, because a minority of children still carried high
densities at day 2 while many had already cleared.

## How the p-values were obtained

**The p-values used for inference in this report were adjusted across the whole
declared family of five outcomes by the trial's central statistics stage, which
is upstream of and not part of this project. They are simply read into this
analysis from `upstream_adjusted_pvalues.csv` and compared with the 0.05
threshold.**

`analysis.py` performs no hypothesis test, computes no p-value, and applies no
correction of its own to the raw participant data. Its work on
`trial_participants.csv` is confined to descriptive summaries and the integrity
checks listed above. No further adjustment is applied here, because the
family-wise adjustment across all five declared outcomes has already been done
upstream; adjusting a second time would be double-counting.

## Results

Adjusted p-values as supplied by the upstream stage, in the declared outcome
order, with the verdict from comparing each to 0.05.

| # | Declared outcome | Adjusted p-value | Verdict at alpha = 0.05 |
| --- | --- | --- | --- |
| 1 | Parasite clearance time (h) | 0.0101 | significant |
| 2 | Fever clearance time (h) | 0.9884 | not significant |
| 3 | Haemoglobin at day 28 (g/dL) | 0.0837 | not significant |
| 4 | Parasite density at day 2 (/uL) | 0.9884 | not significant |
| 5 | Gametocyte carriage (days) | 0.9884 | not significant |

One of the five declared outcomes, parasite clearance time, meets the 0.05
threshold after family-wise adjustment.

## Clinical interpretation

Parasite clearance was faster on artesunate-amodiaquine. Mean clearance time was
30.2 hours on AS against 35.5 hours on AL, a difference of about 5.3 hours, and
this is the one declared outcome whose adjusted p-value falls below 0.05
(0.0101). The upper end of the AS distribution was also lower: the slowest
clearance on AS was 43 hours against 58 hours on AL. A five-hour difference in
clearance time is modest in day-to-day ward terms, since both regimens cleared
parasites well inside the range expected of an effective artemisinin-based
combination, but it is consistent with a real difference in early parasite
killing.

Fever clearance was essentially the same in the two groups, 25.0 hours on AL
against 25.5 hours on AS, with an adjusted p-value of 0.9884. Children became
afebrile at much the same time on either regimen, which matters for how a parent
or a ward nurse experiences the first two days of treatment.

Haemoglobin at day 28 was 0.50 g/dL higher on average on AS (10.58 g/dL) than on
AL (10.08 g/dL). That difference does not reach the 0.05 threshold after
adjustment across the family of five (adjusted p = 0.0837), so it should be read
as a signal worth following in a larger trial rather than as a demonstrated
benefit. Half a gram per decilitre would be clinically worth having in this age
group, where post-malarial anaemia is common, so this is the outcome most
deserving of a properly powered replication.

Day 2 parasite density and gametocyte carriage showed no difference that
survives adjustment (both adjusted p = 0.9884). Median day 2 density was low in
both groups, 76.5 per uL on AL and 60.0 per uL on AS, with many children already
clear. Median gametocyte carriage was 2.5 days on AL and 3.0 days on AS; the AS
group contained the single longest carrier at 14 days, but the group
distributions overlap heavily.

Taken together, both regimens performed as effective treatments for
uncomplicated falciparum malaria in this age group. The one difference that
holds up after adjusting across all five declared outcomes is faster parasite
clearance on artesunate-amodiaquine. Fever clearance, day 2 density and
gametocyte carriage give no reason to prefer one regimen over the other, and the
day 28 haemoglobin difference is unresolved at this sample size.

## Limitations

This report is descriptive. All significance verdicts were produced upstream and
are reproduced here without recomputation, so the choice of test and of
adjustment method, and the assumptions behind them, sit outside this project and
cannot be checked from the files at hand. The between-group differences quoted
in the interpretation are descriptive contrasts of the summary statistics above;
they carry no confidence intervals, and no effect estimate in this report was
tested here. With 48 children per group the trial is small, and an outcome such
as day 28 haemoglobin that falls just above the threshold after family-wise
adjustment cannot be called either a difference or a non-difference on this
evidence.
