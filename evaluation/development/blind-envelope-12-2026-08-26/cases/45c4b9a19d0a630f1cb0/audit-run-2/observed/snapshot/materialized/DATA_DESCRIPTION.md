# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Seeded Python generator. Running it writes `bread_study_data.csv`. The seed is fixed, so the same CSV comes out every time. |
| `bread_study_data.csv` | The end-of-study measurement table for the eight-week bread feeding study. 58 data rows plus one header row. |

## `bread_study_data.csv`

**What one row represents:** one participant, holding that person's end-of-study
values. Every participant was measured once, during the measurement week at the end
of the eight weeks, and appears exactly once in the table. There are 58 rows: 29
participants who ate the wholegrain rye bread and 29 who ate the refined wheat
bread. No cell is blank.

**Columns**, in the order they appear in the file:

| # | Column | Type | Unit | What it holds |
| --- | --- | --- | --- | --- |
| 1 | `participant_id` | text | none | The participant identifier, `P01` through `P58`. Unique across the file. |
| 2 | `group` | text | none | The bread the participant ate for the eight weeks. Exactly two entries appear: `rye` for the wholegrain rye bread and `refined_wheat` for the refined wheat bread. |
| 3 | `stool_freq_per_week` | number, 1 decimal | bowel movements per week | Stool frequency during the measurement week. |
| 4 | `transit_time_h` | number, 1 decimal | hours | Whole-gut transit time from the swallowed marker study. |
| 5 | `ldl_mmol_l` | number, 2 decimals | millimoles per litre | Fasting low-density lipoprotein cholesterol. |
| 6 | `insulin_pmol_l` | number, 1 decimal | picomoles per litre | Fasting insulin. |
| 7 | `butyrate_mmol_kg` | number, 1 decimal | millimoles per kilogram of wet faeces | Faecal butyrate concentration. |

Columns 3 through 7 are the five outcomes named in the protocol, and they appear in
the file in the order the protocol declares them.

**Observed ranges in this file** (all 58 rows together):

| Column | Lowest | Highest |
| --- | --- | --- |
| `stool_freq_per_week` | 4.0 | 14.0 |
| `transit_time_h` | 20.9 | 61.8 |
| `ldl_mmol_l` | 1.91 | 4.55 |
| `insulin_pmol_l` | 27.3 | 99.0 |
| `butyrate_mmol_kg` | 5.8 | 23.5 |

## How the values were produced

`make_data.py` draws each value from a normal distribution around a plausible adult
mean for that measurement, with person-to-person spread. Group assignment uses
permuted blocks of two, so the identifiers are not sorted by group. Each person also
carries two hidden background traits, one for gut motility and one for metabolic
state, so that a person's stool frequency, transit time and butyrate move together
and their cholesterol and insulin move together, the way they do in real people. Any
draw landing outside the plausible range for that measurement has its independent
noise term redrawn until it lands inside.
