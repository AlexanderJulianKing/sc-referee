# Pre-dialysis serum phosphate on two oral binder regimens

*Prepared by the study nephrologist, outpatient haemodialysis unit.*

## Design

Eighteen adults on thrice-weekly maintenance haemodialysis were assigned to one of two
oral phosphate-binder regimens: calcium acetate, the established binder, or sucroferric
oxyhydroxide, the newer binder. Nine patients received each regimen and stayed on it
throughout. Blood was drawn immediately before the mid-week dialysis session on eight
consecutive weeks, giving eight pre-dialysis serum phosphate results per patient and 144
results in total. No samples were missing.

## Data description

The study data sit in one plain-text comma-separated file, `phosphate_data.csv`, with a
header line and 144 data lines.

**One row is one patient at one mid-week study session** — the pre-dialysis serum
phosphate result for that patient in that study week.

| Column | Type | What it holds |
| --- | --- | --- |
| `patient_id` | text | Study identifier for the patient, `HD-01` through `HD-18`. |
| `binder_regimen` | text | The oral phosphate binder the patient was on: `calcium_acetate` (established) or `sucroferric_oxyhydroxide` (newer). |
| `study_week` | integer | The study week the sample came from, 1 to 8, counted consecutively from the start of observation. |
| `serum_phosphate_mmol_l` | number | Pre-dialysis serum phosphate concentration in millimoles per litre, reported to two decimal places as the hospital laboratory issues it. |

All 144 values lie between 0.97 and 2.48 mmol/L, within the range seen routinely in a
dialysis population.

## Method

The two regimens were compared with a standard independent two-sample t-test on the
difference in mean pre-dialysis serum phosphate. Every blood sample in the table entered
the test as one observation, so the sample size is the total number of samples analysed
in each arm: 72 on the established binder and 72 on the newer binder. Group means and
standard deviations were computed on the same basis. The analysis is carried out by
`analysis.py`, which reads the committed CSV directly; the file is the data of record and
is not regenerated at analysis time.

## Result

| Regimen | Samples | Mean phosphate (mmol/L) | SD (mmol/L) |
| --- | --- | --- | --- |
| Calcium acetate (established) | 72 | 1.876 | 0.293 |
| Sucroferric oxyhydroxide (newer) | 72 | 1.551 | 0.302 |

Mean pre-dialysis serum phosphate was 0.325 mmol/L lower on the newer binder. The
independent two-sample t-test gave t(142) = 6.554, p = 9.6 x 10^-10.

## Interpretation

Across 144 mid-week samples, patients taking sucroferric oxyhydroxide ran a mean
pre-dialysis serum phosphate of 1.55 mmol/L against 1.88 mmol/L on calcium acetate, a
difference of 0.33 mmol/L that is highly significant on the two-sample test. A shift of
that size matters at the bedside: it moves an average patient from above the usual
1.78 mmol/L (5.5 mg/dL) target ceiling to comfortably below it, which is the difference
between chasing control with dose escalation and holding a steady regimen. The spread of
values was similar in the two arms, around 0.30 mmol/L, so the newer binder lowered the
level without making phosphate control more erratic. These results support a
phosphate-lowering effect of sucroferric oxyhydroxide relative to calcium acetate in this
outpatient dialysis population, and support offering it to patients whose phosphate stays
above target on the established binder.
