# Multiple-testing code slice 1.0 design — 2026-08-24

**Status:** build-ready design; design and documentation only in this session

**Revision:** 2, incorporating the Revision 2 narrowing review

**Base:**
[`MULTITEST-CODE-SLICE-RECON-2026-08-24.md`](MULTITEST-CODE-SLICE-RECON-2026-08-24.md),
as amended by the maintainer's ten 2026-08-24 review decisions and Revision 2 re-review

**Lane:** development only; detector/check/adapter `1.0.0`

**Production boundary:** the qualified pseudoreplication `3.1.0` binding, the qualified
complete-domain binding, their installed grants and pins, and every existing Finding wording profile
remain unchanged. The existing question-only multiple-testing check also remains unchanged.

This design changes scientific-requirement record meaning and creates a new Finding-eligibility
predicate. Before implementation changes behavior, the maintainer must accept a dedicated ADR under
the repository's change-discipline rule. Building this development lane does not itself authorize a
Finding or a production capability claim.

## 1. Decision summary and evidence boundary

The first slice detects one narrow frozen-contract conflict: a contract names an ordered family of at
least three CSV outcome columns and requires correction over that complete family, while bounded
static analysis proves exactly one uniform registered two-group test per named outcome and proves
that at least one resulting local `.pvalue` member supports a family conclusion without entering a
recognized correction anywhere in the analyzed source.

The detector is a non-executing evidence compiler. It may consume only:

- one accepted scientific-requirement profile and its byte-identical authority snapshot;
- one digest-bound authorized CSV;
- Python AST structure after docstring removal;
- exact paths, headers, literals, import/API identities, call slots, and value/member/control edges;
- controller-owned source, parser, snapshot, and material records; and
- deterministic replay records.

It must never consume Markdown, reports, comments, docstrings, task text, prompt text, human-readable
output labels, string meaning, or inferred scientific intent as evidence or counterevidence. A string
literal is visible only when it occupies a closed structural slot named in this design: path, CSV
header, API keyword value, output-path token, or an exact version discriminator. Format-string
arguments are structurally traversed for value lineage; the format text itself is never read,
matched, or compared.

The slice does not execute or import project-authored code. Unknown, dynamic, conditional,
unsupported, imported, file-loaded, or opaque scientific lineage always abstains. No negative result
is a global pass, correctness certificate, or statement that correction was unnecessary.

## 2. Scientific-requirement contract 1.2.0

### 2.1 Exact authority shape

Profile `scientific_check_requirement_v1` version `1.2.0` adds one authority form for the new check.
Its top-level field set remains exactly:

```json
{
  "profile_id": "scientific_check_requirement_v1",
  "profile_version": "1.2.0",
  "check_id": "check:authorized-complete-family-correction-over-code-test-battery",
  "candidate_id": "complete-correction-over-authorized-outcome-family",
  "semantic_role_authority": {
    "authorized_test_family": {
      "material_input_path": "data/measurements.csv",
      "group_contrast_column": "condition",
      "outcome_columns": ["marker_a", "marker_b", "marker_c"],
      "family_member_rule": "one-two-group-test-per-named-outcome-column",
      "correction_scope": "complete-authorized-family"
    }
  }
}
```

The role has exactly five fields. `group_contrast_values` and `registered_test_api` are forbidden.
The former is derived from the authorized CSV; the latter is derived from the complete resolved call
census. `family_member_rule` and `correction_scope` are exact literals used only to discriminate this
versioned authority shape. They do not authorize prose interpretation or add a second family rule.

Normative validation is:

1. `material_input_path` passes the existing safe normalized project-relative `.csv` path grammar.
2. `group_contrast_column` and every outcome column pass the existing safe authority-column grammar.
3. `outcome_columns` is ordered, duplicate-free, contains at least three entries, and does not contain
   `group_contrast_column`.
4. `family_member_rule` equals `one-two-group-test-per-named-outcome-column` byte for byte.
5. `correction_scope` equals `complete-authorized-family` byte for byte.
6. No undeclared key is accepted at any level.

The authority-binding snapshot repeats all five role fields and adds exactly
`material_input_content_digest`. Path-only authority is insufficient. The snapshot validator receives
the resolved profile version, check ID, and candidate ID explicitly; it must not infer the authority
kind from whether an object is empty.

### 2.2 Derived values

The adapter derives, rather than contracts for:

- the group-value domain: exactly two distinct, nonempty byte values observed in the contract group
  column, canonically ordered by UTF-8 byte order for replay;
- the family cardinality `N`: the length of the ordered contract outcome list; and
- the registered test API: the one normalized API identity shared by all `N` resolved family calls.

An authorized CSV with fewer or more than two group values abstains
`authorized-group-domain-not-exactly-two`. A family using more than one registered API abstains
`mixed-test-api-family`; the contract cannot make a mixed family uniform.

### 2.3 Additive version dispatch and migration invariance

Implementation must not redefine the existing
`SCIENTIFIC_REQUIREMENT_PROFILE_VERSION == "1.1.0"` constant or route old records through new
branches. Add an explicit accepted `1.2.0` constant and predicates for:

- legacy `1.0.0`: no semantic-role authority or authority snapshot;
- existing `1.1.0`: the current dependence authority or the current empty non-dependence authority;
  and
- new `1.2.0`: the new multiple-testing authority above, with every other check/candidate combination
  accepted or rejected by an explicit versioned branch.

Every current equality check in `scientific_requirement_contract.py` and
`method_contract_run.py` must be audited. A broad replacement of `== 1.1.0` with “latest” is
forbidden because it would change frozen dependence semantics.

Before editing the validator, a regression fixture freezes representative and checked-in `1.0.0`
and `1.1.0` inputs. After the edit it must prove byte equality for:

- canonical resolved values;
- `ResolvedScientificRequirement.manifest` bytes;
- lock-profile bytes;
- Answer-value bytes where the lifecycle emits them;
- every semantic digest over those values; and
- the exact `ScientificRequirementContractError` string for every existing invalid-version,
  wrong-field-set, dependence-authority, empty-authority, unsafe-path, unsafe-column, and snapshot-drift
  case.

This is a golden compatibility test, not an assertion that two freshly recomputed values happen to
match each other after the change. The goldens are captured from HEAD `08c0ccb` before implementation.

## 3. Lane identities and candidate meaning

### 3.1 New identities

```text
check:authorized-complete-family-correction-over-code-test-battery@1.0.0
adapter:authorized-complete-family-correction-over-code-test-battery:code-csv-v1@1.0.0
detector:bounded-code-csv-multiple-testing-conflict@1.0.0
method-conflict-binding:authorized-complete-family-correction-over-code-test-battery-v1:development
method-conflict-finding:code-csv-complete-family-correction-requirement-conflict-v1@1.0.0
```

The check has dimension `selection_process`, comparison form `value_equals`, and canonical expected
operand `complete_family_correction_over_authorized_outcome_family`. Its conflicting observed
operands are versioned canonical scalars for `no_recognized_family_correction` and
`recognized_strict_subset_family_correction`.

The four semantic roles are retained by value from the installed multiple-testing vocabulary:

```text
authorized_test_family
performed_test_battery
multiplicity_correction_call
selected_result_sink
```

Their new check-local bindings are, respectively: the human-authorized ordered CSV family; the exact
`N`-instance registered call battery; the completed full-scope correction census with its exact
covered-position set (including the empty set); and the proved code conclusion sinks. Thus the
correction role remains realized when classification is `none`; it does not invent a nonexistent
call. `selected_result_sink` never means a selected report or a prose claim.

### 3.2 Development-only binding

The new module and binding appear only in the development registry projection. The ordinary registry
projection does not contain the new check, detector, or binding. The development controller may emit
an evaluation candidate or abstention but must emit zero Findings. There is no grant-slot key, public
qualification record, or production pin for this binding.

The existing
`check:complete-family-correction-over-performed-test-battery@1.0.0` question-only module remains in
both existing registry projections with byte-identical adapter, grammar, manifest, and outcomes. The
new lane does not upgrade, replace, or import its private source analyzer.

### 3.3 Exact positive class

An evaluation candidate exists only when the ordered predicate in section 5 proves all of the
following:

1. one valid `1.2.0` authority names `N >= 3` outcome columns in one digest-bound CSV;
2. the full-scope resolved registered-call count equals `N` exactly before operand resolution;
3. all `N` call instances resolve to the same registered test API;
4. each call maps bijectively to one authorized outcome column;
5. both operands of every call contain all authorized-CSV rows for their respective derived group
   value and no additional row mask removes a row or has an exactly unevaluable selected-row set;
6. each conclusion p-value terminates at the exact `.pvalue` member of its mapped registered call in
   this source;
7. every authorized member has a structural p-derived conclusion reaching a supported code sink;
8. all closed counterevidence censuses complete; and
9. correction classification is either `none` or `strict_subset`.

`complete` is a covered negative. `unresolved` is always an abstention. A family reduced to one
extremum is not a candidate even if that extremum reaches output.

## 4. Closed registries and structural definitions

### 4.1 Registered family tests

Slice 1 registers exactly:

```text
scipy.stats.ttest_ind
scipy.stats.mannwhitneyu
```

Import aliases resolve to these canonical identities. Dynamic import, callable aliasing not closed by
the copied resolver, `functools.partial`, starred arguments, dynamic attributes, and unresolved
dispatch abstain. The API is not named in the contract; uniformity is proved from all `N` calls.

### 4.2 Full-scope call-count census

The census runs before any test operand is resolved. Its unit is a statically resolved call instance,
not merely a source line:

- `N` separate call expressions contribute `N`;
- one call expression in a loop or comprehension contributes `N` statically expanded instances only
  when the iterable's resolved sequence is byte-for-byte order-equal to the ordered contract outcome
  list; set equality, sorting, reordering, and dynamic construction are insufficient;
