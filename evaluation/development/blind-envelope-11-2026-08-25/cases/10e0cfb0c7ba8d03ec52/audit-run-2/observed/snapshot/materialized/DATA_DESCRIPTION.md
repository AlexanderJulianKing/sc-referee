# Data description

## Files

### `make_data.py`

Deterministic generator for the data set. It uses a fixed random seed (20260825) and only the
Python standard library, so re-running it reproduces `pilot_columns.csv` byte for byte.

### `pilot_columns.csv`

The study data. 32 data rows plus one header row, comma separated, UTF-8, one trailing newline.

**What one row represents:** one pilot-scale trickling filter column. The pilot bank held 32
columns, all fed the same settled sewage from a common header tank for ten weeks. Each column's
row holds its steady-state performance values, each one already averaged over the final two weeks
of the run. There is one row per column and no column appears twice. Every cell is filled; there
are no missing values.

**Columns, in file order:**

| Column | Type | Description |
| --- | --- | --- |
| `pilot_column_id` | text | Identifier of the pilot unit, `TF-01` through `TF-32`. Unique across rows. |
| `bod_removal_percent` | number | Biochemical oxygen demand removal across the column, in percent, one decimal place. Values run from 64.5 to 95.0. |
| `ammonium_nitrogen_removal_percent` | number | Ammonium nitrogen removal across the column, in percent, one decimal place. Values run from 35.8 to 83.1. |
| `effluent_suspended_solids_mg_per_l` | number | Suspended solids in the column effluent, in milligrams per litre, one decimal place. Values run from 8.2 to 58.6. |
| `biofilm_dry_mass_g_per_m2` | number | Attached biofilm dry mass per unit media surface area, in grams per square metre, one decimal place. Values run from 20.5 to 59.6. |
| `packing_media` | text | Packing media the column was filled with. Exactly two distinct values: `crushed_rock` and `plastic_cross_flow`. |

The four measurement columns appear in the order the outcomes were declared in the pilot plan:
BOD removal, ammonium nitrogen removal, effluent suspended solids, biofilm dry mass.

**Group sizes:** 16 columns carry `crushed_rock` and 16 carry `plastic_cross_flow`. Media was
assigned across the bank of 32 units, so the two media are interleaved rather than blocked by
identifier.

**Level and spread as generated** (per media, mean and standard deviation across the 16 columns):

| Outcome | `crushed_rock` | `plastic_cross_flow` |
| --- | --- | --- |
| `bod_removal_percent` | 81.7, sd 5.6 | 77.5, sd 6.6 |
| `ammonium_nitrogen_removal_percent` | 66.7, sd 7.7 | 54.0, sd 8.1 |
| `effluent_suspended_solids_mg_per_l` | 17.3, sd 4.5 | 29.3, sd 10.3 |
| `biofilm_dry_mass_g_per_m2` | 44.3, sd 9.3 | 36.0, sd 8.0 |

**Note on one record:** `TF-07` carries an effluent suspended solids value of 58.6 mg/L. That is
far above every other column in the file, the next highest being 40.3 mg/L, and above the range a
column at steady state produces. The operator's log records that the grab sample for that unit was
disturbed during collection. The value is left in the data file as recorded.
