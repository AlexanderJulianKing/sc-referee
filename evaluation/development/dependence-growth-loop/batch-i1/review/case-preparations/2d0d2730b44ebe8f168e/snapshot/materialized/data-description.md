# Hydrant flush register: chlorine residual around main relining

This file records free chlorine residual readings taken at fire hydrants in a
municipal drinking-water distribution system, before and after the ageing
cast-iron mains feeding those hydrants were cleaned and cement-mortar relined.

Twelve hydrants were enrolled. A field crew visited every enrolled hydrant on
three separate occasions and ran the same standardised flush each time, so each
hydrant contributes three rows to the file and the hydrant identifier repeats
down the table.

One row is: one standardised flush event at one hydrant, carrying the free chlorine residual measured at that hydrant before the upstream main was relined and the residual measured at the same hydrant after relining
Independent unit column: hydrant_id

Columns:

- hydrant_id: identifier of the fire hydrant that was flushed. Twelve hydrants
  appear, each on three rows.
- pressure_zone: the distribution pressure zone the hydrant sits in. All rows
  for a given hydrant carry the same zone.
- flush_event: which of that hydrant's three visits this row records (1, 2 or 3).
  Visit numbers are ordered in time but the spacing between visits is not
  recorded here.
- pre_reline_residual_mg_l: free chlorine residual in milligrams per litre
  measured at the hydrant during the flush, before the upstream main was
  relined.
- post_reline_residual_mg_l: free chlorine residual in milligrams per litre
  measured at the same hydrant during the matching flush after the upstream
  main was relined.

Units and conventions: residuals are in mg/L as free chlorine, reported to two
decimal places from a field colorimeter. There are no missing values, and every
row has both a pre-reline and a post-reline reading.