- a called X4 helper contributes the instances created at its exact call sites after alpha-renamed
  expansion and is not also counted from the original definition;
- a registered call in an uncalled helper or closed-dead branch contributes one conservative instance;
  and
- any loop/comprehension/helper multiplicity that cannot be resolved exactly abstains rather than
  contributing a guessed count.

The resolved count must equal `N` exactly. A count below `N` is
`authorized-family-test-census-incomplete`; a count above `N` is
`extra-registered-test-outside-authorized-family`; unresolved multiplicity is
`test-battery-cardinality-unresolved`. These decisions precede operand lineage, so an extra sensitivity
call cannot disappear because its arguments are unsupported.

### 4.3 X4 helper boundary

The new module copies the pseudoreplication 3.1 X4/X4a helper implementation and its closed reason
codes into the new versioned module. The copied rules retain: unique same-module top-level synchronous
functions; simple-name callees; exact ordinary parameter binding; literal/closed defaults; no
recursion, decorators, async, `global`, or `nonlocal`; depth at most two; one expansion per physical
call site; deterministic alpha-renaming; and member-sensitive actual/formal/return edges. The 3.1
lambda, positional return-destructuring, loop-site, and pure-output-helper amendments are copied by
value. Unsupported helper structure abstains under the copied X4 code; it never turns a helper output
into a p-value by name.

Helper inlining applies to reader, test, `.pvalue`, correction, control, container, conclusion, and
sink lineage. A helper-defined p-value qualifies only when the expansion terminates at a registered
call's `.pvalue` member in this source.

### 4.4 Complete selected-group row lineage

For every one of the `2N` operands, copy the pseudoreplication 3.0 P2.1/P2.2 row-identity algorithm by
value and specialize its projected header to the mapped outcome column. Each operand must:

1. terminate at the single authorized reader;
2. select the contract group header by equality to one of the two CSV-derived group values;
3. project its mapped literal outcome header;
4. contain only a recognized non-reducing edge; and
5. have a computed CSV row-index set byte-equal to all authorized-CSV rows for that group value.

An extra row predicate is eligible for the row-preserving exemption only under the exact copied
`_QUERY` grammar:

```text
\A(?P<header>[A-Za-z_][A-Za-z0-9_]*) == (?P<quote>['\"])(?P<value>[A-Za-z0-9_.-]+)(?P=quote)\Z
```

The matched query has exactly one ASCII space on each side of `==`. It admits only one safe literal
header compared for equality to one single- or double-quoted safe literal value. Exact CSV evaluation
must additionally prove the predicate true for every row already selected by the required group
equality. Only a `.query(LITERAL)` call with exactly one positional string argument, no keywords, and
a literal value matching `_QUERY` is eligible for this exemption; boolean-mask subscripts are never
eligible. Any AST mask, query, operator, conjunction, method, header, value, whitespace, or quoting
form outside this grammar is not row-preserving-provable. Any additional split, holdout, screen,
validation, visit, complete-case,
first/last, deduplication, sampling, row-removing predicate, or predicate with an unevaluable selected
row-index set abstains `selected-group-row-completeness-unproven`. There is no separate
screen/confirm predicate and no natural-language endpoint classification.

Unlike pseudoreplication, this lane does not require repeated unit values because its contract has no
unit column. It inherits the row-set equality proof, not the repeated-unit conclusion.

### 4.5 Local `.pvalue` identity

Every family p-value used by a conclusion or correction must be an exact `.pvalue` member edge rooted
at one of the `N` registered calls in the selected source. Tuple position, a variable merely named
`p`, an imported vector, a value loaded from any file, an adjusted-p column, a wrapper not expanded by
X4, and a result of an unresolved call do not establish p-value identity.

Imported, file-loaded, or unresolved-call p-value lineage abstains
`upstream-correction-lineage-unresolved`. A local registered `.pvalue` entering an unresolved consumer
abstains `unresolved-pvalue-consumer`. Exact member identity is preserved through the copied bounded
list/tuple/dict, loop-target, subscript-store, destructuring, and helper edges.

### 4.6 Recognized correction APIs

The recognized API registry is:

```text
statsmodels.stats.multitest.multipletests
statsmodels.stats.multitest.fdrcorrection
scipy.stats.false_discovery_control
sc_referee.calculation_checks.bh.benjamini_hochberg
```

Accepted calls have one exact p-value container argument, only the API's closed optional literal
keywords, and an input member set that resolves exactly to a nonempty subset of the `N` local
`.pvalue` identities. Unknown keywords, dynamic methods, unknown return members, or unresolved input
membership abstain `correction-family-lineage-unresolved`.

Correction-covered positions are determined from the accepted call's resolved input identities
alone, before return handling. Unsupported return selection or plumbing therefore abstains
`correction-family-lineage-unresolved`; it can never erase the accepted input, reclassify the family
as `none`, or produce a candidate.

For `multipletests`, the method registry is pinned to statsmodels `0.14.4`:

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

An omitted `method=` resolves to the API default `hs` and is recognized. A helper parameter whose
omitted argument is an X4-eligible literal default is treated identically after inlining. A supplied
method must be an exact literal from the registry; any other or dynamic method causes
`unresolved-manual-correction-present`. The adapter records the normalized method but Finding wording
does not expose it.

For `fdrcorrection`, accept exact literal method `indep` or `negcorr`, including the API default
`indep`. For `false_discovery_control`, accept exact literal method `bh` or `by`, including default
`bh`. Its `axis` grammar is closed to: omitted (normalized to API default `0`), literal integer `0`,
literal integer `-1`, or literal `None`; no positional axis, named constant, other integer, or dynamic
value is accepted. The repository BH helper has no method slot. Exact package-version and call-shape
assumptions live in the grammar manifest; project packages are not imported.

Correction return identity is API-specific: the reject member for `multipletests` and
`fdrcorrection`, and adjusted-p members for `false_discovery_control` and repository BH. Unsupported
destructuring or return-member selection abstains.

Widening this correction-acceptance registry is not automatically conservative: a newly accepted
call can classify only a strict subset as corrected and thereby create a candidate. Every future
correction-registry addition is therefore a candidate-surface change requiring its own design and ADR
review, even when the new call also converts other cases to covered negatives.

### 4.7 Manual adjustment and decision thresholds

Slice 1 recognizes only one manual correction grammar: memberwise adjusted Bonferroni values of exact
shape `min(P * N, 1)`, `min(N * P, 1)`, `numpy.minimum(P * N, 1)`, or
`numpy.minimum(N * P, 1)`, where `P` is one local registered `.pvalue`; `N` is either an integer
literal or a closed module constant whose exact integer value equals the completed family census;
the builtin/NumPy identity is unshadowed; and each adjusted value is later compared with a permitted
bare alpha. `len(...)`, a container member, helper return, arithmetic expression, and every other `N`
form are outside the grammar. The member-position census classifies the covered members exactly.

The recon's `ALPHA / N` decision-threshold form is deleted. A family `.pvalue` may be used directly in
a decision comparison only when the other operand is an `ast.Constant` numeric literal whose exact
Decimal value is in this closed set:

```text
0.01
0.05
0.1
```

The literal must occur directly in the comparison. A named constant, unary/computed expression,
division, power, rank-dependent threshold, sequence member, helper return, or any other threshold is
not a bare literal. Unless it is part of the recognized adjusted-value Bonferroni grammar above, it
abstains `unresolved-decision-threshold`.

Apply this additional product rule with exact Decimal arithmetic to every bare literal used for a
family decision, whether the compared value is raw or adjusted: for the exact family census `N` and
bare decision literal `a`, if `a * N` equals `0.01`, `0.05`, or `0.1`, abstain
`unresolved-decision-threshold` even when `a` itself is in the permitted set. The rule is independent
of comparison direction. It closes an off-AST Bonferroni threshold such as `p < 0.01` for `N = 5`
and the `N = 10`, family alpha `0.1` form. Consequently, hand-written Sidak, Holm, and
Bonferroni-threshold variants never read as no correction.

Exact Decimal construction uses the numeric literal's source text when available, or
`Decimal(repr(value))` for an AST numeric value whose source text is unavailable. It must never use
`Decimal(float_value)`: binary-float expansion such as `Decimal(0.01) * 5 != Decimal("0.05")` would
silently bypass this product-rule abstention.

The admitted raw comparisons are exactly `<`, `<=`, `>`, and `>=`, with either operand order. Thus
the closed forms are `P < a`, `P <= a`, `P > a`, `P >= a`, `a < P`, `a <= P`, `a > P`, and
`a >= P`; equality, inequality, chaining, membership, identity, and every other comparison form are
outside the grammar. Reversed order does not bypass the product rule.

The direct-`P` threshold-refusal branch above is itself part of the closed section-4.7 grammar, so a
comparison such as `P < ALPHA / N` stops `unresolved-decision-threshold`. After that exhaustive
threshold classification, any `BinOp`, `Call`, or comparison transform of a family `.pvalue` outside
the exact section-4.6 return and section-4.7 raw/manual grammars abstains
`unresolved-manual-correction-present`. This includes unclamped `P * N`, sorting, ranking, cumulative
extrema, step-up/down logic, `abs(P)`, and nested or helper transforms. Such a value can never be
treated as raw, adjusted, or evidence of `none`.

Direct-`P` comparisons are classified exclusively at order 15, whether admitted or refused, and the
comparison nodes are excluded from the order-14 off-grammar transform census. Order 14 still handles
every non-comparison `BinOp`/`Call` transform. This partition makes
`unresolved-decision-threshold` the determinate first reason for every refused direct-`P` threshold.

### 4.8 Module-independent correction-name census

After docstring removal, inspect only the terminal callee slot of every `ast.Call` in the complete
selected module, independent of receiver identity, imports, and p-value dataflow. The terminal slot
is `Name.id` when that `Name` is the call's complete callee and `Attribute.attr` when that `Attribute`
is the call's callee. ASCII-lowercase that slot and match:

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

