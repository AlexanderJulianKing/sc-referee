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
review. Such a ticket is never a vocabulary-only round. A conditional admission
whose premise is a claim about Python semantics likewise requires that premise
to be verified with design-round rigor before the admission ships.

## 2026-08-15 growth-6 vocabulary amendment

This light-process round adds no proof obligation, classification, or claim
shape. Existing per-module `from`-import vocabularies may share one statement;
every imported name remains independently subject to the same closed whitelist,
and one unlisted name refuses the complete statement. Typing imports are inert
only when the same module contains `from __future__ import annotations`, and
their names may occur only inside annotation syntax.

`collections.OrderedDict()` is admitted only as the empty constructor for the
existing plain-dict grouping proof. It receives no distinct container kind or
obligation: key closure, length equations, operand binding, and sorted unpack
are exactly the plain-dict path. OrderedDict-specific methods remain outside the
group accumulator grammar. Batches G1 and G2 retain the batch-F development
structure with fresh author, blind-review, hostile-review, and escalation seats.

## 2026-08-15 growth-7 heavy amendment: procedure census and joint group calls

The group path now performs one four-step, independently replayed procedure
census. It first collects every syntactic SciPy-stats call; then classifies only
`t`/`norm` `ppf`, `cdf`, and `sf` method forms as distribution helpers, with
registered procedure names taking precedence and a startup disjointness
assertion. It next seeds the sole operand closure from the union of every
remaining registered inferential call's arguments. Only after the partition is
complete does it require each helper to be the entire right-hand side of one
assignment and to lie wholly in the proven sink-bound slice. Helper chains may
compose there. A helper reaching the operand closure, an inline helper, or a
contested SciPy-stats census abstains. These are static flow claims only; helper
numeric success is not certified.

Multiple inferential calls are admitted on the group path only when every call
is a registry-flagged row-independent procedure and the kernel replays identical
ordered operand syntax and group bindings for all members. Operand divergence is
checked before either adverse or clearance conclusion is derived. The adverse
statement therefore quantifies over each bound procedure; clearance requires the
same proven-clean shared operands for all. The single-call case uses exactly the
same union seed as the former singular seed. Count procedures remain singular:
mixing a count procedure with any other inferential member abstains as
`procedure-set-count-member-unsupported`.

Development v2 locks may carry a digest-sealed `resolved_callables` set form.
That set form is unavailable to the v1 lock and production controller. The
existing growth-2 trial-declaration limitation remains: count locks additionally
require the exact `One trial is: one row` declaration. Duplicate calls of one
callable authorize the one unique callable while retaining distinct call tokens
in the certificate.

The closed keyword registry admits only intake-neutral SciPy 1.14.0 settings:
`ttest_ind` literal `equal_var` and `alternative`, and `mannwhitneyu` literal
`alternative` and `method` (`auto`, `exact`, or `asymptotic`). `equal_var=False`
is the distinct Welch registry variant with the same operand semantics. Review
verified that these settings do not change which rows enter the operands.
`nan_policy='omit'` and `trim` are excluded because they drop or trim input
observations; permutation settings and `random_state` are excluded because they
change the computation's intake/determinism contract. Nonliteral or unlisted
keywords abstain as `procedure-keyword-not-closed`; this whitelist is
load-bearing and may not grow without a new reviewed premise.

Batches H1 and H2 retain the v1-scored/v2-development-shadow structure with
fresh author, blind-review, hostile-review, and escalation seats. The v2 adapter
remains unregistered and report-only.

Known Growth-7 fuel-reading wall: a distribution-helper call is required to be
the complete right-hand side of one assignment. The same call written inline in
the report sink therefore abstains as `distribution-helper-not-bound`, even
though that position cannot feed an inferential operand. This is conservative
over-abstention, not evidence of dependence, and is expected to recur in Batch H
fuel measurements until a separately reviewed expression-shape extension exists.

## 2026-08-15 operand-rebinding correction and growth-8 amendment

The analyzer and certificate kernel now route every statement-level binding
form through the one independently derived operand partition. An operand name
appearing as a store target in more than one statement abstains as
`operand-name-rebound`; the rule covers plain and annotated assignments and is
binding-form agnostic. Comprehension targets remain scoped to their individual
comprehensions, and repeated discard targets inside one tuple-unpack remain one
statement. This closes the false-accusation route where reader frames or bound
procedure operands were replaced after the recognizer had selected an earlier
definition.

