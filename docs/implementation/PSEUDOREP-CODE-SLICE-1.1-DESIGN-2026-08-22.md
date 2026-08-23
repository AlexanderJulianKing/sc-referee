# Pseudoreplication code slice 1.1 delta design — 2026-08-22

- **Status:** Accepted for build, with D1-D10 review edits
- **Decision provenance:** Fable, under executive authority granted by Alex 2026-08-21
- **Normative base:**
  `docs/implementation/PSEUDOREP-CODE-SLICE-DESIGN-2026-08-22.md` (code slice 1.0)
- **Governing ADR:**
  `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md`,
  requiring a 1.1 amendment before implementation
- **Delta version:** code/CSV recognition grammar and adapter `1.1.0`
- **Authority profile:** existing `scientific_check_requirement_v1` `1.1.0`, unchanged
- **Evidence channels:** code structure, CSV structure, frozen contract records, and established API
  identities only; prose remains forbidden
- **Project-authored-code execution:** forbidden

## 1. Delta boundary

This document changes exactly four recognition surfaces from code slice 1.0: X1 module setup and three
closed `__file__` path forms; X2 the registered test statistic as a legal result consumer; X3 assigned
straight-line descriptives; and X4 bounded helper inlining. It does not replace or restate the 1.0
contract, CSV/D1' predicate, reader/selection/aggregation/test/dependence API tables, alternate-analysis
scan, source bounds, 16-definition ceilings, typed fact, conflict predicate, bounded Finding wording,
zero-false-accusation rule, or pre-qualification Finding ceiling. Those provisions are incorporated by
reference and remain byte-for-byte normative except where an X1–X4 rule below expressly overrides one
sentence.

No report, Markdown, comment, docstring, printed label, exception message, identifier meaning, or other
prose is evidence or counterevidence. The 1.0 prose tripwire remains mandatory. Nothing in this delta
authorizes a fifth grammar extension, a new reader, a new selector, a new positive test API, execution,
or a production pin.

### 1.1 BUILD-NOTES

- The implementation takes D2 literally: a direct arithmetic expression is not a tracked descriptive
  `NAME`. Consequently Envelope-2 P2 `2df3396d80adbb63dffb` abstains at line 63, where
  `str.format` consumes `n_total - 2`; the exact reason is
  `unregistered-component-call-reaches-output`. Treating that expression as a NAME would widen the
  closed terminal grammar, so the builder did not preserve the earlier inferred Candidate expectation.
- Helper relevance is conservatively over-approximated when a nonconstant actual is present. A helper
  thereby selected must pass the full closed eligibility grammar; this can add abstentions but cannot
  add candidates.
- A returned local `Name` is admitted syntactically and then must resolve as tracked in the expanded
  dataflow. An untracked return cannot create a candidate. This is the narrower implementable reading of
  section 6.2's “tracked Name.”
- Code slice 1.1 is implemented in a new detector module. The code-lane 1.0.0 detector file, generic
  detector, complete-domain pin, and production grant table are not edited.
- The normal-path subject-selection gate in `scientific_checks/integration.py` is mechanically advanced
  from check 1.3.0 to 1.3.1. Without that version-only edit an applicable code observation is attached to
  a selected report surface when one happens to be present, producing an unresolved file reference;
  the edit adds no evidence form and restores the code fact's existing `method_target_ref`.
- The method-conflict dispatcher groups only bindings targeted by answered material questions before it
  requires detector manifests. This preserves validation against the complete locked binding table while
  preventing an untargeted code-lane binding from making an unrelated generic-detector case unsupported;
  it cannot schedule an additional question or candidate.
- Generic-detector matrix tests use the existing validation-only binding projection for the dependence
  check declared in the byte-frozen generic manifest. The live dependence binding remains exclusive to
  the code-lane detector and the projection grants no scheduling or Finding authority.
- The private capability-maturity ledger and regression ledger/plan are regenerated for the check 1.3.1
  content identity. The retained regression cases, labels, Finding ceilings, and expected outcomes do not
  change.

## 2. Observed basis: Envelope 2 burned cleanly

### 2.1 Observed

Envelope 2 produced 0/3 positive recognitions, 0/5 negative convictions, zero Findings, replay equality
8/8, closure equality 64/64, and label/role agreement 8/8. It is burned and contributes no blind credit
(`evaluation/development/blind-envelope-2-2026-08-22/CUSTODY_LOG.md:105-106`;
`evaluation/development/blind-envelope-2-2026-08-22/AUDIT_RESULTS.json:1-16`).

All eight opened scripts use an exact `main` guard. Seven construct the input path from `__file__`; for
example, the three positive forms are a nested `os.path` expression
(`evaluation/development/blind-envelope-2-2026-08-22/cases/e8f97fe750189052f726/project/analysis.py:15`),
the same expression inside a loader
(`evaluation/development/blind-envelope-2-2026-08-22/cases/2df3396d80adbb63dffb/project/analysis.py:20-23`),
and `Path(__file__).resolve().parent / LITERAL`
(`evaluation/development/blind-envelope-2-2026-08-22/cases/ca18f96d45dff1b921ad/project/analysis.py:16`).
Two scripts put the accepted reader in a `load_data`/`load_wells` helper. Across the fourteen opened
scripts from both burned envelopes, the observed organization is four flat scripts, three `main`
scripts without dataflow helpers, and seven `main` scripts with helpers.

