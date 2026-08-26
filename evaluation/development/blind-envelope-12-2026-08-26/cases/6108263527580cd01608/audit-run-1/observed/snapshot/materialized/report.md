# Baseline blood markers and six-month response in early rheumatoid arthritis

A two-stage split-sample study of six protocol-declared baseline markers.

## Summary

Fifty-six patients with early rheumatoid arthritis had a baseline blood sample stored before
first-line therapy began and were classified six months later, by the treating clinician and
blinded to the assays, as responders (29) or non-responders (27). Six baseline markers were
declared in the protocol. Screening in the pre-assigned discovery half carried three markers
forward: C-reactive protein, erythrocyte sedimentation rate and serum calprotectin. In the
validation half, tested at a Bonferroni-adjusted level of 0.0167 (0.05 over the three markers
carried forward), none of the three separated responders from non-responders. **No baseline
marker is confirmed by this study.**

## Data description

The analysis input is `ra_baseline_markers.csv`: 56 data rows plus one header row, comma
separated, UTF-8, with no missing cells.

**One row represents one patient.** Each row is a single stored baseline blood sample drawn
before first-line therapy started, together with that patient's six-month response status and
the half of the split-sample design the patient was allocated to. Each patient appears exactly
once, so the 56 rows are 56 patients, and the patient is the unit of analysis.

Columns, in file order:

| # | Column | Unit | What it holds |
| --- | --- | --- | --- |
| 1 | `patient_id` | none | Patient identifier, `RA-001` through `RA-056`, unique across the file. |
| 2 | `group` | none | Six-month response status assigned by the treating clinician, blinded to the assays. Exactly two entries: `responder` (29 patients) and `non_responder` (27 patients). |
| 3 | `stage` | none | The half of the split-sample design the patient was allocated to. Exactly two entries: `discovery` (28 patients) and `validation` (28 patients). |
| 4 | `crp_mg_l` | mg/L | Baseline C-reactive protein. |
| 5 | `esr_mm_h` | mm/h | Baseline erythrocyte sedimentation rate. |
| 6 | `anti_ccp_u_ml` | U/mL | Baseline anti-cyclic citrullinated peptide antibody. |
| 7 | `rf_iu_ml` | IU/mL | Baseline rheumatoid factor. |
| 8 | `calprotectin_ng_ml` | ng/mL | Baseline serum calprotectin. |
| 9 | `vitd_nmol_l` | nmol/L | Baseline serum 25-hydroxyvitamin D. |

Columns 4 through 9 are the six protocol-declared markers, written in the declared protocol
order. Every patient has a value in every marker column.

## Design

The cohort was split into two halves of equal size by a fixed random allocation. That allocation
was recorded in the study database **before any assay was run**, and it was fixed for the whole
analysis; it is carried in the CSV as the `stage` column. Both halves contain responders and
non-responders in similar proportion:

| Half | Patients | Responders | Non-responders |
| --- | --- | --- | --- |
| Discovery | 28 | 15 | 13 |
| Validation | 28 | 14 | 14 |

The analysis runs in two stages, in order. Stage one screens all six markers using the discovery
half only. Stage two re-tests the surviving markers using the validation half only. The
validation half contributed nothing to the choice of markers carried forward.

Each marker comparison is a two-sided Welch two-sample t-test of responders against
non-responders on that marker.

## Stage one: screening (discovery half only)

The screening threshold was stated in advance: an unadjusted p-value below 0.10. No multiplicity
adjustment is applied at this stage. These results are screening output only. They are not a
claim that any marker separates the two groups; they decide only what is carried into
confirmation.

Discovery half, n = 28 (15 responders, 13 non-responders), mean (SD):

| Marker | Responders | Non-responders | p | Outcome |
| --- | --- | --- | --- | --- |
| C-reactive protein (mg/L) | 14.0 (11.1) | 27.4 (13.3) | 0.0084 | carried forward |
| Erythrocyte sedimentation rate (mm/h) | 27.4 (8.5) | 40.8 (17.0) | 0.0193 | carried forward |
| Anti-CCP antibody (U/mL) | 32.0 (23.3) | 60.4 (71.3) | 0.1911 | dropped |
| Rheumatoid factor (IU/mL) | 48.9 (28.6) | 63.4 (58.6) | 0.4283 | dropped |
| Serum calprotectin (ng/mL) | 1834.1 (560.3) | 3472.0 (1589.4) | 0.0031 | carried forward |
| Serum 25-hydroxyvitamin D (nmol/L) | 63.0 (16.2) | 53.9 (16.2) | 0.1510 | dropped |

Three markers met the screening threshold and were carried into confirmation: C-reactive
protein, erythrocyte sedimentation rate and serum calprotectin.

## Stage two: confirmation (validation half only)

The three surviving markers were re-tested in the validation half alone. Three confirmatory tests
were run, so the level was Bonferroni-adjusted to 0.05 / 3 = 0.0167, which holds the family-wise
error rate across the confirmatory tests at the conventional five percent. A marker counts as
confirmed only if its validation p-value falls below 0.0167.

Validation half, n = 28 (14 responders, 14 non-responders), mean (SD):

| Marker | Responders | Non-responders | p | Passes at 0.0167? |
| --- | --- | --- | --- | --- |
| C-reactive protein (mg/L) | 19.8 (10.8) | 21.8 (7.7) | 0.5790 | no |
| Erythrocyte sedimentation rate (mm/h) | 25.9 (9.8) | 35.8 (15.3) | 0.0545 | no |
| Serum calprotectin (ng/mL) | 2356.4 (1167.2) | 2973.3 (1023.6) | 0.1493 | no |

## Conclusion

The conclusion rests entirely on the validation stage. The adjusted level used there was 0.0167,
Bonferroni over the three markers carried into validation.

None of the three markers passed. **No baseline marker in this study separates six-month
responders from non-responders.** The large discovery-half differences in C-reactive protein and
serum calprotectin did not reproduce in the validation half, which is the pattern a split-sample
design exists to expose. Erythrocyte sedimentation rate came closest (validation p = 0.0545), but
it does not pass at the adjusted level and is reported here as not confirmed, not as borderline
evidence.

The three markers dropped at screening (anti-CCP, rheumatoid factor and 25-hydroxyvitamin D) were
never tested in the validation half. This study says nothing about them either way.

## Limitations

Twenty-eight patients per half is a small confirmatory sample, so the study has limited power to
confirm a marker with a modest effect. A negative result at this size does not rule out a real
but small difference. The screening threshold of 0.10 and the Bonferroni adjustment were both
fixed in advance, and no marker, threshold or subgroup was changed after the validation results
were seen.

## Reproducing the analysis

From the project root:

```
python analysis.py
```

The script reads `ra_baseline_markers.csv`, prints the cohort summary, then the screening stage
and the confirmation stage as separate sections. It requires `pandas` and `scipy`.
