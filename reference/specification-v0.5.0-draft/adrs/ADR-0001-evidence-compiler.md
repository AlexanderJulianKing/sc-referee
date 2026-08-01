# ADR-0001: Use an evidence-compiler architecture

- **Status:** Accepted for this draft
- **Date:** 2026-07-27
- **Related requirements:** SA-FR-008, SA-FR-021, SA-FR-031, SA-FR-042, SA-FR-046; SA-NFR-001, SA-NFR-005
- **Supersedes:** None

## Context

A language model can interpret scientific meaning but is not a reliable authority for exact computation, complete lineage, or final finding admission. A purely deterministic analyzer cannot infer all domain semantics from dynamic scientific code. The architecture must combine both without confusing inference with fact.

## Decision

The system MUST transform a project through explicit stages:

```text
source material
→ observed computational records
→ proposed semantic assertions
→ resolved semantics, conflicts, and unknowns
→ deterministic detector results
→ admitted findings and coverage disclosures
```

Language-model output MUST enter the system as provenance-bearing proposals or review-only hypotheses. Deterministic validation and finding-admission rules MUST control canonical records and final evidence language.

## Consequences

### Positive

- Epistemic status remains inspectable.
- Model changes do not silently alter deterministic findings after semantic lock.
- False-accusation controls can be tested independently from semantic extraction.
- New parsers and domain profiles can share the same downstream kernel.

### Negative and trade-offs

- More schemas and intermediate artifacts are required.
- A complete audit may require a scientist to resolve semantics.
- The system cannot pretend that every concern has a binary answer.

## Alternatives considered

### End-to-end model reviewer

Rejected because it makes provenance, reproducibility, coverage, and wording calibration difficult to enforce.

### Fully static program analyzer

Rejected because scientific meaning, estimands, population roles, and report claims are frequently not recoverable from syntax alone.

## Validation

End-to-end fixtures MUST show that the same semantic lock produces identical detector results without model access, and that model proposals cannot bypass schema or admission checks.
