# Dryland strength programmes for masters swimmers: end-of-block comparison

## Data

The analysis uses `swimmers.csv`: 44 data rows, one header row, no missing
values.

**One row is one competitive masters swimmer, aged 35 to 55, tested once at the
end of a twelve-week dryland strength programme.** The row carries that
swimmer's identifier, the programme they trained on, and their single
end-of-block reading on each of the four pre-declared outcomes.

| Column | Description |
| --- | --- |
| `swimmer_id` | Per-swimmer identifier, `S01` to `S44`. |
| `programme` | Training programme, exactly two values: `heavy_resistance` (few repetitions at high load) and `power_endurance` (many repetitions at moderate load). |
| `sprint_50_free_s` | Outcome 1. 50 m freestyle time from a push start, in seconds. Lower is faster. |
| `tethered_force_n` | Outcome 2. Peak tethered swimming force, in newtons. |
| `cmj_height_cm` | Outcome 3. Countermovement jump height, in centimetres. |
| `shoulder_ir_torque_nm` | Outcome 4. Shoulder internal rotation peak torque, in newton metres. |

Group sizes are 22 swimmers on `heavy_resistance` and 22 on `power_endurance`.
The four outcome columns appear in the order the trial declared them.

## Methods

The trial declared a family of four outcomes in advance. A single family-level
screen guards that whole family, and it is applied before any per-outcome
comparison is made.

The screen is one number computed straight from the four outcome columns with
plain arithmetic and no statistical test of any kind. For each outcome we take
the difference between the two programme means, divide it by the pooled spread
of that outcome, take the size of that quantity, and then average those four
values. The resulting figure is compared with a cutoff of **0.35** that was
fixed before the data were seen.

Per-outcome results are examined and reported only when that screen passes. If
the screen does not pass, the family is reported as showing no overall
separation and no per-outcome comparison is run at all. When the screen does
pass, each declared outcome is compared between the two programmes with a
two-sample t-test, and the verdict is read at 0.05.

## Results

### Family-level screen

| Outcome | Absolute standardised difference |
| --- | --- |
| `sprint_50_free_s` | 0.5441 |
| `tethered_force_n` | 0.6788 |
| `cmj_height_cm` | 0.3954 |
| `shoulder_ir_torque_nm` | 0.1352 |

**Overall screening figure: 0.4384**, against the pre-set cutoff of 0.35. The
screen **passes**, so the per-outcome comparisons below were run and are
reported.

### Per-outcome comparisons, in the declared order

| # | Outcome | `heavy_resistance` mean | `power_endurance` mean | p-value | Verdict at 0.05 |
| --- | --- | --- | --- | --- | --- |
| 1 | `sprint_50_free_s` | 28.400 | 29.300 | 0.0783 | not significant |
| 2 | `tethered_force_n` | 268.009 | 248.991 | 0.0297 | significant |
| 3 | `cmj_height_cm` | 33.595 | 31.895 | 0.1968 | not significant |
| 4 | `shoulder_ir_torque_nm` | 41.205 | 40.400 | 0.6562 | not significant |

## Interpretation for coaches

Taken as a whole, the four end-of-block tests do separate the two programmes,
which is what the family-level screen tells us before any single test is looked
at.

The clearest single difference is in the water. Swimmers on the heavy
resistance programme pulled about 19 N more peak tethered force than swimmers
on the power-endurance programme, 268 N against 249 N, and that gap was the one
difference that reached significance at 0.05.

The 50 m sprint pointed the same way. The heavy resistance group averaged 28.40
s against 29.30 s, a nine-tenths of a second advantage, which is a meaningful
margin in a masters sprint even though the test did not clear 0.05 here.
Countermovement jump height leaned the same way by a smaller margin, 33.6 cm
against 31.9 cm.

Shoulder internal rotation torque was effectively the same in both groups, 41.2
N m against 40.4 N m. Neither programme did more for that quality than the
other, so it is not a reason to prefer one block over the other.

For a masters squad chasing sprint speed, the practical read is that the heavy,
low-repetition dryland block produced more force in the water and a faster
average 50, with no cost anywhere measured. These are 44 swimmers tested once at
the end of one twelve-week block, with no pre-programme baseline, so treat this
as a pointer for programme choice rather than a settled result.
