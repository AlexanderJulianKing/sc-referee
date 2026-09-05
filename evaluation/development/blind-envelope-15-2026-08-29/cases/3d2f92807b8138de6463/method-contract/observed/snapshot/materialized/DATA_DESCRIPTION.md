# Data description

`data.csv` holds the post-training test session for a study of two eight-week hangboard
programmes in 34 experienced sport climbers, matched at baseline for climbing grade. All
measurements were taken at the same post-training session on the same 20 mm edge, and every
climber completed the session.

**One row is one climber**, with that climber's training group and their seven post-training
outcome values. There are 34 data rows plus a single header row: no repeated climbers, no
summary or total rows, and no blank cells.

## Columns, in file order

| Column | Meaning | Unit / scale |
| --- | --- | --- |
| `climber_id` | Climber identifier, `clb_01` through `clb_34`, unique per row | none (text label) |
| `hangboard_protocol` | Training group: `max_hangs` (maximal hangs with long rests) or `repeaters` (short repeater hangs), 17 climbers each | none (text label) |
| `peak_force_n` | Peak finger flexor force on the 20 mm edge | newtons (N), one decimal |
| `critical_force_pct` | Critical force, the sustainable force, expressed as a percentage of that climber's peak force | percent (%), one decimal |
| `time_to_failure_s` | Time to failure hanging at 60 percent of peak force | seconds (s), one decimal |
| `rate_of_force_development_n_per_s` | Rate of force development over the first 200 ms of the pull | newtons per second (N/s), whole numbers |
| `resaturation_half_time_s` | Forearm muscle oxygen resaturation half time measured after failure | seconds (s), one decimal |
| `moves_to_failure` | Number of moves completed to failure on a standard bouldering circuit | count of moves, whole numbers |
| `finger_soreness_0_10` | Self-reported finger soreness during the final training week | rating on a 0 to 10 scale, one decimal |

Columns 3 through 9 are the seven outcomes of the declared outcome family, listed here in the
order in which the study protocol declared them.

## Provenance

The values are invented for this project. `make_data.py` in this directory drew them from the
typical group values and spreads described in the study scenario, with a shared strength factor
and a shared endurance factor so that the outcomes correlate within a climber the way laboratory
measurements do. Values were then rounded as a sports laboratory would round them, and kept
inside their physical limits (forces and times non-negative, the critical force percentage at or
below 100, the soreness rating between 0 and 10).

`data.csv` is a fixed data file. It is read as given and is never regenerated or overwritten by
the analysis.
