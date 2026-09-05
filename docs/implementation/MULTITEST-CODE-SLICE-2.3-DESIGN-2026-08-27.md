# Multiple-testing code slice 2.3 recall-delta design — 2026-08-27

**Status:** build-ready design, Revision 1a

**Version:** detector/check/adapter `2.3.0`, development lane only

**Normative base:**
[`MULTITEST-CODE-SLICE-2.2-DESIGN-2026-08-26.md`](MULTITEST-CODE-SLICE-2.2-DESIGN-2026-08-26.md),
Revision 0a, `sha256:64041f538ef64b4f1307702fa7c43b594dc745e10a93a30e572cdda8492a0a39`.
Unless this document names a delta, every 2.2 predicate, registry, order, reason, limit,
invariant, and test remains normative by value.

**Authoritative recall evidence:**
[`MULTITEST-RECALL-RECON-E13-2026-08-26.md`](MULTITEST-RECALL-RECON-E13-2026-08-26.md),
`sha256:d99c63caf70e2d1b1ff209c1d6ac747c17c73b911fe7616aaf1e8a3bdc34d6db`,
committed at `721b8db`. The complete
[`FINDINGS-PLAYBOOK.md`](FINDINGS-PLAYBOOK.md),
`sha256:9bcb66dff193956d63b37ff6dad289e6a459dc6adc16208102483939ce0f520a`,
governs the evidence, executed-ladder, and false-accusation standard.

The envelope-13 custody and recon pins used here are:

```text
AUDIT_RESULTS.json raw bytes sha256:dce37ab885bf077ee29692bfe00680ae6d21c1d7ead8559539d62061c200ec76
ROLE_MAP.json raw bytes      sha256:456780e6ab2a5decb7c99d31de9a6e898b7f3936e40bf378932aa51e3cda74cb
analysis.py source-set       sha256:1d8215592b8f09e8eabdbb50c6d9e60bb1d80cc745663ad6740363bf61119e58
recon artifact manifest      sha256:f186fd2b29a83d6ebffbbe76b946d95e1593a202a91673bba6b8b6c2a8c45f9a
ladder results               sha256:8a63709717e7f3c06e60cfa7aba749d35d913039995e3908083c873974563465
none-flip/movement results   sha256:19e9be447a92417c2cc2ee0b09558a0928f64877addf834ada52458279b5c052
targeted FA results          sha256:b275ce2f81de285d928b63aaa83f3e4d7d1687e5cd862867939673ffd47f89dc
```

The source-set digest is SHA-256 over the sorted `sha256sum` lines for the fifteen
`cases/*/project/analysis.py` files. Prose in those projects is context only and never detector
evidence.

## 1. Decision and hard boundary

Version 2.3 adopts exactly two recon changes:

1. **D13-A:** at a recognized reader call, resolve one immutable function-local path Name through
   one exact static binding whose right-hand side already satisfies one of two closed path forms;
   and
2. **D13-B:** close provenance between an already-recognized terminal-rendering node and its one
   structurally equal final sink clone, using source position, structure, and family position.

D13-A adds one backward value edge. D13-B repairs one clone-identity edge. Neither adds a reader
API, reader keyword form, correction API, correction method, manual correction, registered test,
threshold, p container, group split, row mask, sink, evidence slot, wording slot, or prose channel.
Neither changes the 2.2 D2/D3/D5/D6 grammars.

The following 2.2 surfaces remain unchanged by value:

- every whole-module registered-test, correction-terminal, statistics-prefix, repeated-construct,
  dynamic-execution, API-rebinding, hierarchy, and execution-prevention census;
- the exact registered-call count `performed_count == N`, including conservative dead-call and
  helper instances and the `>N` sensitivity/duplicate-call guard;
- recognized correction APIs, defaulted methods, return positions, input-determined coverage,
  correction classifications, p-container reconstruction, and the exact manual adjusted-p
  grammar;
- the order-12/off-grammar versus order-13/direct-threshold partition, source-text Decimal rule,
  syntax-wide A5 binding rule, raw-family `{0.05}` narrowing, and product rule;
- operand identity, authorized group selection, and complete-row equality;
- total forward accounting of every family p-value consumer;
- extremum, export, upstream-value, family-collection, hierarchy/control, partition, resampling,
  sensitivity, dead/live branch, outcome-mutation, and statistics guards; and
- the rule that every unresolved call, transform, container, store, alias, or escape on a p slice
  abstains rather than being treated as absence of correction.

P2's two full registered-test passes remain a bin-C residual under the exact global call-count
guard. P6's proper-subset `P * 3` adjustment remains a bin-C residual under the full-family manual
correction grammar. No evidence or wording policy changes in this delta.

The 2.0 load-bearing candidate premise remains intact: global censuses establish the complete
syntactic test/correction/statistics surface; backward slices establish authorized operands and
complete rows; forward slices account for every family p-value; and unrecognized p or threshold
arithmetic cannot be crossed. D13-A cannot create a reader frame—the recognized reader call is
still the sole frame root. D13-B cannot create a conclusion or hide a consumer—the node must
already satisfy a frozen terminal grammar and all original and clone consumers remain total.

## 2. Identity, contract, wording, isolation, and ADR record

### 2.1 Versioned identities

```text
check:authorized-complete-family-correction-over-code-test-battery@2.3.0
adapter:authorized-complete-family-correction-over-code-test-battery:code-csv-v1@2.3.0
detector:bounded-code-csv-multiple-testing-conflict@2.3.0
method-conflict-binding:authorized-complete-family-correction-over-code-test-battery-v1:development
```

Only the development binding advances. Versions `1.0.0`, `1.1.0`, `2.0.0`, `2.1.0`, and
`2.2.0` remain registered and directly importable for historical replay. Maturity remains
`question_only`, production Finding permission remains false, and the development controller
emits no Findings.

### 2.2 Contract and wording

Contract profile `1.2.0`, its group-column plus ordered outcome-family authority, validator,
canonical values, seven error categories, and historical records are byte-unchanged. D13-A
compares a resolved path only with the already-authorized material path. D13-B consumes only
existing p-origin and sink facts. Neither creates authority.

No evidence or wording slot changes. The wording identity remains byte-identical:

```text
method-conflict-finding:code-csv-complete-family-correction-requirement-conflict-v1@1.0.0
sha256:80c4bb3c0afd75b290ab02a195e5285528f982554ab46b373e63072232902259
```

Presentation text remains non-evidence. A wording v2 is neither needed nor permitted. The
`PERFORMED_COUNT`, family size, corrected positions, sink kinds, and conclusion facts retain their
2.2 meanings.

### 2.3 Frozen-lane isolation and 2.2 anchors

The 1.0/1.1/2.0/2.1/2.2 MT modules, qualified pseudoreplication `3.1.0`, complete-domain lane,
GrantPins, grants, qualification records, threshold policies, metric sets, Finding objects,
wording objects, `method_conflict_grant_pins.py`, and every
`code_csv_dependence_dataflow*.py` remain byte-untouched. The 2.3 implementation is made by
versioned copies and has no private cross-version import.

The new frozen 2.2 replay anchor pins:

```text
dataflow     sha256:c34c7ab4872923aeb4271e537905cda9c519646bfa996ad1e99ef149c11cc325
adapter      sha256:155770410e48a238df81cc87b521c8ac2bf526ce7bdf03c49c372c9bb5da7337
detector     sha256:8bcee3d46ee089e5587378f111779ba37f38968c590fa875f0a883fce296f92c
integration  sha256:f63fdb3918dfd36410f39d313781e9a334e604bd51aa81ff858a5a6ecee54f4d
2.2 design   sha256:64041f538ef64b4f1307702fa7c43b594dc745e10a93a30e572cdda8492a0a39
2.2 E12 replay `adapter_replay_records_v2_2.json`
             sha256:f8b7808b3baee264e9c496e2e899686af235e72c37b9647ce4255d10adbb02d8
2.2 development ledger
             sha256:70d408017bcf8d5fdefd9d033828a07425997e043831d352b4abcff7bc03573b
```

The anchor imports those exact 2.2 components, never the active development binding, and replays
the historical E10, E11, E12, E13-baseline, PROBE/NEGSIM, ladder, adversary, and 50-case corpus
inputs. Canonical 2.2 bytes must remain equal.

The corpus anchors are separately immutable:

```text
`adapter_replay_records_v2_1.json` raw bytes
sha256:7c37669c8ccfdb0b754aa03ee1dbcee1dac78fa4bb44105e17c5d1886aaed502

canonical `2.1.0.results` bytes, which frozen 2.2 comparison rows equal
sha256:80e000e923d23133a9c93433b023a871ee4fe095aeffadc9b970ae803c3d8a55
```

