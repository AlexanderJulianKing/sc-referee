# What is in data/input.csv

This table records a nest-choice survey of the rock ant Temnothorax rugatulus
carried out along one ridge during a single field season. Twenty-four
queenright colonies were located, each living under a different granite
outcrop, and no two sampled outcrops were closer than fifty metres. Each
colony was lifted intact into a plaster arena offering two identical cavities,
one shaded by a dark filter and one left open to ambient light, and was scored
once for the cavity into which it completed its emigration. After scoring, the
colony was returned to its outcrop and was never tested again.

Columns:

- colony_id: the label of the colony; every label appears on exactly one row.
- collection_outcrop: the granite outcrop the colony was taken from; every
  outcrop supplied exactly one colony.
- worker_count: number of workers censused in the colony before the assay.
- assay_temp_c: arena air temperature in degrees Celsius during the trial.
- cavity_chosen: the cavity the colony settled in, "shaded" or "exposed".

One row is: one field-collected ant colony scored once in a single two-cavity nest-choice trial
Independent unit column: colony_id
One trial is: one row

Because a colony is measured a single time and no two colonies share an
outcrop, the table holds no repeated measurements and no nesting. The twenty-
four recorded choices are twenty-four independent yes/no outcomes, which is
exactly what the binomial sampling model in the analysis assumes.
