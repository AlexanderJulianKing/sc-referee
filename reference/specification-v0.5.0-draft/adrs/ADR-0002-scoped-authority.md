# ADR-0002: Preserve scoped authorities instead of overwriting conflicts

- **Status:** Accepted for this draft
- **Date:** 2026-07-27
- **Related requirements:** SA-FR-011, SA-FR-021, SA-FR-024, SA-FR-025; SA-NFR-010
- **Supersedes:** None

## Context

The scientist may state the intended population, estimand, or comparison, while the code and dataflow show something different. Treating the scientist's statement as a universal override would erase implementation–intent mismatches. Treating code as the authority for intent would misrepresent the scientific question.

## Decision

Authority MUST be scoped:

- scientists are authoritative for intended scientific meaning;
- source code and runtime evidence are authoritative for observed computation;
- report content is authoritative for what was communicated; and
- model extraction is fallible proposed evidence.

Conflicting scoped assertions MUST remain in the record. Resolution MUST identify the role or scope being resolved and MUST NOT mutate an observation into an intention or vice versa.

## Consequences

### Positive

- Implementation–intent mismatches remain detectable.
- Human expertise is respected without falsifying provenance.
- Report contradictions can be represented independently from code behavior.

### Negative and trade-offs

- Users may perceive unresolved conflicts as verbose.
- The UI must explain why a scientist answer does not erase an observed operation.

## Alternatives considered

### Scientist always overrides every record

Rejected because it would create false negatives and destroy audit lineage.

### Code always overrides intent

Rejected because computation cannot define the intended scientific question.

## Validation

Fixtures MUST cover an intended population that differs from a realized complete-case population and confirm that both remain visible and can support a finding.
