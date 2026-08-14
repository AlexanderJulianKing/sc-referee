# EXPERIMENT-0060 — Dependence semantic v2 growth shadow

Date: 2026-08-14  
Status: unregistered development shadow; no production or qualification authority

## Authority and delivery ceiling

This experiment implements the reviewed dependence growth-1 grammar in a new
`dependence_recognition_v2` package.  It does not modify or supersede the
qualified v1.1.0 package or EXPERIMENT-0058.  It has no scientific-check
registration, method-conflict binding, registry entry, grant, capability claim,
or Finding authority.  Its only authorized invocation is the evaluation-side
development-loop hook.  The production controller does not import or select the
v2 adapter.

## Closed semantic claim

For one digest-bound CSV and one human-authorized independent-unit column, the
trusted prover establishes, for every byte-exact group key `g`, the ordered
sequence

```text
[builtin_cast(row[V]) for row in frozen file order if row[K] == g]
```

where the cast is absent, the real `float`, or the real `int`.  The kernel
requires the exact length equation, complete row partition, closed predeclared
bucket keys, exact distinct group-to-procedure-argument binding, registered
procedure arity, and consumption of every proven group.

Both the group fact and the complete `HumanMethodAuthorization` arrive as
controller-supplied kernel parameters and are selected by exact lookup.  The
certificate carries neither trusted object.  The kernel binds the authority's
record id, analysis/procedure references, unit-definition id, sole key column,
input path, and input digest to the certificate and obligation before any
conclusion can be returned.

Because `csv.DictReader` produces strings, the syntactically admitted absent-cast
form cannot establish numeric procedure consumability in this procedure registry
and therefore abstains as `group-value-cast-absent`.  This is intentional:
successful extraction is not evidence that SciPy can consume the operand.

`repeated_units` requires a repeated authorized unit within at least one bound
operand.  `one_observation_per_unit` requires at most one row per unit in every
bound operand, complete group consumption, and no authorized unit appearing in
more than one bound operand.  The latter violation abstains as
`unit-spans-multiple-operands`.

## Module and function envelope

The module grammar admits only the reviewed import forms, immutable string/path
constants, the v1 main guard, and hygienically inlinable module functions.
Inlining proves an acyclic live call graph before substitution, is bounded at
depth three without truncation, permits at most one call site per live function,
and alpha-renames every parameter, local, and with-target per call.  Arguments
are Names, module constants, or literals.  Parameter rebinding, closures,
global writes, reads of module-level data names, import-name collisions, and
unproved dead functions abstain.  Zero-return functions and a final return in a
final with-body are admitted.

The analyzer and kernel independently close the live flattened statement basis.
An extra assignment, mutation, loop, conditional, call, or other live construct
outside the reader/group/procedure/sink grammar abstains as
`noninterference-unproven`; no analyzer-supplied effect summary is trusted.

The group dictionary must be constructed and consumed under one flattened name.
An alias hop between construction and procedure consumption abstains as
`group-container-aliased`; v2 does not follow container aliases.  Adding such
alias following would be a future reviewed grammar change, not a proof shortcut.

Only `encoding="ascii"` is added to the reader envelope, and only when the
frozen material bytes satisfy `bytes.isascii()`.  UTF-8, BOM, row-shape, digest,
header, and ceiling rules remain fail-closed through the inherited v1 domain
parse.

## Named coverage limits

The shadow preserves granular reasons including:

- `group-accumulator-not-total`, `group-container-not-list`,
  `group-container-aliased`, `group-value-cast-absent`,
  `group-value-cast-unproven`, `group-key-or-unit-cell-empty`,
  `group-set-not-closed`, `group-bucket-unpopulated`,
  `group-operand-arity-mismatch`, `group-operand-sliced`,
  `group-key-equals-value-column`,
  `group-key-is-unit-column`, and `unit-spans-multiple-operands`;
- `module-constant-not-closed`, `unsupported-import-form`,
  `import-use-outside-grammar`, and `import-name-collision`;
- `function-nonpositional-params`, `function-default-params`,
  `function-star-params`, `function-recursive`, `function-closure`,
  `function-globals-write`, `function-return-shape`,
  `function-inline-depth-exceeded`, `function-multiple-call-sites`,
  `function-not-provably-dead`, `function-argument-not-simple`,
  `function-parameter-rebound`, and `function-globals-read`;
- `report-composition-not-modeled`, `reader-bytes-not-ascii`,
  `duplicate-header`, `bom-unsupported`, `ragged-row`, and the statement-kind
  qualified `noninterference-unproven:*` reasons.

A trusted-kernel refusal is surfaced as
`certificate-kernel-refusal:<obligation>` so the development record preserves
which closed equation failed without changing the refusal semantics.

Batch-A rq1/rq3 remain regression fuel rather than promised positives: their
full sorted reason sets must include `report-composition-not-modeled` and
`function-multiple-call-sites`.  Aggregation-aware clearance, report
composition, additional procedure registrations, and selected-result-bound
procedure selection remain out of scope.

## 2026-08-14 batch B development observation

The `dependence-free-b` development envelope observes each frozen case once in
the detector step.  The registered v1 adapter remains the sole scored adapter.
The v2 payload and its comparison outcome are retained beside v1 under an
explicit `development` shadow identity and
`development_v2_scored_for_qualification: false`; they confer no qualification
or production authority.  No second intake or second authored-code execution is
permitted by this hook.
