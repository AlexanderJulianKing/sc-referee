# Pilot-scale anaerobic digestion campaign: weekly reactor monitoring

## What the study did

Twelve bench-scale continuously stirred anaerobic digesters (R01-R12) were operated side by side for an eight-week campaign in a wastewater-treatment research hall. Each digester had its own feed pump, its own sludge line and its own gas meter, and each was randomly assigned to one of two feedstock pretreatments before start-up: `control` (raw thickened waste-activated sludge) or `alkaline` (the same sludge held at pH 10 for six hours before feeding). Six digesters received each pretreatment, and no digester ever changed pretreatment.

After a three-week acclimation period the operators logged one monitoring record per digester per week for run weeks 4 through 8. `data/input.csv` is that log, stored in long format: 12 digesters x 5 weeks = 60 rows.

## Columns

- `reactor_id` - label of the physical digester (R01-R12).
- `pretreatment` - feedstock pretreatment assigned to that digester, `control` or `alkaline`; constant within a digester.
- `run_week` - campaign week the record refers to (4-8).
- `olr_g_vs_per_l_d` - organic loading rate that week, in grams of volatile solids per litre of reactor volume per day.
- `digestate_ph` - pH of the digestate measured at sampling.
- `ch4_yield_nl_per_g_vs` - specific methane yield for that week, in normal litres of methane per gram of volatile solids fed.

## Structure

One row is: one weekly monitoring record for a single pilot digester in a single run week
Independent unit column: reactor_id

Pretreatment was applied to whole digesters, never to individual weeks, and the five weekly records from a digester describe the same physical reactor under the same treatment. A digester therefore contributes five rows to the file but only one independent value to any comparison between the two pretreatments; the weekly records serve to estimate that reactor's steady-state level, not to increase the number of units.
