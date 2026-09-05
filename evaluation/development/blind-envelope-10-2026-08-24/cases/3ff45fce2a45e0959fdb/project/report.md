# Foam versus alginate dressings for chronic venous leg ulcers

A community wound-care service compared a standard foam dressing with an alginate dressing for
chronic venous leg ulcers. Both dressings were used under the same compression bandaging regimen.
Ninety adult patients took part, forty-five in each arm, and each patient was followed for twelve
weeks. One ulcer per patient was studied.

## Data description

The analysis reads a single file, `venous_ulcer_dressings.csv`, which holds 90 data rows plus a
header row. **One row is one patient**, carrying that patient's single studied ulcer: the dressing
the patient was assigned and the six protocol outcomes, each measured once for that patient over the
whole twelve-week follow-up. No patient appears twice, and there are no empty cells.

| Column | Type | Meaning |
| --- | --- | --- |
| `patient_id` | text | Study identifier for the patient, `WLU-001` to `WLU-090`, unique across the file. |
| `dressing_group` | text | The assigned dressing. Exactly two values, `dressing_foam` and `dressing_alginate`, with 45 patients each. |
| `area_reduction_pct` | number, 1 decimal | Ulcer area reduction from baseline, in percent, at twelve weeks. Higher means more of the ulcer closed. |
| `pain_vas_mm` | integer | Worst weekly ulcer pain the patient reported, on a 0 to 100 millimetre visual analogue scale. Higher means more pain. |
| `exudate_score` | number, 1 decimal | Clinician exudate (wound fluid) score on a 0 to 10 scale. Higher means a wetter wound. |
| `periwound_erythema_mm` | number, 1 decimal | Width of the reddened skin ring around the wound edge, in millimetres. Higher means more surrounding inflammation. |
| `days_to_half_healing` | integer | Days from baseline until the ulcer reached fifty percent of its starting area. Lower means faster healing. |
| `wound_qol_score` | integer | Wound-specific quality of life score on a 0 to 100 scale. Higher is better. |

The six outcome columns above appear in the order the protocol declared them.

## Methods

Each declared outcome was compared between the two dressing arms with an independent two-sample
t-test, and judged at the conventional 0.05 threshold. Group means and standard deviations were
computed for every outcome. The analysis script is `analysis.py`, and every number below is one the
script produced.

## Group summaries

Mean, with standard deviation in brackets. Both arms have 45 patients.

| Outcome | Foam | Alginate |
| --- | --- | --- |
| Ulcer area reduction from baseline (%) | 55.96 (17.17) | 66.42 (18.79) |
| Worst weekly pain (VAS, mm) | 43.38 (12.28) | 39.89 (11.77) |
| Clinician exudate score (0-10) | 4.81 (1.34) | 3.76 (1.66) |
| Periwound erythema width (mm) | 9.24 (5.88) | 9.06 (4.34) |
| Days to 50% area healing | 46.49 (14.04) | 37.09 (12.74) |
| Wound-specific quality of life (0-100) | 64.84 (10.54) | 69.00 (12.23) |

## Per-outcome results

Differences are foam minus alginate. Verdicts are at the 0.05 threshold.

| # | Outcome | Difference | t | p | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | Ulcer area reduction from baseline (%) | -10.46 | -2.756 | 0.0071 | significant |
| 2 | Worst weekly pain (VAS, mm) | 3.49 | 1.376 | 0.1724 | not significant |
| 3 | Clinician exudate score (0-10) | 1.05 | 3.295 | 0.0014 | significant |
| 4 | Periwound erythema width (mm) | 0.18 | 0.161 | 0.8723 | not significant |
| 5 | Days to 50% area healing | 9.40 | 3.325 | 0.0013 | significant |
| 6 | Wound-specific quality of life (0-100) | -4.16 | -1.727 | 0.0877 | not significant |

1. **Ulcer area reduction.** Alginate ulcers closed more over twelve weeks, 66.42 percent against
   55.96 percent for foam, a gap of 10.46 percentage points. p = 0.0071, significant.
2. **Worst weekly pain.** Foam patients reported 43.38 mm on the visual analogue scale and alginate
   patients 39.89 mm, a gap of 3.49 mm. p = 0.1724, not significant.
3. **Clinician exudate score.** Alginate wounds were drier, scoring 3.76 against 4.81 for foam, a gap
   of 1.05 points. p = 0.0014, significant.
4. **Periwound erythema width.** The two arms were close, 9.24 mm for foam and 9.06 mm for alginate,
   a gap of 0.18 mm. p = 0.8723, not significant.
5. **Days to 50 percent area healing.** Alginate ulcers reached half their starting area sooner, at
   37.09 days against 46.49 days for foam, a gap of 9.40 days. p = 0.0013, significant.
6. **Wound-specific quality of life.** Alginate patients scored 69.00 and foam patients 64.84, a gap
   of 4.16 points. p = 0.0877, not significant.

Three of the six declared outcomes were significant at 0.05: area reduction, exudate score, and days
to fifty percent healing.

## Conclusion

The service should prefer the alginate dressing. The advantage shows up on the healing and wound
fluid side of the six declared outcomes: alginate ulcers closed more of their area by twelve weeks,
reached half their starting area about nine days sooner, and ran drier on the clinician exudate
score. Each of those three differences was significant at the 0.05 threshold.

The advantage did not extend to the patient-experience and surrounding-skin outcomes. Worst weekly
pain, periwound erythema width, and wound-specific quality of life were not significantly different
between the two dressings. Erythema in particular was near identical in the two arms. So the case for
alginate rests on faster and more complete healing with less exudate, and not on comfort, quality of
life, or the condition of the skin around the wound.
