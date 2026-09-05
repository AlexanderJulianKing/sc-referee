# Data description

File: `aphasia_therapy_data.csv`

## What one row represents

One row is one participant in the service evaluation: one adult with chronic
post-stroke aphasia, four to twelve months after a single left-hemisphere stroke,
allocated to one of the two therapy schedules and assessed once by a blinded
assessor at the end of therapy. Each participant appears exactly once.

The file holds a header row plus 54 participant rows: 27 allocated to the
intensive schedule and 27 to the distributed schedule. Rows are listed in
allocation order, so the two schedules are interleaved. There are no missing
cells and no extra rows; every participant has a value in every column.

## Columns

| Column | Type | Meaning |
| --- | --- | --- |
| `participant_id` | text | Participant identifier: the prefix `P` plus a zero-padded serial number, `P01` through `P54`. Unique across the file. |
| `group` | text | Therapy schedule the participant was allocated to. Exactly two distinct values: `intensive` (15 hours per week for 3 weeks) and `distributed` (the same total hours spread over 9 weeks). |
| `naming_accuracy_pct` | number | Picture-naming accuracy at the end of therapy, as a percentage of the 60 test items named correctly. Recorded as a whole number of items correct and reported as a percentage to one decimal place, so values are multiples of 1/60 of 100 percent. Possible range 0 to 100. |
| `speech_rate_wpm` | number | Connected-speech rate in the standard picture-description task, in words per minute, to one decimal place. |
| `functional_communication_0_100` | integer | Functional communication in everyday life, rated by a familiar communication partner on a 0 to 100 scale, whole points only. Higher means better everyday communication. |

The three outcome columns appear in the order declared in the protocol:
picture naming, then connected-speech rate, then functional communication.

## Notes on the recorded values

- Units follow how each measure is taken: naming accuracy comes from a 60-item
  test, speech rate from a timed picture description, and functional
  communication from a partner-completed rating scale.
- Values are fixed and committed to the CSV. `make_data.py` in this directory is
  the one-off authoring script that produced the file; it is not part of the
  analysis and does not need to be run again.
