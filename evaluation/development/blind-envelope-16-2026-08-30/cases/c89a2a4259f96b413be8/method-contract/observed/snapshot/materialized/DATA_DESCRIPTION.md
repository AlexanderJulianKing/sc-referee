# Data description

File: `bakery_flour_dust.csv`

Occupational health survey of production workers in three industrial bread bakeries. Each worker
was measured once, on a single working shift.

**One row is one production worker.** There are 46 rows, one per worker, and no repeated
measurements: a worker appears exactly once. Every worker has a value in every column, so there are
no missing cells.

The workers fall into two production lines, held in the `dough_line` column, which takes exactly two
values:

- `open` — traditional open dough line, where flour is tipped from sacks and mixed in open bowls
  (24 workers)
- `enclosed` — enclosed automated ingredient dosing line (22 workers)

## Columns

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `worker_id` | text | none | Short per-worker identifier, `W01` to `W46`. Unique within the file. |
| `dough_line` | text | none | Production line the worker was assigned to: `open` or `enclosed`. |
| `dust_mg_m3` | number, 2 decimals | mg/m3 | Shift-average inhalable flour dust concentration in the worker's breathing zone. |
| `fev1_drop_ml` | integer | mL | Cross-shift fall in forced expiratory volume in one second, computed as the start-of-shift value minus the end-of-shift value. Negative values mean FEV1 was higher at the end of the shift than at the start. |
| `ige_wheat_ku_l` | number, 2 decimals | kU/L | Serum specific immunoglobulin E to wheat flour. |
| `nasal_symptom_pts` | integer | points | Work-related nasal symptom score over the previous month, on a 0 to 12 scale where higher means more symptoms. |

The four outcome columns appear in the order in which the study declared them: dust, then
cross-shift FEV1 fall, then wheat-specific IgE, then nasal symptom score.
