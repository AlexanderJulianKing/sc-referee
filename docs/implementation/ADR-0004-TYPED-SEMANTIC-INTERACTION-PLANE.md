# ADR-0004: Promote a typed semantic interaction plane and linked pre-lock resume

- **Status:** Accepted
- **Date:** 2026-07-28
- **Related requirements:** SA-FR-017–025, SA-FR-030, SA-FR-087, SA-NFR-010,
  SA-NFR-013, lifecycle stages 7–11, integration sections 9.4–9.7

## Context

The accepted v0.6.0 release can persist observed computation, controller state, questions, and
semantic assertions, but it cannot represent the bounded interaction needed to resolve semantics:

- the normative `WorkItem` and `Answer` graph nodes have no public schemas;
- `AuditRun` moves directly from `parsed` to `semantics_locked`, omitting proposed semantics,
  waiting for answers, and resolved semantics;
- the temporary publication-surface answer is self-digested but nonpublic;
- model proposals have no controller-owned work-packet identity or submission boundary; and
- a completed run cannot be mutated, while a model call made after its semantic lock cannot alter
  that run.

Hiding work packets, proposals, or answers in extensions would make conversational state
authoritative and would bypass the required provenance, authority, and replay boundaries.

Adding required AuditBundle arrays and lifecycle states is a public shape change. The accepted
v0.6.0 package should not be silently rewritten again after its ADR-0003 amendment.

## Decision

Publish a coordinated local schema release `0.7.0`, derived from immutable v0.6.0, with these
changes.

### 1. Public WorkItem

Add a closed `WorkItem` record containing:

- run identity, work kind, exact target and dependency references;
- status and completion disposition;
- estimated elapsed cost, expected information gain, claim materiality, downstream reach,
  component maturity, cache status, and execution privilege;
- one bounded packet containing only exact source references, required record references,
  unresolved semantic dimensions, required output record types, and explicit limitations;
- a normalized packet digest and normalized prompt-template digest; and
- provenance and timestamps when available.

Open-ended scientific-error discovery is not a valid work kind. Semantic model work may request
only proposed `SemanticAssertion`, `Claim`, conflict, or material-question records named by the
packet. Project-code execution is never implicit in a semantic work item.

### 2. Public Answer

Add a closed `Answer` record containing:

- the exact `MaterialQuestion` reference, source run, and source snapshot digest;
- a human respondent, response source, answer kind, selected option or structured value;
- an authority scope limited to named subjects and semantic dimensions;
- answer time when available plus an explicit timestamp-availability state;
- qualitative certainty or an explicit unavailable state;
- superseded-answer references, provenance, and a self-digest profile.

An Answer establishes scientist intent only within its declared authority scope. It cannot rewrite
observed execution, report wording, parser output, or an earlier answer. Conflicts remain as
separate assertions.

### 3. Proposal boundary

Use existing public `SemanticAssertion` records for model proposals. A model submission must be
bound to one WorkItem and must enter with:

- `epistemic_status: proposed`;
- `finding_eligibility: ineligible` or `pending`;
- model provenance and the exact packet/prompt digests; and
- source references that the controller resolves against the immutable snapshot.

The controller rejects unrequested record types, out-of-snapshot sources, digest mismatches,
invented source text, accepted status, observed-computation authority, and any proposal submitted
after the current run segment is locked. Model confidence never establishes a material premise.

### 4. Linked pre-lock resume

Extend `AuditRun` with `semantics_proposed`, `awaiting_answers`, and `semantics_resolved`. A resume
operation creates a new output directory and new run segment linked through `parent_run_ref`; it
copies no mutable state into the earlier run and requires the same repository snapshot digest.

The typed local protocol is:

```text
resume -> work-queue -> work-packet -> submit-proposals
       -> record-answer (when needed) -> lock-semantics -> complete
```

Every command validates the current durable state and is create-only or append-only. Waiting for a
scientist pauses elapsed audit time. `lock-semantics` records accepted assertions, Answers,
explicit unknowns/conflicts, and flattened contracts. No model call or proposal submission is
allowed after that lock. Detection and reporting remain controller-owned and model-free.

### 5. Bundle, union, storage, and migration

Add required `work_items` and `answers` arrays to AuditBundle and both records to the public record
union and catalog. Canonical JSON/JSONL remains authoritative; SQLite remains generated. Migration
from 0.6.0 creates empty arrays and invents no interaction history.

## Acceptance evidence required

1. Positive examples for ready/completed WorkItems and candidate-selection/structured Answers.
2. Negative schema and controller tests for open-ended work, implicit execution, unresolved packet
   digests, model-accepted assertions, out-of-snapshot sources, nonhuman scientist answers,
   authority-scope escape, answer-option mismatch, answer tampering, and post-lock submission.
3. An exact-snapshot linked resume that persists a packet, proposal, and scientist Answer before a
   new semantic lock without modifying the parent run.
4. A conflict fixture proving scientist intent does not overwrite observed execution.
5. Model-disabled replay with byte-identical accepted assertions, unknowns, contracts, detector
   results, assessments, and coverage.
6. A fresh-context Codex-skill test that uses only the typed protocol and never maintains a second
   conversational copy of audit state.

## Consequences

- The schema version becomes `0.7.0`; accepted v0.6.0 and v0.5.0 packages remain immutable.
- The temporary publication answer can be migrated into the public Answer path and then removed.
- A local typed subprocess protocol is sufficient for the first vertical slice; MCP transport can
  wrap the same operations later without changing scientific record meaning.
- This decision does not qualify a detector, broaden scientific domains, authorize project code,
  deploy W3ID schemas, or create compatibility requirements for the legacy public GitHub repo.

## Acceptance record

- Decision: accept ADR-0004 and schema release `0.7.0`.
- Accepted by: repository owner in the implementation task on 2026-07-28.
- The accepted v0.6.0 and immutable v0.5.0 packages remain unchanged.
