# Gearbox acoustic-emission gate comparison

A condition-monitoring team recorded 10-minute acoustic-emission windows from
gearboxes in an operating wind farm. Each stored window was later replayed
through two denoising gates: the baseline spectral gate currently deployed on
the fleet, and an adaptive gate under evaluation. The noise floor reached by
each replay was logged in decibels, together with the wind-speed band that was
in force while the window was recorded.

One row is: one 10-minute acoustic-emission recording window, holding the noise floor reached by the baseline gate and by the adaptive gate on that same window
Independent unit column: gearbox_id
One trial is: one row

Columns:

- `gearbox_id` - identifier of the gearbox the window came from. The same
  gearbox contributed several windows, so this value repeats across rows.
- `window_id` - unique label for the recording window.
- `wind_bin` - wind-speed band during the window (low, mid or high).
- `baseline_floor_db` - noise floor in dB after the baseline spectral gate.
- `adaptive_floor_db` - noise floor in dB after the adaptive gate.

The table holds 20 windows drawn from 6 gearboxes, so the windows are clustered
within a much smaller number of machines.