### 2.2 Custodian diagnosis, accepted as development evidence but not independently re-executed here

The independent scratch diagnosis says that, after manually removing the scope/path/helper blockers,
all three Envelope 2 positives reach the existing candidate predicate and all five negatives still stop
on code/CSV guards: operand-path aggregation, no repeated unit, a second reader/summary lineage,
`mixedlm`, or an off-registry cluster bootstrap reaching output. That is evidence for trying X1–X4; it
is not evidence that every opened script satisfies the narrower X4 authorized below. Section 8 traces
the literal delta rather than granting the scratch copies qualification credit.

## 3. X1 — module setup screen and exact `__file__` paths

X1 replaces only 1.0 sections 4.3 and 5.2 where they reject non-`Constant` module setup and every
`__file__` expression.

### 3.1 Deterministic module setup screen

For a selected exact `main` plus exact main guard, process the module body in this order:

1. Remove only AST docstring statements. Their bytes and text are not inspected.
2. Require exactly the 1.0 `main` and main-guard forms. The `main` signature rules do not change.
3. Build a top-level lexical binding table without evaluating Python. A binding is one source-ordered
   `Name = EXPR` assignment, an accepted import, or a module-level synchronous `FunctionDef`.
   Rebinding, deletion, an attribute/subscript target, `AnnAssign`, `AugAssign`, walrus, destructuring,
   star target, dynamic import, `global`, or `nonlocal` retains its 1.0 abstention.
4. Seed `scope_loaded_names` with every `Load` name in `main`. Add names loaded by each X4 helper that is
   selected by the relevance fixed point in section 6.1. Follow top-level assignment dependencies until
   no new name is added. Cycles abstain `analysis-scope-ambiguous`.
5. Admit as `module_setup` only:
   - the existing accepted imports plus exact `import os [as NAME]` and `import os.path`;
   - a one-name assignment to one literal `Constant`;
   - a one-name assignment to a tuple of 1 through 16 literal `Constant` values, with no star or nested
     element; the tuple is a structural constant only and supplies no group-domain evidence;
   - an exact file-parent or final path expression from section 3.2; and
   - module-level helper definitions considered under X4.
6. Ignore a one-name assignment outside `scope_loaded_names` only if its right-hand side consists solely
   of literal `Constant`, `Tuple`, `List`, `Set`, `Dict`, unary arithmetic, or binary arithmetic nodes,
   contains no `Call`, `Attribute`, `Subscript`, comprehension, lambda, named expression, await, or
   yield, and every loaded name resolves transitively to another such ignored assignment. It enters no
   resolver table, fact, counterevidence scan, or digest projection.
7. Any other module-level statement outside the exact imports, setup assignments, helper definitions,
   `main`, and main guard remains `unsupported:analysis-scope-ambiguous`, even if a human believes it is
   harmless.

Names such as `HERE`, `BASE_DIR`, `GROUPS`, or `DATA_FILE` have no special status. Only their exact AST
forms and def-use positions matter. This screen admits the opened `GROUPS = ("restored",
"channelised")` tuple and structural path bindings without interpreting their wording
(`evaluation/development/blind-envelope-2-2026-08-22/cases/6090fc1b1b6dbfcd6eee/project/analysis.py:21-26`).

### 3.2 Closed file-parent path evaluator

Add one symbolic token, `PROJECT_FILE_PARENT`, derived only from one of these exact AST forms after
normal import resolution:

```text
os.path.dirname(os.path.abspath(__file__))
pathlib.Path(__file__).resolve().parent
pathlib.Path(__file__).parent
```

The first form requires exact `import os [as NAME]` resolution. The latter two require either existing
accepted pathlib import form. `__file__` is the exact `Name` node; any assignment, parameter, import,
deletion, or other binding of `__file__` abstains `api-resolution-ambiguous`.

An authorized reader path may then resolve by exactly one of:

```text
os.path.join(os.path.dirname(os.path.abspath(__file__)), PATH_LITERAL)
BASE = os.path.dirname(os.path.abspath(__file__))
os.path.join(BASE, PATH_LITERAL)

pathlib.Path(__file__).resolve().parent / PATH_LITERAL
BASE = pathlib.Path(__file__).resolve().parent
BASE / PATH_LITERAL

pathlib.Path(__file__).parent / PATH_LITERAL
BASE = pathlib.Path(__file__).parent
BASE / PATH_LITERAL
```

`PATH_LITERAL` is either one literal string or one name bound by the 1.0 `FINAL_NAME` rule to a closed
module string `Constant`; its resolved bytes independently satisfy the 1.0 safe-path grammar. There is
exactly zero or one `BASE` alias hop, `BASE` is single-assignment, and no other use may redefine it.
The symbolic prefix is discarded and the evaluator returns the bytes of `PATH_LITERAL` as the
project-relative path. Those bytes must still equal the contract `material_input_path`; there is no
basename, case-fold, filesystem, `resolve`, normalization, existence, or suffix fallback. The analyzer
does not call any path API.

This evaluator applies only when the whole reader-path expression is exactly one displayed form; it
does not use prefix containment and does not accept a registered form embedded inside a larger path
expression. It applies inside the selected body and an X4-expanded helper as well as module setup. It
does not extend writer-path forms. `os.getcwd`, environment/argument inputs, string concatenation,
f-strings, `.absolute()`, chained `.parent.parent`, nested `os.path.dirname`, `.parents[...]`,
`.joinpath(...)`, multiple or extra path components, more than one base alias, or any other computed
reader path remains
`unsupported:authorized-reader-lineage-unavailable`.

