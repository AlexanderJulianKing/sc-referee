# Data description

## File

`plantain_frying_batches.csv` — 40 data rows plus one header row, comma separated,
no missing values.

## What one row represents

One row is one independently prepared frying batch of plantain crisps. Each batch was
made from its own separate lot of sliced green plantain and fried under one of the two
frying methods. Every batch was measured once for each of the five outcomes, so a row
carries the complete outcome record for that batch. Batches are listed in processing
run order.

There are 40 batches in total: 20 fried under vacuum at 120 degrees Celsius and 20
fried at atmospheric pressure at 170 degrees Celsius.

## Columns

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `batch_id` | text | none | Per-batch identifier, `b01` through `b40`, unique, in processing run order. |
| `frying_method` | text | none | Frying method contrast. Exactly two values: `vacuum` (120 degrees Celsius under vacuum, 20 batches) and `atmospheric` (170 degrees Celsius at atmospheric pressure, 20 batches). |
| `oil_content_g100g` | number | g per 100 g of product | Oil content of the finished crisps. Recorded to one decimal place. |
| `acrylamide_ug_kg` | integer | micrograms per kilogram | Acrylamide content of the finished crisps. Recorded as a whole number. |
| `breaking_force_n` | number | newtons | Maximum breaking force in a three-point bend test. Recorded to one decimal place. |
| `colour_b_cielab` | number | CIELAB units | Colour b\* value of the ground crisps. Recorded to one decimal place. |
| `crispness_score_pts` | number | points on a 0 to 10 scale | Trained panel crispness score. Recorded to one decimal place. |

The five outcome columns appear in the order in which the outcome family was declared
in advance: oil content, acrylamide, breaking force, colour b\*, crispness score.

## Provenance

The values are simulated for this exercise by `make_data.py`, which draws each batch
from the pilot-plant ranges described in the study brief with a fixed random seed.
No group comparison is computed or stored in this data stage.