The second digest is over compact, key-sorted UTF-8 canonical JSON with no trailing newline.
During the 2.3 build, an explicit frozen-2.2 adapter run must reproduce those fifty comparison
rows byte-for-byte. The 2.1 replay file is not regenerated, and the 2.2 comparison rows are not
re-recorded under changed bytes.

### 2.4 Required ADR-0079 amendment

The build appends a narrow 2.3 note to
`ADR-0079-MULTIPLE-TESTING-CODE-SLICE-2.0-INVERSION.md`. It records:

- D13-A as one exact local reader-path value edge, including both path productions and every
  module-wide stability/escape refusal in section 4;
- that D13-A never rewrites `T0`, creates no frame at the path assignment, and leaves reader APIs,
  keywords, row proofs, and the reader census otherwise unchanged;
- D13-B as source-position-plus-structure clone provenance, using one shared map in the
  off-grammar, hierarchy, and conclusion registries with no terminal grammar change;
- D13-B's placement after the successful 2.2 D6 second-pass equality check, plus its own
  no-AST-mutation and idempotence obligations;
- the executed combined none-flip result `0/25`, `0/36`, `0/6`;
- P2's exact `2N` call-count residual and the rule that changing it needs new evidence/wording
  policy and separate ADR review;
- P6's proper-subset manual factor residual and the rule that widening correction acceptance is
  a candidate-surface change requiring separate ADR review; and
- the four opened adapter-row movements in section 9.2, distinguishing P5's candidate gain from
  P6/N1/N9's honest deeper-wall exposure.

The ADR note does not retroactively alter any historical detector version.

## 3. Pipeline and common structural terms

Let `T0` be the bounded AST parsed from untouched `analysis.py` bytes. Let `S0` be the 2.2
execution scope before its first terminal-helper pass, `S_D6` the scope after the successful D6
one-pass/two-pass equality check, and `S_FINAL` the final expanded scope supplied to `_MtEngine`.

The 2.3 order is:

1. parse `T0`, construct the full resolver, and run every whole-module census on untouched `T0`;
2. run the unchanged registered-call cardinality/API and global unrecognized-correction gates;
3. when the unchanged reader census encounters a recognized reader whose direct path argument is
   an unresolved Name, query D13-A against untouched `T0`; use the successful value only at all
   existing authorized-reader-root queries;
4. run the unchanged 2.2 counted-loop, outcome, D2, helper/X4, D5, and D6 stages;
5. after D6's existing second-pass canonical equality succeeds, create immutable D13-B origin
   descriptors over `S_D6` without changing it;
6. run unchanged literal destructuring, outcome renormalization, record expansion, record-loop
   expansion, D2 occurrence preservation, resolver, and CSV-row stages;
7. resolve each D13-B descriptor against `S_FINAL`, requiring one total clone mapping, and pass
   that one immutable map to `_MtEngine`; and
8. run unchanged ordered guards, with the off-grammar, hierarchy, and conclusion registries
   consulting the same map, then return the first closed reason or one candidate fact.

Generated analyzer nodes and D13-A/B descriptors never feed back into a whole-module census, the
A5 binding count, API rebind scan, outcome-mutation scan, source size/node count, evidence quote,
or source digest. No source is unparsed or reparsed. Evidence locations always refer to `T0`.

Terms used below are structural:

- `READER` is a call already accepted by the complete 2.2 reader API, positional-path, and keyword
  grammar. D13-A does not decide whether a call is a reader.
- `PATH_NAME` is the direct `ast.Name` in `READER.args[0]`.
- `CONST` is either one safe string `ast.Constant`, or one simple module-constant Name that the
  unchanged closed module-constant resolver resolves to exactly one such string. Resolver
  ambiguity is `api-resolution-ambiguous` and is never rescued by D13-A.
- `CALL` is a call whose callee resolves through the unchanged registry to the one uniform
  registered family-test API.
- `P` is the registered `.pvalue` origin of one proved `CALL` and one family position.
- `N` is the exact authorized outcome-family cardinality, at least three.
- `DISPLAY_STRING` is the unchanged nonempty, NUL-free `ast.Constant` string of at most 256 UTF-8
  bytes. Only its byte count/NUL/nonempty properties are measured; text is never interpreted.
- `SOURCE_POS(node)` is exactly `(lineno, col_offset, end_lineno, end_col_offset)`, all present.
- `STRUCT(node)` is the canonical AST node kind and complete field/value tree with contexts and the
  existing `_sc_mt_presentation_helper`/`_sc_mt_terminal_rendering` markers, excluding source
  attributes and object identity.
- `FAMILY_POS(node)` is the singleton position proved by the unchanged p-origin or decision
  resolver. A node with zero or multiple positions has no D13-B key.

Similarity to a production is not equivalence. Failed D13-A/B productions follow the unchanged
2.2 abstention path and never supply partial evidence.

## 4. D13-A — exact static local reader-path binding

### 4.1 Eligible reader site

D13-A is queried only for this production:

```text
READER := accepted_reader(PATH_NAME, <unchanged admitted reader keywords>)
```

All conditions are mandatory:

1. the call is already a `READER` by the 2.2 API and keyword grammar;
2. it has exactly one positional path argument and that argument is `PATH_NAME`;
3. the unchanged direct `_static_path(PATH_NAME, full_resolver)` returns unresolved;
4. `PATH_NAME` is function-local: its sole binding and `READER` occur in the same lexical,
   non-async `ast.FunctionDef` and in no nested function, lambda, class, or comprehension;
5. the binding is a direct element of that function's top-level statement list, and `READER` is
   within a later direct simple `Assign`/closed `AnnAssign` value or direct `Return` value in that
   same list; neither site is inside `If`, `IfExp`, `For`, `While`, `Try`, handler, `else`,
   `finally`, `With`, `Match`, Boolean short-circuit, comprehension, lambda, or generator; and
6. the binding uniquely dominates the reader in that list. Statements between them may not load,
   store, delete, alias, or escape `PATH_NAME`.

`pd.read_csv(path)` and `return pd.read_csv(path)` can qualify. A keyword path such as
`pd.read_csv(filepath_or_buffer=path)`, a `None` path, a second positional argument, or a call newly
made reader-shaped by D13-A cannot. Import aliases for `pandas`, `numpy`, `os`, or `pathlib` are
handled only by the unchanged qualified-identity resolver; they are not path-value aliases. Any
ambiguous/shadowed import keeps its existing reason.

### 4.2 Exact right-hand-side grammar by value

`PATH_NAME` has exactly one parsed binding, which is either:

```text
PATH_NAME = PATH_EXPR
PATH_NAME: CLOSED_ANNOTATION = PATH_EXPR
```

The `Assign` has exactly one simple Name target. The `AnnAssign` has one simple Name target, a
non-`None` value, and the unchanged 2.2 closed annotation. No destructuring, chained assignment,
attribute/subscript target, or `NamedExpr` qualifies.

`PATH_EXPR` is exactly one of these two productions after resolving callee identities and `CONST`:

```text
OS_PATH := os.path.join(
               os.path.dirname(os.path.abspath(__file__)),
               CONST,
           )

PATHLIB_PATH := Path(__file__).resolve().parent / CONST
```

The productions are closed:

- `os.path.join`, `os.path.dirname`, and `os.path.abspath` each have exactly the displayed
  positional arguments and no keywords;
- `Path` resolves exactly to `pathlib.Path`, has sole argument the Load Name `__file__`, and has no
  keywords;
- `.resolve()` has zero positional arguments and no keywords, followed by the direct `.parent`
  attribute;
- `/` is one `ast.BinOp(op=Div)` with that exact left side and `CONST` on the right;
- `CONST` resolves without calls, arithmetic, formatting, environment access, `cwd`, parameters,
  container indexing, or conditional choice; and
- a named `CONST` and its existing module-constant alias closure satisfy the unchanged resolver's
  single-value stability proof—no rebind, mutation, deletion, conditional definition, or
  unresolved escape; and
- applying the unchanged safe-path checks yields bytes exactly equal to the contract's authorized
  CSV path.

No file-parent Name, `os.path.dirname(__file__)`, `Path.cwd()`, `.parents[...]`, `.joinpath()`,
string concatenation, f-string, format call, environment variable, CLI argument, config value,
helper return, absolute path, or additional path component is admitted. An existing direct reader
path accepted by 2.2 does not need and does not enter D13-A.

### 4.3 Module-wide immutability, alias, and escape proof

The analyzer scans all of `T0`, not only the selected execution scope. By spelling and lexical
ownership, `PATH_NAME` must have exactly the one binding in 4.2 and exactly the one value-bearing
Load at `READER.args[0]`. Refuse D13-A if any of the following occurs anywhere in the parsed
module:

- a second `Assign`/`AnnAssign`, any `AugAssign`, `NamedExpr`, `del`, `global`, or `nonlocal` for
  `PATH_NAME`;
- attribute, integer/subscript, or slice Store/Del rooted in `PATH_NAME`;
- any Name-to-Name alias in either direction, including `alias = PATH_NAME`,
  `PATH_NAME = alias`, destructuring, or container insertion;
- any receiver call on `PATH_NAME`, regardless of attribute spelling;
- passage as a positional or keyword argument to any call other than the one eligible `READER`;
- return, yield, await, closure capture, default argument, decorator, lambda/comprehension capture,
  format/f-string payload, comparison, Boolean operation, or other non-reader load;
- a binding in a conditional/lazy/exception/control region; or
- binding in one function and reader use in another, including passage through a helper formal or
  a module-level intermediary.

There is no read-only escape allowlist. A logging use, existence check, `str(PATH_NAME)`, second
reader, or user-helper passage disqualifies the admission. Failure is conservative and keeps the
existing reader-census result; it never assumes immutability from an incomplete scan.

### 4.4 Reader-root projection and refusal outcomes

D13-A returns only the exact authorized path value for the one eligible `READER`. It creates no
assignment-rooted DataFrame, array, frame alias, or row-completeness fact. The call remains the
sole accepted reader root, and unchanged X4/frame return expansion is still required before test
operands can inherit it.

One centralized `resolved_reader_path(READER)` query must be used everywhere 2.2 asks whether the
same call is the authorized root: the full reader census, operand-reader path census, accepted
reader frame creation, authorized-data-name closure, and any downstream equality check. D13-A may
not be implemented only in the first census while leaving a later root query inconsistent.

Failure classifications remain:

- an eligible API call with a refused/unresolved local binding contributes no authorized path and
  retains `authorized-reader-lineage-unavailable`, unless the unchanged second-reader rule has the
  earlier `additional-accepted-reader-present` reason;
- a successfully resolved local binding whose bytes differ from authority retains
  `authorized-reader-lineage-unavailable` or the existing additional-reader result; and
- after a successful path edge, unresolved helper-frame lineage, operands, masks, or row coverage
  reaches its ordinary later reason. D13-A never substitutes a later proof.

## 5. D13-B — terminal-clone provenance closure

### 5.1 Origin eligibility; zero grammar change

D13-B creates an origin descriptor only for a node in `S_D6` that satisfies exactly one frozen
2.2 production:

1. **R1 literal-percent rendering:** an `ast.BinOp(op=Mod)` whose left operand is
   `DISPLAY_STRING`, whose right payload has exactly one existing family-p origin, and which passes
   every non-sink structural condition of the installed `_literal_percent_presentation`; or
2. **transformed two-string verdict:** an `ast.IfExp` already carrying
   `_sc_mt_terminal_rendering=True` from the installed `TPH`, with two admitted `DISPLAY_STRING`
   arms and a test that the unchanged decision resolver maps to exactly one family position.

The descriptor is not available to a merely similar percent operation or IfExp. D13-B does not
run a helper classifier, infer a marker, recognize a new arm, interpret display text, or relax a
threshold. A helper returning arithmetic, a correction call, a number/container, a dynamic arm,
an unrecognized free Name, multiple returns/emissions, or any shape refused by frozen 2.2 `TPH`
has no descriptor.

Each eligible atomic node key is exactly:

```text
(production_kind, SOURCE_POS(origin), STRUCT(origin), FAMILY_POS(origin))
```

All four fields are required. A missing end position, zero/multiple p origins, zero/multiple
decision positions, or inconsistent percent/verdict family position refuses the descriptor.

A D13-B closure entry is composite:

```text
(
  transport_key,        # R1 key, or the terminal IfExp key when it is itself the transport
  decision_key_or_none, # tagged terminal IfExp contained by that transport
  FAMILY_POS,
)
```

When an R1 rendering contains a tagged terminal IfExp, as in E13 P5, both keys are mandatory, the
IfExp must be a descendant of that exact R1 node, and both must resolve to the same singleton
family position. A standalone R1 presentation without a decision has `decision_key_or_none=None`.
A standalone tagged terminal IfExp uses its own key as both transport and decision. This composite
entry prevents the off-grammar registry from clearing one rendering while hierarchy/conclusion
credit a different decision.

The transport and decision are one joint matching unit. The matcher never resolves a transport
clone first and then independently searches for a decision clone. It matches the composite entry
against one final sink payload, verifies the transport-to-decision containment relation once, and
accepts or refuses the entire entry atomically.

### 5.2 Exact final-clone mapping

After all unchanged normalizers produce `S_FINAL`, D13-B searches only descendants of payloads of
the existing registered sinks for which `p_result_eligible=True`. Each atomic final node is a
clone of its origin only when all of these values are equal:

```text
production_kind
SOURCE_POS
STRUCT
FAMILY_POS
```

Exactly one jointly matched transport/decision pair must occur beneath exactly one registered sink
payload for each composite entry. The original and final containment relationship is checked once
as part of that joint match. Object identity is not part of the key. Position alone is
insufficient, structure alone is insufficient, and a match outside a p-eligible sink is
insufficient.

Multiple origin descriptors **may** share one `SOURCE_POS` and one `STRUCT` when every descriptor
resolves to a distinct singleton `FAMILY_POS` and every complete composite entry maps one-to-one to
its own final clone pair. This is the required P5 fanout: the one `print_result` definition is
expanded across seven family members, so five descriptors at one rendering line resolve to
positions `{2,3,4,5,6}` and two descriptors at the other rendering line resolve to positions
`{0,1}`. Shared source/structure across those positions is not ambiguity.

For cross-position sharing, refusal is confined to either of these actual failures:

1. one descriptor's `FAMILY_POS` is not uniquely resolvable to a singleton; or
2. two descriptors compete for the same final transport or decision clone.

Origin descriptors are retained as an ordered occurrence sequence, not a set keyed by their
structural tuple. Equal composite keys from two analyzer occurrences are never deduplicated; each
occurrence must independently claim a final clone pair. The analyzer-only occurrence ordinal
preserves multiplicity but is not a matching field, evidence value, or substitute for
`FAMILY_POS`. This makes the second refusal observable when two equal descriptors compete for one
clone.

A missing marker or failed structural/containment/sink/consumer production remains ineligible under
the surrounding clauses; it is not re-described as a family-position collision. A clone shared by
two emissions is a consumer/cardinality failure. Different, uniquely resolved family positions at
one source position are never by themselves unresolved.

The mapping is an immutable one-to-one relation. No two origins may claim one clone and no clone
may satisfy two descriptors. Its source/position entries are analyzer metadata only and never
become evidence text.

### 5.3 Total consumer accounting and the three consumers of the map

Successful structural matching is necessary but not sufficient. D13-B must prove total accounting
over both the `S_D6` origin and its `S_FINAL` clone:

- every parent edge from the origin through later normalized copies belongs to the unchanged
  presentation transports;
- every consumer of the final clone lies on the single registered p-eligible sink payload path;
- no call, correction, arithmetic transform, comparison other than the already-proved decision,
  container insertion, assignment/store, alias, export, second emission, hierarchy/control edge,
  or escape is omitted; and
- the origin and clone resolve to the same one p origin and family position.

Any unaccounted consumer returns `unresolved-pvalue-consumer`. If the clone participates in a
control/prevention relation that cannot be reconciled with the same map, the result is
`pvalue-control-dependence-unresolved`. Neither failure defaults to terminal rendering or a
conclusion.

Exactly one resolved map object is passed to and queried by all three sites. For a composite entry,
the transport and decision fields are inseparable:

1. `_off_grammar_transform_guard` may exclude the entry's mapped transport clone, and no other
   node;
2. `_hierarchy_guard` may exclude the entry's mapped decision clone only under the frozen terminal
   rule; and
3. `_conclusion_positions` may credit only that same decision clone/family position at the entry's
   same sink.

If the three sites would derive different membership, sink, or family position, construction
fails before any exclusion and abstains. There is no independently recomputed position-only
fallback. This paired use is load-bearing: clearing only off-grammar/hierarchy while failing to
credit the conclusion would strand the case; crediting a conclusion without both guards would
manufacture evidence.

### 5.4 Ordering and idempotence relative to D6

D13-B runs only after the 2.2 D6 check has proved:

```text
canonical_ast(TPH(TPH(S))) == canonical_ast(TPH(S))
```

The required order is:

```text
D6 first pass after X4
-> D6 unchanged second-pass equality check
-> capture D13-B origin descriptors from S_D6
-> unchanged literal/record/outcome expansions
-> resolve D13-B clones in S_FINAL
-> engine guards
```

D13-B never invokes `TPH`, never feeds a mapped clone back to D6, and never mutates either AST.
Therefore it cannot change D6's result or manufacture a second terminal marker. The build must
prove both:

```text
canonical_ast(S_D6 before D13-B) == canonical_ast(S_D6 after D13-B)
canonical_ast(S_FINAL before D13-B) == canonical_ast(S_FINAL after D13-B)
```

and:

```text
closure(closure(S_D6, S_FINAL)) == closure(S_D6, S_FINAL)
```

where equality includes ordered descriptor-occurrence multiplicity, descriptor keys,
origin-to-clone pairs, sink identities, family positions, consumer sets, and failure status.
Running the closure twice on already-mapped scopes changes nothing. Failure is
`multiple-testing-code-inspection-exception` and a stop-and-report ordering regression, not a
reason relabel chosen to satisfy an oracle.

## 6. False-accusation analysis and required fixtures

Every fixture executes the public 2.3 analyzer and adapter. Names and exact outcomes are normative.
A `covered/complete` result means zero candidate and zero Finding with recognized correction
coverage equal to all `N` positions.

### 6.1 D13-A adversaries

| Fixture | Strongest correct-analysis shape | Exact expected outcome | Unchanged protection |
|---|---|---|---|
| `correct-static-local-reader-path-complete-correction` | An admitted local `os.path` binding reads the authorized CSV; every one of `N` p-values enters one recognized default-method `multipletests` call and every verdict uses the adjusted values. | **Covered/complete**, positions `{0..N-1}`; zero candidate/Finding. | D13-A proves only the path. The unchanged correction input/return and conclusion maps prove complete coverage, which cannot become `none` or `strict_subset`. |
| `correct-local-reader-path-mutated` | Bind the exact path, then use `path += ""` before a complete corrected family. | Abstain `authorized-reader-lineage-unavailable`; zero candidate/Finding. | Module-wide `AugAssign` refusal prevents any path edge. |
| `correct-local-reader-path-conditionally-bound` | Bind the exact path in one `if` branch, then read and completely correct the family. | Abstain `authorized-reader-lineage-unavailable`; zero candidate/Finding. | A conditional binding never qualifies, even when the branch test is a literal. |
| `correct-local-reader-path-aliased` | Bind the exact path, assign `reader_path = path`, and pass the alias to the reader before complete correction. | Abstain `authorized-reader-lineage-unavailable`; zero candidate/Finding. | Any Name alias is refused; D13-A does not chase identity aliases. |
| `correct-local-reader-path-nonconstant-component` | Build the filename from a parameter/environment/helper result and then completely correct the family. | Abstain `authorized-reader-lineage-unavailable`; zero candidate/Finding. | `CONST` must resolve to one closed module string; dynamic components are never path evidence. |
| `correct-local-reader-path-reassigned-after-bind` | Read through the exact bound path, then reassign the path later; the scientific family is completely corrected. | Abstain `authorized-reader-lineage-unavailable`; zero candidate/Finding. | The scan is module-wide and includes stores after the reader; immutability is not a reaching-definition approximation. |
| `correct-local-reader-path-cross-function` | One helper binds/returns the path and another calls the reader, followed by complete correction. | Abstain `authorized-reader-lineage-unavailable`; zero candidate/Finding. | Binding and reader must be in one lexical function and the path may not cross a helper boundary. |
| `correct-local-reader-path-second-reader` | The admitted binding is used by the authorized reader while another accepted reader points to a second CSV. | Abstain `additional-accepted-reader-present`; zero candidate/Finding. | The unchanged whole-module reader census sees both calls; D13-A cannot hide or merge the second path. |

The five commission-required refusal shapes are the mutated, conditionally bound, aliased,
nonconstant-component, and reassigned-after-bind fixtures. The cross-function and second-reader
siblings make the escape and global-census boundaries executable rather than prose-only.

E13 N1 is the strongest real complete-correction neighbor sharing the Path production. It moves
only to `correction-family-lineage-unresolved`. E13 N9 is the strongest pre-registered threshold
neighbor sharing the os.path production. It moves only to `unresolved-decision-threshold`. E13 N6
uses `csv.DictReader` and remains `authorized-reader-lineage-unavailable`; D13-A never admits its
reader model.

### 6.2 D13-B adversaries

| Fixture | Strongest correct-analysis shape | Exact expected outcome | Unchanged protection |
|---|---|---|---|
| `correct-terminal-clone-whole-family-bonferroni` | Every p is adjusted by the recognized full-family hand Bonferroni grammar, then passes through the exact cloned R1/two-string terminal transport. | **Covered/complete**, positions `{0..N-1}`; zero candidate/Finding. | Clone closure changes transport identity only; unchanged manual coverage remains complete. |
| `correct-terminal-clone-preregistered-001-N5` | Five raw p-values reach cloned two-string verdicts at literal `0.01`, a pre-registered corrected level. | Abstain `unresolved-decision-threshold`; zero candidate/Finding. | D13-B does not bypass order 13, the `{0.05}` raw-family narrowing, source-text Decimal, or the product rule. |
| `correct-terminal-clone-hidden-correction-helper` | A presentation-shaped outer helper wraps a p from an unresolved adjustment helper. | Abstain `unresolved-pvalue-consumer`; zero candidate/Finding. | The hidden call is an unaccounted p consumer and cannot receive a terminal descriptor. |
| `correct-terminal-clone-ambiguous-two-sinks` | One eligible terminal value is cloned into two otherwise admitted emissions. | Abstain `unresolved-pvalue-consumer`; zero candidate/Finding. | Mapping cardinality must be exactly one sink clone; no sink is chosen heuristically. |
| `correct-terminal-clone-family-position-collision` | Two expanded origin descriptors have the same composite key, including the same singleton family position, while normalization leaves one final transport/decision clone pair; both descriptors therefore claim that one pair. The underlying family is completely corrected. | Abstain `unresolved-pvalue-consumer`; zero candidate/Finding. | This is genuine clone competition, not permitted cross-position fanout. The one-to-one map refuses two descriptors claiming one clone. |
| `positive-terminal-clone-N-position-fanout` | One presentation helper is expanded to `N` family call sites; the `N` descriptors share helper source/structure but resolve to `N` distinct singleton positions and map jointly to `N` distinct clone pairs. The P5 polarity has Holm coverage `{0,1}` and raw conclusions `{2,3,4,5,6}`. | **Candidate** `strict_subset`, corrected positions `{0,1}` of `7`; exactly one candidate and zero Findings. | Source-position reuse is admitted only because family position disambiguates every descriptor and the map proves `N` one-to-one clone pairs with total consumers. This is the mandatory positive control for the P5 shape. |
| `correct-terminal-clone-computed-threshold` | The tagged verdict uses a computed Sidak/Bonferroni threshold. | Abstain `unresolved-decision-threshold`; zero candidate/Finding. | The existing direct-threshold grammar remains the only decision authority. |
| `correct-terminal-clone-export-sibling` | The rendered verdict reaches print while the same family p-value also flows to `.to_csv`, `numpy.savetxt`, or `json.dump`. | Abstain `unresolved-pvalue-consumer`; zero candidate/Finding. | Total accounting includes every original and clone consumer; the export is not presentation. |

The existing 2.2 FA-6 hidden-correction presentation fixture remains
`unresolved-pvalue-consumer`; it lacks the complete eligible-map conditions. A merely similar
numeric helper, arithmetic return, container return, dynamic arm, or untagged IfExp follows its
ordinary 2.2 guard.

### 6.3 Per-admission attack summary

| Admission introduced by 2.3 | Strongest false-candidate attack | Required blocking rule |
|---|---|---|
| One local path value edge | Freeze an authorized-looking value, mutate or alias it to a second file, then run a correctly corrected family. | Module-wide unique binding, no alias/mutation/escape, exact authority byte equality; failure keeps reader abstention. |
| Exact os.path/Path expression | Hide a dynamic component beneath a familiar path API. | Closed two-production AST and closed `CONST`; no recursive general path evaluator. |
| Clone identity across normalization | Put a correctly adjusted p in one clone and a raw p in another structurally similar emission. | Source position + full structure + family position + one-to-one mapping + total consumers. |
| Shared map exclusion/credit | Clear an off-grammar node but credit a different clone as the conclusion. | One immutable map object is consumed by all three registries; disagreement abstains before exclusion. |

