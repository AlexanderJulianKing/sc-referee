# data.csv

Week six visit records from a stop smoking service for adult daily smokers who asked for help
quitting. Seventy-two participants were allocated to one of two nicotine substitution products
(36 to each) and all received the same brief behavioural support. Every participant attended the
week six visit, so every row is complete.

**One row represents one participant**, holding that participant's identifier, the product they
were allocated to, and their three week six outcome measurements. There are 72 data rows plus one
header row. There are no repeated rows, no summary rows, and no blank cells.

## Columns

Columns appear in this order.

| Column | Meaning | Unit / values |
| --- | --- | --- |
| `participant_id` | Identifier for the participant, unique within the file. Assigned in the order participants appear in the clinic record. | Text: the prefix `qs_` followed by a three digit zero padded number, `qs_001` through `qs_072`. |
| `nicotine_product` | The nicotine substitution product the participant was allocated to. | Text, exactly two labels: `vape` (refillable nicotine vaping device, standardised liquid strength) or `patch` (transdermal nicotine patch, standard starting dose). 36 rows carry each label. |
| `exhaled_co_ppm` | Exhaled carbon monoxide measured at the week six visit. | Parts per million (ppm), recorded to one decimal place. Values in this file run from 1.2 to 19.3. |
| `cigarettes_smoked_cpd` | Cigarettes smoked per day at week six, self-reported over the previous seven days. | Cigarettes per day (cpd), whole numbers. Values in this file run from 0 to 14. |
| `urge_to_smoke_vas_0_100` | Strongest urge to smoke in the past week, marked on a visual analogue scale. | Points on a 0 to 100 scale, whole numbers, where 0 is no urge at all and 100 is the strongest possible urge. Values in this file run from 0 to 70. |

The three outcome columns appear in the order the outcomes were declared in the evaluation
protocol before recruitment started: exhaled carbon monoxide, then cigarettes per day, then
strongest urge to smoke.

## Notes

- `data.csv` is a fixed data file. It is read, never generated or overwritten, by anything
  downstream.
- Column names are lower case with underscores throughout.
