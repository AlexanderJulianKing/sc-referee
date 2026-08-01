# ADR-0016: Use user-visible elapsed deadlines and fixed trial mode ceilings

## Status

Accepted.

## Context

An active-compute clock can exclude model, queue, network, installation, or sandbox delays while the scientist still waits. The product must not advertise an interactive ceiling that can be evaded by external latency.

## Decision

The normative clock is user-visible elapsed time. Only time awaiting a scientist response pauses it. Trial cutoff/deadline pairs are quick 120/300 seconds, standard 480/600 seconds, and publication 1500/1800 seconds. Child deadlines cannot exceed the remaining deadline. Modes never escalate automatically; resume creates a linked run segment. See SA-FR-051, SA-FR-052, SA-FR-070, SA-FR-071, and SA-NFR-003.

## Consequences

- Queue and provider latency count against the experience promised to the scientist.
- Partial reports are normal and required.
- Exact durations may change through a later ADR after benchmarking, but no implementation may silently reinterpret the clock.
