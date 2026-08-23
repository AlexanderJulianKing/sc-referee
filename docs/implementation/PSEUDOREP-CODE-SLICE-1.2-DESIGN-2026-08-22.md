# Pseudoreplication code slice 1.2 delta design — 2026-08-22

- **Status:** Accepted for build by maintainer directive
- **Decision provenance:** Fable, under executive authority granted by Alex 2026-08-21
- **Normative bases:**
  `docs/implementation/PSEUDOREP-CODE-SLICE-DESIGN-2026-08-22.md` and
  `docs/implementation/PSEUDOREP-CODE-SLICE-1.1-DESIGN-2026-08-22.md`
- **Governing ADR:**
  `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md`
- **Delta identity:** check `1.3.2`, adapter and recognition grammar `1.2.0`, separate experimental
  code-lane detector `1.2.0`
- **Evidence:** Python AST, CSV structure, frozen contract, and established API names only
- **Project-authored-code execution:** forbidden

## 1. Boundary

This delta adds exactly two output-only recognition forms:

1. **X5:** an X3 descriptive value may cross one already-eligible helper return as one closed scalar,
   dict literal, tuple literal, or list literal, provided its complete use graph is print-only; and
2. **X6:** an X3 descriptive arithmetic descendant may appear directly as a positional argument of the
   already-accepted literal-string `.format(...)` call that flows directly to `print`.

Neither form supplies a reader, selection, test argument, registered test, p-result sink, contract fact,
or Finding premise. The unchanged positive predicate still requires one authorized reader, two raw-frame
group selections, one registered row-independent two-sample test, and one p-result output sink. Any X5
or X6 uncertainty abstains.

No prose channel, new API, new path form, new selector, new test, new sink, inter-file analysis, deeper
inlining, qualification, production pin, CLI option, execution machinery, or Envelope 3 is authorized.

### 1.1 BUILD-NOTES

- The original retirement set contained 31 collected items, but only 29 are report-lane qualification
  items. Those 29 remain retired under `retired_report_lane`. The task-binding disclosure test and
  `test_false_accusation_halts_and_preserves_per_case_outputs` are code-lane process/safety guards, not
  report-evidence tests, and are restored to the default gate in 1.3. Historical report-adapter replay
  tests added while separating the registered code adapter remain explicitly marked as historical.
- `MANIFEST.sha256` is not refreshed. Its dirty-worktree identity test remains an expected release-time
  failure until Alex authorizes a release manifest refresh.
- Ambiguity in “computed scalar” is resolved narrowly: it is only an X3 descriptive reduction, `len`,
  `round` form, or arithmetic descendant built from already-bound X3 descriptive names. `int`, `float`,
  `.var`, `.size`, `.shape`, result attributes, direct embedded reductions inside arithmetic, and other
  casts/properties remain outside X5. This preserves “exactly X3 lifted to helper scope.”
- X5 requires the exact one-name assignment in section 3.1; a qualifying helper called as an expression
  statement or assigned to any other target abstains. Arithmetic must contain an already-bound X3
  descriptive name: a numeric-only computed scalar and arithmetic containing module constants abstain.
- The X5 output graph is source ordered. A returned root does not exist until its marked assignment, so
  a forward reference abstains. Builtin `print` keywords, f-string conversions and format specifications,
  and a print payload mixing X5 data with another non-constant dynamic name also abstain. These are
  deliberately narrower readings of the closed print-only terminal.
- Development fixtures `rq1`, `rq2`, and `rq3` remain honest code-lane misses. Their identical flat
  scripts read `data/input.csv`, build `observed` from the `signal` column and `reference` from the
  `reference` column, then call `st.ttest_ind(observed, reference)`
  (`tests/test_dependence_free_envelope.py:84-103`). The CSV contract authorizes `bird_code` as the unit
  column, but the table has no contract group/contrast column and the operands are two measurement
  columns rather than two row selections on an authorized group column
  (`tests/test_dependence_free_envelope.py:69-81`). The first code-lane reason is therefore
  `two-group-row-selection-unavailable`; re-baselining those three from historical report-lane “caught”
  to `missed_unsupported` did not assert or imply a code-lane catch.