## 4. X2 — test statistic is a legal result consumer only

X2 changes only 1.0 section 5.7's result-payload root. For an accepted
`scipy.stats.ttest_ind` call, the first result element is accepted by the sink tracer in the same
positions already accepted for the p-result:

```text
STAT, P = scipy.stats.ttest_ind(...)
STAT

RESULT = scipy.stats.ttest_ind(...)
RESULT.statistic
RESULT[0]
```

The statistic may traverse exactly the existing p-payload identity aliases and wrappers: `str`,
`float`, `round` with an optional integer literal, one formatted field in an f-string, or the one-argument
`.format` form. Thus `print(f"t = {STAT:.3f}")` is a legal result consumer and does not itself cause
abstention. It does **not** satisfy predicate step 20: that step remains satisfiable only by an accepted
p-result sink. No arithmetic,
comparison, conditional formatting, helper call, logger, serializer, unknown attribute, or other result
element is added.

This is a consumer-legality rule only. It does not assert that the statistic was selected, claimed,
scientifically primary, correct, or executed; it does not add an inferential value to the Finding. The
fact field, Finding wording, and semantic-role target `registered_test_p_result_output_sink` remain
unchanged. `mannwhitneyu` statistic-only output remains outside this delta.

## 5. X3 — assigned straight-line descriptives

X3 replaces the source-order and direct-to-print restriction in the 1.0
`descriptive_output_call` paragraph. A fresh one-name assignment is `descriptive_scalar` exactly when
its right-hand side is one of the existing descriptive-loop reductions:

```text
NAME = V.mean()
NAME = V.std()
NAME = V.std(ddof=1)
NAME = V.median()
NAME = V.min()
NAME = V.max()
NAME = V.count()
NAME = V.sum()
NAME = len(V)
NAME = sum(V)
NAME = min(V)
NAME = max(V)
NAME = round(REDUCTION)
NAME = round(REDUCTION, INTEGER_LITERAL)
```

`V` is one tracked selection/identity Series or array. Builtins must be unshadowed. Method argument and
keyword rules are exactly the 1.0 descriptive-loop rules. `REDUCTION` is one of the preceding method or
builtin reductions written directly in the `round` call. No other method, NumPy reducer, group reducer,
attribute, property, cast, indexing operation, or function is added.

The assignment may occur before or after the candidate test and need not be syntactically inside a
print. Its target is single-assignment and is not itself a tracked frame/operand. Acyclic descendants may
use only numeric literal constants, identity aliases, unary `+`/`-`, and binary `+`, `-`, `*`, `/`, `//`,
`%`, or `**`; they may terminate only in an existing accepted print/format/f-string payload or remain
unused. A descriptive scalar or descendant passed to any other call, used as a receiver, stored into a
container, or used in control flow abstains `unrecognized-call-on-path` or
`unsupported-expression-on-path` under the existing ordered rule.

One terminal exception is exact `STRING.format(ARG, ...)` flowing exclusively into builtin `print`.
It accepts any number of positional arguments only when every argument is (a) a tracked
`descriptive_scalar` name or allowed descendant, (b) a literal `Constant`, or (c) a closed module tuple
element/group-label constant admitted by section 3.1. Keywords, starred arguments, a nonliteral format
receiver, any other argument kind, storing the formatted result, or any consumer other than `print`
abstains. Printed string bytes are never opened or treated as evidence.

After the test candidates are known, recompute both complete test-argument backward-name sets. If any
`descriptive_scalar` name or descendant appears in either set, abstain
`aggregation-on-test-operand-path`. This is the straight-line equivalent of descriptive-loop condition
(c); source order cannot rescue the violation. The reductions supply no Finding evidence.

## 6. X4 — bounded helper inlining

X4 replaces the blanket 1.0 `interprocedural-call-unresolved` rule only for the exact helper grammar
below.

### 6.1 Relevant-helper fixed point

Start from the selected module body or `main`. A call is an `inline_candidate` only if its callee is a
simple `Name` and exactly one same-module, top-level synchronous `FunctionDef` has that name. A helper is
relevant when at least one condition holds:

1. its body or a transitively named helper body contains an accepted reader, positive test,
   dependence-aware API, registered aggregation/safeguard, or result-output sink;
2. one actual argument reads a tracked reader-component, test-argument, statistic, p-result, or a value
   derived from one;
3. its returned definition lies on a backward slice to a test argument or a forward slice from the
   test result to an accepted sink; or
4. its body reads or may write a tracked value.

Compute this set to a fixed point using names and AST API identities only. A helper called only with
constants and containing only constant-label output is irrelevant; it is not inlined, and its printed
text is not opened. An uncalled helper is likewise irrelevant. A dynamic callee, attribute call, callable
alias, lambda, nested definition, or nonunique/rebound function on a relevant path abstains; it is never
guessed.

### 6.2 Eligibility grammar

Every relevant helper and call site must pass all checks:

1. The definition is a unique module-level synchronous `def`, called by its exact simple name.
2. Parameters are ordinary positional-or-keyword parameters only. There are no positional-only or
   keyword-only parameters, annotations, type comments, `*args`, keyword-only separator, or `**kwargs`.
   A parameter may have a default only when that default is a literal `Constant` or a closed module
   constant from section 3.1; an omitted actual binds that value. Any other default is unsupported.