Growth 8 admits module-level helpers called on the proven sink path under the
unchanged Part-F/M restrictions: positional simple arguments, no defaults,
acyclic call graphs, the existing depth bound, and independently replayed
multi-site alpha-renaming. Helper bodies are flattened before the sole sink
partition, so operand reads, aliases, mutations, control, and extra writes remain
subject to the same existing refusals as their hand-inlined forms. Module
constants may be read by a helper; they are substituted in the callee's lexical
scope before hygiene renaming, excluding parameter and local shadows. Reads of
module data names remain outside the module-constant grammar and currently
surface as `module-constant-not-closed` at module parsing.

The reviewed Q3 two-branch return proposal is deliberately detached from this
build. Both the `if`/`else` return form and the early-return form continue to
abstain as `function-return-shape`; no conditional-return production or claim
was added. Batches I1 and I2 retain the v1-scored/v2-development-shadow structure
with fresh author, blind-review, hostile-review, and escalation seats. The v2
adapter remains unregistered, report-only, and labeled `2.4.0-development`.

## 2026-08-15 growth-9 binding amendment: vocabulary and argument expressions

Growth 9 implements only the design memo's binding amendments. Part R1 is
withdrawn. G9-L admits `dict`, `any`, `all`, and `tuple` only in their existing
grammar-appropriate positions; the exact
`[dict(row) for row in csv.DictReader(handle)]` reader materialization; and
nonempty string-list module constants under the existing collection-use rules.
The analyzer and kernel independently verify that the reader comprehension is
one unfiltered, non-async iteration and that `dict(row)` is a one-for-one shallow
copy preserving row multiplicity. Raise guards remain unsupported and surface as
`raise-guard-not-modeled`.

G9-H admits positional argument expressions only through the existing T-3/S3
pure-expression grammar. Mutation remains inexpressible. If any positional
argument is an expression, all arguments are hoisted into deterministic fresh
bindings in source order before substitution, preserving Python's left-to-right
evaluation. Keywords remain forbidden by the existing inlinable-call rule and
starred arguments abstain as `function-argument-starred`. A nested call is still
`function-argument-not-simple` unless it is already an S3 pure call. After the
sole operand partition is derived, a hoisted bare name or subscript rooted in an
operand-slice container abstains at binding time as
`sink-aliases-operand-object`. Calls with no expression arguments retain the
pre-growth-9 flattening and refusal order.

Batches J1 and J2 are checkpoint-cadence configurations only and remain unrun.
J1 reserves authors opus-111 through opus-116, reviewer fable-44, hostile
reviewer fable-45, and escalation opus-27. J2 reserves authors opus-117 through
opus-122, reviewer fable-46, hostile reviewer fable-47, and escalation opus-28.

The separate `scripts/wall_mining_corpus.py` lane is open development fuel, not
measurement. It makes one Haiku generation call per requested script with at
most three concurrent calls, stores only under
`evaluation/development/wall-mining-corpus/run-<n>/`, stamps every emitted JSON
record `record_purpose: development_wall_mining`, applies a deterministic
best-effort declaration translation, and reports v2 shadow wall frequencies.
Its prompts contain no recognizer name or issue taxonomy. It is not registered
in lean, qualification, production, grant, or capability surfaces. The growth-9
shadow identity is `2.5.0-development`.

## 2026-08-16 growth-13 heavy amendment: paired-procedure shadow

The development v2 authority transport adds singular-only `ttest_rel` and `wilcoxon`
under a recursively enumerated, scope-aware, default-deny binding pass. Raw paired
call tokens are counted before callable deduplication; any paired multi-call source
receives no lock. Shadowing, direct rebinding, imported-member mutation, deletion,
and dynamic callable forms remain authority-free. This changes no v1, registry,
grant, pin, qualification, production, or frozen-lane surface.

Only the exact two-vector `scipy.stats.ttest_rel` direct-row form has a new proof
path. One unconditional `csv.DictReader` loop appends finite builtin-`float` or
builtin-`int` values from two distinct columns for every frozen row in file order.
Both sides of row position *i* bind to the same authorized unit and form one
legitimate paired observation. The adverse development-only conclusion requires
the same authorized unit at multiple pair positions; the two sides of one position
are never counted as independent observations. `wilcoxon`, group/crossover operands,
filters, reordering, aliases, rebinding, mutation, and unknown forms abstain.

