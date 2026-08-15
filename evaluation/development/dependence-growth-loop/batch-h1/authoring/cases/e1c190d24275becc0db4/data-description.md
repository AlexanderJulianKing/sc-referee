# What is in data/input.csv

This file records a nest-cavity choice assay run on field-collected colonies of the
acorn ant Temnothorax. Twenty colonies were collected from four woodlots, held for a
week under common laboratory conditions, and then each colony was released once into a
test arena that offered two empty nest cavities: one with a narrow entrance and one
with a wide entrance. Whichever cavity the colony had fully moved into 24 hours after
release was recorded as that colony's choice.

Columns:

- colony_id: unique label for the colony. Each colony appears on exactly one row.
- source_woodlot: the woodlot the colony was collected from (four woodlots in all).
- worker_count: number of workers censused in the colony just before the assay.
- arena_temp_c: air temperature inside the arena during the assay, in degrees Celsius.
- chosen_cavity: which cavity the colony occupied, either narrow or wide.
- latency_min: minutes from release until the colony had fully moved into a cavity.

One row is: one field-collected ant colony, assayed once in the two-cavity choice arena
Independent unit column: colony_id
One trial is: one row

Every colony was tested a single time, so the file holds no repeated measurements of
the same colony: the 20 rows are 20 independent observations, one per colony. The
woodlot label is background information about where a colony came from and does not
turn any row into a repeat of another row.
