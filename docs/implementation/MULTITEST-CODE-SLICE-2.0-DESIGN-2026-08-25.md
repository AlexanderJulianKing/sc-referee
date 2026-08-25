# Multiple-testing code slice 2.0 architecture-inversion design — 2026-08-25

**Status:** build-ready design, Revision 2; documentation only in this session

**Version:** detector/check/adapter `2.0.0`, development lane only

**Normative predecessors:**

- [`MULTITEST-CODE-SLICE-1.0-DESIGN-2026-08-24.md`](MULTITEST-CODE-SLICE-1.0-DESIGN-2026-08-24.md), Revision 2.3, `sha256:ac3306f3e58248ac03fee9c75f06d7a9f8a045547ae84f85baae56ecc98fb651`;
- [`MULTITEST-CODE-SLICE-1.1-DESIGN-2026-08-25.md`](MULTITEST-CODE-SLICE-1.1-DESIGN-2026-08-25.md), Revision 2.1, `sha256:08f8be283dff2f606af935f8aad2de8b14475d73ddd91e6c3bf812ed6e45e484`; and
- [`MULTITEST-RECALL-RECON-E10-2026-08-25.md`](MULTITEST-RECALL-RECON-E10-2026-08-25.md), `sha256:ab32decbca6049d4f5ad16d539281434b643d39a26f1be856a9b39172cd2ad93`.

**Opened-envelope evidence:**

- Envelope 10 at commit `0abb544`: results `sha256:6bfd70dda4d7977b1ad3e1729722179f03381714c7fef74e9781091752ca6b5b`, role map `sha256:ced43841cb53e3527812e6dc5b4e361e635ca77fc7ca64129cae80d5c226c648`;
- Envelope 11 at commit `0380972`: results `sha256:74533215038db4be2c69f3ec56ff76dc54f1e3645d60a8930e7e98ac5f91eeb8`, role map `sha256:1321ff42543dc11de13433a76080bb49ffa33556fb395ee0ef46f3caeac6f90f`.

**Architectural reference:**
`src/sc_referee/scientific_checks/code_csv_dependence_dataflow_v3_1.py`,
`sha256:ab327f5e2f81128febf381b562c1aacce6a272e79e8ab852a5a4c64ecd27ea75`.
Its patterns are copied into new multiple-testing modules; the reference file is never edited or
imported through private helpers.

Envelope 10 and Envelope 11 each scored `0/6` first-contact recall and `0/9` false accusations.
Both passed every hard stop. Delta 1.1 made the first wall more honest but did not change recall:
real scripts still had to satisfy roughly nine independent whole-module grammars before one
candidate could exist. Version 2.0 changes that architecture. The three identity censuses and the
repeated-construct census remain whole-module; the new dynamic-execution, API-rebinding, and
control-prevention integrity scans are whole-module abstention surfaces; value claims are otherwise
proved only on bounded slices. This is a new accepted-policy surface and requires ADR-0079 before
implementation.

## 1. Decision, claim, and hard boundary

The 2.0 analyzer has two proof domains:

1. **Whole-module syntactic censuses.** Every registered test call, correction-terminal spelling,
   statistics-prefix call, and repeated construct in `analysis.py` is inspected regardless of
   reachability, helper use, or slice membership. The closed dynamic-execution and API-rebinding
   scans and the control/prevention registry are also whole-module.
2. **Value slices.** Operand identity and row completeness are proved by backward slices from the
   registered family calls. P-value identity, correction coverage, decisions, controls, and sinks
   are proved by forward slices from every registered family p-value.

There is no chosen `main`/module setup grammar, no module-setup statement enumeration, and no
general read-only-consumer allowlist. A `with`, `try`, class, arbitrary assignment, validation call,
or project helper outside both value slices is not inspected merely because it exists. The global
censuses and integrity scans still inspect their exact channels. In particular, no node in the
whole-module control/prevention registry is eligible for the off-slice admission: its backward
provenance and ability to prevent a slice node are always resolved. The syntax-wide A5 binding
census and tracked-outcome stability closure bring matching bindings or mutations onto a slice;
those are named exceptions, not a return to whole-module value interpretation.

A 2.0 candidate means exactly what the 1.0/1.1 candidate meant: the authorized CSV and contract
family have exactly `N` locally proved registered tests; every member has a proved raw or recognized
adjusted conclusion; correction membership is `none` or `strict_subset`; and at least one concluded
member is outside recognized correction coverage. It does not mean no correction existed outside
the analyzed source, that the analysis is otherwise wrong, or that a result is publishable. The
absence of a recognized correction in the analyzed source does not establish that no correction was
applied.

The following are absolute:

- project code is parsed, never imported or executed;
- code, CSV values, exact API identities, and structural slots are the only detector evidence;
- comments, docstrings, reports, Markdown, identifier prose, output labels, and format text never
  establish or defeat a predicate;
- every unresolved slice edge abstains; it is never silently dropped;
- all `N` calls, `2N` operands, `N` p-value roots, and `N` conclusions must be proved; and
- the development controller continues to emit zero Findings.

## 2. Identities, contract, wording, and isolation

### 2.1 Versioned identities

```text
check:authorized-complete-family-correction-over-code-test-battery@2.0.0
adapter:authorized-complete-family-correction-over-code-test-battery:code-csv-v1@2.0.0
detector:bounded-code-csv-multiple-testing-conflict@2.0.0
method-conflict-binding:authorized-complete-family-correction-over-code-test-battery-v1:development
```

Only the development binding advances. Historical `1.0.0` and `1.1.0` modules remain registered
for replay and locked-record validation. There is one active MT code binding in the development
projection and none in the ordinary/qualified projection. Maturity remains `question_only` and
`production_finding_permitted` remains false.

### 2.2 Contract and evidence projection

Scientific-requirement contract profile `1.2.0` is byte-unchanged. The authority remains the group
column plus ordered outcome-column family; group values and uniform registered API are derived.
Family-member rule and correction scope remain version discriminators only.

`MultipleTestingDataflowFacts`, normalized observation, evidence roles, canonical operands,
receipts, and candidate projection retain their 1.1 field sets and validators. Contract `1.0.0`,
`1.1.0`, and `1.2.0` golden values, digests, manifests, and all seven error-string categories remain
byte-identical.

### 2.3 Wording decision

The existing wording profile is reused byte-for-byte:

```text
method-conflict-finding:code-csv-complete-family-correction-requirement-conflict-v1@1.0.0
sha256:80c4bb3c0afd75b290ab02a195e5285528f982554ab46b373e63072232902259
```

No v2 wording is needed. The inversion resolves the same slots: `CSV_PATH`, `GROUP_COLUMN`,
`OUTCOME_COLUMNS`, `AUTHORIZED_COUNT`, `PERFORMED_COUNT`, `CORRECTED_COUNT`, `UNCORRECTED_COUNT`,
and `TEST_API`.

### 2.4 Qualified-lane isolation

Qualified pseudoreplication `3.1.0`, complete-domain, GrantPins, grants, qualification records,
threshold policies, metric sets, Finding objects, wording profiles, `method_conflict_grant_pins.py`,
and every `code_csv_dependence_dataflow*.py` are byte-untouched. The two-registry differential gate
proves byte equality and non-derivation. Only development MT manifests/binding, the lane-inclusive
registry digest, and downstream locks directly binding that digest may change.

### 2.5 Required ADR-0079 notes

ADR-0079 must record all of the following as policy, not implementation convenience:

- the whole-module/value-slice inversion and the whole-module control/prevention exception to
  off-slice admission;
- the abstention-only dynamic-execution and API-rebinding censuses;
- the section-4.7 narrowing under which an uncorrected family with `N >= 3` admits only bare `0.05`,
  with the deliberate recall cost that genuinely uncorrected `0.01` and `0.1` families are missed;
- the corresponding MJ-6 asymmetry residual: once any recognized correction is present, the
  admitted comparison set remains `{0.01, 0.05, 0.1}`. Therefore an `N = 4` strict-subset analysis
  whose excluded raw members compare at a pre-registered `0.01` remains convictable. The product
  rule does not catch `0.01 * 4 = 0.04`; this is a stated residual, not evidence that the level was
  uncorrected;
- the versioned hierarchy copy and its sole terminal-rendering exclusion;
- the traceable live-conditional decision in 3.1: this design restores an abstaining conservative
  rule and does not restore candidate-producing branch traversal withdrawn by 1.0 Revision 2.3; and
- the surviving string `analysis-scope-structure-unsupported` changes predicate meaning. In 1.1 it
  included the chosen module/setup grammar; in 2.0 it denotes only the tracked outcome-sequence
  stability predicate in 4.2. The 1.1 and 2.0 uses are different predicates and must never be
  compared across versions as if they were one metric or reason distribution.

## 3. Whole-module syntactic censuses

The censuses run over `tuple(tree.body)` after docstring removal and bounded parsing. Calls in
literal-false branches, live branches, handlers, `finally`, `with`, `match`, classes, lambdas,
comprehensions, called helpers, and uncalled helpers remain visible.

### 3.1 Registered-test-call census

The registry is byte-restated from 1.1:

```text
scipy.stats.ttest_ind
scipy.stats.mannwhitneyu
```

Import aliases resolve to these identities. Dynamic imports, unresolved receiver identity, partial
application, or ambiguous callable aliases abstain `api-resolution-ambiguous`; they never make a
registered call disappear.

The 1.1 call-instance rules are retained by value:

- `N` separate unconditional calls contribute `N` instances;
- a call in a proved contract-family loop/comprehension contributes its exact normalized factor;
- a called X4 helper contributes only its call-site expansions and is not double-counted at its
  definition;
