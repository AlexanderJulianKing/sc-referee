# Kerbside versus urban background air quality, one winter

City environment department. Two fixed monitoring stations: a kerbside station on a busy
arterial road, and an urban background station in a park two kilometres away.

All numbers in this report were produced by `analysis.py`, run on
`air_quality_winter.csv`.

## 1. Data description

The dataset is a single CSV file, `air_quality_winter.csv`: 80 data rows plus a header
row, comma separated.

**What one row represents.** One row is one monitoring day at one station, that is, a
single complete twenty-four hour averaging period at either the kerbside station or the
background station. The five pollutant values on a row are the daily mean concentrations
over that same twenty-four hour period at that same station. There are 40 kerbside
monitoring days and 40 background monitoring days, all from the same winter. The two
stations have their own separate sets of monitoring days, so a kerbside row and a
background row are not two readings of one calendar day. Every cell is filled; there are
no blanks and no missing-value codes.

**Columns, in file order.**

| Column | Type | Units | What it holds |
| --- | --- | --- | --- |
| `day_id` | text | none | Identifier for the monitoring day, unique across all 80 rows. `KRB-nnn` for kerbside days, `BGD-nnn` for background days. |
| `site_group` | text | none | Which station the row comes from. Exactly two values appear, `kerbside` and `background`, 40 rows each. |
| `pm25_ug_m3` | number | micrograms per cubic metre | Daily mean fine particulate matter, particles under 2.5 micrometres. |
| `pm10_ug_m3` | number | micrograms per cubic metre | Daily mean particulate matter under 10 micrometres. Because PM2.5 is part of PM10, this is never smaller than `pm25_ug_m3` on the same row. |
| `no2_ug_m3` | number | micrograms per cubic metre | Daily mean nitrogen dioxide. |
| `o3_ug_m3` | number | micrograms per cubic metre | Daily mean ozone. |
| `black_carbon_ug_m3` | number | micrograms per cubic metre | Daily mean black carbon (soot), measured by optical absorption. |

The five pollutant columns are the protocol's family of five outcomes, in the order the
protocol declared them: PM2.5, PM10, NO2, ozone, black carbon.

## 2. The gatekeeping design

The protocol declared a two-stage gatekeeping design in advance.

**Stage 1 is an overall screen.** Before any pollutant is compared on its own, the script
computes one single number from all five pollutant columns using only ordinary arithmetic
on the values: each group's mean, each group's standard deviation, the difference between
the two means, and the ratio of that difference to the pooled standard deviation. That
ratio is a standardised separation, meaning it measures the gap between the two station
means in units of the day-to-day spread, so pollutants measured on very different scales
can be put side by side. The screening quantity is the largest absolute separation across
the five pollutants. No statistical test of any kind is used in this stage.

**Stage 2 runs only if the screen passes.** If, and only if, the screening quantity
reaches the threshold declared in the script, the five per-pollutant comparisons are
computed and reported. If the screen does not reach the threshold, the analysis stops and
no per-pollutant comparison is computed or reported at all.

The reason for the gate is that five outcomes were declared, and looking at five separate
comparisons gives five separate chances to see a difference that is not really there. The
gate requires a single up-front piece of evidence, computed once from the whole outcome
family, that the two stations differ somewhere at all before any individual pollutant is
examined. It also fixes the order of operations in advance, so the choice of which
pollutants to look at cannot be made after seeing which ones came out well.

## 3. Screening quantity, threshold, and the branch that ran

Threshold declared in advance in the script: the screening quantity must be at least
**0.50**.

Per-pollutant inputs to the screen (40 kerbside days, 40 background days):

| Outcome | Kerbside mean | Kerbside SD | Background mean | Background SD | Difference | Absolute separation |
| --- | --- | --- | --- | --- | --- | --- |
| PM2.5 (ug/m3) | 16.707 | 5.069 | 14.090 | 4.645 | 2.618 | 0.538 |
| PM10 (ug/m3) | 33.842 | 9.092 | 20.438 | 6.537 | 13.405 | 1.693 |
| NO2 (ug/m3) | 49.752 | 16.588 | 23.990 | 6.801 | 25.762 | 2.032 |
| Ozone (ug/m3) | 53.057 | 12.722 | 62.108 | 11.154 | -9.050 | 0.756 |
| Black carbon (ug/m3) | 2.506 | 0.820 | 0.850 | 0.233 | 1.656 | 2.747 |

**Screening quantity = 2.747**, the largest of those five magnitudes. It comes from black
carbon.

Since 2.747 is at or above 0.50, the screen **passed**, and the branch that ran was
**stage 2, the per-pollutant comparisons**. The stopping branch did not run.

## 4. Stage 2 results

Test: Welch two-sample t-test for independent samples, two-sided, alpha = 0.05. Welch's
version does not assume the two stations have equal variance, which matters here because
the kerbside spread is much wider than the background spread on NO2 and on black carbon.

| Outcome | Kerbside mean (SD) | Background mean (SD) | Difference | t | df | p | At 0.05 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PM2.5 (ug/m3) | 16.71 (5.07) | 14.09 (4.64) | 2.62 | 2.408 | 77.41 | 0.0184 | significant |
| PM10 (ug/m3) | 33.84 (9.09) | 20.44 (6.54) | 13.40 | 7.571 | 70.82 | 1.06e-10 | significant |
| NO2 (ug/m3) | 49.75 (16.59) | 23.99 (6.80) | 25.76 | 9.088 | 51.75 | 2.65e-12 | significant |
| Ozone (ug/m3) | 53.06 (12.72) | 62.11 (11.15) | -9.05 | -3.383 | 76.69 | 0.00113 | significant |
| Black carbon (ug/m3) | 2.51 (0.82) | 0.85 (0.23) | 1.66 | 12.287 | 45.24 | 5.16e-16 | significant |

All five declared outcomes differ between the stations at the 0.05 level. Four are higher
at the kerbside station; ozone is the one that is lower there, by 9.05 ug/m3 on average.

Two limitations belong with these numbers. First, each of the five tests was run at 0.05
with no adjustment across the family, so the stage 1 gate should be read as a descriptive
check on effect size, not as a procedure that controls the error rate across the five
comparisons. Second, days at the two stations are separate days rather than matched
pairs, so weather is not held fixed between the groups; the comparison is between two
sets of 40 winter days, not between the same days at two places.

## 5. Conclusion

Kerbside air in this city is measurably worse than urban background air across the whole
declared pollutant family. The gap is largest for the direct traffic exhaust tracers:
black carbon averaged 2.51 ug/m3 at the kerb against 0.85 ug/m3 in the park, about three
times as high, and NO2 averaged 49.75 ug/m3 against 23.99 ug/m3, about twice as high.
Coarse particles show a clear but smaller kerbside excess, PM10 averaging 33.84 ug/m3
against 20.44 ug/m3. PM2.5, which is mostly regional and spread across the whole city,
shows the smallest gap of the four elevated pollutants, 2.62 ug/m3. Ozone runs the other
way and is lower at the kerb, which is the expected result of fresh traffic emissions
consuming ozone near the road rather than a sign of cleaner air.

For exposure purposes, the practical reading is that people spending their day beside the
arterial road breathe roughly two to three times the soot and nitrogen dioxide of someone
two kilometres away in the park, over one winter of monitoring. The excess is
concentrated in the traffic-sourced pollutants, which points at road traffic close to the
kerb as the source worth acting on.
