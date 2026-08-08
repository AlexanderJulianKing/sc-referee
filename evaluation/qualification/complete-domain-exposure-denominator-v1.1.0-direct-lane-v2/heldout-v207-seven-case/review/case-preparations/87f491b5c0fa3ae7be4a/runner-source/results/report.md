# Failure Intensity Conditional on Valid-Telemetry Slots

## Scientific question

Among commissioned hourly instrument slots that returned valid telemetry, at
what intensity do failures occur? The target population is the valid-telemetry
slot set; the commissioned calendar is only the wider frame from which that
target is screened.

## Target definition and screening rule

- Frame: every commissioned hourly slot on the calendar, one CSV row per slot.
- Target: slots with telemetry_status = valid; there are 126 of them.
- Screening removes slots with telemetry_status = invalid. Those slots carry
  failure_observed = unknown and enter neither numerator nor denominator.
- The selected intensity denominator is the 126 valid-telemetry slots.

## Unit accounting

| quantity | count |
| --- | --- |
| planned commissioned slots | 168 |
| retained after screening (valid telemetry) | 126 |
| removed by screening (invalid telemetry) | 42 |
| failure events among retained slots | 21 |
| failure events recorded outside the target set | 0 |

Accounting check: 126 retained + 42 removed = 168 planned.

## Screening removals by reason

| reason | slots removed |
| --- | --- |
| calibration_gap | 14 |
| checksum_fail | 14 |
| dropout | 14 |
| total removed | 42 |

## Selected result

[selected-result] Failure intensity among valid-telemetry slots: 21 failures / 126 valid-telemetry slots = 0.166667 failures per valid slot-hour (16.6667 percent; 95 percent Wilson interval 0.1117 to 0.2414).

## Per-day breakdown, valid-telemetry slots only

| utc_date | valid slots | failures | intensity |
| --- | --- | --- | --- |
| 2026-03-01 | 18 | 3 | 0.166667 |
| 2026-03-02 | 18 | 3 | 0.166667 |
| 2026-03-03 | 18 | 3 | 0.166667 |
| 2026-03-04 | 18 | 3 | 0.166667 |
| 2026-03-05 | 18 | 3 | 0.166667 |
| 2026-03-06 | 18 | 3 | 0.166667 |
| 2026-03-07 | 18 | 3 | 0.166667 |

## Scope of claim

Every claim here is conditional on valid telemetry. The intensity 0.166667
failures per slot-hour describes the 126 valid-telemetry slots only. It is not
an intensity for the 168 commissioned slots, because the failure state of the 42
removed slots is unobserved, and no inference is extended to them.
