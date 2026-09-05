# Preventive medicine for episodic migraine: trial analysis report

## Question and design

We asked whether twelve weeks of a preventive medicine reduces migraine burden compared with a
matching placebo in adults with episodic migraine. Eighty-eight adults reporting four to ten
migraine days per month were randomised one to one, forty-four to the medicine and forty-four to
placebo, and treatment arm is the two-level grouping factor throughout. Each participant kept a
headache diary, and every outcome value below summarises that participant's final four weeks of
treatment, so each participant contributes exactly one value per outcome. Seven outcomes were
declared in the protocol before unblinding, and they are examined here in that declared order. The
first two, monthly headache days and monthly migraine attacks, are the primary endpoints.

## Data description

The data file is `migraine_trial.csv`: 88 data rows plus a header row, nine comma-separated
columns, UTF-8.

**One row is one randomised participant.** Each participant appears exactly once, and the seven
outcome values on that row describe that participant's diary over the final four weeks of the
twelve-week treatment period. Every cell is filled; there are no missing values.

| # | Column | Type | What it holds |
| --- | --- | --- | --- |
| 1 | `participant_id` | text | Unique participant identifier, `MIG-001` through `MIG-088`. 88 distinct values. |
| 2 | `monthly_headache_days` | integer, days per 4 weeks | Days in the final four weeks with any recorded headache. |
| 3 | `monthly_migraine_attacks` | integer, attacks per 4 weeks | Distinct migraine attacks recorded in the final four weeks. Never exceeds that participant's headache-day count. |
| 4 | `peak_pain_intensity_0_10` | decimal, 0-10 scale | Worst recorded pain intensity, 0 (no pain) to 10 (worst imaginable), to one decimal place. A participant with no headache days is recorded as 0.0. |
| 5 | `rescue_medication_days_per_month` | integer, days per 4 weeks | Days in the final four weeks on which acute rescue medication was taken. Never exceeds that participant's headache-day count. |
| 6 | `migraine_disability_score_0_60` | integer, 0-60 scale | Migraine-related disability over the final four weeks, 0 (none) to 60 (most). |
| 7 | `nausea_days_per_month` | integer, days per 4 weeks | Days in the final four weeks with recorded nausea. Never exceeds that participant's headache-day count. |
| 8 | `sleep_quality_index_0_21` | integer, 0-21 scale | Sleep quality over the final four weeks, higher meaning worse sleep. |
| 9 | `treatment_arm` | text, exactly two values | `medicine` or `placebo`. 44 rows carry each value. |

## Per-arm summary

Forty-four participants were analysed in each arm, 88 in total, with no exclusions for missing
data. Means are shown with the standard deviation in parentheses.

| Declared outcome | Medicine (n = 44) | Placebo (n = 44) | Difference |
| --- | --- | --- | --- |
| 1. Monthly headache days | 6.02 (2.42) | 7.52 (2.56) | -1.50 |
| 2. Monthly migraine attacks | 3.45 (1.47) | 4.05 (1.74) | -0.59 |
| 3. Peak pain intensity (0-10) | 6.24 (1.47) | 6.72 (1.39) | -0.47 |
| 4. Rescue medication days per month | 3.84 (1.80) | 5.55 (2.07) | -1.70 |
| 5. Migraine disability score (0-60) | 18.95 (9.00) | 24.41 (7.61) | -5.45 |
| 6. Nausea days per month | 2.18 (1.39) | 3.02 (1.32) | -0.84 |
| 7. Sleep quality index (0-21) | 7.20 (2.70) | 8.39 (2.70) | -1.18 |

The difference column is the medicine mean minus the placebo mean. Every outcome is scored so that
lower is better, so the negative differences all point in the direction of benefit for the
medicine.

## Statistical approach

Each of the seven declared outcomes was compared between arms with a two-sample t-test of medicine
against placebo. The two primary endpoints, monthly headache days and monthly migraine attacks,
were then carried together through the Holm adjustment (`statsmodels.stats.multitest.multipletests`)
and decided on their adjusted p-values. The five remaining declared outcomes were each decided on
their own p-value. The threshold is 0.05 in every case.

## Results and conclusions, in declared order

| # | Declared outcome | Role | p-value | Adjusted p | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | `monthly_headache_days` | primary | 0.0058 | 0.0116 | significant |
| 2 | `monthly_migraine_attacks` | primary | 0.0887 | 0.0887 | not significant |
| 3 | `peak_pain_intensity_0_10` | other declared | 0.1228 | - | not significant |
| 4 | `rescue_medication_days_per_month` | other declared | 0.00009 | - | significant |
| 5 | `migraine_disability_score_0_60` | other declared | 0.0029 | - | significant |
| 6 | `nausea_days_per_month` | other declared | 0.0045 | - | significant |
| 7 | `sleep_quality_index_0_21` | other declared | 0.0429 | - | significant |

**1. Monthly headache days (primary).** The medicine arm averaged 1.50 fewer headache days per four
weeks than placebo, 6.02 against 7.52. After the Holm adjustment across the two primary endpoints
the adjusted p-value is 0.0116, below 0.05, so the medicine differs significantly from placebo on
this endpoint.

**2. Monthly migraine attacks (primary).** The medicine arm averaged 0.59 fewer distinct attacks,
3.45 against 4.05. The adjusted p-value is 0.0887, above 0.05, so the medicine does not differ
significantly from placebo on this endpoint. The difference sits in the direction of benefit but
the trial does not establish it.

**3. Peak pain intensity (0-10).** Worst recorded pain was 6.24 on the medicine and 6.72 on
placebo, a difference of 0.47 points with p = 0.1228. The arms barely separate here, and the
medicine does not differ significantly from placebo on peak pain intensity.

**4. Rescue medication days per month.** Participants on the medicine took acute rescue medication
on 1.70 fewer days, 3.84 against 5.55, with p = 0.00009. This is the largest separation in the
declared family, and the medicine differs significantly from placebo.

**5. Migraine disability score (0-60).** Disability averaged 18.95 on the medicine and 24.41 on
placebo, 5.45 points lower, with p = 0.0029. The medicine differs significantly from placebo.

**6. Nausea days per month.** Nausea was recorded on 2.18 days on the medicine and 3.02 days on
placebo, 0.84 days fewer, with p = 0.0045. The medicine differs significantly from placebo.

**7. Sleep quality index (0-21).** Sleep scores averaged 7.20 on the medicine and 8.39 on placebo,
1.18 points lower and therefore better sleep, with p = 0.0429. This one lands just inside the
threshold, and the medicine differs significantly from placebo.

## Summary

Of the two protocol-designated primary endpoints, monthly headache days separates the arms after
the Holm adjustment and monthly migraine attacks does not. Among the five remaining declared
outcomes, four separate the arms on their own p-values (rescue medication days, disability score,
nausea days, and sleep quality index) and one does not (peak pain intensity). Every point estimate
in the declared family favours the medicine. The headache-day reduction of 1.50 days per four
weeks, together with 1.70 fewer rescue-medication days and a 5.45-point drop in disability, is the
clinically meaningful core of the result.

## Reproducing this analysis

From the project root, run `python analysis.py`. The script reads `migraine_trial.csv`, prints the
per-arm counts and the per-arm mean and standard deviation of each declared outcome, then prints
each outcome's p-value, the adjusted p-value where one was produced, and its verdict. It requires
`pandas`, `scipy`, and `statsmodels`.
