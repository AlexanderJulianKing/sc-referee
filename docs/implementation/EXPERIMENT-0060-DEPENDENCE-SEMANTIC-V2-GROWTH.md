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

## 2026-08-14 growth-2: symbolic count procedures and exact path forms

Growth-2 extends only this unregistered development shadow.  The qualified
v1.1.0 recognizer, its experiment, scientific-check registry, installed grants,
and capability claims remain unchanged.

The added path grammar folds `os.path.join` with POSIX semantics only when every
component is a string literal and the folded value equals the frozen reader or
selected-result path exactly.  The only
other admitted `os` uses are `os.path.dirname` of such a proven constant and
`os.makedirs(proven_constant, exist_ok=True)`.  All other `os` use abstains.

The count grammar covers `scipy.stats.binomtest` and
`scipy.stats.fisher_exact` over digest-bound CSV rows.  The certificate carries
symbolic domain and conjunction-of-byte-equality predicates plus operand
positions; it carries no traced operand value.  The trusted prover returns
ordered frozen rows, and the kernel independently evaluates predicates,
cardinalities, observation identities, and authorized-unit multiplicities.
Binomial success rows must be a row-level subset of trial rows.  Fisher cells
must be pairwise disjoint, collectively exhaustive over the proven universe,
and form the exact product of two string-valued columns with two levels each;
no authorized unit may span cells.  Arithmetic/subtraction cells are outside
the grammar.

The C-3 v3 design choice, as corrected before batch C, is explicit: both
binomial operands must be nonempty, while Fisher requires only a nonempty
universe and permits empty individual cells.  An adverse branch does not
require a proper subset of another set.  Repetition is determined solely from
authorized-unit multiplicity in the procedure-relevant proven sets.  No
`count-derivation-not-closed` catch-all is defined; each refusal uses the
closed growth-2 reason vocabulary.

That vocabulary adds exactly `count-domain-not-row-bound`,
`count-predicate-literal-not-string`, `count-predicate-not-closed`,
`count-set-degenerate`, `count-cell-derived-by-arithmetic`,
`count-success-not-subset`, `count-cells-not-partition`,
`count-cells-not-factorial`,
`unit-spans-multiple-cells`, `count-increment-not-total`,
`count-multiple-increment-sites`, `procedure-alternative-not-default`, and
`count-procedure-trial-declaration-missing`.  Path-form refusals retain the
existing granular `module-constant-not-closed`, `import-use-outside-grammar`,
reader-binding, and report-composition reasons rather than adding a catch-all.

Development count authority uses a distinct `dependence_semantic_v2_growth_2`
lock line under `authority/locks-v2/`.  Its procedure registry is exactly
`ttest_ind`, `mannwhitneyu`, `binomtest`, and `fisher_exact`.  A count lock is
minted only when the role-blind data description contains exactly one closed
line `One trial is: one row`; otherwise the v2 observation abstains as
`count-procedure-trial-declaration-missing`.  The v1 lock and scored v1 outcome
are unchanged by presence or absence of this distinct line.

Growth-2 adds batch C at
`evaluation/development/dependence-growth-loop/batch-c/`, with authors
opus-39 through opus-44, blind reviewer fable-20, hostile reviewer fable-21,
and escalation opus-15.  Like batch B, v1 alone is scored and the v2 result is
retained side by side as non-qualification development evidence.

## 2026-08-14 development review-response retention amendment

For development-loop envelopes only, a primary blind-review response that is
not valid JSON or does not satisfy the frozen response schema is retained as a
per-case `review-response-malformed` refusal.  It is never interpreted as a
label, receives no retry, remains in the development denominator, and is
excluded from detector measurement as `burned_review_response_malformed`.
Re-entry reprojects the same digest-bound process capture to the same refusal.
Qualification envelopes retain their pre-existing strict failure behavior.

## 2026-08-15 growth-3 amendment: proven sink slice, multi-site identities, imports

Growth-3 leaves the operand and count grammars unchanged.  The completeness
equation now partitions the independently flattened live module into the
backward operand slice and a proven sink-bound slice.  The kernel re-derives
that exact partition and its statement tokens.  Residue that is not fully
classified abstains; sink bindings are positive pure-expression constructions,
never aliases to operand objects.  Fresh containers (`sorted`, `list`, and a
full slice) are eligible only over the proven-cast immutable scalar sequences.
The reader, accumulation/count construction, registered call, and sole report
write remain unconditional.  The pure sink function whitelist takes no
keywords; ordinary string methods may take keywords.  User helpers in the sink
slice remain unsupported.

