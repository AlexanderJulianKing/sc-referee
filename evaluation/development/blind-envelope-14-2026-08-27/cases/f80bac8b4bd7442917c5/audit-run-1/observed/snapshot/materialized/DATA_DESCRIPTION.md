# Data description

File: `handball_warmup.csv`

One row is one senior club handball player, measured at the single end-of-study
testing session held on one morning after six weeks on the assigned warm-up
protocol. Every player appears exactly once. The file has a header row, 48 data
rows, and no blank cells.

## Columns

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `player_id` | text | none | Player identifier, `P01` through `P48`, unique within the file. |
| `warm_up` | text | none | Warm-up protocol the player followed for six weeks. Exactly two values: `usual` (club mobility and jogging warm-up) and `neuromuscular` (structured warm-up with added eccentric and balance work). 24 players per group. |
| `cmj_height_cm` | number | centimetres | Countermovement jump height, recorded to one decimal place. |
| `sprint_20m_s` | number | seconds | Twenty metre sprint time from timing gates, recorded to hundredths of a second. |
| `throw_velocity_kmh` | number | kilometres per hour | Ball velocity on a standing handball throw, recorded to one decimal place. |
| `agility_time_s` | number | seconds | Change-of-direction agility test time from timing gates, recorded to hundredths of a second. |
| `knee_flexor_torque_nm` | number | newton metres | Peak isokinetic knee flexor torque, recorded to one decimal place. |

The five outcome columns appear in the declared order: jump height, sprint time,
throw velocity, agility time, knee flexor torque.

## Notes on the recorded values

- Lower values are better for the two timed outcomes (`sprint_20m_s`,
  `agility_time_s`). Higher values are better for the other three.
- Player `P31` has a recorded twenty metre sprint time of `8.74` seconds. No
  senior player runs twenty metres that slowly; the value is consistent with a
  timing gate that triggered late. It is left in the file exactly as recorded.
  Every other sprint time falls between 2.97 and 3.53 seconds.
- Observed spans of the remaining columns: jump height 27.6 to 49.4 cm, throw
  velocity 63.4 to 94.6 km/h, agility time 8.95 to 11.55 s, knee flexor torque
  144.2 to 238.7 N·m.