Paired obligations, facts, certificates, verified conclusions, kernel obligations,
adapter reasons, and wording are distinct from the row-independent group path. The
analyzer and kernel reuse the existing single operand/sink partition independently;
the row-independent path and its cross-operand unit safeguard are unchanged.

### 2026-08-16 Growth-13 code-review repair retention

Binding memo Section 22 closes three review-demonstrated seams without widening the
Growth-13 grammar. The existing authority pass now owns imports and calls by Python
lexical scope, enumerates attribute Store/Del targets across supported binding fields,
and sends every callable or stats-module alias form through one unresolved-alias
census. These failures produce no lock and no authority record.

The paired kernel now receives the exact selected `FrozenMaterialInput` and independently
reconstructs the complete strict-CSV paired fact from its bytes and references before
comparing it with the supplied trusted fact. Exact header and row order, source strings,
observation and unit ids, finite cast representations, counts, ASCII proof, file and
asset references, and every obligation field are therefore bound at `paired-fact-closure`.
Paired operand walrus targets reach the existing sole operand/sink partition before the
generic named-expression refusal; non-operand named expressions remain unsupported by
their existing reason.

## 2026-08-16 growth-15 heavy amendment: abort-only guard fallthrough

Growth 15 admits only the fallthrough semantics of a direct, uncaught
`if CONDITION: raise ValueError(MESSAGE)` or `SystemExit(MESSAGE)` guard before the
row-independent procedure and selected sink. The full condition language contains
only exact real-builtin-`len` comparisons `len(NAME) < 2` and `len(NAME) != 2`, plus
`or` trees of those atoms. Every name must map through the one existing operand/sink
partition to its already established row-sequence, group-container, or exact
procedure-operand role. `not NAME` remains syntax-only wall decomposition: it creates
no role, truth result, token, certificate, or conclusion. Attributes, subscripts,
other operators or literals, caught or nested raises, shadowed `len`, post-sink
guards, and incomplete raise inventories remain unsupported.

The development certificate carries an ordered source/role token for each admitted
full guard. Tokens bind source path and span, lexical and inlining call path, source
order, complete condition and raise AST digests, and the existing role of each name.
They carry no material fact, sequence, cardinality, value, or analyzer-supplied truth
claim. The certificate kernel independently inventories the source guards, proves the
real builtin binding, reconstructs their roles from its sole partition replay, and
requires exact token equality. A true replayed guard returns only the existing
`sink-controls-operand-flow` abstention; all-false guards merely permit the unchanged
dependence conclusion equations to run.

The ordinary group kernel now requires exactly one controller-selected
`FrozenMaterialInput`. It independently reconstructs the complete current
`GroupValueSequenceFact` from the obligation and digest-bound bytes under the same
strict-CSV budgets, line models, casts, bucket closure, ordering, identities, source
values, cast representations, and material references as the controller. The supplied
fact is accepted only for complete equality comparison and is then discarded as a
semantic input. Source and reader replay, operand and conclusion equations, guard
truth, certificate identity, and the returned verified fact all consume the one
kernel-replayed object. There is no material-free verified compatibility path.

This amendment remains confined to the unregistered development v2 shadow. It changes
no v1 recognizer, refusal registry, grant, pin, qualification, capability, production,
public, or frozen-lane surface.

## 2026-08-17 growth-14 binding amendment: closed pandas source recognition

Growth 14 implements only the revived contract in binding design-memo Sections 17-19.
The development-v2 shadow carries one immutable literal runtime premise for isolated
Python 3.11.15 with pandas 3.0.5, NumPy 2.2.6, SciPy 1.14.0, and python-dateutil
2.9.0.post0. The premise binds the pandas distribution artifacts and complete RECORD
counts; it is not a grant, installed pin, runtime dependency, qualification, or public
capability. The recognizer neither imports pandas nor inspects or mutates the runtime.

Before pandas source classification, the analyzer and kernel independently require one
immutable whole-root repository snapshot, its complete associated regular-file records,
full-digest identities, and the exact development runtime-premise identity. Missing,
ambiguous, symlinked, shadowing, or customization-route inventories refuse. No case id
or frozen inventory digest appears in recognizer code.

The only pandas material form is the original digest-bound ASCII CSV byte stream with
no terminal LF. Physical validation occurs before decode or record splitting and
rejects every second representation, including terminal LF, CR/CRLF, leading or doubled
LF, blank records, BOM, NUL, quotes, escapes, ragged rows, empty or whitespace cells,
non-ASCII bytes, and the complete pandas-3.0.5 missing-token vocabulary. The group and
numeric grammars are the exact tiny reviewed grammars; values reconstruct only as the
reviewed `int64` or `float64` domain, and `.dropna()` must be proven row-preserving.

