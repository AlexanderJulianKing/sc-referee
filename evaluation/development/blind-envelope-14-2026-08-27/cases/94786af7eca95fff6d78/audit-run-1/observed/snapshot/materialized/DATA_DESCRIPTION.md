# Data description

**File:** `room_attendant_workload.csv`

**What one row represents:** one hotel room attendant, measured over a single
instrumented shift at the end of the four-week study period. Each attendant
appears exactly once. There are 72 rows: 36 attendants in the `solo` scheme
and 36 in the `paired` scheme. There are no missing values.

## Columns

| Column | Type | Units / scale | Meaning |
| --- | --- | --- | --- |
| `worker_id` | text | — | Attendant identifier, `RA-001` through `RA-072`. Unique per row. |
| `work_scheme` | text | `solo` or `paired` | Work-organisation scheme the attendant was assigned to for the four weeks. `solo` = cleans rooms alone in the usual way; `paired` = works in a fixed pair sharing each room. |
| `borg_exertion` | integer | Borg 6-20 scale | Declared outcome 1. Perceived exertion reported at end of shift. |
| `neck_shoulder_vas_mm` | integer | mm, 0-100 | Declared outcome 2. Neck and shoulder pain at end of shift on a visual analogue scale. |
| `wrist_hand_vas_mm` | integer | mm, 0-100 | Declared outcome 3. Wrist and hand pain at end of shift on a visual analogue scale. |
| `rooms_per_shift` | integer | count | Declared outcome 4. Rooms cleaned during the instrumented shift. |
| `mean_heart_rate_bpm` | number (1 decimal) | beats per minute | Declared outcome 5. Mean heart rate across the shift. |
| `trunk_flexion_over60_pct` | number (1 decimal) | percent | Declared outcome 6. Proportion of shift time with trunk flexion beyond 60 degrees. |
| `step_count` | integer | steps | Declared outcome 7. Steps recorded over the shift. |
| `recovery_need_score` | integer | 0-100 scale | Declared outcome 8. Need-for-recovery score reported after the shift. |

Outcome columns appear in the pre-declared order, after the identifier and
group columns. Higher values mean more exertion, more pain, more output, more
movement, or greater need for recovery, depending on the column.

## Provenance

The values are synthetic, produced by `make_data.py` in this directory with a
fixed random seed. Each attendant's outcomes are generated from two shared
person-level factors (general physical strain and work pace), so the outcomes
are correlated within a person the way field measurements are. Whole-number
scales are stored as whole numbers, and values are held inside the plausible
range of each instrument.