`benjamini*` means an ASCII prefix match on the terminal slot. A recognized call under sections
4.6-4.7 is discharged by its exact grammar. Any remaining slot match, even on an unknown object and
even when no family p-value lineage is resolved, abstains `unresolved-manual-correction-present`.
Identifiers in assignments, parameters, containers, attributes that are not the callee terminal,
keywords, method strings, comments, output labels, and prose never enter this census. This is a new,
closed callee-terminal identifier channel and must be named as such in the authorizing ADR.

This census and the p-value-consumer census are deliberately independent: one catches reserved
callee-terminal calls whose module cannot be resolved, and the other catches opaque consumers whose
terminal slots carry no registered cue.

### 4.9 Statistics-prefix census and exact exemptions

The new module restates the pseudoreplication 3.0 registry by value. Resolve imports/aliases and
inspect every call under exactly:

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

`scipy` alone is not a match outside `scipy.stats`; NumPy random draws are handled by the resampling
guard. A call under a prefix abstains `unresolved-inference-sibling-present` unless it is one of the
`N` registered family calls, a recognized correction, or one of these two exact exemptions:

1. `scipy.stats.sem(V)` with one positional value and only optional literal `axis`, `ddof`, or
   `nan_policy`. Its result must have no path to a registered test, correction, p-derived conclusion,
   decision threshold, branch/loop condition, or family container. Every terminal path must be
   identity/arithmetic/formatting into a supported output sink. Any other consumer abstains.
2. `scipy.stats.t.ppf(P, DF)` with two positional scalar arguments and no keywords. `DF` must derive
   only from lengths or variances of the two operands of one uniquely associated registered family
   call; `P` must be an `ast.Constant` bare numeric literal whose exact Decimal value is one of
   `0.9`, `0.95`, `0.975`, `0.99`, or `0.995`; and the result may reach only
   arithmetic/formatting and output associated with that same call. Any arithmetic, name, container
   member, helper return, or other expression in `P` disqualifies the exemption and follows the
   normal statistics-prefix abstention path. Ambiguous association, another test/correction, a
   branch/loop condition, or a family conclusion also abstains.

   Apply the product-rule mirror with exact Decimal arithmetic and the exact completed family census
   `N`: if either `(1 - P) * N` or `2 * (1 - P) * N` equals `0.01`, `0.05`, or `0.1`, disqualify the
   exemption and follow the normal statistics-prefix abstention path. Thus `P = 0.99` and `P = 0.995`
   are refused at `N = 5` as the one-sided and two-sided Bonferroni critical points, respectively.
   Decimal construction uses the `P` literal's source text when available, or
   `Decimal(repr(value))` when source text is unavailable, and never `Decimal(float_value)`.

These are finite graph conditions, not judgments based on names or output text. Other distribution
methods, `pearsonr`, `spearmanr`, `linregress`, `f_oneway`, `kruskal`, one-sample tests, model fits,
cross-validation, and dynamic statistics calls abstain.

### 4.10 P-derived conclusion and sink

A conclusion for one authorized member is exactly one of:

- a local raw `.pvalue` compared under one of section 4.7's eight exact operand/operator forms with a
  permitted bare alpha that also passes the product rule;
- an API-recognized reject member;
- an adjusted p-value produced directly by one exact section-4.6 API-return grammar or one of the four
  exact section-4.7 manual grammars, compared under section 4.7 with a permitted bare alpha that
  passes the product rule; or
- membership of that outcome's exact contract column identifier in a closed list/tuple/dict/set
  whose inclusion predicate is one of the preceding booleans.

No `BinOp`, `Call`, comparison transform, wrapper, or value merely named as adjusted qualifies under
the third bullet. Off-grammar family `.pvalue` transforms have already abstained
`unresolved-manual-correction-present` and can never reach conclusion classification.

The conclusion must reach a copied v3.1 p-result-eligible console/file sink, including its exact
report-buffer code shape, through the bounded forward graph. Merely assigning, returning from an
uncalled helper, or outputting numeric p-values is not a conclusion. Every one of the `N` authorized
members must have a conclusion and sink path, or the lane abstains
`pderived-conclusion-family-incomplete` or `conclusion-output-sink-unavailable`.

The family-extremum guard is closed to these exact unshadowed forms over a direct container holding at
least two family p-value identities:

1. builtin `min(PVALUES)` or `max(PVALUES)`;
2. `numpy.min(PVALUES)`, `numpy.max(PVALUES)`, `numpy.nanmin(PVALUES)`, or
   `numpy.nanmax(PVALUES)` with one positional argument and no keywords;
3. the four NumPy calls in item 2 when their sole argument is exact
   `numpy.array(PVALUES)` or `numpy.asarray(PVALUES)` with one positional argument and no keywords;
4. `SERIES.min()` or `SERIES.max()` with no arguments when `SERIES` has exact family-member lineage;
5. `sorted(PVALUES)[0]` or `sorted(PVALUES)[-1]` with unshadowed `sorted`, one positional argument,
   and no keywords;
6. `numpy.sort(PVALUES)[0]` or `numpy.sort(PVALUES)[-1]` with one positional argument and no
   keywords; and
7. `SERIES.sort_values().iloc[0]` or `SERIES.sort_values().iloc[-1]` with no call arguments or
   keywords and exact family-member lineage.

When one of these values reaches a sink, abstain
`family-pvalue-extremum-reduction-present` before incomplete-conclusion reporting. Every other
extremum or selection form is unrecognized and abstains `unresolved-manual-correction-present` under
the off-grammar-call rule. In particular, `numpy.argmin`, `numpy.argmax`, Series `.idxmin()`/
`.idxmax()`, `numpy.partition`, `heapq.nsmallest`/`nlargest`, `min(MAPPING.values())`, dynamic indices,
and any unlisted nested call are not recognized extremum forms.

The copied v3.1 guard-terminal exports are not conclusion sinks. If any family `.pvalue` identity
flows into exact DataFrame/Series `.to_csv(STATIC_PATH)`, `numpy.savetxt(STATIC_PATH, VALUE)`, or
`json.dump(VALUE, WRITE_HANDLE)`, abstain `unresolved-pvalue-consumer`, even when separate raw flags
also reach a p-result-eligible sink. Export is not evidence that correction occurs later.

## 5. Ordered evidence predicate and closed outcomes

Predicate order is normative. Full-scope guards are computed to a fixed point, but the first outward
reason is selected by the order below, never by source position.

| Order | Required proof or decision | First abstention code(s) |
|---:|---|---|
| 1 | Resolve one installed `1.2.0` check/candidate authority and a byte-identical role snapshot. | `verified-contract-authority-unavailable`; `authorized-test-family-shape-unsupported` |
| 2 | Require ordered unique family cardinality `N >= 3`. | `authorized-family-cardinality-below-three` |
| 3 | Resolve one digest-equal authorized CSV at the exact authority path. | `frozen-authority-material-mismatch` |
| 4 | Parse the bounded CSV; prove every authorized outcome cell on every authorized row parses as a finite numeric value, prove at least two rows in each of the two derived groups for every outcome, and derive exactly two nonempty group values. | `authorized-family-csv-domain-unavailable`; `authorized-group-domain-not-exactly-two` |
| 5 | Select exactly one root `analysis.py`; refuse alternate `.py` analysis surfaces, notebooks, and R; scan every other Python file for registered statistics imports. | `analysis-source-envelope-unavailable`; `alternate-analysis-file-present`; `statistics-api-imported-outside-analysis-py` |
| 6 | Parse without execution; resolve imports, aliases, closed constants, and copied X4 helper/loop structure within the inherited 1 MiB, 50,000-node, depth, and definition ceilings. | `api-resolution-ambiguous`; `dataflow-definition-ceiling-exceeded`; the copied X4 codes in section 5.2 |
| 7 | Require exactly one accepted reader definition at the authorized CSV path, including uncalled-helper census. | `additional-accepted-reader-present`; `authorized-reader-lineage-unavailable` |
| 8 | Expand only exact contract-outcome iterations and run the full-scope registered-call census before operand resolution; require resolved count exactly `N`. | `test-battery-cardinality-unresolved`; `authorized-family-test-census-incomplete`; `extra-registered-test-outside-authorized-family` |
| 9 | Require all `N` calls to resolve to one registered API. | `mixed-test-api-family` |
| 10 | Map calls bijectively to the ordered outcome list and prove both exact group operands for every member. | `test-operand-lineage-unresolved` |
| 11 | Prove complete selected-group CSV row sets independently for every operand. | `selected-group-row-completeness-unproven` |
| 12 | Bind every family p-value to the local registered `.pvalue` member and reconstruct its ordered container/member identities. | `upstream-correction-lineage-unresolved`; `pvalue-family-collection-unresolved`; `unresolved-pvalue-consumer` |
| 13 | Detect a family-to-one extremum reaching output. | `family-pvalue-extremum-reduction-present` |
| 14 | Census recognized correction inputs/returns and exact manual adjusted values; census all correction-name terminal slots. | `correction-family-lineage-unresolved`; `unresolved-manual-correction-present` |
| 15 | Census every p-derived decision threshold and require a permitted bare literal unless the adjusted-value grammar already discharged it. | `unresolved-decision-threshold` |
| 16 | Apply hierarchy/control, partition, upstream, resampling, and statistics-prefix guards to complete selected scope. | `hierarchical-gatekeeping-present`; `pvalue-control-dependence-unresolved`; `multiple-family-partition-present`; `resampling-cardinality-unresolved`; `permutation-family-control-present`; `unresolved-inference-sibling-present` |
| 17 | Prove one p-derived conclusion for every authorized member and exact reachability to a called sink. | `pderived-conclusion-family-incomplete`; `conclusion-output-sink-unavailable` |
| 18 | Classify correction membership as `complete`, `strict_subset`, or `none`; unresolved classifications have already abstained. | no new code |
| 19 | Emit a covered negative for `complete`; emit one development evaluation candidate for `strict_subset` or `none`; enforce the development no-Finding ceiling. | `multiple-testing-code-inspection-exception` on localized adapter failure |

