# Leaf-disc necrosis assay in chestnut saplings

Eight potted chestnut (Castanea sativa) saplings of the same seed lot were grown in a
glasshouse for six weeks under one of two soil moisture regimes: `saturated`, in which
pots stood in flooded trays, or `drained`, in which pots were free-draining. Four
saplings were assigned to each regime.

After the growth period, three leaf discs were punched from three separate mature leaves
of each sapling. Every disc was floated on a standard zoospore suspension of the root-rot
oomycete under identical incubation conditions and scored once, 96 hours later, as either
`necrotic` (a visible spreading lesion covering more than a quarter of the disc) or
`intact` (no spreading lesion). Discs were scored by a single reader working from coded
labels.

Columns in data/input.csv:

- `disc_id`: the label of the individual leaf disc (D01 through D24).
- `sapling_id`: the label of the sapling the disc was punched from (CH01 through CH08).
- `moisture_regime`: the soil moisture regime applied to that sapling, `saturated` or `drained`.
- `disc_area_mm2`: the measured area of the punched disc, in square millimetres.
- `necrosis_score`: the 96 h outcome for that disc, `necrotic` or `intact`.

One row is: one inoculated leaf disc scored 96 hours after inoculation
Independent unit column: sapling_id
One trial is: one row