All historical adversaries remain pinned: default-method complete correction, hand
Sidak/Holm/Bonferroni, off-registry correction, sensitivity duplicate, discovery/validation split,
all-NumPy assert/match/short-circuit and early-exit gates, label-permutation maxT, extremum, export,
upstream p, partition, resampling, outcome mutation, dynamic p container, and N=4 bare `0.01` do
not weaken.

## 7. Ordered integration and closed reasons

### 7.1 Ordered predicate changes

The 2.2 first-reason order remains. The two insertions are:

| Existing stage/order | 2.3 operation | Failure path |
|---|---|---|
| after global test/correction gates, at reader-root resolution | D13-A answers the authorized path only for one eligible unresolved Name argument | `authorized-reader-lineage-unavailable`; existing `additional-accepted-reader-present` |
| after successful D6 equality and final expansion, before engine guards | D13-B builds one provenance map used by off-grammar, hierarchy, and conclusion logic | `unresolved-pvalue-consumer`; `pvalue-control-dependence-unresolved`; inspection exception only for violated internal idempotence |

D13-A cannot change the earlier P2 call-count reason. D13-B cannot change correction coverage,
manual arithmetic, or direct-threshold order. Direct-P comparisons remain exclusive to order 13.
P6 advances past the reader wall but stops at the unchanged order-12 manual grammar.

### 7.2 Guard ownership

| Guard | Trigger source in 2.3 | Delta effect |
|---|---|---|
| Registered tests, sensitivity, dead/live branches | Untouched `T0` census plus existing conservative multiplicity | No effect; P2 remains `12 > N=6`. |
| Correction/statistics/repeated/dynamic/API rebind | Untouched `T0` | No effect. |
| Reader and additional-reader census | Untouched `T0`, full resolver, and D13-A's one exact value query | One unresolved local path Name can resolve; all calls remain globally visible. |
| Operand and row completeness | Backward slices rooted at the recognized reader call | No new frame or selection route; no effect after root creation. |
| Family collection and total p consumers | Forward slices over normalized scope plus D13-B map | A mapped clone is a known transport only when every origin/clone consumer is total. |
| Manual correction and threshold | Forward slice plus untouched source bindings | No effect; D13-B transports existing decisions only. |
| Hierarchy/control/prevention | Whole module plus slice provenance | One already-tagged terminal clone uses the shared map; every other control remains. |
| Conclusions | Forward slice and registered p-eligible sinks | The same mapped terminal decision can credit its existing singleton position; no new comparison grammar. |
| Extremum/export/upstream/partition/resampling/statistics | Global censuses and slices | No effect. |

### 7.3 Closed reason set

No reason is added, removed, retired, or relabeled. The 2.3 set is exactly:

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

The documented-unreachable annex for `conclusion-output-sink-unavailable` remains unchanged.
Public 2.3 analyzer emitter fixtures plus that annex are set-equal to the adapter closed set. A
reason literal in a historical-version test cannot satisfy 2.3 coverage.

## 8. Considered and rejected

### 8.1 P2 — duplicate complete family pass

P2 executes two complete six-member registered-test passes and emits decisions from both. The
whole-module census therefore proves `performed_count=12` while authority fixes `N=6`. Version 2.3
retains `extra-registered-test-outside-authorized-family` exactly.

Collapsing the calls as presentation duplicates would make the evidence count false and would
weaken the same guard protecting a complete corrected family followed by a sensitivity rerun. A
future delta needs an explicit model of pass roles, conclusion ownership, sensitivity polarity,
and wording for `2N` performed calls, plus its own ADR. This delta changes none of them.

### 8.2 P6 — proper-subset manual factor

After D13-A, P6 reaches `min(P * 3, 1)` for three selected members while the authorized family has
`N=5`. The installed manual grammar recognizes only the exact full-family factor `N`. Version 2.3
therefore pins `unresolved-manual-correction-present`.

Recognizing a proper-subset factor would widen correction acceptance and can manufacture
`strict_subset` accusations. It requires its own policy ADR, correction-surface adversaries, and
review of whether the subset is itself an authorized family. D13-A is not authority for that
change. The standing declined `P < ALPHA / K` manual-Bonferroni policy also remains declined.

### 8.3 No proxy admission into deferred residuals

Version 2.3 does not enter any 2.2 deferred family:

- DataFrame p-table construction/transport;
- positional-record subset identity before strict-subset inference;
- the dominated record-flag fold; or
- zip write-back with complete/partial dual polarity.

A D13-B node embedded in one of those unresolved containers remains unresolved. Clone provenance
does not supply record identity, row order, subset positions, write-back polarity, or table
semantics.

## 9. Adapter-level oracles

### 9.1 Envelope 13 — normative fifteen-row table

The 2.3 adapter executes each project through its committed `profile_1_2_0.json`. The exact oracle
is:

| Role / case | 2.3 adapter outcome | Exact reason/classification |
|---|---|---|
| P1 `686d1432762cd49d9b54` | candidate | `none` |
| P2 `c336be2521785ab6a954` | abstain | `extra-registered-test-outside-authorized-family` |
| P3 `4f042d10b3f9a43d1099` | candidate | `none` |
| P4 `ffbe12246cf8a4227210` | candidate | `none` |
| P5 `80091f37c722eba28e18` | candidate | `strict_subset`, corrected positions `{0,1}` of `7` |
| P6 `d0f9fcd52f47e4d64668` | abstain | `unresolved-manual-correction-present` |
| N1 `b7d38f6e9284abfd3ee6` | abstain | `correction-family-lineage-unresolved` |
| N2 `f65170c644b90c4a893c` | abstain | `unresolved-decision-threshold` |
| N3 `c15f507ad59999fd9371` | abstain | `unresolved-manual-correction-present` |
| N4 `cfbb5edfd1534e7419fd` | abstain | `extra-registered-test-outside-authorized-family` |
| N5 `8f37c5176ab3c0a61e4d` | abstain | `test-battery-cardinality-unresolved` |
| N6 `6a102a97a065f9c8879f` | abstain | `authorized-reader-lineage-unavailable` |
| N7 `aba768f8d0b3f3548683` | abstain | `authorized-family-test-census-incomplete` |
| N8 `325c686a92196956359a` | abstain | `test-battery-cardinality-unresolved` |
| N9 `ab70cdb37bb2977d725c` | abstain | `unresolved-decision-threshold` |

The adapter writes a checked-in 2.3 E13 replay record and replays it twice byte-identically. The
sealed `AUDIT_RESULTS.json`, `ROLE_MAP.json`, projects, profiles, custody log, and blind score are
read-only and are never regenerated.

P5's pinned row also depends on the unchanged closed module-constant resolver proving
`ADJUST_METHOD = "holm"` at the recognized correction call. The E13 oracle test must assert that
the method resolves to `holm` before it asserts coverage `{0,1}`. A future correction-grammar or
constant-resolver tightening therefore cannot silently preserve a superficially similar candidate
while losing the correction-method proof.

### 9.2 Exact opened movement set

Movement means any canonical adapter-row byte change in outcome, first reason, correction
classification, or corrected positions between explicit frozen 2.2 and 2.3 adapter executions.
The movement set is exactly four rows:

| Case | Frozen 2.2 row | Required 2.3 row | Explanation |
|---|---|---|---|
| E13 P5 `80091f37c722eba28e18` | abstain `authorized-reader-lineage-unavailable` | candidate `strict_subset`, positions `{0,1}/7` | D13-A clears the path; D13-B closes the already-recognized terminal clone; unchanged Holm/raw position accounting supplies the candidate. |
| E13 P6 `d0f9fcd52f47e4d64668` | abstain `authorized-reader-lineage-unavailable` | abstain `unresolved-manual-correction-present` | D13-A exposes the deliberate proper-subset-factor residual; this is an honest deeper-wall movement, not a candidate. |
| E13 N1 `b7d38f6e9284abfd3ee6` | abstain `authorized-reader-lineage-unavailable` | abstain `correction-family-lineage-unresolved` | D13-A exposes the retained unresolved correction-family mapping in a correct complete-correction case. |
| E13 N9 `ab70cdb37bb2977d725c` | abstain `authorized-reader-lineage-unavailable` | abstain `unresolved-decision-threshold` | D13-A exposes the retained pre-registered `0.01` narrowing. |

The exact movement-set assertion is:

```text
changed_case_ids == {
  "80091f37c722eba28e18",
  "d0f9fcd52f47e4d64668",
  "b7d38f6e9284abfd3ee6",
  "ab70cdb37bb2977d725c",
}
len(changed_case_ids) == 4
```

