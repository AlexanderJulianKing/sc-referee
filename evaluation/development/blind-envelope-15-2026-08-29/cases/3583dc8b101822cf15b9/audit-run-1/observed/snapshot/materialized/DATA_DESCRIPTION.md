# data.csv

Environmental health survey of informal electronic waste recycling in one city.
Ninety-six adult male workers: 48 who dismantle and burn electronic scrap and 48
from a nearby textile trade with no metal exposure, matched on age band and years
of work. Each worker gave one blood sample and one spot urine sample on the same
morning.

**One row is one worker**, holding that worker's trade, his pre-assigned analysis
stage, and his six declared outcome measurements from that single sampling
morning. There are 96 rows plus a header row. There are no repeated rows, no
summary rows, and no blank cells.

## Columns, in file order

| Column | Meaning | Unit | Values |
| --- | --- | --- | --- |
| `worker_id` | Anonymous survey identifier for the worker | none | `ews001` to `ews096`, unique |
| `trade` | Exposure group: the worker's trade | none | `recycling` (dismantles and burns electronic scrap) or `textile` (control trade, no metal exposure) |
| `analysis_stage` | The half of the survey the worker was allocated to by a fixed random allocation made before any sample was analysed | none | `discovery` or `validation` |
| `blood_lead_ug_dl` | Blood lead concentration | micrograms per decilitre (ug/dL) | 1 decimal place |
| `urinary_cadmium_ug_g_cr` | Urinary cadmium, creatinine-corrected | micrograms per gram of creatinine (ug/g creatinine) | 2 decimal places |
| `urinary_nickel_ug_l` | Urinary nickel concentration | micrograms per litre (ug/L) | 1 decimal place |
| `haemoglobin_g_dl` | Blood haemoglobin concentration | grams per decilitre (g/dL) | 1 decimal place |
| `serum_alt_u_l` | Serum alanine aminotransferase activity | units per litre (U/L) | whole numbers |
| `urinary_8ohdg_ng_mg_cr` | Urinary 8-hydroxy-2-deoxyguanosine, creatinine-corrected | nanograms per milligram of creatinine (ng/mg creatinine) | 1 decimal place |

The six outcome columns appear in the order in which the survey protocol
declared them, and every worker has a value for every outcome.

## Group and stage counts

| | discovery | validation |
| --- | --- | --- |
| recycling | 24 | 24 |
| textile | 24 | 24 |

The `analysis_stage` column records an allocation that was fixed and written into
the data file before any sample was analysed; it is not derived from the
measurements. Row order does not encode trade or stage.
