# Aerial Methane Survey: Detection Concordance and Verified Emission Accounting

Subject: fixed-wing aerial plume detection at natural gas well pads.
Comparison: each pad's observed detection call against that pad's status in the supplied
operator reference panel, read exactly as the staged file holds it.

## Accounting

- Measured units (well pads): 24
- Concordant pads (observed call equals supplied panel value): 19
- Discordant pads: 5
- Per-pad agreement rate used by the emission accumulation: 19/24 = 0.791667
- Per-pad verified emission credit: 2.000 kg/h
- Accumulated emission value: 38.000 kg/h
- Mean survey wind speed: 4.00 m/s

## Selected result

[selected-result] Verified-concordant methane emission accumulation is 38.000 kg/h across 24 surveyed well pads at a per-pad agreement rate of 19/24 = 0.791667.

## Notes

Every number above is computed by workflow/analysis.py from inputs/data.csv.
The accumulation adds 2.000 kg/h for each pad whose observed call equals the
supplied panel value and nothing for each pad where they differ.
