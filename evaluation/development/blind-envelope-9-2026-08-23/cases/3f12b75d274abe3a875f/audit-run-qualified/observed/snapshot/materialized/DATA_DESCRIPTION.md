# Data description

## File

`whistle_recordings.csv` — the only data file in this project. It holds the whistle measurements
themselves. The study calls for a single CSV, so there is no separate summary file; the reduction
from recordings to one row per dolphin happens inside the analysis, not on disk.

The file was produced by `make_data.py` (Python standard library only, fixed seed `20260823`), so
re-running that script reproduces it byte for byte.

## What one row represents

One row is **one whistle recording of one dolphin**: a single good-quality signature whistle,
captured during one encounter, with its peak frequency measured.

A row is *not* a dolphin. Each dolphin appears on six separate rows.

## How many units and rows

- **18 dolphins** (the units). Photo-identified adult bottlenose dolphins of known sex from one
  estuary, catalogue identifiers `EST-001` through `EST-018`.
- **6 recordings per dolphin**, each from a separate encounter. Every dolphin has all six, with no
  missing values.
- **108 rows** of data (18 x 6), plus one header line.

## The two groups

The comparison is between the two sexes, held in the `sex` column:

| Group    | Dolphins | Catalogue ids       | Rows |
| -------- | -------- | ------------------- | ---- |
| `male`   | 9        | EST-001 to EST-009  | 54   |
| `female` | 9        | EST-010 to EST-018  | 54   |

Sex is a property of the animal, so it is the same on all six rows for a given dolphin.

## Columns

| Column                 | Type              | Meaning |
| ---------------------- | ----------------- | ------- |
| `dolphin_catalogue_id` | text              | Catalogue identifier of the photo-identified animal the recording came from, in the form `EST-001` through `EST-018`. This is the unit column: rows sharing an id are repeated measurements of the same dolphin. |
| `sex`                  | text, `male` or `female` | Sex of the animal. Constant within a dolphin. Nine dolphins carry each value. |
| `recording_number`     | whole number, 1 to 6 | Which of that animal's six retained recordings this row is. It counts within the animal, restarting at 1 for each dolphin, and each encounter was separate. It is a label, not a time point on a common clock, so recording 3 of one dolphin has nothing to do with recording 3 of another. |
| `peak_frequency_khz`   | number, 2 decimals | Peak frequency of the whistle in **kilohertz** (the unit is in the column name). This is the outcome being compared between the sexes. Values run from 8.18 to 15.98 kHz. |

## Structure the numbers carry

Because six recordings come from the same animal, the rows are not independent of one another.
Each dolphin has its own characteristic whistle, which is what makes signature whistles useful for
identifying individuals. That shows up in the data three ways:

- Recordings of the same dolphin sit close together (typical spread within an animal is about
  0.8 kHz).
- Different dolphins sit further apart (typical spread of animal averages within a sex is about
  1.4 to 2.1 kHz).
- Female animal averages sit roughly 1.9 kHz above male animal averages in this sample.

Anyone analysing the file has to take the repeated measurements into account rather than treating
all 108 rows as 108 independent observations.
