# ADR-0006: Group downstream manifestations under a root cause

- **Status:** Accepted for this draft
- **Date:** 2026-07-27
- **Related requirements:** SA-FR-036, SA-FR-043, SA-FR-062; SA-NFR-005
- **Supersedes:** None

## Context

One cohort-selection or denominator error can affect many models, figures, tables, and claims. Reporting every manifestation as an independent warning would overwhelm the scientist and inflate issue counts.

## Decision

The system MUST group findings by a graph-supported root cause. A finding group MUST identify the root node or mismatch, the primary issue, all material downstream claims and artifacts, propagation paths, and any bounded unaffected descendants. Deduplication MUST be based on causal structure and violated semantic dimension, not only textual similarity.

## Consequences

### Positive

- Scientists see one actionable issue and its full impact.
- Metrics can evaluate root-cause recall rather than warning volume.
- Remediation and review can focus on the earliest material divergence.

### Negative and trade-offs

- Root-cause inference can be ambiguous when multiple errors interact.
- The UI must still make individual manifestations inspectable.

## Alternatives considered

### One warning per claim

Rejected because it creates warning floods and misleading counts.

### Pure text clustering

Rejected because similar wording does not establish a shared cause.

## Validation

Fixtures MUST include one upstream population error affecting multiple claims and confirm that the report emits one root group with every affected descendant.
