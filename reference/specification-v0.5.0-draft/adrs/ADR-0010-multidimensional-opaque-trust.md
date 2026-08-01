# ADR-0010: Represent trust in opaque boundaries by dimension

- **Status:** Accepted for this draft
- **Date:** 2026-07-27
- **Related requirements:** SA-FR-009, SA-FR-013, SA-FR-029, SA-FR-039; SA-NFR-005, SA-NFR-010
- **Supersedes:** None

## Context

A workflow may call a proprietary tool, custom package, compiled binary, remote service, or unavailable HPC process. A scientist may reasonably accept its output while the auditor cannot inspect its internal scientific model. A single trusted/untrusted Boolean would either block all downstream analysis or overstate verification.

## Decision

Opaque operations and external artifacts MUST record trust separately for at least:

- artifact identity and integrity;
- execution provenance;
- numerical output correctness;
- internal scientific semantics; and
- reproducibility or re-executability.

Downstream evidence ceilings and coverage disclosures MUST reflect the weakest relevant dimension. Reproducing an output MUST NOT imply that the operation's scientific assumptions were validated.

## Consequences

### Positive

- Useful downstream auditing can continue across explicit trust boundaries.
- Reports can state precisely what was and was not inspected.
- External tools do not receive blanket scientific endorsement.

### Negative and trade-offs

- Trust records are more complex than a Boolean.
- Detector authors must declare which trust dimensions they require.

## Alternatives considered

### Treat every opaque operation as wholly trusted

Rejected because it would hide scientific and lineage uncertainty.

### Treat every opaque operation as wholly unsupported

Rejected because it would make many real workflows unauditable even when outputs and provenance are well established.

## Validation

Fixtures MUST show downstream claim checking across an identity-trusted but semantics-opaque operation, with a corresponding coverage limitation rather than an automatic finding.
