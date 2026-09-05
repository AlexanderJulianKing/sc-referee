# Mandibular advancement device study: two device designs compared

## Data

The data file is `mad_device_study.csv`, with 50 data rows and one header row.

One row is one adult participant with moderate obstructive sleep apnoea. The row holds that
person's device assignment and the five protocol outcomes from a single overnight home sleep study
carried out after eight weeks of device use. Each participant appears exactly once, there are no
repeated measurements, and no cell is blank. Twenty-five participants were fitted with each device
design.

| Column | Meaning | Unit or scale |
| --- | --- | --- |
| `participant_id` | Study identifier for the participant, `P001` through `P050` | Identifier, no unit |
| `device_group` | Device design fitted: `custom_titratable_two_piece` or `prefabricated_one_piece` | Categorical label, no unit |
| `ahi_events_per_hour` | Apnoea-hypopnoea index: apnoeas and hypopnoeas per hour of sleep. Declared outcome 1 | Events per hour |
| `odi_events_per_hour` | Oxygen desaturation index: qualifying desaturation events per hour of sleep. Declared outcome 2 | Events per hour |
| `epworth_sleepiness_score_0_24` | Epworth Sleepiness Scale total score; higher means more daytime sleepiness. Declared outcome 3 | Integer points, 0 to 24 scale |
| `min_oxygen_saturation_percent` | Lowest pulse-oximetry oxygen saturation reached during the overnight study. Declared outcome 4 | Percent |
| `sleep_efficiency_percent` | Time asleep as a share of time in bed. Declared outcome 5 | Percent |

## Analysis

Each of the five declared outcomes was compared between the two device groups with the same test, a
Welch two-sample t-test. The five outcomes were declared in the protocol before recruitment as one
outcome family, so **all five raw p-values were adjusted together as one complete family** using the
Holm step-down procedure, which controls the family-wise error rate at 0.05. Every verdict below is
read from the adjusted p-value, not the raw one.

## Results

| Outcome | Mean, custom titratable two-piece (n = 25) | Mean, prefabricated one-piece (n = 25) | Raw p | Adjusted p | Verdict at family-wise 0.05 |
| --- | --- | --- | --- | --- | --- |
| `ahi_events_per_hour` | 13.316 | 18.820 | 0.000641 | 0.003207 | Significant |
| `odi_events_per_hour` | 9.960 | 14.248 | 0.002187 | 0.008747 | Significant |
| `epworth_sleepiness_score_0_24` | 8.640 | 8.760 | 0.918311 | 0.918311 | Not significant |
| `min_oxygen_saturation_percent` | 86.548 | 84.592 | 0.126593 | 0.253186 | Not significant |
| `sleep_efficiency_percent` | 86.924 | 82.404 | 0.002693 | 0.008747 | Significant |

All five outcomes were adjusted together as a single family of five; none was adjusted on its own or
in a smaller subset.

Three outcomes separate the designs after adjustment. The custom titratable two-piece device gives a
lower apnoea-hypopnoea index (13.316 against 18.820 events per hour), a lower oxygen desaturation
index (9.960 against 14.248 events per hour), and a higher sleep efficiency (86.924 percent against
82.404 percent). Daytime sleepiness and minimum overnight oxygen saturation do not separate the two
designs after adjustment.

## Sensitivity check (robustness only, not an inferential result)

Participant `P032` has a recorded `min_oxygen_saturation_percent` of 62.4 percent. That value is
implausibly low for this population, and the sleep technician's note attributes it to the pulse
oximeter probe slipping off the finger for part of the night, so the number reflects a detached
sensor rather than the participant's true overnight nadir. The value stays in the data file exactly
as recorded and stays in the family analysis above. It was set aside for this one re-run only, to
check whether a single instrument artefact was driving the saturation comparison.

With `P032` excluded, the minimum oxygen saturation comparison gives group means of 86.548 percent
(custom titratable two-piece, n = 25) against 85.517 percent (prefabricated one-piece, n = 24), a
Welch t statistic of 1.1971, and an unadjusted p-value of 0.237289.

This is a robustness check on one outcome, not a sixth result. It is not entered into the family
adjustment and it carries no verdict of its own. The inference for minimum oxygen saturation remains
the family analysis: adjusted p = 0.253186, not significant at the family-wise 0.05 level. Setting
the artefact aside moves the group means closer together and leaves that conclusion unchanged, which
is the reassurance the check was run for.

## Conclusion

At eight weeks, the custom titratable two-piece device outperformed the prefabricated one-piece
device on the two respiratory outcomes and on sleep efficiency, and these three differences survive
family-wise adjustment across all five declared outcomes. Self-reported daytime sleepiness was
essentially identical between the designs, and minimum overnight oxygen saturation did not separate
them, with or without the sensor-artefact reading. On this evidence the custom titratable two-piece
design is the better choice for respiratory control and sleep continuity in adults with moderate
obstructive sleep apnoea, while neither design shows an advantage in symptom burden or oxygen nadir.
These findings come from a small single-clinic comparison of 25 participants per group with one
overnight study each, so they need confirmation in a larger sample before they guide practice
broadly.
