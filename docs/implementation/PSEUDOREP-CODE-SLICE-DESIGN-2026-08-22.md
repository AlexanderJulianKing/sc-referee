# Pseudoreplication code-slice design — 2026-08-22

- **Status:** Accepted and frozen for Envelope 2
- **Frozen date:** 2026-08-22
- **Freeze acceptance provenance:** Fable, under executive authority granted by Alex 2026-08-21
- **Decision owner:** Alex King
- **Design lane:** contract-bound CSV multiplicity plus static Python dataflow
- **Issue class:** `issue-class:repeated-authorized-independent-unit-entry-into-row-independent-procedure`
- **Fresh blind acceptance bar:** 3/3 positives recognized, 0/all fresh negatives convicted, zero false
  Findings on the existing 108 blind and 155 regression cases, and replay equality
- **Project-authored-code execution:** forbidden
- **Prose evidence:** forbidden
- **Governing ADR:** amended
  `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md`

## 1. BUILD-NOTES: the report lane is withdrawn

Alex's permanent evidence rule is: sc-referee must not read prose. For this check, report text,
Markdown, comments, docstrings, headings, tables, captions, links, output wording, free-text string
contents, and task prose have no evidentiary or suppressive force. The adapter must not request a
Markdown parser result, tokenize report text, inspect comments or docstrings, search a report for a CSV
path, extract an N, lex a t or p literal, or treat prose such as “sensitivity only” as a safeguard.

Accordingly, the following `report_csv_dependence_adapter.py` surfaces are retained only as burned
history and are not Finding-eligible: `_inspect_report`, its admission grammar, N witnesses, selected
path anchor, inferential-result lexer, visible-text machinery, and `_report_suppressor`
(`src/sc_referee/scientific_checks/report_csv_dependence_adapter.py:823-1649`). They must not be
extended. The adapter's verified contract reader and complete CSV scan through D1' are reusable: the
current implementation performs authority/material equality and CSV inspection before it attempts any
report operation (`src/sc_referee/scientific_checks/report_csv_dependence_adapter.py:422-456`), and the
closed CSV implementation is isolated at
`src/sc_referee/scientific_checks/report_csv_dependence_adapter.py:570-752`.

The accepted report-lane design and its BUILD-NOTES remain untouched as the exact history that produced
the burned closure. This document is the replacement build note. The report adapter stays in the tree,
unregistered for the active dependence check and ineligible for any new qualification. The following
pieces remain valid and are reused unchanged in meaning:

- scientific-requirement profile `1.1.0` and its exact `semantic_role_authority`;
- the human Answer and verified-assertion authority chain;
- the authority-bound CSV path and content digest;
- the authorized unit and group/contrast columns;
- CSV bounds, multiplicity facts, and D1';
- the first three existing dependence semantic roles and canonical operands, with the sink role renamed
  as fixed below;
- controller preflight and final contract binding;
- the generic bounded method-conflict detector and admission machinery;
- optional Finding-profile fields in `GrantPin`; and
- the single existing dependence pin slot, which remains stale and nonauthorizing until a fresh
  qualification is separately accepted.

The burned report envelope is evidence, not qualification. Its frozen result was 0/3 positive
recognition, 0/3 negative convictions, zero Findings, 6/6 replay equality, and 31/31 closure matches
(`evaluation/development/blind-envelope-2026-08-21/CUSTODY_LOG.md:76-77`;
`evaluation/development/blind-envelope-2026-08-21/AUDIT_RESULTS.json:1-15`). Its six labels agreed with
the sealed roles (`evaluation/development/blind-envelope-2026-08-21/BLIND_REVIEW.json:1-79`). Those
opened cases are development fixtures only and can never be fresh blind evidence again.

The exact-root `analysis.py` requirement below is a naming-convention admission gate. Its satisfaction
does not demonstrate a scientific fact, make the file primary, or make any result selected. It exists
only to bound which code bytes the first code-lane grammar can inspect; missing or additional analysis
surfaces cause abstention.

### 1.1 Authorized-build notes

- **B1 class-root dependence guard:** registered `MixedLM` and `GEE` class identities suppress through
  every statically resolved attribute suffix, including constructors, `.from_formula`, `.fit`, and any
  other method. The match is an exact registered class root followed by `.`; arbitrary `MixedLM`/`GEE`
  spelling is not inspected.
- **B2 shared output-sink registry:** one structural sink table is used by both the p-result output check
  and the component-call-to-output guard. `print`, `Path.write_text`, and the bounded write handle are
  p-result eligible. Exact `.to_csv`, `numpy.savetxt`, and `json.dump` file terminals are in the same
  table with `p_result_eligible=false`: they close rule 2 but do not establish a new Finding-eligible
  p-result sink. This is a narrowing only.
- **B3 loop and builtin-shadow narrowing:** descriptive-loop target names are checked against every name
  on both complete test-argument backward slices and against every tracked definition. Any target that
  rebinds either set abstains. A `FunctionDef`, `AsyncFunctionDef`, or `ClassDef` whose bound name is one
  of the registered builtins, as well as an assignment/import that shadows one, makes API resolution
  ambiguous and abstains.
- **B4 complete definition ceiling:** the 16-definition ceiling is calculated independently over both
  reader-to-operand paths, every reader-component sibling path reaching a registered sink, and every
  p-result-to-output path. Sixteen labeled definitions pass; seventeen abstain.
- **B5 closed minor resolutions:** both exact `from pathlib import Path [as NAME]` and exact
  `import pathlib [as NAME]` resolve the same established `pathlib.Path` identity. Only literal
  `Constant` assignments qualify as closed module constants; module-level `Call`, `BinOp`, or `Name`
  assignments do not. `importlib`, `__import__`, and relative/star imports make both the selected-source
  resolver and the other-Python E6 scan incomplete. Any `global` or `nonlocal` node anywhere in
  `analysis.py` abstains.
- **B6 matrix completion:** the test surface now has positive and negative cases for each implemented
  import, path, reader, selection, reducer, test, payload wrapper, and sink family; explicit regressions
  for B1 through B5; an adapter/dataflow prose-payload tripwire; same-span prose mutations; and
  report-absent/present/altered invariance. Enumerated but deliberately unimplemented DictReader and
  per-unit-loop forms remain negative coverage probes and cannot become pass-through by omission.
- **B7 regression expected-outcome correction:** the changes in
  `evaluation/regression-corpus-v1/execution-plan.json` are semantic expected-outcome updates, not
  digest-only churn. For `case:calculation:bh-ambiguous`,
  `case:calculation:bh-corrected-twin`, `case:calculation:bh-hard-negative`, and
  `case:calculation:bh-positive`, the dependence lane's new reportless naming gate changes the disclosure
  split from 22 not-applicable / 1 unsupported to 21 not-applicable / 2 unsupported; Finding counts and
  replay expectations remain unchanged.
- **Content-addressed aftermath:** the scientific-check release registry, private capability maturity
  ledger, and the exact adapter-manifest expectation in the multiple-testing integration suite were
  refreshed to the narrowed code adapter identity. The complete-domain check identity, generic detector
  bytes/manifest, production pin, Finding behavior, and calculation-check behavior remain unchanged.

- **E14/E15 implementation rule:** the descriptive-loop exception has no source-order condition. Its
  exact calls include the reviewed Series/array reductions `mean`, `std`, `median`, `min`, `max`,
  `count`, `len`, `sum`, and `round` only when their scalar result flows exclusively into the bounded
  print/format/f-string/arithmetic-to-print path and no bound name or store reaches a test-argument
  backward slice. Constant strings in the loop iterable are structural labels and are not read.
- **Frozen profile-1.1.0 lock compatibility:** the opened-envelope contracts froze check `1.2.0`
  before Alex withdrew the report plane, while this build necessarily registers check `1.3.0`.
  Preflight and final binding therefore accept exactly the `1.2.0` to `1.3.0` ADR-0076 migration when
  the candidate, operand, comparison form, human semantic-role authority, and frozen material-binding
  snapshot are byte-equivalent. Preflight derives an in-memory current-manifest Answer/assertion pair
  only after verifying the immutable parent chain; no broader check-version migration is accepted.
  This narrow compatibility surface was required to exercise the six already-frozen profile-`1.1.0`
  locks without rewriting their bytes.
- **Conservative implementation boundaries:** CSV DictReader reader/selection variants and per-unit
  reducer-loop recognition remain abstaining until their exact AST implementations
  have mutation-complete tests. They remain enumerated design targets and are not treated as equivalent
  by name or resemblance. The implemented reader/selection path is limited to the reviewed pandas
  forms and exact NumPy `genfromtxt` named-array boolean mask, followed by a registered SciPy test and
  one of the three p-result-eligible sinks in section 5.7; the opened positives exercise only pandas and
  builtin `print`. NumPy `.loc` and every other cross-library lookalike abstain. This is a narrowing,
  never a conviction widening.
- **Authorized detector identity split:** Alex authorized a separate code-lane detector identity on
  2026-08-21 at approximately 22:10, relayed by Fable. The code lane is exclusively
  `detector:bounded-code-csv-dependence-conflict@1.0.0`. The installed generic detector source remains
  byte-identical at `sha256:d22f5b5cffbde98201077edf1a3825274780ac23bff997c78b44465e67bdf6d1`;
  its manifest, installed qualifications, complete-domain binding, and complete-domain production pin
  remain unchanged. Because that frozen generic manifest still lists the dependence check, registry
  construction supplies a validation-only binding projection for the frozen allowlist. Scheduling and
  evaluation use only each detector identity's actual registered bindings, so the generic detector can
  never evaluate the reportless dependence question. This projection grants no Finding authority.
- **K naming-gate clarification:** every original K project stores its analysis at
  `workflow/analysis.py`, not the required root `analysis.py`. Through the normal audit path all four
  therefore abstain first at `analysis-source-envelope-unavailable`. Section 10's
  `interprocedural-call-unresolved` entries describe the next diagnostic blocker only after a
  filename-normalized, development-only source trace; they are not the original-project normal-path
  reason. The naming gate was not widened to improve K recall.