3. The call has no starred positional or dynamic keyword argument. Python's ordinary positional-then-
   keyword binding maps every actual argument to exactly one parameter, with no missing, duplicate, or
   unexpected parameter.
4. The helper call graph is neither directly nor indirectly recursive.
5. The helper contains exactly one `Return` node. It is the final top-level statement. Its value is
   exactly one of: a tracked `Name`; an accepted reader call from base-design section 5.3; an accepted
   selection or identity expression from base-design section 5.4 and base-design section 4.4; or a
   registered test call from base-design section 5.5. A bare return, `dict`, `list`, `tuple`, computed
   scalar, yield, or return nested in control flow abstains
   `helper-return-expression-unsupported`.
6. There is no `global` or `nonlocal` anywhere in the helper.
7. There is no nested function, async function, class, lambda, or closure.
8. There is no decorator, async definition/call, `await`, `yield`, or `yield from`.
9. Apart from the final `Return`, every body statement must be accepted by base-design sections 4.3,
   5.3 through 5.7, and 6.2, plus this delta section 5; there is no helper-only statement exemption.
10. Root selected scope has inline depth 0. Its direct helper has depth 1; a helper called from that
    expansion has depth 2. Any attempted depth 3 expansion abstains.
11. Each syntactic call site is expanded once. Re-entry to the same call-site identity during expansion
    abstains; two distinct source call sites may each receive their own expansion.

### 6.3 New helper abstention codes

Each failed X4 condition has one closed code. Codes are reported at the relevant call-site span, so an
invalid but uncalled helper cannot dominate a result.

| Condition | Exact reason |
| --- | --- |
| callee is not a simple name | `helper-callee-not-simple-name` |
| no unique un-rebound module definition | `helper-definition-unavailable-or-nonunique` |
| positional-only, keyword-only, annotation, or type-comment form | `helper-parameter-shape-unsupported` |
| any default outside section 6.2's literal/closed-module-constant forms | `helper-parameter-default-unsupported` |
| `*args`, keyword-only separator, or `**kwargs` | `helper-variadic-parameter-unsupported` |
| actual-to-formal binding is not exact 1:1 | `helper-argument-binding-unsupported` |
| direct or indirect recursion | `helper-recursion-unsupported` |
| return count is not exactly one | `helper-return-count-unsupported` |
| return is not the final top-level statement or is bare/nested | `helper-return-position-unsupported` |
| returned expression is outside section 6.2's four exact classes, including tuple/dict/list/computed scalar | `helper-return-expression-unsupported` |
| `global` or `nonlocal` | `helper-global-nonlocal-unsupported` |
| closure, nested definition, class, or lambda | `helper-closure-or-nested-definition-unsupported` |
| decorator, async, await, or yield | `helper-async-decorator-or-yield-unsupported` |
| any non-return body statement is outside the selected-body allowlist | `helper-body-statement-unsupported` |
| a free load name is absent from the closed module table | `helper-free-name-unbound` |
| attempted inline depth 3 | `helper-inlining-depth-exceeded` |
| second expansion of one syntactic call site | `helper-call-site-reentry-unsupported` |

These codes occupy existing path-local precedence rank 6, where
`interprocedural-call-unresolved` currently sits. Order by relevant call-site source span; at one span,
the table order is the tie-break. Successfully expanded body nodes retain their original source spans
and existing 1.0 reason ranks. Thus a `mixedlm` exposed by successful inlining remains
`dependence-aware-sibling-present`, not a helper error.

### 6.4 Expansion algorithm

For each eligible call site in source order:

1. Bind actual expressions to formal parameters under section 6.2.
2. Give every parameter and helper-local store the internal identity
   `inline::<call-line>:<call-column>::<def-line>:<def-column>::<original-name>`. These identities are IR
   labels, not source identifiers, and cannot collide with source names.
3. Insert synthetic single-assignment parameter definitions at the call site, then the renamed body
   statements in original order. Replace the final return with one synthetic return-definition bound to
   the call's assignment target. A standalone helper call discards that definition but does not waive
   the exactly-one-return rule.
4. Preserve every original node span plus the call-site span. Evidence spans point to original reader,
   selection, test, and sink nodes; synthetic bindings never become evidence.
5. Count each synthetic parameter and return definition in every applicable 16-definition path. The
   reader-to-operand, component-to-sink, and result-to-output ceilings remain independent.
6. Resolve every helper free `Load` name exclusively against section 3.1's module binding table. A name
   absent from that table and not a bound parameter, helper local, or registered unshadowed builtin
   abstains `helper-free-name-unbound`; Python runtime global lookup is not approximated.
7. Repeat to depth 2, then rerun reader census, selection/test construction, direct-path
   counterevidence, sibling/dependence suppressors, unregistered component-to-sink guards, loop checks,
   and result-sink tracing over the expanded IR.

Inlining occurs before all sibling and suppressor scans. It cannot erase an aggregation, mutation,
second reader, dependence-aware API, unregistered output-reaching call, or unsupported body construct.
Unsupported expansion always abstains and is recorded as a coverage limit.

## 7. Predicate and identity delta

The ordered 1.0 Finding predicate changes only as follows. Its step order dominates section 6.4's
earliest-source-span rule: a failed earlier predicate step is reported even when a later refusal has an
earlier source line.

- At scope selection, run X1's setup screen.
- Before reader census, expand every relevant eligible X4 helper; failure returns its exact X4 reason.
- Resolve an authorized reader's path with the union of the unchanged 1.0 forms and X1's three symbolic
  file-parent forms.
