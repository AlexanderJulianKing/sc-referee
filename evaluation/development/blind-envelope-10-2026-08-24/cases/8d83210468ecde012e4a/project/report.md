# Winter wheat fungicide programme trial: two-stage report

## Data description

The analysis reads one file, `wheat_fungicide_trial.csv`. **One row is one individually tagged wheat
plant**: the programme it received, the study half it was allocated to before any measurement, and
its six end-of-season measurements. The file holds 144 data rows and no empty cells.

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `plant_id` | text | — | Field tag of the plant, `WW-001` to `WW-144`, unique |
| `program_group` | text | — | Fungicide programme, exactly two values: `single_spray` (one spray at flag leaf emergence) and `two_spray` (an added earlier stem extension spray), 72 plants each |
| `stage_split` | text | — | Pre-assigned study half, exactly two values: `discovery` and `validation`, 72 plants each, with 36 plants from each programme inside each half |
| `grain_yield_g` | number | g per plant | Grain harvested from that plant |
| `tgw_g` | number | g | Thousand grain weight for that plant's grain sample |
| `septoria_severity_pct` | number | % leaf area | Septoria tritici blotch severity on that plant's flag leaf |
| `green_canopy_days` | number | days | Green canopy duration for that plant |
| `plant_height_cm` | number | cm | Height of that plant at maturity |
| `spike_count` | integer | count | Number of fertile spikes on that plant |

## Design

The protocol declared six outcomes in advance, in the order listed above, each measured once per
plant. It also fixed the split into a discovery half and a validation half before any measurement was
taken, and that allocation is recorded in the `stage_split` column rather than being drawn during the
analysis.

The study runs in two stages.

* **Stage 1, screening.** In the discovery half only, the two programmes are compared on each of the
  six outcomes with a two-sided Student two-sample t test for independent samples (36 plants per
  programme, 70 degrees of freedom). An outcome screens through at p < 0.05.
* **Stage 2, confirmation.** In the validation half only, only the screened-through outcomes are
  tested again, with the same test on the untouched 72 validation plants. Each is judged against a
  Bonferroni-adjusted level, that is, the 0.05 family budget split evenly across the outcomes carried
  forward, so the chance of any false confirmation across the whole confirmatory stage stays at 0.05.

Outcomes that do not screen through are never re-tested and get no confirmatory verdict. Every
scientific conclusion below rests on the validation stage.

All figures are produced by `analysis.py`; differences are reported as two-spray minus single-spray.

## Descriptive statistics

Mean +/- standard deviation, 36 plants per programme in each cell.

| Outcome | Discovery, single_spray | Discovery, two_spray | Validation, single_spray | Validation, two_spray |
| --- | --- | --- | --- | --- |
| Grain yield (g/plant) | 14.77 +/- 3.30 | 17.80 +/- 3.29 | 14.46 +/- 2.63 | 17.76 +/- 2.93 |
| Thousand grain weight (g) | 41.01 +/- 2.18 | 43.31 +/- 2.66 | 41.84 +/- 2.18 | 43.36 +/- 2.16 |
| Septoria severity (% leaf area) | 28.46 +/- 9.04 | 13.86 +/- 8.11 | 26.01 +/- 9.76 | 16.52 +/- 7.09 |
| Green canopy duration (days) | 28.14 +/- 4.11 | 33.59 +/- 4.15 | 29.27 +/- 3.69 | 32.63 +/- 3.97 |
| Plant height (cm) | 82.02 +/- 6.15 | 82.21 +/- 5.37 | 81.84 +/- 5.78 | 82.87 +/- 6.91 |
| Fertile spikes (count) | 4.47 +/- 1.13 | 4.67 +/- 1.01 | 4.67 +/- 0.99 | 4.97 +/- 1.16 |

## Stage 1: discovery screening (alpha = 0.05)

| Outcome | Difference | t (df = 70) | p | Verdict |
| --- | --- | --- | --- | --- |
| Grain yield (g/plant) | +3.031 | 3.903 | 0.00022 | screens through |
| Thousand grain weight (g) | +2.303 | 4.022 | 0.00014 | screens through |
| Septoria severity (% leaf area) | -14.600 | -7.212 | 5.1e-10 | screens through |
| Green canopy duration (days) | +5.453 | 5.602 | 3.9e-07 | screens through |
| Plant height (cm) | +0.189 | 0.139 | 0.89 | not carried forward |
| Fertile spikes (count) | +0.194 | 0.767 | 0.45 | not carried forward |

Four outcomes screen through: grain yield, thousand grain weight, septoria severity and green canopy
duration. Plant height and fertile spike count do not, so they stop here. They are not re-tested in
the validation half and they carry no confirmatory verdict; the discovery numbers above are all that
can be said about them.

## Stage 2: validation of the carried-forward outcomes

Four outcomes were carried forward, so k = 4 and the adjusted level actually used is

    alpha = 0.05 / 4 = 0.0125

which is the family budget of 0.05 divided evenly among the four confirmatory tests.

| Outcome | Difference | t (df = 70) | p | Verdict at alpha = 0.0125 |
| --- | --- | --- | --- | --- |
| Grain yield (g/plant) | +3.307 | 5.040 | 3.5e-06 | confirmed |
| Thousand grain weight (g) | +1.511 | 2.958 | 0.0042 | confirmed |
| Septoria severity (% leaf area) | -9.486 | -4.716 | 1.2e-05 | confirmed |
| Green canopy duration (days) | +3.361 | 3.723 | 0.00039 | confirmed |

All four clear the adjusted level in the independent validation half. Thousand grain weight is the
closest call: its p of 0.0042 clears 0.0125 but would not have cleared a stricter budget.

## Conclusion

On the validation half, adding the earlier stem extension spray pays off. Plants on the two-spray
programme carried 9.486 percentage points less septoria on the flag leaf, held a green canopy 3.361
days longer, and returned 3.307 g more grain per plant with individual grains 1.511 g heavier per
thousand, every one of those differences confirmed at the adjusted 0.0125 level. The chain is
consistent: less disease, a canopy that stays green longer, and more grain filled.

Two things this trial does not show. Plant height and fertile spike count never screened through, so
the second spray has no demonstrated effect on plant structure, and the yield gain appears to come
through disease control and grain filling rather than through more spikes. And the result is one site
in one season with no cost figures attached, so whether the extra spray pays off financially depends
on grain price and application cost, which this analysis does not address.
