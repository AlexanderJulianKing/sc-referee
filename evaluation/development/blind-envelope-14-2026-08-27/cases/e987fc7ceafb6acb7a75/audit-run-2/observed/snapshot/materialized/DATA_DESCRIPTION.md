# Data description: honey_markers.csv

## What one row represents

One row is one honey sample: a single homogenised jar from one registered producer,
analysed once on the full marker panel. There are 90 rows plus a header row, and no
sample appears twice. Every cell is filled; there are no blanks and no missing-value
codes.

## Columns

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `sample_id` | text | none | Laboratory identifier for the jar, `H-001` through `H-090`. Unique across the file. |
| `floral_origin` | text | none | Declared floral origin of the sample. Exactly two values: `lime`, `oilseed_rape`. |
| `analysis_set` | text | none | Pre-assigned analysis set. Exactly two values: `discovery`, `validation`. Assigned before any measurement was made; no measurement influenced it. |
| `moisture_pct` | number | percent by mass | Moisture content, rounded to 0.1. |
| `conductivity_ms_per_cm` | number | mS per cm | Electrical conductivity of a 20 percent (w/w) solution, rounded to 0.001. |
| `hmf_mg_per_kg` | number | mg per kg | Hydroxymethylfurfural content, rounded to 0.1. Right-skewed across samples. |
| `diastase_number` | number | Schade units | Diastase activity, rounded to 0.1. |
| `proline_mg_per_kg` | number | mg per kg | Proline content, rounded to the nearest whole mg per kg. |
| `free_acidity_meq_per_kg` | number | milliequivalents per kg | Free acidity, rounded to 0.1. |

The six marker columns appear in the order the laboratory declared them:
moisture, conductivity, HMF, diastase, proline, free acidity.

## Group and set sizes

| Floral origin | discovery | validation | Total |
| --- | --- | --- | --- |
| `lime` | 23 | 22 | 45 |
| `oilseed_rape` | 23 | 22 | 45 |
| Total | 46 | 44 | 90 |

## Notes on the values

- Each marker stays inside the range the laboratory considers plausible for its method,
  and each is stored at the rounding the laboratory reports it at, so repeated values at
  the same rounded reading are expected.
- Sample-to-sample spread within one floral origin reflects producer-to-producer and
  jar-to-jar variation, not repeat measurement of the same jar. Each jar was analysed
  once, so the file contains no replicate rows to average.
- `sample_id` numbering follows the order the jars were logged in. Floral origins and
  analysis sets are interleaved through that order rather than blocked, so the file is
  not sorted by group.
