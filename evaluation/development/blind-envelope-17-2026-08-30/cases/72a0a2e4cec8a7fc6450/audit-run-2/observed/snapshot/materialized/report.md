# Levothyroxine tablet versus oral liquid: week-twelve results

## Question and formulations

Does switching from a standard levothyroxine tablet to an oral liquid
formulation, at an unchanged microgram dose, change thyroid control in adults
with primary hypothyroidism who were already on a stable tablet dose?

Sixty-four patients were randomised for twelve weeks: thirty-two continued on
the standard tablet (`tablet`) and thirty-two switched to the oral liquid
formulation (`liquid`). These two formulations are the only comparison in the
study. Bloods and the symptom questionnaire were taken at the week-twelve
visit.

## Data

File: `levothyroxine_formulation_trial.csv`. One row is one randomised patient,
holding that patient's week-twelve measurements. Each patient appears exactly
once; there are 64 data rows, thirty-two per group, with a value in every cell.

| Column | Description |
| --- | --- |
| `patient_id` | Patient identifier, `pt_01` through `pt_64`. |
| `group` | Formulation randomised to: `tablet` or `liquid`. |
| `tsh_miu_l` | Serum thyroid stimulating hormone at week twelve, milli-international units per litre. |
| `free_t4_pmol_l` | Serum free thyroxine at week twelve, picomoles per litre. |
| `total_cholesterol_mmol_l` | Total cholesterol at week twelve, millimoles per litre. |
| `symptom_score_0_40` | Hypothyroid symptom questionnaire score at week twelve, 0 to 40, higher meaning more symptoms. |

## How the comparison was done

The four outcomes above were declared in the trial protocol before
randomisation as one outcome family, in the order listed. Each outcome was
compared between the two formulations with a two-sample t-test. All four
p-values were then adjusted together, as one complete family of four, using the
Holm-Bonferroni procedure, which controls the family-wise error rate across the
whole declared family. Every verdict below is read from the adjusted p-value at
the conventional 0.05 threshold. Unadjusted p-values are shown for reference
only and no verdict is taken from them.

## Results

### 1. Serum thyroid stimulating hormone (`tsh_miu_l`)

Mean 3.131 on tablet, 2.099 on liquid (difference -1.032 mIU/L on liquid).
Unadjusted p = 0.0221; **adjusted p = 0.0883**. Verdict: not significant.

### 2. Serum free thyroxine (`free_t4_pmol_l`)

Mean 15.194 on tablet, 16.384 on liquid (difference +1.191 pmol/L on liquid).
Unadjusted p = 0.0240; **adjusted p = 0.0883**. Verdict: not significant.

### 3. Total cholesterol (`total_cholesterol_mmol_l`)

Mean 5.350 on tablet, 5.100 on liquid (difference -0.251 mmol/L on liquid).
Unadjusted p = 0.2168; **adjusted p = 0.2168**. Verdict: not significant.

### 4. Hypothyroid symptom score (`symptom_score_0_40`)

Mean 12.531 on tablet, 10.438 on liquid (difference -2.094 points on liquid).
Unadjusted p = 0.0603; **adjusted p = 0.1206**. Verdict: not significant.

## Sensitivity check

Patient `pt_60`, in the tablet group, had a week-twelve thyroid stimulating
hormone of 14.20 mIU/L, far above every other patient in the trial (the next
highest value is 5.00). The clinic reads this as likely missed doses in the
run-up to the visit rather than a formulation effect. The value is a real
recorded measurement and it stays in the main analysis above. As a single
robustness check, the thyroid stimulating hormone comparison was repeated once
with that one patient excluded: across the remaining 63 patients, mean 2.774 on
tablet (n = 31) and 2.099 on liquid (n = 32), difference -0.674 mIU/L,
p = 0.0119. This is a robustness check on the thyroid stimulating hormone
result and not an inferential result of its own: it was not adjusted, nothing
was re-adjusted or re-verdicted on the strength of it, and no other re-analysis
was run. The trial's conclusions rest on the adjusted family analysis reported
above.

## Conclusion

After adjusting all four declared outcomes together, none of the four reached
the 0.05 threshold. Free thyroxine and thyroid stimulating hormone both moved
in the direction expected of better absorption on the liquid, and the symptom
score was lower on the liquid, but once the error rate is controlled across the
whole declared family, this trial does not show that the oral liquid
formulation changes thyroid control relative to the standard tablet at an
unchanged microgram dose.