- a registered call in an uncalled helper contributes one conservative instance;
- a registered call under exact `ast.Constant(value=False)` `If`/`While` stops
  `test-battery-cardinality-unresolved` and is never asserted to execute;
- a registered call in any other conditional body, `try` part, handler, `else`, `finally`, `with`,
  or `match` stops `authorized-family-test-census-incomplete`; and
- unresolved loop/comprehension/helper multiplicity stops `test-battery-cardinality-unresolved`.

The live-conditional rule is an explicit safety narrowing: it restores conservative abstention for
these bodies while preserving 1.0 Revision 2.3's withdrawal of the unsound traversal that counted
their calls as established executions. No live or unresolved conditional body contributes a
candidate-producing instance.

The resolved count must equal `N` before operand identity. Below `N` is
`authorized-family-test-census-incomplete`; above `N` is
`extra-registered-test-outside-authorized-family`.

### 3.2 Correction API and terminal censuses

The recognized API registry is byte-restated:

```text
statsmodels.stats.multitest.multipletests
statsmodels.stats.multitest.fdrcorrection
scipy.stats.false_discovery_control
sc_referee.calculation_checks.bh.benjamini_hochberg
```

The accepted `multipletests` methods remain:

```text
b
bonferroni
s
sidak
hs
holm-sidak
h
holm
sh
simes-hochberg
hommel
fdr_bh
fdr_by
fdr_tsbh
fdr_tsbky
```

Omitted `multipletests` method resolves to `hs`; omitted `fdrcorrection` method to `indep`; omitted
`false_discovery_control` method to `bh`. The latter axis is only omitted, literal `0`, literal
`-1`, or literal `None`. Input coverage is determined from forward-slice p identities. Unsupported
methods, axis, keywords, returns, or membership retain the existing correction reasons.

Independently, the callee-terminal census ASCII-lowercases only complete-callee `Name.id` or
`Attribute.attr` and matches:

```text
multipletests
fdrcorrection
false_discovery_control
multicomp
fdr_correction
p_adjust
padjust
bonferroni
holm
sidak
benjamini*
```

`benjamini*` is an ASCII prefix. A match not discharged by the exact recognized-call grammar
abstains `unresolved-manual-correction-present`, even wholly off-slice. Non-callee identifiers never
enter this channel.

### 3.3 Statistics-prefix census

The exact registry remains byte-equal to dependence v3.1 and MT 1.1:

```text
scipy.stats
statsmodels
pingouin
pymer4
bambi
gpboost
merf
linearmodels
sklearn
pymc
numpyro
stan
cmdstanpy
rpy2
lifelines
```

Registered family and recognized correction calls are discharged. The sole exemption remains the
exact 1.0 `scipy.stats.sem(V)` output-only grammar. There is no `scipy.stats.t.ppf` exemption. Every
other match abstains `unresolved-inference-sibling-present`. The adapter's scan of every other
Python file for these imports is unchanged.

### 3.4 Repeated-construct census — fourth global census

The fourth global census records every `ast.For`, `ast.ListComp`, `ast.SetComp`, `ast.DictComp`, and
`ast.GeneratorExp`, plus every call resolving to this byte-restated registered-draw registry:

```text
numpy.random.choice
numpy.random.randint
numpy.random.random
numpy.random.random_sample
numpy.random.sample
numpy.random.ranf
numpy.random.standard_normal
numpy.random.normal
numpy.random.uniform
```

It also records receiver methods `choice`, `integers`, `random`, `standard_normal`, `normal`, and
`uniform` only when the receiver has the exact closed binding
`numpy.random.default_rng([CLOSED_SEED])`. Occurrence discovery is purely syntactic and
whole-module. The section-5 resampling trigger separately proves authorized-data provenance,
cardinality, repeated-output reduction, and conclusion/sink control. An unresolved cardinality on a
recorded construct consuming authorized family data retains `resampling-cardinality-unresolved`; it
is never dropped because the construct is off the ordinary operand/p-value slices.

### 3.5 Dynamic-execution census

The following closed whole-module list is always abstention-only and returns
`api-resolution-ambiguous`:

- calls to unshadowed builtins `exec`, `eval`, `compile`, or `__import__`;
- `importlib.import_module`, including exact import aliases;
- unshadowed `getattr(MODULE, ...)` or `setattr(MODULE, ...)` when `MODULE` resolves to any imported
  module or an exact alias of one; and
- mutation of the mapping returned by unshadowed `globals()` or `locals()`, directly or through an
  exact identity alias. Mutation is exactly subscript `Store`/`Del`, `__setitem__`, `update`,
  `setdefault`, `pop`, `popitem`, or `clear`.

Plain nonmutating `globals()`/`locals()` calls are not on this list. No other spelling, reflection
API, or inferred intent is added. Presence of any listed shape anywhere in the parsed module stops
before slicing; nothing dynamically generated may be assumed absent from the three API censuses.

### 3.6 API-rebinding census

This syntax-wide integrity census also returns `api-resolution-ambiguous`. It fires on either:

1. any `Store` or `Del` to an `ast.Attribute` whose receiver resolves to a statistics-prefix module,
   a registered-test module, or a recognized-correction module, including exact import-alias
   closure; or
2. any local `FunctionDef`, `AsyncFunctionDef`, `ClassDef`, argument binding, or `ast.Name` in
   `Store`/`Del` context whose spelling shadows an import alias that is actually live in this module
   and resolves to a registered test/correction API or to a canonical module/path prefix used to
   resolve one.

The original `import`/`from ... import ...` binding that creates a live alias is excluded; any later
binding of that same alias is not. A spelling that merely equals an API terminal is insufficient:
in a module with no matching live import, variables named `ttest_ind`, `multipletests`, or
`benjamini_hochberg` do not enter this census. This census never attempts source-order recovery after
a real live-alias rebind and never treats the hidden registered identity as absent.

### 3.7 Whole-module hierarchy and execution-prevention registry

The hierarchy registry is evaluated over the whole parsed module and is expressly excluded from
section 1's off-slice admission. Its closed control-node set is every 1.0 control node:

- a registered test-call argument, recognized correction-call argument, p-derived conclusion
  operand, or family-container insertion key/value when the value determines execution, membership,
  threshold, branch, or member selection rather than serving as the ordinary payload;
- `ast.If.test`, `ast.IfExp.test`, `ast.While.test`, `ast.Assert.test`, `ast.Match.subject`, every
  non-`None` `ast.match_case.guard`, each `ast.For`/`ast.AsyncFor` iterable, each comprehension
  iterable or `if`, and every boolean short-circuit operand feeding any node in this list; and
- any argument/member that selects which member a registered sink emits.

It additionally includes every `return`, `break`, `continue`, and `raise`, and every call resolving
exactly to `sys.exit`, when that early exit can prevent any backward operand/family node, forward
p/correction/conclusion/sink node, or another enumerated control node from executing. For `return`,
`raise`, and `sys.exit`, provenance includes their value/exception/cause/arguments and the control
expressions governing reachability. For `break` and `continue`, it includes the enclosing loop and
all control expressions governing reachability.

For every registry entry, compute the bounded backward name/member closure from 1.0 section 5.1 by
value. Resolve the header set of each authorized-reader projection independently. A projection
contributes to joint derivation only when its resolved header set is nonempty and is a subset of the
contract outcome-column set. A mixed projection containing an identifier, group, metadata, or any
other non-outcome header contributes nothing, even when it also contains two or more outcomes. A
scalar is jointly derived exactly when the union of all contributing pure-outcome projection sets
in its closure contains at least two distinct contract outcome headers. Thus
`frame[["batch_id", GROUP_COLUMN, *OUTCOMES]].isna()` is a data-integrity check, not a scientific
gate, while `frame[OUTCOMES]`, two separate pure outcome projections, and the all-NumPy omnibus
fixtures remain jointly derived. If a local family p value, recognized reject or adjusted-p value,
A5 alpha value, or jointly-derived value reaches the control edge, abstain
`hierarchical-gatekeeping-present`. The exact 4.8 terminal-rendering transport is the sole exclusion.
If the AST control-flow/dominance analysis cannot resolve whether the node can prevent a slice or
enumerated control node, abstain `pvalue-control-dependence-unresolved`. A resolved untracked control
edge does not by itself abstain.

The listed nodes are a minimum terminal registry, not an execution-prevention ceiling. Any other
node whose evaluation can prevent an enumerated control node or a slice node from executing is also
a control edge and receives the same backward-provenance classification. This residual is resolved
only from AST control-flow, short-circuit, and dominance structure; identifier wording and prose are
never consulted.

## 4. Slice construction and value domains

### 4.1 Graph, fixed point, and limits

The analyzer builds one bounded AST parent map and lexical binding index, not a general program
representation. The backward worklist starts at both operands of every resolved registered-call
instance and at iterable/member bindings needed for its family position. The forward worklist starts
at that instance's abstract `pvalue` member. Worklists are deterministic by source position then
family position and retain the 1 MiB, 50,000-node, 16-definition, X4-depth, and recursion ceilings.

A Name load has one usable reaching definition only when lexical resolution plus closed X4
substitution yields one value. Multiple possible bindings, `global`, `nonlocal`, unresolved closure,
or a store/delete affecting a tracked value abstains. Source position is not used to assume a
conditional store executed. Format-string arguments are traversed for lineage; format text is never
read, matched, or compared.

### 4.2 Closed outcome-sequence normalization

This is the sole normalizer for outcome-name sequences and tables. It runs only when such a value
feeds call multiplicity, authorized outcome projection, or outcome-label/position conclusion
membership. It never reconstructs a p-value container or determines correction coverage; section
4.6 is the sole grammar for those triggers. The outcome normalizer supports:

