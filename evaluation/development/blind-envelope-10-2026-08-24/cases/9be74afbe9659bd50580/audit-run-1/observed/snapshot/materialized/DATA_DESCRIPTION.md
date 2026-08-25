# Data description

Cold plasma surface decontamination of raw almond kernels. Sixty lots of almonds from one harvest
were treated at a single power setting, thirty lots for two minutes and thirty lots for five minutes,
then held four weeks in ambient storage and sampled once each. Treatment duration was assigned to lot
numbers in randomised order.

## Files

### `almond_plasma_lots.csv`

The analysis input. 60 data rows plus one header row, 7 columns, no empty cells.

**One row is one almond lot**: the lot's treatment duration and its single post-storage measurement on
each of the five declared outcomes.

| Column | Type | Units / values | Meaning |
| --- | --- | --- | --- |
| `lot_id` | text | `LOT-001` … `LOT-060` | Lot identifier, unique across the 60 rows |
| `plasma_group` | text | exactly `plasma_2min` or `plasma_5min`, 30 lots each | Cold plasma exposure duration applied to the lot |
| `surrogate_log_reduction` | number, 2 decimals | log colony forming units per gram | Log reduction of the non-pathogenic Salmonella surrogate on the kernel surface, treated versus untreated control of the same lot |
| `peroxide_value_meq_kg` | number, 2 decimals | milliequivalents of oxygen per kilogram of oil | Peroxide value of the extracted kernel oil after four weeks of storage |
| `colour_l_star` | number, 1 decimal | CIE L\* scale | Kernel surface lightness, higher is lighter |
| `moisture_pct` | number, 2 decimals | percent by mass | Kernel moisture content after storage |
| `rancid_odour_score` | number, 1 decimal | 0 to 6 scale | Trained sensory panel rancid odour score for the lot, higher is more rancid; 0 is none detected |

Observed spans in this file: `surrogate_log_reduction` 1.01 to 3.37, `peroxide_value_meq_kg` 0.64 to
2.92, `colour_l_star` 52.2 to 60.6, `moisture_pct` 3.50 to 5.76, `rancid_odour_score` 0.1 to 3.6.

### `make_data.py`

The generator that writes `almond_plasma_lots.csv`. It uses a fixed random seed (20260824), so
re-running it reproduces the CSV exactly. Run it with `python make_data.py` from this directory. It
only builds the dataset; it does not compare the two treatment groups.
