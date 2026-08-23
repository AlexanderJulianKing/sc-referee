# Sleep efficiency on slow versus rapid shift rotation

## Question

Does sleep quality differ between two shift-rotation patterns at a large distribution
warehouse? Sleep quality is measured as sleep efficiency, the percentage of time in bed
that is actually spent asleep, scored each night by a wrist actigraphy monitor. Higher is
better. The two patterns compared are a slowly rotating shift pattern (`slow`) and a
rapidly rotating one (`rapid`).

## Data description

The single data file is `sleep_efficiency.csv`. The data are simulated, not collected from
real people.

**One row is one monitored night for one worker.** Each of the 26 workers was monitored on
seven consecutive nights, so each worker contributes seven rows and the seven rows sharing
a `worker_id` are repeated measurements from the same person.

The file has four columns, in this order:

| # | Column | Type | Meaning |
| --- | --- | --- | --- |
| 1 | `worker_id` | text, `WK-01` ... `WK-26` | Which worker was monitored. Appears on exactly 7 rows. |
| 2 | `rotation_pattern` | text, `slow` or `rapid` | Which shift-rotation pattern that worker was on. Constant across all 7 of a worker's rows, so it is a property of the person. |
| 3 | `night_number` | integer, 1 ... 7 | Which of the seven consecutive monitored nights this row is, counted within the worker. |
| 4 | `sleep_efficiency_pct` | number, one decimal place | The outcome: percentage of time in bed spent asleep on that night. |

Counts in the file: 182 data rows (183 lines including the header), 26 workers, 7 nights
per worker, 13 workers on `slow` (91 rows) and 13 on `rapid` (91 rows). There are no
missing values. Night-level values run from 61.7 to 99.0 percent; three nights sit exactly
on the 99.0 ceiling used when the values were simulated.

**How many values entered the statistical comparison: 26.** One value per worker, not one
per night. The 182 nights were first averaged down to 26 worker means, and those 26 numbers
are what the test was run on.

## Analysis unit

The analysis unit is the worker. Nights are the underlying measurements. Seven nights from
one person are not seven independent people: they share that person's own usual sleep level,
so treating them as separate observations would count the same person seven times and make
the evidence look stronger than it is. The script therefore reduces the night-level table to
one mean per worker in a separate named step (`reduce_nights_to_workers` in `analysis.py`)
before any comparison is made, and the two-sample test runs on the per-worker table that
step returns.

## Numbers

| Rotation pattern | Workers | Mean sleep efficiency (%) | SD of worker means (pp) | Range of worker means (%) |
| --- | --- | --- | --- | --- |
| slow | 13 | 84.38 | 4.74 | 77.91 - 92.83 |
| rapid | 13 | 78.74 | 5.21 | 71.43 - 88.39 |
| **Total** | **26** | | | |

- Difference (slow minus rapid): **5.64 percentage points**, favouring the slow rotation.
- 95 percent confidence interval for the difference: 1.61 to 9.67 percentage points.
- Independent two-sample t test (equal variances, Student's t) on the 26 worker means:
  **t(24) = 2.888, p = 0.0081**.

## Conclusion

Workers on the slowly rotating shift pattern slept better. Their mean sleep efficiency was
84.38 percent against 78.74 percent for the rapidly rotating pattern, a difference of 5.64
percentage points. With 13 workers per group the difference is statistically significant at
the conventional 5 percent level (p = 0.0081), and the confidence interval places the true
difference somewhere between about 1.6 and 9.7 percentage points, so the direction is clear
even though the size is not pinned down tightly.

Two limits are worth stating. The comparison rests on 26 people, so the interval is wide.
And the workers were not randomly assigned to rotation patterns in this design, so the
result is an observed difference between two groups of workers, not proof that the rotation
pattern itself caused it.