- flat/nested literal List/Tuple values within A1 bounds;
- constant dictionaries within A2 bounds and insertion order;
- A3 `Assign`/`AnnAssign` targets and values;
- exact identity aliases and same-kind List/Tuple `+` concatenation;
- exact literal integer indexing/slicing of a proved finite sequence;
- direct iteration, `enumerate(SEQUENCE[, start])`, and `zip` when all values are exact and the
  result maps order-equal to the contract family;
- one-generator, no-`if`, non-async List/Dict comprehensions using exact destructuring and literal
  member projection over a proved finite family; and
- exact X4 actual/formal/return and loop-target substitution.

Battery projection must be byte-for-byte order-equal to the contract list with each member once.
Set, sort, reorder, dynamic key, filter, duplicate, unknown member, or unresolved comprehension
never proves battery cardinality. An exact subset is retained only as correction-coverage metadata;
it never proves the complete battery.

The tracked outcome sequence remains immutable by value. Form its transitive exact-name alias
closure and inspect every use. Mutation, alias mutation, rebinding, `del`, slice/subscript store, or
unresolved escape anywhere stops `analysis-scope-structure-unsupported`. Refused receiver attributes
remain `append`, `remove`, `pop`, `insert`, `extend`, `clear`, `sort`, `reverse`, and `__setitem__`.
This stability closure belongs to the backward family slice; unrelated sequences are off-slice.

### 4.3 X4 slicing

Copy X4/X4a from dependence 3.1 by value: unique top-level synchronous helpers; simple-name calls;
closed ordinary binding/defaults; no recursion, decorators, async, `global`, or `nonlocal`; depth at
most two; deterministic alpha-renaming; one expansion per call site; and the lambda,
return-destructuring, loop-site, and pure-output-helper amendments.

Expand only helper statements needed by a backward operand/family edge, forward p edge, or control
edge that can prevent such a node. Arbitrary sibling statements in the same helper are off-slice.
Unsupported statements on a required path retain exact X4 reasons. An arbitrary uncalled helper body
is ignored except for its globally censused calls.

A4 is retained without the dependence sibling's `None` tolerance. Resolving a path formal creates
no reader frame at the call site; helper-returned frames/p values require ordinary X4 expansion.

### 4.4 Backward operand proof

Every `2N` operand slice terminates at one authorized reader of the exact authority path. Accepted
reader roots remain the 1.1 pandas/NumPy grammars; `csv.DictReader`, record dictionaries, `open`,
NumPy load, JSON, and arbitrary reader calls remain unsupported.

Group split/outcome projection is closed to:

1. exact `.loc[MASK, OUTCOME]` with one same-frame group equality;
2. exact `.query(LITERAL)[OUTCOME]` whose sole string argument matches by value
   `\A(?P<header>[A-Za-z_][A-Za-z0-9_]*) == (?P<quote>['"])(?P<value>[A-Za-z0-9_.-]+)(?P=quote)\Z`,
   with any extra query predicate proved true for every already selected row; and
3. A7 same-frame boolean subscript `FRAME[FRAME[GROUP_COLUMN] == GROUP_VALUE][OUTCOME]`, including
   reversed equality.

`.values`, `.array`, no-argument `.to_numpy()`, no-argument `.copy()`, and exact A6
`.astype(CLOSED_DTYPE)` are row-identity edges. No mask, `isin`, conjunction, negation, dynamic
query, row-affecting helper, discovery/validation split, missing-value filter, sample, deduplication,
or strict subset is admitted. Each computed CSV row-index set must be byte-equal to all authorized
rows for that group; failure is `selected-group-row-completeness-unproven`.

### 4.5 Registered p-value roots

Each registered call instance creates an abstract `pvalue` member. That identity may be exposed only
through:

- exact `.pvalue` on the direct result or an identity-bound result name;
- exact literal position `1` on that result; or
- the second target of exact two-target List/Tuple destructuring of the direct registered call.

The position-1 forms copy the registered-return projection pattern from dependence v3.1 and are
pinned to the SciPy return layout in lockfile versions `1.17.1` and `1.18.0`; changing either pinned
version or admitting another version requires a reviewed grammar change. They do not recognize a
generic tuple, wrapper, imported result, or call because its second value is named `p`. Sibling
registered-result members—including `.statistic`, `.df`, and literal position `0`—are off the
p-value slice: they establish neither a p root, correction coverage, nor a conclusion. Every
admitted root still terminates at the registered call's pinned abstract `.pvalue` member in this
source. Imported, file-loaded, or unresolved-call values retain
`upstream-correction-lineage-unresolved`; a local root with an unresolved consumer retains
`unresolved-pvalue-consumer`.

### 4.6 Forward p-value proof and consumer totality

For every registered p root, enumerate every AST Load, member, actual/formal/return, container, call,
store, comparison, control, and sink consumer to a fixed point. Each consumer edge is classified
exactly once as:

1. closed identity/presentation;
2. closed family-container transport;
3. recognized correction input/return;
4. recognized manual adjustment;
5. recognized decision/conclusion;
6. registered output sink;
7. one named abstention guard; or
8. unresolved, returning `unresolved-pvalue-consumer`.

There is no output-only escape hatch for an unresolved edge. A proved conclusion on one branch does
not excuse an unresolved call, transform, store, export, container, or return on another.

Closed scalar edges are copied narrowly from the v3.1 p-depth pattern:

- unshadowed `float(P)` with exactly one direct registered p identity and no keywords is a numeric
  identity edge;
- unshadowed `bool(C)` with one recognized decision comparison is a decision identity edge;
- `str(P)`, f-string payload, literal-string `.format`, and `%` formatting with a literal format
  string are presentation-only edges when their result proceeds solely to registered output; and
- `round(P[, K])` is never a decision identity. On a p-to-decision path it retains
  `pvalue-scalar-cast-or-rounding-unsupported`; invalid scalar-call shapes retain
  `unresolved-manual-correction-present`.

Thus exact `float(P)` moves from the 1.1 scalar abstention to a one-to-one local p identity.
`float(P) * N`, `float(P / N)`, `float(adjust(P))`, attribute/dynamic float, or any nested call does
not: the p root remains visible to the off-grammar guard.

The p-container reconstruction grammar is separate from 4.2 and complete. A `PITEM` is exactly one
registered p identity or that identity's exact literal field in a reconstructable family record. A
`PSEQ` is admitted only through these productions:

1. a List/Tuple display whose every element is one `PITEM`, or a Dict display with no unpacking,
   unique literal string/integer keys, and one `PITEM` per value, preserving source insertion order;
2. a Name with exactly one usable reaching definition of `PSEQ`, or an exact identity alias of it;
3. an exact literal integer slice of `PSEQ` with omitted/literal bounds and omitted or literal-one
   step; literal integer indexing yields one `PITEM`, not a sequence;
4. same-kind List/List or Tuple/Tuple `+` concatenation of two `PSEQ` values;
5. one non-async, one-generator, no-`if` List/Tuple comprehension over a proved family-record
   sequence or exact `zip(OUTCOME_SEQUENCE, PSEQ)`, with exact destructuring and an element that is
   solely the p field/target;
6. a list builder bound once to `[]` or an exact `PSEQ`, followed only by source-ordered,
   unconditionally executed `.append(PITEM)` or `.extend(PSEQ)` in the same lexical/X4-expanded
   path; or
7. a List/Dict builder of exact final length/key set whose literal integer/key subscript positions
   are each stored exactly once with one `PITEM` before any load.

Every admitted production must reconstruct a unique ordered tuple of family positions. Duplicate
positions, Set/SetComp, mismatched concatenation kind, nonliteral/dynamic key or slice, filtering,
reordering, conditional or duplicate store, alias mutation, attribute store, unresolved escape, or
any member with zero/multiple p origins fails the grammar. A family-bearing container failing this
grammar abstains `pvalue-family-collection-unresolved`; an otherwise unknown consumer abstains
`unresolved-pvalue-consumer`.

Correction-input classification uses only that grammar. Thus `pvals[:3]` is an exact first-three
`strict_subset` correction input when `pvals` is a complete ordered `PSEQ`; `pvals + extra` is an
exact correction input only when both operands are same-kind reconstructed `PSEQ` values and their
concatenation has unique known positions (otherwise `correction-family-lineage-unresolved`); and
direct `zip(OUTCOMES, pvals)` is a sequence of pairs, not `PSEQ`, so passing it directly to a
recognized correction abstains `correction-family-lineage-unresolved`. Only production 5's exact
p-field projection from that zip can become a correction input. In that production, section 4.2
proves only the outcome-sequence side and order; section 4.6 alone proves the p side and coverage.

An exact `pandas.DataFrame(P_RECORDS)` construction and later DataFrame/Series mutation are not
recognized in slice 2.0. Any family p entering that pipeline abstains
`unresolved-pvalue-consumer`. This is the explicit Envelope-11 P5 residual.

### 4.7 Correction, manual arithmetic, and threshold partition

Recognized correction input/return grammars, input-determined coverage, default methods, and
unsupported-return abstention are unchanged. A future correction-registry addition remains a
candidate-surface change requiring review.

The sole manual adjusted-p grammar remains:

```text
min(P * N, 1)
min(N * P, 1)
numpy.minimum(P * N, 1)
numpy.minimum(N * P, 1)
```

`N` is an integer literal or closed module constant exactly equal to the family census. Every other
p-derived BinOp/Call transform abstains `unresolved-manual-correction-present`, except the exact
scalar identity/presentation edges in 4.6, which never classify correction coverage.

Direct-p comparisons remain exclusive to threshold classification. Operators are exactly `<`,
`<=`, `>`, `>=`, in either operand order. The threshold is a bare numeric literal or A5 Name with
exactly one binding event anywhere in the parsed module. Decimal construction uses the literal's
source text after permitted underscore removal, or `Decimal(repr(value))` when source text is
unavailable, never `Decimal(float)`.

