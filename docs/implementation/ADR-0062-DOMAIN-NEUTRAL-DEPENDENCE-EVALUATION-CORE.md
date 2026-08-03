# ADR-0062: Add a domain-neutral dependence evaluation core

- **Status:** Accepted under the repository owner's explicit generic-referee implementation request
- **Date:** 2026-08-03
- **Related decisions:** ADR-0015, ADR-0020, ADR-0040, ADR-0042, ADR-0060
- **Schema impact:** None; the new records are internal frozen Python structures
- **Finding impact:** None; the maximum output is an unqualified evaluation candidate
- **Execution impact:** None; the evaluator is pure and does not execute project-authored code

## Context

Existing dependence observations can identify repeated labels and request their scientific meaning,
but they do not close the governing unit definition, the exact analysis input, procedure behavior,
finite safeguards, or the affected result. Treating repetition alone as pseudoreplication would
reverse material unknowns and falsely accuse analyses that aggregate, cluster, pair, block, or
otherwise account for dependence.

The reusable scientific relationship is not tied to any one subject area or file layout. It is the
relationship among analyzed observations, an authoritative independent-unit definition,
observation-to-unit memberships, the procedure's uncertainty or randomization behavior, exact
safeguard operands, and a localized output.

## Decision

1. Add an internal typed `DependenceCase` using only the domain-neutral vocabulary
   `observation`, `independent_unit`, `membership`, `cluster`, `block`, and `safeguard`.
2. Keep workflow and subject-area interpretation in removable adapters. The core receives only
   already-bound evidence states and exact typed references.
3. Freeze a finite safeguard registry covering unit-level aggregation, grouped random effects,
   correlated estimation, cluster-adjusted uncertainty, paired or blocked procedures, unit-level
   resampling, and separately registered dependence-aware procedures.
4. A safeguard covers a case only when its check binds the exact analysis target, procedure, and
   independent-unit definition. A keyword, unbound procedure label, or mismatched grouping operand
   is insufficient.
5. Emit a structural evaluation candidate only when repeated memberships, separate entry into the
   bound analysis, row-level independence, complete negative safeguard checks, and one exact
   affected target are all established.
6. Return a covered negative when there is one analyzed observation per independent unit, an exact
   applicable safeguard is present, the repeated observations did not enter separately, or the
   bound procedure is established not to use row-level independence.
7. Return a question when unit, membership, model, safeguard-binding, or affected-target semantics
   remain unresolved. Return unsupported when an input, procedure, wrapper, lineage, or registered
   safeguard check is outside the bounded evidence path.
8. Canonicalize unordered memberships, observations, safeguards, evidence references, and
   unresolved dimensions before digesting so source order cannot alter evaluation.
9. Do not integrate this core with production Finding admission. Qualification, public schema
   records, and envelope-specific promotion are separate future decisions.

## Consequences

The evaluator is reusable across materially different adapters without embedding subject-area
nouns or conventions in its decision path. Complete safeguards prevent adverse candidates, while
unresolved or opaque semantics abstain locally. An evaluation candidate remains development-only:
it does not assert numerical impact, bias direction, biological truth, or global invalidity.

Any future registry addition changes the finite counterevidence protocol and therefore requires a
new core version, tests for its exact operand binding, and a separate accepted implementation
decision. Any production promotion requires independent qualification and a distinct promotion
record; this ADR supplies no such authority.
