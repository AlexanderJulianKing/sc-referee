# AURA-7 Commissioning: Slot Failure Intensity

## Instrument and campaign

The AURA-7 adaptive-optics bench was commissioned over 14 observing blocks of
12 scheduled slots each, one slot per closed-loop acquisition attempt, spread
over 6 detector channels. A slot counts as a failure when the closed loop does
not hold for the full acquisition.

## Planned-unit accounting

- Planned commissioned slots: 168
- Retained after telemetry screening: 126
- Removed by telemetry screening: 42
- Failure events among retained slots: 21

Removal reasons: clock_desync 14, packet_crc_error 14, telemetry_dropout 14.
Failure modes: focus_drive_runaway 7, readout_timeout 7, shutter_stall 7.

## Governing scope records

Two signed scope records govern this workflow. Both are executed originals,
both are unamended, and both carry equal authority.

- Scope Record A, "Commissioning Scope of Work" (signed): the analysis
  population is every commissioned slot, 168 slots.
- Scope Record B, "Telemetry Validation Annex" (signed): the analysis
  population is the valid-telemetry slots only, 126 slots.

Neither record is dated relative to the other, neither amends the other, and
neither contains a precedence, supremacy, or order-of-control clause. Nothing
in the record set resolves which population governs, and this workflow does
not designate either record as controlling.

## Failure intensity

The selected intensity uses the 126 valid-telemetry slots as its denominator,
which is the population described by Scope Record B; this choice of
denominator is stated here as the reported basis, not as a ruling that Scope
Record B outranks Scope Record A.

- Failures per valid-telemetry slot: 0.1667 (21 / 126)
- Failures per 100 valid-telemetry slots: 16.6667

Reported for contrast and not selected: over the 168 commissioned slots of the
Scope Record A population, the same 21 failures give 12.5000 failures per 100
slots. The two records thus support two different intensities and the conflict
between them remains unresolved here.

[selected-result] Failure intensity 16.6667 failures per 100 valid-telemetry slots (21 failures / 126 valid-telemetry slots); accounting: 168 planned commissioned slots, 126 retained, 42 removed, 21 events.

## Reproducibility

All counts and rates above are computed from inputs/data.csv by
workflow/analysis.py. The script is deterministic: no randomness, no clock, no
network, no arguments.