## 2. Diagnosis of the three 1.1 positive misses

All observations below are from frozen Python AST/source bytes. Comments and docstrings were not used to
classify any path.

### 2.1 `e8f97fe750189052f726`

The first 1.1 blocker is the call `standard_stats = describe_group(standard)` and its twin for
`high_sugar`; `describe_group` returns this exact dict literal:

```python
return {
    "n_flies": int(values.count()),
    "mean_mm": float(values.mean()),
    "sd_mm": float(values.std(ddof=1)),
}
```

(`evaluation/development/blind-envelope-2-2026-08-22/cases/e8f97fe750189052f726/project/analysis.py:28-34,49-50`).
The returned subscripts feed only arithmetic assigned to `difference_mm` and `total_flies`, then literal
`.format(...)` calls under `print`; they never reach either `ttest_ind` argument
(`:52-57,67-92`). The dict nevertheless fails X5 because each value adds an unregistered `int` or
`float` cast around an X3 reduction.

Even if those casts were absent, the next blocker is
`welch_df = welch_degrees_of_freedom(high_sugar, standard)`. That helper returns
`float((va + vb) ** 2 / (...))` after tuple assignment from `.var(ddof=1)` and `.count()`
(`:37-40,55`). The scalar is print-only at line 91, but `.var`, the tuple target, and `float` are outside
X3/X5. Therefore 1.2 still abstains honestly.

### 2.2 `ca18f96d45dff1b921ad`

The blocker is `res = compare_groups(df)`. The helper selects `thinned` and `unthinned`, performs
`result = stats.ttest_ind(thinned, unthinned)`, and returns a dict mixing `.size`, X3 reductions,
arithmetic, `result.statistic`, and `result.pvalue`
(`evaluation/development/blind-envelope-2-2026-08-22/cases/ca18f96d45dff1b921ad/project/analysis.py:29-48,74-77`).
The returned dict is passed only to `report(res)`, whose subscripts are printed at lines 51-71; it does
not feed another test argument or reader.

X5 does not admit a descriptive helper that packages a registered-test result, `.size`, result
attributes, or arithmetic containing those values. Independently, `report` has no terminal return and
is not an X4 helper. This case remains an honest miss; allowing it would merge the positive test lane
with a new structured-result/output-helper grammar rather than lift X3.

### 2.3 `2df3396d80adbb63dffb`

The 1.1 blocker is exactly:

```python
print("  df = {:d}".format(n_total - 2))
```

(`evaluation/development/blind-envelope-2-2026-08-22/cases/2df3396d80adbb63dffb/project/analysis.py:63`).
`n_total` is the arithmetic descendant of `n_control = len(control)` and
`n_treated = len(treated)` (`:32-34`). `n_total - 2` is used only as a positional argument of a literal
format call flowing directly to `print`; it never reaches the test arguments, reader, or registered
test. This is a descriptive X3 descendant. X6 registers precisely this terminal position.

## 3. X5 — output-only descriptive helper returns

### 3.1 Candidate call site and helper

X5 is considered only for an X4-relevant, same-module, simple-name call in an exact one-name assignment:

```text
RETURN_TARGET = HELPER(ARG, ...)
```

The helper must first satisfy every unchanged X4/X4a rule: signature and default binding, depth at most
2, one expansion per call site, no recursion, async/yield, decorator, closure, global/nonlocal, dynamic
binding, unsupported statement, unbound free name, or definition-ceiling violation. X5 changes only the
return-expression gate.

### 3.2 Closed return shapes

After parameter binding and fresh-name rewriting, the terminal return is one of:

1. one X3 descriptive scalar `Name` or arithmetic descendant;
2. one dict literal with 1 through 16 unique literal `str` or finite literal `int` keys and no unpack;
3. one tuple literal with 1 through 16 elements and no star; or
4. one list literal with 1 through 16 elements and no star.

Each container element/value independently must be exactly one of:

- an X3 descriptive scalar name already assigned from `mean`, `std`, `median`, `min`, `max`, `count`,
  `sum`, builtin `len`, `sum`, `min`, or `max`, including X3's exact `std(ddof=1)` and `round` forms;
- an X3 arithmetic descendant containing only such descriptive names, finite numeric literal constants,
  unary `+`/`-`, and binary `+`, `-`, `*`, `/`, `//`, `%`, or `**`;
- one literal `Constant`; or
- one closed module group-label constant already accepted by 1.1 section 3.1.

The element expression may not contain a call except the reduction call already bound to a descriptive
name. In particular `int(...)`, `float(...)`, `.var`, `.size`, `.shape`, `numpy.*`, result attributes,
readers, registered tests, dependence-aware APIs, comprehensions, conditional expressions, lambdas,
walrus, attribute mutation, subscripts of non-X5 containers, and nested containers are not added.

### 3.3 Mandatory post-expansion scan

The helper body is inlined before any reader census, positive-test construction, aggregation scan,
dependence-aware sibling scan, unregistered component-to-output scan, or result-sink scan. X5 cannot
erase or relabel any body node. Consequently:

- aggregation exposed in the body retains the existing substantive aggregation abstention;
- a dependence-aware call retains `dependence-aware-sibling-present`;
- a registered test is visible to the normal candidate/multiple-test rules; and
- an unsupported component-consuming call reaching output retains its existing reason.

If a helper with an X5-shaped return also contains a registered test and the returned structure contains
any test result/statistic/p-value member, X5 fails. A descriptive helper cannot carry test output.

### 3.4 Complete output-only use graph

Before admitting the return, construct a forward use graph from `RETURN_TARGET` over the expanded scope.
The only derivations are:

- identity assignment `NAME = PREVIOUS_NAME`;
- exact literal-key/integer-index subscript `NAME = CONTAINER[LITERAL]` for the frozen X5 shape; and
- an X3 arithmetic descendant assigned to one fresh name.

Every root, alias, subscript, and descendant must terminate only as:

- a payload of builtin `print`;
- a positional argument of the X3/X6 literal-string `.format(...)` call that flows directly to builtin
  `print`; or
- a formatted field of an f-string flowing directly to builtin `print`.

Unused returned members are permitted; an unused whole return is not. Any store into a container,
attribute access, iteration, condition, comparison, reader argument/path, registered or unregistered
call, helper argument, file sink, registered-test argument, test-result construction, or use outside the
three terminals fails X5. Any root or derived name on either test-argument backward slice fails X5 even
if it also prints.

All X5 shape, element, or use-graph failures return the new rank-6 coverage code:

```text
descriptive-helper-return-contract-unsupported
```

Predicate-step order remains dominant. Existing earlier CSV, reader, selection, mutation, and
aggregation reasons are not replaced by X5.

## 4. X6 — descriptive arithmetic in literal `.format` under `print`

Extend only 1.1 section 5's terminal exception. Each positional argument of an exact literal-string
`.format(...)` flowing directly and exclusively to builtin `print` may additionally be an X3 arithmetic
descendant expression. It must contain at least one already-bound `descriptive_scalar` name; every loaded
name must be such a name or a closed group-label/module literal constant; and every AST node must be one
of `Name`, `Load`, finite numeric `Constant`, unary `+`/`-`, or binary `+`, `-`, `*`, `/`, `//`, `%`,
`**`. Calls, attributes, subscripts, comparisons, containers, conditional expressions, and keywords
remain refused.

The expression must occur directly as the `.format` positional argument and the format result must flow
directly to builtin `print`. It may not be stored. The post-candidate backward-slice veto remains: if any
descriptive name in the expression reaches a test argument, abstain. `n_total - 2` in section 2.3 is the
target form.

## 5. Ordered predicate delta

The 1.1 predicate changes only at helper expansion and output-consumer validation:

1. Apply every unchanged contract, CSV, D1', scope, import, path, reader, and helper precondition.
2. For an otherwise-eligible X4 helper return rejected only by its return expression, apply X5 sections
   3.2 and 3.4. Failure records `descriptive-helper-return-contract-unsupported`.
3. Inline an admitted X5 helper with the unchanged fresh-name/depth/definition accounting.
4. Run all existing reader, dataflow, positive-test, sibling, suppressor, loop, and sink scans on the
   expanded body.
5. During literal `.format` validation, apply X6 in addition to the unchanged X3 argument classes.
6. Require the unchanged p-result sink. Statistic-only or descriptive-only output never satisfies the
   Finding predicate.

The check becomes `1.3.2`; adapter, grammar, and detector become `1.2.0`. The new detector module extends
the 1.1 implementation under its own content digest. The 1.0.0 and 1.1.0 detector modules and their
bytes remain untouched. There is no qualification or production pin for 1.2.0.

## 6. Opened-development re-trace

These cases are opened development evidence and confer no blind credit.

| Envelope / case | 1.2 expectation | First reason or complete path |
| --- | --- | --- |
| 1 P1 `45dcad2f6496a0fd5778` | Candidate | Unchanged raw reader-selection-test-p-sink path. |
| 1 P2 `88e59abe85a8eea2b8cd` | Candidate | Unchanged raw reader-selection-test-p-sink path. |
| 1 P3 `0f721a41bac71a461dd2` | Candidate | Unchanged raw reader-selection-test-p-sink path. |
| 1 N1 `5994e65153b07855b07c` | Abstain | `aggregation-on-test-operand-path`. |
| 1 N2 `e804a86a1e05b781f292` | Not applicable | `no-repeated-authorized-unit`. |
| 1 N3 `11af5bb3f9b7e8e0b293` | Abstain | `tracked-value-mutation`. |
| 2 P1 `e8f97fe750189052f726` | Abstain; honest miss | `descriptive-helper-return-contract-unsupported`; `int`/`float` casts in `describe_group` are outside X3. The Welch helper is an independent later refusal. |
| 2 P2 `2df3396d80adbb63dffb` | **Candidate** | X6 accepts the print-only `n_total - 2`; the raw reader-selection-`ttest_ind`-p-sink chain is otherwise complete. |
| 2 P3 `ca18f96d45dff1b921ad` | Abstain; honest miss | `descriptive-helper-return-contract-unsupported`; the dict mixes a registered test result, `.size`, attributes, and arithmetic outside X3. |
| 2 N1 `15b07ef7670800ba88e0` | Abstain | Earlier predicate step: `two-group-row-selection-unavailable`. |
| 2 N2 `5ef43dbf631adcf3daec` | Not applicable | `no-repeated-authorized-unit`. |
| 2 N3 `e60c84d0cda3cc465df7` | Abstain | `helper-body-statement-unsupported`; later `mixedlm` remains independent counterevidence. |
| 2 N4 `6090fc1b1b6dbfcd6eee` | Abstain | `additional-accepted-reader-present`. |
| 2 N5 `d4d95cdd4f4e698d675c` | Abstain | `descriptive-helper-return-contract-unsupported`; the tuple contains `pd.DataFrame(lines)` and an aggregated frame, and its helper body is outside X5. |

Honest opened expectation: **4/6 positives become evaluation candidates; 0/8 negatives become
candidates; all fourteen produce zero pre-qualification Findings and replay identically.**

## 7. Batch-K re-trace

X5/X6 do not alter the exact root `analysis.py` naming gate. All four t-test cases remain:

| Case | Outcome | First reason |
| --- | --- | --- |
| `0de3a6061d3bb4056306` | Abstain | `analysis-source-envelope-unavailable` |
| `6b2da0c7167dbba3738f` | Abstain | `analysis-source-envelope-unavailable` |
| `e9e2718573bb47f7d17b` | Abstain | `analysis-source-envelope-unavailable` |
| `3ae92d0bb421d6eee99e` | Abstain | `analysis-source-envelope-unavailable` |

The two binomial K controls remain `authorized-group-domain-not-exactly-two`.

## 8. Test-plan delta

