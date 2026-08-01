# Experiment 0024: Static qualification implementation validation

- **Status:** Completed; focused independent revalidation passed
- **Date:** 2026-07-30
- **Governing decision:** Accepted ADR-0022 and public schema v0.15.0
- **Production detector or Finding authority:** None

## Question

Does the implemented static qualification path enforce the complete frozen snapshot and
case-selection boundary independently of the production detector, without importing or executing
project-authored code?

## Initial independent result

A fresh-context implementation review found two material fail-closed defects despite the existing
green suite:

1. candidate enumeration followed only files still present under the materialized snapshot, so
   deleting a disqualifying `.py`/`.csv` pair while retaining its original FileRecords could turn
   an ambiguous proof into a complete proof; and
2. an opaque case assignment could name a different selection-protocol identity from the protocol
   frozen into its StaticQualificationProfile.

Both defects affected proof authority and were fixed before completion. They were not treated as
documentation or cosmetic issues.

## Correction

The answer-side verifier now:

- derives the complete candidate set from the supplied snapshot-bound FileRecord and
  AssetIdentity inventories rather than from currently visible files alone;
- requires one-to-one FileRecord/AssetIdentity closure, rederives every file and identity ID, and
  recomputes the RepositorySnapshot digest and ID from the full inventory;
- requires the materialized `.md`, `.py`, and `.csv` set to equal the complete committed candidate
  set before reading or interpreting any candidate;
- rehashes every candidate's full bytes and preserves missing or changed materialization as an
  unavailable proof;
- requires the case assignment to bind both the exact selection-protocol artifact ID and digest
  frozen into the profile; and
- performs the protocol check before inspecting case bytes.

## Independent revalidation

The same independent reviewer reran both original reproductions after the correction:

- deleting the second supported closure preserved `proof_status: unavailable`, with
  `candidate_enumeration_complete: unavailable` because the materialized candidates no longer
  equaled the snapshot inventory;
- omitting the candidate and its identity from the supplied manifest failed the recomputed
  snapshot digest;
- a different selection-protocol ID was rejected before source inspection; and
- the project-authored side-effect marker remained absent throughout.

The reviewer reported **PASS** with no remaining broad architecture or epistemic blocker in the
focused path. The isolated verifier and fixture suites passed after the change.

## Test, acceptance criterion, and remaining limitation

- **Tests added:**
  `test_snapshot_candidate_removal_cannot_narrow_an_ambiguous_case`,
  `test_snapshot_manifest_omission_cannot_narrow_candidate_inventory`, and
  `test_case_assignment_must_name_the_profile_selection_protocol` in
  `tests/test_static_qualification_verifier.py`; plus canonical JSONL/disposable-SQLite round-trip
  coverage for both new public proof records in `tests/test_evaluation_control_fixture.py`.
- **Acceptance criterion satisfied:** removal or omission of a required snapshot candidate cannot
  strengthen a proof, a case assignment cannot escape its pre-frozen selection protocol, proof
  replay remains deterministic, and no project code or model establishes a material premise.
- **Remaining limitation:** this is synthetic mechanism and adversarial-mutation evidence. It is
  not an authenticated real answer-blind panel, a numerical threshold decision, a detector
  qualification, a maintainer promotion, or production Finding permission. The first verifier
  still covers only the exact bounded raw-two-group-mean/static-writer/report-direction grammar.
