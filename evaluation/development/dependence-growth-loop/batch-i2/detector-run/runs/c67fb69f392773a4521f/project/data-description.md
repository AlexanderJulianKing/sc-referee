# Rain garden infiltration surveys

Sixteen street-side rain gardens in the Lower Kepple stormwater district were retrofitted during the same construction season. Every garden contains two cells of equal footprint, side by side and fed from the same kerb inlet: one cell whose soil was blended with green-waste compost, and one untreated reference cell. Field crews revisited each garden three or four times across the following summer, and on every visit they ran a double-ring infiltrometer once in each cell.

`data/input.csv` stores those visits in long format: one line per visit, with the two cell readings from that visit sitting on the same line.

Columns:

- `garden_id` - label of the rain garden that was visited (RG-01 through RG-16).
- `survey_round` - which visit to that garden the line describes (1, 2, 3 or 4).
- `rainfall_prior_7d_mm` - rain recorded at the district gauge during the seven days before the visit, in millimetres.
- `amended_mm_per_h` - steady infiltration rate measured in the compost-amended cell on that visit, in millimetres per hour.
- `reference_mm_per_h` - steady infiltration rate measured in the untreated reference cell on that visit, in millimetres per hour.

One row is: one infiltrometer visit to a single rain garden, holding the paired amended-cell and reference-cell readings taken during that visit

Independent unit column: garden_id

Repeated visits to the same garden re-measure the same construction, the same soil profile and the same inlet, so they are not separate independent cases; only the gardens themselves were sited and built independently of one another. An analysis should reduce each garden's visits to a single value before testing, which leaves sixteen values for sixteen gardens. The number of visits is not balanced across gardens, because four sites were inaccessible during the third survey round.
