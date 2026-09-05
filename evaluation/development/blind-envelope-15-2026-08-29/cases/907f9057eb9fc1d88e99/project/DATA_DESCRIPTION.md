# Data description: peatland restoration monitoring campaign

## What the file contains

`data.csv` holds the field measurements from one midsummer monitoring campaign on a bog with two
adjacent management blocks. Thirty-two permanent gas sampling collars are the measurement subjects.
Sixteen collars sit in a block rewetted by ditch blocking eight years ago; sixteen sit in an
adjacent block that is still drained. Each collar is installed in its own location and was measured
once during the campaign.

**One row is one collar, with the single set of measurements taken at that collar during the
campaign.** There are 32 data rows plus one header row. There are no repeated rows, no summary
rows, and no empty cells. Every collar has a value for every measured variable.

## Columns

The columns appear in the order listed below. The four measured variables are in the order in which
the monitoring plan declared them.

| Column | Meaning | Unit | Type and format |
| --- | --- | --- | --- |
| `collar_id` | Identifier of the permanent gas sampling collar. Unique across the file. | none | Text, `collar_` followed by a two-digit zero-padded number, `collar_01` to `collar_32` |
| `drainage_status` | Drainage status of the block the collar sits in. | none | Text, exactly two labels: `rewetted` (block rewetted by ditch blocking) and `drained` (block still drained) |
| `methane_flux_mgc_m2_h` | Methane flux measured at the collar, expressed as methane carbon. | milligrams of methane carbon per square metre per hour (mg C m-2 h-1) | Number, 2 decimal places |
| `respiration_co2_flux_mgc_m2_h` | Ecosystem respiration measured at the collar as carbon dioxide flux, expressed as carbon dioxide carbon. | milligrams of carbon dioxide carbon per square metre per hour (mg C m-2 h-1) | Number, 1 decimal place |
| `water_table_depth_cm` | Depth of the water table below the peat surface at the collar. Larger values mean a deeper, drier water table; `0.0` means the water table stood at the peat surface. | centimetres (cm) | Number, 1 decimal place |
| `sphagnum_cover_pct` | Sphagnum cover on the collar area, as a share of ground area. | percent of ground area (%) | Whole number, 0 to 100 |

## Recording conventions

- Group sizes are balanced: 16 rows with `drainage_status` of `rewetted` and 16 with `drained`.
  Collars `collar_01` to `collar_16` are the rewetted block, `collar_17` to `collar_32` the drained
  block.
- Each variable is rounded the way the campaign records it: methane flux to two decimals, carbon
  dioxide flux and water table depth to one decimal, and Sphagnum cover to the nearest whole
  percent, since cover is a visual estimate on the collar area.
- Methane fluxes on drained collars sit close to zero. Nothing in the file falls below the
  analyser's reporting floor.
- Water table depth is recorded as depth below the surface, so it is never negative in this
  campaign; the water table did not stand above the peat surface at any collar.
- Sphagnum cover can be `0`, which means no Sphagnum was recorded on that collar area.

## Provenance

`data.csv` is the fixed record of the campaign. It is read as input and is not regenerated or
overwritten by anything downstream.