The sink slice makes static-source flow claims about frozen source only and
makes no claim that report-value computation succeeds.  A raising sink-bound
statement can prevent the report write at execution; nevertheless, its
certified sink-reachability claim is only that the source expression is on the
closed static path to that write.  Accepting such a statement is consistent
with the static-relationship wording ceiling and the v1.1.0 consumability
precedent.

Multi-site inlining is identified by `(source span, call_path_id)`.  Alpha
renames are keyed by function, call path, and original name; the kernel proves
fresh-name injectivity across sites and disjointness from caller-visible names.
`import statistics` is admitted only in the proven sink slice.
`from collections import defaultdict` is admitted only as `defaultdict(list)`
for grouping; sorted unpack is forbidden and every constant operand key must be
an observed frozen group key.

## 2026-08-15 growth-4 vocabulary amendment

This light-process vocabulary round changes no proof obligation or claim
shape.  `from __future__ import annotations` is inert; every other future form
abstains.  `from dataclasses import dataclass` may be bound but any live use
abstains as `dataclass-use-not-modeled`, and class definitions remain outside
the grammar.  Module constants additionally fold literal-only POSIX
`Path("segment") / "segment"` chains under the existing frozen path-binding
equality.  `scipy.stats.wilcoxon` remains a named paired-procedure gap, in the
same unsupported class as `ttest_rel`; it is not admitted.

Batch D is the same v1-scored/v2-development-shadow envelope at
`evaluation/development/dependence-growth-loop/batch-d/`, with fresh author and
review seats.  The pinned Claude CLI exposes `--json-schema`; batch D therefore
passes the frozen primary and hostile review schemas to the transport.  The
retained malformed-response burn remains fail-closed.  Qualification lanes and
their historical call identities are unchanged.

## 2026-08-15 growth-5 vocabulary amendment

This light-process round adds no proof obligation or claim shape. Module
constants may additionally be nonempty tuples of string literals or nonempty
dicts with unique string-literal keys and string-literal values. Their only
admitted reads are a proven literal/constant subscript, iteration in an already
modeled loop position, or membership in an already modeled comparison;
everything else abstains as `module-collection-use-not-modeled`. A subscripted
string value and an ordinary module string constant are folded before the
existing byte-predicate replay, so the kernel continues to receive literal
string atoms only.

The five already sink-bound statistics callables (`fmean`, `mean`, `stdev`,
`median`, and `variance`) may be imported directly from `statistics`; their use
ceiling is unchanged. Annotation-only statements are erased as runtime-no-op
syntax. An annotated assignment is lowered to its plain assignment only when
the existing kernel-derived operand partition proves its target is neither an
operand-slice name nor an alias of one; all other annotations retain the
`annotated-assignment-not-modeled` refusal.

`scipy.stats.wilcoxon` remains a named paired-procedure gap alongside
`ttest_rel`; neither procedure is admitted to the v2 authorization-lock
registry. Batches F1 and F2 retain the batch-E development-only structure with
fresh author, blind-review, hostile-review, and escalation seats.

### Growth-5 addendum G5-9: inert docstrings

A leading string-literal expression at module scope, and a leading
string-literal expression in an otherwise inlinable function body, is treated
only as its Python docstring role. It is excluded independently by the analyzer
and certificate kernel from entry counting, flattening, sink partitioning, and
completeness replay. It binds no name and contributes no flow. A bare string
expression in any non-leading position remains outside the modeled statement
class.

### 2026-08-15 Growth-5 annotation-partition correction

Annotation lowering now consumes the sole operand definition produced by the
existing sink partition, independently in the analyzer and certificate kernel.
There is no annotation-specific operand closure. An annotated target in that
partition, including the frozen reader frame, grouping container, or any proven
alias, abstains as `annotated-assignment-not-modeled`; only a target outside the
partition may lower to its equivalent plain assignment.

Process tier rule: any ticket that introduces or duplicates a classification is
a heavy-process change requiring the corresponding design and adversarial
review. Such a ticket is never a vocabulary-only round.
