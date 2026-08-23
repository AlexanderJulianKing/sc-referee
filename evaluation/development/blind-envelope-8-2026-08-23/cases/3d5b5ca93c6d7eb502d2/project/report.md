# Evolved fitness cost of selection under an efflux-pump inhibitor

## Study

Sixteen independent lineages of a bacterial pathogen were propagated for thirty days. Eight
evolved in medium containing a sub-inhibitory efflux-pump inhibitor and eight evolved in plain
medium. At the end of the experiment each evolved lineage was assayed for maximum growth rate.
The assay was run six times on the same frozen stock of each lineage on the same plate reader,
giving 96 assay runs in total.

## Data description

The project holds one data file, `growth_rates.csv`, with a header row and 96 data rows.

**One row is one assay run of one evolved lineage:** a single measurement of maximum growth rate
taken from that lineage's frozen stock in one well of one plate-reader run.

| Column | Type | Units | Description |
|---|---|---|---|
| `lineage_id` | text | — | Identifier of the evolved lineage the assayed stock came from. Values `LIN01` through `LIN16`, each appearing in 6 rows. |
| `selection_regime` | text | — | The arm of the evolution experiment the lineage was propagated in: `inhibitor` or `plain`. Constant within a lineage. |
| `replicate_run` | integer | — | Which of that lineage's six assay runs the row is, numbered 1 to 6. Numbering restarts at 1 for each lineage. |
| `growth_rate_per_h` | number | per hour (h⁻¹) | Maximum growth rate measured in the assay run, taken from the steepest part of the growth curve. Values in the file run 0.4446 to 0.8165. |
| `plate_id` | text | — | Identifier of the assay plate the run was read on: `PLT01` or `PLT02`. |
| `well` | text | — | Well position on that plate, a row letter A–D plus a zero-padded column number 01–12, for example `C07`. Unique within a plate; the layout was randomised. |
| `final_od600` | number | OD units at 600 nm | Optical density at 600 nm at the end of the run, that is, the plateau of the growth curve. Values in the file run 0.779 to 1.093. |

Counts: 16 lineages x 6 assay runs = 96 rows. `LIN01`–`LIN08` are the inhibitor-evolved lineages
(48 rows) and `LIN09`–`LIN16` the plain-medium lineages (48 rows). The 96 runs occupy 96 distinct
wells across 2 plates, 48 wells per plate, with all six runs of a given lineage on one plate. Each
plate carries four inhibitor-evolved and four plain-medium lineages, so plate does not track
selection regime.

These are simulated values, invented to match the study design and the growth-rate ranges in the
study brief. They are not measurements from a real laboratory experiment.

## Methods

Maximum growth rate was compared between the two selection regimes with an independent two-sample
t-test in Welch's form, which does not assume the two regimes share a variance. Every assay run in
the table entered the comparison as one observation, so the sample size is the total number of rows,
48 per regime and 96 overall. The reported effect is the difference in mean growth rate,
inhibitor minus plain, with a 95% confidence interval from the same Welch standard error, and
Cohen's *d* computed on the pooled standard deviation.

The analysis was run with Python 3, pandas 2.0.3 and SciPy 1.9.1, using
`scipy.stats.ttest_ind(..., equal_var=False)`. The script is `analysis.py` at the project root and
reads `growth_rates.csv` directly; running it reproduces every number below.

## Results

Growth rate by selection regime, over all 96 assay runs:

| Regime | n | Mean (h⁻¹) | SD (h⁻¹) | SEM (h⁻¹) | Min | Max |
|---|---|---|---|---|---|---|
| `inhibitor` | 48 | 0.5582 | 0.0527 | 0.0076 | 0.4446 | 0.6472 |
| `plain` | 48 | 0.6878 | 0.0550 | 0.0079 | 0.6016 | 0.8165 |

Inhibitor-evolved lineages grew more slowly by 0.1296 h⁻¹ (95% CI 0.1078 to 0.1514 h⁻¹ slower), a
reduction of 18.8 % relative to the plain-medium mean.

Independent two-sample t-test, all 96 assay runs:

- t = −11.79
- df = 93.84
- **p = 3.2 × 10⁻²⁰**
- Cohen's *d* = −2.41

Final optical density, reported for context and not tested, was 0.904 (SD 0.056) for the
inhibitor-evolved lineages and 0.979 (SD 0.052) for the plain-medium lineages.

## Interpretation

Thirty days of propagation under a sub-inhibitory efflux-pump inhibitor left the pathogen growing
measurably slower in drug-free medium than lineages propagated in plain medium over the same
period. The mean maximum growth rate fell from 0.688 h⁻¹ to 0.558 h⁻¹, a drop of about a fifth,
and the difference is large relative to the scatter among assay runs (Cohen's *d* = −2.41). This is
the classic signature of an evolved fitness cost: the adaptations that let a lineage tolerate
efflux-pump inhibition carry a growth penalty that shows up once the inhibitor is removed.

The lower final OD600 in the inhibitor-evolved lineages, about 0.08 OD units below the
plain-medium lineages, points the same way. The cost is not confined to the exponential phase; the
inhibitor-evolved populations also reach a lower plateau, so the burden shows up in yield as well
as in rate.

Practically, a cost of this size is encouraging for inhibitor-based adjuvant strategies. Adaptation
to the efflux-pump inhibitor does not come free, so inhibitor-adapted genotypes should be at a
disadvantage against wild-type competitors whenever the inhibitor is withdrawn, which supports
cycling or intermittent dosing rather than continuous exposure. These lineages evolved under a
sub-inhibitory dose; a fully inhibitory dose could select different mechanisms with a different
cost profile, and the assays here were run in a single rich medium, so the size of the cost in
other growth conditions remains to be measured.