### 5.1 Guard definitions and precedence within order 16

1. **Hierarchy/control.** A value is *jointly derived* exactly when its bounded backward
   name/member closure contains authorized-reader projections of at least two distinct contract
   outcome headers. The closure follows only identity/annotated assignment, attribute/subscript,
   literal container and exact destructuring, subscript store, X4 actual/formal/return,
   unary/arithmetic/boolean/comparison, and call receiver/argument-to-result taint edges. A call edge
   is suppressive taint only; it does not establish scientific meaning or an admitted positive
   transform. Abstain `hierarchical-gatekeeping-present` when a local family p-value, reject flag,
   adjusted p-value, alpha value, or such a jointly-derived value controls one of these enumerated
   nodes: a registered test-call argument; recognized correction-call argument; p-derived conclusion
   operand; family-container insertion key or value; `ast.If.test`; `ast.IfExp.test`;
   `ast.While.test`; `ast.Assert.test`; `ast.Match.subject`; every non-`None`
   `ast.match_case.guard`; a `for`/comprehension iterable or comprehension `if`; every boolean
   short-circuit operand feeding an enumerated node; or an argument/member that selects what a
   registered sink call emits. For call, conclusion, container, and sink nodes, *controls* means that
   the value determines execution, membership, threshold, branch, or emitted member; an ordinary
   authorized test operand, correction p-value payload, conclusion p-value payload, container payload,
   or sink payload is not a control edge.

   The enumeration is a minimum terminal-node registry, not an execution-prevention ceiling. Any node
   whose evaluation can prevent an enumerated control node from executing is also a control edge when
   its backward closure carries one of the tracked values above. This residual is resolved only from
   AST control-flow, short-circuit, and dominance edges; it never reads names or prose. If whether such
   a node can prevent execution is unresolvable, abstain `pvalue-control-dependence-unresolved`. This
   catches a hand-written NumPy omnibus assert or match gate without naming or interpreting it.
2. **Partitions.** Abstain `multiple-family-partition-present` when the `N` local p-values are placed
   into two or more disjoint correction inputs or separately emitted decision collections, or when
   separate outer strata create independently corrected partitions. Exact concatenation into one
   complete correction is allowed only if member identity is complete and no partition-specific
   conclusion exists.
3. **Locality/upstream.** The order-12 local `.pvalue` rule dominates. A second accepted reader,
   imported p-values, a loaded adjusted column, or unresolved wrapper never becomes proof of local
   uncorrected testing.
4. **Permutation/maxT/minP.** First detect repeated generators and registered draws using the copied
   pseudoreplication 3.0 S2 construct registry. If such a construct consumes authorized-CSV-derived
   family data and its cardinality does not resolve to one of S2's enumerated closed constant sources,
   abstain `resampling-cardinality-unresolved` immediately. Do not inherit S2's skip-on-unresolved
   behavior, and do not require a reducer or sink for this unresolved-cardinality branch. In
   particular, arithmetic such as `20 * len(FRAME)` is not a closed cardinality source.

   For a resolved cardinality, abstain `permutation-family-control-present` when the cardinality is at
   least 10, the construct consumes authorized CSV-derived family data, produces multiple family
   statistics per draw, reduces a draw by one of the copied joint-extremum/count-ratio/sorted-index
   forms or compares observed registered `.pvalue`-associated conclusions with the joint null, and
   that result reaches a sink or controls conclusions. A resolved cardinality below 10 is only a near
   miss for this guard; every other predicate still applies.

For condition 2 of that guard, inherit pseudoreplication 3.0 S2 verbatim:

> The repeated body or registered draw indexes, samples, permutes, concatenates, or otherwise draws
> from a dict/list/tuple/Series/array/frame member derived anywhere from the authorized CSV. The 2.x
> requirement that the value carry a particular tracked-name label is deleted. Member edges, helper
> returns, destructuring, actual/formal bindings, and subscript stores are followed.

The resolved repeated-cardinality sources, registered NumPy/random draw identities, factor rules, reducer,
count-ratio, sorted-index, X4, and sink breadth are copied by value from pseudoreplication 3.0 S2. The
multiple-testing guard additionally requires that any ordinary family conclusion lineage terminate
at the registered local `.pvalue` member; a test statistic, variable name, or imported p-value cannot
satisfy that lineage.

### 5.2 Closed abstention-code set

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

No screen/confirm code exists in slice 1. Ambiguity maps to one of the closed reasons above, never to
a candidate.

## 6. Per-guard false-accusation analysis

Every row below names an answer-visible adversarial correct-analysis fixture required before Envelope
10. Each fixture must be isolated so that its named guard is the first reason, even when a later
envelope case intentionally realizes more than one role.

| Guard | False accusation prevented | Required isolated fixture and expected outcome | Accepted recall cost / residual boundary |
|---|---|---|---|
| Recognized complete correction | A complete standard correction could otherwise look absent. | `correct-default-method-multipletests`: `multipletests(pvalues)` over all `N`; covered negative, with omitted method normalized to `hs`. | Unsupported return plumbing abstains even if runtime behavior would be correct. |
| Computed decision threshold | Hand Sidak/Holm/Bonferroni variants could look like raw alpha decisions. | `correct-hand-sidak`: exact Sidak arithmetic; `unresolved-decision-threshold`. | Even mathematically checkable threshold arithmetic abstains until its whole grammar is registered. |
| Bare-literal product rule | An off-AST correction can be precomputed into a literal that otherwise resembles raw alpha. | `correct-bare-literal-bonferroni-off-ast`: `N = 5`, every local `.pvalue` is compared as `p < 0.01`, and the complete correction is outside the AST; `unresolved-decision-threshold` because `0.01 * 5 == 0.05`. | The same literal at family sizes 5 or 10 suppresses even when it was not intended as Bonferroni. |
| Module-independent correction-name census | A valid correction from an unsupported package or wrapper could be missed by import resolution. | `correct-off-registry-correction`: `pingouin.multicomp(...)`; `unresolved-manual-correction-present`. | An unrelated method with a reserved terminal slot also abstains. |
| Exact call count | A duplicated sensitivity analysis could be silently dropped from family accounting. | `correct-sensitivity-duplicate`: `N` contract-mapped calls plus one duplicate call; `extra-registered-test-outside-authorized-family`. | An unused registered call in a dead or uncalled scope suppresses. |
| Complete row lineage | Independent discovery/validation rows could be merged into one flat family accusation. | `correct-discovery-validation-split`: outcome screening and retesting use additional disjoint row masks; `selected-group-row-completeness-unproven`. | Any non-tautological or unevaluable extra mask abstains even when scientifically benign. |
| Local `.pvalue` lineage | Adjustment may have occurred in an upstream stage. | `correct-upstream-adjusted-input`: local diagnostic calls exist, but emitted conclusions use a loaded adjusted-p column; `upstream-correction-lineage-unresolved`. | The lane cannot credit correction outside the selected source. |
| Opaque local p-value consumer | A correction may be implemented by an imported helper whose callee carries no registered correction name. | `correct-cross-module-numpy-correction-helper`: the family p-value container enters an imported NumPy-based helper; `unresolved-pvalue-consumer`. | Any opaque consumer suppresses even when it is unrelated to correction. |
| Guard-terminal p-value export | A raw p-value table may be an intermediate for a documented downstream correction stage. | `correct-export-for-downstream-correction`: raw flags reach console and the family p-value table reaches exact `.to_csv`; `unresolved-pvalue-consumer`. | The analyzed source cannot establish what consumes the export. |
| Hierarchy/control | A valid gate can make flat complete-family correction inapplicable. | `correct-all-numpy-omnibus-gate`: a scalar jointly derived from the authorized outcome matrix controls family calls; `hierarchical-gatekeeping-present`. | Data-derived validation gates over multiple outcomes also suppress. |
| Assertion execution gate | A jointly derived assertion can halt the run before every family call without appearing in an `if` or loop. | `correct-numpy-omnibus-assert-gate`: an exact three-outcome NumPy aggregate reaches `ast.Assert.test` before three raw `ttest_ind` conclusions; `hierarchical-gatekeeping-present`. | Any tracked assert/match/short-circuit execution gate suppresses even when it is a valid validation check. |
| Family partition | Two prespecified disjoint corrected families could look like one incompletely corrected family. | `correct-disjoint-correction-families`: two disjoint p containers and decision collections; `multiple-family-partition-present`. | Temporary partitioning abstains unless exact concatenation and absence of partition conclusions are proved. |
| Resolved permutation/maxT/minP | Joint-null family control may have no conventional correction call. | `correct-label-permutation-maxT`: at least 10 label permutations, all authorized outcomes per draw, joint maximum, adjusted conclusions; `permutation-family-control-present`. | Any at-least-10 repetition with the same closed structural reach suppresses. |
| Unresolved resampling cardinality | A dynamic maxT/permutation procedure must not disappear because its trip count is opaque. | `correct-unresolved-cardinality-maxT`: family-data label permutations under `range(20 * len(frame))`; `resampling-cardinality-unresolved` before reducer/sink requirements. | Every unresolved repeated construct consuming authorized family data suppresses. |
| Statistics-prefix sibling | A supported-looking raw family may coexist with another inferential procedure. | `correct-off-family-survival-sibling`: a `lifelines` fit beside the family; `unresolved-inference-sibling-present`. | A harmless non-exempt statistics call anywhere in scope suppresses. |
| Family extremum | Reporting only the minimum p-value is not proof of memberwise family conclusions. | `correct-minimum-p-global-summary`: `min(pvalues)` reaches output; `family-pvalue-extremum-reduction-present`. | The lane abstains even if a downstream consumer would apply a valid global procedure. |
| Conclusion and sink completeness | Numeric p-values may be an intermediate artifact corrected downstream. | `correct-pvalue-table-only`: all raw p-values are printed numerically to console without decisions or guard-terminal export; `pderived-conclusion-family-incomplete`. | The lane requires structural conclusions and cannot infer them from labels or a later report. |

