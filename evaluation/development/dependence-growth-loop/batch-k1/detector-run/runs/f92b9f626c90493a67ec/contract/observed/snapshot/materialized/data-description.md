# Kaldbekk fen warming array: campaign methane fluxes

Twenty-four intact peat mesocosms were cut from a subarctic fen in spring 2025 and set
out in a common outdoor array arranged in four spatial blocks. Twelve mesocosms received
an open-top warming chamber and twelve were left at ambient temperature. The treatment
was assigned once, to the whole mesocosm, and never changed during the season. Methane
flux was measured with a static chamber on four campaigns spread across the thaw season
(weeks 3, 6, 9 and 12), so every mesocosm appears in the file four times, once per
campaign. The file is stored campaign by campaign: all 24 mesocosms for week 3, then all
24 for week 6, and so on, giving 96 rows.

Columns:
- mesocosm_id: label of the peat mesocosm (M01 to M24). The mesocosm is the unit that was
  randomised to a treatment.
- block: spatial block of the outdoor array (1 to 4).
- treatment: ambient or warmed, fixed for the whole season.
- campaign_week: thaw-season week of the measurement (3, 6, 9 or 12).
- ch4_flux_mg_m2_h: methane flux measured on that campaign, in mg CH4 per square metre
  per hour.
- soil_temp_10cm_c: soil temperature at 10 cm depth at the time of the campaign, in
  degrees Celsius. Recorded for context; it is not part of the reported comparison.

One row is: one static-chamber methane flux measurement of one peat mesocosm on one campaign
Independent unit column: mesocosm_id

The rows are not all independent of one another: the four rows that share a mesocosm_id
are repeated measurements of the same physical mesocosm and are correlated. Anything said
about the warming treatment has to be argued across mesocosms, for example by first
summarising each mesocosm's four campaigns into a single seasonal value and comparing
those 24 values.
