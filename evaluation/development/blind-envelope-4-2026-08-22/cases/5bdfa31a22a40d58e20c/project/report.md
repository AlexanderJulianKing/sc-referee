# Sedation protocol and oxygenation in ventilated adults with moderate respiratory failure

## Question

In mechanically ventilated adults with moderate respiratory failure, does the ratio of arterial
oxygen tension to inspired oxygen fraction (PaO2/FiO2, mmHg) differ between a light sedation
protocol and a deep sedation protocol?

## Data

Twenty-four adults in a single-centre intensive care unit were managed under one of two sedation
protocols, twelve under light sedation and twelve under deep sedation. Each patient contributed
six arterial blood gases, drawn at enrolment and at 6, 12, 24, 36 and 48 hours. That gives 144
blood gas measurements, 72 in each arm, with no missing values. The data are synthetic and were
generated for this project; no real patient data were used.

The measurements are held in `sedation_abg.csv`.

**One row is one arterial blood gas measurement taken on one patient at one scheduled time
point.**

The file has four columns, in this order:

| # | Column | Type | Values | Meaning |
|---|--------|------|--------|---------|
| 1 | `PatientID` | text | `ICU-01` … `ICU-24` | Identifier of the patient the blood gas was taken on. |
| 2 | `SedationArm` | text, 2 levels | `light`, `deep` | The sedation protocol the patient was managed under. |
| 3 | `HoursFromEnrolment` | integer | 0, 6, 12, 24, 36, 48 | Hours between enrolment and this blood gas; `0` is the enrolment measurement. |
| 4 | `PFRatio` | integer | 114–339 mmHg observed | PaO2/FiO2 for this blood gas, in mmHg. |

Observed PFRatio values run from 114 to 339 mmHg, which sits inside the clinically believable
range for this population.

## Analysis

The two arms were compared with an independent two-sample t-test of `PFRatio`, assuming equal
variances, run over every row in the table. Each arterial blood gas result is an observation
contributing to the sample size, so the analysis is based on N = 144 measurements. The analysis
is in `analysis.py` and is reproduced with `python3 analysis.py`.

## Results

| Arm | N measurements | Mean PFRatio (mmHg) | SD (mmHg) |
|-----|----------------|---------------------|-----------|
| Light sedation | 72 | 243.8 | 51.9 |
| Deep sedation | 72 | 214.9 | 39.2 |

Mean PFRatio was 243.8 mmHg under light sedation and 214.9 mmHg under deep sedation. The
difference, light minus deep, is 28.8 mmHg in favour of light sedation.

The test statistic is t(142) = 3.76, with p = 0.00025.

Mean PFRatio by time point:

| Hours from enrolment | Light (mmHg) | Deep (mmHg) |
|----------------------|--------------|-------------|
| 0  | 227.3 | 216.7 |
| 6  | 231.9 | 217.1 |
| 12 | 243.0 | 208.8 |
| 24 | 251.4 | 220.2 |
| 36 | 252.9 | 206.4 |
| 48 | 255.9 | 220.4 |

The light arm is above the deep arm at every one of the six scheduled time points.

## Conclusion

Light sedation is associated with better oxygenation. Across 144 arterial blood gases, PaO2/FiO2
was 28.8 mmHg higher under the light sedation protocol than under the deep sedation protocol,
and the difference is significant at the conventional 5% level (p = 0.00025). A gain of roughly
29 mmHg in PaO2/FiO2 is clinically meaningful in ventilated patients with moderate respiratory
failure. These data support light sedation as the preferred protocol in this population.