For an exact family `N >= 3` with no call admitted by the recognized-correction grammar, the only
admitted bare decision literal is `{0.05}`; bare `0.01` and `0.1` abstain
`unresolved-decision-threshold`. When at least one recognized correction call exists, the existing
comparison set `{0.01, 0.05, 0.1}` remains for its resolved raw/adjusted member conclusions. The
product rule is unchanged in both cases: for exact `N`, if `a * N` is in `{0.01, 0.05, 0.1}`, abstain
`unresolved-decision-threshold`. Arithmetic, power, helper return, table cell, destructured value,
dynamic value, or second A5 binding also abstains that reason. Direct-p comparisons remain excluded
from the off-grammar transform census, preserving the order-14/order-15 partition. This deliberate
narrowing misses genuinely uncorrected analyses using `0.01` or `0.1` so that a plausible
pre-registered corrected decision level cannot be convicted from code silence.

### 4.8 Conclusions and display-only rendering

A member conclusion is the unchanged raw/adjusted comparison, recognized reject flag, or exact
membership form from 1.0 section 4.10. It must reach a registered `p_result_eligible` sink. Numeric p
reporting alone is not a conclusion.

The slice projection distinguishes scientific control from terminal rendering. A recognized member
decision may select display text only under either exact form:

```text
Constant[str] if DECISION else Constant[str]
```

or one X4-expanded pure output helper whose body, after a possible docstring, consists only of
`if DECISION: return Constant[str]` and a final `return Constant[str]`. Both strings are nonempty,
NUL-free, and at most 256 UTF-8 bytes. The 256-byte cap is measured from the UTF-8 encoding; the text
is never inspected, tokenized, matched, or compared for meaning. The selected string may pass
through identity assignment or the same member's reconstructable record before one or more
unconditionally executed registered sinks. Repeated unconditional reporting of the same decision is
presentation, not a second emission branch.

Terminal rendering requires total forward accounting of every consumer of the selected string and
of every Name bound to it, transitively. The only admitted transports are exact identity assignment,
the same member's reconstructable record field, literal format/f-string payload transport that does
not alter control, and the payload position of an unconditionally executed registered sink. Any
other call, comparison, operation, container use, store, return, control, or unresolved consumer
removes the node from the rendering exclusion and returns it to the whole-module hierarchy registry;
tracked provenance then abstains `hierarchical-gatekeeping-present`, and unresolved prevention
abstains `pvalue-control-dependence-unresolved`. One admitted sink does not excuse another consumer.

Everything adjacent remains hierarchical: either arm containing a call/tracked value; non-string
arms; nested/compound control; deciding whether a sink executes; choosing between sink calls;
selecting a family member/container; gating a test/correction; controlling iteration; or unresolved
parent/dominance edges. This is the only display rescope.

The 1.1 `_hierarchy_guard` cannot remain byte-identical because it classifies every `If`/`IfExp`
before roles exist and does not perform section 3.7's whole-module prevention proof. The 2.0 module
therefore has a versioned copy with the same tracked-value meanings, the now-explicit 1.0 node set,
and the execution-prevention residual; it adds early exits, whole-module provenance, and one leading
classification excluding only exact terminal-rendering nodes. Every other branch and reason is
copied by value. The change is forced by slice rescoping and the correct early-return corpus cases;
it is not a general verdict-text exemption.

## 5. Guard ownership and ordered predicate

### 5.1 Guard ownership

| Guard | 2.0 scope | Surviving behavior |
|---|---|---|
| Test/sensitivity/dead branch | global census + outcome-sequence normalizer | Exact `N`; extra, conditional, uncalled-helper, unresolved multiplicity retain reasons. |
| Correction terminal | global census + forward discharge | Every terminal seen; only exact recognized call discharged. |
| Statistics prefix | global census | Every matching call seen; only exact exemption discharged. |
| Dynamic execution | global integrity census | Any exact 3.5 shape stops `api-resolution-ambiguous`; dynamically hidden APIs are never assumed absent. |
| API rebinding | global integrity census | Any exact 3.6 rebind stops `api-resolution-ambiguous`; shadowed registered calls are never counted as resolved. |
| Outcome mutation | backward family slice + syntax-wide alias/use closure | Mutation, rebinding, delete, store, escape retain `analysis-scope-structure-unsupported`. |
| Discovery/validation | backward operands | Every row set equals complete group rows. |
| Upstream adjusted | forward lineage + reader roots | File/import/unresolved roots never become local p. |
| Family collection | forward slice | Every member position reconstructs; no dynamic escape dropped. |
| Extremum | forward slice | Closed min/max/nan/sorted forms retain extremum reason; others retain manual/unresolved reasons. |
| Export | forward slice | `.to_csv`, `numpy.savetxt`, `json.dump` carrying family p retain `unresolved-pvalue-consumer`. |
| Threshold/manual | forward + syntax-wide A5 | Source Decimal, product rule, and off-grammar abstentions unchanged. |
| Hierarchy/control | whole-module 3.7 registry + backward provenance + value slices + AST dominance | Assert, match, BoolOp, early exits, scientific/sink control, and execution residual survive; only 4.8 rendering excluded. |
| Partition | correction/conclusion forward slice | Disjoint corrections/conclusion partitions retain `multiple-family-partition-present`. |
| Resampling/maxT | fourth global repeated-construct census + backward data provenance + forward control | Unresolved cardinality and resolved joint control retain distinct reasons. |

Resampling condition-2 breadth is copied verbatim from pseudoreplication 3.0 as restated in the 1.0
design: provenance follows member edges, helper returns, destructuring, actual/formal bindings, and
subscript stores without requiring a tracked-name label. Cardinality forms, draw identities,
reducers, ratios, sorted indices, and minimum 10 remain unchanged.

### 5.2 Ordered predicate

All guards are computed over declared scopes; outward first reason is selected only here:

| Order | Required proof | First reason(s) |
|---:|---|---|
| 1 | Resolve one installed `1.2.0` authority/snapshot. | `verified-contract-authority-unavailable`; `authorized-test-family-shape-unsupported` |
| 2 | Unique ordered family, `N >= 3`. | `authorized-family-cardinality-below-three` |
| 3 | Digest-equal authorized CSV. | `frozen-authority-material-mismatch` |
| 4 | CSV finite family domain, exact two groups, >=2 rows/group/outcome. | `authorized-family-csv-domain-unavailable`; `authorized-group-domain-not-exactly-two` |
| 5 | One `analysis.py`; alternate-source and other-file statistics scan. | `analysis-source-envelope-unavailable`; `alternate-analysis-file-present`; `statistics-api-imported-outside-analysis-py` |
| 6 | Bounded parse, API resolver, global callee indexes, dynamic-execution census, and API-rebinding census; no chosen setup scope. | `api-resolution-ambiguous`; `dataflow-definition-ceiling-exceeded` |
| 7 | Global registered-call census and exact `N` multiplicity. | `test-battery-cardinality-unresolved`; `authorized-family-test-census-incomplete`; `extra-registered-test-outside-authorized-family`; X4 reasons |
| 8 | Uniform API and order-equal family mapping. | `mixed-test-api-family`; `test-operand-lineage-unresolved` |
| 9 | Complete backward reader/operand slices and group-row equality. | `additional-accepted-reader-present`; `authorized-reader-lineage-unavailable`; `test-operand-lineage-unresolved`; `selected-group-row-completeness-unproven`; X4 reasons |
| 10 | Bind every local p root; account for every forward consumer/container; upstream/export/collection guards. | `upstream-correction-lineage-unresolved`; `pvalue-family-collection-unresolved`; `unresolved-pvalue-consumer`; X4 reasons |
| 11 | Family extremum guard. | `family-pvalue-extremum-reduction-present` |
| 12 | Corrections/manual values; global terminal discharge; noncomparison off-grammar transforms. | `correction-family-lineage-unresolved`; `unresolved-manual-correction-present`; `pvalue-scalar-cast-or-rounding-unsupported` |
| 13 | Every direct-p threshold under comparison/A5/product grammar. | `unresolved-decision-threshold` |
| 14 | Whole-module hierarchy/prevention registry, partition, fourth global resampling census, and global statistics prefix. | `hierarchical-gatekeeping-present`; `pvalue-control-dependence-unresolved`; `multiple-family-partition-present`; `resampling-cardinality-unresolved`; `permutation-family-control-present`; `unresolved-inference-sibling-present` |
| 15 | One recognized conclusion and sink for every member. | `pderived-conclusion-family-incomplete`; `conclusion-output-sink-unavailable` |
| 16 | Classify `complete`, `strict_subset`, or `none`. | no new reason |
| 17 | Covered negative for complete; one dev candidate for subset/none; no Findings. | `multiple-testing-code-inspection-exception` on localized failure |

No source-order tie-breaking changes precedence.

## 6. Closed reasons and retired module grammar

The 2.0 closed reason set is exactly:

