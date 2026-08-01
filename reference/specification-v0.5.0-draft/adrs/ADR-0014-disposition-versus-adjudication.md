# ADR-0014: Separate scientist disposition from independent adjudication

- **Status:** Accepted
- **Date:** 2026-07-27

## Context

The scientist is authoritative about intended meaning and may judge materiality or accept risk, but is not automatically authoritative about whether a detector implementation is objectively defective.

## Decision

Scientist dispositions are `confirmed`, `accepted_risk`, `disputed`, `not_material`, `deferred`, or `corrected_in_later_revision`. Objective outcomes—`adjudicated_true_positive`, `adjudicated_false_positive`, `detector_defect`, and `insufficient_evidence`—belong to independent Adjudication records.

## Consequences

A factual scientist answer can change the evidence and recompute an item. A bare disagreement neither erases the record nor becomes a false-positive label.
