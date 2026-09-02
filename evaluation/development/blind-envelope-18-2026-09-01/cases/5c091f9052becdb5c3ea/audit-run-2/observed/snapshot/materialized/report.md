# Spray versus wipes: occupational health monitoring of hospital cleaners

## What was compared and why

An occupational health service wanted to know whether the way a disinfectant is applied changes
what hospital cleaning staff breathe in and how they feel at the end of a shift. Fifty-eight
cleaners on general wards took part. Twenty-nine worked their shift using a trigger-spray
application and twenty-nine used pre-soaked wipes, at the same product concentration. The same
occupational hygiene team measured each worker once, at the end of one monitored shift. The
monitoring plan declared five outcomes in advance, and all five are reported here.

## The data

`data.csv` holds one row per cleaning worker, 58 rows plus a header. Its columns are:

- `worker_id`: anonymous worker identifier, `W001` to `W058`.
- `application_method`: the method used during the shift, either `trigger_spray` or `pre_soaked_wipes`.
- `fev1_l`: forced expiratory volume in one second, in litres.
- `feno_ppb`: fractional exhaled nitric oxide, in parts per billion.
- `airway_symptom_score`: airway symptom questionnaire score on a 0 to 20 scale, higher meaning more symptoms.
- `peak_tvoc_mg_m3`: peak airborne total volatile organic compounds measured on the worker, in milligrams per cubic metre.
- `eye_skin_irritation_score`: eye and skin irritation on a 0 to 10 scale, higher meaning more irritation.

## What the analysis did

`analysis.py` reads `data.csv` and compares the two application methods on each declared outcome
with a two-sample t-test that does not assume the two groups have equal spread. Because five
outcomes were declared, testing them one at a time would give five separate chances to see a
difference that is not really there, so the script reaches no verdict at that stage. It collects all
five raw p-values, then passes them together, in one step, through the multiple-comparisons
adjustment routine in statsmodels with no correction method named, taking whatever adjustment that
routine applies by default. All five declared outcomes are adjusted together as a single family.
Every verdict rests on the adjusted value, judged against the usual 0.05 threshold. No outcome is
judged on its raw p-value.

## Conclusions, in the declared order

1. **Lung function (`fev1_l`)**: no difference. Spray 3.363 L (SD 0.445), wipes 3.380 L (SD 0.358); adjusted value 0.871.
2. **Exhaled nitric oxide (`feno_ppb`)**: no difference. Spray 20.572 ppb (SD 9.449), wipes 18.400 ppb (SD 7.103); adjusted value 0.547.
3. **Airway symptom score**: the spray group scored higher, and the gap holds after adjustment. Spray 8.069 (SD 2.203), wipes 3.172 (SD 2.377); adjusted value 1.9e-10.
4. **Peak airborne TVOC (`peak_tvoc_mg_m3`)**: the spray group was exposed to more, and the gap holds after adjustment. Spray 2.384 mg/m3 (SD 0.633), wipes 0.833 mg/m3 (SD 0.324); adjusted value 4.2e-14.
5. **Eye and skin irritation score**: no difference. Spray 2.793 (SD 1.236), wipes 3.483 (SD 1.479); raw p-value 0.059, adjusted value 0.167.

Each group had 29 workers for every outcome, with no missing values.