```text
verified-contract-authority-unavailable
authorized-test-family-shape-unsupported
authorized-family-cardinality-below-three
frozen-authority-material-mismatch
authorized-family-csv-domain-unavailable
authorized-group-domain-not-exactly-two
analysis-source-envelope-unavailable
alternate-analysis-file-present
statistics-api-imported-outside-analysis-py
api-resolution-ambiguous
analysis-scope-structure-unsupported
dataflow-definition-ceiling-exceeded
helper-callee-not-simple-name
helper-definition-unavailable-or-nonunique
helper-parameter-shape-unsupported
helper-parameter-default-unsupported
helper-variadic-parameter-unsupported
helper-argument-binding-unsupported
helper-recursion-unsupported
helper-return-count-unsupported
helper-return-position-unsupported
helper-return-expression-unsupported
helper-global-nonlocal-unsupported
helper-closure-or-nested-definition-unsupported
helper-async-decorator-or-yield-unsupported
helper-body-statement-unsupported
helper-free-name-unbound
helper-inlining-depth-exceeded
helper-call-site-reentry-unsupported
additional-accepted-reader-present
authorized-reader-lineage-unavailable
test-battery-cardinality-unresolved
authorized-family-test-census-incomplete
extra-registered-test-outside-authorized-family
mixed-test-api-family
test-operand-lineage-unresolved
selected-group-row-completeness-unproven
upstream-correction-lineage-unresolved
pvalue-family-collection-unresolved
unresolved-pvalue-consumer
family-pvalue-extremum-reduction-present
correction-family-lineage-unresolved
unresolved-manual-correction-present
pvalue-scalar-cast-or-rounding-unsupported
unresolved-decision-threshold
hierarchical-gatekeeping-present
pvalue-control-dependence-unresolved
multiple-family-partition-present
resampling-cardinality-unresolved
permutation-family-control-present
unresolved-inference-sibling-present
pderived-conclusion-family-incomplete
conclusion-output-sink-unavailable
multiple-testing-code-inspection-exception
```

No surviving reason string is renamed, and surviving reasons other than the following keep their
predicate meanings. `analysis-scope-structure-unsupported` deliberately changes meaning: in 2.0 it
means only on-slice outcome-sequence mutation/rebinding/delete/store/escape and no longer means an
unrelated module/setup statement. As required by 2.5, its 1.1 and 2.0 occurrences are
version-incomparable. `pvalue-scalar-cast-or-rounding-unsupported` survives for round and adjacent
scalar shapes; direct `float(P)` is the closed identity in 4.6.

Retired predicates with no 2.0 emitter are `_chosen_scope` as an MT prerequisite, module/main/setup
statement enumeration, the whole-module setup value gate, the general read-only consumer allowlist,
and the broad raw-scope relabel. No string is deleted because the shared scope code has the
surviving mutation meaning. Emitter fixtures, not a synthetic retired-reason annex, must cover it.

`conclusion-output-sink-unavailable` retains the documented-unreachable argument: conclusion
positions arise only from eligible sinks, so complete positions with no sink kind cannot arise.
It remains in replay vocabulary; tests must not monkeypatch reachability.

## 7. False-accusation invariant and proof obligations

### 7.1 Load-bearing invariant

A candidate asserts no recognized correction and raw conclusions only after:

1. the global correction-terminal census sees every reserved correction name, even off-slice;
2. every family p forward slice accounts for every consumer, so an unrecognized correction cannot
   be crossed through an unknown helper/library, arithmetic, store, container, or export; and
3. finite correction/manual grammars plus the order-12/13 partition and Decimal product rule block
   all unrecognized p/threshold arithmetic; and
4. dynamic execution, API rebinding, and every control edge capable of preventing a family slice
   are either proved harmless under their closed registries or abstain.

Machine-checkable receipts include global call positions/identities, every p root, every classified
consumer edge, correction input members, conclusion members, and set equality of discovered versus
accounted p-consumer edges. Missing receipt means abstention.

### 7.2 Admission adversaries

| Admission | Strongest correct-analysis fixture | Required block/no-candidate argument |
|---|---|---|
| Off-slice statement | `correct-offslice-hand-holm-definition` | Family p passed to arbitrary `hand_holm` is on forward slice: `unresolved-pvalue-consumer`. |
| Unrecognized module shape | `correct-offslice-try-with-finally-correction` | Global correction terminal sees correction; forward consumer also cannot cross it. |
| Non-statistics import | `correct-offslice-custom-adjuster-import` | Import allowed, p-bearing `westfall_adjust` call unresolved: `unresolved-pvalue-consumer`. |
| Arbitrary helper body off-slice | `correct-offslice-helper-plus-complete-correction` | Helper ignored; exact complete `multipletests` yields covered negative. |
| Off-slice registered test | `correct-unused-sensitivity-helper` | Global test census adds conservative instance: `extra-registered-test-outside-authorized-family`. |
| Off-slice correction name | `correct-unused-holm-call` | Global terminal census: `unresolved-manual-correction-present`. |
| Off-slice statistics call | `correct-unused-shapiro-helper` | Global prefix census: `unresolved-inference-sibling-present`. |
| Off-slice dynamic execution | `correct-eval-based-correction-helper` | Global dynamic-execution census: `api-resolution-ambiguous`, whether or not the helper is called. |
| Off-slice API rebinding | `correct-monkeypatched-statistics-correction` | Global API-rebinding census: `api-resolution-ambiguous`; the patched call is never treated as the registered identity. |
| Nonalias API-terminal spelling | `correct-nonalias-terminal-name-with-complete-correction` | Calls use live module aliases, while unrelated Stores named `ttest_ind` and `benjamini_hochberg` shadow no live alias; 3.6 does not fire and the exact complete correction yields a covered negative. |
| Off-slice extra reader | `correct-unused-secondary-reader` | Unused reader admitted; paired mixed-reader operand enters backward slice and stops `additional-accepted-reader-present`. |
| Slice setup only | `correct-outcome-alias-pop-in-unused-helper` | Stability closure brings mutation on-slice: `analysis-scope-structure-unsupported`. |
| Helper slicing | `correct-helper-row-filter` | QC filter is on operand slice: `selected-group-row-completeness-unproven`. |
| Position-1 p | `correct-position-one-then-holm` | Projection tied to registered return; complete correction yields covered negative. Generic tuple unresolved. |
| Direct float identity | `correct-float-p-hand-bonferroni` | Multiplication remains p-derived and is recognized manual or abstains manual reason. |
| Display rendering | `correct-display-decision-gates-correction` | Controls correction, so outside 4.8: `hierarchical-gatekeeping-present`. |
| Off-slice early exit | `correct-early-return-panel-gate` | Synthetic isolated fixture: the panel scalar uses only pure `FRAME[OUTCOMES]` projections, the early `return` precedes the family calls, and every family operand uses admitted `.loc[FRAME[GROUP] == VALUE, OUTCOME]`; order 9 passes and whole-module 3.7 is the first reason, `hierarchical-gatekeeping-present`. |
| Subset metadata | `correct-two-prespecified-families` | Disjoint corrections stop `multiple-family-partition-present`; subsets never merge. |

### 7.3 Surviving guard adversaries

| Guard | Named fixture | Required first outcome |
|---|---|---|
| Hand Sidak | `correct-hand-sidak-threshold` | `unresolved-decision-threshold` |
| Off-registry correction | `correct-off-registry-pingouin-multicomp` | `unresolved-manual-correction-present` |
| Default method | `correct-default-method-multipletests` | covered negative, `hs` |
| Sensitivity | `correct-sensitivity-duplicate` | `extra-registered-test-outside-authorized-family` |
| Discovery/validation | `correct-discovery-validation-split` | census reason; isolated fixed-count form reaches `selected-group-row-completeness-unproven` |
| NumPy gate | `correct-numpy-omnibus-assert-gate` | `hierarchical-gatekeeping-present` |
| Match/short circuit | `correct-match-guard-and-boolop-gate` | `hierarchical-gatekeeping-present` |
| Execution residual | `correct-try-gate-residual` | `pvalue-control-dependence-unresolved` |
| Early-return panel gate | `correct-early-return-panel-gate` | Synthetic isolated fixture with pure-outcome panel provenance and admitted `.loc` family operands: exact first reason `hierarchical-gatekeeping-present`. It is not sourced from `spec-14` or `spec-36`. |
| Dynamic resampling | `correct-dynamic-label-permutation` | `resampling-cardinality-unresolved` |
| Resolved maxT | `correct-label-permutation-maxT` | `permutation-family-control-present` in isolated reachable fixture |
| Extremum | `correct-min-p-reported` | `family-pvalue-extremum-reduction-present` |
| Export | `correct-raw-flags-plus-p-export` | `unresolved-pvalue-consumer` |
| Upstream values | `correct-loaded-adjusted-p` | upstream reason or earlier exact zero-test census in full fixture |
| Family collection | `correct-dynamic-p-dict` | `pvalue-family-collection-unresolved` |
| Partition | `correct-disjoint-prespecified-families` | `multiple-family-partition-present` |
| Product rule | `correct-off-AST-bonferroni-001-N5` | `unresolved-decision-threshold` |
| Pre-registered bare level | `correct-preregistered-threshold-001-N4` | Four raw `p < 0.01` decisions and no recognized correction: `unresolved-decision-threshold`. Protocol prose is not detector evidence. |
| Statistics sibling | `correct-assumption-check` | `unresolved-inference-sibling-present` |

No fixture accepts alternative reasons. Combined opened cases may stop earlier than isolated guards;
both exact expectations are pinned.

## 8. Evidence, replay, and reuse

Candidate evidence includes reader, each member's two operands, procedure, p root, decision/
correction, and output sink. Global census receipts are coverage records, not prose evidence.
`PERFORMED_COUNT = N` comes from exact instance census.

| Surface | 2.0 decision |
|---|---|
| MT 1.1 dataflow/adapter/detector/integration | Copy to new 2.0 modules; never edit 1.0/1.1. |
| Dependence v3.1 | Copy graph/worklist, p-depth, return-position, X4, row, sink, guard patterns by value; no edit/private import. |
| Inherited MT registries | Copy registered-test, correction, statistics-prefix, and resampling constants byte-for-byte from 1.1/pinned v3.1 and assert equality. |
| 2.0 integrity registries | New exact dynamic-execution, API-rebinding, and whole-module control/early-exit tuples; abstention-only and version-pinned. |
| Hierarchy implementation | Versioned copy required by 3.7/4.8; no edit or private import of 1.1/dependence code. |
| Contract 1.2.0 | Reuse without edit. |
| MT wording v1 | Reuse exact object/digest. |
| Qualified lanes/pins | Byte-untouched and absent from development binding. |

