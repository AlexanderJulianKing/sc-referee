# Nightly echolocation recordings at two summer bat roosts

A field crew worked at two summer roosts of a small insectivorous bat: an old
quarry adit on the ridge and a road culvert near Halden. Six individually
marked bats were followed at each roost, and every marked bat was recorded on
four separate emergence nights. For each bat on each night the crew counted how
many clean search-phase calls could be extracted from that night's recording and
measured the peak frequency of the call spectrum, in kilohertz.

One row is: one night of echolocation recording from one marked bat at its roost
Independent unit column: bat_id

Columns:

- bat_id: the individually marked bat the recording came from. There are 12
  bats in the file and each one appears on four rows, one per recording night.
- roost_site: the roost where that bat was recorded, either quarry_adit or
  halden_culvert. A bat was only ever recorded at one roost.
- night_index: which of the four recording nights the row describes, 1 to 4.
- calls_analyzed: how many clean search-phase calls were measured that night.
- peak_frequency_khz: peak frequency of that night's call spectrum for that
  bat, in kilohertz.
