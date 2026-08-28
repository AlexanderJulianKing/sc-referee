# Source-capture ventilation and solvent vapour exposure in nail salon technicians

## Data

`data.csv` holds one row per technician. Each row carries that technician's bench type and the five
outcome measurements taken over a single monitored shift. The columns are:

- `technician_id`: identifier for the technician, and so for the salon and the monitored shift
  (text label, `tech_01` through `tech_56`).
- `ventilation`: bench type (text label, two levels). `capture` is a bench fitted with source-capture
  local exhaust ventilation; `no_capture` is a bench with no source capture and general room
  ventilation only.
- `tvoc_mg_m3`: personal airborne total volatile organic compounds over the shift, from the
  technician's personal sampler, in milligrams per cubic metre.
- `urinary_acetone_mg_l`: acetone in the end-of-shift urine sample, in milligrams per litre.
- `eye_irritation_0_10`: self-reported eye irritation at the end of the shift, on a 0 to 10 rating
  scale, higher is worse.
- `headache_0_10`: self-reported headache at the end of the shift, on a 0 to 10 rating scale, higher
  is worse.
- `neurobehavioural_score_0_30`: score on the end-of-shift neurobehavioural symptom questionnaire,
  0 to 30 points, higher is worse.

There are 56 technicians and no missing values.

## Design

Fifty-six nail salon technicians took part, each working in a different salon and each monitored
across one full working shift of similar length and client load. Twenty-eight worked at benches
fitted with source-capture local exhaust ventilation and twenty-eight worked at benches with general
room ventilation only. Each technician wore a personal sampler for the shift, gave an end-of-shift
urine sample, and completed the symptom items at the end of the shift.

The survey protocol declared five outcomes before fieldwork began, in this fixed order: personal
airborne TVOC, end-of-shift urinary acetone, eye irritation, headache, and the neurobehavioural
symptom score.

## Method

The two ventilation groups are independent samples of technicians, so each declared outcome was
compared between the groups with a two-sided two-sample Welch t-test, one test per outcome, taking
the five outcomes in the declared order. Each outcome is its own exposure or health question, and
each was judged at the conventional 0.05 threshold on its own p-value.

## Results

Group sizes were 28 technicians at capture benches and 28 at uncaptured benches. Values below are
mean plus or minus standard deviation, and the difference is the uncaptured group minus the capture
group.

| Outcome | Capture (n=28) | No capture (n=28) | Difference | Welch t | p | Conclusion at 0.05 |
|---|---|---|---|---|---|---|
| `tvoc_mg_m3` | 1.43 +/- 0.69 | 3.33 +/- 0.98 | +1.90 | t(48.4) = -8.429 | < 0.001 | significant |
| `urinary_acetone_mg_l` | 1.99 +/- 0.90 | 3.47 +/- 1.22 | +1.48 | t(49.8) = -5.169 | < 0.001 | significant |
| `eye_irritation_0_10` | 2.57 +/- 1.20 | 3.00 +/- 1.68 | +0.43 | t(48.9) = -1.100 | 0.277 | not significant |
| `headache_0_10` | 2.32 +/- 1.33 | 2.57 +/- 1.29 | +0.25 | t(53.9) = -0.713 | 0.479 | not significant |
| `neurobehavioural_score_0_30` | 6.29 +/- 3.52 | 7.43 +/- 3.55 | +1.14 | t(54.0) = -1.210 | 0.232 | not significant |

Personal airborne TVOC was 1.90 mg/m3 higher at uncaptured benches, 3.33 against 1.43 mg/m3, and
that difference was significant. End-of-shift urinary acetone was 1.48 mg/L higher at uncaptured
benches, 3.47 against 1.99 mg/L, and was also significant. The three end-of-shift symptom outcomes
all pointed the same way, with uncaptured technicians reporting slightly worse eye irritation
(+0.43 rating points), headache (+0.25 points), and neurobehavioural score (+1.14 points), but none
of those three differences reached the 0.05 threshold.

## Conclusion

In this survey, technicians at benches with source-capture local exhaust ventilation had markedly
lower solvent vapour exposure than technicians at benches with general room ventilation only, both
in the air they breathed over the shift and in the acetone measured in their end-of-shift urine.
The end-of-shift symptom reports were all somewhat milder in the capture group as well, but those
differences were small relative to the spread between technicians and did not meet the 0.05
threshold. The survey supports source capture as an effective control for airborne and absorbed
solvent exposure, while its effect on end-of-shift symptoms remains undemonstrated at this sample
size.
