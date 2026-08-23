# Data description

Speech-in-babble session, cochlear implant sound-processing strategies.

## Study units and groups

Eighteen adult cochlear implant recipients, each with at least one year of device
experience, were tested in a single session. Each recipient is assigned to exactly one
of two sound-processing strategy groups:

| group value in the files | meaning | recipients |
| --- | --- | --- |
| `established` | the established sound-processing strategy | 9 |
| `noise_reduction` | the newer noise-reduction processing strategy | 9 |

Every recipient completed five different standard sentence lists presented in background
babble, and the percentage of words repeated correctly was scored for each list. That
gives 18 recipients x 5 lists = 90 scored lists in total, with no missing lists.

Recipient identifiers run `CI01` through `CI18`. `CI01`-`CI09` are the established
strategy group and `CI10`-`CI18` are the noise-reduction group. The same identifiers
appear in both files, so the two files join one-to-many on `recipient_id`.

## File 1: `sentence_list_scores.csv` (raw scoring sheet)

90 data rows plus one header row.

**One row represents one sentence list scored for one recipient**, that is, a single
list-level score. Each recipient contributes five rows.

| column | type | description |
| --- | --- | --- |
| `recipient_id` | text | Recipient identifier, `CI01`-`CI18`. Repeats five times, once per sentence list. |
| `processing_strategy` | text | Sound-processing strategy the recipient was tested with: `established` or `noise_reduction`. Constant within a recipient. |
| `sentence_list` | text | Which of the five standard sentence lists this row is: `list_1`, `list_2`, `list_3`, `list_4`, `list_5`. |
| `percent_words_correct` | number | Percentage of words repeated correctly on that list, 0-100, recorded to one decimal place. |

## File 2: `recipient_mean_scores.csv` (per-recipient summary sheet)

18 data rows plus one header row. This is the summary sheet the audiologist prepared
from the session.

**One row represents one recipient**, summarising that recipient's five sentence lists.

| column | type | description |
| --- | --- | --- |
| `recipient_id` | text | Recipient identifier, `CI01`-`CI18`. Appears exactly once. |
| `processing_strategy` | text | Sound-processing strategy for that recipient: `established` or `noise_reduction`. |
| `mean_percent_words_correct` | number | That recipient's mean percentage of words correct across their five sentence lists, 0-100, recorded to two decimal places. |
| `lists_scored` | integer | How many sentence lists the mean is based on. This is 5 for every recipient in this session. |

## Consistency between the two files

`mean_percent_words_correct` in the summary sheet is the arithmetic mean of that
recipient's five `percent_words_correct` values in the raw scoring sheet, rounded to two
decimal places. `lists_scored` equals the number of raw rows carrying that
`recipient_id`. Both checks hold for all 18 recipients.

## Provenance

The values are simulated, not collected from patients. `make_data.py` in this directory
generates both CSVs from a fixed random seed using only the Python standard library, so
the files reproduce exactly. Recipient-level ability was drawn around a group mean of 54
percent words correct for the established strategy and 63 percent for the noise-reduction
strategy, with a between-recipient spread of about 12 percentage points, and list-to-list
scores were drawn around each recipient's own level with a spread of about 9 percentage
points. Values were constrained to the 0-100 percentage range; in the generated files no
value reached either bound. The CSVs are committed as plain text and are not regenerated
at analysis time.
