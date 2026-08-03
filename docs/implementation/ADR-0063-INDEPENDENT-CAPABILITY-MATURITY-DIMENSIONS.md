# ADR-0063: Report six capability-maturity dimensions independently

- **Status:** Accepted under the repository owner's explicit generic-referee implementation request
- **Date:** 2026-08-03
- **Related decisions:** ADR-0040, ADR-0059, ADR-0060
- **Schema impact:** None; the ledger is a private documentation projection, not a public record
- **Finding impact:** None; the ledger cannot qualify or promote a detector
- **Execution impact:** None

## Context

Calculation availability has sometimes been described as complete capability even when evidence
recognition, finite structural verification, impact analysis, evaluation-candidate admission, and
production qualification were absent. One broad label hides those differences.

## Decision

1. Capability documentation reports `inventoried`, `recognized`, `structurally_verified`,
   `impact_tested`, `evaluation_candidate`, and `finding_qualified` independently.
2. Each dimension is projected from its own exact manifest or registry fields. An earlier
   dimension never supplies evidence for a later dimension.
3. `supported` means a bounded implementation path exists; it does not mean every audit completed
   the step. `not_evidenced` is not a pass, negative result, or correctness claim.
4. Calculation comparisons may support impact testing without supporting structural diagnosis.
   Scientific-check bindings may support structural verification without establishing a candidate.
5. Finding qualification requires its own promoted qualification and explicit detector permission.
6. No aggregate `full`, readiness, risk, or pass status is generated.
7. The ledger is private documentation derived from accepted source collections. It does not
   modify or extend the immutable v0.18 public schemas.

## Consequences

Capability documentation can improve one dimension without silently lifting another. A future
public maturity record requires a separate schema decision; this ledger creates no production
authority.