Add tests that prove:

- each scalar/container X5 shape succeeds only with X3 elements and print-only use;
- 0-, 1-, and 16-element boundaries behave as specified, and 17 elements abstain;
- duplicate/nonliteral dict keys, nested containers, stars/unpack, casts, `.var`, attributes, calls,
  result members, and direct embedded reductions abstain with the new code;
- every forbidden use-graph edge—test argument, registered test, reader, helper call, unknown call,
  condition, iteration, comparison, mutation, file sink, stored format result—abstains;
- a descriptive helper that secretly aggregates and a raw test elsewhere still abstains through the
  expanded substantive scan;
- a dict return reaching a test argument abstains;
- a helper mixing reductions with a registered test abstains;
- X6 accepts `n_total - 2` and every listed arithmetic operator, but rejects a call, attribute,
  subscript, comparison, container, conditional, keyword, stored format result, untracked name, and a
  name on the test-argument backward slice;
- X5/X6 do not satisfy the p-result sink step;
- comments, docstrings, literal strings, printed labels, and report payload mutations remain
  observation-byte-invariant through helper expansion;
- all fourteen opened cases and six K cases match sections 6 and 7 through normal `sc-referee audit`,
  with replay equality and zero Findings;
- all 108 blind and 155 regression cases produce zero Findings from the lane and preserve unrelated
  outcomes.

Run the active default test gate, `ruff check .`, `ruff format --check .`, `mypy src`, and
`python scripts/validate_starter.py`. The root release-manifest identity check remains separately pending
Alex's release refresh.

## 9. File-by-file delta

| File | Responsibility |
| --- | --- |
| `src/sc_referee/scientific_checks/code_csv_dependence_dataflow.py` | X5 return/use graph, new code, X6 terminal. |
| `src/sc_referee/scientific_checks/code_csv_dependence_adapter.py` | Check/adapter/grammar identity bump only. |
| `src/sc_referee/scientific_checks/profiles.py` | Check `1.3.2`, adapter `1.2.0`, detector `1.2.0`. |
| `src/sc_referee/scientific_checks/integration.py` | Advance the existing code-lane subject-version gate to `1.3.2`. |
| `src/sc_referee/scientific_requirement_contract.py` | Permit only the frozen 1.2/1.3/1.3.1 contract migrations to active `1.3.2`. |
| `src/sc_referee/detectors/bounded_code_csv_dependence_conflict_v1_2.py` | New detector identity; subclass 1.1 without editing it. |
| `src/sc_referee/detectors/method_conflict_registry.py` | Register the 1.2 detector class. |
| `scripts/build_capability_source_manifests.py` | Generate the 1.2 detector manifest. |
| generated capability/scientific registries and private/regression ledgers | Refresh content identities only. |
| `tests/test_code_csv_dependence_dataflow.py` | X5/X6 unit/adversarial matrix. |
| `tests/test_code_csv_dependence_adapter.py` | Identity and no-prose integration. |
| `tests/test_dependence_code_slice_development.py` | Fourteen opened and K normal-path expectations. |
| `pyproject.toml` and the four historical dependence test modules | Register/mark exactly 31 withdrawn-lane tests outside the default active gate. |
| this design, ADR-0076, and `docs/implementation/PUBLIC_INTERFACES.md` | Record the bounded delta, identity, and coverage limits. |

Explicitly unchanged: both prior code-lane detector modules, generic detector, production pin table,
contract schema/profile `1.1.0`, CSV/D1' logic, Finding wording, report/prose adapter bytes, qualification
records, execution/security machinery, Slice C, v2 wall grammar, and both burned envelopes.

## 10. Acceptance and next boundary

This build is accepted as implementation evidence only if section 6 is exactly 4/6 and 0/8, section 7
is unchanged, the active full gate is green except the Alex-owned root manifest refresh, and the old
detector/pin hashes remain byte-identical. Four opened candidates do not themselves authorize Envelope 3;
Fable decides whether the remaining known coverage limits are acceptable before any new blind prompt is
commissioned.
