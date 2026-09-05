# Data description: `lipid_panel.csv`

## What one row represents

One row is one participant in the eight-week parallel-group feeding study. The row holds that
participant's identifier, the daily snack they were allocated to, and the five declared lipid
outcomes measured on the single fasting blood sample taken at the end of week eight. Each
participant appears exactly once. There are 70 rows plus one header row, and no blank cells.

## Columns

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `participant_id` | text | none | Study identifier, `NUT-001` through `NUT-070`. Unique across the file. |
| `snack` | text | none | Allocated daily snack. Exactly two values: `walnut` (30 g walnuts per day) and `cracker` (30 g matched savoury cracker snack per day). |
| `ldl_c_mmol_per_l` | number, 2 decimals | mmol/L | Declared outcome 1. Fasting LDL cholesterol. |
| `hdl_c_mmol_per_l` | number, 2 decimals | mmol/L | Declared outcome 2. Fasting HDL cholesterol. |
| `triglycerides_mmol_per_l` | number, 2 decimals | mmol/L | Declared outcome 3. Fasting triglycerides. Right-skewed on the raw scale. |
| `total_c_mmol_per_l` | number, 2 decimals | mmol/L | Declared outcome 4. Fasting total cholesterol. |
| `apo_b_g_per_l` | number, 2 decimals | g/L | Declared outcome 5. Fasting apolipoprotein B. |

The five outcome columns appear in the order the unit declared them before recruitment.

## Group sizes

| `snack` | Participants |
| --- | --- |
| `walnut` | 35 |
| `cracker` | 35 |
| Total | 70 |

## Notes on the values

- All lipid values are reported to two decimal places, as a clinical laboratory reports them.
- The panel is internally consistent: total cholesterol tracks the Friedewald relationship
  `TC = LDL + HDL + TG / 2.2` up to assay error, and apolipoprotein B rises with LDL and
  triglycerides, since it counts the same atherogenic particles.
- Values fall inside the reporting windows named in the study protocol: LDL 2.0-4.6, HDL 0.85-2.1,
  triglycerides 0.55-2.8, total cholesterol 3.6-7.2 (all mmol/L), apolipoprotein B 0.55-1.35 g/L.
- Rows are ordered by `participant_id`, which follows the randomisation order, so the two snack
  groups are interleaved rather than blocked.