The guards only remove eligibility. None asserts that the fixture's procedure is scientifically
correct, required, or applicable in another analysis.

## 7. Evidence projection and Finding wording profile

### 7.1 Observation projection

One candidate observation contains only controller-checkable fields:

- authority and snapshot digests;
- CSV path/content/file identity, group column, derived two-value-domain digest, and ordered outcome
  columns;
- authorized, performed, corrected, and uncorrected counts, with
  `AUTHORIZED_COUNT == PERFORMED_COUNT == N` and
  `UNCORRECTED_COUNT == N - CORRECTED_COUNT > 0`;
- one normalized registered test API;
- ordered call/member positions and correction-covered positions;
- exact code evidence spans for authority reader, `N` calls, `.pvalue` members, any recognized
  corrections, conclusions, and sinks;
- completed receipt identities for every finite guard; and
- the semantic-role bindings from section 3.1.

No runtime p-value, effect, group value, output label, report path, or source prose enters the
candidate or wording slots.

### 7.2 Versioned wording profile

Freeze this profile on the first implementation commit:

```text
profile_id: method-conflict-finding:code-csv-complete-family-correction-requirement-conflict-v1
profile_version: 1.0.0
title: Analysis code contradicts the frozen complete-family correction requirement
issue_class: x-review-scoped-analysis-method-requirement-mismatch
```

Its semantic digest is `semantic_digest` of the canonical object containing `profile_id`,
`profile_version`, title, summary template, slot schema, issue class, severity rationale,
non-inferences, and next action. The digest is registered in the detector manifest and development
binding. Pseudoreplication wording objects and digests are not edited.

The immutable summary template is:

> The frozen requirement for `{CSV_PATH}` names the ordered outcome columns {OUTCOME_COLUMNS} under
> group column `{GROUP_COLUMN}` as one complete-correction family with {AUTHORIZED_COUNT} members. In
> `analysis.py`, static analysis establishes {PERFORMED_COUNT} matching `{TEST_API}` calls. For
> {UNCORRECTED_COUNT} registered `.pvalue` members, p-derived conclusions reach a supported code sink
> without entering a recognized correction anywhere in the analyzed source; {CORRECTED_COUNT}
> registered `.pvalue` members enter a recognized correction. This conflicts with the frozen
> complete-family-correction requirement.

The closed slots are:

| Slot | Validator |
|---|---|
| `CSV_PATH` | safe normalized authority path, byte-equal to the digest-bound material path |
| `GROUP_COLUMN` | safe authority column, byte-equal to the contract field |
| `OUTCOME_COLUMNS` | canonical JSON rendering of the ordered safe authority-column list |
| `AUTHORIZED_COUNT` | checked integer equal to contract list length and at least 3 |
| `PERFORMED_COUNT` | checked integer equal to the resolved registered-call census and `AUTHORIZED_COUNT` |
| `CORRECTED_COUNT` | checked integer from 0 through `PERFORMED_COUNT - 1` |
| `UNCORRECTED_COUNT` | checked integer equal to `PERFORMED_COUNT - CORRECTED_COUNT` and at least 1 |
| `TEST_API` | one of the two registered canonical API identities, uniform across all calls |

The profile's frozen non-inferences are:

- The contract author may be wrong.
- Static source does not establish that project code executed.
- Absence of a recognized correction in the analyzed source does not establish that no correction
  was applied.
- Correction may occur in unsupported, uninspected, upstream, downstream, or external code.
- The detector does not establish runtime p-values, test assumptions, effect sizes, inflated error
  rates, statistical invalidity, selection, publication use, interpretation, or reliance.
- The detector does not establish that the named outcomes should scientifically form one family.

Severity rationale and next action remain contract-conflict bounded: align the checked code with the
frozen requirement or record an authorized amendment and re-audit the exact source and CSV. They must
not recommend a particular correction method.

## 8. Reuse and isolation map versus pseudoreplication 3.1

| Surface | Decision |
|---|---|
| `code_csv_dependence_adapter_v3_1.py`, `code_csv_dependence_dataflow_v3_1.py` | Copy the necessary implementation into new multiple-testing versioned files, then specialize the copies. Do not edit these files and do not import their private helpers. |
| 3.1 source envelope, parser bounds, import resolver, closed constants, X4/X4a expansion, reader census, member graph, complete-row proof, sink graph, resampling breadth, and prefix census | Copy by value into the new module. Preserve their bounds and exact inherited reason semantics unless this design explicitly specializes them. |
| Core inspection records, canonical JSON/digests, evidence spans, receipts, frozen material lookup, registry lane API, and admission framework | Import as public framework utilities without changing their semantics. |
| Existing multiple-testing question-only module and `multiple_testing_recognition/` package | Leave byte-identical. Reuse its established test/correction identities only as reviewed values; do not route the new lane through its report-only certificate. |
| Decimal BH calculation check | Leave unchanged; use only as a test oracle for exact adjusted-value fixtures, not as runtime evidence for unknown project p-values. |
| Pseudoreplication check, adapter, detector, wording v1/v2, qualification records, grants, pins, frozen sources, and opened-case ledgers | Byte- and outcome-immutable. Add digest/isolation assertions around the new development registration. |
| Complete-domain check, detector, wording, qualification records, grant, and pin | Untouched. |

The exact frozen pseudoreplication identities named by the isolation gate are:

```text
adapter implementation: sha256:6900611a3ef6c06be5740df14333eac5d789c6c93165b8826c796a8b4de87170
recognition grammar:     sha256:69256d48b46f16d7c144e01d5b4509470e9b187bf3db4f7e259d782459c2d476
finding profile v2:     sha256:1dad7c14985fbfb89a7f8fe24a5e7f36d07a7c9fc6f76b4d14951cc71337c04a
wording profile v1:     sha256:0440fdb918eb04ff975e7129c4152a2d681f3f4203ae8c7a1f8fc9ebf8916288
```

The new check ID prevents qualification-history conflation. The new detector identity is a versioned
wrapper around the canonical scalar conflict comparison plus the multiple-testing-specific candidate
shape; it must not reuse the dependence detector ID.

### 8.1 Exact permitted digest churn and non-derivation gate

Adding one development module changes the lane-inclusive registry digest because that digest binds
both complete lane projections. At implementation time, the only pre-existing stored byte surfaces
permitted to change for that cause are:

1. the development module/binding collections in
   `src/sc_referee/resources/scientific-check-manifests-v1/registry.json`, that resource's enclosing
   canonical bytes, and the lane-inclusive `registry_digest` computed from those collections;
2. `scientific_check_registry.registry_digest` in newly generated audit semantic locks, plus only the
   enclosing lock identifiers/digests whose canonical input directly contains that field; and
3. newly regenerated replay, work-packet, audit-bundle, or golden-record bytes that directly embed one
   of the exact lock bytes or digests from item 2, together with their direct enclosing digests and
   `MANIFEST.sha256` entries.

Historical lock/replay records are not rewritten. No other pre-existing record may change merely
because the lane-inclusive digest changed. Replay assertions compare exact bytes within one frozen
registry state; cross-state isolation comparisons remove only the enumerated registry/lock-derived
fields above and require byte equality for every remaining field.

The build must run a two-registry differential gate that changes only the new development projection.
It must prove byte equality of every field in each installed `GrantPin`, the canonical grant set,
qualification records, metric-set records, threshold-policy references, and all qualified Finding
objects. It must also prove by explicit construction/serialization dependency checks that no
`GrantPin` field, grant field, qualification field, or Finding field is populated from the
lane-inclusive `registry_digest` or from an enclosing lock digest that includes it. A changed audit
lock is therefore expected; any changed authority record or qualified Finding byte is a hard failure.

### 8.2 Required ADR notes

The authorizing ADR must record both accepted boundaries below exactly:

1. **BL-1 residual.** The bare-literal product rule tests only the conventional family-alpha set
   `{0.01, 0.05, 0.1}`. It does not infer an arbitrary family alpha. An unconventional family alpha
   whose quotient lands on a permitted decision literal—for example `0.15 / 3 == 0.05`,
   `0.5 / 5 == 0.1`, or `0.3 / 3 == 0.1`—is therefore still convicted as an uncorrected family by
   this slice. This is an accepted residual, not evidence that those family alphas are impossible.
2. **Envelope-count deviation.** Revision 1 deviates from binding amendment (i)'s six-positive/eight-
   negative Envelope-10 protocol by adding the BL-1 negative role N9. The frozen protocol is now six
   positives and nine negatives, with hard stops `0/9` and replay `15/15`. This enlarges only the
   zero-candidate negative surface; it does not enlarge candidate eligibility or the Finding surface.

## 9. Test plan

### 9.1 Contract and compatibility

1. Positive `1.2.0` profile, lock, Answer, snapshot, and material-digest lifecycle.
2. Exact wrong-field-set tests for the removed group-value/API fields, missing/duplicate outcome
   columns, unsafe path/header, group column in outcomes, wrong discriminators, wrong check/candidate,
   snapshot mismatch, and digest mismatch.
3. The HEAD-`08c0ccb` golden regression from section 2.3 proving byte-identical `1.0.0`/`1.1.0`
   resolved values, lock/Answer bytes, semantic digests, and exact error strings.
