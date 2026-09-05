# Improved biomass cookstove versus traditional open fire

## What was compared, and why

One hundred rural households took part in a household energy and health
programme: fifty cooked on an improved biomass stove and fifty on a traditional
open fire. Each household was monitored for one full cooking day by the same
field team, and the main cook filled in one symptom questionnaire. The question
is whether the improved stove changes kitchen air quality, fuel demand, the
cook's reported symptoms, and the time spent cooking.

## The data

`data.csv` holds 100 rows plus a header. One row is one household: its single
monitored cooking day and its cook's single questionnaire. The columns are:

- `household_id` - household identifier, `HH001` through `HH100`.
- `stove_type` - study group, either `improved_biomass_stove` or
  `traditional_open_fire`.
- `kitchen_pm25_ug_m3` - 24-hour kitchen fine particulate matter, micrograms per
  cubic metre (declared outcome 1).
- `kitchen_co_ppm` - 24-hour kitchen carbon monoxide, parts per million
  (declared outcome 2).
- `fuelwood_use_kg_day` - fuelwood used on the monitored day, kilograms per day
  (declared outcome 3).
- `respiratory_symptom_score` - cook's respiratory symptom score on a 0 to 12
  scale, higher meaning more symptoms (declared outcome 4).
- `cooking_time_min` - total cooking time on the monitored day, minutes
  (declared outcome 5).

Every household has a value in every column, and there are no blanks.

## What the analysis did

`analysis.py` reads `data.csv` and, for each of the five declared outcomes in
the declared order, compares the two stove groups with a Welch two-sample
t-test, which does not assume the groups share a variance. It reports each
group's size, mean, and standard deviation, then checks the p-value against the
0.01 per-outcome threshold the protocol fixed before any data were collected.

## Why the threshold is 0.01

The protocol declared five outcomes as one family and asked for family-wise
error control across that whole family. The Bonferroni correction splits the
conventional 0.05 family-wise level evenly among the family's tests: 0.05
divided by 5 outcomes gives 0.01 per outcome. So the pre-fixed 0.01 threshold is
the Bonferroni-corrected per-outcome level for a family of five outcomes at a
0.05 family-wise level. The script simply applies that fixed number.

## Results

1. **Kitchen PM2.5**: improved 223.532 ug/m3 (sd 67.076) versus traditional
   618.704 ug/m3 (sd 200.991); p = 2.4e-19. Significant. Improved stove
   households were far lower.
2. **Kitchen carbon monoxide**: improved 4.176 ppm (sd 1.819) versus traditional
   13.010 ppm (sd 4.392); p = 5.2e-20. Significant, again much lower.
3. **Fuelwood use**: improved 3.625 kg/day (sd 0.792) versus traditional 6.473
   kg/day (sd 1.030); p = 2.1e-27. Significant, about 2.8 kg/day less.
4. **Respiratory symptom score**: improved 5.200 (sd 2.010) versus traditional
   5.100 (sd 2.367); p = 0.820. Not significant; the groups sit essentially
   together.
5. **Cooking time**: improved 171.294 minutes (sd 25.754) versus traditional
   174.160 minutes (sd 31.829); p = 0.622. Not significant.

Each group contributed 50 households to every comparison.
