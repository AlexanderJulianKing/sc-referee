# Experiment 0004: Exact JSON output grader

- **Status:** Active local experiment; not scientific-label admission or qualification evidence
- **Date:** 2026-07-28
- **Scope:** One explicit JSON Pointer into one immutable full-digest fixture output

## Purpose

Add the first non-executing answer-side grader primitive without allowing final-answer agreement to
stand in for scientific validity. The grader compares one runner-declared JSON value against one
value read from immutable captured bytes.

## Exact envelope

The runner supplies one public BenchmarkFixture, its exact BenchmarkAdjudication, one
content-addressed RepositorySnapshot, matching FileRecords and full-digest AssetIdentities, the
materialized immutable snapshot, and a private grader specification containing exactly:

- the matching case and fixture identities;
- comparison profile `exact_canonical_json_v1`;
- one safe repository-relative JSON file path and RFC 6901 JSON Pointer; and
- one runner-side expected JSON value.

The grader validates every public record, reconstructs the full stable-ID file/identity manifest
and snapshot digest, resolves the fixture snapshot and file identity, rejects symlinks and drift,
parses strict JSON without duplicate keys or non-finite constants, resolves the exact pointer, and
compares canonical JSON encodings. Its write-once result stores value digests rather than the
values, all input identities, the exact match/mismatch observation, explicit non-inferences, and a
self-digest.

## Safety boundaries

- The grader never imports or executes project-authored code.
- No tolerance, rounding, coercion, unit conversion, array reordering, or semantic equivalence is
  inferred.
- A match establishes only equality under the declared JSON pointer and comparison profile. It does
  not establish a valid workflow, correct root cause, defensible estimand, or claim agreement.
- A mismatch does not establish a demonstrated scientific issue.
- The result is not metric-eligible and cannot admit a label or Finding.
- The private grader record is not added to immutable public schema v0.9.0 or the production wheel.

## Exit evidence

- `test_exact_json_grader_observes_match_and_mismatch_without_scientific_inference` verifies both
  exact outcomes, immutable identity binding, and non-execution.
- `test_exact_json_grader_rejects_snapshot_digest_and_pointer_drift` verifies fail-closed snapshot
  and locator handling.
- `test_exact_json_grader_cli_is_canonical_and_write_once` verifies the isolated CLI artifact.

## Remaining limitation

Only strict JSON and exact canonical equality are supported. Scientific tolerances, units,
stochastic outputs, tabular results, execution grading, claim linkage, and correctness metrics need
separate explicit profiles and evidence. This experiment cannot establish detector-to-root-cause
equivalence or promote any detector.
