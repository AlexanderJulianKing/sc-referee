# ADR-0008: Canonicalize answer-side root-cause reconciliation

- **Status:** Accepted
- **Date:** 2026-07-28
- **Proposed schema release:** `0.9.0`
- **Related requirements:** SA-FR-023, SA-FR-097, AC-09, AC-15, AC-43, AC-55–58,
  AC-62, AC-64

## Context

Accepted public schema v0.8.0 records root causes as prose in `AgentReview` and
`BenchmarkAdjudication`. The isolated evaluation package can verify the review panel, provider and
context separation, chronology, exact source evidence, falsification records, and fixture scope.
It cannot verify that differently worded reviews identify the same bounded root cause. Text
similarity, majority vote, and model confidence are not eligible substitutes.

This blocks positive scientific-label admission before detector observation. Reusing one
answer-side canonical identifier in Stage 1 would appear to solve the comparison, but would leak a
proposed answer into the blind review and anchor otherwise independent reviewers. A bare hash of
root-cause prose would instead make equivalent wording compare unequal and would still not
establish scientific equivalence.

## Decision

Publish schema v0.9.0 from immutable v0.8.0 and add a two-level identity protocol.
The release is part of the architecture overhaul and creates no compatibility requirement for the
legacy public GitHub repository.

### 1. Review-local candidate identity

Every `AgentReview` with verdict `demonstrated_issue` carries one closed
`root_cause_identity` object containing:

- a review-local `candidate_root_cause_id`;
- the identity profile `review-local-root-cause-v1`; and
- for Stage 2 only, an exact nonempty set of Stage-1 candidate references that the reviewer
  asserts describe the same bounded root cause.

A candidate reference contains an exact `agent_review` reference and its review-local candidate
ID. The candidate ID is deterministically derived from the case ID, review ID, issue class,
bounded statement, root-cause text, evidence, affected records, and reviewed scope. The evaluator
recomputes it; reviewers cannot choose an unrelated identifier.

Stage-1 reconciliation sets are empty and no canonical identity is disclosed in a Stage-1 packet.
Stage-2 packets contain only the frozen Stage-1 review-local candidates. Each fresh Stage-2
reviewer independently selects the candidates it judges equivalent and supports that selection
with exact evidence and the existing falsification record.

### 2. Public adjudicated root cause

Add a closed public `AdjudicatedRootCause` record containing:

- `adjudicated_root_cause_id`, `case_id`, and identity profile
  `cross-review-candidate-set-v1`;
- the exact Stage-1 candidate-reference set selected identically by both fresh Stage-2 providers;
- the two or more Stage-2 review references that made that selection;
- one bounded statement copied exactly from a named supporting Stage-2 review;
- one exact issue class shared by the admitted candidate set;
- exact evidence and affected-record references;
- explicit required scientific premises and stronger-claim exclusions;
- `material_dissent: false` and `confidence_used_for_identity: false`; and
- provenance and adjudication time.

The canonical ID is a stable digest-derived identifier over the case ID, identity profile, issue
class, and sorted Stage-1 candidate-reference set. It is independent of prose wording. The record
is admitted only when the linked Stage-2 reviews independently select the identical set, that set
contains at least one demonstrated Stage-1 candidate from each required provider family, all
source evidence resolves against the immutable fixture snapshot, falsification survives, and no
material dissent or reversing premise remains.

The identifier records the panel's exact equivalence decision. It does not make that decision
true merely because a hash exists; its authority comes only from the complete accepted panel and
deterministic evidence gates.

### 3. Adjudication and fixture linkage

Replace duplicated positive-label prose as the authoritative identity with typed references:

- `BenchmarkAdjudication` gains `adjudicated_root_cause_refs`. A
  `positive_demonstrated` label requires at least one resolving reference and a verified
  root-cause-reconciliation check. Nonpositive and excluded labels cannot cite an admitted
  positive root cause.
- `BenchmarkFixture` gains `expected_root_cause_refs`. A `positive_issue_fixture` requires at
  least one exact reference to a root cause carried by its adjudication. String issue labels may
  remain descriptive but cannot establish evaluation identity.
