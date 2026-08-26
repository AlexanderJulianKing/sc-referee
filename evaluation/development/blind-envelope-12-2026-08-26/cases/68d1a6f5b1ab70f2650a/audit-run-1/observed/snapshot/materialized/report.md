# Nasal spray service evaluation: corticosteroid versus antihistamine

Allergy clinic, single grass-pollen season. Sixty adults with moderate seasonal allergic
rhinitis each received exactly one regimen for four weeks: an intranasal corticosteroid spray
once daily (30 patients) or an intranasal antihistamine spray twice daily (30 patients). Every
patient attended one end-of-treatment visit at which the whole outcome set was recorded. The
patient is the unit of the study.

## Data

The analysis input is `allergy_spray_trial.csv`: one header row and 60 data rows, comma
separated, no missing values. **One row is one enrolled adult patient**, holding that patient's
treatment arm and the five protocol outcomes as recorded at their single end-of-treatment visit.
Each patient appears exactly once.

| Column | What it holds | Unit / scale |
| --- | --- | --- |
| `patient_id` | Patient identifier, `P001` to `P060`, unique across the file | none, text |
| `group` | Treatment arm, exactly two entries: `corticosteroid` (once daily) and `antihistamine` (twice daily) | none, text |
| `tnss_total` | Total nasal symptom score at end of treatment, the sum of four nasal symptoms each scored 0 to 3. Higher is worse | points, 0 to 12 |
| `pnif_l_min` | Peak nasal inspiratory flow at end of treatment. Higher is better | litres per minute |
| `disturbed_nights` | Nights in the past week with sleep disturbed by nasal symptoms. Higher is worse | nights, 0 to 7 |
| `tos_total` | Total ocular symptom score, the sum of three eye symptoms each scored 0 to 3. Higher is worse | points, 0 to 9 |
| `rqlq_total` | Rhinoconjunctivitis quality of life total score, averaged to a 0 to 6 scale. Higher is worse | points, 0 to 6 |

The five outcome columns appear in the protocol's declared order.

## Method

Each declared outcome was compared between the two arms with a Welch two-sample t-test on the
patient values (`analysis.py`). Five comparisons were performed in total.

The clinic regards the nasal symptom score and the airflow measurement as the two outcomes that
will drive prescribing. Their p-values were corrected by hand: each raw p-value was multiplied by
the number of comparisons performed (five) and capped at one, and the verdict for those two
outcomes was taken from the corrected value against the conventional five percent threshold. The
three remaining outcomes were judged on their raw p-values against the same threshold. The table
below states, for each outcome, which p-value the verdict rests on.

## Results

All five declared outcomes, in the declared order. Means are per arm.

| # | Outcome | Corticosteroid | Antihistamine | p used | Basis of p | Verdict at 0.05 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Total nasal symptom score (points) | 4.47 | 5.60 | 0.1216 | corrected (raw 0.0243 x 5) | Not significant |
| 2 | Peak nasal inspiratory flow (L/min) | 131.73 | 118.67 | 0.0121 | corrected (raw 0.0024 x 5) | Significant |
| 3 | Disturbed nights (nights/week) | 1.97 | 2.63 | 0.0685 | raw | Not significant |
| 4 | Total ocular symptom score (points) | 3.17 | 3.17 | 1.0000 | raw | Not significant |
| 5 | Rhinoconjunctivitis QoL total (points) | 2.24 | 2.52 | 0.1377 | raw | Not significant |

Outcome by outcome:

1. **Total nasal symptom score.** Corticosteroid 4.47 points (SD 1.74), antihistamine 5.60 points
   (SD 2.04), a difference of 1.13 points in favour of the corticosteroid. Raw p = 0.0243;
   corrected p = 0.1216. This is one of the two prescribing-relevant outcomes, so the verdict
   rests on the corrected value: not significant at five percent.
2. **Peak nasal inspiratory flow.** Corticosteroid 131.73 L/min (SD 16.47), antihistamine
   118.67 L/min (SD 15.43), a difference of 13.07 L/min in favour of the corticosteroid. Raw
   p = 0.0024; corrected p = 0.0121. Also prescribing-relevant, and it clears the five percent
   threshold after correction: significant.
3. **Disturbed nights.** Corticosteroid 1.97 nights (SD 1.19), antihistamine 2.63 nights
   (SD 1.56). Raw p = 0.0685, not significant at five percent.
4. **Total ocular symptom score.** Corticosteroid 3.17 points (SD 1.15), antihistamine 3.17
   points (SD 1.18). The arm means are equal to two decimal places. Raw p = 1.0000, not
   significant at five percent.
5. **Rhinoconjunctivitis quality of life total.** Corticosteroid 2.24 points (SD 0.72),
   antihistamine 2.52 points (SD 0.76). Raw p = 0.1377, not significant at five percent.

The clinic treated outcomes 1 and 2, the total nasal symptom score and the peak nasal inspiratory
flow, as the prescribing-relevant pair. Those are the two whose p-values were corrected for the
five comparisons. Outcomes 3 to 5 were read on their raw p-values.

## Conclusion

On these data the once-daily intranasal corticosteroid is the regimen to prescribe. It is the
only outcome pair member with a difference that survives the clinic's own multiplicity
correction: nasal airflow was 13.07 L/min higher on the corticosteroid, corrected p = 0.0121. The
nasal symptom score pointed the same way, 1.13 points lower on the corticosteroid, but its
corrected p of 0.1216 does not clear the five percent threshold, so that outcome should be read
as supportive direction rather than a demonstrated difference.

The two regimens looked alike on the ocular symptom score, where the arm means were identical at
3.17 points. Disturbed nights (1.97 versus 2.63, raw p = 0.0685) and quality of life (2.24 versus
2.52, raw p = 0.1377) both favoured the corticosteroid numerically without reaching the threshold.
Patients whose main complaint is eye symptoms have no evidence here for preferring one spray over
the other.

Two caveats for anyone acting on this. First, thirty patients per arm is a small service
evaluation, so the outcomes that fell short of the threshold are not evidence that the regimens
are equivalent, only that this sample could not separate them. Second, the correction was applied
to the two prescribing-relevant outcomes only, as the protocol directed, so the three raw p-values
in the table carry no multiplicity adjustment and should not be read as if they did.