Frozen MT 1.1 dataflow source is pinned at
`sha256:d4a58899d6f7a9597f311641646bc1a8b47d2e392c011aceb51dd536cc9c85c1`.
Historical 1.0/1.1 E10/E11 replay tests import frozen components explicitly, never the active
development binding.

## 9. Executable validation plan

### 9.1 Slice engine gates

1. **Global/slice differential.** Insert each registered test, correction terminal, statistics call,
   repeated construct, dynamic-execution shape, API rebind, and 3.7 control/early-exit node into
   every off-slice AST body kind; its exact global census or integrity outcome changes. Insert
   unrelated nonregistered statements/calls/imports in the same places; facts/reasons do not change.
   A Store to an actually imported live API/module alias must abstain `api-resolution-ambiguous`;
   the identical Store spelling in a module without that live import must not enter 3.6. Execute
   `correct-nonalias-terminal-name-with-complete-correction` as the covered-negative control.
2. **Backward totality.** For every admitted operand edge, mutate one predecessor to a dynamic call,
   second binding, row mask, wrong group/outcome, or alternate reader. Require the exact reason.
3. **Forward totality.** Independently enumerate every consumer parent of every p root. Analyzer
   accounted-edge receipts are set-equal. Insert unresolved call, transform, container, store,
   attribute store, helper escape, export, or return on any branch and require the exact guard.
4. **Family cardinality.** Cross explicit calls, direct loops, enumerate, zip, comprehensions,
   helpers, uncalled helpers, literal-false/live bodies, duplicates, reorder/set equality, and
   dynamic subsets. Pin counts and reasons.
5. **Return/scalar normalization.** Cross `.pvalue`, `[1]`, two-target destructuring, generic tuple,
   wrapper, exact/nested float, round, presentation, and arithmetic. Only closed registered
   projections/presentation cross.
6. **Display rendering.** Cross direct/assigned/helper/record constant-string rendering and repeated
   unconditional sinks. Calls, nonstrings, conditional sink execution, alternate sink branches,
   test/correction/container gates, BoolOps, assert, match, and unresolved parents retain guards.
   Add a second consumer to the selected string and to each identity-bound alias; every unaccounted
   consumer returns the node to hierarchy.
7. **P-container grammar.** Cross every 4.6 production and one-edge near miss. Pin `pvals[:3]` as
   exact subset coverage, same-kind unique `pvals + extra` as exact union coverage, direct
   `zip(OUTCOMES, pvals)` as `correction-family-lineage-unresolved`, and its exact p-field
   comprehension as reconstructed coverage.
8. **Control prevention.** Execute fixtures for every 3.7 node, including early `return`, `break`,
   `continue`, `raise`, and `sys.exit`, both tracked and untracked. Pin tracked/joint provenance to
   `hierarchical-gatekeeping-present`, unresolved dominance to
   `pvalue-control-dependence-unresolved`, and untracked resolved controls to no guard. Cross the
   identical early-raise validation with pure `FRAME[OUTCOMES]` and mixed
   `FRAME[[IDENTIFIER, GROUP, *OUTCOMES]]` projections: only the pure projection contributes to joint
   derivation. The synthetic `correct-early-return-panel-gate` must pass order 9 and stop first at
   hierarchy.
9. **Threshold narrowing.** With `N = 4` and no recognized correction, cross bare `0.01`, `0.05`,
   and `0.1`: only `0.05` is admitted and the other two require
   `unresolved-decision-threshold`. Repeat with a recognized correction to pin the retained set, and
   independently exercise every source-text Decimal product-rule value.

### 9.2 Registry, reasons, guards, and isolation

- Byte-equality pins every inherited section-3 registry, `_QUERY`, correction methods/defaults,
  axis forms, SciPy `1.17.1`/`1.18.0` position-1 contracts, thresholds/operators, extremum,
  resampling, and sink registry. Exact tuple/set equality pins the new dynamic-execution,
  API-rebinding, and control-node registries.
- Every closed reason except documented-unreachable sink has one real public-analyzer fixture; 17
  X4 reasons may share a parametrized module. Emitters plus unreachable annex equal the closed set.
- Every section-7 fixture executes the public analyzer; private-helper or AST-shape assertions do
  not satisfy a gate.
- Two-registry differential proves byte equality/non-derivation for qualified GrantPins, grants,
  qualifications, metrics, threshold references, and Finding objects.
- Candidate fixtures emit exactly one development candidate and zero Findings; complete correction
  emits covered negative and zero candidates.

### 9.3 Prose tripwire

The tripwire covers global/slice membership, family normalization, reaching definitions, stability
closure, X4 pruning, position-1 p projection, float identity, consumer classification, subset
metadata, display rendering, and every rescoped guard.

For every positive/adversarial fixture independently mutate comments, docstrings, Markdown,
reports, task text, unrelated strings, output labels, format text, annotations, and non-callee
identifiers. Add/remove report and Markdown files. Rename non-callee identifiers to `bonferroni`,
`holm`, `sidak`, and `benjamini_hochberg`. Facts, first reasons, and classification remain equal.
Those rename mutations remain outside 3.6 unless the exact spelling is already an actually live
import alias in that module; the tripwire fixtures intentionally have no such alias.

Paired structural controls move correction spelling into a callee terminal; add off-slice
registered/statistics/repeated/dynamic-execution call; rebind a registered API; pass p to unresolved
helper; replace registered position `1`; wrap `float(P)` in multiplication; replace display Constant
with a call; add a second selected-string consumer; conditionally execute a sink; add an early
tracked return; add a row mask; mutate tracked outcomes through alias. Each changes only its named
predicate. Deleting one load-bearing structural literal in a positive control must change the
result.

### 9.4 Historical and opened-corpus gates

- Explicitly import frozen MT 1.0/1.1 adapters over all opened cases and compare canonical bytes to
  immutable E10/E11 records.
- Execute 2.0 adapter over all 30 opened cases and require section 10 twice byte-identically.
- Rerun deterministic 98-file analysis census and exact API compositions.
- Rerun all pseudoreplication/dependence/complete-domain regressions and qualified envelopes without
  rewriting locks.
- Execute every PROBE, NEGSIM, ladder, and retained 1.1 fixture under section 11.
- Through the same open-corpus adapter harness, execute and freeze an adapter-level 1.1 baseline.
  Keep the committed analyzer-only `baseline_1_1.json` as a diagnostic; do not overwrite it.

### 9.5 Open development corpus gate

`evaluation/development/multitest-open-corpus-v1/` is the answer-visible corpus committed at
`d7cc94f22dcd99f642b356b47f6ee5d6d62acf26` (`d7cc94f`). It contains exactly 50 cases: 25
`correct` and 25 `misstep`. The authoritative labels are
`evaluation/development/multitest-open-corpus-v1/specs/labels.json`, raw-file
`sha256:f9d2d33ba3b8247b0d0d65e5f72f765af02bfca6dc932f895010d79129f36f80`.

The frozen analysis-source-set digest is
`sha256:7888b72a6ac1ec70830d4041517a977b8ea8ff6c4294a7d13a734ab9af377a2e`.
It is computed as SHA-256 of UTF-8 canonical JSON plus one LF, where the JSON is a sorted,
compact-separator mapping from each relative `cases/spec-XX/analysis.py` path to the SHA-256 of that
file's raw bytes. The map has exactly 50 entries. Any count, label, source, or digest change is a
hard fixture failure. Because the corpus is open, it is regression evidence, not qualification
evidence.

The public 2.0 adapter executes every case. Hard gate: zero candidates on every labeled-correct
script. Any candidate is a stop-and-report design regression, not relabeled or excluded. Recall on
labeled-misstep scripts is reported with case IDs/exact first reasons but has no threshold. Source
and label digests, label counts, candidates, histogram, and repeat canonical-byte equality are
checked in. The build also re-records the 1.1 baseline at adapter level through this identical case
harness. The existing `baseline_1_1.json`,
`sha256:b2ab49cd1bea5fe27a9a738d380432fe8164facaa73096020f3c1a7f08165cf6`,
remains explicitly labeled analyzer-level diagnostic evidence. Adapter-level 1.1 can only add an
earlier envelope abstention to an analyzer abstention and therefore cannot create a candidate; its
`0/25` correct-case result holds a fortiori and is asserted again in the new adapter record.

Two correct-case first reasons are pinned independently of the zero-candidate aggregate:

| Case | Required 2.0 outcome | Ordered reason |
|---|---|---|
| `spec-14` | abstain `test-operand-lineage-unresolved` | The family operands use `~is_low_ph`; the negated boolean mask is refused at order 9 before hierarchy. |
| `spec-36` | abstain `test-operand-lineage-unresolved` | The family operands use `~mask`; the negated boolean mask is refused at order 9 before hierarchy, although `pots[OUTCOMES]` independently satisfies the pure-outcome joint-provenance definition. |

## 10. Required 2.0 oracle for all 30 opened cases

These are adapter-level. `candidate/none` and `candidate/strict_subset` mean one development
candidate and zero Findings. `covered negative/complete` is a deterministic no-candidate state, not
an abstention.

### 10.1 Envelope 10