- **Non-executing gate boundary:** the final suite intentionally excludes the parked historical
  dependence qualification/sandbox tests. Those tests execute authored workflow fixtures and assert an
  installed Finding from the withdrawn report lane, so running or repairing them would violate both the
  no-project-code-execution directive and the stand-down. The completed gate is the 585-test static,
  audit/replay, identity, 108-case, and 155-case suite named in the build report.

## 2. Decision boundary and exact identities

The replacement check retains:

```text
check_id = check:authorized-independent-unit-entry-into-row-independent-procedure
candidate_id = one-analyzed-row-per-authorized-independent-unit
binding_id = method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1
intended_operand = one_analyzed_row_per_authorized_independent_unit
observed_conflict_operand = multiple_analyzed_rows_per_authorized_independent_unit
```

The build creates these new versioned identities:

```text
check_version = 1.3.0
adapter_id = adapter:authorized-independent-unit-entry-into-row-independent-procedure:code-csv-rowwise-two-sample-v1
adapter_version = 1.0.0
applicability_profile = bounded-code-csv-rowwise-two-sample-dependence-v1
evidence_plane = static_source
parser_manifest = parser:python-ast-tokenize@0.15.1
semantic_parser = python-ast@3.11
fact_profile = code_csv_row_entry_evidence_v1
output_ceiling_before_fresh_qualification = question_only
```

The active check module registers exactly this adapter. It does not register the report adapter as a
second alternative or require both planes. The binding requires exactly `static_source`, assertion role
`observed`, and four role slots; the first three are reused and the fourth is renamed to avoid a
selection inference:

| Role | Exact code/authority evidence |
| --- | --- |
| `authorized_independent_unit_key` | verified profile `1.1.0` authority plus exact CSV column/digest |
| `analyzed_row_domain` | complete CSV plus two closed group selections whose rows partition the table |
| `row_independent_procedure` | one statically resolved registered two-sample API call |
| `result_output_sink` | one accepted structural output sink reached by the registered call's p-result |

No CLI flag is added. The normal route for this lane is:

```text
sc-referee method-contract PROJECT --task TASK --profile PROFILE --actor-id HUMAN --output CONTRACT
sc-referee audit PROJECT --material-input AUTHORIZED.csv --method-contract-lock CONTRACT/semantic.lock.json --output AUDIT
```

`--report` is deliberately absent. `TASK` remains an identity-bound lifecycle input; neither this
adapter nor its Finding predicate reads or interprets the task's prose. A project may contain prose
files, but this check never requests their parsed or decoded contents and never cites them.

## 3. Exact contract and CSV evidence reused

### 3.1 Contract authority

The adapter accepts only the existing profile `scientific_check_requirement_v1` version `1.1.0` with
this exact extension for this check/candidate:

```json
{
  "semantic_role_authority": {
    "authorized_independent_unit_key": {
      "material_input_path": "NORMALIZED/RELATIVE.csv",
      "column_name": "EXACT_UNIT_HEADER",
      "group_contrast_column": "EXACT_GROUP_HEADER"
    }
  }
}
```

The existing Answer, deterministic assertion, `x-authority-binding-snapshot`, full CSV digest,
pre-inspection projection, and final child binding must all agree. Profile `1.0.0`, nonhuman authority,
post-contract material drift, duplicate authority, and any path/column/digest disagreement abstain. No
unit, group column, or material path is inferred from code, headers, variable names, comments, or prose.

### 3.2 Complete CSV predicate

Reuse `_authority` and `_parse_csv` byte-for-byte in meaning. The accepted input is one authority-named,
CLI-selected regular `.csv` with the current strict UTF-8, newline, header, width, row, column, field,
and material-byte bounds. Let:

- `N_csv` be the complete number of data rows;
- `U` be the number of distinct byte-exact authorized-unit values;
- `R` be the number of unit values with multiplicity greater than one; and
- `M` be the maximum unit multiplicity.

The conflict side requires `N_csv > U`, `R >= 1`, and `M >= 2`. `N_csv == U` returns
`not_applicable:no-repeated-authorized-unit`. Malformed, incomplete, oversized, ambiguous, or
unavailable inputs abstain.

D1' remains exact. Before uniqueness testing, candidate column `C` must be neither the authorized unit
column nor the contract group column and must have `distinct(C) <= U`. For each candidate and each unit
`u`, `T_C(u)` is the ascending byte-lexicographic sorted tuple of every decoded `C` value in rows for
`u`, retaining duplicates and empty strings. `C` is a within-unit index exactly when every `T_C(u)` is
byte-identical. Abstain if any candidate has unique `(unit_value, C_value)` pairs across every row and is
not a within-unit index. An incomplete scan abstains. There is no header-name, data-type, identifier,
response, or scientific-semantic exemption.

The code predicate adds one data check: the complete byte-exact domain of the authorized group column
must contain exactly two distinct nonempty values `G0` and `G1`, and every CSV row must have one of them.
The two code selections must use those exact values in either order. This proves from data structure—not
from an N literal—that the selected vectors are disjoint and jointly cover all `N_csv` rows.

## 4. Python source envelope and absolute prose exclusion

### 4.1 Selected source

As a naming-convention admission gate, the adapter considers exactly one strict project-root path
`analysis.py`. It must have one regular-file
record, one full-digest asset identity, one `parser:python-ast-tokenize@0.15.1` result in state `parsed`
with no syntax issues, and bytes identical to the parser source digest. Its size is at most 1 MiB and its
Python 3.11 AST is at most 50,000 nodes. Missing, duplicate, non-UTF-8, mismatched, unparsable, or
over-budget source abstains.

Other Python files are not inlined. The snapshot-wide alternate-analysis scan is mandatory and reads
only filenames and Python import nodes:

1. A project file whose final ASCII-case-folded suffix is `.ipynb` or `.r` causes
   `unsupported:alternate-analysis-file-present`; notebook JSON and R bytes are not opened.
2. Every regular `.py` other than root `analysis.py` is parsed, within the same aggregate 1 MiB and
   50,000-node ceilings, only far enough to enumerate `Import` and `ImportFrom` nodes after deleting
   docstrings. For `import X`, the candidate is `X`; for each `from X import Y`, it is `X.Y`. A
   candidate equal to a prefix, or beginning with that prefix plus `.`, is a hit; raw string-prefix
   matching is forbidden. The exact prefixes are `scipy`, `scipy.stats`, `statsmodels`, `pingouin`,
   `pymer4`, `bambi`, `linearmodels`, `sklearn`, `pymc`, `numpyro`, `stan`, `cmdstanpy`, `rpy2`, and
   `lifelines`. A hit causes `unsupported:statistics-api-imported-outside-analysis-py`.
   Relative/star/dynamic imports, parse or
   decode failure, resource overflow, or inability to prove the complete `.py` file inventory causes
   `unsupported:other-python-statistics-scan-unavailable`.
3. If `analysis.py` imports a project-local module, or if another project Python file has a top-level
   name `pandas.py`, `numpy.py`, `scipy.py`, or `statsmodels.py`, or a same-named package directory with
   `__init__.py`, API resolution is ambiguous and the adapter abstains.

These are coverage gates against an omitted primary analysis, not evidence that `analysis.py` is
primary and not execution or security hardening.

`method_target_ref` is the `analysis.py` file record. The scope join is the existing unique
`FULL_DIGEST_PROFILE` edge from that file record to the current repository snapshot. It does not use a
publication surface, report artifact, writer-to-report edge, or report path. If the exact full-digest
scope proof is absent or nonunique, abstain.

### 4.2 What “never read prose” means mechanically

The dataflow walker reparses only `analysis.py` bytes with the standard-library AST. The separate
section-4.1 alternate-analysis gate parses other `.py` files only for import nodes and never passes their
string literals, comments, docstrings, or executable bodies to the predicate. These rules apply before
dataflow:

1. Comments are unavailable because token comments are never passed to the predicate.
2. A leading module, function, or class `Expr(Constant(str))` docstring is deleted from the semantic
   body. Every other standalone string expression is ignored and can never be a fact or suppressor.
3. Constant string contents are inspected only when they occupy an enumerated structural API slot:
   input path, CSV header key, group value, exact `query` mini-language, exact enum keyword, encoding,
   file mode, or output path. These are code/data operands, not natural-language evidence.
4. Constant portions of f-strings and `.format` templates are never lexed. They contribute no evidence;
   only the AST dependency from a p-result into a sink is followed.
5. Identifier spelling is used only for lexical binding. Names such as `independent`, `average`,
   `sensitivity`, `primary`, or `exploratory` have no special meaning.
6. No Markdown or plain-text `InspectionDocument`, parser result, report artifact, task body, comment,
   docstring, exception message, or printed literal is opened by this adapter.

Mutation tests must prove that deleting, replacing, or adversarially changing every comment, docstring,
report byte, heading, printed label, and free-text f-string segment leaves the normalized observation
byte-identical. Prose must also be unable to rescue a missing code edge or suppress a complete one.

### 4.3 Supported statement scopes

The candidate path may be in exactly one of:

- module-level straight-line statements; or
- one zero-argument synchronous `def main()` or `def main() -> None` plus one exact
  `if __name__ == "__main__": main()` call with no `else`.

For `main`, the return annotation is either absent or the exact AST name `None`; parameters, parameter
annotations, decorators, type comments, and every other function annotation are unsupported. No other
annotation is accepted in the chosen scope.

Imports and closed module constants may precede either scope. The walker does not inline any other
helper, lambda, class, decorator, generator, coroutine, closure, or callback. An unsupported helper is
ignored only when it is outside every tracked reader/test/sink/safeguard slice and cannot mutate a
tracked object. If it lies on such a slice, abstain with `interprocedural-call-unresolved`.

Within the chosen scope, tracked names are single-assignment. Identity alias assignments are allowed.
Tuple destructuring is allowed only for the exact two-name result target described below. Attribute,
subscript, augmented, starred, walrus, global, nonlocal, deletion, or rebinding stores that can touch a
tracked value abstain. More narrowly, any `global` or `nonlocal` node anywhere in `analysis.py` abstains
before scope selection. A function, async function, class, assignment, or import binding that shadows
`print`, `str`, `float`, `round`, `len`, `sum`, `min`, `max`, `open`, or `list` makes API resolution
ambiguous and abstains, whether or not the shadow appears on the eventual candidate slice. Control flow involving a tracked value abstains except for the exact CSV bucket
loop enumerated in section 5.3, the exact top-level `__main__` guard, and this one descriptive-loop
exception:

