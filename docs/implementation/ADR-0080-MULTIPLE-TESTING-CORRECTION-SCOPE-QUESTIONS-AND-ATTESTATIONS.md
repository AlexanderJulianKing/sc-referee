# ADR-0080: Multiple-testing correction-scope questions and asymmetric attestations

- **Status:** Accepted
- **Date:** 2026-08-29
- **Acceptance provenance:** Alex approved the 3.1 design; adversarial review approved build
  conditional on Revision 1a MJ-1/MJ-2
- **Decision owners:** Alex / sc-referee maintainers
- **Scope:** Development-only multiple-testing question and attestation layer `3.1.0`
- **Companion design:**
  `docs/implementation/MULTITEST-3.1-SCOPE-QUESTIONS-ATTESTATION-DESIGN-2026-08-29.md`,
  Revision 1a, raw SHA-256
  `55161e9afd5d4ba890e851217a03d14fd494bdf4d8bb37122bf975dd29fc8cb7`
- **Execution impact:** None; project-authored code remains unexecuted
- **Production impact:** None; questions and attestations grant no Finding, qualification,
  promotion, or scoring authority

## Context

Multiple-testing 3.0 conservatively abstains when it positively locates a correction-shaped
operation but cannot prove its complete-family scope. That evidence is useful to a reviewer, but an
abstention alone does not expose the material unknown. The accepted public schema already keeps
`Finding`, `ConditionalConcern`, `MaterialQuestion`, and `Disclosure` distinct and provides an
`Answer` record for explicit human input.

The symmetric trust policy—accepting either an incomplete-scope or complete-scope author statement
as classification evidence—would create two unacceptable errors. Treating an admission of
incomplete scope as a tool Finding would be a false accusation by provenance. Treating a
self-serving completeness statement as clearance would be false clearance. The second failure has
the same zero-tolerance standard as the first.

## Decision

1. Advance only the development multiple-testing check, adapter, and detector identities to
   `3.1.0`. The frozen 3.0 analyzer selects its source outcome first, and the additive question
   layer never changes that module classification.
2. Exactly these five first reasons are eligible for a correction-scope question:
   `correction-family-lineage-unresolved`, `record-family-lineage-unresolved`,
   `record-family-mutation-unresolved`, `unresolved-decision-threshold`, and
   `unresolved-manual-correction-present`. A reason name is necessary but insufficient. One exact
   reason-associated `CorrectionScopeWitness` under the closed grammar is also required.
3. The witness grammar admits only a registered correction call, a closed callee-terminal
   correction call, closed manual adjusted-p arithmetic, closed manual decision-threshold
   arithmetic, or a closed record correction store. The correction occurrence must be p-derived,
   associated with the frozen first reason and authorized family, unique after structural
   dominance, and bounded by the declared family size. Code AST, registered identities, contract
   columns, source coordinates, and digests are evidence; comments, docstrings, report prose,
   variable prose, and source excerpts are not.
4. An eligible witness produces a development-only `DetectorResult` with
   `state=material_question_candidate`, one closed `MaterialQuestion`, and one linked open
   `ConditionalConcern`. The visible template has only source-span position and contract family
   size slots. It asks whether the located correction covers all declared outcomes; it does not
   assert that correction is incomplete.
5. Attestations enter only through an explicit, external `--attestations` JSON file. The file is
   closed-schema, noninteractive, outside the audited project, regular and non-symlink, limited to
   one MiB and one answer, and bound to the exact question ID, source snapshot digest,
   `analysis.py` content digest, question-evidence digest, and authority-binding digest. Any
   validation failure refuses the complete input and publishes no partial bundle.
6. Answer A—correction does not cover the full family—is stored as a public `Answer` plus a
   `ConditionalConcern` whose report label is exactly
   `Author attestation — not a tool Finding`. Its premise remains `unknown`; it has no severity and
   cannot create a Finding or scoring catch.
7. Answer B—correction covers the full family—is an untrusted pointer only. Its supplied source
   span selects one root for the existing 3.0 structural proof. The supplied factor is retained as
   a claim receipt and never enters value resolution. No correction API, terminal, arithmetic,
   factor, container, record, threshold, helper, or consumer grammar is added. A successful proof
   requires complete corrected positions and corresponding conclusions under the unchanged checks.
   A failed proof creates a non-accusatory `Disclosure` and leaves the question open.
8. Every successful B fixture has an answer-removal-equivalence companion. Removing the Answer and
   invoking the same existing proof at the now-known node must yield the identical corrected-position
   set. Any answer-guided position not independently available is answer laundering and stops the
   build or replay.
9. A B answer alone can never create a Finding, candidate accusation, verified-correct statement,
   new corrected position, qualification, promotion credit, or suppression of another check's
   Finding. An A answer can never be described as tool-demonstrated.
10. Question and answer identities exclude timestamps and output paths where specified and bind
    all content identities. Identical source, authority, registry, clock fixture, attestation bytes,
    and options replay byte-identically. Answers never carry forward automatically to another
    snapshot.

## Record and wording boundary

No fifth public assessment type is introduced. The existing public records retain these meanings:

- a `Finding` is a tool-demonstrated issue and is never produced here;
- a `MaterialQuestion` is the unresolved scope question;
- a `ConditionalConcern` records a consequence conditional on an unresolved or author-reported
  premise;
- a `Disclosure` records an unverified B claim with `non_accusatory=true`; and
- an `Answer` records the human statement and its exact authority/provenance boundary.

The question wording object is
`material-question:multiple-testing-correction-scope-v1@1.0.0`. Its only slots are
`AUTHORIZED_COUNT` and `SOURCE_LOCATION`, where the location is rendered from structured position
facts as `analysis.py:<line>:<column>`. The source reason, method name, tokens, comments, report
language, answer prose, and case labels never enter visible question wording.

## Scoring and isolation

Blind-envelope scoring is unchanged. Blind cases provide no attestation file; questions, concerns,
answers, and disclosures are not catches and do not change promotion arithmetic. The question
count is an auxiliary usability measure only.

The qualified lane, pseudoreplication components, GrantPins, grants, qualifications, metric sets,
threshold policies, historical Finding wording, and all 3.0 and older multiple-testing modules stay
byte-untouched. No qualified record or Finding byte may derive from the development-inclusive
registry digest.

## Validation and stop rule

The first executed 140-case question census is authoritative. The design's `14/90 + 10/50 =
24/140` count is a hand-derived projection and is re-pinned from executed output if needed; the
implementation is never tuned toward it. Source outcomes remain byte-equal to 3.0 in all 140 cases.

Build and replay stop on any answer-derived Finding, source-classification change, new corrected
position, B-fails clearance, stale binding acceptance, non-deterministic question census, failure
of the 15 attested replay pairs, generic interaction acceptance of this subtype, or mismatch in an
answer-removal-equivalence fixture. A required positive proof that cannot be obtained from the
unchanged grammar is a design regression, not permission to widen it.