| Role | Case ID | Required 2.0 outcome | Proof/residual |
|---|---|---|---|
| P1 | `ebbb8a5dbc2664257144` | abstain `authorized-reader-lineage-unavailable` | `csv.DictReader`/record value model unsupported. |
| P2 | `104493a5d99796a002c0` | candidate / `none` | Enumerate, helper path, boolean split, named alpha, `.pvalue`, and display resolve; its mixed identifier/group/outcome missing-value check contributes nothing to joint provenance. |
| P3 | `3ff45fce2a45e0959fdb` | candidate / `none` | Helper/comprehension, p projection, float identity, dict records, display resolve. |
| P4 | `7296b0e2cf7faeefca64` | candidate / `none` | X4 loop, position-1 p, record appends, conclusions resolve. |
| P5 | `c51d08801b3d0ba4e532` | candidate / `strict_subset` | Seven calls; `multipletests` covers three primaries and four raw conclusions remain. Its mixed identifier/group/outcome integrity projection is not jointly derived. |
| P6 | `f4cf62caeb8ad68dc5b3` | candidate / `strict_subset` | Full battery; exact first-three subset supplies manual coverage only, two raw remain. |
| N1 | `cb2e207276a0dc3247bb` | covered negative / `complete` | Defaulted `multipletests` covers all four. |
| N2 | `9be74afbe9659bd50580` | abstain `unresolved-decision-threshold` | Computed Sidak helper result. |
| N3 | `b787314c170f8f690060` | abstain `unresolved-manual-correction-present` | Global terminal sees `multicomp`; prefix secondary. |
| N4 | `60f96fabb7129d662b23` | abstain `extra-registered-test-outside-authorized-family` | Family plus sensitivity exceeds `N`. |
| N5 | `8d83210468ecde012e4a` | abstain `test-battery-cardinality-unresolved` | Validation multiplicity depends on discovery subset. |
| N6 | `4907932548f745afe942` | abstain `authorized-family-test-census-incomplete` | Family calls under live NumPy-derived branch; hierarchy secondary. |
| N7 | `6d2fdc67ab98bc0e0e6e` | abstain `statistics-api-imported-outside-analysis-py` | Historical generator remains in project. |
| N8 | `dfc9f20a94ecefc7f7b5` | abstain `test-battery-cardinality-unresolved` | Hand NumPy maxT lacks exact registered-call family census. |
| N9 | `e1bce32a32e3b2df475e` | abstain `unresolved-decision-threshold` | Source Decimal: `0.01 * 5 == 0.05`. |

### 10.2 Envelope 11

| Role | Case ID | Required 2.0 outcome | Proof/residual |
|---|---|---|---|
| P1 | `8726b87ac4ba4c34c0a3` | candidate / `none` | Four explicit calls, `.pvalue`, pure display helper, unconditional reports resolve. |
| P2 | `6f08fe90c58e51737a4d` | candidate / `none` | Enumerated tuple family, position-1 p, display resolve. |
| P3 | `69c5d0aec76eefb67148` | candidate / `none` | Helper/dict comprehension, float identity, records, display resolve. |
| P4 | `dfd35001c5a99ab1486b` | candidate / `none` | Outcome/helper slices and exact records resolve; summaries off-slice. |
| P5 | `114782f595d9c24b923d` | abstain `unresolved-pvalue-consumer` | P records enter unsupported pandas DataFrame pipeline/dynamic stores. |
| P6 | `0249919d05de1abc25fd` | candidate / `strict_subset` | Eight calls; first-three manual coverage, five raw conclusions. |
| N1 | `d1533e4a8bbd10cb727e` | covered negative / `complete` | Defaulted `multipletests` covers all five. |
| N2 | `d11a7136d1e91ed8e26f` | abstain `unresolved-decision-threshold` | Computed Sidak threshold. |
| N3 | `479317f1706d4fb929e5` | abstain `unresolved-manual-correction-present` | Global terminal sees `multicomp`. |
| N4 | `10e0cfb0c7ba8d03ec52` | abstain `extra-registered-test-outside-authorized-family` | Sensitivity rerun extra. |
| N5 | `2a712805024597719d32` | abstain `test-battery-cardinality-unresolved` | Data-dependent validation subset. |
| N6 | `1cce7d6b580caa25f597` | abstain `authorized-family-test-census-incomplete` | Family tests under live jointly-derived gate; hierarchy secondary. |
| N7 | `9bccc428f23dde0d43f0` | abstain `authorized-family-test-census-incomplete` | Loaded upstream adjusted values and zero local registered calls. |
| N8 | `53c4753f38f9e253d541` | abstain `test-battery-cardinality-unresolved` | Hand NumPy maxT lacks exactly `N` registered instances. |
| N9 | `08565c720304eb6fd9d3` | abstain `unresolved-decision-threshold` | `0.01 * 5` product rule. |

Opened-positive forecast is **10/12 candidates**. E10 P1 remains behind `DictReader`; E11 P5 remains
behind an unresolved pandas p consumer. Revision 2 re-verified all 30 section-10 rows against the
pure-outcome-subset definition in 3.7; P2 and P5 above are the only Revision-1 outcomes restored,
and every Envelope-11 row remains unchanged. This answer-visible forecast is not Envelope-12
credit.

## 11. Recon, ladders, and 1.1-gate delta oracle

### 11.1 PROBE and NEGSIM

Every source executes through the public analyzer:

| Fixture(s) | Provenance | Required 2.0 outcome |
|---|---|---|
| `PROBE_annassign.py`, `PROBE_astype.py`, `PROBE_boolmask.py`, `PROBE_dicttable.py`, `PROBE_enumerate.py`, `PROBE_helpertest.py`, `PROBE_namedalpha.py`, `PROBE_nestedtable.py`, `PROBE_pathparam.py`, `PROBE_query.py`, `PROBE_floatp.py` | One-construct mutations of opened uncorrected misstep baselines. | candidate / `none` |
| `PROBE_ternary.py` | Misstep-baseline mutation: one terminal-rendering ternary replaces the baseline's direct display form. It is not an independently authored positive. | candidate / `none` |
| `PROBE_roundp.py` | One-construct mutation of an uncorrected misstep baseline. | `pvalue-scalar-cast-or-rounding-unsupported` |
| `NEGSIM_A.py` | Correct-analysis near-simulation. | `correction-family-lineage-unresolved` |
| `NEGSIM_B.py` | Correct-analysis near-simulation. | `unresolved-manual-correction-present` |
| `NEGSIM_C.py` | Misstep-baseline mutation: exact direct `float(P)` replaces the baseline p scalar. It is not an independently authored positive. | candidate / `none` |

Enumerate/helper change because proof is slice-scoped; float fixtures change because direct float is
a registered-p identity; ternary changes under terminal rendering. These are known uncorrected
misstep baselines. No labeled-correct FA fixture loses abstention.

### 11.2 Mutation ladders

```text
P2 original, P2_m1, P2_m2, P2_m3, P2_m4, P2_m5, P2_m6, P2_m7, P2_m8:
    candidate / none

P3 original, P3_s1, P3_s2, P3_s3, P3_s4, P3_s5, P3_s6:
    candidate / none
P3_s7:
    extra-registered-test-outside-authorized-family
P3_s8:
    candidate / none
```

P3_s7 retains an uncalled helper conservative instance plus direct family calls, so remains safety
abstention. Other changed rungs are known-positive recall gains from removing unrelated walls.

### 11.3 1.1 fixture families

| 1.1 gate family | 2.0 expectation |
|---|---|
| Contract/CSV/domain, detector ValueErrors, identity, no-Finding, registry/isolation | Byte/semantic unchanged except versions. |
| Correction API/default/method/axis/return/manual/product/terminal | Exact outcomes unchanged except the threshold-only narrowing in the next row. |
| Bare raw threshold, no recognized correction | `0.05` fixtures retain their outcome; `0.01` and `0.1` now require exact `unresolved-decision-threshold`. Computed/product fixtures retain their exact reasons. |
| Row completeness, upstream, export, extremum, partition, statistics, resampling, sensitivity, dead/live conditional | Exact outcomes unchanged. |
| Assert/match/BoolOp/execution residual | Exact outcomes unchanged. |
| Display-only known-positive `If`/`IfExp` | Candidate only under 4.8; adjacent hierarchy negatives unchanged. |
| Whole-module control/early exit | Every 3.7 node executes. Synthetic `correct-early-return-panel-gate` requires `hierarchical-gatekeeping-present`; mixed-column integrity raises do not become jointly derived; open-corpus `spec-14`/`spec-36` stop earlier at `test-operand-lineage-unresolved`. |
| Unsupported module setup wholly off-slice | No abstention; complete uncorrected baseline becomes candidate. |
| Outcome mutation/alias/rebind/store/delete/escape | Remain `analysis-scope-structure-unsupported`, but 1.1/2.0 reason statistics are not compared because section 6 changes the predicate meaning. |
| Read-only allowlist/over-admission | Allowlist retired; required uses need 4.2, p/operand escapes abstain, off-slice invariant. |
| Direct float known positives | Candidate; round and hand arithmetic retain reasons. |
| Closed-set fixtures | Rebuilt against section 6; old test files not retargeted. |

Historical 1.0/1.1 tests keep frozen imports. New `_v2` tests are copies plus 2.0 oracles; old test
string literals cannot satisfy 2.0 closed-set coverage.

## 12. Envelope 12 protocol

Envelope 12 is class-pure with six fresh blind positives and nine fresh blind negatives. It inherits
P1-P6/N1-N9 semantic roles, data-author custody, isolated authors/custodian, pre-contact freezes,
and digest chronology from Envelope 11. Generator/data-author artifacts remain outside audited
`project/`.

Hard stops:

- zero negative candidates (`0/9`);
- zero Findings anywhere;
- byte-identical replay for all 15;
- zero false accusations in latest 36 class-specific blind cases.