- During graph construction, classify X3 scalars and enforce the post-candidate backward-slice veto.
- During result-consumer validation, accept X2 statistic roots; at output-sink step 20 still require an
  accepted p-result sink.
- Run direct-path and component counterevidence on the expanded IR, not the unexpanded function bodies.

The human authority, CSV fact, D1' scan, two-group requirement, Finding title/summary, and generic
contract-conflict semantics do not change. This is recognition-grammar `1.1.0`. The build must bump the
adapter version from `1.0.0` to `1.1.0`, the check version from `1.3.0` to `1.3.1`, and the separate
experimental code-lane detector identity from `1.0.0` to `1.1.0`; those are content-addressed identity
updates, not additional grammar. The old Envelope 2 manifest and its 1.0 closure remain immutable
burned history. No qualification or production pin is created by the version bump.

## 8. Updated opened-development check: all fourteen scripts

These are opened development cases and earn no blind credit. Outcomes below are inferred from the exact
X1–X4 algorithm and must be locked by tests before Envelope 3. “Candidate” means an evaluation candidate;
pre-qualification normal-path Findings remain zero.

| Envelope / role | Case | Expected 1.1 outcome | First reason or complete path |
| --- | --- | --- | --- |
| 1 / P1 | `45dcad2f6496a0fd5778` | **Candidate** | Unchanged flat reader/selection/test/p-output path; its descriptive loop remains valid (`evaluation/development/blind-envelope-2026-08-21/cases/45dcad2f6496a0fd5778/project/analysis.py:11-29`). |
| 1 / P2 | `88e59abe85a8eea2b8cd` | **Candidate** | Unchanged flat reader/selection/test/p-output path (`evaluation/development/blind-envelope-2026-08-21/cases/88e59abe85a8eea2b8cd/project/analysis.py:11-28`). |
| 1 / P3 | `0f721a41bac71a461dd2` | **Candidate** | Unchanged flat reader/selection/test/p-output path; descriptive loop remains valid (`evaluation/development/blind-envelope-2026-08-21/cases/0f721a41bac71a461dd2/project/analysis.py:7-28`). |
| 1 / N1 | `5994e65153b07855b07c` | Abstain, correct negative | `aggregation-on-test-operand-path`; tested values come from `groupby(...).agg(...mean...)` (`evaluation/development/blind-envelope-2026-08-21/cases/5994e65153b07855b07c/project/analysis.py:41-45`, `:56-59`, `:84`). |
| 1 / N2 | `e804a86a1e05b781f292` | Not applicable, correct negative | `no-repeated-authorized-unit` before source inspection (`evaluation/development/blind-envelope-2026-08-21/cases/e804a86a1e05b781f292/project/analysis.py:15-29`). |
| 1 / N3 | `11af5bb3f9b7e8e0b293` | Abstain, correct negative | `tracked-value-mutation` at the group-column assignment; mixed model and aggregated sibling remain later guards (`evaluation/development/blind-envelope-2026-08-21/cases/11af5bb3f9b7e8e0b293/project/analysis.py:25-31`, `:69-75`, `:101-149`). |
| 2 / P1 | `e8f97fe750189052f726` | **Abstain; honest development miss** | X4a admits `load_data(path=DATA_FILE)` because `DATA_FILE` is a closed module constant, so the authorized reader becomes eligible. The next earlier predicate blocker is `helper-return-expression-unsupported` at `describe_group(standard)`: `describe_group` returns a dict, outside section 6.2's four return classes (`evaluation/development/blind-envelope-2-2026-08-22/cases/e8f97fe750189052f726/project/analysis.py:23-34`, `:44-50`). The later computed-scalar `welch_degrees_of_freedom` return is independently unsupported. |
| 2 / P2 | `2df3396d80adbb63dffb` | **Abstain; honest development miss** | X4 expands the loader and X1 resolves its path, but D2's exact terminal rejects the direct arithmetic argument `n_total - 2` in the line-63 `.format` call: `unregistered-component-call-reaches-output`. The statistic consumer at line 62 is legal and the p-result sink at line 64 exists, but neither waives that component-consuming output guard (`evaluation/development/blind-envelope-2-2026-08-22/cases/2df3396d80adbb63dffb/project/analysis.py:20-42`, `:61-64`). |
| 2 / P3 | `ca18f96d45dff1b921ad` | **Abstain; honest development miss** | `helper-return-expression-unsupported` at `compare_groups(df)`: its returned dict packages `.size`, `int`, `float`, reductions, and test-result fields outside the unchanged expression grammar (`evaluation/development/blind-envelope-2-2026-08-22/cases/ca18f96d45dff1b921ad/project/analysis.py:29-48`, `:74-77`). Independently, `report(res)` has zero explicit returns and would fail `helper-return-count-unsupported`; neither rule is loosened for this case. |
| 2 / N1 | `15b07ef7670800ba88e0` | Abstain, correct negative | Predicate step 14 fires first: `two-group-row-selection-unavailable`, because the tested value column `litter_mean_body_mass_g` is not a header in the authorized CSV. The later mean-reduced groupby path remains independent counterevidence (`evaluation/development/blind-envelope-2-2026-08-22/cases/15b07ef7670800ba88e0/project/analysis.py:52-58`, `:73-82`). |
| 2 / N2 | `5ef43dbf631adcf3daec` | Not applicable, correct negative | `no-repeated-authorized-unit` at the CSV gate; helper grammar is never consulted (`evaluation/development/blind-envelope-2-2026-08-22/cases/5ef43dbf631adcf3daec/project/analysis.py:38-75`). |
| 2 / N3 | `e60c84d0cda3cc465df7` | Abstain, correct negative | `helper-body-statement-unsupported` at `load_data(CSV_PATH)`: its reader helper contains comprehensions, tracked conditionals, and a tracked subscript store outside the selected-body grammar (`evaluation/development/blind-envelope-2-2026-08-22/cases/e60c84d0cda3cc465df7/project/analysis.py:48-80`, `:345-350`). If that helper were supported later, `smf.mixedlm` would independently suppress (`:190-193`). |
| 2 / N4 | `6090fc1b1b6dbfcd6eee` | Abstain, correct negative | `additional-accepted-reader-present`: main reads both the authorized raw file and the summary file (`evaluation/development/blind-envelope-2-2026-08-22/cases/6090fc1b1b6dbfcd6eee/project/analysis.py:21-38`). The constant-only `rule` helper is irrelevant under section 6.1. |
| 2 / N5 | `d4d95cdd4f4e698d675c` | Abstain, correct negative | After the eligible loader, `describe(wells)` is the first relevant invalid helper and returns a tuple: `helper-return-expression-unsupported` (`evaluation/development/blind-envelope-2-2026-08-22/cases/d4d95cdd4f4e698d675c/project/analysis.py:121-148`, `:154-178`). The later cluster-bootstrap helper and its output remain independent counterevidence (`:47-115`, `:213-255`), before the raw-row test at `:261-274` can qualify. |

