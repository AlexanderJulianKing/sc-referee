# Berth 7 four-year gauge survey

Berth 7 is a steel sheet-pile quay wall. Twelve pilings along the berth were
picked for a coating trial: alternate pilings were recoated with the yard's
usual coal tar epoxy, the others with a glass-flake polyester system. Four
years later a diver crew re-gauged every piling with an ultrasonic thickness
probe at four fixed depth bands below mean sea level, and each reading was
turned into an average annual thickness loss.

The table holds one line per gauge reading, so a single piling appears on four
consecutive lines - once for each of its depth bands. All four readings from a
piling share that piling's coating system, its position on the berth, and its
exposure to the tide and to passing traffic.

Columns:

- piling_id: which piling was gauged, PIL-01 through PIL-12.
- coating_system: the protective system that piling carries, either
  coal_tar_epoxy or glassflake_polyester. A piling carries the same system on
  every one of its readings.
- depth_band_m: depth of the gauge spot below mean sea level, in metres. The
  same four bands (0.5, 1.5, 3.0, 5.0) were used on every piling.
- wall_thickness_mm: steel wall thickness left at that spot, in millimetres,
  against a 14.00 mm as-built wall.
- corrosion_rate_um_per_yr: thickness loss at that spot averaged over the four
  service years, in micrometres per year. This is the response of interest;
  bigger numbers mean the steel is being eaten away faster.

One row is: one ultrasonic thickness reading on one piling at one depth band
Independent unit column: piling_id