- `AuditBundle`, the record union, catalog, canonical JSONL, disposable SQLite projection, report,
  and replay include the new record and enforce exact typed-reference resolution.

### 4. Authority and chronology

- Stage 1 remains answer-blind and never receives a canonical root-cause key.
- Stage-2 candidate selection occurs only after the Stage-1 panel is frozen and while detector
  identity and output remain hidden.
- The evaluator creates the canonical record only from two fresh, cross-provider Stage-2 reviews
  with identical membership selections and complete evidence gates.
- Prose similarity, embeddings, an LLM tie-breaker, self-reported confidence, and majority vote
  cannot create or repair the identity.
- Any missing candidate, provider mismatch, set disagreement, unresolved premise, source drift,
  or ID mismatch makes reconciliation unresolved and excludes the case from positive admission.
- This decision does not map a detector Finding to an adjudicated root cause, create qualification
  metrics, qualify a detector, or authorize project execution. Those Stage-3 meanings remain
  separately gated.

## Migration from v0.8.0

Review-local candidate IDs may be deterministically added to v0.8.0 demonstrated-issue reviews
because they restate exact existing content and assert no cross-review equivalence. No Stage-2
reconciliation set or `AdjudicatedRootCause` may be inferred from prose.

A v0.8.0 `positive_demonstrated` adjudication therefore migrates as excluded or insufficient
evidence in v0.9.0, preserving the old status and prose in `x-v0-8-*` extensions, until the Stage-2
membership protocol is rerun. Ambiguous and failed adjudications remain excluded. Migration never
invents agreement, evidence, or a canonical root cause.

## Alternatives

### Hash normalized root-cause prose

Rejected because wording differences create false disagreement, normalization choices smuggle in
semantic policy, and equal text does not independently prove equal scientific meaning.

### Give Stage-1 reviewers an answer-side root-cause key

Rejected because it leaks answer structure and anchors the blind review.

### Let one adjudicator or a majority assign the key

Rejected because the specification requires fresh cross-provider agreement and forbids majority
vote from overriding material dissent.

### Keep reconciliation evaluation-private

Rejected because an untyped private convention cannot support durable label admission, fixture
identity, replay, or later qualification evidence.

## Acceptance evidence required

1. Schema examples and invariants for Stage-1 local identity, Stage-2 reconciliation, admitted
   root cause, excluded disagreement, adjudication linkage, fixture linkage, and full bundle refs.
2. Candidate IDs recompute from exact review content and reject mutation of any identity input.
3. Stage-1 packets contain no canonical ID or answer-side equivalence grouping.
4. Two fresh Stage-2 providers selecting the identical cross-provider candidate set can create one
   stable `AdjudicatedRootCause`; different sets, issue classes, or source evidence abstain.
5. Positive label admission requires the canonical record, complete deterministic checks, exact
   source resolution, surviving falsification, and no material dissent.
6. Ambiguous, insufficient, failed, verified-good, and hard-negative cases cannot acquire a
   positive root cause through this protocol.
7. A fail-closed v0.8-to-v0.9 migration invents no equivalence and cannot leave a legacy positive
   label eligible without rerunning Stage 2.
8. Canonical JSONL, disposable SQLite rebuild, report rendering, semantic lock, and model-free
   replay preserve the new record and every reference byte-for-byte.
9. Production and evaluation wheels remain isolated, and no model or project-authored code is
   invoked by reconciliation.

## Consequences

- K03 can become locally complete and positive label admission can be implemented without prose
  similarity or answer leakage.
- Public schema version becomes `0.9.0`; accepted v0.8.0 and earlier packages remain immutable.
- Existing synthetic v0.8.0 positive examples are migration baselines, not automatically admitted
  v0.9.0 qualification labels.
- Stage-3 detector-to-root-cause equivalence and qualification metrics remain a later explicit
  decision; canonical scientific truth is necessary but not sufficient for scoring detector
  output.

## Acceptance record

Accepted by the repository owner on 2026-07-28 as proposed, including schema v0.9.0. Accepted
v0.8.0 and earlier schema packages remain immutable.
