# Two pre-match warm-up protocols in senior club handball players

## Data

The analysis uses one file, `handball_warmup.csv`. One row is one senior club
handball player, measured at the single end-of-study testing session held on one
morning after six weeks on the assigned warm-up protocol. Each player appears
exactly once. The file has a header row, 48 data rows, and no blank cells.

| Column | What it holds |
| --- | --- |
| `player_id` | Player identifier, `P01` through `P48`, unique within the file. |
| `warm_up` | The warm-up protocol the player followed for six weeks. Exactly two values: `usual` and `neuromuscular`. |
| `cmj_height_cm` | Countermovement jump height, in centimetres. |
| `sprint_20m_s` | Twenty metre sprint time from timing gates, in seconds, to hundredths. |
| `throw_velocity_kmh` | Ball speed on a standing handball throw, in kilometres per hour. |
| `agility_time_s` | Change-of-direction agility test time from timing gates, in seconds, to hundredths. |
| `knee_flexor_torque_nm` | Peak isokinetic knee flexor torque, in newton metres. |

For the two timed outcomes, `sprint_20m_s` and `agility_time_s`, a lower value
is better. For the other three, a higher value is better.

## Design

Forty-eight players from the same regional league were allocated to one of two
warm-up protocols and followed it for six weeks. Twenty-four players did the
club's usual mobility and jogging warm-up (`usual`). Twenty-four did a
structured neuromuscular warm-up with added eccentric and balance work
(`neuromuscular`). All 48 players were then measured on the same five outcomes
in one testing session. Group sizes are 24 and 24, and every player has a value
for every outcome.

The five outcomes were declared before the study, in this fixed order: jump
height, sprint time, throw velocity, agility time, knee flexor torque. Each
outcome was compared between the two groups with a two-sample Welch t-test,
which is the t-test that does not assume the two groups have the same spread.

## How the multiple comparisons were handled

The whole declared family of five outcomes was adjusted together. All five raw
p-values went into a single Holm-Bonferroni step-down adjustment, which controls
the family-wise error rate across the complete family. Controlling the
family-wise error rate means holding down the chance of even one false alarm
anywhere in the set of five, the way a stricter bar for each individual test
keeps the whole batch honest. No outcome was left out of the adjustment, and no
extra comparison was added to it.

Every conclusion below is read off the adjusted p-values, at a threshold of
0.05. The raw p-values are shown for transparency only.

## Results

Means are group averages. The difference is the neuromuscular mean minus the
usual mean.

| Outcome | Usual mean | Neuromuscular mean | Difference | Raw p | Adjusted p | Conclusion from adjusted p |
| --- | --- | --- | --- | --- | --- | --- |
| Countermovement jump height (cm) | 34.75 | 42.15 | +7.40 | <0.0001 | <0.0001 | Difference supported. The neuromuscular group jumped higher. |
| Twenty metre sprint time (s) | 3.23 | 3.40 | +0.17 | 0.4805 | 0.4805 | No supported difference. |
| Throwing velocity (km/h) | 80.51 | 77.30 | -3.22 | 0.0974 | 0.1947 | No supported difference. |
| Change-of-direction agility time (s) | 10.47 | 9.86 | -0.61 | 0.0010 | 0.0038 | Difference supported. The neuromuscular group was faster through the agility test. |
| Peak knee flexor torque (N·m) | 181.47 | 202.36 | +20.89 | 0.0020 | 0.0060 | Difference supported. The neuromuscular group produced more torque. |

Three of the five declared outcomes show a difference that survives the
family-wide adjustment: jump height, agility time, and knee flexor torque, all
favouring the neuromuscular warm-up. Throwing velocity and twenty metre sprint
time do not, so for those two outcomes the study does not claim a difference
between the protocols.

## Robustness check on one suspect timing value

This subsection is a robustness check, not an inferential result. It is not part
of the declared family, it was not adjusted, and it does not produce a verdict.

Player `P31` has a recorded twenty metre sprint time of 8.74 seconds. No senior
player runs twenty metres that slowly, and the value is consistent with a timing
gate that triggered late. Every other sprint time in the file falls between 2.97
and 3.53 seconds. The value was left in the data file exactly as recorded, and
it is included in the family analysis above. The check below simply re-runs the
sprint comparison once with that single record dropped, to see whether the
sprint result depends on it.

| Sprint comparison | Usual mean (s) | Neuromuscular mean (s) | Difference (s) | Raw p | n usual | n neuromuscular |
| --- | --- | --- | --- | --- | --- | --- |
| Family analysis, all data | 3.23 | 3.40 | +0.17 | 0.4805 | 24 | 24 |
| Re-run with `P31` excluded | 3.23 | 3.17 | -0.06 | 0.0509 | 24 | 23 |

Dropping that one record moves the sprint comparison a long way. The direction of
the group difference flips, and the unadjusted p-value falls close to the
conventional 0.05 threshold. That tells us the sprint result is sensitive to the
single suspect value and should be treated with caution, and it flags the timing
record itself as worth checking. It does not change what the study concludes.
This re-run was not part of the declared family, the p-value shown for it is
unadjusted, and no verdict is drawn from it.

## Conclusion

The study's conclusions rest on the adjusted family analysis. Against the
family-wide adjustment of all five declared outcomes, the structured
neuromuscular warm-up is associated with higher countermovement jump height,
faster change-of-direction agility times, and higher peak knee flexor torque.
The study does not claim a difference between the two protocols in throwing
velocity or in twenty metre sprint time. The sprint re-run reported above is a
robustness check on one suspect timing value only, and the sprint conclusion
stays the one from the adjusted family analysis: adjusted p = 0.4805, no
supported difference.
