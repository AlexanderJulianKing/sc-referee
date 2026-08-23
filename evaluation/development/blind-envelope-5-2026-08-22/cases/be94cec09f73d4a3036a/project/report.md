# Twelve-week probing depth: stannous fluoride versus conventional sodium fluoride paste

## Data description

The analysis uses one comma-separated file, `probing_depth.csv`: a header line plus 208 data rows.

**One row is one index tooth in one patient, measured at the twelve-week visit.** A row is not a
patient. Each patient was measured on eight index teeth, so **each patient appears on exactly eight
rows**, and those eight rows all carry the same patient code and the same paste arm.

The file has five columns, in this order.

| # | Column | Type | What it holds |
| --- | --- | --- | --- |
| 1 | `patient_code` | text | Anonymised trial code for the patient, e.g. `GNG-01-102`. Repeats on the eight rows for that patient. 26 distinct values. This is the cluster identifier and the independent unit. |
| 2 | `paste_arm` | text | The paste the patient was randomised to: `stannous_fluoride` or `sodium_fluoride`. Constant across a patient's eight rows, because whole people were randomised. |
| 3 | `tooth_site` | text | Which index tooth was measured, in FDI two-digit notation. The same eight teeth in every patient: 16, 12, 24, 26, 32, 36, 44, 46. |
| 4 | `bleeding_on_probing` | text | Whether that tooth bled when probed: `yes` or `no`. Measured per tooth, so it varies inside a mouth. |
| 5 | `probing_depth_mm` | number | Periodontal probing depth for that tooth, in millimetres, to one decimal. This is the outcome. |

No values are missing.

| Unit | Count |
| --- | --- |
| Patients (randomised units) | 26 |
| Patients per arm | 13 stannous, 13 sodium |
| Index teeth per patient | 8 |
| Rows (teeth) in the file | 208 (104 per arm) |

Observed depth ran from 2.1 to 3.6 mm in the stannous arm and 2.4 to 3.9 mm in the sodium arm.
Bleeding on probing was recorded on 39 of 104 stannous teeth (37.5%) and 36 of 104 sodium teeth
(34.6%).

| Arm | Patients | Teeth | Mean depth (mm) | SD across teeth | SD across patient means |
| --- | --- | --- | --- | --- | --- |
| `stannous_fluoride` | 13 | 104 | 2.857 | 0.396 | 0.362 |
| `sodium_fluoride` | 13 | 104 | 3.238 | 0.337 | 0.280 |

Most of the spread across teeth is spread across patients, not spread inside a mouth. That is why
the patient has to be the unit of analysis.

## Primary method and result

**Route taken: a resampling procedure written by hand in `analysis.py`.** It is not a clustered
routine from a statistics package. Each replicate draws whole patients with replacement, 13 from the
stannous arm and 13 from the sodium arm, carries all eight teeth of every drawn patient along with
that patient, and rebuilds the between-arm difference in mean probing depth. Because the patient is
what gets drawn, teeth from one mouth stay together and their shared behaviour is carried into the
uncertainty instead of being ignored. The script runs 20,000 replicates from a fixed random seed
(20260822), so the numbers reproduce exactly.

The 95% interval is the 2.5th and 97.5th percentiles of the replicate differences. The p-value is
two-sided: the replicate distribution is shifted so it sits on a difference of zero, and the p-value
is the share of shifted replicates at least as far from zero as the difference actually seen.

| Quantity | Value |
| --- | --- |
| Effect measure | Mean probing depth, stannous minus sodium |
| Point estimate | **-0.382 mm** |
| Bootstrap standard error | 0.122 mm |
| 95% percentile interval | **-0.615 mm to -0.139 mm** |
| Two-sided bootstrap p-value | **0.0017** |

Teeth in the stannous arm were about 0.38 mm shallower on average. The interval stays below zero
across its whole width, so the direction of the difference is consistent with the data at this
sample size.

## Illustrative contrast, not a valid basis for inference

A naive two-sample Welch t-test run on all 208 teeth as if each tooth were its own subject gives:

| Quantity | Value |
| --- | --- |
| Point estimate | -0.382 mm |
| Naive standard error | 0.051 mm |
| Naive 95% CI | -0.482 mm to -0.281 mm |
| Test statistic | t = -7.490, df = 201.0 |
| p-value | 2.13e-12 |

**This tooth-level test is not a valid basis for inference.** It treats the eight teeth from the same
patient as eight independent observations, and they are not independent: they sit in one mouth and
share that person's plaque control and smoking, so they move up and down together. The test counts
the sample as 208 teeth when only 26 patients were randomised. That inflated count shrinks the
standard error and the p-value and makes the finding look far more certain than the design can
support. The honest patient-clustered standard error is 2.39 times the naive one, and the naive
p-value is smaller by about nine orders of magnitude. The tooth-level numbers appear here only as a
contrast with the patient-clustered result above, and no conclusion rests on them.

Note that both routes give the same point estimate of -0.382 mm. The clustering problem is a problem
about uncertainty, not about the size of the effect: ignoring it does not move the estimate, it only
makes the error bar around the estimate far too narrow.

## Clinical interpretation

Across 26 randomised patients and 208 index teeth, twelve weeks of the stannous fluoride paste left
probing depths about 0.4 mm shallower than the conventional sodium fluoride paste, with a
patient-clustered 95% interval running from roughly 0.6 mm to 0.1 mm shallower. In patients with mild
chronic gingivitis, whose depths sit in the 2 to 4 mm range, a shift of this size is a modest but
real improvement in the direction clinicians want, and it points toward less inflammation rather than
toward established periodontal attachment loss.

Two limits are worth stating plainly. First, the lower end of the interval is only about 0.1 mm, a
difference too small to matter at a single tooth, so the study establishes the direction of the
effect more firmly than its exact magnitude. Second, 26 patients is a small trial, this analysis
covers one twelve-week visit with no baseline adjustment, and bleeding on probing was similar in the
two arms (37.5% versus 34.6% of teeth), so the depth result is not backed here by a matching
difference in bleeding. A larger trial, with baseline depths and a longer follow-up, would be needed
before treating this as a settled clinical advantage.
