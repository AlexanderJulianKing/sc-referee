# Peatland methane chamber survey

This dataset comes from a growing-season survey of methane emissions on a
lowland raised bog complex. Twelve permanent static-chamber collars were
installed and left in place for the whole season: six collars on a block of
peat that was ditch-drained decades ago for forestry, and six collars on an
adjacent block of peat that was never drained.

Each of the twelve collars was revisited five times during the season. On
each visit a technician sealed an opaque chamber onto the collar, took
headspace samples over a timed closure, and converted the concentration rise
into a methane flux. The depth to the water table was read from a dipwell
next to the collar at the same visit. So the file holds 12 collars x 5 visits
= 60 measurement records.

## Columns

- `collar_id`: label of the permanent chamber collar. There are twelve
  distinct collars (D01-D06 on the drained block, N01-N06 on the intact
  block), and each one appears five times in the file.
- `peat_condition`: whether the collar sits on `drained` or `intact` peat.
  This is a property of the collar, so it is the same on all five of that
  collar's visits.
- `closure_index`: which of that collar's five seasonal visits produced the
  record, numbered 1 to 5 in visit order.
- `water_table_cm`: depth to the water table at the collar on that visit, in
  centimetres below the peat surface (negative numbers mean the water table
  sits below the surface).
- `ch4_flux_mg_m2_h`: the methane flux estimated from that chamber closure,
  in milligrams of CH4 per square metre per hour. This is the outcome of
  interest.

## Structure to keep in mind

The five records that share a `collar_id` are repeat visits to the same patch
of peat, not five separate patches. Fluxes from the same collar tend to sit
close together because they share the same microtopography, vegetation and
drainage history, while different collars on the same block can differ
noticeably from each other. The drainage treatment was applied to blocks of
peat and is fixed at the collar level, so the number of physically
independent pieces of peat in the study is twelve, not sixty.

One row is: one timed static-chamber closure at one collar on one visit
Independent unit column: collar_id
