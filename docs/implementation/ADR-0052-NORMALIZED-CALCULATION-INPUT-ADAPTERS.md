# ADR-0052: Separate calculation contracts from repository-layout adapters

- **Status:** Accepted under the owner's standing authorization for non-escalating architecture
  decisions
- **Date:** 2026-08-02
- **Related decisions:** ADR-0044, ADR-0045, ADR-0048, ADR-0051
- **Related backlog item:** L09
- **Coordinated schema release:** None; retain public schema 0.18.0
- **Finding impact:** None
- **Execution impact:** None

## Context

The eight deterministic calculation families already have separate registry modules, but each
initial adapter recognizes one purpose-built report declaration and immediately performs table or
source evaluation. That safely established the calculation boundary, yet it couples a reusable
calculation to one evidence layout. Adding another repository layout by copying the calculation
would create divergent scientific behavior and make cross-layout equivalence difficult to prove.

Natural repositories also cannot be expected to rename their files or reports to match development
fixtures. They do need an explicit, independently checkable binding for scientific semantics that
cannot be inferred safely from column names alone.

## Decision

1. Each calculation family separates a normalized, typed internal contract from adapters that
   recognize evidence layouts. The evaluator consumes only that normalized contract and exact
   `FrozenCalculationInput` identities.
2. Existing report-declaration adapters remain supported. A second adapter may consume an
   explicitly selected, fully digested YAML sidecar with the root marker
   `sc_referee_calculation_contracts: 1` and a bounded list of `{check_id, contract}` entries.
3. The sidecar filename and repository directories are not semantic. It enters the calculation
   context only through the existing scientist-selected material-input scope edge. Paths and column
   names inside a contract are explicit bindings and may use alternate safe identifiers.
4. The sidecar parser is strict and bounded: UTF-8 only, safe YAML loading, finite byte and contract
   ceilings, exact root and entry keys, unique supported check IDs, and mapping-only contracts.
   Unmarked YAML is ignored. Multiple marked sidecars, duplicate check entries, or simultaneous
   report and sidecar observations fail closed through the existing registry ambiguity rule.
5. Layout adapters may normalize syntax but cannot infer an implicit scientific premise. Missing
   units, family completeness, thresholds, producer bindings, or analysis semantics remain
   unsupported or not applicable according to the family contract.
6. Adapter source references identify the exact report span or whole selected sidecar plus every
   exact calculation input. No adapter executes or imports project-authored code.
7. Public observation schema, output ceilings, comparison relations, and Finding admission remain
   unchanged. New content-addressed adapter manifests and the changed registry release are frozen
   in a new calculation-manifest version.

## Alternatives rejected

### Infer all semantics from familiar filenames and columns

Rejected because names such as `pvalue`, `sample`, or `cluster` do not establish family
completeness, experimental unit, intended threshold, data independence, or producer identity.

### Copy each calculation into every repository adapter

Rejected because two layouts could silently implement different arithmetic or counterevidence
rules while claiming the same check identity.

### Treat a sidecar as scientist proof of correctness

Rejected. A sidecar is a scoped declaration and exact binding, not evidence that the declaration is
true, scientifically adequate, or used at runtime.

## Acceptance evidence required

- every active calculation family evaluates at least two materially different evidence layouts
  through distinct content-addressed adapters;
- cross-adapter tests compare normalized operands and outcomes while varying paths, column order,
  and safe identifiers;
- missing and duplicate identifiers, extra rows, units, NA representations, thresholds, and
  over-budget inputs fail closed or retain the family-specific non-adverse state;
- the original development controls retain their exact scientific outcomes;
- simultaneous competing layouts do not produce an observation;
- semantic-lock replay is byte-stable and no project-authored code or model call is introduced; and
- the public schema remains 0.18.0 and every calculation remains below Finding authority.

## Remaining limitations

The sidecar makes existing calculations portable; it does not discover every relevant calculation
or prove that a declaration matches hidden runtime behavior. Repository support is still bounded by
the available static readers, exact selected inputs, normalized scientific vocabulary, and each
family's finite calculation profile.
