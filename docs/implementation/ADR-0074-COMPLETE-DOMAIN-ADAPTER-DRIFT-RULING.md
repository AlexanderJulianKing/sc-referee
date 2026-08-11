# ADR-0074: Maintainer ruling on the complete-domain adapter drift

- **Status:** Accepted by the maintainer on 2026-08-11, in session ("yes", in response to the
  framed decision: rule the current adapter bytes inside the qualified envelope, with the grant
  pinning today's digests so any future drift fails closed).
- **Date:** 2026-08-11
- **Scope:** the `check:complete-domain-exposure-denominator` v2.0.7 qualified envelope only.
  This ruling covers exactly the adapter bytes identified below and no later bytes.
- **Relates to:** ADR-0070, ADR-0071 (which anticipated this ruling as one of two Round-2
  routes), the Round-2 implementation plan.

## Context

ADR-0071 pinned the exam-time adapter identity and disclosed that HEAD had drifted through two
commits: `444d643` (an overflow guard added to `quantity_consistency_adapter.py` by an
adversarial-review fix) and `63fb0a1` (a `core.py` change from founder-orientation v3 work that
feeds the shared implementation digest). The recognition-grammar digest, the identity of what
the adapter recognizes, did not move. ADR-0071 held that live production use required either a
fresh sealed confirmation or an explicit maintainer ruling.

## Evidence

1. **Grammar stability.** The recognition-grammar digest is byte-identical at exam time and at
   HEAD: `sha256:c757692071a6925a5ca5e409dc0ad79f7421fcdbc93fb15c14efb30050524362`.
2. **Drift attribution is complete.** Both contributing commits are identified; no third
   contributor exists in the digest closure.
3. **Sealed-case replay at HEAD.** All seven sealed examination cases were re-run against the
   current adapter bytes (`REPLAY_AT_HEAD.json`, semantic digest
   `sha256:2c8fc8cbbb22912768cde8b43b00aff22b8de5a0d999b31972d3c3e3b44b87ca`, in the lane
   beside the sealed exam). Agreement was seven of seven: identical outcomes, identical
   candidate counts. The replay is explicitly non-blind and is evidence about behavioral
   equivalence on the examined objects, not a fresh examination.

## Decision

1. The current adapter bytes (implementation digest
   `sha256:cb6de94e39efdf726cc516178b77b85443044415b72c8671025ef9c2e6eef05c`, adapter manifest
   digest `sha256:231046e541e1e84671b7fe716a2454c67d2d931f1cfe432e7de80512987d3a20`) are ruled
   inside the qualified envelope of the v2.0.7 sealed examination.
2. The Round-2 installed grant pins these HEAD digests as its exam adapter identity, so the
   next adapter drift, of any kind, fails the grant closed rather than inheriting authority.
3. Restoring exam-time bytes was considered and rejected as infeasible: it would revert an
   adversarial-review bug fix and a shared module that later qualified work depends on.
4. This ruling does not generalize: any future adapter change requires a new ruling with fresh
   replay evidence, or a fresh sealed examination.

## Consequences

- Round 2 may proceed to grant installation with the HEAD identity pinned.
- The replay artifact and this ADR travel together in the qualification record's disclosure
  set: the promoted detector's live authority rests on the sealed exam plus this documented,
  evidence-backed equivalence ruling, and the record says so plainly.
