# Room attendant workload: solo versus paired room cleaning

## Design

Seventy-two room attendants employed by the same hotel group were assigned to one of two
work-organisation schemes for four weeks. Thirty-six worked rooms alone in the usual way
(`solo`) and thirty-six worked in fixed pairs sharing each room (`paired`). Shift length,
room type, and equipment were the same in both schemes. Each attendant was measured over
one full instrumented shift at the end of the period, and the same eight pre-declared
outcomes were recorded for everyone. Group sizes are 36 and 36; there are no missing
values.

## Data

**File:** `room_attendant_workload.csv`

**One row** is one attendant, measured over a single instrumented shift at the end of the
four-week period. Each attendant appears exactly once, so the file has 72 rows.

| Column | Units / scale | Meaning |
| --- | --- | --- |
| `worker_id` | text | Attendant identifier, `RA-001` to `RA-072`, unique per row |
| `work_scheme` | `solo` or `paired` | Work-organisation scheme assigned for the four weeks |
| `borg_exertion` | Borg 6-20, whole numbers | Outcome 1: perceived exertion at end of shift |
| `neck_shoulder_vas_mm` | mm, 0-100 | Outcome 2: neck and shoulder pain at end of shift |
| `wrist_hand_vas_mm` | mm, 0-100 | Outcome 3: wrist and hand pain at end of shift |
| `rooms_per_shift` | count | Outcome 4: rooms cleaned during the instrumented shift |
| `mean_heart_rate_bpm` | beats per minute | Outcome 5: mean heart rate across the shift |
| `trunk_flexion_over60_pct` | percent of shift | Outcome 6: time with trunk flexion beyond 60 degrees |
| `step_count` | steps | Outcome 7: steps recorded over the shift |
| `recovery_need_score` | 0-100 | Outcome 8: need-for-recovery score after the shift |

## Analysis

Each outcome was compared between the two schemes with a two-sample Welch t-test, which
does not assume the two schemes have equal variance. Differences are reported as solo
minus paired, so a positive difference means the solo attendants scored higher.

Outcomes 1, 2, 3 and 5 are the team's headline symptom and effort measures. Their
p-values were corrected by hand: each raw p-value was multiplied by the number of
comparisons, four, and capped at 1.0, and the corrected value was judged against 0.05.
The remaining declared outcomes were judged on their raw p-values against 0.05.

## Results

| # | Outcome | Mean solo | Mean paired | Difference | p used | p type | Conclusion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `borg_exertion` | 13.92 | 12.39 | +1.53 | 0.0004 | corrected | Significant: solo higher |
| 2 | `neck_shoulder_vas_mm` | 46.06 | 34.03 | +12.03 | 0.0014 | corrected | Significant: solo higher |
| 3 | `wrist_hand_vas_mm` | 33.78 | 28.14 | +5.64 | 0.1981 | corrected | Not significant |
| 4 | `rooms_per_shift` | 15.14 | 15.22 | -0.08 | 0.8499 | raw | Not significant |
| 5 | `mean_heart_rate_bpm` | 99.50 | 95.21 | +4.29 | 0.0279 | corrected | Significant: solo higher |
| 6 | `trunk_flexion_over60_pct` | 16.50 | 13.50 | +3.00 | 0.0051 | raw | Significant: solo higher |
| 7 | `step_count` | 12800.03 | 13249.92 | -449.89 | 0.2150 | raw | Not significant |
| 8 | `recovery_need_score` | 55.00 | 44.44 | +10.56 | 0.0035 | raw | Significant: solo higher |

Raw p-values for the four hand-corrected outcomes, before the correction, were 0.000095
(outcome 1), 0.000342 (outcome 2), 0.049523 (outcome 3) and 0.006982 (outcome 5).
Outcome 3 sits just under 0.05 before correction and above it afterwards, so its verdict
is the one that turns on the correction.

## Conclusions by outcome

1. **Perceived exertion.** Solo attendants ended the shift 1.53 Borg points higher than
   paired attendants. Significant on the corrected p-value.
2. **Neck and shoulder pain.** Solo attendants reported 12.03 mm more pain on the visual
   analogue scale. Significant on the corrected p-value.
3. **Wrist and hand pain.** Solo attendants reported 5.64 mm more pain, a marginal
   result: below 0.05 on the raw p-value but above it once corrected. Not significant as
   judged here.
4. **Rooms cleaned per shift.** The two schemes cleaned essentially the same number of
   rooms per attendant, 15.14 against 15.22. Not significant.
5. **Mean heart rate.** Solo attendants averaged 4.29 bpm higher across the shift.
   Significant on the corrected p-value.
6. **Trunk flexion beyond 60 degrees.** Solo attendants spent 3.00 percentage points more
   of the shift in deep trunk flexion. Significant on the raw p-value.
7. **Step count.** Paired attendants took about 450 more steps, which is not distinguishable
   from chance here. Not significant.
8. **Need for recovery.** Solo attendants scored 10.56 points higher after the shift.
   Significant on the raw p-value.

## Occupational health interpretation

The pattern points the same way across the measures that describe how hard the shift is
on the body. Attendants working alone reported higher perceived exertion, more neck and
shoulder pain, a higher average heart rate through the shift, more time bent past 60
degrees, and a greater need to recover afterwards. Wrist and hand pain moved in the same
direction but did not clear the threshold once corrected.

What makes this worth acting on is outcome 4. Rooms cleaned per shift was effectively
identical in the two schemes, and step count was not distinguishable either. Pairing did
not cost output per attendant in this study, yet the attendants in pairs finished their
shifts with less strain. The two measures that describe posture and cardiovascular load,
trunk flexion and heart rate, suggest a plausible route: sharing a room lets two people
split the awkward tasks, such as bed-making and bathroom work, that drive deep forward
bending.

The need-for-recovery gap, 55.0 against 44.4, is the measure most tied to how the job
carries into the rest of the day. A gap that size matters for fatigue that accumulates
across a work week.

These results come from one instrumented shift per attendant at the end of a four-week
period, in one hotel group, so they describe that setting. The pain and exertion measures
are self-reported, while heart rate, trunk flexion, and step count are instrumented; the
agreement between the two kinds of measure is what makes the overall picture more
convincing than any single outcome.
