# Data description

Two CSV files sit at the project root. The first holds the trial's raw participant
records. The second holds the results that the trial's central statistics stage
produced upstream of this project.

## trial_participants.csv

One row is one child enrolled in the trial. There are 96 rows plus a header row:
48 children allocated to artemether-lumefantrine and 48 to artesunate-amodiaquine.
Every child has a value for every outcome, so there are no blank cells. Rows are in
enrolment order, so the two regimen groups are interleaved.

| Column | Meaning | Type and units |
| --- | --- | --- |
| `child_id` | Participant identifier. `AL-###` for children allocated to artemether-lumefantrine, `AS-###` for children allocated to artesunate-amodiaquine. Unique across the file. | text |
| `regimen` | Allocated treatment group. Exactly two values appear: `artemether_lumefantrine` and `artesunate_amodiaquine`. | text |
| `parasite_clearance_h` | Declared outcome 1. Time from first dose until asexual parasites are no longer seen on the blood film. | whole hours, 18 to 58 in this file |
| `fever_clearance_h` | Declared outcome 2. Time from first dose until axillary temperature stays below 37.5 C. | whole hours, 8 to 55 in this file |
| `haemoglobin_day28_g_per_dl` | Declared outcome 3. Haemoglobin measured at the day 28 visit. | g/dL, one decimal place, 7.2 to 13.5 in this file |
| `parasite_density_day2_per_ul` | Declared outcome 4. Asexual parasite density on the day 2 blood film. Strongly right-skewed, and 0 for the 29 children who had already cleared by day 2. | whole parasites per microlitre, 0 to 1961 in this file |
| `gametocyte_carriage_days` | Declared outcome 5. Number of follow-up days on which gametocytes were seen, across the 28-day follow-up. | whole days, 0 to 14 in this file |

The five outcome columns appear in the order the trial declared them before recruitment.

## upstream_adjusted_pvalues.csv

One row is one declared outcome. There are 5 rows plus a header row, in the declared
order. The values come from the trial's central statistics stage, which is not part of
this project. That stage compared the two regimens on each outcome and adjusted the
p-values across the whole family of five declared outcomes. The p-values in this file
are therefore already adjusted; nothing in this project adjusts them again.

| Column | Meaning | Type |
| --- | --- | --- |
| `outcome` | Name of the declared outcome. Matches the corresponding column name in `trial_participants.csv`. | text |
| `adjusted_p_value` | The regimen-comparison p-value for that outcome after adjustment across the family of five, as produced upstream. | number between 0 and 1, four decimal places |