Honest opened expectation after D2: **3/6 positives become evaluation candidates; 0/8 negatives become
candidates; all fourteen produce zero dependence Findings before qualification; replay projections are
identical.** The three positive misses are fixed coverage limits of the authorized X3/X4 grammar, not
builder discretion.

## 9. Batch-K development check

X1–X4 do not move analysis files or add a non-root filename admission. All four K t-test cases therefore
retain their normal-path first reason before helper inlining:

| K case | Expected normal-path outcome | First reason; later diagnostic blocker |
| --- | --- | --- |
| `0de3a6061d3bb4056306` | Abstain | `analysis-source-envelope-unavailable`; only `workflow/analysis.py` exists. Even after diagnostic normalization, comprehension buckets and subscript test arguments remain unsupported (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/0de3a6061d3bb4056306/workflow/analysis.py:21-32`, `:49-58`, `:119-122`). |
| `6b2da0c7167dbba3738f` | Abstain | `analysis-source-envelope-unavailable`; only `workflow/analysis.py` exists. `defaultdict` and the mutating bucket/reactor loop remain outside the grammar (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/6b2da0c7167dbba3738f/workflow/analysis.py:23-25`, `:36-51`). |
| `e9e2718573bb47f7d17b` | Abstain | `analysis-source-envelope-unavailable`; only `workflow/analysis.py` exists. `.strip()` and `np.array` remain unsupported transforms (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/e9e2718573bb47f7d17b/workflow/analysis.py:23-30`, `:49-58`, `:106-109`). |
| `3ae92d0bb421d6eee99e` | Abstain | `analysis-source-envelope-unavailable`; only `workflow/analysis.py` exists. `defaultdict`, `.strip()`, and `np.array` remain unsupported (`evaluation/development/dependence-growth-loop/batch-k2/authoring/cases/3ae92d0bb421d6eee99e/workflow/analysis.py:23-32`, `:45-56`). |

K expectation remains **0/4 candidates**. The two K binomial cases remain outside the unchanged positive
test API table.

## 10. Fresh Envelope 3 protocol delta

Envelope 3 repeats code-slice 1.0 section 11's isolation, chronology, freezing, nonexecution, scoring,
replay, and burn rules with wholly new bytes. Envelope 1 and Envelope 2 prompts, cases, labels, roles,
outputs, and opened code earn no credit.

The exact deltas are:

1. Use a newly frozen prompt-author briefing with a new byte length and digest. One isolated prompt-author
   agent sees neither design, implementation, allowlists, prior prompts/cases, K, detector output, nor
   opened development code.
2. The only platform constraint remains one root `analysis.py` in Python. The briefing must not mention
   X1 path forms, helpers, defaults, return rules, reductions, API spellings, wording, accepted grammar,
   or suppressors.
3. Freeze three positive prompts and five negative prompts before builder/Fable access. Positives request
   the same scientific behavior as before: repeated authorized units, two groups, and row-level values
   passed to an independent two-sample test.
4. Keep all five Envelope 2 negative scientific shapes. To preserve the explicitly directed 3P/5N size
   while adding the new helper shape, the original “aggregate to one value per unit before testing”
   negative is instantiated as a **helper-defined pseudobulk that returns the aggregated frame**. The
   other four remain: genuine one-row-per-unit input; a dependence-aware or aggregated alternative beside
   a tempting raw test; a correct per-unit summary loaded from a second CSV; and an off-registry
   dependence-aware primary with an illustrative raw test.
5. Freeze a new implementation closure only after the ADR amendment, build, independent audit, complete
   test matrix, 108-case blind gate, and 155-case regression gate pass. Any closure-byte change after
   briefing/prompt/case disclosure burns Envelope 3.
6. Acceptance remains 3/3 positive roots recognized, missed roots 0, root recall 1.0, 0/5 negative
   candidates/Findings, completed-opportunity false-positive rate 0.0, zero false Findings across the 108
   blind and 155 regression cases, and replay equality 8/8. After a separately accepted qualification and
   pin only, require three positive normal-path Findings and zero negative Findings.

No prompt retry or grammar tuning follows a miss. An unsupported author output remains a miss and burns
the envelope. Fable, under executive authority granted by Alex 2026-08-21, accepts on 2026-08-22 that
this no-retry run proceeds with one known uncovered common idiom: helpers returning dict/tuple compute
payloads. That burn risk is deliberate and does not authorize post-freeze widening.

## 11. Test-plan delta

All code-slice 1.0 tests and gates remain. Add the following without reducing any existing negative
matrix.

### 11.1 X1 module/path tests

- Positive and byte-equality tests for each of the three direct file-parent forms and each one-base-alias
  form, under exact and aliased accepted imports.
- Relevant literal path constants, numeric constants, and 1-to-16-element constant tuples; tuple sizes 0,
  16, and 17; starred/nested/dynamic tuple refusals.
- Irrelevant side-effect-free literal assignments produce byte-identical observations when added,
  removed, or renamed. Calls, attributes, comprehensions, non-name stores, relevant unsupported
  assignments, cycles, and every other module statement abstain.
- Exact contract-path match and byte-case mismatch; path mismatch remains refusal.
- Refusals for rebinding `__file__`, two alias hops, `os.getcwd`, environment/argv, f-string,
  concatenation, `.absolute`, `.parents`, `joinpath`, multiple/nonliteral join components, alternate path
  API, and applying the new idioms to an otherwise unregistered reader.
- Prove the symbolic evaluator performs no filesystem or path-library call.

### 11.2 X2 sink tests

- Tuple statistic name, `RESULT.statistic`, and `RESULT[0]` are legal consumers through every unchanged
  wrapper; statistic-only `print(f"t = {t:.3f}")` must **not** satisfy predicate step 20.
- `RESULT[1]` remains the p root; other indices/attributes, arithmetic, conditional formatting, helper
  payloads, serializers, and `mannwhitneyu` statistic-only output abstain.
- Statistic sink changes no fact wording, Finding wording, CSV fact, or selected-result implication.

### 11.3 X3 descriptive-scalar tests

- One positive probe for every exact method/builtin reduction, both before and after the test, assigned
  outside print, unused, and passed through each allowed scalar arithmetic descendant to print.
- Negative probes for each wrong argument/keyword, unknown receiver/method, redefinition, container
  store, control-flow use, unregistered call, mutation, NumPy reducer, and group reducer.
- For every reduction, route the assigned name or a descendant into one test-argument backward slice and
  require `aggregation-on-test-operand-path` regardless of source order.

### 11.4 X4 helper tests

- Eligible loader, selector, test, dependence-safeguard, descriptive, and sink helpers at depth 1 and 2;
  positional, keyword, and mixed exact binding; two distinct call sites with collision-prone source names.
- One negative probe for every section-6.3 code, including direct and mutual recursion, depth 3, call-site
  re-entry, zero/two/nonfinal/tuple returns, every parameter-shape violation, nested definitions,
  decorators, async/yield, and each unsupported body statement.
- Prove uncalled helpers and constant-only print helpers are ignored, while a helper consuming tracked
  data or carrying a registered API cannot be ignored.
- Put `mixedlm`, aggregation, a second reader, tracked mutation, and an unregistered output-reaching call
  inside otherwise eligible helpers; require the existing substantive guard after expansion.
- Helper-defined pseudobulk returning an aggregated frame must abstain on
  `helper-return-expression-unsupported` when the return expression itself is outside section 6.2's
  four classes, or `aggregation-on-test-operand-path` when the aggregation is first assigned and the
  helper returns its accepted tracked `Name`; no helper name or comment participates.
- Definition-ceiling tests at 16 and 17 on reader, sibling, and result-output paths after synthetic
  parameter/return nodes are counted.

### 11.5 Development/corpus/normal-path gates

- Lock the exact section-8 result and first reason for all fourteen opened scripts through both the
  direct dataflow entry and normal `sc-referee audit` path with their existing profile-`1.1.0` authority
  records; require replay equality and zero pre-qualification Findings.
- Lock section 9 for all four K t-test cases and both K binomial controls.
- Keep the end-to-end prose tripwire over source-envelope selection, adapter inspection, helper expansion,
  and dataflow analysis. Comments, docstrings, printed strings, reports present/absent/mutated, and other
  prose payloads must produce byte-identical observations.
- Require zero Findings from this lane on all 108 existing blind and 155 regression cases, preserve every
  unrelated Finding, and require deterministic replay.
- Run the full changed-surface suite, `ruff check .`, `ruff format --check .`, `mypy src`, full `pytest`,
  and `python scripts/validate_starter.py`. No project-authored file is imported or executed.

## 12. File-by-file build delta

Rough counts are estimates. Files omitted from this table must not change for the 1.1 build.

| File | Delta responsibility | Rough logical change |
| --- | --- | ---: |
| `src/sc_referee/scientific_checks/code_csv_dependence_dataflow.py` | Implement X1 setup/path evaluator, X2 result-statistic sink root, X3 descriptive scalars, X4 helper IR expansion/codes/precedence. | +420 / -70 |
| `src/sc_referee/scientific_checks/code_csv_dependence_adapter.py` | Bump adapter/check identities and bind new grammar digest; preserve the p-result role target, fact, and wording. | +10 / -6 |
| `src/sc_referee/scientific_checks/profiles.py` | Register check `1.3.1`, adapter `1.1.0`, revised known gap “bounded helper inlining”; no new evidence plane or role. | +12 / -8 |
| `src/sc_referee/scientific_checks/integration.py` | Advance the exact code-lane subject-selection version gate to check `1.3.1`; preserve the existing method-target rule. | +1 / -1 |
| `src/sc_referee/detectors/bounded_code_csv_dependence_conflict_v1_1.py` | Add the separate experimental code-lane detector identity `1.1.0`; preserve every byte of the 1.0.0 detector module. | new, ~100 |
| `src/sc_referee/detectors/method_conflict_registry.py` | Dispatch only detector families targeted by answered questions while retaining full-lock validation inputs. | +12 / -1 |
| `src/sc_referee/resources/scientific-check-manifests-v1/registry.json` | Deterministically regenerate code check/adapter/digest rows only. | generated |
| `src/sc_referee/resources/capability-manifests-v1/detector-manifests.json` | Register code-lane detector `1.1.0` and bounded-helper limitation; preserve generic detector bytes/identity. | generated |
| `src/sc_referee/resources/capability-manifests-v1/manifest-set.json` | Regenerate collection digest after the code-lane manifest change. | generated |
| `scripts/build_capability_source_manifests.py` | Generate the revised code-lane manifest without changing generic detector generation. | +12 / -5 |
| `tests/test_code_csv_dependence_dataflow.py` | Complete X1–X4 unit and adversarial matrix, every helper reason, ceilings, guards, and prose tripwire. | +1,050 |
| `tests/test_code_csv_dependence_adapter.py` | Identity, role target, fact stability, no-prose, authority/CSV integration, and normal abstention propagation. | +180 |
| `tests/test_dependence_code_slice_development.py` | Fourteen opened cases, four K t-tests, two binomials, exact first reasons, normal audit, replay. | +260 / -30 |
| `tests/test_scientific_check_integration.py` | Adapter/check identity and unchanged static-source observation semantics. | +45 |
| `tests/test_scientific_check_registry.py` | Registry/digest identity assertions. | +30 |
| `tests/test_method_conflict_target_matrix.py` | Preserve generic-detector coverage through its existing validation-only dependence projection. | +10 / -3 |
| `tests/test_dependence_recognition_scientific_adapter.py`, `tests/test_dependence_recognition_v2.py`, `tests/test_multiple_testing_recognition_scientific_adapter.py` | Update exact active-identity assertions; assert the withdrawn dependence pin is stale. | +5 / -5 |
| `evaluation/development/pseudorep-code-slice-v1_1/DEVELOPMENT_LEDGER.json` | Canonical hashes, labels, expected candidate state/first reason for 14 opened plus K controls; zero blind credit. | new, ~180 |
| `docs/implementation/CAPABILITY_MATURITY_LEDGER.json`, `evaluation/regression-corpus-v1/ledger.json`, `evaluation/regression-corpus-v1/execution-plan.json` | Regenerate content-addressed private/current-regression projections only; no case or outcome change. | generated |
| `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md` | After approval, record X1–X4 eligibility amendment and provenance; no wording or authority change. | +35 |
| `docs/implementation/PUBLIC_INTERFACES.md` | Replace the intraprocedural limitation with the exact depth-2 helper limit; no public capability claim. | +6 / -4 |

Explicitly unchanged: contract parser/schema `1.1.0`, report adapter and every prose grammar byte, CSV/D1'
implementation, fact projection fields, Finding template, generic detector implementation/manifest,
qualification records, metric sets, production pins, reporting policy, CLI flags, execution/security
machinery, Slice C, v2 wall grammar, and both burned envelope directories.

## 13. Observed, inferred, and verification-needed

### Observed

- Envelope 2 failed only on unsupported/scope paths and convicted no negative; closure and replay were
  complete (section 2).
- The exact opened source forms and guards cited in sections 2 and 8 are present in the frozen files.
- Code slice 1.0 currently accepts only literal module constants, rejects every `__file__` path, does no
  helper inlining, traces p-result rather than statistic roots, and limits straight-line assigned
  descriptives (`src/sc_referee/scientific_checks/code_csv_dependence_dataflow.py:1261-1427`,
  `:1093-1156`, `:1614-1756`).

### Inferred; must be verified by the build tests

- The exact delta should yield 3/6 opened positive candidates and 0/8 opened negative candidates;
  X4a admits `e8f97fe750189052f726`'s loader but its dict-returning descriptive helper remains the next
  honest blocker.
- X4 exposes registered counterevidence without creating a new positive API or expression form.
- Synthetic parameter/return nodes can be added while preserving stable source evidence and the three
  independent 16-definition ceilings.
- The registry/check/detector version plan in section 7 is the minimal content-addressed identity update.

### One review choice that would change the blind protocol, not the implementation

The directive says both “3P/5N” and “the same negative shapes plus one more.” This draft preserves the
explicit eight-case bar by making the existing aggregation negative use the new helper-defined
pseudobulk shape, so all requested behavior is tested in five negatives. If “plus one more” instead means
an additive sixth negative case, Fable must change Envelope 3 to 3P/6N before its briefing is frozen; no
X1–X4 implementation rule would change.