Pandas syntax extends the pre-existing single operand/sink partition. Detailed frame,
base/final Series or ndarray lineage, procedure arguments and result targets, aliases,
rebindings, mutations, summaries, and writer flow are derived only inside that partition
in both analyzer and kernel. There is no pandas-local classifier and no
`pandas-binding-not-closed` reason. Source failures use the eleven fixed analyzer/domain
reasons and their total precedence; alias, rebind, and mutation siblings retain the
existing partition reasons.

The certificate kernel applies exactly six singleton-preemptive pandas obligations in
the reviewed order: package identity, source closure, single partition, material domain,
operand values, and result sink. It independently reparses source, rederives the package
and partition, scans the original bytes with logic distinct from the analyzer, returns a
new value-equal fact object, and binds certificate identity and conclusion to that
returned object. Supplied facts are equality checks only and never substitute for byte
reconstruction.

This build remains unregistered and report-only. It changes no v1, authority
translation or lock, grant, installed pin, registry, capability, qualification,
production/public, harness, wall-corpus, evaluation, or frozen-lane surface. Frozen
re-measurement, batches, manifest regeneration, commit, and push remain orchestrator
operations after independent code review.

### 2026-08-17 Section-20 manifest-bijection repair build record

The focused Section-20.2/20.4 repair binds the controller-persisted
`observed/files.jsonl` artifact as one immutable value containing its exact bounded
`file_manifest_ref`, original canonical JSONL bytes, and SHA-256 digest. The controller
captures those already-written bytes before the development observer runs; linked
interaction re-entry applies the same capture. Missing, unreadable, symlink-resolved,
changed-during-read, or otherwise ambiguous artifacts yield no manifest input. The
capture layer does not parse entries or assert completeness.

To preserve the accepted v1 scientific-check release identities and installed pins,
the binding is a controller-local frozen subtype of the existing
`FrozenInspectionContext`; the release-pinned scientific-check core and integration
modules remain unchanged. This placement adds no registry entry, production adapter,
public record, or storage behavior. The subtype preserves the base v1 manifest
projection and context digest exactly; its separately held immutable manifest value is
not a second v1 projection or digest channel.

The analyzer and certificate kernel consume only that frozen value. Each separately
parses the original bytes, requires byte-exact canonical JSONL lines, establishes the
complete bidirectional match to snapshot-associated file records, validates their
identity and byte metadata, and retains every entry until the existing non-regular,
symlink, identity, and pandas-shadow refusals run. Neither path accepts a parsed
manifest, a completeness flag, or the other path's match result. The existing pandas
package-identity refusal boundary and all non-v2 conclusions remain unchanged.
Growth 14 binds the independently validated manifest digest only through
`PandasPackageIdentity` and the resulting certificate identity.

### 2026-08-17 Section-20.5 adjacent-import-candidate repair build record

The final focused repair derives the source, bytecode, and extension suffix categories
from the running proof interpreter's `importlib.machinery` only when its exact Python
version, implementation, cache tag, and SOABI match the immutable development-runtime
premise. The categories must be nonempty, path-safe, duplicate-free, and exactly equal
to that interpreter's combined reported suffix vocabulary; mismatch or ambiguity
refuses at the existing pandas package-identity boundary. The recognizer does not
import pandas, execute project code, inspect the external runtime, or carry a manually
written suffix vocabulary.

After each proof's independent exact manifest-to-record bijection, the analyzer and
kernel separately enumerate `pandas` plus every derived module suffix in every
import-reachable adjacent directory, together with the adjacent `pandas` package path,
and compare those candidates with their own proven-complete inventory. Any regular,
non-regular, or symlink entry at a candidate path refuses package identity. Neither
proof consumes a certificate-carried path set, completeness assertion, analyzer result,
or shared package-identity decision. Existing customization-path, all-regular-file,
source/material identity, certificate, conclusion, and refusal semantics are unchanged.

Permanent regressions retain the manifest-record omission refusal and add the exact
`workflow/pandas.so` analyzer/direct-kernel/adapter route, ordinary-versus-`-I` runtime
control, every suffix reported by the pinned importer, adjacent package-path entry
kinds, mismatched running-interpreter identity, and ambiguous importer vocabulary.
This remains unreviewed build evidence only and authorizes no re-measure or batch.