4. An assertion that all qualified pseudoreplication contract fixtures still resolve as `1.1.0` and
   retain their frozen authority/snapshot bytes.
5. Authorized-CSV boundary tests proving that every cell in every authorized outcome column is finite
   numeric and that each derived group has at least two rows for every outcome; one failed cell or
   group/outcome count must stop at order 4.

### 9.2 Call, operand, p-value, and conclusion matrices

1. Exactly `N` repeated calls, explicit calls, an order-equal contract-list loop/comprehension, X4 test
   helper, helper-returned container, and ordered dict members. Set-equal reordered, sorted, and
   dynamically built iterables must stop `test-battery-cardinality-unresolved`.
2. Counts `N-1`, `N+1`, an unresolved loop, a dead extra call, and an uncalled-helper extra call;
   assert call-count reasons occur before operand reasons.
3. Uniform `ttest_ind`, uniform `mannwhitneyu`, and every mixed ordering; uniformity is derived, never
   supplied by the contract.
4. One positive and one refusal for every copied non-reducing operand edge, every row-dropping
   operator, every unknown mask, and the sole extra-query exemption under the exact section-4.4 regex.
   Include both quote forms and refuse every changed operator, spacing, header/value alphabet,
   conjunction, AST mask, boolean-mask subscript, nonliteral `.query`, multi-argument `.query`, and
   unevaluable query. Run the complete row-set proof for all `2N` operands.
5. Exact `.pvalue` members through every admitted container/helper edge; reject tuple index, imported,
   file-loaded, unresolved-wrapper, adjusted-column, dynamic-key, and unresolved consumer lineage.
6. Exercise all eight `<`, `<=`, `>`, `>=` raw comparison/operand-order forms for every permitted
   alpha and both sides of the product rule. The required isolated
   `correct-bare-literal-bonferroni-off-ast` fixture uses `p < 0.01`, `N = 5`, and correction outside
   the AST and must stop `unresolved-decision-threshold`. Reject named constants, every arithmetic
   operator, sequence/helper/rank thresholds, equality, inequality, chaining, membership, identity,
   and all hand Sidak/Holm/Bonferroni threshold variants. Assert that every refused direct-`P`
   comparison stops first at order 15 and never enters the order-14 off-grammar transform set.
7. Every admitted conclusion shape and sink; numeric-p-only output; missing one member conclusion;
   uncalled/dead output; statistic-only output; and every exact family-extremum form. Every unlisted
   extremum/selection form in section 4.10 must stop `unresolved-manual-correction-present`.
8. Send each family `.pvalue` separately and in a container to each exact `.to_csv`, `numpy.savetxt`,
   and `json.dump` export shape, with and without separately printed raw flags; every case must stop
   `unresolved-pvalue-consumer`.

### 9.3 Correction closure

1. Complete and strict-subset inputs for every registered API and accepted method. Prove covered
   positions are fixed from inputs before return handling; every unsupported return form abstains and
   none classifies as `none`.
2. `multipletests` with omitted `method`, explicit `hs`, every alias, dynamic method, unknown method,
   unsupported keyword, unresolved input membership, and unresolved return member. For
   `false_discovery_control`, accept only omitted `axis`, literal `0`, literal `-1`, and literal
   `None`; refuse positional, named-constant, other-integer, and dynamic axis forms.
3. Exact adjusted-value Bonferroni in both multiplication orders and NumPy form, for complete and
   strict-subset position sets. Admit `N` only as an integer literal or closed module constant equal
   to the exact census; refuse `len`, container, helper, arithmetic, wrong-value constants, every near
   miss, unclamped multiplication, and all threshold-division forms.
4. One callee-terminal-slot test for every exact correction name and for the `benjamini` prefix,
   across simple and attribute callees on unrelated receivers. Near misses in variable names,
   keywords, strings, comments, docstrings, and output labels must not fire.
5. Manual BH/Sidak/Holm sorting, ranking, cumulative-extremum, and stepwise adversaries all abstain;
   none may classify as `none`.
6. Multiple correction calls, overlapping inputs, disjoint inputs, exact full concatenation, and a
   partition-specific conclusion matrix.

### 9.4 Guard-first matrix

1. Isolate every section-6 fixture and assert its exact first reason or covered-negative state.
2. Exercise hierarchy/control for p, reject, adjusted p, alpha, and a scalar jointly derived from two
   authorized outcomes; include the all-NumPy omnibus gate. Independently isolate
   `correct-numpy-omnibus-assert-gate` with three authorized headers and assert
   `hierarchical-gatekeeping-present`. Cover `ast.Assert.test`, `ast.Match.subject`, every non-`None`
   `match_case` guard, boolean short-circuit operands feeding each enumerated node, the structural
   execution-prevention residual, and an unresolvable residual edge that must stop
   `pvalue-control-dependence-unresolved`.
3. Reproduce every pseudoreplication 3.0 S2 cardinality source, registered draw factor case, reducer,
   count ratio, sorted-index statistic, member/helper edge, and sink under the new module. Add the
   resolved label-permutation maxT fixture and pin conclusion lineage to registered `.pvalue` members.
   Independently isolate `correct-unresolved-cardinality-maxT` with `range(20 * len(frame))`; it must
   stop `resampling-cardinality-unresolved` before any reducer/sink requirement.
4. Test every exact statistics prefix in section 4.9, including uncalled helpers and dynamic
   attributes. Test both exact `sem`/`t.ppf` exemptions and every forbidden consumer edge. Exercise
   every admitted bare `t.ppf` probability and refuse arithmetic, named, container, and helper-returned
   probabilities through the normal statistics-prefix abstention. At `N = 5`, prove `P = 0.99` and
   `P = 0.995` fail the mirrored one-sided/two-sided product rule; cover both mirrored expressions and
   all three conventional family-alpha values under exact Decimal arithmetic.
5. Combine guards in reverse source order and across separate X4 helpers; predicate rank, not line
   order, must select the outward reason.

### 9.5 Prose tripwire over every new predicate

Instrument the contract dispatch, snapshot validator, CSV domain derivation, source envelope, import
resolver, X4 expansion, reader census, call-count expansion, uniform-API check, operand and row-set
proofs including the exact `.query` call shape, `.pvalue` member graph, extremum guard, correction API
grammar, correction-name census, manual-adjustment/off-grammar transform closure, bare-literal product
rule, direct-`P` order-14/order-15 partition, decision-threshold grammar, hierarchy/assert/match/
short-circuit/execution-prevention graph, partition graph, unresolved/resolved resampling graph and
distinct reason projection, statistics-prefix census and mirrored `t.ppf` product exemption,
conclusion graph, guard-terminal export census, sink graph, observation projection, detector
comparison, and wording-slot projection.

For a fixed candidate and every isolated guard fixture, mutate comments, docstrings, Markdown,
reports, task text, unrelated strings, output labels, and human-readable format text; add and remove
reports entirely. Normalized observation/candidate bytes and first reasons must remain identical.
Rename non-callee identifiers in turn to `bonferroni`, `holm`, `sidak`, and
`benjamini_hochberg`; normalized observations and first reasons must remain identical. The paired
control moves each spelling into the callee terminal slot and must change only the
correction-name-census predicate.
Delete or replace a required structural literal in its authorized AST slot and prove that the
appropriate predicate changes. A prose-only correction claim never suppresses, and code-only guard
structure suppresses regardless of its surrounding prose.

### 9.6 Registry, replay, and regression gates

1. Qualified-lane registry selection and the ordinary CLI: no new module, binding, candidate, or
   Finding; existing qualified bindings and installed pins match byte-identical identities. The
   enclosing two-lane registry digest changes only as specified in section 8.1.
2. Development registry: exactly one new check/binding/detector identity; candidates remain
   evaluation-only and draftable only with wording profile v1.
3. Freeze the new profile object and semantic digest; prove all existing pseudoreplication wording
   profile bytes/digests unchanged.
4. Replay every new positive, covered negative, and abstention byte identically.
5. Run a checked-in deterministic corpus-census test over the 98 opened `analysis.py` files. It must
   reproduce exactly: 19 files with at least two slice-1 calls; 12 with exactly two; seven with
   exactly three; zero with at least three calls to a single registered API; and, among the seven,
   exactly two `ttest_ind` plus one `mannwhitneyu` call per file. Among the 12 two-call files, exactly
   two are one-`ttest_ind`/one-`mannwhitneyu` mixes; they still stop at the order-8 incomplete census
   before API uniformity. The census must also prove zero terminal callee-slot matches from section
   4.8.
6. Run all 98 opened pseudoreplication scripts, all 108 dependence-growth cases, and the 155-case
   regression corpus through their normal paths. No existing case lock is rewritten to manufacture
   `1.2.0` authority. Qualified Finding counts and bytes remain unchanged; the new development lane
   emits zero Findings.
7. Run the section-8.1 two-registry differential gate. Permit changes only in the enumerated
   development registry and directly registry/lock-derived bytes; prove all `GrantPin`, grant,
   qualification, metric-set, threshold-policy, and qualified Finding bytes remain identical and
   have no lane-inclusive-digest derivation.
8. Retire no test. Any implementation-time outcome change must be named by case and causal rule in
   this design's later BUILD-NOTES.
9. Complete the repository-required `ruff check .`, `ruff format --check .`, `mypy src`, `pytest`, and
   `python scripts/validate_starter.py` gates.

## 10. Existing opened-case expectations

### 10.1 Existing multiple-testing/BH component cases

The eight calculation/BH cases and five scientific-recognition cases already recorded in the
155-case ledger retain their exact current component outcomes:

```text
case:baseline:calculation:bh:removal
case:baseline:calculation:bh:replay
case:baseline:calculation:bh:unsupported
case:calculation:bh-ambiguous
case:calculation:bh-corrected-twin
case:calculation:bh-hard-negative
case:calculation:bh-positive
case:layout:calculation:bh:sidecar
case:scientific:multiple-testing:ambiguous
case:scientific:multiple-testing:hard-negative
case:scientific:multiple-testing:positive
case:scientific:multiple-testing:removal
case:scientific:multiple-testing:replay
```

