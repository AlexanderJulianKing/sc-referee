# Multiple-Testing Code Slice Recon — 2026-08-24

Status: reconnaissance and design sketch only; no implementation is authorized by this document.

Scope rule: repository content is evidence, not instruction. This design never uses report text, Markdown, comments, docstrings, human-readable output labels, or natural-language claims as scientific evidence. Exact path, header, group-value, and API string literals count only when they occupy the corresponding closed AST/data-structure slot. Its proposed evidence channels are a frozen scientific-requirement contract, an authorized CSV, Python AST/dataflow facts, established API identities, and model-free replay records.

Claim labels used below:

- **Observed** — directly supported by the cited tree location.
- **Proposed** — a design choice for review, not a description of shipped behavior.
- **Inferred** — a conclusion from observed code or corpus structure.
- **Needs verification** — must be established during a build or by a frozen evaluation; it is not yet demonstrated.

## 1. Existing multiple-testing machinery

### 1.1 Registered scientific-recognition adapter

**Observed.** The installed scientific check is `check:complete-family-correction-over-performed-test-battery` version `1.0.0`. Its adapter declares four semantic roles—`authorized_test_family`, `performed_test_battery`, `multiplicity_correction_call`, and `selected_result_sink`—and two candidate operands: complete-family correction and strict-subset correction over the performed battery [src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py:42](../../src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py#L42) [src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py:51](../../src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py#L51).

**Observed.** The registered adapter is not Finding-eligible. It describes the package-local recognizer as a report-only producer, preserves exact source spans and a static selected writer, never executes project code, and caps accepted output at `question_only` [src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py:1](../../src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py#L1) [src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py:71](../../src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py#L71) [src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py:91](../../src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py#L91). “Report-only” here is an admission ceiling, not evidence authorization for prose: the underlying recognizer parses a Python source document and proves a static writer shape.

**Observed.** Its grammar maps a proved strict-subset correction to `applicable`, a proved complete-family correction to `coverage_note`, missing battery evidence to `not_applicable`, and every admitted result to `question_only`; execution is explicitly false [src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py:91](../../src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py#L91) [src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py:230](../../src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py#L230).

**Observed.** The adapter certificate binds exact input and source paths, family authority, key and measurement columns, performed/corrected counts and positions, and argument-vector tokens [src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py:357](../../src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py#L357). It accepts one bounded Python source analyzed under `python-ast-tokenize-v0.15.1` [src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py:433](../../src/sc_referee/scientific_checks/multiple_testing_recognition_adapter.py#L433).

### 1.2 Package-local analyzer and what it proves

**Observed.** The package is an unregistered shadow recognizer whose own contract says it is static, consumes controller-owned p-value/family authority, produces a replayable certificate, and never executes the analyzed project [src/sc_referee/multiple_testing_recognition/adapter.py:1](../../src/sc_referee/multiple_testing_recognition/adapter.py#L1). Its output distinguishes `correction_subset` from `correction_complete`, but remains report-only/question-only [src/sc_referee/multiple_testing_recognition/adapter.py:136](../../src/sc_referee/multiple_testing_recognition/adapter.py#L136) [src/sc_referee/multiple_testing_recognition/adapter.py:200](../../src/sc_referee/multiple_testing_recognition/adapter.py#L200) [src/sc_referee/multiple_testing_recognition/adapter.py:238](../../src/sc_referee/multiple_testing_recognition/adapter.py#L238).

**Observed.** The analyzer has useful closed identities already:

- supported tests: `scipy.stats.ttest_ind` and `scipy.stats.mannwhitneyu`;
- supported correction: `statsmodels.stats.multitest.multipletests` with `method="fdr_bh"`;
- a repository BH identity, presently refused by the source-shape analyzer; and
- pinned SciPy/statsmodels versions in its certificate surface.

These are defined together [src/sc_referee/multiple_testing_recognition/python_analyzer.py:93](../../src/sc_referee/multiple_testing_recognition/python_analyzer.py#L93), and the current repository-BH refusal is explicit [src/sc_referee/multiple_testing_recognition/python_analyzer.py:254](../../src/sc_referee/multiple_testing_recognition/python_analyzer.py#L254).

**Observed.** The old accepted source shape is substantially narrower than the proposed code lane. It refuses every `for`, `async for`, and `while`; requires a static selected artifact path; binds separate p-value-family and measurement CSVs; and requires one exact human family-authority record with scope `all_rows` [src/sc_referee/multiple_testing_recognition/python_analyzer.py:186](../../src/sc_referee/multiple_testing_recognition/python_analyzer.py#L186) [src/sc_referee/multiple_testing_recognition/python_analyzer.py:233](../../src/sc_referee/multiple_testing_recognition/python_analyzer.py#L233) [src/sc_referee/multiple_testing_recognition/python_analyzer.py:261](../../src/sc_referee/multiple_testing_recognition/python_analyzer.py#L261) [src/sc_referee/multiple_testing_recognition/python_analyzer.py:323](../../src/sc_referee/multiple_testing_recognition/python_analyzer.py#L323).

**Observed.** Within that closed shape it proves one list-comprehension test battery, one exact `multipletests(..., method="fdr_bh")` call, correction input equal to the full p-value name or a nonnegative contiguous slice, and one exact `write_text` report binding [src/sc_referee/multiple_testing_recognition/python_analyzer.py:865](../../src/sc_referee/multiple_testing_recognition/python_analyzer.py#L865) [src/sc_referee/multiple_testing_recognition/python_analyzer.py:1217](../../src/sc_referee/multiple_testing_recognition/python_analyzer.py#L1217) [src/sc_referee/multiple_testing_recognition/python_analyzer.py:1251](../../src/sc_referee/multiple_testing_recognition/python_analyzer.py#L1251) [src/sc_referee/multiple_testing_recognition/python_analyzer.py:1271](../../src/sc_referee/multiple_testing_recognition/python_analyzer.py#L1271) [src/sc_referee/multiple_testing_recognition/python_analyzer.py:1291](../../src/sc_referee/multiple_testing_recognition/python_analyzer.py#L1291).

**Observed.** Its verifier turns performed and corrected p-value position tokens into multisets, proves either equality or strict subset, and recomputes BH with exact decimal arithmetic rather than trusting emitted adjusted values [src/sc_referee/multiple_testing_recognition/certificate.py:188](../../src/sc_referee/multiple_testing_recognition/certificate.py#L188) [src/sc_referee/multiple_testing_recognition/certificate.py:1806](../../src/sc_referee/multiple_testing_recognition/certificate.py#L1806). The calculation-check implementation independently recomputes BH adjusted values and records mismatches [src/sc_referee/calculation_checks/bh.py:185](../../src/sc_referee/calculation_checks/bh.py#L185) [src/sc_referee/calculation_checks/bh.py:405](../../src/sc_referee/calculation_checks/bh.py#L405).

### 1.3 What transfers to a code-lane detector

| Existing element | Transfer decision | Reason |
|---|---|---|
| The four semantic-role names | **Reuse** | They name the needed code facts without implying prose evidence. `selected_result_sink` would mean a code output sink only. |
| Test API identities | **Reuse and version** | They are established APIs and already have certificate semantics. A family must use one normalized API throughout. |
| Per-test argument tokens and performed/corrected position multisets | **Reuse conceptually** | These give a deterministic family census and exact subset/equality relation. The new tokens must be derived from the authorized CSV and outcome-column contract, not an old p-value CSV. |
| `strict_subset_correction` relation | **Reuse** | It is the core demonstrated conflict once gatekeeping/disjoint-family guards pass. |
| Exact BH recomputation | **Reuse as verifier/test oracle only in slice 1** | Runtime p-values are not statically known in the proposed ordinary code path. Numeric BH recomputation becomes decisive only if a later contract authorizes a frozen p-value table. |
| Old separate p-value and measurement CSVs | **Do not reuse** | The new slice binds one authorized analysis CSV and derives the performed family from code dataflow. |
| Old human family-authority record | **Replace with the scientific-requirement contract extension below** | The current scientific requirement contract only allows dependence-specific semantic-role authority; non-dependence requirements must have no such authority [src/sc_referee/scientific_requirement_contract.py:1090](../../src/sc_referee/scientific_requirement_contract.py#L1090). |
| Exact list-comprehension-only grammar and loop ban | **Do not reuse** | The target explicitly includes loops, comprehensions, and repeated calls. |
| Exact selected report writer | **Do not reuse** | No report or prose evidence is permitted. A bounded code sink is required instead. |
| Existing question-only adapter identity | **Leave byte-immutable** | The new lane needs a separate check and detector identity; silently changing a shipped question-only check would conflate qualification histories. |

**Observed.** The current code-lane architecture already separates `qualified` and `development` bindings, and registry identity/digest computation includes both lanes [src/sc_referee/scientific_checks/registry.py:74](../../src/sc_referee/scientific_checks/registry.py#L74) [src/sc_referee/scientific_checks/registry.py:113](../../src/sc_referee/scientific_checks/registry.py#L113) [src/sc_referee/scientific_checks/registry.py:133](../../src/sc_referee/scientific_checks/registry.py#L133). The CLI exposes an explicit `--development-lane` and states that it can never emit Findings [src/sc_referee/cli.py:715](../../src/sc_referee/cli.py#L715).

**Observed.** The qualified pseudoreplication analyzer is a prose-free, non-executing Python-AST lane with bounded parsing, a single-root-`analysis.py` envelope, alternate-analysis-file refusal, helper expansion, a syntactic test census, value/member edges, operand backward slices, and result-to-output reachability [src/sc_referee/scientific_checks/code_csv_dependence_dataflow_v3_1.py:1](../../src/sc_referee/scientific_checks/code_csv_dependence_dataflow_v3_1.py#L1) [src/sc_referee/scientific_checks/code_csv_dependence_dataflow_v3_1.py:29](../../src/sc_referee/scientific_checks/code_csv_dependence_dataflow_v3_1.py#L29) [src/sc_referee/scientific_checks/code_csv_dependence_dataflow_v3_1.py:489](../../src/sc_referee/scientific_checks/code_csv_dependence_dataflow_v3_1.py#L489) [src/sc_referee/scientific_checks/code_csv_dependence_dataflow_v3_1.py:558](../../src/sc_referee/scientific_checks/code_csv_dependence_dataflow_v3_1.py#L558) [src/sc_referee/scientific_checks/code_csv_dependence_dataflow_v3_1.py:930](../../src/sc_referee/scientific_checks/code_csv_dependence_dataflow_v3_1.py#L930).

**Proposed.** Reuse the public framework—inspection context, bounded material lookup, evidence spans, fact/observation records, replay, registry lanes, admission/pin mechanics—and copy only the necessary AST/dataflow primitives into a new versioned multiple-testing module. Do not import or edit private frozen v3.1 implementation helpers. The qualified pseudoreplication detector, adapter, wording profiles, and pin remain byte-identical.

## 2. First-slice misstep class

### 2.1 Exact contract extension

**Proposed.** Add scientific-requirement profile `1.2.0`, leaving `1.1.0` byte-immutable. A multiple-testing requirement record must contain exactly:

```json
{
  "profile_version": "1.2.0",
  "requirement_id": "requirement:authorized-complete-family-correction",
  "material_input_path": "data/measurements.csv",
  "group_contrast_column": "condition",
  "group_contrast_values": ["control", "treated"],
  "outcome_columns": ["marker_a", "marker_b", "marker_c"],
  "registered_test_api": "scipy.stats.ttest_ind",
  "family_member_rule": "one-two-group-test-per-named-outcome-column",
  "correction_scope": "complete-authorized-family"
}
```

Normative constraints:

1. `material_input_path`, `group_contrast_column`, each group value, and each outcome column are nonempty byte-exact UTF-8 strings.
2. `group_contrast_values` is an ordered pair of distinct values.
3. `outcome_columns` is an ordered, duplicate-free list of at least three columns; neither the group column nor any declared unit column may appear in it.
4. `registered_test_api` is exactly one of `scipy.stats.ttest_ind` or `scipy.stats.mannwhitneyu` in slice 1.
5. `family_member_rule` and `correction_scope` have the exact literal values above.
6. The authority snapshot repeats the record and binds the authorized CSV content digest. No path-only authority is sufficient.

The explicit outcome list is intentional. “All numeric columns,” “all endpoints,” or a name-pattern family is not statically closed enough for the first zero-false-accusation slice.

### 2.2 Candidate class

**Proposed.** A development-lane evaluation candidate exists only when all of the following are proven:

1. The authorized family contains `N >= 3` outcome columns.
2. The script performs exactly one registered two-group test for each authorized outcome, using the same normalized test API for all `N` calls.
3. Both operands of each test trace to the single authorized reader and to row selection on the contract group column for the two contract group values, followed by projection of the same authorized outcome column.
4. The `N` p-value members are tracked individually through any admitted container.
5. Code derives a conclusion for every family member from a raw or corrected p-value and that complete family of conclusions reaches a bounded output sink.
6. Either:
   - no family p-value enters any correction operation anywhere in complete analyzed scope; or
   - a recognized correction receives a strict, nonempty subset of the performed family, while conclusions for excluded members are derived from their unadjusted p-values.
7. Every family-C analogue guard in section 3 is discharged.

“Conclusion” is structural and deliberately narrower than “p-value was printed.” It is one of:

- a p-derived boolean from `<`, `<=`, `>`, or `>=` against a finite closed numeric alpha;
- a p-derived `reject` member returned by a recognized correction API; or
- a filtered set/list/dict of authorized outcome names whose membership predicate is one of those booleans.

The boolean or selected outcome identities must reach `print`, a supported file-write sink, or a returned value that reaches such a sink. Merely assigning, storing, or printing numeric p-values is not a conclusion and causes abstention.

### 2.3 Correction census

**Proposed.** Slice 1 recognizes these established correction APIs:

- `statsmodels.stats.multitest.multipletests` with a closed literal method;
- `statsmodels.stats.multitest.fdrcorrection`;
- `scipy.stats.false_discovery_control`; and
- `sc_referee.calculation_checks.bh.benjamini_hochberg`.

It also recognizes these exact manual Bonferroni shapes:

- decision threshold `ALPHA / N`, where `N` resolves to the exact authorized family cardinality; or
- adjusted value `min(P * N, 1)` / `minimum(P * N, 1)`, applied memberwise to the complete p-value container.

A manual BH implementation is not initially accepted as “complete correction” unless its full-family membership and adjusted decisions can be proven by a separate exact grammar. Any sorting/ranking/cumulative-minimum shape that consumes family p-values but does not match that grammar causes abstention as `unresolved-manual-correction-present`; it is never treated as absence of correction.

### 2.4 Out of scope

**Proposed.** The first slice does not decide:

- whether correction is scientifically required absent the frozen family contract;
- families inferred from prose, comments, variable names, captions, or report wording;
- families indexed by windows, row strata, or arbitrary subsets rather than by the explicit outcome-column list (slice 1 varies the outcome column; its row selections are only the two contract group values);
- more than two group levels, paired/repeated-measures tests, regression coefficient families, omnibus/post-hoc structures, interactions, spatial tests, or gene-wide single-cell differential-expression APIs;
- adaptive FDR, weighted hypotheses, online FDR, local FDR, closed testing, alpha spending, selective inference, or graphical gatekeeping;
- cross-language or notebook analyses;
- dynamic API dispatch, dynamic outcome-column construction, reflection, generated code, project execution, or p-values entering unsupported calls;
- correctness of runtime p-values, test assumptions, effect sizes, or the chosen family contract; or
- a correction performed outside the bounded analyzed source closure.

All such cases abstain rather than weaken the candidate predicate.

## 3. Family-C analogue: false-accusation surface

The central risk is not a correct full-family correction—the census handles that directly. It is code whose raw-looking tests belong to a structured testing procedure that the first-slice family model cannot distinguish. The guards below run over complete analyzed scope before a candidate is returned; source position does not change precedence.

### 3.1 Structurally primary and exploratory endpoints

**Observed limitation.** “Primary” and “exploratory” cannot be learned from names, comments, strings, or prose.

**Proposed guard.** If a corrected p-value or reject flag for a strict subset controls whether any remaining family test executes, whether its conclusion is emitted, or which alpha is used for it, abstain with `hierarchical-gatekeeping-present`. If only one corrected/thresholded endpoint reaches a conclusion sink and other p-values are merely printed, step 5 in section 2.2 is unsatisfied; there is no candidate.

**False-accusation mode prevented.** A prespecified primary endpoint with secondary endpoints evaluated only after success could otherwise look like incomplete correction.

**Declared residual.** If all raw endpoint decisions are output independently and the only evidence that one is primary is prose, the code contradicts the frozen complete-family contract. The Finding wording is about that contract conflict, not a claim that the scientific gatekeeping plan is invalid.

### 3.2 Hierarchical or gatekeeping procedures

**Proposed guard.** Any p/reject/alpha value from one test or correction that controls another test call, correction call, conclusion sink, branch, loop, or family container causes `hierarchical-gatekeeping-present`. Any recognized closed-testing, alpha-recycling, or gatekeeping API causes the same abstention. Unresolved control dependence causes `pvalue-control-dependence-unresolved`.

**False-accusation mode prevented.** A valid serial or hierarchical family is not equivalent to applying one flat correction to every executed p-value.

### 3.3 Disjoint families

**Proposed guard.** Abstain with `multiple-family-partition-present` if performed tests are structurally partitioned into two or more p-value containers, correction calls, distinct group contrasts, distinct outer-loop strata, or separately output decision collections. Do not merge partitions merely because they use the same API or CSV.

**False-accusation mode prevented.** Two independently prespecified families could otherwise be counted as one and make each correction appear to cover a strict subset.

**Conservative consequence.** A program that creates temporary per-batch containers before concatenating them into one proved complete correction also abstains in slice 1 unless the concatenation/member identity is exact and no partition-specific conclusions exist.

### 3.4 Corrections applied upstream

**Proposed guard.** Candidate p-values must be direct `.pvalue` members of the registered tests proved in the current source. A test wrapper, imported p-value array, adjusted-p column, correction result loaded from a second file, or p-derived value entering an unresolved helper causes `upstream-correction-lineage-unresolved`. A second accepted reader anywhere causes `additional-accepted-reader-present`; statistics APIs in another Python file cause `statistics-api-imported-outside-analysis-py`.

**False-accusation mode prevented.** The code under inspection may consume already adjusted values or delegate correction to a trusted upstream stage.

### 3.5 Permutation maxT/minP and resampling family control

**Proposed guard.** Abstain with `permutation-family-control-present` when a loop/comprehension or vectorized draw repeatedly consumes the authorized outcome matrix, computes multiple test statistics per draw, reduces each draw by `max`/`min`, or compares observed statistics with the joint null distribution to derive p/reject outputs. Resolve loop cardinality through literals, closed constants, helper defaults, container lengths, and draw `size` factors as in the qualified code-lane guard style. Any unresolved resampling construct consuming the family causes the same abstention.

**False-accusation mode prevented.** MaxT/minP controls family error without a conventional `multipletests` call.

### 3.6 Screen-then-confirm pipelines

**Proposed guard.** Abstain with `screen-then-confirm-present` if a p-value, score, or model result selects outcomes or rows and the selected members are retested on a provably disjoint holdout split; also abstain if disjointness cannot be proven but the screening result controls the confirmatory test census.

**False-accusation mode prevented.** A discovery screen and independent confirmation stage are not one flat performed family.

### 3.7 Closed-world statistics guard

**Proposed guard.** Any call under a registered statistics prefix that is neither the authorized family test, a recognized correction, nor an explicitly descriptive reducer causes `unresolved-inference-sibling-present`. Multiple authorized-family candidates or any extra registered inferential test causes `multiple-test-family-candidates` or `extra-registered-test-outside-authorized-family` before correction absence is considered.

**Reason.** These are the multiple-testing analogue of the pseudoreplication family-C guards. When structure cannot distinguish a competing inferential procedure, the only zero-false-accusation result is abstention.

## 4. Finding wording profile

**Proposed.** Create and freeze a versioned profile on day one:

- profile ID: `code_csv_multiple_testing_finding_profile_v1`;
- profile version: `1.0.0`;
- immutable title:

> Analysis code contradicts the frozen complete-family correction requirement

- bounded summary template:

> The frozen requirement names {AUTHORIZED_COUNT} outcome columns under group column {GROUP_COLUMN} as one {TEST_API} family. Static code establishes {PERFORMED_COUNT} matching tests, but {CORRECTED_COUNT} family p-values enter registered correction before p-derived conclusions reach output. The outcome columns are {OUTCOME_COLUMNS}. This conflicts with the frozen complete-family-correction requirement.

Allowed slots are only:

- integers `AUTHORIZED_COUNT`, `PERFORMED_COUNT`, and `CORRECTED_COUNT`;
- normalized established API identifier `TEST_API`;
- exact contract column identifier `GROUP_COLUMN`; and
- the ordered exact contract column-identifier list `OUTCOME_COLUMNS`.

No path, p-value, threshold, effect, result label, prose fragment, comment, docstring, report field, or inferred scientific judgment is a wording slot.

Required frozen non-inferences include: the contract may be wrong; the code may never execute; correction may exist outside the inspected closure; the record does not establish inflated error rates, invalid science, or which conclusions the authors intended; and the detector does not read prose.

## 5. Proposed evidence predicate and identities

### 5.1 Ordered checks

Predicate order is normative; no later observation may override an earlier abstention.

1. **Authority profile.** Resolve exactly one accepted `1.2.0` complete-family requirement and byte-identical authority snapshot. Otherwise abstain `verified-contract-authority-unavailable` or `authorized-test-family-shape-unsupported`.
2. **Family cardinality.** Require an ordered unique outcome list of length at least three. Otherwise abstain `authorized-family-cardinality-below-three`.
3. **Material binding.** Resolve exactly one authorized CSV whose path and digest match the contract. Otherwise abstain `frozen-authority-material-mismatch`.
4. **CSV facts.** Within existing byte/row/column/field bounds, prove the group column, exactly the two declared group values, all outcome columns, and sufficient finite cells for each two-group test. Otherwise abstain `authorized-family-csv-domain-unavailable` or `authorized-group-domain-not-exactly-two`.
5. **Source envelope.** Admit one root `analysis.py`; reject `.ipynb`/`.R`; scan every other Python file for statistics imports. Otherwise abstain `analysis-source-envelope-unavailable`, `alternate-analysis-file-present`, or `statistics-api-imported-outside-analysis-py`.
6. **Bounded AST resolution.** Parse without execution, establish imports/aliases/closed constants, and perform bounded helper/container expansion. Dynamic or over-ceiling constructs abstain `api-resolution-ambiguous` or `dataflow-definition-ceiling-exceeded`.
7. **Reader census.** Require exactly one accepted reader bound to the authorized CSV. Any additional reader abstains `additional-accepted-reader-present`; unresolved lineage abstains `authorized-reader-lineage-unavailable`.
8. **Full test census.** Syntactically census registered inferential calls across complete scope before resolving operands. Two competing family candidates, an unknown statistics call, or an extra registered test abstains with the relevant sibling code.
9. **Authorized battery.** Expand loops, comprehensions, and repeated calls. Prove exactly one same-API test for each authorized outcome and no other member, with both operands selected on the two contract group values from the authorized reader. Otherwise abstain `test-battery-cardinality-unresolved`, `authorized-family-test-census-incomplete`, `mixed-test-api-family`, or `test-operand-lineage-unresolved`.
10. **P-value identities.** Bind the `.pvalue` member of every test and preserve ordered family-member identity through lists, tuples, dicts, loop targets, helper returns, and destructuring. Otherwise abstain `pvalue-family-collection-unresolved`.
11. **Correction census.** Across complete scope, bind every recognized API/manual correction input to exact p-value member positions. Classify the family as `none`, `complete`, `strict_subset`, or `unresolved`. Unresolved correction-like arithmetic/calls abstain `correction-family-lineage-unresolved` or `unresolved-manual-correction-present`.
12. **All safety guards.** Run gatekeeping, partition, upstream, resampling, screen-confirm, statistics-sibling, and unknown-p-consumer guards to a fixed point. Guards dominate `none`/`strict_subset` classification regardless of source order.
13. **Conclusion census.** Prove a p-derived conclusion for every authorized family member and exact reachability to a called output sink. Otherwise abstain `pderived-conclusion-family-incomplete` or `conclusion-output-sink-unavailable`.
14. **Decision.** `complete` is a covered negative; guarded/unresolved cases abstain; `none` or `strict_subset` yields one contract-conflict observation containing only counts, API, contract columns, evidence spans, and semantic-role bindings.
15. **Development admission.** Detector `1.0.0` may emit evaluation candidates/abstentions only under the development lane. It cannot emit a Finding until a sealed envelope passes and a new production pin is accepted and installed.

### 5.2 Closed abstention-code set for slice 1

The proposed code set is:

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
additional-accepted-reader-present
authorized-reader-lineage-unavailable
test-battery-cardinality-unresolved
authorized-family-test-census-incomplete
extra-registered-test-outside-authorized-family
multiple-test-family-candidates
mixed-test-api-family
test-operand-lineage-unresolved
pvalue-family-collection-unresolved
correction-family-lineage-unresolved
unresolved-manual-correction-present
unresolved-pvalue-consumer
hierarchical-gatekeeping-present
pvalue-control-dependence-unresolved
multiple-family-partition-present
upstream-correction-lineage-unresolved
permutation-family-control-present
screen-then-confirm-present
unresolved-inference-sibling-present
pderived-conclusion-family-incomplete
conclusion-output-sink-unavailable
multiple-testing-code-inspection-exception
```

**Proposed.** Ambiguity always maps to one of these abstentions, never to conviction.

### 5.3 Reuse/copy map

**Share without semantic modification:**

- scientific-requirement parsing/version dispatch, extended with the new `1.2.0` record;
- frozen inspection/material lookup and bounded CSV utilities;
- evidence spans, facts, observations, receipts, replay, and canonical projection;
- dual-registry lane selection and the development-lane CLI flag;
- generic admission, qualification-history, pin, and Finding-drafting framework; and
- the exact Decimal BH implementation for certificate fixtures and future frozen-p-value validation.

**Copy into a new multiple-testing module and specialize:**

- bounded AST/import/constant resolver;
- root-`analysis.py` source envelope and alternate statistics-file scan;
- reader census and authorized-reader lineage;
- bounded helper inlining, value/member identity edges, container reconstruction, and output-sink reachability; and
- full-scope registered-call census and guard precedence machinery.

Copying rather than importing private v3.1 helpers keeps the qualified pseudoreplication closure frozen and permits multiple-testing-specific p-family and control-dependence semantics.

**New:**

- family-authority contract fields and CSV family fact;
- loop/comprehension/repeated-call family expansion;
- p-value-member and corrected-position census;
- complete/strict-subset/no-correction classification;
- p-derived conclusion graph;
- the six family-C analogue guards; and
- wording profile v1.

### 5.4 Identity plan

**Proposed identities:**

```text
check:authorized-complete-family-correction-over-code-test-battery
adapter:authorized-complete-family-correction-over-code-test-battery:code-csv-v1
detector:bounded-code-csv-multiple-testing-conflict@1.0.0
code_csv_multiple_testing_finding_profile_v1@1.0.0
```

The new check enters the **development** binding only. The existing question-only multiple-testing check remains registered and byte-immutable. The qualified pseudoreplication binding, detector `3.1.0`, wording profile, grant, and production pin remain untouched. A development evaluation cannot change `installed_pin_matches_live_identity` for either qualified check.

## 6. Development corpus and envelope 10

### 6.1 What is actually available

**Observed.** The 155-case regression ledger includes 13 answer-visible multiple-testing/BH component cases: eight BH-calculation cases and five scientific-recognition cases (`ambiguous`, `hard-negative`, `positive`, `removal`, and `replay`) [evaluation/regression-corpus-v1/ledger.json:1](../../evaluation/regression-corpus-v1/ledger.json#L1). These are regression/development evidence, not blind qualification evidence.

**Observed.** The scientific-recognition fixture supplies the old exact strict-subset form (`pvals[:2]`) and the complete-family twin (`pvals`) [tests/test_multiple_testing_recognition_adapter.py:43](../../tests/test_multiple_testing_recognition_adapter.py#L43). The tests expect the strict subset to become an applicable question-only candidate and the complete correction to become a negative/coverage outcome [tests/test_multiple_testing_recognition_adapter.py:341](../../tests/test_multiple_testing_recognition_adapter.py#L341). These are useful skeletons for the new position-census and subset/equality unit tests, but they use the old two-CSV authority and selected writer, so they are not ready-made code-lane cases.

**Observed.** The BH control family includes a positive, corrected twin, hard negative, and ambiguous control [tests/test_multiple_testing_control_family.py:71](../../tests/test_multiple_testing_control_family.py#L71). Its hard-negative distinction is report-text based [tests/test_multiple_testing_control_family.py:89](../../tests/test_multiple_testing_control_family.py#L89); that semantic distinction must not transfer to the code lane.

**Observed.** Static census of the nine opened pseudoreplication envelopes found 98 `project/analysis.py` files, no recognized multiple-correction call spelling, 20 files with at least two registered statistics calls, and no file with three calls to the same currently registered two-sample API. Representative mixed/sibling shapes include two row/unit-level tests in envelope 1 [evaluation/development/blind-envelope-2026-08-21/cases/11af5bb3f9b7e8e0b293/project/analysis.py:101](../../evaluation/development/blind-envelope-2026-08-21/cases/11af5bb3f9b7e8e0b293/project/analysis.py#L101), multiple heterogeneous tests in envelope 3 [evaluation/development/blind-envelope-3-2026-08-22/cases/5b80f0787b1b6c47048b/project/analysis.py:108](../../evaluation/development/blind-envelope-3-2026-08-22/cases/5b80f0787b1b6c47048b/project/analysis.py#L108), and raw plus aggregate tests in envelope 8 [evaluation/development/blind-envelope-8-2026-08-23/cases/ef9e199c282b9038e4c3/project/analysis.py:182](../../evaluation/development/blind-envelope-8-2026-08-23/cases/ef9e199c282b9038e4c3/project/analysis.py#L182). They are useful negative/sibling-census fixtures, not planted multiple-testing positives.

**Observed.** Static census of the 108 dependence-growth authoring cases found no recognized correction API spelling. They and the remaining regression cases therefore remain full zero-Finding regression surfaces; they do not by themselves measure first-contact recall for this new class.

**Inferred.** There is no existing blind, contract-bound, code-lane multiple-testing benchmark. Re-labeling pseudoreplication envelopes would not create one: their prompts, contracts, and planted class were different.

**Needs verification.** The static counts above must be reproduced by a checked-in deterministic corpus-census test during the build. They were obtained without executing project-authored code.

### 6.2 Development corpus plan

**Proposed.** Before freezing an envelope, create answer-visible development fixtures covering:

- repeated calls, a loop, and a comprehension over three or more explicit outcome columns;
- no correction, complete correction through every allowlisted API, exact manual Bonferroni, strict-subset correction, and unresolved manual BH;
- conclusion-versus-p-value-only output;
- every contract/CSV/source bound and boundary;
- every abstention code in section 5.2;
- each family-C guard in section 3, including adversarial near misses; and
- every old MT/BH regression case, plus the 20 opened multi-test sibling shapes, as unchanged outcomes.

The 108 blind and 155 regression corpora must continue to emit zero new Findings. All 98 opened envelope scripts must remain non-candidates unless a new `1.2.0` multiple-testing contract is deliberately added to a copied development fixture; no historical case lock is rewritten to manufacture authority.

### 6.3 Envelope 10 recommendation

**Proposed recommendation: class-pure first envelope, 6 positives and 6 negatives.** Do not split six positives between pseudoreplication and multiple testing. Pseudoreplication has already qualified; a 3+3 mix would give this new detector only three first-contact trials, make one miss dominate the estimate, and entangle two independent per-class running tallies.

Envelope 10 should use a new briefing and independent isolated author/custodian chronology. Authors may be told only that each project has one root `analysis.py`, one CSV, and a frozen structured requirement. They are not shown the grammar, API allowlists, Finding wording, prior cases, or detector output. Prompt bytes, role map, closure, and case bytes freeze under the established digest protocol.

Positive roles should all implement the contract-declared same-API family but vary ordinary code shape: repeated calls, a loop, a comprehension, containers/helper returns, no correction, and strict-subset correction. Negative roles should cover, at minimum:

1. complete correction of the authorized family;
2. structural primary/secondary gatekeeping;
3. two disjoint corrected families;
4. correction applied in an upstream/second stage;
5. permutation maxT/minP family control; and
6. screen-then-confirm on disjoint data.

The initial class-specific bar should mirror the established running-tally policy:

- hard stop: `0/6` negative candidates in the envelope;
- first-envelope recall gate: at least `3/6` positive candidates;
- report first-contact recall exactly, with misses and first abstention codes;
- once 18 blind positives exist for this class, require at least 50% candidates over the latest 18;
- hard stop on any false accusation in the latest 36 class-specific blind cases and report lifetime false accusations separately;
- zero Findings from the unqualified development lane;
- zero new Findings across the 108 blind and 155 regression corpora;
- replay equality for all 12 cases; and
- record the number and shapes of family-C analogue negatives in every envelope.

Pseudoreplication metrics remain a separate historical series. A future mixed envelope is appropriate only after multiple testing has its own qualified baseline and each class receives enough independently scored positives and family-C negatives to preserve separate tallies.

## 7. Review decisions that change the build

1. Accept or revise the proposed `1.2.0` contract fields, especially the explicit ordered outcome-column family.
2. Decide whether slice 1 supports both `ttest_ind` and `mannwhitneyu` or begins with `ttest_ind` only.
3. Accept or narrow the correction API/manual-Bonferroni registry.
4. Accept the structural definition of a p-derived conclusion; printing numeric p-values alone will not qualify.
5. Accept the conservative abstentions for gatekeeping, partitioned families, upstream adjustment, permutation control, and screen-confirm pipelines.
6. Accept the separate development check/detector identity and wording profile v1.
7. Accept a class-pure 6-positive/6-negative envelope 10 and the proposed class-specific running-tally bar.
