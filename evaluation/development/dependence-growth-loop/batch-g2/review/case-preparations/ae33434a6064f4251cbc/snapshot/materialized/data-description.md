# Limpet thermal tolerance survey

Twelve rocky-shore limpets were collected by hand from a single granite shore
platform: six from the low-shore zone, which is submerged for most of the
tidal cycle, and six from the high-shore zone, which is exposed to air and sun
for long stretches. Each animal was held in a common flow-through aquarium and
then placed in a heated seawater bath on four consecutive days. On each day
the bath temperature was raised at a steady rate and the temperature at which
the animal lost its grip on the substrate was recorded as its critical thermal
maximum for that ramp. Every animal therefore appears in the file four times,
once per ramp day, and the four values for an animal are repeated readings of
the same individual rather than readings of four different animals.

Columns:

- `limpet_id`: tag code of the individual animal, LP01 through LP12.
- `shore_zone`: tidal zone the animal was collected from, `low` or `high`.
- `trial_no`: which of the four ramp days the reading came from, 1 to 4.
- `shell_length_mm`: shell length of the animal in millimetres, measured once
  at collection and repeated on each of that animal's rows.
- `ctmax_c`: critical thermal maximum in degrees Celsius for that ramp.

One row is: one heated-bath temperature ramp of one limpet on one day
Independent unit column: limpet_id
