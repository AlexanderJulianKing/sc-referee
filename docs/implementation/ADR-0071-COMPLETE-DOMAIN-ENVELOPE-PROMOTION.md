# ADR-0071: Promote the exam-time complete-domain envelope

- **Status:** Accepted by the maintainer on 2026-08-10, in session ("Yes. And we should work
  until the pseudoreplication stuff meets the same.")
- **Date:** 2026-08-10
- **Scope:** `check:complete-domain-exposure-denominator` version `2.0.7` under
  `method-conflict-binding:complete-domain-exposure-denominator-v1`, at the exact exam-time bytes
  below. This decision does not promote the detector generally or any sibling binding.
- **Relates to:** ADR-0061, ADR-0066, ADR-0067, ADR-0068, ADR-0070, and Experiment 0056
- **Finding impact:** None in Round 1. The production grant registry remains empty and the
  controller remains disconnected from private qualification records.
- **Execution impact:** None

## Context

ADR-0070 froze a one-shot, seven-cell held-out exam before its labels were observed. The exact
`2.0.7` envelope completed all seven cells on its first and only attempt: two of two demonstrated
errors produced bounded evaluation candidates, and all five controls produced no candidate. The
qualification report records 7/7 complete cases, zero of five false accusations, two of two
sensitivity, deterministic replay, and no execution of project-authored code.

The exam-time tuple is not identical to the live checkout. Commit `444d643` subsequently added an
overflow guard to the quantity-consistency adapter. Commit `63fb0a1` also changed
`scientific_checks/core.py`, whose bytes feed `adapter_common._COMMON_IMPLEMENTATION_DIGEST` and
therefore the adapter identity. Those changes altered the adapter implementation identity while
leaving the recognition grammar digest unchanged. Restoring the pinned exam-time identity would
require more than reverting the overflow guard. A maintainer decision must bind the object actually
examined, not silently inherit later bytes.

ADR-0061 also describes the older full-panel qualification route. Accepted ADR-0066 and ADR-0067
subsequently changed provider composition and review count, and ADR-0068 consolidated the lean
evidence process. The sealed exam has no separate Stage-3 comparison artifact. The promotion
decision therefore has to state whether the retained lean-consolidated evidence is accepted in its
place rather than pretending the older artifact exists.

## Decision

1. **Promote the exact examined binding.** The maintainer promotes
   `check:complete-domain-exposure-denominator` version `2.0.7` under binding
   `method-conflict-binding:complete-domain-exposure-denominator-v1` to the requested and effective
   maturity `validated`. The evidence is the sealed ADR-0070 seven-case exam: 7/7 cases completed in
   one attempt, with two bounded true-positive candidates and zero candidates on five controls.
   This is a binding-level decision, not detector-wide authority.

2. **Pin the exam-time identities.** Authority is limited to this exact set, copied from the frozen
   `heldout-v207-seven-case/authoring/AUTHORING_PROTOCOL.json` and its bound detector manifest:

   - adapter ID/version:
     `adapter:complete-domain-exposure-denominator:quantity-consistency-v1` / `2.0.7`;
   - adapter implementation digest:
     `sha256:87cbc5031db19e9b74b7b294204f0227be60b81176ea814638d6caeb56e3a3bf`;
   - adapter manifest digest:
     `sha256:ad1760c9c84d2141128ceffb8979c122bb649579fd4895ab8bb02e935fcbbe6a`;
   - recognition grammar digest:
     `sha256:c757692071a6925a5ca5e409dc0ad79f7421fcdbc93fb15c14efb30050524362`;
   - detector tuple digest:
     `sha256:c0d6ec05c8e24e04e4382430e3bfa7fa4086bef016df218f28b907542f2ca3c3`;
   - production binding digest:
     `sha256:f0b46686e0c5a4ff137cc43b4729fc6194e7aa550565bf4f9fe637f2480262ed`;
   - detector manifest digest:
     `sha256:a8e8bdf16e847745276a3d8da0bc2ba44062e42293e1f3185c9ccf9a19abecbc`;
   - check manifest digest:
     `sha256:c3ef7acd8597c86e8a121ba43e94d4f2a2993c08cd2c14981b85b13c431841a9`;
   - exam-time scientific-check registry content digest:
     `sha256:5ecad5ee3773c6ee5ae7686b6aa2e189ef65d1e4b56c816348564d6eec647fe9`.

3. **Exclude drifted live bytes from Round 1.** Commit `444d643` changed the adapter implementation,
   and commit `63fb0a1` changed `scientific_checks/core.py`, which contributes through
   `adapter_common._COMMON_IMPLEMENTATION_DIGEST` to the adapter's computed identity;
   the current scientific-check registry records implementation-file digest
   `sha256:cb6de94e39efdf726cc516178b77b85443044415b72c8671025ef9c2e6eef05c`,
   while the recognition grammar remains the pinned
   `sha256:c757692071a6925a5ca5e409dc0ad79f7421fcdbc93fb15c14efb30050524362`.
   The authority in this ADR applies only to the pinned exam-time bytes. HEAD bytes are outside the
   Round-1 grant. Live production use requires a fresh sealed confirmation on current bytes or an
   explicit follow-up maintainer ruling.

4. **Translate the pre-label threshold without changing its meaning.** ADR-0070's zero-of-five
   control false-accusation bar maps to
   `completed_opportunity_false_positive_rate`, the fixed compiler metric that counts unsafe
   projected candidates among completed detector opportunities, with statistic `estimate`,
   operator `at_most`, and threshold `0.0`. Its sensitivity bar maps to
   `adjudicated_root_recall`, with statistic `estimate`, operator `at_least`, and the frozen
   threshold `0.5` (at least one boundedly localized root of two). The observed two-of-two result,
   or `1.0`, remains an achievement in the metric set and is not rewritten into the pre-label
   policy. The minimum counts equal the frozen
   exam: 7 workflows, 7 distinct problem clusters, 2 adjudicated roots, and 5 control cases. The
   policy uses estimate-only decisions and sets `require_estimable_intervals` to `false`: seven
   clusters are too few to make bootstrap interval bounds the accepted decision rule, although the
   metric set still reports the cluster-aware intervals and their limitations.

5. **Reconcile every ADR-0061 promotion gate explicitly.** Their status for this one binding is:

   - pre-case profile and opaque assignment: satisfied by the retained lane freeze, sealed
     assignments, held-out opening, and exam-time authoring protocol;
   - fresh error, corrected, valid-alternative, hard-negative, ambiguous, unsupported, and renamed
     forms: satisfied by the seven frozen roles and label ledger;
   - four blind Stage-1 reviews across two providers and two fresh Stage-2 adjudications:
     superseded by accepted ADR-0067's lean review with escalation, with the two-provider
     requirement separately superseded by accepted ADR-0066;
   - independent static proof and fresh Stage-3 comparison: the seven detector audits are static,
     digest-locked, and replayed, but a separate Stage-3 comparison artifact does not exist. The
     maintainer accepts the disclosed lean-consolidated audit and review evidence in its place for
     this binding;
   - pilot-informed threshold frozen before held-out labels: satisfied by ADR-0070 and the held-out
     opening chronology;
   - recomputed clustered metrics passing all counts and thresholds: satisfied by the private
     Round-1 QualificationMetricSet derived from the digest-bound detector ledger;
   - public qualification report and explicit maintainer promotion: satisfied by the retained
     `QUALIFICATION_REPORT.md` and this decision; and
   - accepted forward public schema plus installed content-addressed grant: intentionally not yet
     satisfied. It remains the Round-2 production-authority gate.

6. **Record private proof without installing authority.** Round 1 retains an evaluation-private
   DetectorQualification and QualificationMetricSet, proves that the existing fail-closed resolver
   returns one `validated` grant for the pinned binding, and leaves
   `qualification-manifests.json` byte-identical and empty. The detector manifest remains
   `experimental`, every production binding retains `production_finding_permitted: false`, the
   public capability matrix is unchanged, and no controller path consumes the private records.
   The resolver's closed vocabulary has no value for one calibrated agent reviewer with escalation,
   so the record retains `review_basis: agent_panel`; ADR-0067's one-review-with-escalation design
   and the retained review ledgers provide the more precise disclosure. The
   `regression_fixture_for_every_discovered_false_accusation` and
   `unresolved_disagreement_excluded` gates are vacuously true for this exam: no false accusation
   was discovered and no unresolved disagreement existed, so there was nothing to fixture or
   exclude.

7. **Make Round 2 a separate authority change.** Round 2 requires all of: public acceptance of
   schema v0.19.0; installation of a content-addressed qualification grant whose threshold-policy
   digest is pinned to an externally recorded value rather than accepted from a self-consistent
   record (the Round-1 resolver otherwise permits a policy mutation accompanied by digest refresh);
   production-controller wiring; resolution of the adapter digest drift for the live bytes; and a
   floor-independent missed-root check before this policy is reused with more positives. The
   current `adjudicated_root_recall` denominator counts only resolved roots, so a missed root can
   fall out of that denominator. None of these gates may be inferred from the Round-1 resolver test
   or the delivery-plan promotion checkbox.

## Consequences

- The honest delivery score records one maintainer-promoted envelope, backed by the exact private
  qualification pair and sealed exam, while the installed-product and production-Finding score
  remains zero.
- The private projector is digest-bound to the frozen detector ledger and never modifies any held-
  out file. It preserves the unsupported and ambiguous controls as noncandidate outcomes and
  stratifies all five controls in the accepted static closed-scope family.
- The separate Stage-3 artifact remains explicitly absent. This ADR records the maintainer's
  acceptance of the lean substitute; it does not rewrite history or generalize that exception.
- Zero observed false accusations is evidence for this narrow binding and tuple, not a correctness
  certificate, domain-wide validation, or authority for later adapter bytes.
- Any Round-2 implementation that cannot re-establish the exact digest and schema gates must fail
  closed without installing the grant.
- The Round-1 root-manifest regeneration expanded the tracked inventory from 4,726 to 13,043 files
  and repaired 40 pre-existing stale parent-manifest rows, including rows for `registry.json`,
  `scientific_checks/core.py`, and `scientific_checks/profiles.py` even though those files did not
  change in the Round-1 work. That repair records parent-manifest staleness, not content drift or
  an expansion of the promotion decision.
