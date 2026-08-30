# Eel contaminant and condition survey: two catchments

## Data

`eel_catchment_survey.csv` holds one row per individual European eel. Each eel was
caught and sampled once, and every eel was measured for every outcome. There are
80 rows and no missing values.

| Column | Meaning |
|---|---|
| `eel_id` | Per-eel identifier, `EEL001` to `EEL080`. |
| `catchment` | Group column, two values: `impacted` (40 eels) and `reference` (40 eels). |
| `stage` | Pre-assigned analysis stage, two values: `discovery` and `validation`, 20 and 20 within each catchment. |
| `hg_mg_kg` | Muscle total mercury, mg/kg wet weight. |
| `pcb6_ug_kg` | Sum of the six indicator PCBs in muscle, ug/kg wet weight. |
| `erod_pmol_min_mg` | Liver EROD activity, pmol/min/mg protein. |
| `fulton_k` | Fulton condition factor, dimensionless. |
| `hsi_pct` | Hepatosomatic index, percent of body mass. |
| `lipid_pct` | Muscle lipid content, percent of wet mass. |

The last six columns are the six pre-declared outcome variables, stored in the
order in which the survey declared them.

## Methods

Each eel was assigned to the discovery stage or the validation stage before any
measurement was made, 20 eels per stage in each catchment. The two stages are
therefore disjoint sets of eels, 40 in discovery and 40 in validation.

Catchments are compared with Welch's two-sample t-test (unequal-variance
two-sample t-test) throughout.

The discovery stage screens all six declared outcomes at a liberal level of
p < 0.05. It is a screen only and makes no claim.

The validation stage re-tests only the outcomes that survived the screen, in the
validation eels alone, against a level adjusted for the number of outcomes
carried forward: 0.05 divided by that number. Three outcomes were carried
forward, so the adjusted validation level is 0.05 / 3 = 0.016667.

## Results

### Discovery screen (20 impacted, 20 reference; screening only)

| Outcome | Impacted mean | Reference mean | t | p | Screen |
|---|---|---|---|---|---|
| `hg_mg_kg` | 0.4284 | 0.1759 | 5.130 | 2.555e-05 | survives |
| `pcb6_ug_kg` | 96.380 | 29.705 | 5.713 | 8.848e-06 | survives |
| `erod_pmol_min_mg` | 34.800 | 18.585 | 6.002 | 1.569e-06 | survives |
| `fulton_k` | 0.1592 | 0.1651 | -1.074 | 0.2895 | screened out |
| `hsi_pct` | 1.2890 | 1.3265 | -0.492 | 0.6255 | screened out |
| `lipid_pct` | 17.675 | 18.180 | -0.479 | 0.6349 | screened out |

Three of the six outcomes survive to confirmation: `hg_mg_kg`, `pcb6_ug_kg` and
`erod_pmol_min_mg`. The three condition outcomes are not carried forward, so no
verdict is reached on them.

### Validation (20 impacted, 20 reference; adjusted level 0.016667)

| Outcome | Impacted mean (SD) | Reference mean (SD) | t | p | Verdict |
|---|---|---|---|---|---|
| `hg_mg_kg` | 0.4070 (0.1786) | 0.1851 (0.0871) | 4.994 | 2.935e-05 | confirmed |
| `pcb6_ug_kg` | 91.200 (45.446) | 32.020 (21.087) | 5.283 | 1.455e-05 | confirmed |
| `erod_pmol_min_mg` | 33.110 (9.864) | 19.355 (5.247) | 5.506 | 6.261e-06 | confirmed |

All three outcomes carried into validation clear the adjusted level of 0.016667.

## Interpretation

Read only from the validation stage, and for catchment management:

Eels from the industrially impacted catchment carry more contaminant burden than
eels from the rural reference catchment. Validation-stage muscle mercury averages
0.407 mg/kg wet weight in the impacted catchment against 0.185 mg/kg in the
reference catchment, a little over twice as high. The sum of the six indicator
PCBs averages 91.2 ug/kg against 32.0 ug/kg, close to three times as high. Liver
EROD activity, a biomarker of exposure to inducing organic contaminants, averages
33.1 pmol/min/mg protein against 19.4, about 1.7 times as high. The raised EROD
activity is consistent with the raised tissue burdens rather than a separate
finding.

Fish-to-fish scatter is wide in both catchments, so individual eels overlap even
where the catchment averages are far apart. Management measures should be set on
the catchment averages, not on single fish.

No verdict is offered on eel condition. Fulton condition factor, hepatosomatic
index and muscle lipid content did not pass the discovery screen and so were not
carried into validation. That is not evidence that the catchments have equal
condition; it means this survey stopped short of testing those three outcomes at
the confirmatory stage.
