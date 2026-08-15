# Data description: vessel-noise playback in shore crabs

The file data/input.csv stores the session-level record of a laboratory playback
experiment on shore crabs (Carcinus maenas). Twelve crabs were collected from a
harbour shoreline, held individually in flow-through chambers, and exposed on four
consecutive days to either quiet ambient sound or recorded vessel noise. During the
last minute of every session an observer counted scaphognathite beats, the pumping
movement that drives water over the gills, as a measure of ventilation rate.

Each crab went through two quiet sessions and two vessel-noise sessions. The order
was alternated between animals: odd-numbered crabs began with a quiet session, even-
numbered crabs began with a vessel-noise session. The table is therefore in long
format, with four rows per animal and 48 rows in total.

One row is: one playback session for one crab, holding that crab's ventilation count for that session
Independent unit column: crab_id

Columns:

- crab_id: identifier of the individual crab (CM-01 to CM-12); each crab appears in
  four rows.
- session_index: 1 to 4, the order in which that crab's sessions were run.
- playback_condition: quiet (ambient control) or vessel_noise (recorded vessel pass).
- ventilation_beats_per_min: scaphognathite beats counted in the final minute of the
  session, in beats per minute.
- carapace_width_mm: carapace width of the crab, measured once at capture, so it is
  constant across that crab's four rows.
- seawater_temp_c: seawater temperature in the chamber during the session, in degrees
  Celsius.
- tank_bay: A or B, the holding bay the chamber sat in; fixed for each crab.

How to treat the repetition: rows from the same crab_id are repeated measurements on
one animal and are not independent of each other. Sessions must be averaged within
crab (once per condition) before any procedure that assumes independent rows; the
number of independent units is the number of distinct crab_id values, which is 12,
not the 48 stored rows.
