# Data description

## File

`reef_fish_surveys.csv` — one plain-text CSV at the project root, comma separated,
with a header line and 80 data rows.

The file was produced once by `make_data.py` (Python standard library only, fixed
random seed `20260823`) and is committed as text. The analysis reads the CSV; it does
not regenerate the numbers.

## What one row is

**One row is one dive survey of one artificial reef module.** It records the number
of fish counted inside the fixed survey radius around that module on that occasion.

## Units and counts

- 16 artificial reef modules, deployed on sandy seabed at similar depth and spacing.
- 5 dive surveys per module, spread over one summer.
- 16 x 5 = **80 rows**.
- The **module** is the independent unit here, not the row. The five surveys of one
  module are repeat visits to the same patch of reef, so they are correlated with each
  other. There are 16 independent units, 8 per design.

## The two groups

The grouping variable is `reef_design`, with two levels and eight modules each:

| `reef_design` value   | Modules | Rows | What it is |
| --------------------- | ------- | ---- | ---------- |
| `simple_block`        | 8 (MOD01–MOD08) | 40 | Simple block modules: plain low-complexity concrete blocks with few interstitial spaces. |
| `complex_high_relief` | 8 (MOD09–MOD16) | 40 | Complex high-relief modules: tall, structurally intricate units with many interstitial spaces and holes for shelter. |

## Columns

| Column | Type | Values | Meaning |
| ------ | ---- | ------ | ------- |
| `module_id` | text | `MOD01`–`MOD16` (16 distinct values, each on exactly 5 rows) | Identifier of the artificial reef module surveyed. Constant across that module's five surveys. Modules `MOD01`–`MOD08` are simple blocks; `MOD09`–`MOD16` are complex high-relief units. |
| `reef_design` | text | `simple_block`, `complex_high_relief` | Design of the module. A property of the module, so it is the same on all five of that module's rows. This is the group being compared. |
| `survey_number` | integer | `1`–`5` | Which of the five survey occasions this row is, in time order within the module. Every module has one row per survey number. |
| `fish_count` | integer | whole numbers, 0 and above | Outcome. Total fish counted within the fixed survey radius on that dive. Whole fish, never negative. |

## Realised values in the committed file

For orientation only; the analysis computes its own numbers from the CSV.

- `simple_block`: 40 survey rows, mean 21.7 fish, range 0 to 42.
- `complex_high_relief`: 40 survey rows, mean 29.9 fish, range 12 to 47.
- Module means range from 7.0 to 42.4 fish, so modules differ noticeably from one
  another on top of the survey-to-survey wobble. One survey of one weak simple module
  recorded zero fish.
- No missing values; every module has all five surveys.
