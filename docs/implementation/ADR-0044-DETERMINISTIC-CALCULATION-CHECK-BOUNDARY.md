# ADR-0044: Add a typed deterministic-calculation check boundary

- **Status:** Accepted by owner on 2026-07-31
- **Date:** 2026-07-31
- **Coordinated schema release:** `0.18.0`
- **Related decisions:** Accepted ADR-0017 through ADR-0020, ADR-0042, and ADR-0043
- **Finding impact:** None until a separately qualified detector is explicitly promoted
- **Execution impact:** None; calculation adapters read bounded immutable inputs and never execute
  project-authored code

## Context

The accepted scientific-check registry represents closed method choices and their exact evidence.
That is sufficient for questions such as whether a target entered its own background, but it is not
an honest representation of an auditor-owned calculation over a vector of supplied values.

Experiment 0029 freezes the first multiple-testing family. Its positive and corrected twin require
the auditor to retain the complete declared family, recomputed Benjamini-Hochberg values, reported
and recomputed discovery counts, exact disagreement positions, and the finite checks establishing
table identity and contract scope. A scalar method operand cannot carry those facts. Encoding the
calculation in a receipt description, an opaque semantic-lock extension, or a BH-specific controller
branch would make replay and future pseudoreplication/confounding checks depend on special cases.

## Decision

Add a parallel `deterministic_calculation_check_v1` extension boundary rather than widening the
existing method-question contract.

The public schema should add one `DeterministicCheckObservation` record with:

- a content-addressed check and adapter identity;
- an applicability state and explicit output ceiling;
- exact target, input Artifact, and source references;
- a closed array of typed named operands (`boolean`, integer, finite number, string, and bounded
  scalar arrays);
- one declared comparison relation and the outcome `conformant`, `nonconformant`, `unknown`, or
  `not_applicable`;
- finite applicability, ambiguity, counterevidence, and completeness receipts;
- lineage status and limitations;
- explicit non-inferences about execution, causality, universal method adequacy, and Findings; and
- deterministic provenance and replay identity.

Calculation modules should have their own manifest kind and registry projection. They may reuse the
controller's immutable inspection context but cannot emit assessments directly. Experimental
detectors consume only locked typed observations plus any independently authorized scientific
contract. Finding admission remains controller-owned and unchanged.

The first adapter would implement only the Experiment 0029 profile:

1. one selected Markdown report explicitly declares BH/FDR, alpha, a complete testing-family table,
   and exact column bindings;
2. one fully digested CSV/TSV under finite byte, row, and column ceilings resolves to that path;
3. all identifiers, raw p-values, adjusted values, and calls parse under a closed grammar;
4. the auditor recomputes BH without importing project code;
5. the observation retains exact reported/recomputed counts and mismatches; and
6. an unqualified detector can emit at most an evaluation candidate or Disclosure.

The single-primary hard negative is not applicable. A selected-hits table or unresolved family is
unknown and may produce a bounded MaterialQuestion, never an adverse observation.

## Alternatives rejected

### Add BH directly to the controller

Rejected because pseudoreplication, confounding, pairing, and future numerical checks would each
require another controller special case, recreating the whack-a-mole architecture the modular
registry was intended to prevent.

### Store the calculation as a method operand

Rejected because a scientist-authorized method choice and an auditor-recomputed numerical relation
have different authority, structure, and counterevidence requirements.

### Put an untyped payload only in `semantic.lock.json`

Rejected because it would be durable detector input without a public schema, standalone validation,
canonical JSONL storage, or explicit migration semantics.

### Restore the old single-cell execution engine as the extension API

Rejected because the overhaul is not a compatibility port and the MPP does not execute project-
authored workflows. Auditor-owned bounded calculations over supplied immutable data remain allowed.

## Acceptance evidence

- Immutable schema `0.18.0` is published without altering earlier releases.
- Positive, corrected-twin, hard-negative, ambiguous, malformed, over-budget, workspace-drift,
  removal, ordinary-audit, report, semantic-lock, and replay tests exercise the generic record and
  registry.
- All Experiment 0029 roles pass through the ordinary audit path with zero production Findings.
- Removing the BH module removes its calculation observation and associated assessment without
  changing unrelated audit behavior.
- A separate qualification freeze and owner promotion remain mandatory before any production
  Finding.

## Remaining limitation

This decision creates a reusable evidence carrier, not broad statistical intelligence. Each
scientific calculation still needs a separately frozen contract, independent oracle, adapters,
hard negatives, fresh cases, and qualification evidence.
