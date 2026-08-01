# Experiment 0003: Post-label detector-output comparison

- **Status:** Active local experiment; not qualification evidence
- **Date:** 2026-07-28
- **Scope:** One frozen scientific label and one complete public AuditBundle

## Purpose

Exercise the accepted Stage-3 chronology without weakening the answer-side root-cause identity
gate. The experiment reveals and binds detector output only after the scientific label freeze, then
records exact detector-result and Finding observations inside the fixture's declared scope.

## Exact envelope

The evaluation-only comparison accepts one public BenchmarkFixture, its exact public
BenchmarkAdjudication, the immutable scientific-label freeze, one complete public AuditBundle, one
detector identity declared by the fixture, and an explicit comparison timestamp. It validates all
public records and requires:

- the fixture, adjudication, and freeze identities, label, and digests to agree exactly;
- the freeze and adjudication to carry the identical typed adjudicated-root-cause references;
- the AuditBundle root AuditRun to resolve the fixture's exact immutable RepositorySnapshot;
- the freeze to state `detector_output_observed:false` and remain self-digest-valid;
- the comparison timestamp to follow the scientific-label freeze;
- every referenced Finding detector-result identity to resolve inside the supplied AuditBundle;
- every selected detector result to share one detector version and manifest digest; and
- Finding scope and detector attribution to use exact public identifiers only.

The canonical comparison record binds the full AuditBundle digest, the selected result and Finding
references, result-state counts, exact in-scope and out-of-scope Finding references, unresolved
scope, mixed-detector attribution, and a self-digest. It records
`detector_output_observed:true` without modifying the frozen label or adjudication.

## Safety boundaries

- The comparison never invokes a model, detector, or project-authored code.
- It does not search for scientific issues or infer equivalence from wording.
- It does not classify an observation as a true positive, false positive, true negative, or false
  negative.
- It is never metric-eligible. Even a canonically admitted scientific label remains unscored until
  detector-to-root-cause equivalence is separately accepted; ambiguous and failed adjudications
  remain excluded.
- A public AuditBundle artifact is required instead of loose detector records. Its schema and
  internal references are checked, but this experiment cannot independently prove that a caller
  did not omit otherwise unreferenced records before constructing the bundle.
- The private comparison record is not added to immutable public schema v0.9.0 or the production
  package.

## Exit evidence

- `test_stage3_comparison_binds_post_freeze_detector_output_without_scoring` verifies exact
  chronology, bundle binding, scope classification, and metric withholding.
- `test_stage3_comparison_rejects_freeze_tampering_or_unresolved_result_refs` verifies fail-closed
  integrity and reference handling.
- `test_stage3_cli_persists_a_canonical_comparison` verifies the isolated CLI and write-once output.

## Remaining limitation

Public v0.9.0 now has canonical answer-side root-cause identity but no public Stage-3 comparison or
detector-to-adjudicated-root-cause equivalence record. Clean-execution grader evidence, calibrated
thresholds, cluster-aware metrics, and real held-out qualification evidence remain absent. An ADR
and later schema revision are required before this experiment may classify outcomes or contribute
to detector promotion.
