# Data description

Bone-density supplement study, outpatient bone health service. Thirty post-menopausal women each
completed one of two twelve-month supplement regimes. At the end of the study each woman had a
single lumbar spine scan, and the radiographer read areal bone mineral density (aBMD) separately at
four vertebral levels of that one spine.

## Units and groups

- **Units:** 30 women, identified by `patient_ref` codes `BD-01` through `BD-30`. One woman is one
  independent unit of the study.
- **Groups:** two supplement regimes, 15 women each.
  - `vitamin_d_calcium` — combined vitamin D and calcium (15 women)
  - `vitamin_d_only` — vitamin D alone (15 women)
- **Repeated measurements:** each woman contributes 4 vertebral-level readings (`L1`, `L2`, `L3`,
  `L4`) from her one scan. The four readings from a single spine are not independent of each other;
  they are four looks at the same woman.
- **Totals:** 30 women x 4 levels = 120 vertebral-level readings.

## File 1 — `vertebral_level_readings.csv`

120 data rows plus a header row. **One row is one vertebral level of one woman's scan** (for
example, the L3 reading for BD-07). Each woman appears on exactly 4 rows.

| Column | Type | Description |
| --- | --- | --- |
| `patient_ref` | text | Study code of the woman the reading came from, `BD-01` to `BD-30`. Repeats 4 times, once per vertebral level. |
| `supplement_regime` | text | Which regime that woman took: `vitamin_d_calcium` or `vitamin_d_only`. Constant across a woman's 4 rows. |
| `vertebral_level` | text | Which lumbar vertebra was read: `L1`, `L2`, `L3` or `L4`. |
| `bmd_g_per_cm2` | number | Areal bone mineral density at that vertebral level, in grams per square centimetre, to 3 decimal places. Range in this dataset 0.738 to 1.193. |

## File 2 — `patient_summary.csv`

30 data rows plus a header row. **One row is one woman**, so each woman appears exactly once. This
is the file at the level of the study's independent unit.

| Column | Type | Description |
| --- | --- | --- |
| `patient_ref` | text | Study code of the woman, `BD-01` to `BD-30`. Unique in this file. |
| `supplement_regime` | text | Which regime she took: `vitamin_d_calcium` or `vitamin_d_only`. |
| `mean_bmd_g_per_cm2` | number | That woman's mean aBMD across her vertebral levels, in grams per square centimetre, to 4 decimal places. |
| `n_levels` | integer | How many vertebral-level readings went into her mean. It is 4 for every woman here; no scan had an unreadable level. |

## How the two files relate

`patient_summary.csv` is derived from `vertebral_level_readings.csv`. Each woman's
`mean_bmd_g_per_cm2` is the arithmetic mean of her 4 `bmd_g_per_cm2` values as they appear in the
level file (rounded to 4 decimal places), and `n_levels` is the count of those rows. `patient_ref`
and `supplement_regime` match between the files for every woman. The files therefore agree
numerically: the summary file adds no information beyond the level file, it only collapses each
woman's 4 readings into 1 row.

## How the values were produced

`make_data.py` (Python standard library only, fixed seed `20260823`) generates both CSVs.
Each reading is built as:

```
reading = 0.960 (baseline)
        + 0.045 if on the combined regime
        + a per-woman offset drawn with SD 0.100 g/cm^2
        + a fixed level offset (L1 -0.022, L2 -0.006, L3 +0.009, L4 +0.019)
        + measurement noise drawn with SD 0.030 g/cm^2
```

The per-woman offset is drawn once and shared by all 4 of that woman's readings, which is what makes
the levels within one spine resemble each other more closely than readings from different women.
The level offsets follow the usual lumbar pattern of density rising from L1 to L4. Regime allocation
was shuffled with the same seed and forced to exactly 15 women per regime.
