# data.csv

Day-14 measurements from a napa cabbage kimchi brining trial. Forty-four small
fermentation containers were filled from one homogenised batch of shredded
cabbage and seasoning, brined at either 2.0 percent or 3.0 percent salt
(22 containers per level), held at 4 degrees Celsius, and opened once on day 14
for measurement.

**One row is one fermentation container**, measured a single time on day 14.
There are 44 rows plus a header row. Every container has a value for every
outcome; there are no blank cells.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `container_id` | text | Container label, `C01` through `C44`. Unique; one per row. |
| `salt_pct` | number | Brining salt level of the container, as percent salt in the brine. Exactly two values occur: `2.0` and `3.0`. This is the group column. |
| `ph` | number | pH of the fermented product on day 14. Unitless. Two decimal places. |
| `titratable_acidity_pct` | number | Titratable acidity, expressed as percent lactic acid by mass. Two decimal places. |
| `lab_count_log10_cfu_g` | number | Lactic acid bacteria count, as log10 colony forming units per gram. Two decimal places. |
| `firmness_n` | number | Cabbage firmness in newtons, peak force from a penetration probe. One decimal place. |
| `sourness_score` | number | Sourness rated by a trained sensory panel on a 1 to 9 scale, reported as the panel mean for that container. One decimal place. |

The five outcome columns appear in the order the study plan declared them:
pH, titratable acidity, lactic acid bacteria count, firmness, panel sourness.

## Observed value ranges in the file

| Column | Minimum | Maximum |
| --- | --- | --- |
| `ph` | 3.96 | 4.54 |
| `titratable_acidity_pct` | 0.53 | 1.05 |
| `lab_count_log10_cfu_g` | 7.30 | 8.84 |
| `firmness_n` | 10.0 | 16.8 |
| `sourness_score` | 3.4 | 7.6 |

## Format notes

- Comma separated, UTF-8, Unix (LF) line endings, one header row.
- No missing values, no quoted fields, no index column.
- Row order is the container order `C01`..`C44`; salt levels are interleaved
  rather than blocked.
