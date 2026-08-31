# Data description

## File

`workstation_evaluation.csv` — the committed data file for the sit-stand workstation
evaluation. Fixed values, held in the file; nothing in it is generated at run time.

## What one row represents

One row is **one employee**. Each of the 56 desk-based claims processors who took part
appears exactly once, with the workstation condition they were on for the twelve weeks and
their value for each of the seven declared outcome variables. Measurements were taken over
the final working week, from the questionnaires, the chair-and-desk posture logger and the
keyboard software.

The file has 56 data rows plus a header row, 9 columns, no missing cells and no extra rows.
28 employees are in each of the two workstation conditions.

## Columns

Columns 3 through 9 are the seven declared outcome variables, in the order fixed in the
evaluation protocol.

| # | Column | Type | Unit or scale | Range in file | Source |
|---|--------|------|---------------|---------------|--------|
| 1 | `employee_id` | text | `EMP` prefix plus a zero-padded two-digit serial | `EMP01` to `EMP56`, unique | employee roster |
| 2 | `workstation_group` | text | workstation condition, exactly two values: `fixed_desk` (existing fixed-height desk) and `sit_stand` (height-adjustable sit-stand workstation with a short training session) | 28 rows each | allocation record |
| 3 | `neck_shoulder_discomfort_0_10` | integer | neck and shoulder discomfort over the past week, 0 to 10 numeric rating scale, higher is worse | 0 to 8 | questionnaire |
| 4 | `lower_back_discomfort_0_10` | integer | lower-back discomfort over the past week, 0 to 10 numeric rating scale, higher is worse | 0 to 7 | questionnaire |
| 5 | `sitting_time_min` | integer | sitting time during the working day, in minutes | 203 to 475 | posture logger |
| 6 | `sit_to_stand_changes_per_day` | integer | number of sit-to-stand posture changes per working day, a count | 3 to 25 | posture logger |
| 7 | `end_of_day_fatigue_0_10` | integer | end-of-day fatigue, 0 to 10 scale, higher is worse | 1 to 8 | questionnaire |
| 8 | `typing_throughput_kpm` | decimal, 1 place | typing throughput in keystrokes per minute during logged work | 132.8 to 287.8 | keyboard software |
| 9 | `work_engagement_0_6` | decimal, 1 place | work engagement, 0 to 6 questionnaire scale, higher means more engaged | 2.1 to 5.8 | questionnaire |

## Recording and rounding

Each value is rounded the way its instrument records it: the 0-to-10 rating scales and the
0-to-6 engagement scale are questionnaire responses, the discomfort and fatigue ratings as
whole numbers and engagement to one decimal place; sitting time is whole minutes and posture
changes a whole count from the logger; typing throughput is keystrokes per minute to one
decimal place from the keyboard software.

## Notes for anyone using the file

- Read `workstation_group` as the grouping variable. It holds exactly two distinct values.
- All seven outcomes are complete for every employee, so no missing-value handling is needed.
- The two conditions overlap on every outcome. Individual employees in either condition can
  be found across most of each scale.