Envelope-12 first-contact recall is independently reported as candidates/six with every miss and
first reason; there is no new per-envelope gate. E10+E11+E12 do make 18 blind MT positives, so the
standing trailing-18 recall statistic is computed for the first time. The first-contact history is
not rescored with 2.0: E10 and E11 remain `0/6` each, so even an E12 `6/6` yields only `6/18` and
cannot meet the 50% promotion criterion. That is reported honestly and means promotion cannot occur
until later fresh positives replace enough of the zero-recall history; it is not converted into an
E12 hard stop or used to alter cases.

Every negative records realized roles, designed/actual first guards, secondary guards, and family-C
shapes. Briefing must not hint at syntax, assumption checks, readers, helpers, containers,
constants, tuple returns, DataFrames, verdicts, or off-slice placement. Passing installs no
grant/pin/qualification.

## 13. File-by-file build list

| File/surface | Planned change |
|---|---|
| New `ADR-0079-MULTIPLE-TESTING-CODE-SLICE-2.0-INVERSION.md` | Authorize identities, split, whole-module integrity/control censuses, scalar/return/display edges, threshold narrowing, version-incomparable reason meaning, open corpus, E12, isolation. |
| New `code_csv_multiple_testing_dataflow_v2.py` | Versioned copy implementing sections 3-7; no private dependence import. |
| New `code_csv_multiple_testing_adapter_v2.py` | Version 2.0, exact reasons, unchanged facts/projection. |
| New `bounded_code_csv_multiple_testing_conflict_v2.py` | Versioned wrapper and unchanged operand guards. |
| New `integration_multiple_testing_v2.py` | Development-only integration. |
| `scientific_checks/profiles.py` | Retain 1.0/1.1 files; point active development binding to 2.0. |
| `method_conflict_registry.py` | Register 2.0 beside historical versions. |
| `method_conflict_finding.py` | Permit exact 2.0 dev binding to reuse unchanged wording v1. |
| Development controller | Dispatch 2.0 only under development registry. |
| Manifests/registry resources | Add 2.0 identities/files; retain historical versions. |
| New `tests/test_code_csv_multiple_testing_dataflow_v2.py` | Slices, p-container grammar, totality, global integrity/control censuses, guards, FA, PROBE/NEGSIM/ladders, prose. |
| New adapter/detector/integration tests | Identities, set, schemas, ValueErrors, projections, zero Findings. |
| New `test_multiple_testing_e10_e11_replay_v2.py` | Execute section-10 oracle twice. |
| Historical replay anchors | Frozen explicit 1.0/1.1 imports/bytes. |
| `multitest-open-corpus-v1/` | Verify frozen commit/counts/label/source digests; add adapter-level 1.1/2.0 replay records without replacing the analyzer diagnostic; hard zero-correct-candidate gate. |
| New `multitest-code-slice-v2/` | Answer-visible guard/adversarial fixtures and ledger. |
| Future blind Envelope 12 | Execute section 12 after answer-visible gates. |
| Ledger, source manifests, `MANIFEST.sha256` | Regenerate after final implementation/test change. |

The 1.0/1.1 MT modules/designs, ADR-0077/0078, E10/E11 artifacts, qualified modules, and dependence
dataflow files are not edited.

## 14. Build acceptance and stop conditions

Build acceptance requires:

1. all global registries byte-equal pinned sources and every dynamic-execution/API-rebinding/control
   integrity fixture exact;
2. discovered/accounted forward consumer edges set-equal for every candidate;
3. complete `2N` operand and `N` p/conclusion proofs;
4. section-7 adversaries exact;
5. 30-case replay exact and deterministic;
6. PROBE/NEGSIM/ladders and retained 1.1 gates exact;
7. exact 50-case/25+25 open-corpus custody digests, adapter-level 1.1 replay, and zero candidates on
   labeled-correct 2.0 projects;
8. prose invariance plus effective structural controls;
9. qualified byte equality/non-derivation;
10. unchanged contract goldens and historical replays; and
11. after manifests regenerate following the final change, fresh `ruff check .`,
    `ruff format --check .`, `mypy src`, full `pytest`, and
    `python scripts/validate_starter.py` all pass.

Implementation stops and reports design regression rather than adapting the design if any
load-bearing gate, section-10 oracle, zero-correct-candidate gate, or qualified differential cannot
pass. No reason string or section-6 predicate meaning is changed and no guard is weakened at build
time to make an oracle pass.

## 15. Revision 1 changelog

Revision 1 is relative to the reviewed document at
`sha256:09deb93bfea99ff023455686ac8253df5e6af4b2a572fb7ea45a360a0797ec72`. Every change below is an
abstention-only narrowing, an exact closure of an already intended trigger, or an honest
versioned-meaning/custody clarification. No Revision-1 change enlarges candidate or Finding
eligibility.

| Review item | Sections changed | Revision-1 disposition |
|---|---|---|
| BL-1 | 1; 2.5; 3.7; 4.3; 4.8; 5.1-5.2; 7.1-7.3; 9.1-9.3; 10.1; 11.3; 13-14 | Defined the whole-module 1.0 control registry plus early `return`/`break`/`continue`/`raise`/`sys.exit`, excluded it from off-slice admission, required backward provenance and the execution-prevention residual, and added `correct-early-return-panel-gate` with `spec-14`/`spec-36`. Re-evaluation narrowed E10 P2/P5 and the opened forecast from 10/12 to 8/12. |
| MJ-1 | 1; 2.5; 3.5; 5.1-5.2; 7.1-7.2; 9.1-9.3; 13-14 | Added the closed whole-module dynamic-execution census. Every listed shape abstains `api-resolution-ambiguous`. |
| MJ-2 | 1; 2.5; 3.6; 5.1-5.2; 7.1-7.2; 9.1-9.3; 13-14 | Added the closed whole-module API-rebinding census, including registered module attributes, API terminal bindings, and live import aliases. |
| MJ-3 | 4.2; 4.6; 9.1-9.2 | Made 4.2 outcome-sequence-only and specified a separate complete p-container grammar. Pinned `pvals[:3]`, `pvals + extra`, direct `zip(OUTCOMES, pvals)`, and exact p-field projection classifications. |
| MJ-4 | 3.7; 4.8; 5.1; 7.2; 9.1; 9.3 | Required total forward accounting of the selected display string and every bound alias. Any nontransport consumer returns the node to hierarchy. |
| MJ-5 | 9.4-9.5; 13-14 | Pinned commit `d7cc94f`, exact 50/25+25 counts, authoritative labels path, label/source-set digests, and adapter-level execution. Required a same-harness adapter-level 1.1 record while retaining the pinned analyzer baseline as diagnostic evidence. |
| MJ-6 | 2.5; 4.7; 7.3; 9.1; 11.3; 13-14 | Narrowed uncorrected `N >= 3` bare thresholds to `{0.05}`; `0.01`/`0.1` now abstain. Retained the product rule, added the N=4 pre-registered-0.01 fixture, and recorded the deliberate recall cost and ADR obligation. |
| MJ-7 | 2.5; 6; 11.3; 13 | Kept the reason string but recorded that `analysis-scope-structure-unsupported` has different 1.1 and 2.0 predicates and must never be compared across versions. |
| Minor 1 | 4.5; 9.2 | Pinned position-1 registered-result projection to lockfile SciPy `1.17.1` and `1.18.0`. |
| Minor 2 | 4.5 | Stated that sibling registered-result members, including statistic/df/position 0, are off the p-value slice. |
| Minor 3 | 1; 3.4; 5.1-5.2; 9.1-9.2 | Named and byte-restated the repeated-construct census as the fourth global census. |
| Minor 4 | 2.5; 3.1; 5.1; 11.3 | Recorded the live-conditional abstention as a traceable narrowing that does not reinstate the candidate-producing traversal withdrawn by 1.0 Revision 2.3. |
| Minor 5 | 4.8; 9.1 | Stated that the 256-byte cap is a UTF-8 byte-length measurement and display text is never semantically inspected. |
| Minor 6 | 11.1 | Recorded `PROBE_ternary.py` and `NEGSIM_C.py` as mutations of known misstep baselines, not independently authored positives. |

## 16. Revision 2 changelog

Revision 2 is relative to Revision 1 at
`sha256:34c09e0331f4da2bbc888782b1c36d83dc52c8b06b8207e4ef72b8e88b3490f6`. It resolves three
cross-section defects and records one accepted residual. ND-1 restores the intended Revision-0
opened-case eligibility after replacing an overbroad Revision-1 reading; ND-2 and ND-3 are
abstention-preserving precedence/evidence-channel corrections.

| Review item | Sections changed | Revision-2 disposition |
|---|---|---|
| ND-1 | 3.7; 9.1; 10.1-10.2; 11.3 | Adopted the exact pure-outcome-subset contribution rule. Mixed identifier/group/outcome integrity projections contribute nothing to joint derivation. Re-verified all 30 E10/E11 rows, restored E10 P2/P5 to candidates, and restored the opened-positive forecast to 10/12; every E11 row is unchanged. |
| ND-2 | 7.2-7.3; 9.1; 9.5; 11.3 | Made `correct-early-return-panel-gate` a synthetic isolated pure-outcome fixture with admitted `.loc` operands so hierarchy is its first reason. Pinned real `spec-14` and `spec-36` to order-9 `test-operand-lineage-unresolved` from their negated masks. |
| ND-3 | 3.6; 7.2; 9.1; 9.3 | Restricted simple-name rebinding to an alias actually imported and live in the module. Bare API-terminal spellings without that live alias do not abstain; added the complete-correction covered-negative control and kept the full non-callee rename tripwire intact. |
| MJ-6 asymmetry residual | 2.5 | Required ADR-0079 to state that the wider threshold set retained when any recognized correction is present leaves an `N = 4` strict-subset excluded-member `p < 0.01` case convictable; `0.01 * 4` does not trigger the product rule. |
