# Data description

`data.csv` holds the post-operative records for the sixty-four healthy adult bitches enrolled after
routine elective ovariohysterectomy. **One row is one dog**: its identifier, the analgesia protocol
it was recovered on, and its value for each of the seven outcomes declared in the study protocol.

The file has 64 data rows plus a header row. Thirty-two dogs were recovered on protocol A (systemic
opioid alone) and thirty-two on protocol B (systemic opioid plus a local incisional block). Every
dog has a value in every column; there are no blanks.

## Columns

| Column | Meaning | Units / scale |
| --- | --- | --- |
| `dog_id` | Unique identifier for the dog, `D01` through `D64` | none (text) |
| `protocol` | Analgesia protocol the dog was recovered on. Exactly two values: `A` (systemic opioid alone) or `B` (systemic opioid plus local incisional block) | none (text) |
| `pain_score_6h` | Declared outcome 1, primary. Composite behavioural pain score assessed 6 hours after extubation | points on a 0 to 24 clinical scale; whole numbers |
| `rescue_analgesia_24h_mg` | Declared outcome 2, primary. Total rescue analgesia given in the first 24 hours | milligrams (mg), one decimal place; `0.0` means no rescue analgesia was needed |
| `serum_cortisol_6h_ug_dl` | Declared outcome 3. Serum cortisol measured at 6 hours | micrograms per decilitre (ug/dL), one decimal place |
| `heart_rate_6h_bpm` | Declared outcome 4. Heart rate at 6 hours | beats per minute (bpm); whole numbers |
| `respiratory_rate_6h_brpm` | Declared outcome 5. Respiratory rate at 6 hours | breaths per minute (brpm); whole numbers |
| `food_intake_24h_g` | Declared outcome 6. Food eaten in the first 24 hours | grams (g); whole numbers |
| `rectal_temperature_6h_c` | Declared outcome 7. Rectal temperature at 6 hours | degrees Celsius (C), one decimal place |

The seven outcome columns appear in the order the study protocol declared them, and the first two
columns after `dog_id` and `protocol` are the two named primary outcomes.

Rows are stored in mixed protocol order, and `dog_id` numbers the rows as they appear in the file,
so the identifier carries no information about the protocol or about any outcome value.