P2 remains `extra-registered-test-outside-authorized-family`. P6 remains an abstention at its
recon-pinned residual, although its first reason necessarily changes after D13-A. Every other
opened E10-E13 adapter row is byte-identical to explicit frozen-2.2 replay. This four-row count is
the executed combined prototype result in `sweep_results.json`; treating only candidate changes as
movements is forbidden.

The eligible-site population is structurally closed and separately asserted. Exactly five opened
cases contain a function-local path binding consumed by a recognized reader, all in E13:

```text
P2 c336be2521785ab6a954  # held at the earlier >N call-census wall
P5 80091f37c722eba28e18  # reader wall -> candidate strict_subset
P6 d0f9fcd52f47e4d64668  # reader wall -> manual-correction wall
N1 b7d38f6e9284abfd3ee6  # reader wall -> correction-lineage wall
N9 ab70cdb37bb2977d725c  # reader wall -> threshold wall
```

E10, E11, and E12 contain zero such function-local eligible sites; their module-level path
bindings are already resolved by 2.2 and do not enter D13-A. This five-site census explains the
movement set structurally: four rows move, while P2 cannot reach reader resolution because the
retained `performed_count > N` census fires first. P2's non-movement is contingent on that exact
guard and is reserved for the separate duplicate-pass evidence/wording ADR in sections 8.1/12.1.

### 9.3 Open corpus — all fifty rows frozen

The committed open corpus remains 50 cases, 25 labeled correct and 25 labeled misstep:

```text
root                evaluation/development/multitest-open-corpus-v1/
labels raw bytes    sha256:f9d2d33ba3b8247b0d0d65e5f72f765af02bfca6dc932f895010d79129f36f80
analysis source set sha256:7888b72a6ac1ec70830d4041517a977b8ea8ff6c4294a7d13a734ab9af377a2e
2.1 replay bytes    sha256:7c37669c8ccfdb0b754aa03ee1dbcee1dac78fa4bb44105e17c5d1886aaed502
2.2 result rows     sha256:80e000e923d23133a9c93433b023a871ee4fe095aeffadc9b970ae803c3d8a55
```

At adapter level, every 2.3 per-case result row is byte-identical to the explicit frozen-2.2
comparison row and therefore to the corresponding frozen 2.1 result. The wrapper adapter identity
is not compared across versions. Neither `adapter_replay_records_v2_1.json` nor the frozen 2.2
comparison rows is regenerated or rewritten.

Required score:

```text
labeled correct candidates:  0 / 25 (hard stop)
labeled misstep candidates: 19 / 25 (unchanged)
```

### 9.4 Historical opened and recognizer oracles

- All 45 E10/E11/E12 adapter rows retain their exact 2.2 outcomes, classifications, positions,
  and first reasons, including E10 N7's adapter-only outside-file statistics reason and E12's
  exactly-three 2.1-to-2.2 movements.
- The twelve PROBE baselines and `NEGSIM_C` remain candidate/`none`; `PROBE_roundp`, `NEGSIM_A`,
  and `NEGSIM_B` retain their exact reasons.
- E10 P2/P3 mutation ladders, all corpus20 and E12 ladders, the 32 2.0 adversaries, every 2.1
  admission/refusal fixture, all 2.2 D2/D3/D5/D6 matrices and FA fixtures, and all historical
  contract/detector guards retain their exact outcomes.
- The five prior frozen-version anchors remain green. Tests keep explicit old-version imports and
  are copied for 2.3 rather than retargeted.

No existing correct analysis moves to candidate. E13 N1/N9 move only to named deeper abstentions;
the five new local-path refusal fixtures remain abstentions; and the two complete-correction
fixtures are covered/complete.

## 10. Executed none-flip guarantee

The recon executed baseline, D13-A, D13-B, and D13-A+B. The combined prototype produced:

```text
open-corpus labeled correct: 0 candidates / 25 executed
opened negatives E10-E13:   0 candidates / 36 executed
six 2.2 FA fixtures:         0 candidates / 6 executed
```

Each D13 proposal independently also produced `0/25`, `0/36`, and `0/6`. The build gate reruns
the **combined final 2.3 implementation through the real adapter**, not only an analyzer-equivalent
harness, over the same 67 inputs. Exact requirements are:

```text
candidate_ids(corpus_correct) == empty
candidate_ids(opened_negatives_E10_E13) == empty
candidate_ids(six_FA_fixtures) == empty
```

The six FA outcomes remain exact:

```text
FA-2   abstain unresolved-manual-correction-present
FA-3   covered complete
FA-3b  abstain unresolved-manual-correction-present
FA-5   abstain analysis-scope-structure-unsupported
FA-5b  covered complete
FA-6   abstain unresolved-pvalue-consumer
```

Reason movement for E13 N1/N9 is permitted only as pinned in 9.2. Zero candidates is necessary but
not sufficient: all exact oracle rows, movement-set equality, corrected positions, and complete
coverage assertions must also pass.

## 11. Recon ladders and prototype obligations

### 11.1 Executed ladder rungs

All twelve executed E13 rungs remain checked in under
`evaluation/development/multitest-recall-recon-e13/` and are copied or referenced by immutable
digest in the 2.3 regression matrix. Execute and pin:

- P2: real duplicate pass -> one-family-pass reader wall -> direct-reader candidate control;
- P5: real reader wall -> direct-reader terminal wall -> direct-verdict `strict_subset {0,1}/7`;
  and
- P6: real reader wall -> direct-reader manual wall -> List-to-Set -> membership-only Set ->
  literal subset size -> full-family-factor candidate control.

Every rung test invokes the public analyzer or adapter. Fixture-shaped private assertions do not
replace execution. The P2/P6 final rungs are controls, not admissions: deleting a test pass or
changing the scientific correction factor is not behavior implemented by 2.3.

### 11.2 Prototype-versus-final condition

The runnable recon prototype is pinned:

```text
prototypes.py sha256:429061ba9ba5eb16224aebc0dccab40a0033a4dff43fc8aa5d51fce40bf92154
sweep.py      sha256:92bfe3f23bfdac08b6063b09825cabd904abd334c5253839d17d5380da33c9fd
```

The prototype rewrites source for measurement and monkeypatches engine methods; neither mechanism
is production design. Equivalence is therefore extensional over the frozen evidence domain, not a
claim that implementation strategy is equal. The final 2.3 implementation must equal D13-A+B on:

- all twelve ladder rungs;
- all 50 corpus cases;
- all 60 opened E10-E13 cases;
- the six 2.2 FA fixtures; and
- the four targeted E13 correct-analysis attacks.

The final implementation is intentionally stricter than the prototype in both delta components:

- D13-A's alias/mutation/conditional/path refusal matrix lies outside the prototype's demonstrated
  positive domain; and
- D13-B's executed prototype used a materially weaker position-only `any()` sink matcher with no
  `STRUCT`, `FAMILY_POS`, or cardinality bound, whereas the final design requires joint composite
  matching and one-to-one per-position clones.

The none-flip direction transfers soundly: tightening an admission cannot create a candidate the
looser prototype did not create. The positive D13-B claim does **not** transfer. Before section
9.1 is satisfied, the final strict matcher must re-demonstrate P5 as candidate `strict_subset`,
positions `{0,1}/7`, through the real adapter and must pass
`positive-terminal-clone-N-position-fanout`. P5 is the row protected by the exact movement-equality
gate. A final candidate where the prototype was a noncandidate is a stop; a final P5 abstention is
also a stop. Only after that demonstration may final/prototype be said to have the same four opened
movements and zero corpus movements.

## 12. Residuals

### 12.1 Exact `2N` duplicate-call census

P2 remains `extra-registered-test-outside-authorized-family`. Its two complete registered passes
are real executions with two decision surfaces, not cloned presentation. The exact call-count
guard remains the protecting rule and no evidence/wording policy is changed. See 8.1.

### 12.2 Proper-subset manual factor

P6 remains `unresolved-manual-correction-present` after D13-A exposes the deeper wall. The factor
three is not the authorized family size five. Recognition requires a future correction-policy ADR;
no manual grammar changes here. See 8.2.

### 12.3 DataFrame p-table value model

Any family p-value entering a pandas DataFrame remains `unresolved-pvalue-consumer`. A future model
must prove columns, position, row order, mutation, filtering, assignment, iteration, and export
semantics before any accusation.

### 12.4 Positional-record subset and dominated flag fold

A runtime-filtered positional record list cannot establish contract positions. The dominated
record-flag fold remains bundled with that missing model. D13-B cannot turn cloned rendering into
record identity.

### 12.5 Zip write-back dual polarity

Zip write-back occurs in both complete-correction and partial-correction analyses. It remains
unresolved until one reviewed model proves both polarities without manufacturing strict-subset
positions.

## 13. Executable validation plan

