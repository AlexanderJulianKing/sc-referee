# About data/input.csv

This table comes from a bench-scale anaerobic digestion trial. Twelve identical
5-litre laboratory digesters were charged with the same food-waste feedstock.
Six of the vessels received untreated seed sludge ("control") and six received
seed sludge that had been thermally pretreated at 70 degrees Celsius for one
hour ("thermal"). Pretreatment was assigned to the vessel once, at start-up, and
never changed during the run.

Each vessel was then sampled four times, on run days 6, 10, 14 and 18. Every
sampling visit produced one stored record holding the specific methane yield
measured for that vessel on that day, together with the digestate pH and the
acetate concentration measured in the same sample. The file is therefore in long
format: the same digester appears four times, once per monitoring session.

One row is: one monitoring session on one digester, i.e. a single sampling visit to one vessel on one run day

Independent unit column: digester_id

The four rows that share a digester_id are repeated measurements of the same
physical reactor and are not independent of one another; they differ only in the
day the sample was drawn. Independent replication in this experiment is the
vessel, of which there are twelve, six per pretreatment arm.

## Columns

- digester_id: label of the physical reactor (DG01 to DG12).
- pretreatment: inoculum treatment assigned to that reactor, "control" or
  "thermal"; constant within a digester.
- session_day: run day on which the sample was drawn (6, 10, 14 or 18).
- ch4_yield_ml_per_g_vs: specific methane yield for that session, in millilitres
  of methane per gram of volatile solids fed.
- digestate_ph: pH of the digestate in the same sample.
- vfa_acetate_mg_per_l: acetate concentration in the digestate, mg per litre.

## Intended use

Any comparison between the control and thermal arms should be made at the level
of the digester. The usual route is to average each vessel's four session yields
into a single vessel-level value and then compare the twelve vessel-level values
between arms, so that each independent reactor contributes exactly one number to
the comparison.
