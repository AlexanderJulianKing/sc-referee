# ADR-0039: Admit an exact selected-output writer scope join

- **Status:** Accepted under the repository owner's standing authorization for non-authority-
  changing development ADRs
- **Date:** 2026-07-31
- **Related decisions:** Accepted ADR-0019, ADR-0020, ADR-0037, and ADR-0038
- **Schema impact:** None; accepted schema v0.15.0 remains unchanged

## Context

ADR-0038 lets an exact supported static method shape inside the selected notebook or Quarto source
Artifact support a bounded scientist question. The same method shape in a separate `analysis.py`
file remains unscoped, even when that file contains the only statically recognized writer for the
exact selected `report.md`. This blocks a common real repository layout and leaves source evidence
as a suppressor rather than public question evidence.

Repository membership and matching filenames are insufficient: analysis files may be unused,
multiple writers may compete, path construction may be dynamic, and a writer declaration does not
show that code ran. The safe increment is therefore a finite static declaration path to the exact
full-digest selected Artifact, with ambiguity and reachability checks, while retaining the existing
question-only ceiling.

## Decision

### 1. Extend only the exact source-parent writer grammar

Python parser `parser:python-ast-tokenize` version `0.15.1` recognizes a selected-output path only
when all of the following are statically true:

1. `Path` is imported exactly as `from pathlib import Path` and is not rebound;
2. one top-level name is bound exactly once to `Path(__file__).parent` or
   `Path(__file__).resolve().parent`;
3. the writer receiver joins that name to one safe literal relative path with `/`; and
4. the call is exactly `write_text` or `write_bytes`.

Absolute paths, parent traversal, `Path.cwd()`, repeated or dynamic bindings, dynamic path
components, deeper parent traversal, and other path APIs remain unsupported. Parser and descendant
cache identities bind the new component version.

### 2. Require one exact selected Artifact and one statically reachable writer

The existing founder-orientation source adapter may attach analysis scope only when the static
output path has been identity-merged with the exact full-digest selected report Artifact and that
Artifact has exactly one producer Operation. The Operation must:

- be a supported `write_text` or `write_bytes` call from the inspected source FileRecord;
- declare the selected Artifact as its sole output; and
- be either a direct module-level expression or a direct expression in one undecorated,
  zero-argument top-level function that is called exactly once by an exact
  `if __name__ == "__main__"` guard.

The scope path is:

`FileRecord -> unique writer Operation -> selected Artifact -> PublicationSurface`.

More than one producer, an unused writer function, indirect or parameterized entrypoints, a path or
digest mismatch, or an unresolved surface prevents the join.

### 3. Permit only compatible cross-plane scope paths

A scientific-check module may combine the longer source path with the report observation's shorter
`selected Artifact -> PublicationSurface` path only when every shorter path is an exact suffix of
one unique longest path. Divergent paths remain ambiguous and cannot compile. No general graph
reachability or fuzzy scope equivalence is introduced.

### 4. Preserve the question-only and non-execution boundary

This join can only make the existing founder-orientation normalized observation applicable and add
its exact static source citation to the existing scientist question and later compatibility ledger.
It does not establish that the writer ran, that the file produced the existing bytes, that the
method was primary rather than exploratory, that the report reflects historical intent, that any
number was caused by the method, or that either operand is scientifically correct.

The check, answer, and exact-conflict result remain Finding-ineligible. A conflicting scientist
Answer produces the existing bounded Disclosure, not a Finding. Any future Finding permission
requires a separate authority-changing ADR and complete detector qualification.

## Alternatives rejected

### Scope every source file that mentions the report path

Rejected because filenames and mentions do not establish a unique typed output declaration.

### Accept arbitrary path expressions or control-flow reachability

Rejected because dynamic path and general control-flow interpretation would exceed the frozen
static grammar and weaken the hard-negative boundary.

### Treat the writer as execution or authorship evidence

Rejected because static declarations show only what the source says it may write, not what ran or
who authored the selected bytes.

### Promote the resulting incompatibility directly to a Finding

Rejected in this decision because exact connectivity is only one Finding premise. The detector,
finite counterevidence protocol, answer-blind qualification evidence, and promotion authority do
not yet exist.

## Test, acceptance criterion, and remaining limitation

- **Tests added:** exact source-parent path parsing; dynamic, absolute, parent-traversing, and
  non-source-root path hard negatives; a unique guarded writer positive; unused and competing
  writer negatives; combined report/source question compilation; inert project-code marker;
  structured scientist Answer; exact incompatibility Disclosure; semantic lock; and model-free
  replay.
- **Real validation:** the frozen answer-isolated multiparent-QTL workflow now supplies both the
  exact report declaration and the separately scoped static source operand. The previously accepted
  repository-owner requirement, `repair_ril_founder_orientation_before_hmm_emission`, produces one
  exact review-scoped incompatibility Disclosure with zero Findings. Replay preserves the complete
  Answer, assertions, Disclosure, and scope path.
- **Acceptance criterion satisfied:** a common separate-analysis-file layout can reach the
  scientist and preserve exact source evidence through Answer, lock, incompatibility, and replay
  without executing project code or broadening Finding authority.
- **Remaining limitation:** arbitrary path libraries, general DAG/control-flow reachability,
  multiple writers, separate generated-result intermediates, R writers, execution and primary-role
  provenance, numerical causality, and Findings remain unsupported.
