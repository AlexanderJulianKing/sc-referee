# Weekly paired methane-yield log from a digester fleet

Five full-scale anaerobic digesters at a municipal water-resource recovery
facility were followed for four consecutive weeks. Each digester is plumbed
with two parallel feed trains: one is fed thermally hydrolysed sludge, the
other is fed the same sludge with no pretreatment. Once per week an operator
walks a sampling round, draws a matched pair of biogas samples (one from each
train of the same digester), and records the specific methane yield of both.
The file therefore holds four weekly sampling sessions for every digester, and
the two yield columns in a row always come from the same digester in the same
week.

One row is: one weekly paired sampling session on a single digester, holding that week's pretreated and control specific methane yields side by side
Independent unit column: digester_id
One trial is: one row

Columns:
- digester_id: label of the digester the session belongs to (D-01 through D-05); the same digester contributes four rows, one per study week
- week: study week number, 1 through 4
- operator_shift: whether that sampling round was walked on the day or the night shift
- pretreated_yield_m3_per_kgvs: specific methane yield of the thermally hydrolysed train, in cubic metres of methane per kilogram of volatile solids fed
- control_yield_m3_per_kgvs: specific methane yield of the untreated control train, same units

Digesters differ from one another in sludge blend, mixing regime and retention
time, so the weekly readings taken from one digester tend to move together.
