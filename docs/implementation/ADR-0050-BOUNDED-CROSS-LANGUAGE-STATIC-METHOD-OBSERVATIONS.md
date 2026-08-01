# ADR-0050: Admit bounded cross-language static method observations

- **Status:** Accepted under the repository owner's standing authorization for non-material backlog
  decisions
- **Date:** 2026-08-01
- **Coordinated public schema release:** None
- **Related decisions:** Accepted ADR-0033, ADR-0042, ADR-0047, ADR-0048, and ADR-0049
- **Finding impact:** None; every added adapter remains question-only
- **Execution impact:** None; Python and R source remain inert bytes

## Context

Most installed scientific checks can recognize only an explicit declaration in the selected report.
The general scope graph can now bind an explicitly selected analysis source, a selected active cell,
or one uniquely connected static report writer to the selected publication surface. What is missing
is a reusable way for existing checks to recognize the same closed operand in ordinary Python and R
source without treating a call name, a model's confidence, or an unscoped helper as proof of the
governing analysis.

The retained structural-copy and MVMR development workflows expose two concrete high-value gaps:
classifier outputs are transformed into a quantitative copy dosage, and robust MVMR inputs may be
LD-whitened before fitting. Both choices already have accepted question-only checks and report
operands. Adding new checks would duplicate the scientific obligation.

## Decision

### 1. Add one shared, closed static-source adapter boundary

The production registry may attach isolated Python and R adapters to an existing scientific check.
Each adapter:

- reads only immutable bytes and the controller-owned parser receipt in `FrozenInspectionContext`;
- emits an existing `CanonicalOperand` or a bounded abstention;
- requires one exact path through the accepted static scope graph before becoming applicable;
- preserves an exact but unscoped operand only as an unsupported suppressor; and
- remains incapable of emitting a Finding.

The first rules cover classifier-derived copy dosage and LD whitening before a robust fit. Their
language-specific syntax normalizes to the same existing operand values used by the report
adapters. The implementation is organized around shared call binding, literal argument, assignment,
control-boundary, scope, receipt, and evidence-span machinery so another code form does not require
controller, storage, reporting, admission, or schema edits.

### 2. Keep call and dataflow recognition finite

Python bindings may resolve exact imports and explicit import aliases from a closed package/function
allowlist. R bindings may resolve exact literal namespaces and a closed set of unshadowed direct
calls; aliases are accepted only when one immutable identifier is assigned one literal namespace
target. Supported formulas, class-state vectors, method arguments, assignments, and short local
function summaries are enumerated.

Shadowing, wildcard imports, computed call targets, dynamic dispatch, ambiguous assignments,
competing supported targets, or method-defining branches force abstention. A loop may preserve an
already resolved representation but does not prove that an iteration occurred. Static parsing never
imports, sources, evaluates, or executes target code.

### 3. Require the controller parser boundary and expose disagreement

Python observations require a complete matching CPython-AST parser receipt. R observations require
a complete Tree-sitter-R receipt. If the independently available base-R inventory disagrees with the
Tree-sitter call inventory, the semantic adapter is unsupported. Base-R unavailability remains an
explicit parser limitation and does not silently become agreement.

Source/report operand disagreement is reduced by the existing scientific-check registry to
`ambiguous`. A model confidence score, numeric answer, benchmark identity, file name, or repository
identity cannot arbitrate it.

### 4. Preserve the authority ceiling

An applicable source observation states only that one exact, statically connected source shape
encodes the normalized method operand. It does not establish runtime values, package behavior,
execution, dead-code absence, primary-analysis status, historical intent, numeric causality, or
scientific correctness. Those limitations are retained in adapter manifests and emitted receipts.

No public record meaning changes, so schema `0.18.0` remains current.

## Alternatives rejected

### Infer scientific meaning from arbitrary call names

Rejected because names can be rebound, wrapped, or used for a different purpose and package
behavior is a runtime premise.

### Let a model decide which source call governs the result

Rejected because model confidence cannot establish a material premise and would make replay
nondeterministic.

### Treat every source file as part of the selected analysis

Rejected because an unused helper or sibling workflow would create false questions. Exact scope
selection or an independently supported static connection remains required.

### Create new scientific checks for Python and R

Rejected because language and syntax are adapter concerns when the normalized scientific choice is
unchanged.

## Test, acceptance criterion, and remaining limitation

- **Tests required:** Python direct and aliased imports; R direct and namespaced calls plus the
  closed namespace-alias form; exact method arguments and formulas; shadowing; dynamic dispatch;
  branches; competing calls; parser disagreement; source/report agreement and disagreement;
  selected, unscoped, sibling, and removal cases; cross-language operand equivalence; manifest
  mutation; no execution/model calls; and exact replay.
- **Acceptance criterion:** Python and R source adapters emit the same normalized operand as the
  existing report adapters, use the common scope graph, make disagreement explicitly ambiguous,
  and require no controller, storage, report, admission, or public-schema change.
- **Remaining limitation:** static source cannot prove runtime values, package behavior, execution,
  dead-code absence, or primary-analysis status. The initial closed grammars do not cover arbitrary
  wrappers, generated formulas, general interprocedural flow, or other scientific checks.