They use calculation inputs or the old two-CSV/question-only authority, not the new `1.2.0` code-lane
authority. The new adapter therefore returns `verified-contract-authority-unavailable` if invoked on
their unchanged records; it emits no candidate and no Finding. Their existing modules continue to
produce byte-identical results.

### 10.2 Opened pseudoreplication envelopes

All 98 opened `analysis.py` files lack a new `1.2.0` authority and therefore first abstain
`verified-contract-authority-unavailable` in the new lane. No opened script contains a terminal
callee slot from the correction-name registry.

Nineteen opened scripts currently resolve at least two slice-1 family-test calls:

```text
11af5bb3f9b7e8e0b293
5ef43dbf631adcf3daec
5b80f0787b1b6c47048b
f4e4d89ac44385a18261
23cc44d49100a68655c5
540f7dfdf1614ceda57d
4d64fa6416ee8406f678
4e24fb76c83774381e41
6dfee3d81dba1754e893
71bd62d3b1b9d590020a
7edfc9aa77704a8a46b8
912aee5d3e2b3997a652
40496ca2298519b8825d
472f5d15184e7ee55bb2
95bf6d32f231a92494c4
d415b84d1e942c483f28
ef9e199c282b9038e4c3
4e9bd2ac9d532a4b45e8
6dffe3d7986dc5675127
```

This list is a regression surface, not a relabeling. If each script is copied into an answer-visible
fixture and deliberately given a matching three-member `1.2.0` authority solely to exercise later
predicates, the twelve scripts with two registered calls stop
`authorized-family-test-census-incomplete`; the seven scripts with three calls stop
`mixed-test-api-family` because each combines `ttest_ind` and `mannwhitneyu`. The latter decision is
made before operand resolution. No current opened script has three calls to one slice-1 API, so none
becomes a multiple-testing candidate by adding authority alone.

The original pseudoreplication outcomes, including qualified Findings and family-C abstentions, stay
exactly as recorded. The new lane does not reinterpret their contracts, labels, or case roles.

## 11. Envelope 10 protocol

Envelope 10 is class-pure: six blind multiple-testing positives and nine blind negatives. It has a
new briefing, independently isolated authors/custodian, pre-contact prompt/role/closure freezes, and
the established canonical digest chronology. No author sees the detector grammar, API registries,
wording, prior cases, or outputs.

The six positive roles are:

1. repeated explicit calls with no recognized correction;
2. exact contract-outcome loop with no recognized correction;
3. exact contract-outcome comprehension with no recognized correction;
4. X4 helper/container family with no recognized correction;
5. registered strict-subset correction plus raw conclusions for excluded members; and
6. exact adjusted-value Bonferroni on a strict subset plus raw conclusions for excluded members.

The nine negative roles are frozen as:

| Role | Required realization | Expected first outcome |
|---|---|---|
| N1 | complete `multipletests(pvalues)` with omitted method | covered negative |
| N2 | hand-written Sidak decision thresholds | `unresolved-decision-threshold` |
| N3 | complete `pingouin.multicomp` correction | `unresolved-manual-correction-present`; also records statistics-prefix realization |
| N4 | complete authorized family plus one sensitivity duplicate | `extra-registered-test-outside-authorized-family` |
| N5 | discovery/validation split with additional disjoint row masks | `selected-group-row-completeness-unproven` |
| N6 | all-NumPy joint-outcome gate with separately emitted branches | `hierarchical-gatekeeping-present`; also records partition realization |
| N7 | local diagnostic calls but conclusions from upstream loaded adjusted p-values | `upstream-correction-lineage-unresolved` |
| N8 | label-permutation maxT over all outcomes | `permutation-family-control-present` |
| N9 | `N = 5`, `p < 0.01` for each member, with the complete Bonferroni correction outside the analyzed AST | `unresolved-decision-threshold` by the bare-literal product rule |

The frozen role map records every role each negative actually realizes, the designed first guard, and
any secondary guard. Development fixtures independently isolate guards that are combined in N3 or
N6.

The envelope hard stops are only:

- zero negative candidates (`0/9`);
- zero Findings anywhere, including the development cases and all ordinary qualified/regression
  surfaces;
- byte-identical replay for all 15 cases; and
- no false accusation in the latest 36 class-specific blind cases, or in all available
  class-specific blind cases until 36 exist.

First-contact recall is reported exactly as `positive candidates / 6`, with each miss and first
abstention reason. It has no pass gate in Envelope 10. The class-specific trailing-window requirement
of at least 50% begins only after 18 blind multiple-testing positives exist; before that point it is
not computed as a promotion threshold. Pseudoreplication history remains a separate series.

Lifetime class-specific false accusations are reported separately and do not replace the latest-36
hard stop. Every envelope record also states the number and exact structural shapes of its family-C
analogue negatives, including every secondary guard realized by a role. First-contact recall is
expected to be near the floor because ordinary analyses often include non-exempt assumption checks
such as `scipy.stats.shapiro` or `scipy.stats.levene`; the blind briefing must not hint that authors
should omit or avoid assumption checks.

Passing these hard stops does not install a grant or pin. Any later qualification or production
promotion requires its own accepted ADR, frozen exact identity, applicable public schema support,
qualification record, grant, and production pin.

## 12. File-by-file implementation list

| File or surface | Planned change |
|---|---|
| New `docs/implementation/ADR-0077-...md` (final number/title assigned at build) | Record the accepted 1.2.0 authority meaning, candidate predicate, development-only identity, finite counterevidence protocol, wording profile, the new closed callee-terminal identifier evidence channel from section 4.8, both required section-8.2 residual/deviation notes, and decision provenance before behavior changes. |
| `src/sc_referee/scientific_requirement_contract.py` | Add explicit 1.2.0 dispatch, new family authority/snapshot validators, and version-aware snapshot calls while retaining literal 1.0.0/1.1.0 branches and error strings. |
| `src/sc_referee/method_contract_run.py` | Bind the new authorized CSV digest and carry 1.2.0 authority through preflight, lock, Answer, verification, and replay without changing 1.0.0/1.1.0 projections. |
| New `src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v1.py` | Copy the necessary 3.1 AST/dataflow machinery and implement the call, family/member, correction, threshold, guard, conclusion, and sink predicates. |
| New `src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v1.py` | Validate authority/CSV facts, invoke the new analyzer once, construct receipts/evidence projection, localize exceptions, and expose check/adapter/grammar `1.0.0`. |
| New `src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v1.py` | Register the new detector identity and validate the two conflicting canonical observed operands before delegating the bounded scalar comparison. |
| `src/sc_referee/detectors/method_conflict_registry.py` | Dispatch the exact new detector only for the new development binding. Leave all existing detector dispatches unchanged. |
| `src/sc_referee/detectors/method_conflict_finding.py` | Add the independent versioned wording profile, semantic digest, slot validation, and development draft path; do not edit pseudoreplication profile objects. |
| `src/sc_referee/scientific_checks/profiles.py` | Add the new check/module/binding to the development projection only, preserve the old question-only multiple-testing module, and include new implementation identities in the release projection. |
| `src/sc_referee/scientific_checks/integration.py` | Admit the exact new static-source subject/version in development only. |
| Detector/scientific-check capability manifests and `src/sc_referee/resources/scientific-check-manifests-v1/registry.json` | Add immutable 1.0.0 identities and the development binding; regenerate canonical resources without changing qualified binding identities. |
| New `tests/test_scientific_requirement_contract_v1_2.py` and existing contract lifecycle tests | Add the 1.2.0 matrix and HEAD-`08c0ccb` 1.0.0/1.1.0 byte/digest/error-string goldens. |
| New `tests/test_code_csv_multiple_testing_dataflow_v1.py` | Implement sections 9.2-9.4, every abstention code, every named adversarial fixture, and guard precedence. |
| New adapter/detector/wording test modules | Pin observation projection, local exception behavior, detector identity, wording object/digest/slots/non-inferences, and development no-Finding behavior. |
| Registry, integration, capability, grant/pin-isolation, and replay tests | Prove development-only registration, the exact section-8.1 permitted digest churn, absence of lane-inclusive digest derivation in every `GrantPin`/grant/qualification/Finding field, and byte-identical qualified pseudoreplication/complete-domain behavior. |
| Prose-tripwire tests | Instrument every predicate named in section 9.5 and prove byte invariance under all forbidden prose mutations. |
| New deterministic opened-corpus census test | Pin the section-9.6 counts and exact per-file API composition without executing project-authored code. |
| New `evaluation/development/multitest-code-slice-v1/` | Store canonical answer-visible fixture sources and expected first outcomes; qualification use is forbidden. |
| Future `evaluation/development/blind-envelope-10-.../` | Freeze and run the separate 6-positive/9-negative protocol only after the implementation and answer-visible guard matrix are green. |
| `evaluation/regression-corpus-v1/ledger.json` | Keep existing case roles, selectors, expected outcomes, and bytes unchanged; new answer-visible multiple-testing fixtures live only in the new development corpus. |
| `docs/implementation/SCHEMA_GAP_REGISTER.md` | Change only if build review finds an unresolved conflict with accepted public schemas; do not silently choose. No public-schema change is planned for a development-only lane. |
| `MANIFEST.sha256` and generated derived manifests | Refresh only after all required gates pass. |

