# Data description

## File

`damselfly_condition.csv` — 70 data rows plus one header row, comma separated, UTF-8.

## What one row represents

One row is one adult male blue-tailed damselfly. Each insect was hand-netted within two days of
emergence, at a single pond, and measured individually in the laboratory on the day of capture. No
insect appears twice, and every insect has a value in every column, so there are no missing cells.

Seventy insects are present: 35 netted at fish-free ponds and 35 netted at fish-stocked ponds. All
ponds lie in one lowland landscape and were sampled in the same fortnight. Specimen serial numbers
run in capture order, which interleaves the two pond types, so the serial number does not track the
pond type.

## Columns

| Column | Type | Units / values | Meaning |
| --- | --- | --- | --- |
| `specimen_id` | text | `dam_001` … `dam_070` | Unique specimen identifier: the prefix `dam` plus a zero-padded serial number in capture order. |
| `pond_type` | text | exactly two values: `fish_free`, `fish` | Group column. The type of pond the insect emerged from: `fish_free` = pond holding no fish, `fish` = pond stocked with fish. |
| `body_length_mm` | number | millimetres, 0.1 mm | Total body length, head to abdomen tip, measured with digital callipers. |
| `hindwing_length_mm` | number | millimetres, 0.1 mm | Hind-wing length, measured with digital callipers. |
| `abdominal_fat_mg` | number | milligrams, 0.01 mg | Abdominal fat content, dry mass of the solvent-extracted fat body, weighed on a microbalance. |
| `mite_count` | integer | whole mites, count | Ectoparasitic water-mite load: number of mites attached to the individual, counted under a stereo microscope. |
| `encapsulation_grey` | integer | greyscale value, 0–255 | Immune encapsulation response to a nylon monofilament implant, read as an 8-bit greyscale darkness value. Higher values mean a darker, stronger encapsulation response. |

The five outcome columns appear in the order fixed by the field protocol before sampling:
body length, hind-wing length, abdominal fat, mite load, encapsulation response.

## Provenance

The values are fixed and committed in the CSV. They were produced once by `make_data.py`, which
draws each outcome from the distributions stated in the field protocol, keeps the within-individual
correlations that real morphometric and condition measures show, and rounds every value to the
precision of the stated measurement method. The generator is kept for reference only; the analysis
reads the CSV.
