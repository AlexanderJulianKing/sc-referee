# ADR-0038: Use scoped verified-good and hard-negative fixture classes

## Status

Accepted.

## Context

A correct final answer, one canonical workflow, and a global “gold” label do not establish that an analysis is defensible or free from a named issue.

## Decision

Evaluation distinguishes `verified_good_fixture`, `scope_verified_good`, `hard_negative_fixture`, `positive_issue_fixture`, and `ambiguous_fixture`. Every negative label declares exact scope and proof obligations. Hard negatives document the suspicious pattern and decisive innocent explanation. No fixture permits a global correctness claim. See SA-FR-064 and SA-FR-098.

## Consequences

- False-accusation tests are explicit and reusable.
- Real HPC workflows can be verified narrowly without overclaiming.
- Noncanonical but defensible workflows become first-class controls.
