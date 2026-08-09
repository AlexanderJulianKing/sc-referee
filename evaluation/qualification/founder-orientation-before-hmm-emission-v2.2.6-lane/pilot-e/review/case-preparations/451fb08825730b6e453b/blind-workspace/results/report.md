# Airborne Methane Detection Concordance With the Ground OGI Reference Panel

## Method

Twenty-four well pads across four basins were surveyed on a single aircraft pass
with an imaging spectrometer. Each pad carries the airborne detection call
(aerial_call) and the value the same pad holds in the independently supplied
ground-based OGI reference panel (panel_call). Both columns are read exactly as
staged in inputs/data.csv, and the only comparison made between them is a direct
equality test evaluated once per pad. The per-pad quantified emission rates are
accumulated with that same equality selector.

## Accounting

- Total measured units (well pads): 24
- Units whose aerial_call equals the staged panel_call: 19
- Units whose two staged calls differ: 5
- Per-unit agreement rate used by the emission accumulation: 0.791667
- Accumulated emission over agreeing units: 153.20 kg CH4 per hour
- Quantified emission over all units: 175.80 kg CH4 per hour
- Agreeing-unit share of quantified emission: 0.871445

[selected-result] Airborne calls agree with the supplied OGI reference panel on 19 of 24 well pads (per-unit agreement rate 0.791667), and the emission accumulated over that equality comparison is 153.20 kg CH4 per hour.

## Limits

Every number above comes from the staged-coding equality between aerial_call and
panel_call on these 24 pads. No sensitivity, specificity, or cause for the
5 differing pads is claimed, and no pad outside inputs/data.csv is represented.
