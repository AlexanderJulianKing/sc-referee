# Data description

## File

`swimmers.csv` — 44 data rows plus one header row, comma separated, no missing
values.

## What one row represents

One row is one competitive masters swimmer, aged 35 to 55, tested once at the
end of a twelve-week dryland strength programme. The row holds that swimmer's
identifier, the programme they were assigned to, and their single end-of-block
reading on each of the four pre-declared outcome variables. Each swimmer
appears exactly once, and every swimmer has a value in all four outcome
columns.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `swimmer_id` | text | Per-swimmer identifier, `S01` through `S44`. Unique; one per row. |
| `programme` | text | Training programme contrast. Exactly two values: `heavy_resistance` (few repetitions at high load) and `power_endurance` (many repetitions at moderate load). |
| `sprint_50_free_s` | number | Outcome 1. 50 metre freestyle time from a push start, in seconds. Lower is faster. |
| `tethered_force_n` | number | Outcome 2. Peak tethered swimming force, in newtons. |
| `cmj_height_cm` | number | Outcome 3. Countermovement jump height, in centimetres. |
| `shoulder_ir_torque_nm` | number | Outcome 4. Isokinetic shoulder internal rotation peak torque, in newton metres. |

The four outcome columns appear in the order the trial declared them.

## Group sizes

| `programme` | Swimmers |
| --- | --- |
| `heavy_resistance` | 22 |
| `power_endurance` | 22 |

## Observed value ranges

| Column | Minimum | Maximum |
| --- | --- | --- |
| `sprint_50_free_s` | 25.55 | 32.08 |
| `tethered_force_n` | 198.6 | 331.2 |
| `cmj_height_cm` | 23.6 | 44.7 |
| `shoulder_ir_torque_nm` | 28.4 | 50.0 |

## Provenance

The values are invented rather than measured. They were produced by
`generate_data.py` in this directory, which draws each swimmer from a shared
latent athleticism factor plus outcome-specific variation, then rescales within
each programme so the group means and athlete-to-athlete spreads sit at the
levels the study describes. The generator is a staging helper and is not part
of the finished project.
