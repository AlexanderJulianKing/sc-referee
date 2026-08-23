# Data description

## File

`probing_depth.csv` — one comma-separated file, 209 lines: one header line plus 208 data rows.

## What one row is

**One row is one index tooth in one patient, measured at the twelve-week visit.**

Each patient was measured on eight index teeth, so **each patient appears on exactly eight rows**.
The rows for a patient are consecutive and always run through the eight teeth in the same order.
Teeth on the same patient's rows are not independent observations: they come from one mouth, and
that mouth's plaque control and smoking push all eight of its teeth up or down together.

## Units and counts

| Unit | Count |
| --- | --- |
| Patients (randomised units) | 26 |
| Patients per arm | 13 and 13 |
| Index teeth per patient | 8 |
| Data rows (teeth) | 208 |

## The two groups

Patients were randomised as whole people. The arm is a property of the patient, not of the tooth,
so all eight rows for a patient carry the same arm label.

| `paste_arm` value | Meaning | Patients | Rows |
| --- | --- | --- | --- |
| `stannous_fluoride` | Stannous fluoride paste | 13 | 104 |
| `sodium_fluoride` | Conventional sodium fluoride paste | 13 | 104 |

## Columns

Columns appear in this order.

| # | Column | Type | Description |
| --- | --- | --- | --- |
| 1 | `patient_code` | text | Anonymised trial code for the patient, in the form `GNG-SS-NNN`, where `SS` is a two-digit study site (`01`, `02`, `03`) and `NNN` is a three-digit subject number. Repeats on the eight rows belonging to that patient. 26 distinct values. This is the cluster identifier. |
| 2 | `paste_arm` | text | Which paste the patient was randomised to. Exactly two values: `stannous_fluoride` or `sodium_fluoride`. Constant within a patient. |
| 3 | `tooth_site` | text | Which index tooth was measured, in FDI two-digit notation (first digit = quadrant, second = tooth position). The same eight teeth in every patient: `16`, `12`, `24`, `26`, `32`, `36`, `44`, `46`. Two teeth per quadrant. |
| 4 | `bleeding_on_probing` | text | Whether that tooth bled when probed. Exactly two values: `yes` or `no`. Recorded per tooth, so it varies within a patient. 75 of 208 teeth are `yes` (39 of 104 in the stannous arm, 36 of 104 in the sodium arm). |
| 5 | `probing_depth_mm` | number | Periodontal probing depth for that tooth in millimetres, rounded to one decimal. This is the outcome. Observed range 2.4 to 3.9 in the sodium fluoride arm and 2.1 to 3.6 in the stannous fluoride arm. |

No cell is blank; there are no missing values.

## How the file was made

`make_data.py` in this directory generates the file. It uses only the Python standard library and a
fixed random seed (`20260822`), so re-running it reproduces the same file exactly.

Depth for a tooth is built as an arm mean, plus a patient offset drawn once per patient, plus
tooth-level noise drawn once per tooth, then clipped to the plausible clinical range for that arm and
rounded to one decimal. The patient offset is the part that stands in for plaque control and smoking:
because it is shared by all eight of a patient's teeth, the teeth inside one mouth are correlated,
and the patient, not the tooth, is the independent unit. Bleeding on probing is then drawn per tooth
with a probability that rises with that tooth's depth.
