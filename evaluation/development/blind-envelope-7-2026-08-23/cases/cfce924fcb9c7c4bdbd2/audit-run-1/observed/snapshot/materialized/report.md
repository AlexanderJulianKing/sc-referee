# Peripapillary RNFL thickness after one year on two topical drop regimens

## Design

Twenty-four patients with open-angle glaucoma were treated for one year with one of two topical
pressure-lowering drop regimens: timolol, the older regimen, or latanoprost, the newer one.
Twelve patients were allocated to each arm and stayed in that arm for the whole year. One eye per
patient was designated the study eye. At the final visit that eye was imaged by optical coherence
tomography, and peripapillary retinal nerve fibre layer (RNFL) thickness was reported for six
clock-hour sectors in micrometres. The outcome is RNFL thickness at that final visit.

## Data description

The single raw data file is `rnfl_sector_thickness.csv`: 144 data rows under one header line.

**One row is one clock-hour sector of one patient's study eye at the final visit.** It is not one
patient. Each patient appears on six rows, one per sector, and those six rows are repeated
measurements on the same eye.

| Column | Description |
| --- | --- |
| `patient_id` | Patient identifier, `pt_01` to `pt_24`. Repeated across that patient's six rows; this is the column that marks which rows come from the same eye. |
| `drop_regimen` | Treatment arm, either `timolol` (older) or `latanoprost` (newer). Constant within a patient. |
| `clock_hour_sector` | Which sector the value comes from: `temporal`, `superotemporal`, `superonasal`, `nasal`, `inferonasal`, `inferotemporal`. Each occurs once per patient. |
| `rnfl_thickness_um` | RNFL thickness for that sector of that eye, in micrometres, to one decimal place. The study outcome. |

There are no missing values, and every patient has a complete set of six sectors.

## Method

Sectors within one optic disc differ systematically, since the superior and inferior arcuate
bundles are thicker than the nasal and temporal ones, so the six values from a single eye are
correlated and cannot be treated as six independent observations. The unit that was allocated to a
regimen is the patient, so the patient is also the unit of analysis.

Each patient's six sector values were therefore averaged into **one mean RNFL thickness per
patient** before any comparison was made. The two regimens were then compared on those 24
per-patient values with a standard independent two-sample t-test assuming equal variances. The
sample size of that test is **12 patients in each arm**, not 72 sector rows per arm. Analysis was
carried out in `analysis.py` (Python, pandas and SciPy) directly from the committed CSV.

## Results

Per-patient mean RNFL thickness:

| Regimen | Patients | Mean (um) | SD (um) |
| --- | --- | --- | --- |
| timolol (older) | 12 | 79.13 | 5.84 |
| latanoprost (newer) | 12 | 82.64 | 8.46 |

The newer regimen was 3.51 um thicker on average (95% CI -2.65 to 9.67 um). The independent
two-sample t-test on the 12-versus-12 per-patient means gave **t(22) = 1.183, p = 0.249**.

## Interpretation

RNFL thickness at one year was about 3.5 um greater in the latanoprost arm, but the difference
did not reach statistical significance and the confidence interval spans zero, running from
roughly 2.7 um thinner to 9.7 um thicker on the newer regimen. The two regimens cannot be
separated on structural grounds here. The interval is wide enough that a clinically meaningful
advantage in either direction remains compatible with these data, so the result is inconclusive
rather than evidence of equivalence. With 12 patients per arm the study has limited power to
detect a difference of this size; a larger cohort, or a design using each eye's baseline
thickness as its own reference, would be needed to settle the question.
