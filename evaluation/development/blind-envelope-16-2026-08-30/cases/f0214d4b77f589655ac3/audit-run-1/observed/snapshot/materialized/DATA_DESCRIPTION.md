# Data description: `girth_pad_trial.csv`

A veterinary welfare trial on harness padding for working donkeys hauling brick carts.
48 adult working donkeys were each assessed once, after four weeks of normal work.
24 donkeys worked in a new closed-cell foam girth pad and 24 in the traditional
sacking-wrapped girth.

**One row is one donkey**: a single animal, with its harness group and the five
declared outcome measurements taken at that one assessment. There are 48 rows plus a
header row. Every donkey has a value for every outcome; there are no missing values.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `donkey_id` | text | Per-donkey identifier, `D01` through `D48`. One value per row, unique across the file. |
| `girth_type` | text | Harness group. Exactly two values: `foam_pad` (closed-cell foam girth pad, 24 donkeys) and `sacking_wrap` (traditional sacking-wrapped girth, 24 donkeys). |
| `lesion_score_pts` | integer | Girth-region skin lesion score, in points on a 0 to 5 integer scale. Higher means more lesion damage. |
| `hair_loss_cm2` | number | Area of hair loss in the girth region, in square centimetres. |
| `nociceptive_threshold_n` | number | Mechanical nociceptive threshold at the girth region, in newtons: the pressure force at which the donkey first responds. Higher means less sensitivity to pressure. |
| `body_condition_pts` | number | Body condition score, in points on a 1 to 9 scale, recorded to the nearest half point. |
| `rectal_temp_c` | number | Rectal temperature 15 minutes after the working day, in degrees Celsius. |

The five outcome columns appear in the order the trial declared them: lesion score,
hair loss, nociceptive threshold, body condition, rectal temperature.
