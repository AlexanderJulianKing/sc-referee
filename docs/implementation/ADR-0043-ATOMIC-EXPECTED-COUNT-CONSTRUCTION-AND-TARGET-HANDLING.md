# ADR-0043: Add atomic expected-count construction and focal-target handling checks

- **Status:** Accepted under the repository owner's standing approval for minor ADRs and schemas
  that do not change authority or Finding policy
- **Date:** 2026-07-31
- **Coordinated public schema release:** None; schema `0.17.0` is unchanged
- **Related decisions:** Accepted ADR-0018 through ADR-0020 and ADR-0042
- **Finding impact:** None; both checks are question-only and have no detector binding
- **Execution impact:** None; inspection remains static and project-authored code remains disabled

## Context

Experiment 0025's answer-isolated Hi-C workflow explicitly reported two method choices: it used a
per-replicate same-distance arithmetic mean as expected count, and it included the focal pixel in
that background. The existing ADR-0018 claimless obligation correctly asked which complete
six-dimension expected-count profile governed, but it retained no normalized reported operand.
Even after a human supplied the benchmark-authorized profile, that branch could not compare the
two visible choices because the report remained outside the complete-profile grammar.

An answer-aware evaluator-owned golden workflow independently implemented the official masked
negative-binomial estimator and reproduced all three expert-key values within about `1e-9`, far
inside the `0.02` tolerances. A separate static method reviewer accepted that workflow and found no
material method defect or answer leakage into estimation. The original candidate missed all three
fields and openly declared the same-distance, target-inclusive shortcut. This supplies a concrete
development case, not production scientific authority.

The complete `expected_count_background_v1` profile should not be weakened merely to serialize a
partial or unsuitable method. The reusable need is instead to represent two atomic method choices
that occur across domains: how an expected background is constructed, and whether the focal
observation contributes to its own background.

## Decision

Add two independent, release-manifested selected-Markdown checks through ADR-0042's existing
extension boundary:

1. `check:expected-count-background-construction` under `measurement_model`, comparing the closed
   scalar operands `same_stratum_arithmetic_mean_expected_count` and
   `negative_binomial_glm_predicted_expected_count`.
2. `check:expected-count-focal-target-handling` under `selection_process`, comparing the closed
   scalar operands `include_focal_target_in_expected_count_background` and
   `exclude_focal_target_from_expected_count_training`.

Each adapter recognizes only enumerated explicit primary-method wording in the exact selected
Markdown surface. It retains exact source spans and full-digest scope, fails closed on partial or
conflicting declarations, and does not interpret sensitivity-only target exclusion as the primary
method. The two axes remain independent because a model prediction can still leak its target and a
same-stratum mean can still be leave-one-out.

Each applicable check emits a Finding-ineligible observed assertion and a bounded
analysis-scoped MaterialQuestion. Only a human Answer may establish the review-scoped requirement.
An exact mismatch may then produce the existing deterministic material compatibility Disclosure;
it is not a Finding and does not establish execution, historical intent, numerical causality, or
universal scientific correctness.

The checks receive no `MethodConflictBinding`, no static-source adapter, no qualification profile,
and no production Finding permission. The official GeneBench report and answer key remain
development-evaluation evidence only. They are not production audit inputs and are not silently
promoted to authority for unrelated studies. The broader claimless six-dimension obligation
remains available and unchanged for unresolved covariates, grouping, resolution, masking, and
other method details.

The v0.2 pre-case qualification freeze continues to bind the founder check and the registry-file
digest that existed at freeze time. Its reconstruction builder verifies the exact frozen binding
digest but does not rebind that historical artifact to the current whole-registry digest. This
allows unrelated question-only sibling modules to be appended without mutating or invalidating the
already frozen candidate; any change to the founder binding itself still fails reconstruction.

## Alternatives rejected

### Allow target inclusion inside `expected_count_background_v1` without a version change

Rejected because that would silently change an accepted complete-profile meaning and conflate
representation of one atomic disagreement with the profile's stronger completeness contract.

### Add one Hi-C-specific “correct method” detector

Rejected because the reusable scientific relations are background construction and information
separation, not the assay label. Available count tables, GC, mappability, or restriction-site
columns cannot nominate a negative-binomial model.

### Treat answer-key mismatch as the Finding

Rejected because numeric disagreement does not by itself establish method cause or production
scientific intent. The answer-side comparison remains controlled development evidence.

## Test, acceptance criterion, and remaining limitation

- **Tests added:** exact same-stratum and negative-binomial declarations; exact target inclusion
  and exclusion declarations; simultaneous independence of both axes; partial, lookalike, and
  conflicting hard negatives; scientist-Answer incompatibility on each axis; and semantic-lock and
  rendered-report replay. The pre-case reconstruction test also proves that unrelated live-registry
  growth leaves the historical freeze byte-identical while its exact binding remains guarded.
- **Acceptance criterion satisfied:** the preserved flawed Hi-C report now yields both exact
  observed operands and bounded questions. Under the repository owner's answer-key-backed review
  decisions, separate linked segments produce exact material incompatibility Disclosures for the
  construction and target-handling axes, with byte-identical semantic locks and reports on replay.
- **Remaining limitation:** coverage is explicit selected-Markdown wording only. The checks do not
  parse arbitrary paraphrases, prove which code ran, validate masks or covariates, attribute a
  numeric error, choose a governing method, or emit a production Finding. The complete expected-
  count profile remains unresolved unless separately supplied.