Every fixture executes the public 2.3 analyzer or adapter. AST/private-helper assertions supplement
but never replace public-path execution.

### 13.1 D13-A grammar matrix

Cross and pin:

- direct literal and module-constant `CONST` for both exact os.path and pathlib productions;
- imported spellings and unambiguous import aliases resolving to the exact APIs;
- Assign and unchanged closed AnnAssign; direct read assignment and direct reader Return;
- exact authority match versus safe-but-different, unsafe, absolute, empty, dot, dot-dot, and
  multi-component paths;
- every excluded path near miss: missing/extra call argument, keyword, different dirname/abspath
  nesting, `.joinpath`, `.parents`, `cwd`, string addition, f-string, format, environment, CLI,
  helper, parameter, subscript, and conditional expression;
- mutation by Assign/AnnAssign/AugAssign/NamedExpr/Del, attribute/subscript/slice store, every
  receiver call, alias in either direction, container insertion, second reader, call argument,
  return/yield/closure/default/format/compare load, and cross-function flow;
- binding under every conditional/lazy/control owner and a reassignment after the reader;
- unchanged direct-path readers and unchanged refused `csv.DictReader`; and
- all seven named section-6.1 fixtures, including covered/complete.

Assert the value query is identical at the full reader census, operand-reader census, authorized
data-name closure, and engine root. A test deliberately replacing only one query must fail the
consistency gate.

### 13.2 D13-B matrix, ordering, and idempotence

Run both eligible productions through each 2.2 normalization site that can clone them. Cross:

- one exact clone, zero clone, two competing descriptors for one clone, two sinks, same
  source/different structure, same structure/different source, unresolved family position, and
  missing end positions;
- equal-key origin occurrences remain two records rather than being deduplicated before the
  competition check;
- the admitted P5 fanout control: one helper, `N` descriptors sharing source/structure, `N`
  distinct singleton positions, and `N` jointly matched one-to-one clone pairs;
- original/clone unrecognized calls, stores, aliases, containers, exports, second emissions, and
  control consumers;
- every installed terminal-helper production and every frozen refusal shape;
- exact raw, complete correction, strict-subset correction, computed threshold, conventional bare
  threshold, and pre-registered `0.01` threshold;
- R1 percent rendering with direct and container-derived p origins; and
- all eight named section-6.2 fixtures.

Assert the off-grammar, hierarchy, and conclusion registries receive the same map object and same
composite entry: off-grammar uses its transport field, while hierarchy and conclusion use its
decision field. Independently run the D6 ordering and all three idempotence equalities in 5.4. Confirm D2
occurrence keys, D5 membership positions, source spans, consumer sets, and evidence bytes are
unchanged.

### 13.3 E13 adapter replay and exact movements

1. Execute all fifteen E13 projects through the real 2.3 adapter and exact committed profiles.
2. Compare every row with section 9.1, including positions `{0,1}/7` for P5, and independently
   assert that P5's correction method resolves from `ADJUST_METHOD` to exact `holm`.
3. Execute explicit frozen 2.2 and 2.3 adapters through the same harness.
4. Assert the opened eligible-site census is exactly the five E13 cases in section 9.2, zero for
   E10-E12, and that P2 stops at the retained `>N` census before reader resolution.
5. Assert the canonical changed-case set and length equal section 9.2 exactly.
6. Write one canonical 2.3 replay record, execute twice, and assert byte equality.
7. Assert sealed custody, source, audit, role-map, profile, and blind-score bytes are untouched.

An analyzer-level table may be retained as a diagnostic but cannot replace this adapter gate.

### 13.4 None-flip, corpus, and historical replay gates

- Execute the combined 67-case none-flip gate in section 10 at adapter level.
- Execute all 50 corpus cases with explicit 2.1, 2.2, and 2.3 adapters. Pin the raw 2.1 record, the
  canonical 2.2-row digest, byte-equal 2.3 rows, `0/25` correct, and `19/25` misstep candidates.
- Execute all 45 E10-E12 adapter rows and compare exact frozen 2.2 rows.
- Execute the E13 baseline through explicit frozen 2.2 and compare sealed results before applying
  the four 2.3 movements.
- Execute every PROBE/NEGSIM, historical ladder, and adversary named in 9.4.
- Import and replay all historical adapters explicitly; never obtain a frozen baseline through the
  active development binding.

### 13.5 Prose tripwire and structural controls

Extend the 2.2 tripwire over every D13-A/B predicate, ladder rung, FA fixture, and oracle source.
Independently mutate comments, docstrings, reports, Markdown, task text, annotations, unrelated
strings, display labels, format strings, and non-callee identifiers; add/remove report and Markdown
files; rename non-callee identifiers through `bonferroni`, `holm`, `sidak`, and
`benjamini_hochberg`. Facts, reason, classification, positions, and evidence bytes remain equal.

Specific boundaries:

- D13-A reads AST shape, resolved API identities, binding/Load/Store relations, safe path bytes,
  and exact equality with the contract path. It never reads comments, variable semantics, report
  claims, or filenames outside structural `CONST` resolution.
- D13-B reads node kinds/fields, source positions, existing provenance markers, singleton family
  positions, sink identity, and consumer edges. Presentation strings are measured only for the
  unchanged nonempty/NUL/256-byte bounds. Their bytes may participate in exact origin/clone
  structural equality, but are never tokenized, matched to vocabulary, interpreted, compared for
  scientific meaning, or emitted as evidence.

Paired positive controls each change one structural slot: exact local RHS -> dynamic component;
one binding -> reassignment; sole reader Load -> alias; unconditional -> conditional binding;
authorized -> different path; exact clone position -> different position; singleton -> duplicate
sink; marked -> unmarked IfExp; same -> different family position; total -> exported consumer; 256
-> 257 display bytes. Each must change its named predicate. Deleting the recognized reader/test
callee or contract path/outcome literal from a positive control changes the result.

### 13.6 Closed set, differential, and repository gates

- Public 2.3 emitters plus the documented-unreachable annex are set-equal to section 7.3; every
  non-X4 reason has an exact public fixture and X4 reasons retain the parametrized module.
- Explicit frozen 1.0/1.1/2.0/2.1/2.2 anchors execute; no old test is retargeted.
- Dual-registry differential proves qualified GrantPins, grants, qualifications, metric sets,
  threshold references, and Findings are byte-equal and do not derive from the development
  lane-inclusive digest.
- Contract `1.0.0`/`1.1.0` goldens, all seven error categories, deterministic corpus/source
  censuses, registry digests, and frozen replay records remain exact.
- Registry resources and capability ledger are regenerated after the final source/test/artifact
  change. `MANIFEST.sha256` follows the repository custodian's committed-tree procedure.
- Run fresh `ruff check .`, `ruff format --check .`, `mypy src`, `pytest`, and
  `python scripts/validate_starter.py`; report exact unfiltered outputs and never claim a change
  absent from the diff.

## 14. Evidence projection and candidate meaning

Facts, observation schemas, canonical operands, evidence roles, and wording slots are unchanged.
D13-A evidence cites the original reader call and exact path binding span only as authorized-reader
lineage; the assignment is not a read operation or a frame. D13-B evidence cites the original
terminal helper/rendering and registered sink spans already used by 2.2, preserving the existing
p origin and family position. Analyzer clone keys and display text are not evidence.

A 2.3 candidate still asserts only that the authorized complete family has exactly `N` proved
registered tests and raw conclusions outside complete recognized correction coverage. Absence of a
recognized correction in analyzed source does not establish that no correction was applied. The
detector does not infer correction, preregistration, importance, or meaning from names, paths,
reports, labels, display strings, or prose.

P5's candidate is permissible only because the unchanged global census proves exactly seven
registered calls, the backward slices prove authorized complete rows for all seven positions, the
recognized Holm call covers exactly `{0,1}`, total forward accounting proves raw conclusions for
the other five, and D13-B maps only already-recognized terminal transport. D13-A/B alone cannot
support the accusation.

## 15. Honest read and envelope 14 posture

The honest development expectations are:

```text
open corpus correct:       0 / 25 candidates (hard gate)
open corpus misstep:      19 / 25 candidates (unchanged)
E13 sealed first contact:  3 / 6 positives (immutable)
E13 retrospective 2.3:    4 / 6 positives
opened E10-E13 floor:     18 / 24 positives
blind first contact:       5 / 24 positives (E10-E13; immutable)
opened negatives:          0 candidates / 36 (hard gate)
```

The delta moves zero of 50 open-corpus rows. Byte identity remains the corpus gate; there is no
claim of improved unbiased-corpus recall. Retrospectively, D13-A+B catches one additional E13
positive, moving the answer-visible score from `3/6` to `4/6`; blind credit remains the sealed
`3/6`.

