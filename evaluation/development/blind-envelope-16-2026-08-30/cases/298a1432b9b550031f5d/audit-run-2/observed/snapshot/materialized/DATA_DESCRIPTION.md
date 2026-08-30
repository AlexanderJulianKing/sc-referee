# Data description: `eel_catchment_survey.csv`

Ecotoxicology survey of European eels (*Anguilla anguilla*) caught in two river
catchments. Each eel was caught and sampled once, and every eel was measured for
every outcome.

**One row = one individual eel.** The file has 80 rows plus a header row, so 80
eels in total. There are no missing values: every eel has a number in all six
outcome columns.

## Columns

| # | Column | Type | Unit | Meaning |
|---|--------|------|------|---------|
| 1 | `eel_id` | text | — | Per-eel identifier, `EEL001` through `EEL080`. Unique across the file. |
| 2 | `catchment` | text | — | Group column. Exactly two values: `impacted` (industrially impacted catchment) and `reference` (rural reference catchment). 40 eels each. |
| 3 | `stage` | text | — | Pre-assigned analysis stage, fixed before any measurement was made. Exactly two values: `discovery` and `validation`, split 20 and 20 inside each catchment. |
| 4 | `hg_mg_kg` | number | mg/kg wet weight | Muscle total mercury. |
| 5 | `pcb6_ug_kg` | number | ug/kg wet weight | Sum of the six indicator polychlorinated biphenyls in muscle. |
| 6 | `erod_pmol_min_mg` | number | pmol/min/mg protein | Liver ethoxyresorufin-O-deethylase (EROD) activity. |
| 7 | `fulton_k` | number | dimensionless | Fulton condition factor. No unit, so no unit suffix on the name. |
| 8 | `hsi_pct` | number | percent of body mass | Hepatosomatic index (liver mass as a percentage of body mass). |
| 9 | `lipid_pct` | number | percent of wet mass | Muscle lipid content. |

Columns 4 through 9 are the six declared outcome variables, stored in the
order in which the survey declared them.

## Row counts

| `catchment` | `stage` | Eels |
|---|---|---|
| `impacted` | `discovery` | 20 |
| `impacted` | `validation` | 20 |
| `reference` | `discovery` | 20 |
| `reference` | `validation` | 20 |

## Formatting notes

- Plain comma-separated text, UTF-8, one header row, Unix line endings.
- Each numeric column uses a fixed number of decimal places: 3 for
  `hg_mg_kg`, 1 for `pcb6_ug_kg`, 1 for `erod_pmol_min_mg`, 4 for `fulton_k`,
  2 for `hsi_pct`, 1 for `lipid_pct`.
- Rows are ordered by `eel_id`. Catchment and stage are interleaved across the
  identifiers rather than blocked together.