A `for` loop is `descriptive_loop` and permitted exactly when all three checks pass: (b) its iterable and
body only read tracked values, with constant strings permitted alongside them in the iterable, and do
not write a tracked name; (c) every name bound by its target is absent from both test-argument backward
slices; and (d) every call on a tracked Series/array or reduction result is one of `V.mean()`, `V.std()`,
`V.std(ddof=1)`, `V.median()`, `V.min()`, `V.max()`, `V.count()`, `V.sum()`, unshadowed `len(V)`,
unshadowed `sum(V)`, unshadowed `min(V)`, unshadowed `max(V)`, or unshadowed
`round(X)`/`round(X, INTEGER_LITERAL)` where `X` is one of those scalar reduction results. Each reduction result must flow
exclusively through `print`, `str.format`, f-string construction, or `BinOp` arithmetic that feeds
builtin `print`, and never into a store that reaches either test-argument backward slice. The loop has no
`else`, `break`, `continue`, nested control flow, comprehension, await/yield, write to a tracked name,
mutating call, or other call. Source order relative to the candidate test is irrelevant. Failure of (b),
(c), or (d) returns `unsupported:unsupported-control-flow-on-path`. This exception supplies no Finding
evidence.

### 4.4 Normative dataflow terms

These definitions control every later use of the terms:

- **Authorized reader definition:** the one assignment or exact bucket-loop definition produced by a
  section-5.3 reader whose statically evaluated input path byte-equals the contract
  `material_input_path`.
- **Reader component:** the directed def-use component rooted at the authorized reader definition. It
  contains that root and every definition, receiver use, positional or keyword argument use, return
  definition, mutation, test, and output-sink use transitively reachable from it in the chosen scope,
  including nodes produced by unsupported calls. Source-text resemblance and shared variable spelling
  without a def-use edge do not join a component.
- **Tracked:** the authorized reader definition; every value in its reader component; the registered
  test and its statistic/p-result definitions; and values transitively derived from those definitions.
  Contract constants and unrelated output-path constants are not tracked merely because they are in
  scope.
- **May write:** an AST `Store` or `Del` to a tracked name, attribute, or subscript; an augmented or
  walrus assignment rooted at a tracked value; or passing a mutable tracked value as receiver or
  argument to a call that is not explicitly classified as read-only by sections 5.3 through 5.7.
  Inability to prove read-only behavior is `may write`.
- **Identity alias:** exactly `NEW = OLD`, where both are `Name` nodes, `OLD` is tracked, `NEW` has no
  other definition, and the edge is acyclic. `df.copy()`, `.view()`, slicing, constructors, casts,
  destructuring, and attribute/subscript extraction are not identity aliases.
- **P-derived:** reachable from the registered call's p-result definition solely through identity
  aliases and the exact payload wrappers in section 5.7. A constant string surrounding a formatted
  expression is not read and is not itself p-derived.
- **Safe path:** a nonempty UTF-8 string using `/` separators, with no NUL or backslash, no leading or
  trailing slash, and no empty, `.` or `..` segment. Its byte sequence after the closed evaluator—not a
  basename, normalized spelling, or case fold—is compared with the contract path.
- **Relevant:** a node in the chosen scope that is on a forward or backward path among the authorized
  reader, its component, the candidate test, the p-result, and an output sink; may write a tracked value;
  is any accepted reader; or is a registered/unregistered call that consumes the reader component and
  can reach an output sink. Other nodes cannot create evidence or suppress this candidate.

## 5. Closed API and expression allowlists

Anything not enumerated here is not “close enough.” If it is on a required dataflow or can mutate a
tracked value, the result is abstention.

### 5.1 Import and callable resolution

Accepted positive import bindings are exactly:

```text
import pandas [as NAME]                         -> NAME.read_csv
import numpy [as NAME]                          -> NAME.genfromtxt
import csv [as NAME]                            -> NAME.DictReader
from pathlib import Path [as NAME]              -> NAME(path)
import pathlib [as NAME]                        -> NAME.Path(path)
from scipy import stats [as NAME]               -> NAME.ttest_ind / NAME.mannwhitneyu
import scipy.stats [as NAME]                    -> NAME.ttest_ind / NAME.mannwhitneyu
import scipy                                    -> scipy.stats.ttest_ind / scipy.stats.mannwhitneyu
from scipy.stats import ttest_ind [as NAME]     -> NAME
from scipy.stats import mannwhitneyu [as NAME]  -> NAME
```

The same exact SciPy forms resolve `ttest_rel` and `wilcoxon` as safeguard calls. Suppressor-only
statsmodels bindings are exactly:

```text
import statsmodels.formula.api as NAME                         -> NAME.mixedlm
import statsmodels.api as NAME                                 -> NAME.MixedLM / NAME.GEE
from statsmodels.formula.api import mixedlm [as NAME]          -> NAME
from statsmodels.regression.mixed_linear_model import MixedLM [as NAME] -> NAME
from statsmodels.genmod.generalized_estimating_equations import GEE [as NAME] -> NAME
```

Relative imports, star imports, `importlib`, `__import__`, `getattr`, callable assignment, monkeypatching,
or rebinding/deleting an accepted module, callable, or builtin used by the slice abstains. Unrelated
standard-library imports may coexist if they never enter or mutate a tracked slice.

### 5.2 Static path expressions

`PATH` in a reader or writer is accepted only when the AST constant evaluator resolves it to one safe
path as normatively defined in section 4.4, by these forms:

```text
"a/b.csv"
FINAL_NAME                         # one module-level assignment to an accepted path expression
Path("a/b.csv")
Path("a") / "b.csv"
Path("a") / "b" / "c.csv"
```

`Path` must resolve from the accepted pathlib import. Concatenation, f-strings, `os.path`, `__file__`,
`.parent`, `.resolve`, environment values, command-line arguments, functions, conditionals, and path
normalization calls are unsupported. The reader path after POSIX joining must be byte-identical to the
contract `material_input_path`; basename matching and suffix matching are forbidden.

For `FINAL_NAME`, the module-level right-hand side is one literal `Constant` only. A module-level
`Name`, `Call`, `BinOp`, f-string, collection, or other computed expression is not a closed module
constant and makes an otherwise selected `main` scope ambiguous. Direct reader/writer arguments may
still use the exact `Path(...)` and `/` forms above. Both accepted pathlib import forms resolve the same
exact established API identity; neither spelling is inferred from an identifier.

### 5.3 Reader allowlist

Exactly one authorized-path reader lineage is required. The accepted forms are:

| Reader ID | Exact AST form |
| --- | --- |
| `pandas_read_csv_v1` | `FRAME = PANDAS.read_csv(PATH)`; exactly one positional argument, no keywords |
| `numpy_genfromtxt_named_csv_v1` | `FRAME = NUMPY.genfromtxt(PATH, delimiter=",", names=True, dtype=None, encoding="utf-8")`; keyword set and values exact, order irrelevant, no other arguments |
| `csv_dictreader_materialized_v1` | one `with open(PATH, "r", encoding=ENC, newline="") as H:` or `with PATHOBJ.open("r", encoding=ENC, newline="") as H:`, containing `FRAME = list(CSV.DictReader(H))`; `ENC` is exactly `"utf-8"`, `"UTF-8"`, or `"ascii"`; `DictReader` has one positional argument and no keywords |
| `csv_dictreader_bucket_loop_v1` | the same exact handle and `CSV.DictReader(H)`, iterated once by the exact two-bucket loop below without materializing a separate frame |

For the bucket-loop form, the body is exactly one append statement after optional assignments that are
simple aliases of `ROW[GROUP]` and `CAST(ROW[VALUE])`:

```python
BUCKETS = {G0: [], G1: []}
for ROW in CSV.DictReader(H):
    BUCKETS[ROW[GROUP]].append(CAST(ROW[VALUE]))
LEFT = BUCKETS[G0]
RIGHT = BUCKETS[G1]
```

`CAST` is absent or the unshadowed builtin `float`. `GROUP`, `VALUE`, `G0`, and `G1` are direct string
literals or closed module string constants. Dictionary keys must be exactly the two CSV group-domain
values. No `DictReader` dialect, delimiter, rest key/value, header override, row mutation, condition,
exception handler, or additional loop body is accepted.

`csv.reader`, pandas aliases such as `read_table`, NumPy `loadtxt`, Arrow/Polars/Dask readers, database
reads, H5AD reads, and custom wrappers are outside this first slice and abstain.

The walker performs a complete census of the chosen scope before selecting a candidate. There must be
exactly one call matching any accepted reader form, and it must be the authorized reader definition.
Any second accepted reader call—whether it uses the same path, a different path, or an unresolved
path—causes `unsupported:additional-accepted-reader-present`. Both registered test-argument backward
slices must terminate at this single definition; a slice rooted at any other definition causes
`unsupported:test-operands-not-from-authorized-reader`. Thus a correct per-unit summary loaded from a
second CSV cannot be mistaken for row-wise use of the authorized CSV.

### 5.4 Row selection and column projection allowlist

Both test arguments must resolve to different names, each assigned by one accepted selection whose
receiver is tracked in the authorized reader component. Parsing this selection shape does not erase an
intervening aggregation or transform; that node stays on the backward slice for section 6.3 step 17.
Each selection uses the contract group column `GROUP`, one of the two exact CSV group values, and the
same projected `VALUE` header. `VALUE` must exist and differ from `GROUP` and the authorized unit header.

Accepted pandas forms are exactly:

```python
LEFT = FRAME.loc[FRAME[GROUP] == G0, VALUE]
RIGHT = FRAME.loc[FRAME[GROUP] == G1, VALUE]

LEFT = FRAME[FRAME[GROUP] == G0][VALUE]
RIGHT = FRAME[FRAME[GROUP] == G1][VALUE]

LEFT = FRAME.query(QUERY0)[VALUE]
RIGHT = FRAME.query(QUERY1)[VALUE]

GROUPED = FRAME.groupby(GROUP)
LEFT = GROUPED.get_group(G0)[VALUE]
RIGHT = GROUPED.get_group(G1)[VALUE]
```