The section-12 registry/isolation tests must assert these literal frozen values, not labels or a live
lookup: adapter implementation
`sha256:6900611a3ef6c06be5740df14333eac5d789c6c93165b8826c796a8b4de87170`, recognition grammar
`sha256:69256d48b46f16d7c144e01d5b4509470e9b187bf3db4f7e259d782459c2d476`, dependence Finding profile
v2 `sha256:1dad7c14985fbfb89a7f8fe24a5e7f36d07a7c9fc6f76b4d14951cc71337c04a`, and wording profile v1
`sha256:0440fdb918eb04ff975e7129c4152a2d681f3f4203ae8c7a1f8fc9ebf8916288`.

No implementation file is changed by this design-only session.

## 13. Build acceptance checklist

A build conforms to this design only if all are true:

1. the ADR is accepted before semantic implementation changes;
2. every ordered predicate, exact registry, abstention code, and adversarial fixture above is present;
3. old `1.0.0`/`1.1.0` contract outputs, digests, and error strings pass the golden test;
4. the qualified pseudoreplication `3.1.0` adapter implementation
   `sha256:6900611a3ef6c06be5740df14333eac5d789c6c93165b8826c796a8b4de87170`,
   recognition grammar
   `sha256:69256d48b46f16d7c144e01d5b4509470e9b187bf3db4f7e259d782459c2d476`,
   Finding-profile v2
   `sha256:1dad7c14985fbfb89a7f8fe24a5e7f36d07a7c9fc6f76b4d14951cc71337c04a`,
   wording-profile v1
   `sha256:0440fdb918eb04ff975e7129c4152a2d681f3f4203ae8c7a1f8fc9ebf8916288`,
   and all complete-domain identities, wording, grants, pins, outcomes, and Finding bytes are
   unchanged;
5. the old question-only multiple-testing component remains byte- and outcome-identical;
6. the new binding exists only in the development projection and emits zero Findings;
7. only section 8.1's enumerated registry/lock-derived bytes change, and no `GrantPin`, grant,
   qualification, or Finding byte derives from a lane-inclusive digest;
8. all answer-visible development fixtures and existing opened/regression surfaces replay exactly;
9. the deterministic opened-corpus census reproduces section 9.6 exactly;
10. the prose tripwire covers every new predicate; and
11. every repository-required command completes successfully.

Any ambiguity discovered during implementation is an abstention or a recorded schema/design gap. It
is not resolved by broadening evidence, inferring intent, or weakening a finite guard.

## 14. Revision 1 changelog

Every Revision 1 item below was intended to add an abstention/validation gate, close an admitted
grammar, add a negative test, or restore a recon guard/accounting clause. The former sentence "None
enlarges candidate eligibility" is withdrawn: MJ-3's closed node list omitted assert/match gates that
Revision 0 and recon 3.2 covered, thereby widening candidate eligibility. Revision 2 closes that gap.

| Review item | Sections changed | Narrowing or restored clause |
|---|---|---|
| BL-1 | 4.7, 6, 9.2, 11 | Added the exact-Decimal `a * N` product-rule abstention, the isolated `N = 5`, `p < 0.01` off-AST Bonferroni fixture, and blind-negative role N9. |
| BL-2 | 4.7, 4.10, 9.2-9.3 | Made 4.6/4.7 value production normatively closed; every family-`.pvalue` `BinOp`/`Call`/comparison transform outside it abstains `unresolved-manual-correction-present`, while direct unrecognized thresholds take the closed threshold-refusal branch. Removed the judgment phrase identified by review. |
| BL-3 | 5.1, 6, 9.4 | Restored recon 3.5: every repeated generator/registered draw consuming authorized family data abstains when cardinality is not a closed S2 constant; no reducer/sink and no skip-on-unresolved behavior is admitted. |
| MJ-1 | 8.1, 9.6, 12, 13 | Enumerated the only legitimate development-registry and direct lock/replay byte churn and added a differential gate proving no `GrantPin`, grant, qualification, metric/threshold, or qualified Finding byte derives from the lane-inclusive digest. |
| MJ-2 | 4.4, 9.2 | Replaced the open row-mask exemption with the exact copied `_QUERY` regex plus exact CSV truth evaluation; all other masks are unproved. |
| MJ-3 | 5.1, 9.4 | Defined jointly-derived by a bounded backward projection closure, enumerated its edge kinds and every control-node kind, and bounded *controls* so ordinary payload edges do not satisfy the guard. |
| MJ-4 | 4.10, 9.2 | Replaced the open extremum phrase with seven exact syntactic families and explicitly made `argmin`/`idxmin`/partition/heap forms and every unlisted form abstain. |
| MJ-5 | 4.9, 9.4 | Restricted `t.ppf` probability to a bare literal in `{0.9, 0.95, 0.975, 0.99, 0.995}`; arithmetic and indirection take the normal statistics-prefix abstention. |
| MJ-6 | 1, 9.5 | Removed the undefined string category; format arguments retain structural value lineage while format text is never read, matched, or compared, and prose mutations are tripwired. |
| MJ-7 | 11 | Restored the latest-36 false-accusation hard stop, separate lifetime reporting, and per-envelope count/shape accounting for family-C analogue negatives. |
| MJ-8 | 4.10, 6, 9.2 | Made every family `.pvalue` flow to exact `.to_csv`, `numpy.savetxt`, or `json.dump` an `unresolved-pvalue-consumer` abstention and added an isolated downstream-correction export fixture. |
| MJ-9 | 6, 9.2, 11 | Added the required isolated bare-literal Bonferroni fixture and made the same structure a recorded envelope-negative role. |
| MJ-10 | 4.8, 9.3, 9.5, 12 | Restricted name reading to terminal callee slots, excluded all non-callee identifiers, named the closed identifier channel for the ADR, and added paired mutation tests. |
| Minor 1 | 4.6, 9.3 | Made correction coverage depend on recognized inputs before return handling; every unsupported return abstains and can never become `none`. |
| Minor 2 | 4.6, 9.3 | Pinned the `false_discovery_control` axis grammar to omitted, literal `0`, literal `-1`, or literal `None`; every other form abstains. |
| Minor 3 | 4.7, 4.10, 9.2 | Enumerated `<`, `<=`, `>`, and `>=` in both operand orders and excluded every other comparison form. |
| Minor 4 | 5 order 4, 9.1 | Quantified CSV usability as every authorized outcome cell on every row finite numeric plus at least two rows per group per outcome. |
| Minor 5 | 4.2, 9.2 | Chose order equality: only a byte-for-byte order-equal contract iterable expands; set equality, sorting, and reordering are insufficient. |
| Minor 6 | 3.3, 4.4 | Deleted the undefined row-lineage verb and stated the positive and abstention boundaries solely as exact row removal/evaluable-set conditions. |
| Minor 7 | 4.7, 9.3 | Limited manual-adjustment `N` to an integer literal or closed module constant exactly equal to the completed census. |
| Minor 8 | 8, 12, 13 | Named the four frozen pseudoreplication adapter/grammar/Finding-profile/wording digests in isolation and acceptance gates. |
| Minor 9 | 9.6, 10.2, 12, 13 | Added a checked-in deterministic census gate for all 98 files, the 19/12/7 counts, exact mixed-API compositions, zero same-API-three-call cases, and zero correction-name terminal slots. |
| Minor 10 | 9.5 | Promoted non-callee renaming to `bonferroni`, `holm`, `sidak`, and `benjamini_hochberg` into the full prose-tripwire mutation set. |
| Minor 11 | 11 | Documented expected near-floor first-contact recall from ordinary assumption-check abstentions and prohibited briefing hints to avoid those checks; no predicate changed. |

## 15. Revision 2 changelog

Every Revision 2 behavioral change only adds an abstention or narrows an exemption. The ADR notes and
changelog correction disclose existing boundaries without changing candidate eligibility.

| Review item | Sections changed | Narrowing or required record |
|---|---|---|
| MJ-3 still open | 5 order 16, 5.1, 6, 9.4.2, 9.5 | Added `ast.Assert.test`, `ast.Match.subject`, `match_case` guards, boolean short-circuit operands, and the structural execution-prevention residual; unresolved residual reachability abstains. Added `correct-numpy-omnibus-assert-gate`. |
| ND-1 | 4.4, 9.2.4, 9.5 | Limited the row-preserving exemption to a one-literal-argument `.query` call matching `_QUERY`; boolean-mask subscripts are never eligible. |
| ND-2 | 4.9, 9.4.4, 9.5 | Mirrored the BL-1 product rule into `t.ppf` using exact `(1 - P) * N` and `2 * (1 - P) * N` checks. |
| ND-3 | 4.7, 9.2.6, 9.5 | Made direct-`P` comparisons exclusive to order 15 and excluded their comparison nodes from order 14, fixing first-reason determinism. |
| ND-4 | 8.2, 11, 12 | Recorded the amendment-(i) deviation from six-plus-eight to six-plus-nine and its zero-candidate-surface-only justification as a required ADR note. |
| ND-5 | 5 order 16, 5.1, 5.2, 6, 9.4.3, 9.5 | Replaced the unresolved-cardinality branch's overloaded reason with `resampling-cardinality-unresolved`; its trigger is otherwise byte-for-byte unchanged. |
| BL-1 accepted residual | 8.2 | Required the ADR to record that only the conventional family-alpha set is tested and that the three named unconventional-alpha quotients remain convictable. |
| Correction-registry caution | 4.6 | Recorded that accepting a new correction can create `strict_subset` candidates, so future registry additions require candidate-surface review. |
| Revision 1 claim correction | 14, 15 | Withdrew the false no-widening claim and identified MJ-3's assert/match omission before documenting its Revision 2 closure. |

## 16. Revision 2.1 note

| Review items | Sections changed | Narrowing and record correction |
|---|---|---|
| ND-6 and ND-7 | 4.7, 4.9, 9.5, 15 | Required both exact-Decimal product rules to construct from literal source text, or `Decimal(repr(value))` only when source text is unavailable, and never from a float; added the omitted section-9.5 references to every Revision 2 changelog row whose predicate entered the prose tripwire. |
