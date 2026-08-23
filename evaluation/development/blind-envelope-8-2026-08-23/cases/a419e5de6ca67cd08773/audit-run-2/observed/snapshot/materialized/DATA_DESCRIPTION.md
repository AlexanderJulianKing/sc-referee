# Data description

## File

`flush_yields.csv` — the single data file for the substrate trial. Comma separated, one header
row, UTF-8, no missing values.

The file is produced by `make_data.py`, which uses only the Python standard library and a fixed
random seed, so re-running it reproduces the file byte for byte. The values are invented for this
write-up, not measured from a real crop.

## What one row is

One row is **one flush from one growing chamber**: the weight harvested from a single chamber in a
single weekly flush, together with that chamber's air temperature at the time and how many days had
passed since spawning.

## Units and counts

- Growing chambers: **14** (`CH01` through `CH14`).
- Flushes recorded per chamber: **4** (flush 1 through flush 4, in time order).
- Rows: **56** (14 chambers x 4 flushes).

Every chamber contributes exactly four rows, so the four rows sharing a `chamber_id` are the same
chamber at four successive points in time.

## The two groups

The chambers are split evenly between two substrates:

| substrate | chambers | rows | chamber ids |
|---|---|---|---|
| `supplemented` | 7 | 28 | CH01, CH03, CH05, CH07, CH09, CH11, CH13 |
| `standard` | 7 | 28 | CH02, CH04, CH06, CH08, CH10, CH12, CH14 |

`supplemented` chambers were filled with straw substrate plus the protein-rich additive.
`standard` chambers were filled with the grower's usual straw substrate. A chamber keeps the same
substrate for all four of its flushes.

## Columns

| column | type | units | description |
|---|---|---|---|
| `chamber_id` | text | — | Identifier of the growing chamber, `CH01` to `CH14`. Repeats across the four rows belonging to that chamber. |
| `substrate` | text | — | Which substrate filled the chamber: `supplemented` or `standard`. Constant within a chamber. |
| `flush_number` | integer | — | Which flush this row records, `1` to `4`, in the order the chamber produced them. |
| `flush_yield_g` | number, 1 decimal | grams | Harvested mushroom weight from that chamber in that flush. |
| `air_temp_c` | number, 1 decimal | degrees Celsius | Chamber air temperature recorded at that flush. |
| `days_from_spawn` | integer | days | Days elapsed from spawning the chamber to that flush. |

## Observed ranges

- `flush_yield_g`: 770.9 to 1855.4 g. Mean by substrate: supplemented 1399.2 g, standard 1149.8 g.
- `flush_yield_g` by flush, averaged over all 14 chambers: flush 1 = 1536.9 g, flush 2 = 1321.9 g,
  flush 3 = 1189.8 g, flush 4 = 1049.2 g. Yield falls off with each successive flush, the first
  being the largest.
- `air_temp_c`: 19.3 to 23.4 C.
- `days_from_spawn`: 19 to 46 days. By flush: flush 1 = 19-23, flush 2 = 26-31, flush 3 = 33-38,
  flush 4 = 40-46. Chambers differ a little in how fast they came on.

## Sorting

Rows are sorted by `chamber_id`, then by `flush_number` ascending.