For `.loc`, the slice is one two-element tuple and the mask is exactly one `Eq` comparison. Boolean-mask
form has exactly the displayed two subscripts. `groupby` and `get_group` have the displayed positional
arguments and no keywords. `QUERY0`/`QUERY1` are direct literals matching the exact ASCII regex
`\A(?P<header>[A-Za-z_][A-Za-z0-9_]*) == (?P<quote>['\"])(?P<value>[A-Za-z0-9_.-]+)(?P=quote)\Z`;
the captured header and value must equal the contract group header and one complete-domain CSV value.
No backticks, escapes, interpolation, `@` variables, conjunctions, or method calls are accepted.

The accepted NumPy named-array form is exactly:

```python
LEFT = FRAME[FRAME[GROUP] == G0][VALUE]
RIGHT = FRAME[FRAME[GROUP] == G1][VALUE]
```

The accepted materialized `csv.DictReader` form is exactly two list comprehensions:

```python
LEFT = [CAST(ROW[VALUE]) for ROW in FRAME if ROW[GROUP] == G0]
RIGHT = [CAST(ROW[VALUE]) for ROW in FRAME if ROW[GROUP] == G1]
```

Each comprehension has one non-async generator, one equality filter, no nested generator, and no other
condition. `CAST` is absent or builtin `float`. The bucket-loop reader already produces the accepted
operands and needs no second selection.

Identity aliases of `FRAME`, `LEFT`, or `RIGHT` are accepted if single-assignment and acyclic. `.values`,
`.to_numpy`, `.dropna`, `.fillna`, `.astype`, `.iloc`, `.xs`, `isin`, inequality, sorting, slicing,
sampling, index operations, multi-condition masks, and any other transform are unsupported. In
particular, row dropping cannot be inferred harmless from the CSV; it abstains.

After steps 15 and 17 prove that no aggregation, copy, transform, or unknown node intervenes, the code
check establishes that each operand is an unmodified direct row selection from the authorized reader
definition, the predicates name the same contract group column, and their two byte-exact equality
literals are the two different complete-domain CSV values. Under the registered
pandas/NumPy/DictReader selection semantics this code structure partitions the authorized reader's rows.
The controller-owned CSV scan supplies the corresponding positive group counts and their sum `N_csv`;
those counts are structured corroboration and fact fields, not by themselves evidence about what the
code passed to the test.

### 5.5 Registered row-independent tests

The positive test registry is exactly the existing group-procedure subset:

| Procedure ID | Exact call |
| --- | --- |
| `scipy.stats.ttest_ind` | two positional operand names; optional sole keyword `equal_var=True` or `equal_var=False` |
| `scipy.stats.mannwhitneyu` | two positional operand names; optional sole keyword `alternative` with literal `"two-sided"`, `"less"`, or `"greater"` |

No `*args`, `**kwargs`, axis, NaN, trimming, permutation, method, keep-dimension, or other keyword is
accepted. For `ttest_ind`, missing or `equal_var=True` records variant `student`; `False` records
`welch`. Both procedures are treated only as established row-independent two-sample API identities; no
numeric result is recomputed and no claim is made about distributional assumptions.

The call target is exactly one of:

```python
RESULT = TEST(LEFT, RIGHT)
T_VALUE, P_VALUE = TEST(LEFT, RIGHT)
```

For the name target, the p-result token is `RESULT.pvalue` or `RESULT[1]`. For two-name destructuring,
the second name is the p-result token under the registered API return contract. Any other target shape,
more than one raw-row candidate, same operand on both sides, or unresolved callable abstains.

### 5.6 Aggregation and dependence-aware guard registry

The walker labels a node `row_reducing_aggregation` when a tracked reader-derived value reaches any of
these exact APIs:

```text
pandas GroupBy methods:
  agg aggregate mean median sum first last min max count size nunique prod std var sem quantile
pandas frame/series methods:
  mean median sum min max count nunique prod std var sem quantile pivot_table
pandas Resampler terminal methods:
  agg aggregate mean median sum first last min max count size nunique prod std var sem quantile
numpy functions:
  mean nanmean median nanmedian sum nansum average min nanmin max nanmax std nanstd var nanvar
statistics functions:
  mean fmean median median_low median_high
builtin:
  sum
```

For pandas, the receiver must be tracked, or the call must receive a tracked value. A `groupby` followed
only by `get_group` is the accepted selection form and is not aggregation. The registry asymmetries are
normative:

- `GroupBy.mean` and the other listed `GroupBy` reducers are in-registry aggregations;
- `Series.mean`/`DataFrame.mean` and every other listed frame/series reducer are in-registry
  aggregations, including when used only descriptively after the candidate test;
- `pivot_table` is an in-registry aggregation, while `pivot` is an out-of-registry transform and causes
  `unsupported:unrecognized-call-on-path` whenever it consumes the reader component;
- `resample` without a listed terminal is out-of-registry and abstains; a listed Resampler terminal is
  an in-registry aggregation; and
- `rolling` and `expanding`, alone or followed by any method, are out-of-registry and abstain whenever
  they consume the reader component.

None of these operations is pass-through by omission. A
`drop_duplicates` call is a dependence safeguard only when its literal `subset` is the authorized unit
header or a literal list/tuple containing that header; any dynamic or absent subset on a candidate path
is unsupported.

The walker also recognizes a per-unit reduction loop only in this closed shape: a dictionary is keyed by
`ROW[UNIT]`; every source row appends one `ROW[VALUE]`; a later comprehension or loop emits one scalar per
dictionary key through one listed reduction. The unit key must be the contract unit header, and the
resulting reduced sequence must feed a registered test. Any other loop on a candidate operand path is
unsupported, not inferred as safe.

The registered dependence-aware call set is exactly:

```text
scipy.stats.ttest_rel
scipy.stats.wilcoxon
statsmodels.formula.api.mixedlm
statsmodels.api.MixedLM
statsmodels.regression.mixed_linear_model.MixedLM
statsmodels.api.GEE
statsmodels.genmod.generalized_estimating_equations.GEE
```

For the four registered `MixedLM`/`GEE` class identities, an exact class root followed by any attribute
chain remains the same dependence-aware guard. Thus constructors, `.from_formula`, `.fit`, and any other
statically resolved class-rooted method suppress; the resolver does not require a method-name allowlist.
An instance `.fit()` is associated only when the constructor assignment is direct and
single-assignment, but constructor presence alone is already enough to suppress. A user-defined class
or unrelated API whose final identifier merely resembles `MixedLM` or `GEE` is not a hit.

Outside a loop, `descriptive_output_call` is registered as non-suppressing exactly when it occurs after
the candidate test, consumes only `LEFT` or `RIGHT`, is unshadowed `len(V)`, `V.mean()`, or
`V.std(ddof=1)`, and its scalar return reaches only builtin `print` through arithmetic or an f-string and
never reaches any test or mutation. This closed exception accounts for straight-line descriptive output;
it supplies no evidence. It does not extend the stricter loop-body call list in section 4.3.

The only component-consuming calls classified as non-suppressing are the accepted reader/selection/test
calls, `descriptive_output_call`, the accepted output sinks and payload wrappers in section 5.7, and calls inside
a `descriptive_loop` that satisfies every section-4.3 condition. Everything else is registered
aggregation/dependence counterevidence or an unregistered call.

The following code facts force abstention:

1. any registered aggregation, `drop_duplicates` safeguard, or dependence-aware call lies on either
   reader-to-test-argument backward slice;
2. any registered dependence-aware call consumes a value from the same authorized reader component,
   even on a sibling branch, or any unregistered call consumes that component (or a frame derived from
   it) and its return/attribute result reaches an accepted output sink;
3. any second registered two-sample test consumes an aggregated value from the same reader component,
   or any unregistered test-like call consumes a reader-component value and reaches an accepted output
   sink. “Test-like” is not inferred from a name: this second clause is the general unregistered-call
   rule in item 2 and therefore covers `pingouin`, `pymer4`, `bambi`, `linearmodels`, a custom
   cluster-bootstrap helper, `scipy.stats.ttest_1samp`, `f_oneway`, `kruskal`, and `linregress` without
   adding any of them as positive APIs;
4. any mutation of the reader frame, accepted operand, group column, value column, or unit column occurs
   before the candidate test; or
5. the walker cannot resolve whether a call or mutation lies on one of those paths.

Descriptive aggregation after the candidate test does not suppress merely because it reads `LEFT` or
`RIGHT`, provided its result cannot reach a test argument and it cannot mutate a tracked value. This is
necessary for P2's straight-line printed group means. Loop bodies remain governed by the narrower
section-4.3 list. Such descriptive calls do not become evidence.

No prose can override these facts. A printed “primary,” “sensitivity,” “do not cite,” or “exploratory”
label is ignored. Conversely, a recognized mixed model or unit aggregation suppresses without requiring
any explanatory comment.

### 5.7 Result output sinks

At least one p-result token must reach one accepted output sink through a finite forward def-use slice.
One shared structural sink registry serves both this p-result check and section-5.6 rule 2. Its exact
rows are:

```text
p-result eligible:
  print(PAYLOAD, ...)
  OUTPUT_PATH.write_text(PAYLOAD, encoding="utf-8")
  HANDLE.write(PAYLOAD) inside with open/Path.open(OUTPUT_PATH, "w" or "wt", encoding="utf-8", newline absent or literal "")

rule-2 guard terminal only; p_result_eligible=false:
  COMPONENT.to_csv(OUTPUT_PATH)
  NUMPY.savetxt(OUTPUT_PATH, COMPONENT)
  JSON.dump(COMPONENT, HANDLE) inside the exact bounded write-handle context above
```

All calls have exactly the displayed positional arguments and no unlisted keywords. `OUTPUT_PATH` is
one safe static path. `NUMPY` and `JSON` must resolve through exact imports to `numpy` and `json`.
The last three rows only establish that an unregistered reader-component consumer reaches a file
terminal; they cannot satisfy `result_output_sink`, even if a p-derived value happens to occupy their
component slot. This explicit eligibility bit prevents the B2 guard fix from widening conviction.

