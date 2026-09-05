# Data description

Two CSV files, both produced by `make_data.py` (seeded, deterministic; rerunning the
script reproduces both files byte for byte).

Setting: a late-winter supplementary feeding study in a northern reindeer herding
district. Seventy-two semi-domesticated reindeer were followed from January to April.
Thirty-six were fed pelleted supplement at feeding stations, thirty-six grazed natural
winter pasture only. Each animal was handled once in April and contributes one set of
measurements.

## `reindeer_winter_measurements.csv`

Raw handling records. 72 data rows plus one header row. One row is one reindeer,
measured at its single April handling. Ear-tag numbers were handed out at capture, so
the two feeding regimes are interleaved in the file rather than blocked.

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `animal_id` | text | none | Ear-tag identifier of the animal, `RD-1001` through `RD-1072`. Unique; one row per identifier. |
| `body_mass_kg` | number, 1 decimal | kilograms | Live body mass at the April handling, from the handling-crush scale. Observed range 51.2 to 95.6. |
| `back_fat_thickness_mm` | number, 1 decimal | millimetres | Subcutaneous back fat depth measured by ultrasound at the April handling. Observed range 4.8 to 21.5. |
| `serum_urea_mmol_per_l` | number, 2 decimals | millimoles per litre | Serum urea concentration from the April blood sample. Observed range 1.49 to 8.48. |
| `hair_cortisol_pg_per_mg` | number, 2 decimals | picograms per milligram of hair | Hair cortisol concentration from the April hair sample, an integrated marker of the winter period. Observed range 0.40 to 5.65. |
| `feeding_regime` | text | none | Grouping factor, exactly two distinct values: `supplemented` (36 animals) and `pasture_only` (36 animals). |

The four outcome columns appear in the order the study plan declared them: body mass,
back fat thickness, serum urea, hair cortisol. No cell is empty in any row or column.

## `adjusted_pvalues.csv`

Output carried over from an earlier, separate pipeline stage. That stage compared the
two feeding regimes for all four declared outcomes and then corrected the whole family
of four comparisons for multiple testing at the conventional 0.05 family level
(two-sided Welch two-sample tests, step-down Holm correction across the four). The
stage is not part of this project; only its result table is supplied here.

4 data rows plus one header row. One row is one declared outcome, and the rows appear
in the declared order.

| Column | Type | Meaning |
| --- | --- | --- |
| `outcome` | text | Name of the declared outcome. Matches the corresponding column name in `reindeer_winter_measurements.csv` exactly: `body_mass_kg`, `back_fat_thickness_mm`, `serum_urea_mmol_per_l`, `hair_cortisol_pg_per_mg`. |
| `p_raw` | number | The uncorrected p-value the earlier stage started from, before any family correction. |
| `p_adjusted` | number | The family-corrected p-value the earlier stage produced for that outcome, after correcting across all four declared outcomes. |

Both p columns are written with six significant digits.