The arrival prior remains conservative. One new reader-path idiom caused two positive misses and
three negative first walls, yet clearing it catches only P5 because P6 immediately reaches a
deliberate policy boundary. The planning expectation for E14 is around the current `3/6`, with
high uncertainty—not the answer-visible E13 ceiling and not a pass prediction. Under the running
E12-E14 window, the sealed E12 `2/6` plus E13 `3/6` leaves E14 needing at least `4/6` to reach
`9/18`; fresh first contact must be reported regardless.

Data generators remain outside the audited project tree. Briefings do not reveal admissions,
guards, prior idioms, or ways to avoid assumption checks. Replay equality, zero negative
candidates, zero Findings, and the available/latest-36 class FA window remain hard stops;
first-contact recall is reported only.

## 16. Reuse map and file-by-file build list

Versioned-copy discipline from the 2.0-2.2 designs governs. Shared historical modules are copied,
never edited.

| File/surface | Required 2.3 change |
|---|---|
| This design | Frozen build specification; no behavior edits during build without reviewed revision. |
| `ADR-0079-MULTIPLE-TESTING-CODE-SLICE-2.0-INVERSION.md` | Append the reviewed 2.3 note from 2.4 and sections 8/9; do not rewrite prior decisions. |
| New `src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v2_3.py` | Versioned copy of frozen v2_2 implementing only D13-A and D13-B at the exact pipeline placements. No dependence/private-version import. |
| New `src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v2_3.py` | Version `2.3.0`; unchanged contract/evidence projection and exact closed reason set. |
| New `src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v2_3.py` | Versioned detector/check wrapper and unchanged operand/ValueError guards. |
| New `src/sc_referee/scientific_checks/integration_multiple_testing_v2_3.py` | Development-only identities and integration. |
| `scientific_checks/profiles.py` | Retain all historical implementation files; register 2.3 and advance only the active development binding. |
| `detectors/method_conflict_registry.py`, `method_conflict_finding.py`, development controller/resources | Register/dispatch 2.3 beside historical versions; reuse wording v1 only for the exact development binding; no qualified permission. |
| New `_v2_3` test modules | Copy 2.2 test families, retain explicit old imports, and add sections 6/10/11/13. Do not retarget old tests. |
| `evaluation/development/multitest-code-slice-v2_3/` | Add D13-A/B matrices, named FA sources, copied/pinned E13 ladders, canonical manifest, and development ledger. |
| `evaluation/development/blind-envelope-13-2026-08-26/` replay surface | Add only a 2.3 adapter replay record/oracle; custody/source/audit/role-map bytes remain untouched. |
| `multitest-open-corpus-v1` replay harness | Add an explicit 2.3 adapter execution path comparing to frozen 2.2 rows; do not rewrite `adapter_replay_records_v2_1.json`. |
| New 2.3 oracle/replay tests | E13 15-row table, exact four-row movement set, 67-case none-flip, 50-row equality, E10-E12, PROBE/NEGSIM/ladders/adversaries, and explicit frozen 2.2 anchor. |
| Registry resources, capability ledger, source inventories, release manifest | Regenerate in repository-prescribed order after final implementation/test/artifact changes; custodian refreshes committed-tree manifest as required. |

No-edit surfaces are the qualified lane, GrantPins, wording profiles, contract, historical MT
modules/tests/replay bytes, dependence modules, and E10-E13 custody/audit/source records.

## 17. Build acceptance and stop-and-report conditions

Build acceptance requires all of:

1. exact D13-A site, RHS, immutability, alias, escape, authority-equality, and cross-query grammar;
2. exact D13-B source-position/structure/family-position key, permitted same-source distinct-
   position fanout, jointly matched one-to-one clone pairs, and total origin/clone consumer
   accounting;
3. one shared D13-B composite map used consistently by off-grammar, hierarchy, and conclusion
   registries, with transport/decision containment checked once;
4. unchanged D6 grammar and second-pass equality, followed by D13-B no-mutation and idempotence;
5. every section-6 named fixture, including both covered/complete controls and exact refusal
   reasons;
6. exact fifteen-row E13 adapter oracle and exactly four changed rows relative to explicit frozen
   2.2;
7. the combined adapter-level none-flip gate `0/25`, `0/36`, `0/6`;
8. byte-identical 50-row corpus results, `0/25` correct and `19/25` misstep candidates, without
   regenerating the frozen 2.1 record or changing the frozen 2.2 comparison rows;
9. unchanged E10-E12, PROBE/NEGSIM, ladder, adversary, and historical oracles;
10. checked-in E13 ladders and extensional prototype-final equality on the frozen evidence domain;
11. effective prose tripwire and paired structural controls;
12. closed-reason set equality with no synthetic reachability;
13. explicit frozen 2.2 replay and qualified-lane differential; and
14. fresh repository-required lint, format, type, full-test, and starter-validation gates after
    final registry/ledger/artifact generation.

If any correct-case hard gate, adapter oracle, movement-set equality, D13-A stability/authority
proof, D13-B unique mapping/total accounting/shared-map proof, D6/D13-B idempotence, frozen replay,
reason-set equality, or qualified differential cannot pass as written, implementation stops and
reports a design regression. It must not broaden a path or terminal grammar, weaken a census or
consumer guard, skip P6's manual arithmetic, collapse P2's calls, relabel a surviving reason,
reinterpret prose, rewrite a frozen record, or adapt an oracle.

## 18. Revision log

### Revision 0 — commissioned design

Revision 0 adopts only D13-A and D13-B from the executed E13 recon. It records P2 and P6 as bin-C
residuals, preserves every deferred 2.2 model, pins the frozen 2.2 surfaces, and makes the exact
four-row opened movement set executable. No change weakens a surviving guard or broadens correction,
threshold, reader-API, row-completeness, evidence, or wording policy.

| Commission item | Sections | Revision 0 disposition |
|---|---|---|
| D13-A | 3, 4, 6.1, 7, 13.1 | Adds one exact immutable local reader-path value edge with closed os.path/pathlib forms and module-wide mutation/alias/escape refusal. |
| D13-B | 3, 5, 6.2, 7, 13.2 | Adds zero grammar; closes one terminal clone by source position, full structure, family position, and total consumers through one shared map. |
| P2/P6 residuals | 1, 8, 12, 17 | Keeps exact call-count and full-family manual-correction guards; records future ADR requirements. |
| Frozen surfaces | 2.3, 9.3-9.4, 13.4, 16 | Freezes 2.2 modules/replays/comparison rows and all prior oracles; advances only the development binding. |
| E13 oracle and movements | 9.1-9.2, 13.3, 17 | Pins all fifteen adapter rows and the exact four-case movement set `{P5,P6,N1,N9}`. |
| None-flip guarantee | 6, 10, 13.4, 17 | Elevates executed combined counts `0/25`, `0/36`, `0/6` to a real-adapter build gate. |
| Honest read | 15 | Records E13 retrospective `3/6 -> 4/6`, zero corpus movement, and conservative E14 arrival economics. |

### Revision 1a — adversarial design review

Revision 1a folds one blocker, one major, and three minors. It preserves the fifteen-row E13
oracle, exact four-row movement count, combined none-flip totals, closed reason set, and every
correction/threshold/census guard. The D13-B fixture matrix now has eight named fixtures because
the missing P5-shaped positive fanout control is explicit.

| Review finding | Sections changed | Revision 1a disposition |
|---|---|---|
| `BL-1` same-source family fanout | 5.2, 6.2, 13.2, 17 | Allows multiple descriptors to share source/structure only when each has a distinct singleton family position and its own jointly matched clone pair; confines family-position refusal to unresolved singleton position or actual clone competition; rewrites the collision fixture and adds the mandatory `N`-position P5 positive control. |
| `MJ-1` weak prototype transfer | 11.2, 13.2-13.3, 17 | Records the prototype's position-only `any()` matcher, permits none-flip transfer only in the safe tightening direction, and requires the final strict matcher to re-demonstrate P5 before the oracle is satisfied. |
| `m1` eligible-site population | 9.2, 13.3 | Pins exactly five function-local recognized-reader sites, all E13, zero in E10-E12; P2's non-movement remains contingent on the retained `>N` census and separate ADR. |
| `m2` composite matching granularity | 5.1-5.3, 13.2, 17 | Requires transport and decision clones to match jointly in one composite entry with containment checked once, never independently reconciled. |
| `m3` P5 correction-method dependency | 9.1, 13.3 | Pins closed module-constant resolution of `ADJUST_METHOD = "holm"` as a prerequisite for P5 coverage `{0,1}`. |
