# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Seeded generator that writes `exo_picking_trial.csv`. Running it again with the same seed reproduces the file exactly. |
| `exo_picking_trial.csv` | The measurement file for the study. 100 data rows plus one header row. |

## `exo_picking_trial.csv`

**One row is one order picker**, measured once on a single standardised mixed-case
picking round during one full shift. Each picker appears exactly once. There are 100
pickers: 50 in the exoskeleton group and 50 in the control group. Every cell is filled;
the file contains no blanks and no missing-value codes.

The file is comma separated, UTF-8, with the header row
`picker_id,exo_group,peak_lumbar_compression_n,borg_exertion_score,round_time_min,picking_errors,shoulder_discomfort_score`.

### Columns

| Column | Type | Values in this file | Meaning |
| --- | --- | --- | --- |
| `picker_id` | text | `P001` to `P100`, each used once | Identifier for the order picker. Carries no information about the group. |
| `exo_group` | text | exactly two values: `exoskeleton`, `control` | Whether the picker wore the passive back-support exoskeleton for the shift (`exoskeleton`) or worked the same shift pattern without it (`control`). 50 rows of each. |
| `peak_lumbar_compression_n` | integer | 2047 to 5204 | Highest lumbar spine compression force recorded during the round, in newtons, rounded to the nearest newton. |
| `borg_exertion_score` | integer | 10 to 19 | Borg rating of perceived exertion given by the picker at the end of the round, on the 6 to 20 scale. Higher means harder perceived work. |
| `round_time_min` | number, one decimal place | 19.2 to 42.2 | Time the picker took to complete the standardised round, in minutes. |
| `picking_errors` | integer count | 0 to 8 | Number of picking errors (wrong item, wrong quantity, wrong location) made during the round. |
| `shoulder_discomfort_score` | integer | 0 to 9 | Shoulder discomfort the picker reported at the end of the shift, on a 0 to 10 scale where 0 is no discomfort. |

The five outcome columns (`peak_lumbar_compression_n`, `borg_exertion_score`,
`round_time_min`, `picking_errors`, `shoulder_discomfort_score`) are the five outcomes
the protocol declared in advance, and they are listed above in that declared order. Each
one is measured once per picker.

## How the file was produced

`make_data.py` draws each picker's values from fixed distributions with a fixed seed
(`SEED = 20260824`), so the file is reproducible. Each picker carries a latent strain
score, so lumbar compression, perceived exertion and shoulder discomfort move together
somewhat within a picker instead of being independent. Group offsets are set separately
for each outcome and are listed at the top of the script.