For `print`, `sep` and `end` may be literal strings; `file`, star arguments, and dynamic keywords are not
accepted. `PAYLOAD` may be the p-result itself, an identity alias, `str(P)`, `float(P)`, `round(P,
INTEGER_LITERAL)`, an f-string containing a formatted p-derived expression, or a `.format` call whose
positional argument is p-derived. Constant wording is ignored. Arithmetic, comparison, conditional
formatting, helper calls, logger calls, serialization libraries, and unknown methods on the p-result
slice abstain.

For file sinks, `OUTPUT_PATH` uses the path evaluator in section 5.2 and must be a safe path under
section 4.4; no report content or extension is inspected. The output bytes need not exist in the
snapshot because the code is not executed. An assignment is “used in output” only if this exact def-use
trace reaches one of the three sinks. Assignment alone is not a sink.

Multiple p-result-eligible sinks for the same p-token are permitted and sorted by source span. More than one
different candidate test reaching sinks, a p-token with both accepted and unrecognized sink consumers,
or an unresolved output path abstains.

## 6. Candidate-scoped AST algorithm

### 6.1 Why a new narrow walker

Do not extend either existing dependence analyzer. The v1 analyzer explicitly rejects every pandas
import as `pandas-frame-model` (`src/sc_referee/dependence_recognition/python_analyzer.py:810-875`). The
v2 analyzer has useful AST utilities but its pandas route requires one whole-script reader, selection,
writer, package, and partition grammar (`src/sc_referee/dependence_recognition_v2/python_analyzer.py:1333-1435`,
`:1870-2008`, `:4913-5335`). The K history shows that unrelated helpers and imports become global walls
before the scientifically relevant path is reached
(`docs/implementation/RECALL-RECON-2026-08-21.md:201-205`).

Implement a new narrow walker over the existing `parser:python-ast-tokenize` bytes. Reuse guarded parsing,
AST/source-span helpers, stable token/digest conventions, import qualification patterns, and resource
ceilings where they fit. Do not reuse v1/v2 certificates, their hidden authority locks, report writer
selection, whole-module bans, or qualification records.

### 6.2 Graph labels

Each tracked definition has exactly one immutable label:

```text
reader(path, api)
identity(parent)
row_selection(parent, group_column, group_value, value_column, selection_kind)
aggregation(parent, api, grouping_columns)
dependence_guard(parent_set, api)
row_independent_test(left, right, api, variant)
test_p_result(test)
output_sink(parent, sink_kind)
unknown(parent_set, syntax_kind)
```

Edges point from definitions to uses. Source ordering is `(lineno, col_offset, end_lineno,
end_col_offset)`; ties are impossible for distinct AST nodes and otherwise break by canonical AST dump.
Tracked names cannot be rebound. The walker keeps an explicit set of mutations and unknown calls that
read or may write each tracked definition. Every simple def-use path may contain at most 16 labeled
definition nodes, inclusive of its first and last labeled nodes. A path with 17 or more, or a cycle,
abstains with `unsupported:dataflow-definition-ceiling-exceeded`; this ceiling applies independently to
reader-to-operand, reader-component sibling, and p-result-to-output paths.

### 6.3 Ordered Finding predicate

A builder must run these checks in this order and may not skip a failed earlier check:

1. **Authority:** verify exactly one complete profile `1.1.0` authority and current contract chain. Input:
   shared Answer/assertion records. Failure: `verified-contract-authority-unavailable`.
2. **Material identity:** require exactly one selected material input whose path and digest equal the
   authority snapshot. Input: frozen material record and bytes. Failure:
   `frozen-authority-material-mismatch`.
3. **CSV completion:** run the unchanged bounded CSV parser over every byte. Input: CSV and authority
   columns. Failure: the existing exact CSV reason.
4. **Repeated unit:** require `N_csv > U`, `R >= 1`, `M >= 2`. `N_csv == U` is
   `not_applicable:no-repeated-authorized-unit`.
5. **D1':** complete every candidate/distinct/tuple/pair scan. Any unique nonindex composite causes
   `unsupported:unique-nonindex-authorized-unit-composite-key-possible`.
6. **Two-group domain:** require exactly two complete-domain group values. Failure:
   `unsupported:authorized-group-domain-not-exactly-two`.
7. **Source identity/naming gate:** select exact root `analysis.py`, parser identity, full digest, AST and
   resource bounds, and unique snapshot identity path. Failure:
   `unsupported:analysis-source-envelope-unavailable`. This is an admission gate, not evidence.
8. **Alternate-analysis exclusion:** inventory all project paths, refuse every `.ipynb`/`.R` file, and
   complete the import-only scan of every other `.py` under section 4.1. Failure is that section's exact
   alternate-file, statistics-import, or incomplete-scan reason.
9. **Prose exclusion:** remove docstring nodes and establish that the adapter has requested no prose
   document or token stream. Internal invariant failure: `unsupported:prose-free-source-view-unavailable`.
10. **Imports/no-shadow:** resolve only section 5.1 names and prove no relevant rebinding or local module
    shadow. Failure: `unsupported:api-resolution-ambiguous`.
11. **Scope selection:** choose module body or the one exact annotated-or-unannotated `main` body.
    Failure: `unsupported:analysis-scope-ambiguous`.
12. **Reader census:** census every accepted reader call in scope; require exactly one and require its
    static path to byte-equal the authority path. Failure:
    `unsupported:authorized-reader-lineage-unavailable` or
    `unsupported:additional-accepted-reader-present`.
13. **Def-use graph:** build all labels and relevant mutation/unknown edges in the chosen scope. Any
    unbounded resource, 17-node path, cycle, or ambiguous store fails its exact section-6.2 reason or
    `unsupported:code-dataflow-graph-incomplete`.
14. **Selections:** find exactly two accepted same-value-column selections with distinct exact group
    values. Failure: `unsupported:two-group-row-selection-unavailable`.
15. **Authorized-reader provenance:** walk both selection/test-argument backward slices and require each
    to terminate at the single authorized reader definition, with no intervening second reader or
    disconnected root. Preserve every classified aggregation, copy, transformation, and unknown node
    for ordered counterevidence at step 17; their presence does not change the root-provenance identity.
    Failure: `unsupported:test-operands-not-from-authorized-reader`. Input: AST definitions and static
    reader path, not CSV counts.
16. **Test:** find exactly one registered raw-row test over the two selection definitions and validate
    its signature/variant/target. Failure: `unsupported:rowwise-two-sample-test-unavailable` or
    `unsupported:multiple-rowwise-test-candidates`.
17. **Direct-path counterevidence:** walk both test arguments backward to the reader. Any aggregation,
    safeguard, unknown call, control edge, mutation, or unsupported construct fails with the exact first
    source-ordered reason from section 6.4.
18. **Component counterevidence:** scan the reader component for registered dependence-aware calls,
    second tests over aggregated values, and every unregistered component-consuming call that reaches an
    output sink. Presence fails `unsupported:dependence-aware-sibling-present`,
    `unsupported:aggregated-sibling-test-present`, or
    `unsupported:unregistered-component-call-reaches-output`.
19. **Control-flow exceptions:** validate every tracked loop against the exact bucket-loop or
    descriptive-loop grammar. Failure: `unsupported:unsupported-control-flow-on-path`.
20. **Output sink:** identify the registered call's p-result and require at least one complete accepted
    forward path to an output sink. Failure: `unsupported:test-result-output-sink-unavailable`.
21. **Uniqueness:** require one reader, one value column, one group partition, one raw candidate test, and
    one canonical output-sink set. Conflicts fail `unsupported:code-lineage-nonunique`.
22. **Fact:** construct the exact typed projection in section 7 and recompute its digest. Any missing or
    extra field abstains.
23. **Observation:** emit one `static_source` observation with all four role bindings, code spans, CSV
    SourceRef, full-digest scope edge, and `question_only` ceiling.
24. **Generic conflict:** the existing detector may form an evaluation candidate only if its ten finite
    checks and every receipt complete. No code adapter can bypass the detector.
25. **Admission:** before a fresh accepted qualification and replacement dependence pin match the exact
    check, adapter, grammar, fact profile, wording profile, metric set, threshold policy, and binding,
    production Findings remain zero.

### 6.4 Closed abstention precedence within code paths

The ordered predicate in section 6.3 dominates this path-local earliest-span rule. A failed earlier
predicate step is reported before any later-step refusal even when the later refusal has an earlier
physical source span. Code-slice 1.1 adds only the bounded exceptions and helper codes in its accepted
delta design; this 1.0 burned-history grammar is otherwise unchanged.

When more than one path-local refusal applies, report exactly the earliest source span, breaking equal
spans by this rank:

1. `tracked-value-mutation`
2. `dynamic-or-rebound-api`
3. `dependence-aware-operator-on-path`
4. `aggregation-on-test-operand-path`
5. `unsupported-control-flow-on-path`
6. `interprocedural-call-unresolved`
7. `unregistered-component-call-reaches-output`
8. `unrecognized-call-on-path`
9. `unsupported-expression-on-path`

Reasons are coverage records and MaterialQuestions, never Findings. An exception or internal mismatch
returns `unsupported:code-csv-dependence-inspection-exception`; it may not fall back to prose or a partial
graph.

## 7. Typed fact and observation projection

The applicable adapter emits exactly one omitted-when-absent `row_entry_evidence` projection with this
closed schema:

```json
{
  "profile": "code_csv_row_entry_evidence_v1",
  "material_input_path": "string",
  "material_input_content_digest": "sha256:...",
  "material_file_ref": {"record_type": "file_record", "record_id": "..."},
  "authorized_unit_column": "string",
  "group_contrast_column": "string",
  "data_row_count": 1,
  "distinct_unit_count": 1,
  "repeated_unit_count": 1,
  "maximum_unit_multiplicity": 1,
  "composite_key_scan_complete": true,
  "composite_key_candidate_columns": ["sorted strings"],
  "distinct_count_excluded_columns": ["sorted strings"],
  "within_unit_index_columns": ["sorted strings"],
  "unique_pair_within_unit_index_columns": ["sorted strings"],
  "unique_nonindex_authorized_unit_composite_columns": [],
  "analysis_path": "analysis.py",
  "analysis_content_digest": "sha256:...",
  "analysis_file_ref": {"record_type": "file_record", "record_id": "..."},
  "alternate_analysis_file_scan_complete": true,
  "other_python_statistics_import_scan_complete": true,
  "reader_api": "one section-5.3 reader ID",
  "accepted_reader_count": 1,
  "all_test_operand_paths_rooted_in_authorized_reader": true,
  "selection_kinds": ["left kind", "right kind"],
  "value_column": "exact header",
  "group_values": ["source-order left value", "source-order right value"],
  "group_row_counts": [1, 1],
  "all_csv_rows_partitioned": true,
  "procedure_id": "scipy.stats.ttest_ind or scipy.stats.mannwhitneyu",
  "procedure_variant": "student, welch, or mannwhitneyu",
  "output_sink_kinds": ["sorted unique output-sink kinds"],
  "dataflow_max_definition_nodes": 1,
  "descriptive_loop_count": 0,
  "aggregation_path_scan_complete": true,
  "dependence_guard_scan_complete": true,
  "unsupported_call_scan_complete": true,
  "unregistered_output_call_scan_complete": true,
  "authority_binding_digest": "sha256:...",
  "code_evidence_spans": [
    {"role": "reader|left_selection|right_selection|procedure|output_sink", "path": "analysis.py", "start_line": 1, "end_line": 1, "start_column": 1, "end_column": 1}
  ],
  "fact_digest": "sha256:canonical-json-excluding-fact-digest-v1"
}
```

Integer examples above express types, not minimum values. Actual invariants are: `data_row_count >
distinct_unit_count >= 2`; repeated and maximum counts agree with the CSV; both group counts are
positive and sum to `data_row_count`; list fields are duplicate-free; evidence roles occur once except
one or more output sinks; `accepted_reader_count == 1`; every operand provenance flag and scan-complete
flag is true; `1 <= dataflow_max_definition_nodes <= 16`; all spans lie inside the exact analysis bytes;
and the fact digest is the semantic
digest of the projection with `fact_digest` omitted.

Integration stores this fact only as
`x-code-csv-row-entry-evidence` plus `x-code-csv-row-entry-evidence-digest` on the `observed` static
assertion. It must not also publish the old `x-report-csv-row-entry-evidence` extension. The CSV SourceRef
is the full-file reference; code SourceRefs are exact AST spans. No report SourceRef is present.

## 8. Bounded Finding wording

The contract-contradiction form is retained, with the evidence subject changed from report to code.

Exact title:

> Analysis code contradicts the frozen one-row-per-authorized-unit requirement

Exact summary template:

> The frozen requirement for `{CSV_PATH}` permits one analyzed row per `{UNIT_COLUMN}`. In
> `analysis.py`, the two checked arguments to `{PROCEDURE_ID}` are direct `{GROUP_COLUMN}` row
> selections from that CSV and jointly cover all `{N_csv}` rows; the table contains `{U}` distinct
> `{UNIT_COLUMN}` values, `{R}` of them repeat, and the maximum multiplicity is `{M}`. The static
> contract representation and the checked code/dataflow representation therefore conflict. The
> contract author may be wrong, and static source does not establish execution, statistical invalidity,
> numerical impact, bias direction, or the adequacy of unsupported or uninspected analysis paths.

Slots are limited to normalized authority path/header values, the registered API ID, and checked
integers. Group values, response values, variable names, comments, docstrings, printed text, report text,
and model-generated wording are never interpolated. The Finding profile digest covers the exact title,
summary, slot schema, severity rationale, non-inferences, and next action.

The Finding is not titled “pseudoreplication,” does not say the scientific analysis is wrong, and does
not claim the code ran. Its demonstrated conflict is only: the human froze one row per authorized unit,
while one exact static code path supplies every selected CSV row to an established row-independent test
and exposes its p-result to an output sink. Reaching an output sink is not evidence that this result was
selected, primary, reported, interpreted, relied upon, or claimed; the role is therefore
`result_output_sink`, never `selected_result_sink`, and the Finding wording makes none of those
inferences.

## 9. Burned-envelope development check

These six cases are opened and contribute no blind N. The expected classifications below use only
`analysis.py`, the project file inventory and other-Python import nodes, contract records, and CSV bytes;
comments, docstrings, reports, and printed literals are ignored. Each project also has `make_data.py`;
the import-only scan finds no section-4.1 registered
statistics prefix in those files, and none of the six projects contains `.ipynb` or `.R`, so the
alternate-analysis gate passes for all six.

| Case / role | Structured CSV fact | Exact code path or guard | Expected code-slice result |
| --- | --- | --- | --- |
| `45dcad2f6496a0fd5778` / opened P1 | `N=96`, `U=8`; D1' has no candidate column | `pd.read_csv` line 11; exact `.loc` selections lines 14-15; the loop at lines 18-23 reads only `control`/`fluoxetine`, constant labels, and allowed mean/std reductions whose values feed print; `stats.ttest_ind` line 26; p-result print line 29 (`evaluation/development/blind-envelope-2026-08-21/cases/45dcad2f6496a0fd5778/project/analysis.py:7-29`) | **Applicable evaluation candidate.** Correct positive. The pre-test descriptive loop passes revised (b)-(d) and supplies no evidence. |
| `88e59abe85a8eea2b8cd` / opened P2 | `N=60`, `U=10`; candidate `collar_position` has six values and is a regular within-unit index | reader line 11; `.loc` selections lines 14-15; test line 18; p-result print line 28 (`evaluation/development/blind-envelope-2026-08-21/cases/88e59abe85a8eea2b8cd/project/analysis.py:7-28`) | **Applicable evaluation candidate.** Correct positive. Later descriptive means do not feed a test. |
| `0f721a41bac71a461dd2` / opened P3 | `N=64`, `U=16`; candidate `hatch_date` has nine values, is not a within-unit index, and does not form unique unit pairs | reader line 7; `.loc` selections lines 10-11; test line 14; the loop at lines 18-23 reads only `supplemented`/`control`, constant labels, and allowed len/mean/std reductions whose values feed print; p-result print line 28 (`evaluation/development/blind-envelope-2026-08-21/cases/0f721a41bac71a461dd2/project/analysis.py:3-28`) | **Applicable evaluation candidate.** Correct positive. The descriptive loop passes revised (b)-(d) and supplies no evidence. |
| `5994e65153b07855b07c` / opened N1 | `N=60`, `U=12`; `sample_replicate` is a within-unit index; `harvest_viability_pct` is nonindex but its unit pairs repeat | the tested frame is built by `df.groupby(["fermenter_run", "feed_strategy"]).agg(... "mean" ...)` lines 41-45; selections lines 56-59 and test line 84 consume that aggregation (`evaluation/development/blind-envelope-2026-08-21/cases/5994e65153b07855b07c/project/analysis.py:16-21`, `:41-45`, `:56-59`, `:84-95`) | **Abstain:** `aggregation-on-test-operand-path`. Correct negative. |
| `e804a86a1e05b781f292` / opened N2 | `N=24`, `U=24` | the complete CSV gate stops before source analysis with `no-repeated-authorized-unit`; code also computes `df["hive_label"].duplicated()` and raises on duplicates (`evaluation/development/blind-envelope-2026-08-21/cases/e804a86a1e05b781f292/project/analysis.py:15-29`) | **Not applicable:** `no-repeated-authorized-unit`. Correct negative. The `os.path.join` reader path is never evaluated after this ordered gate. |
| `11af5bb3f9b7e8e0b293` / opened N3 | `N=70`, `U=14`; `nubbin_code` is a regular five-level within-unit index | after reader line 25, line 29 stores `pd.Categorical(...)` into the tracked group-column subscript; later code also has `smf.mixedlm` lines 69-74 and an aggregated second t-test lines 101-118 (`evaluation/development/blind-envelope-2026-08-21/cases/11af5bb3f9b7e8e0b293/project/analysis.py:17-31`, `:69-75`, `:101-122`, `:144-149`) | **Abstain:** first source-ordered reason `tracked-value-mutation` at line 29. Dependence-aware and aggregated-sibling guards remain later independent reasons. Correct negative. |

Development expectation under the literal reviewed grammar: **3/3** opened positives become evaluation
candidates, 0/3 opened negatives do, all six emit zero pre-qualification Findings, and every
audit/replay projection is equal. A positive miss or negative candidate is a build failure; it is not
permission to widen the loop API or read prose.

## 10. Batch-K development check

The four K `ttest_ind` positives remain label-visible development cases. Their CSVs continue to pass D1'
exactly as documented in the burned report design. Their analysis programs, however, all place required
reader, partition, test, or sink edges across multiple custom helpers:

| K case | First required unsupported code edge | Independent blocker even if bounded inlining existed | Expected result |
| --- | --- | --- | --- |
| `0de3a6061d3bb4056306` | The original project has only `workflow/analysis.py`; after filename normalization, `read_measurements` returns the CSV rows, `flux_by_group` creates test operands, and `compose` owns the test/result while `main` owns the file sink (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/0de3a6061d3bb4056306/workflow/analysis.py:21-32`, `:49-58`, `:119-122`) | The bucket dictionary is a comprehension at line 29 rather than the exact two-key literal, and the test arguments at lines 56-58 are subscripts rather than operand names. | Normal path: abstain `analysis-source-envelope-unavailable`; normalized diagnostic: `interprocedural-call-unresolved` |
| `6b2da0c7167dbba3738f` | The original project has only `workflow/analysis.py`; after filename normalization, `read_table` supplies rows across a helper boundary before the in-main bucket loop (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/6b2da0c7167dbba3738f/workflow/analysis.py:23-25`, `:36-51`) | The selection uses `defaultdict(list)` and one loop that also mutates reactor sets and a counter at lines 39-46, outside the exact bucket-loop grammar. | Normal path: abstain `analysis-source-envelope-unavailable`; normalized diagnostic: `interprocedural-call-unresolved` |
| `e9e2718573bb47f7d17b` | The original project has only `workflow/analysis.py`; after filename normalization, `read_densities` owns reader/partition, `build_report` owns test, and `main` owns writer (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/e9e2718573bb47f7d17b/workflow/analysis.py:23-30`, `:49-58`, `:106-109`) | The reader-derived group key passes through `.strip()` at line 28 and operands pass through `np.array` at line 30; neither transform is registered. | Normal path: abstain `analysis-source-envelope-unavailable`; normalized diagnostic: `interprocedural-call-unresolved` |
| `3ae92d0bb421d6eee99e` | The original project has only `workflow/analysis.py`; after filename normalization, `read_records` and `flux_samples` construct operands across helper boundaries before the in-main test (`evaluation/development/dependence-growth-loop/batch-k2/authoring/cases/3ae92d0bb421d6eee99e/workflow/analysis.py:23-32`, `:45-56`) | The bucket form is `defaultdict(list)`, the group key uses `.strip()` at line 31, and the returned operands pass through `np.array` at line 32. | Normal path: abstain `analysis-source-envelope-unavailable`; normalized diagnostic: `interprocedural-call-unresolved` |

Therefore the frozen first-slice K expectation is 0/4 candidates. This is an honest coverage limit, not a
regression against a previously qualified capability: K's prior 3/4 result belonged to the now-withdrawn
report plane and produced zero production Findings. Interprocedural inlining is **deferred** from adapter
version `1.0.0`; that is a fixed decision, not an open builder choice. Even hypothetical bounded inlining
would leave all four cases abstaining on the independent constructs enumerated above.

The two K binomial cases remain outside the registered group-procedure set and abstain. No report bytes
are opened to establish that result.

## 11. Fresh sealed-envelope protocol

The burned prompt strings, case bytes, labels, and roles are forbidden as fresh evidence. Envelope 2
uses eight new scenarios, eight new prompts, eight new author sessions, and new opaque IDs: three
positives and five negatives.

### 11.1 Author constraints and isolation

- One independent prompt-author agent that has not seen this design, its allowlists, implementation,
  K code, burned code, detector output, or prior prompts writes all eight author prompts.
- Before that agent begins, the custodian freezes the complete prompt-author briefing as exact UTF-8
  bytes, records its byte length and SHA-256 digest, and handles it with the same no-normalization,
  change-burns-envelope rule as every authored prompt. The briefing's only code/platform constraint is
  the exact line `Each project must contain a single root analysis.py in Python.` followed by one LF. It does not require or
  name pandas, SciPy, wording, a code template, an accepted selection form, a suppressor, a variable
  name, a regex, or Finding text.
- Three positive prompts ask for a repeated-unit two-group analysis that passes row-level values to an
  independent two-sample test. Five negatives ask respectively for: unit aggregation before testing; a
  genuine one-row-per-unit table; a dependence-aware or aggregated alternative alongside a tempting
  raw-row comparison; a correct per-unit summary analysis loaded from a second CSV; and an off-registry
  dependence-aware primary analysis with an illustrative raw-row test. These are scientific behaviors,
  not lexical instructions.
- Eight fresh mutually isolated project-author sessions each receive one frozen prompt and the structured
  task/input/contract package. They do not see this design, K, burned cases, other projects, roles, or
  detector output.
- A fresh calibrated reviewer labels the frozen projects before detector execution under ADR-0067, with
  cross-model escalation only under that ADR's conditions.

### 11.2 Freeze chronology

1. Accept the ADR-0076 amendment and this design.
2. Build and review the exact implementation and all development/corpus gates without creating blind
   prompts.
3. Freeze the implementation closure: contract parser, preflight, exact CSV machinery, code walker,
   allowlists, adapter, fact and Finding profiles, detector/admission path, pin structure, tests,
   development expectations, threshold policy, scorer, and this protocol.
4. Freeze and digest the exact prompt-author briefing bytes, then commission the isolated prompt author.
   Freeze the eight prompt byte strings independently, their fixed ordering, author provenance, role map
   digest, and opaque case IDs before the builder or Fable reads prompt bytes or roles.
5. Freeze all eight new input packages (including the second-summary-CSV negative) and eight profile
   `1.1.0` authority records. Alex supplies or explicitly
   delegates the scientific authority values. Run `method-contract` before any analysis code exists;
   freeze every lock digest.
6. Release each prompt once to its isolated author. Freeze the returned project bytes immediately. A
   failed or unsupported result is retained as an envelope miss, not retried or rewritten.
7. Run nonexecuting intake only. No project-authored code runs, imports, or installs dependencies.
8. Freeze blind scientific labels and any required escalation before detector execution.
9. Run the frozen adapter once. Any positive miss or negative evaluation candidate burns the envelope;
   no code/grammar tuning is permitted.
10. If and only if the candidate run passes, derive the qualification, metric set, threshold record,
    Finding-profile binding, and replacement dependence pin deterministically. Alex separately accepts
    or rejects installation.
11. After accepted installation with no implementation change, run the ordinary reportless audit route
    and require exactly one Finding on each positive and none on each negative.
12. Replay each of the eight audit locks model-free and compare complete canonical detector-result, Finding, and
    coverage-record projections, sorted by stable record ID.

Any implementation, grammar, fact, wording, suppression, threshold, or admission change after author
briefing bytes, prompt bytes, or case bytes are visible burns the envelope and requires a wholly new
briefing and eight new prompts/cases. Environment
or dependency installation by an author is a protocol deviation and does not authorize execution.

### 11.3 Acceptance threshold

The fresh threshold remains:

- at least three adjudicated positive roots;
- `missed_roots == 0` and root recall `1.0`;
- exactly five blind negative controls for Envelope 2;
- completed-opportunity false-positive rate `0.0`;
- 3/3 positive normal-path Findings after promotion;
- 0/all fresh negative Findings (0/5 for Envelope 2);
- zero false Findings across the existing 108 blind cases, 155 regression cases, and all new negatives;
  and
- exact replay equality for all eight fresh cases.

No credit comes from the six opened burned cases or K.

## 12. Test plan

### 12.1 Prose prohibition

- Replace every report, Markdown, comment, docstring, heading, output label, exception message, variable
  name, and constant f-string text while preserving structural operands; require byte-identical
  normalized observations.
- Delete every report/Markdown file and omit `--report`; require unchanged dependence observations.
- Put every former admission, N form, path anchor, test result, suppressor, “primary,” and “sensitivity
  only” phrase in comments/docstrings/printed literals; prove none changes applicability.
- Remove one required AST/data/authority edge while adding persuasive prose; require abstention.
- Instrument `CodeCsvDependenceAdapter.inspect` and `analyze_code_csv_dataflow` in tests. Replace every
  Markdown/plain-text document with an object whose payload access raises immediately, prove the adapter
  reaches the dataflow entry exactly once using only `analysis.py` bytes, and require the test to fail on
  any prose-payload touch.
- Hold structural spans fixed while byte-mutating same-length docstrings, comments, standalone string
  literals, f-string/print labels, and require the typed dataflow observation to remain byte-identical.
  Hold `analysis.py` fixed while report/Markdown files are absent, present behind a payload tripwire, or
  replaced; require the selected code envelope and normalized scientific result to remain identical.

### 12.2 Authority and CSV

- Reuse all profile `1.1.0`, authority propagation, current-digest, path/header, cardinality, CSV boundary,
  multiplicity, D1', and label-collision tests from the report slice.
- Add exact two-group-domain tests: zero/one/two/three groups; blank group value; each group missing;
  selection labels swapped; one mismatched; duplicate labels; counts summing to `N_csv-1`, `N_csv`, and
  `N_csv+1`.
- Prove `N_csv==U` stops before any source path or API expression is interpreted.

### 12.3 Source, import, and path envelope

- Test strict UTF-8, parser identity/version/state, source/AST byte and node ceilings, exact root
  `analysis.py`, duplicates, full-digest scope proof, and snapshot drift.
- Add every case-folded `.ipynb`/`.R` suffix; every exact other-`.py` statistics import prefix; benign
  `make_data.py` imports; malformed, dynamic, relative, and over-budget other Python; and incomplete file
  inventory. Require the exact section-4.1 coverage code.
- One positive and one negative for every import form in section 5.1; star, relative, dynamic, callable
  alias, import rebinding, builtin shadowing, local module shadowing, and attribute monkeypatch negatives.
- One positive for every path form in section 5.2; negatives for basename-only match, case mismatch,
  absolute/parent traversal, `os.path`, `__file__`, f-string, concatenation, environment, and dynamic
  value.
- Module body, `def main()`, and `def main() -> None` positives; every other return annotation,
  parameter/annotation, `AnnAssign`, helper, decorator, async, nested function, class, lambda, alternate
  main guard, and relevant control-flow negatives.

### 12.4 Reader and selection matrices

- One positive and mutation-complete negatives for every reader row in section 5.3.
- A second accepted reader at the same, different, and dynamic path always abstains; each test-operand
  slice must terminate at the sole byte-exact authorized reader.
- Every pandas selection form, NumPy mask, CSV comprehension, and CSV bucket loop in both group orders.
- Mutate every operator, key, group value, projected column, receiver, arity, keyword, comprehension
  count, condition count, loop body, cast, and group domain; require the exact abstention.
- Prove aliases are single-assignment/cycle-free and all mutations/rebindings abstain.

### 12.5 Aggregation and safeguards

- One test for every exact aggregation API in section 5.6 on a test-argument path.
- GroupBy `get_group` remains allowed; every GroupBy reducer suppresses.
- Cover `Series`/`DataFrame` reducers, `pivot_table`, out-of-registry `pivot`, bare/terminal `resample`,
  and every `rolling`/`expanding` form at their exact in-registry/out-of-registry outcomes.
- `drop_duplicates` on the unit column suppresses; another literal column on the path is unsupported;
  dynamic/absent subset abstains.
- Exact per-unit reducer-loop positives for suppression and near-miss loops that abstain as unsupported.
- Every dependence-aware constructor/call form, direct and imported alias, on the same reader component.
- One sink-reaching unregistered call for each named off-registry package/example in section 5.6, a
  hand-rolled cluster-bootstrap helper, and an unknown receiver; all abstain without interpreting names.
- A correct second-CSV per-unit summary plus a tempting authorized raw test abstains at the second-reader
  census before either output is ranked.
- N3's mixed-model branch plus aggregated second test suppresses even though the raw test reaches print.
- Straight-line post-test `len`, `.mean()`, and `.std(ddof=1)` at the exact
  `descriptive_output_call` shape do not suppress; any other arity, method, consumer, or source order
  abstains.
- Descriptive-loop condition mutations cover before/after test equivalence, tracked/untracked iterable,
  constant-string labels, bound-name reuse, every exact reduction/signature and output-only flow, a store
  reaching a test slice, tracked mutation, nested flow, and unknown call. Require P1 and P3 to pass
  exactly as section 9 records.
- Unknown calls, mutation, control flow, or dynamic attributes before either test argument always abstain.

### 12.6 Test and sink matrices

- `ttest_ind` default/True/False and `mannwhitneyu` three allowed alternatives; mutate every disallowed
  argument and keyword.
- Result-name and two-name destructuring forms; `.pvalue`, `[1]`, and second tuple name.
- Every output sink and payload wrapper in section 5.7; paths with 1 and 16 labeled definitions pass and
  17 abstains under the normative section-6.2 ceiling.
- Exercise every row of the shared sink table twice where meaningful: p-result eligibility for the three
  eligible rows, and unregistered component-call reachability for all six rows. Assert that `.to_csv`,
  `numpy.savetxt`, and `json.dump` never establish `result_output_sink`.
- Result unused, statistic-only output, unrecognized logger, dynamic print target, file keyword,
  conflicting sinks, multiple raw tests, and aggregated sibling test negatives.

### 12.7 Facts, detector, and end to end

- Mutate/remove/add every fact field, count, span, role, digest, receipt, authority binding, parser
  identity, and scope edge; require no candidate.
- Prove the static assertion uses only `x-code-csv-row-entry-evidence`, semantic role `observed`, and
  evidence plane `static_source`.
- Prove the old report adapter, report fact/profile, report plane, old check `1.2.0`, old pin, burned
  qualification absence, and any stale identity cannot promote.
- Exact title/summary recomputation and slot-safety tests; no prose/group/response value interpolation.
- Run the six opened cases at the section-9 expectation—all three positives are candidates and all three
  negatives abstain—and replay identically.
- Run all four K t-test and two K binomial cases at the section-10 abstention expectations.
- Run the 108 blind and 155 regression cases with zero Findings from this adapter; report any case with
  valid new authority separately rather than treating missing authority as substantive specificity.
- Preserve complete-domain Finding behavior and every unrelated scientific-check identity not in the
  dependency closure.
- During the authorized build only, run `ruff check .`, `ruff format --check .`, `mypy src`, `pytest`,
  and `python scripts/validate_starter.py` as required by `AGENTS.md:46-54`.

## 13. File-by-file build list

Rough counts are inferred estimates, not changes made in this design task.

| File | Exact planned responsibility | Rough logical change |
| --- | --- | ---: |
| `src/sc_referee/scientific_checks/code_csv_dependence_dataflow.py` | New candidate-scoped AST walker, alternate-file/import scan, exact reader census and provenance, allowlists, graph labels, suppressor scan, output trace, source spans, and prose exclusion. | new, ~1,050 |
| `src/sc_referee/scientific_checks/code_csv_dependence_adapter.py` | Reuse verified authority and `_parse_csv`/D1'; select `analysis.py`; construct typed fact, receipts, roles, and static observation. | new, ~330 |
| `src/sc_referee/scientific_checks/report_csv_dependence_adapter.py` | No grammar change. Remains retained; only its existing authority/CSV helpers are imported. | 0 |
| `src/sc_referee/scientific_checks/profiles.py` | Check `1.3.0`; register only code adapter; static parser/plane/known gaps; report adapter retained but inactive. | +55 / -30 |
| `src/sc_referee/scientific_checks/integration.py` | Route `code_csv_row_entry_evidence_v1` to the code-specific assertion extensions; retain old report extension reader only for historical replay. | +30 / -5 |
| `src/sc_referee/detectors/bounded_code_csv_dependence_conflict.py` | New evaluation-only detector identity for this code lane; reuse the generic finite-check implementation without modifying its installed source bytes. | new, ~360 |
| `src/sc_referee/detectors/method_conflict_registry.py` | Dispatch the new detector and validate the frozen generic manifest through a construction-only binding projection; scheduling remains identity-local. | +65 |
| `src/sc_referee/detectors/method_conflict_finding.py` | New code fact validator and bounded contract-conflict wording/profile; retain old report profile for history. | +150 / -15 |
| `src/sc_referee/controller.py` | Accept the exact code Finding profile in the existing preflight/draft/admission path; do not require a selected report for this check. | +30 / -15 |
| `src/sc_referee/detectors/method_conflict_grant_pins.py` | Resolve active dependence Finding profile by exact code profile identity; no replacement pin before fresh qualification. | +20 / -10 |
| `src/sc_referee/resources/scientific-check-manifests-v1/registry.json` | Regenerate check/adapter/binding identities with static source/observed role and `production_finding_permitted=false`. | generated |
| `src/sc_referee/resources/capability-manifests-v1/detector-manifests.json` | Register the separate experimental code-lane detector while retaining the generic detector record and digest. | generated |
| `scripts/build_capability_source_manifests.py` | Deterministically generate the new detector manifest; do not rewrite the installed generic detector identity. | +65 |
| `tests/test_code_csv_dependence_dataflow.py` | Complete source/API/dataflow/alternate-file/reader/suppressor/output/prose mutation matrix. | new, ~1,600 |
| `tests/test_code_csv_dependence_adapter.py` | Authority/CSV/fact/role/scope/abstention adapter tests. | new, ~700 |
| `tests/test_scientific_check_integration.py` | Static fact extension and report-free normal integration. | +120 |
| `tests/test_method_contract_run.py` | Assert unchanged profile `1.1.0` authority works against check `1.3.0`; old locks stay replayable but ineligible. | +45 |
| `tests/test_installed_method_conflict_grants.py` | Old/stale pin and code-profile refusal until qualification. | +60 |
| `tests/test_production_finding_demonstration.py` | Preserve zero dependence Findings pre-promotion and unrelated demonstration behavior. | +30 |
| `tests/test_dependence_code_slice_development.py` | Six opened cases, four K t-tests, two K binomials, exact outcomes, report mutation independence, replay. | new, ~350 |
| `evaluation/development/pseudorep-code-slice-v1/DEVELOPMENT_LEDGER.json` | Digest-only opened/K expectations and zero qualification credit. | new canonical JSON |
| `docs/implementation/PUBLIC_INTERFACES.md` | Document reportless existing-flag lifecycle and profile `1.1.0` reuse. | +20 / -10 |

Do not edit Slice C, execution/security machinery, v2 wall-by-wall growth code, run-40 mining,
qualification grants, metric sets, the production dependence pin contents, public capability claims, or
the burned envelope. Qualification/pin/ledger promotion artifacts are a later, separately authorized
change after a passing fresh envelope.

## 14. Observed, inferred, and verification-needed

### Observed

- The report adapter's CSV scan and report scan are separable in source, and the CSV/D1' result is
  complete before `_inspect_report` runs
  (`src/sc_referee/scientific_checks/report_csv_dependence_adapter.py:422-492`).
- The current active registry binds dependence check `1.2.0` to `reported_text`, role `reported`, and the
  report adapter (`src/sc_referee/scientific_checks/profiles.py:684-719`).
- Static observations already map to semantic role `observed`, structural-parser verification, and
  `static_source` in common integration (`src/sc_referee/scientific_checks/integration.py:641-693`).
- The generic detector already recognizes the exact `static_source` evidence-plane class
  (`src/sc_referee/detectors/bounded_analysis_method_conflict.py:662-718`).
- All three opened positives use the first-slice direct pandas reader/selection/test/output path and pass
  the revised descriptive-loop grammar; the negatives exercise an aggregated path, no repeated unit, and
  an earlier tracked-column mutation plus later safeguards (section 9).

### Inferred design choices

- A new candidate-scoped walker is smaller and more auditable than relaxing either existing whole-module
  analyzer. This is an engineering inference to be reviewed, not an observed code fact.
- Exact root `analysis.py`, one optional `main`, two registered group tests, and the enumerated API lists
  are intentional first-slice coverage ceilings chosen for zero false accusation and the fresh author
  constraint.
- K's 0/4 expectation is an accepted coverage limit. Interprocedural inlining is deferred from `1.0.0`,
  and all four K programs also contain independently unsupported selection/transform shapes.

### Must be verified during the build

- The current full-digest scope graph can supply one canonical `analysis.py`-to-snapshot edge without a
  selected report; if not, add only a deterministic existing-record full-digest helper, not a new CLI or
  authority surface.
- Common integration and the generic detector accept the code fact/roles without assuming a publication
  artifact. Any hidden report assumption must be removed narrowly and covered by unrelated-check tests.
- Importing the existing private authority/CSV helpers creates no digest cycle. If Python import structure
  prevents this, move only those helpers to a neutral internal module without semantic changes and record
  the deviation in BUILD-NOTES before building.
- P1, P2, and P3 each produce exactly one candidate under the literal grammar, including the bounded
  descriptive loops in P1 and P3.
- N3 returns `tracked-value-mutation` at line 29 before any later safeguard or ignored literal can affect
  precedence.

## 15. Fixed decisions and open questions

Interprocedural inlining is deferred from version `1.0.0`; it is not an open question. The
`analysis.py` naming gate, alternate-analysis exclusions, exact reader census, and 3/3 opened-positive
development expectation are also fixed for this build contract.

The system-wide no-prose directive is not an open question. This document implements it for the
dependence lane only; bringing any other report-backed check into compliance requires a separate scoped
change, but no maintainer or builder may treat prose as permissible evidence in the meantime.

There are no open choices delegated to the builder. Ambiguity is resolved toward abstention, never
toward conviction.
