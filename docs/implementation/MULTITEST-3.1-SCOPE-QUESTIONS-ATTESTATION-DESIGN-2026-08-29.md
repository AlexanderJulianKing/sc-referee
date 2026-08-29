# Multiple-testing 3.1 correction-scope questions and asymmetric attestation design — 2026-08-29

**Status:** proposed build-ready design, Revision 0  
**Target:** detector/check/adapter `3.1.0`, development lane only  
**Predecessor:** multiple-testing record-model slice `3.0.0`  
**Authority:** accepted schema package `0.21.0`, `MASTER_SPEC.md`, the frozen scientific-requirement contract profile `1.2.0`, and the existing 3.0 structural detector  
**Scope:** deterministic MaterialQuestion emission for positively located but scope-unresolved corrections, digest-bound author attestations, and asymmetric answer handling  
**Implementation in this session:** none

## 0. Evidence basis and observed/inferred boundary

This design preserves the evidence-compiler boundary in `AGENTS.md`: a `Finding` means a
demonstrated issue, while unresolved meaning remains a `MaterialQuestion`, a linked
`ConditionalConcern`, or a non-accusatory `Disclosure`. The governing public requirements are:

- `SA-FR-024`: scientist answers are persisted with respondent, source, authority scope,
  timestamp when available, and qualitative certainty;
- `SA-FR-066`: `Finding`, `ConditionalConcern`, `MaterialQuestion`, and `Disclosure` remain
  distinct, and only `Finding` denotes a demonstrated issue;
- `MASTER_SPEC.md` section 3.11: a MaterialQuestion is emitted only when plausible answers can
  change applicability or assessment type, and it records the exact unknown, why it matters,
  evidence searched, candidate answers including unknown, blocked detectors, priority, status,
  and linked concerns; and
- `MASTER_SPEC.md` section 5.5: a ConditionalConcern has potential impact rather than severity,
  and a Disclosure alleges no scientific defect.

The evidence inspected for this design is:

1. repository state `211d9c068f8eb1a802228a508245fdc32ccea046` on
   `dev/dependence-growth`, including the installed 3.0 multiple-testing modules and their closed
   61-reason adapter registry;
2. every sealed-then-opened envelope-10 through envelope-15 `AUDIT_RESULTS.json` and source tree;
3. all 50 open-corpus cases and the frozen `adapter_replay_records_v2_1.json` comparison rows;
4. the record-model design, prototype sweep, final 3.0 oracle tests, and audit-fix fixtures;
5. accepted public schemas `material-question`, `answer`, `conditional-concern`, and `disclosure`
   at schema version `0.21.0`; and
6. the existing noninteractive CLI and the authoritative agent boundary in
   `docs/AGENTIC_SKILL.md`.

The following are **observed**:

1. E15 first-contact recall is `2/6`, with P3 and P6 stopping at
   `unresolved-manual-correction-present`, P5 at `record-family-mutation-unresolved`, and P4 at
   `test-battery-cardinality-unresolved`.
2. E15 P5 contains a recognized Holm call over only two of seven declared outcomes and later
   stores adjusted values into those two records; E15 P6 multiplies only selected p-values by the
   full family size. Those are positive correction-scope witnesses whose complete-family coverage
   the current detector does not prove.
3. E15 P3 does **not** contain correction arithmetic. Its reason is caused by a summary
   `len(results)` consumer while all verdicts use raw p-values at `0.05`. A reason string alone is
   therefore not evidence that a section-4 correction witness was located.
4. Across the 90 opened envelope cases, exactly 14 have both a qualifying first abstention reason
   and the closed witness required by section 4. Across the 50 open-corpus cases, exactly 10 do.
5. The 3.0 adapter classifications for all 140 cases are already pinned. Version 3.1 does not
   change any no-attestation detector classification, corrected-position set, Finding, or
   covered/complete result.

The following are **design decisions**, not observations:

1. a qualifying reason is necessary but never sufficient for a question;
2. an author answer that correction is incomplete is recorded as a public `Answer` plus a linked
   `ConditionalConcern`, not as a Finding and not as a fifth public assessment type;
3. an author answer that correction is complete is self-serving and is never classification
   evidence; it is only a pointer for the unchanged structural proof; and
4. a failed answer-guided proof yields a Disclosure and leaves the MaterialQuestion open.

Any build evidence that changes the 14/10 question census, exposes a correction witness outside
the closed grammar, or requires a new correction-recognition admission invokes section 17.

## 1. Decision and load-bearing asymmetric rule

Version 3.1 adds a question layer **after** the frozen 3.0 adapter has selected its exact first
abstention reason. It does not change the 3.0 correction, record, p-value, threshold, census,
hierarchy, row-completeness, or Finding grammar.

The load-bearing safety invariant is asymmetric:

```text
located correction-scope uncertainty
  -> ask a closed MaterialQuestion

Answer A: "does not cover all N"
  -> preserve the human Answer
  -> emit an explicitly author-attested ConditionalConcern
  -> never emit a tool Finding

Answer B: "covers all N"
  -> treat claimed location/factor only as a search pointer
  -> rerun unchanged 3.0 structural checks at that pointer
  -> covered/complete only if those checks independently prove all N positions
  -> otherwise emit a non-accusatory Disclosure and keep the question open

unknown/no answer
  -> keep the question open
```

This asymmetry prevents both symmetric hazards:

- **false accusation:** the tool must not turn an admission against interest into a demonstrated
  Finding that the code itself did not prove; and
- **false clearance:** a self-serving completeness claim must not clear a partial correction that
  the structural analyzer cannot verify.

Both hazards have a zero-tolerance gate. Neither answer changes the source-derived detector result.
An A answer may create an author-attested concern; a B answer may guide an existing proof. No
attestation may create a candidate, a Finding, a new corrected position, or a
`no_issue_detected_within_coverage` result by assertion alone.

## 2. Identities, schema boundary, frozen surfaces, and ADR

### 2.1 Versioned development identities

The versioned identities are:

```text
check_id          check:authorized-complete-family-correction-over-code-test-battery
check_version     3.1.0
detector_id       detector:bounded-code-csv-multiple-testing-conflict
detector_version  3.1.0
adapter_id        adapter:authorized-complete-family-correction-over-code-test-battery:code-csv-v1
adapter_version   3.1.0
grammar_id        bounded-code-csv-multiple-testing-conflict-v1
grammar_version   3.1.0
```

The development binding advances to 3.1.0. Versions 1.0 through 3.0 remain registered for replay.
No 3.1 identity resolves on a qualified lane. The qualified pseudoreplication lane, GrantPins,
grants, qualification records, metric sets, threshold policies, and all prior wording objects stay
byte-untouched.

### 2.2 Contract and detector-result boundary

Contract profile `1.2.0`, evidence profile `code_csv_multiple_testing_evidence_v2`, and Finding
wording profile v2 are unchanged. The source analyzer still returns exactly one of its current
candidate, covered/complete, or 61 closed abstention outcomes.

For a section-3/4 match, the 3.1 adapter additionally emits a specialized source-derived
`DetectorResult` with `state=material_question_candidate`. It contains only the question
profile ID, qualifying reason, canonical `CorrectionScopeWitness`, `N`, source references, and
digests. It is not a detector candidate for Finding admission, never enters the Finding adapter,
and is excluded from detector precision/recall catches. The controller converts it into a
`MaterialQuestion` and linked open `ConditionalConcern` under section 5.

The derived DetectorResult has `candidate.assessment_type=material_question`, the closed title
`Correction scope requires clarification`, and the closed bounded statement `Static analysis
located correction-related computation but did not establish complete-family coverage.` Its one
unresolved premise ID is derived from the question-evidence digest. Applicability and coverage are
`uncertain`/`unknown`; detector maturity remains `experimental`. It has a result ID distinct from
the preserved source-result ID, so one never overwrites or masquerades as the other.

The IDs are exact:

```text
question-result ID = detector-result:multiple-testing-correction-scope:<24hex>
unresolved premise ID = premise:multiple-testing-correction-scope:<24hex>
```

The suffixes are separate domain-separated semantic digests of the section-5.1 question identity
object. The result targets the analysis artifact and authorized-family contract; its evidence has
the section-4 source ref. No target or evidence ref is inferred from prose.

The 61 abstention strings remain byte-equal and closed. Version 3.1 adds no abstention reason.

### 2.3 Existing public record types

No new public assessment type is introduced.

- `MaterialQuestion` stores the unresolved complete-family scope.
- `Answer` stores the human response with `response_source=provided_answer_file`, human respondent,
  reported-intent authority scope, explicit certainty, and the existing answer digest profile.
- `ConditionalConcern` stores the possible or author-attested consequence without severity. Its
  `detector_result_ids` contains the source-derived question result and its `material_question_id`
  links the question.
- `Disclosure` stores an unverified completeness attestation with `non_accusatory=true`.
- `Finding` is never created by the question or attestation path.

The A path uses Answer plus ConditionalConcern because the accepted schema already separates the
human statement from the tool's unresolved assessment. A proposed `attested_misstep` fifth type
would violate the four-type public vocabulary and is rejected. Because
`ConditionalConcern.condition.premise_state` admits only `unknown` or `conflicted`, the concern's
premise is precisely “the author attestation accurately describes the audited source state,” which
remains unverified by the tool. The Answer itself records that the author confirmed incomplete
scope; the concern never claims that the tool established it.

### 2.4 Frozen 3.0 anchor

The build must pin these installed bytes before copying them:

```text
code_csv_multiple_testing_dataflow_v3.py
  sha256:498bf5c22305270fe64ed1ef73b7ac8a7a2637ce4f64520e8d9ca4ac15166618
code_csv_multiple_testing_record_model_v3.py
  sha256:f9f96c6e4bf861d9c186cb19685c74723d5fc6f9da4fcd1eaaada14d39230534
code_csv_multiple_testing_adapter_v3.py
  sha256:cddc845c2f404938ab86b8d87a79b4eb763090dfdfbb33854038998520728f53
integration_multiple_testing_v3.py
  sha256:1a340ab3b124994c88dbf7c08e21be11a8c2795198afc49a182ff8abcc74ac47
bounded_code_csv_multiple_testing_conflict_v3.py
  sha256:3284e70646d48039f42d2bcf6790c92910de43785f3d03701e5b6cf1ac1eb437
3.0 record-model design Revision 1b
  sha256:e950b6015198c92e7f7f16d30f901be9f131c0145e96524a22df4e33ed6ec166
3.0 prototype-sweep RESULTS.json
  sha256:762d6e7a5ee563c1f36bfecd1d3a8e9ac97ca943defd7a80f823ca3b5824e18b
E15 AUDIT_RESULTS.json
  sha256:ad0b30b8ebdf6d4a799628b5a6eb37ac7742d93f441ec604a0d6b81a34db142e
tests/test_multiple_testing_opened_envelopes_v3.py
  sha256:4901d301b3601b1fa7e3cb210cbb11dbe2404c27f885f1cb54f7da48931062a1
tests/test_multiple_testing_open_corpus_v3.py
  sha256:ce9d14ea55c8746c3f40813f71690d91c5826b86a9f224b8b4ff3d784310a7bf
tests/test_code_csv_multiple_testing_record_model_v3.py
  sha256:8bf778b83ec5030940e9406f524e94b9c54a0c23c646ddda76f3786b7fc08a8f
evaluation/development/multitest-code-slice-v3_0/audit-fix-r1-oracle/EXPECTED_ROWS.json
  sha256:d3376525fa208c01b03efb7832d56ee2aa5ac939c299ceeeef35ed894ff6abb7
evaluation/development/multitest-code-slice-v3_0/audit-fix-r2-oracle/EXPECTED_ROWS.json
  sha256:c189f2bb59bb8e84a59016dbaca1fd8315963551053523743eb56060c8a4f111
evaluation/development/multitest-code-slice-v3_0/audit-fix-r3-oracle/EXPECTED_ROWS.json
  sha256:99a1a3d39f4956fbd95dc710ff3aa03496920ddf32e94c32ef5f5d2ec4365d2a
```

The older frozen records remain pinned, including:

```text
adapter_replay_records_v2_1.json
  sha256:7c37669c8ccfdb0b754aa03ee1dbcee1dac78fa4bb44105e17c5d1886aaed502
E12 adapter_replay_records_v2_2.json
  sha256:f8b7808b3baee264e9c496e2e899686af235e72c37b9647ce4255d10adbb02d8
E13 adapter_replay_records_v2_3.json
  sha256:d171c40e0715ff2b0f4c65bb667e817b78575ea1f2d73a8bc9af0869d3143489
```

Version 3.1 uses new `_v3_1` copies. The 3.0 and older MT modules are not edited. A two-registry
differential must prove that no qualified GrantPin, grant, qualification record, metric-set record,
threshold-policy reference, or Finding byte derives from a development-inclusive digest.

### 2.5 Required policy record

Before build, add ADR-0080 (or the next available accepted ADR number) recording:

1. the five qualifying reason names plus the independent witness requirement;
2. the exact witness grammar and the reason-first ordering;
3. the question wording profile and non-prose evidence boundary;
4. Answer A as Answer plus author-attested ConditionalConcern, never Finding;
5. Answer B as an untrusted pointer followed by unchanged structural proof;
6. the false-accusation and false-clearance zero standards;
7. digest-bound, noninteractive attestation input and deterministic replay;
8. the meaning of an open question alongside an unchanged abstention; and
9. scoring isolation.

This changes public audit records and answer authority handling. It cannot be hidden in the
adapter. The accepted public schemas need no field change: versioned `x-` extensions carry the
narrow additional receipts described below.

The ADR records Alex's 2026-08-29 maintainer approval of the asymmetric policy. That approval
authorizes development implementation; it is not scientific evidence, a qualification grant, or
permission to promote any question/answer path to Finding status.

## 3. Closed qualifying-reason decision

### 3.1 The complete 61-reason universe

Version 3.1 copies this 3.0 closed set byte-for-byte:

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
family-test-api-dispatch-unresolved
multiple-registered-tests-for-family-member
test-operand-lineage-unresolved
selected-group-row-completeness-unproven
upstream-correction-lineage-unresolved
pvalue-family-collection-unresolved
record-family-lineage-unresolved
record-family-mutation-unresolved
record-decision-polarity-unresolved
record-duplicate-conclusion-ambiguous
record-subset-position-unresolved
dataframe-pvalue-table-unresolved
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

The build asserts length 61 and exact set equality independently in detector, adapter, question
classifier, fixture emissions, and registry resources.

### 3.2 Exactly five reason names are eligible

The qualifying reason-name set is exactly:

```text
correction-family-lineage-unresolved
record-family-lineage-unresolved
record-family-mutation-unresolved
unresolved-decision-threshold
unresolved-manual-correction-present
```

Eligibility is the conjunction:

```text
first_abstention_reason in QUALIFYING_REASON_NAMES
AND one canonical CorrectionScopeWitness from section 4
AND witness is causally tied to the same family p-value/decision slice that produced the reason
AND exact N and an exact source span are available
```

If any conjunct is unresolved, no question is emitted and the original abstention remains the sole
detector assessment. The implementation may not infer a witness from the English meaning of a
reason name.

| Reason | Why the name is eligible | Additional witness required |
|---|---|---|
| `correction-family-lineage-unresolved` | A recognized or census-matched correction terminal is present, but complete ordered coverage is unresolved. | A recognized-correction-call or closed-terminal-correction-call witness consuming family-derived p-values. |
| `record-family-lineage-unresolved` | A record field can hide corrected/raw p lineage. | A correction-origin expression causally feeding the unresolved cross-field/record edge. Generic field transport does not qualify. |
| `record-family-mutation-unresolved` | A post-construction store may implement partial adjustment. | A correction-origin expression causally feeding the mutation, or a recognized correction result stored into only resolvable positions. Generic mutation does not qualify. |
| `unresolved-decision-threshold` | Hand correction may be encoded in a threshold. | The exact manual threshold grammar in section 4.5; a bare or merely computed unknown threshold does not qualify. |
| `unresolved-manual-correction-present` | The analyzer has refused a correction-shaped p transform or correction terminal. | The exact manual adjusted-p grammar, exact terminal-call grammar, or exact record correction store. Summary `len`, casts, formatting, and unrelated arithmetic do not qualify. |

### 3.3 The other 56 reason names are excluded

The exclusion is closed, not a default semantic guess:

- the first 40 reasons through `pvalue-family-collection-unresolved` concern authority, source,
  helper, reader, census, operand, row, upstream, or generic collection boundaries rather than a
  positively located local correction scope;
- `record-decision-polarity-unresolved`, `record-duplicate-conclusion-ambiguous`,
  `record-subset-position-unresolved`, and `dataframe-pvalue-table-unresolved` locate record/table
  uncertainty but not necessarily correction arithmetic;
- `unresolved-pvalue-consumer` is an opaque-flow fact, not positive correction evidence;
- `family-pvalue-extremum-reduction-present` concerns selective reporting;
- `pvalue-scalar-cast-or-rounding-unsupported` concerns scalar presentation transforms;
- all hierarchy, control-dependence, partition, resampling, permutation, inference-sibling,
  conclusion-completeness, sink, and inspection-exception reasons concern different unknowns.

In particular, `upstream-correction-lineage-unresolved` is excluded: imported or file-loaded
adjusted values have no local correction span to ask about, and the question's claim location could
not be bound to the audited source.

The classifier contains an explicit map for all 61 names to either one of the five eligible reason
classes or `not_correction_scope_question`. Adding a future reason is a build failure until that map
and this design are reviewed.

## 4. Closed CorrectionScopeWitness grammar

### 4.1 Common proof object and source boundary

Every emitted question has one immutable `CorrectionScopeWitness`:

```text
witness_kind
qualifying_reason
analysis_path = "analysis.py"
analysis_content_digest
source_span = (start_line, start_column, end_line, end_column)
source_span_digest
authorized_count = N
family_position_origins = sorted unique known positions, possibly empty
correction_input_positions = sorted unique known positions, possibly empty
threshold_operator = one of <, <=, >, >=, or null
factor_kind and factor_value, or null
callee_identity, or null
association_digest
```

`source_span_digest` hashes the UTF-8 bytes selected by the AST/token span, not a normalized or
quoted source string. `association_digest` hashes the canonical provenance edges from family
`.pvalue`/adjusted-result/decision nodes to the witness. Source bytes, identifier spellings, string
contents, comments, docstrings, format text, and report prose are never copied into wording.

Public lines and columns are one-based; the end coordinate is exclusive. CPython's zero-based byte
column offsets are converted only after strict UTF-8 token mapping. A public `SourceRef` omits
`quoted_text` and records path, digest, and these coordinates.

The exact source span and position facts may appear as structured evidence. The detector never
matches phrases such as “Bonferroni,” “adjusted,” “primary,” or “complete” outside the closed
callee-terminal and AST slots below.

One reason and one span may yield at most one canonical witness. Unresolved source mapping,
ambiguous provenance, unknown N, or a witness outside `analysis.py` means no question.

### 4.2 Recognized correction call witness

`registered-correction-call` admits exactly a call whose resolved callee is one of:

```text
statsmodels.stats.multitest.multipletests
statsmodels.stats.multitest.fdrcorrection
scipy.stats.false_discovery_control
sc_referee.calculation_checks.bh.benjamini_hochberg
```

The existing 3.0 alias resolver must prove the identity. The accepted correction input argument,
including the default `method=` behavior for `multipletests`, is resolved by the unchanged 3.0
correction grammar. At least one input element must be proved family-p-derived. The witness records
every input `POS` that existing logic proves and leaves coverage unresolved when the set is not
exactly all `0..N-1`.

Unsupported return projections, unresolved input containers, an alias rebind, or an unresolved
call association do not expand this witness grammar. They may still produce the underlying
abstention, but no question unless section 4.3 or 4.4 independently matches.

### 4.3 Closed terminal correction-call witness

`closed-terminal-correction-call` uses the existing module-independent callee-terminal census and
only its callee attribute/name terminal slot. The lowercase terminal must be exactly one of:

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
```

or start with the exact prefix `benjamini`.

At least one positional or keyword argument must be proved family-p-derived through the unchanged
slice. A mere terminal name elsewhere, a non-callee identifier, an import with no call, a prose
string, or a call with no family p-derived argument cannot witness a question. This preserves the
global abstention census while narrowing question emission to associated evidence.

### 4.4 Manual adjusted-p arithmetic witness

`manual-adjusted-p-arithmetic` admits only these expressions, modulo parentheses and operand-order
symmetry where shown:

```text
P * K
K * P
min(P * K, ONE)
min(K * P, ONE)
min(ONE, P * K)
min(ONE, K * P)
numpy.minimum(P * K, ONE)
numpy.minimum(K * P, ONE)
numpy.minimum(ONE, P * K)
numpy.minimum(ONE, K * P)
```

where:

- `P` is an exact family `.pvalue`, recognized correction-result p member, or 3.0 record/DataFrame
  p field with a uniquely proved nonempty position set;
- `ONE` is a bare numeric literal whose source-text Decimal value is exactly 1;
- `min` is the unshadowed builtin and `numpy.minimum` is the resolved NumPy identity; and
- `K` is exactly one of: a positive integer literal, a single-binding immutable Name resolving to
  such a literal, `len(OUTCOME_TABLE)`, or `len(STATIC_SUBSET)` where the existing 3.0
  normalizer maps every member order-preservingly to distinct contract outcome positions.

The Decimal is constructed from literal **source text**, or `Decimal(repr(value))` only when source
text is unavailable; `Decimal(float)` is forbidden.

No other BinOp or Call matches. In particular `P / K`, `P + K`, `P ** K`, nested arithmetic in K,
`len(results)`, runtime-filter lengths, unknown calls, `max`, `clip`, `where`, or a factor carrying
both corrected and raw origins do not create a question. Their normal abstention remains.

For a capped form, the outer `min`/`numpy.minimum` call is the one witness span; its inner multiply
is provenance, not a second occurrence. For an uncapped form, the multiply is the witness span.

### 4.5 Manual decision-threshold arithmetic witness

`manual-decision-threshold-arithmetic` admits only a family p-derived comparison using one of
`<`, `<=`, `>`, or `>=`, including reversed operand order, where the other operand resolves exactly
to either:

```text
A / K
1 - (1 - A) ** (1 / K)
```

Parentheses may be elided only as Python AST precedence permits. Each intermediate may be a Name
only when the A5 syntax-wide binding invariant holds: the Name has exactly one binding event
anywhere in the parsed module and that one simple binding resolves to the corresponding closed
literal or subexpression above. A second binding, conditional alternative, unresolved RHS,
`global`, `nonlocal`, or `Del` disqualifies it.

The census counts every recursive `Store` target in assignment, annotation, augmentation,
`NamedExpr`, loop, comprehension, and `with ... as`; every function/lambda parameter; every import
alias binding; function and class names; exception-handler names; and match captures. Bindings in
literal-false branches, uncalled helpers, handlers, match cases, and nested scopes still count. It
never ignores a binding because its RHS is a BinOp. Ordinary immutable loads of a proved scalar in
formatting or output do not create a second binding and do not erase the correction witness.

Unchanged X4 expansion runs before this test. A helper parameter is not accepted by name: it must
be substituted from one resolved call site, and the substituted argument and every remaining Name
must satisfy the same syntax-wide single-binding rule. This is the route used by the pinned Sidak
helper cases in E10–E13.

`A` is a bare numeric literal with source-text Decimal value in `{0.01, 0.05, 0.1}`. `K` has the
same closed forms as section 4.4. Literal `1` is exact by source-text Decimal. Arithmetic in A or K,
unresolved helper calls, `math.pow`, `numpy.power`, or any algebraically equivalent but differently
shaped expression does not match.

One position-resolved selection is admitted for witness association only. Its AST is exactly an
`IfExp` whose test is `HEADER in STATIC_SUBSET` or `HEADER not in STATIC_SUBSET`, and whose body and
orelse are exactly one `CORRECTED_THRESHOLD` and one `A`, in either order.
`CORRECTED_THRESHOLD` must resolve to one exact expression above; `A` is the same family alpha;
`HEADER` is the existing per-position contract header; and `STATIC_SUBSET` is the existing closed,
immutable, distinct contract-header subset. The 3.0 position mapper must prove each branch and at
least one position in each branch. No runtime predicate, row mask, arbitrary membership container,
chained conditional, or unresolved header is accepted. This is the exact route for corpus
`spec-47`; it records only the corrected-branch position association and still leaves the source
result unresolved.

This is witness recognition only. It does not admit the threshold into the detector's conclusion
grammar, does not recognize hand correction as covered, and does not change the order-14/order-15
partition. The existing `unresolved-decision-threshold` remains the source result.

The descriptor span is the outermost comparison-associated expression that completes the grammar:
the final threshold binding RHS, or the expanded helper's return expression. Split intermediate
bindings such as `KEEP_PROBABILITY`, `EXPONENT`, and `PER_TEST_KEEP` are provenance nodes, not
additional correction occurrences.

### 4.6 Record correction-store witness

`record-correction-store` is a composite witness, not a generic mutation matcher. It requires:

1. a section-4.2, 4.3, or 4.4 correction origin;
2. the unchanged 3.0 record graph to map a source p position and destination record position;
3. the correction origin to flow causally into the exact store or cross-field edge that triggers
   `record-family-lineage-unresolved` or `record-family-mutation-unresolved`; and
4. no unresolved merge between corrected and raw origins before that store.

A plain `result.update(...)`, a duplicate store with no correction expression, a flag mutation,
an alias escape, or an arbitrary cross-field assignment is not a correction-scope witness. The
record reason remains, but no question is emitted.

### 4.7 Association, dominance, cardinality, and refusal

Question association is computed after the unchanged 3.0 first reason:

1. build the bounded backward slice from the reason's guarded AST node;
2. require a section-4 witness on that slice;
3. build the bounded forward slice from the family p origin to the witness;
4. require both slices to agree on at least one exact position or one exact correction container;
5. require the witness span to be inside the snapshotted `analysis.py`; and
6. require exact contract N.

`UNRESOLVED` is absorbing. The question classifier may not cross a helper, call, store, merge,
alias, record, or container edge that the existing analyzer could not resolve.

If multiple descriptors denote the same correction occurrence, canonical dominance is:

```text
record-correction-store
manual-adjusted-p-arithmetic
registered-correction-call
closed-terminal-correction-call
manual-decision-threshold-arithmetic
```

Loop/helper clones with the same source span, witness kind, and structural digest coalesce before
`association_digest` is computed; their uniquely resolved position associations are unioned in
contract order. Competing origins or an unresolved clone refuse the group. After dominance and
coalescing, **exactly one** distinct witness must remain for the project. Zero or two-or-more
distinct correction occurrences, overlapping nonidentical witnesses, competing family
associations, or unknown cardinality emits no question for that abstention. The classifier never
asks separate singular-scope questions about a potentially collective correction scheme.

## 5. MaterialQuestion, linked concern, and closed wording

### 5.1 Stable question identity

The question identity is:

```text
material-question:multiple-testing-correction-scope:<first-24-hex-of-semantic-digest>
```

The semantic digest input is the canonical object:

```text
profile = material-question:multiple-testing-correction-scope-v1
profile_version = 1.0.0
question_profile_semantic_digest
check_id and check_version
detector_id and detector_version
adapter_id and adapter_version
grammar_id and grammar_version
source_snapshot_digest
analysis_content_digest
authority_binding_digest
qualifying_reason
authorized_count
witness_kind
source_span
source_span_digest
association_digest
```

It excludes audit-run identity, filesystem absolute path, timestamp, source text, question text,
and attestation content. The same source snapshot, authority, detector bytes, reason, and witness
therefore produce the same question ID across replay. Distinct witnesses produce distinct IDs.

`question_evidence_digest` is the semantic digest of the complete canonical witness, the five
versioned identities, and the question wording-profile semantic digest. It is stored in the
question extension and required by every attestation.

### 5.2 Closed wording profile

Create the development-only wording object:

```text
material-question:multiple-testing-correction-scope-v1
profile_version = 1.0.0
```

Its `semantic_digest` is computed from canonical profile bytes excluding the digest field and is
pinned in the development registry, question-evidence digest, replay record, and wording golden
from day one. It is independent of every historical Finding wording profile.

The exact visible template is:

```text
Question:
Does this correction cover all {AUTHORIZED_COUNT} declared outcomes?

Why it matters:
Static analysis located correction-related computation at {SOURCE_LOCATION}, but could not prove
whether it covers all {AUTHORIZED_COUNT} outcomes in the declared family. The answer can change
how this unresolved case is recorded; it cannot create a tool Finding by itself.
```

`SOURCE_LOCATION` is rendered only as `analysis.py:<START_LINE>:<START_COLUMN>` from the structured
span. `AUTHORIZED_COUNT` is the contract integer N. Those are the only slots. No method name,
variable name, source token, source excerpt, comment, docstring, report prose, answer prose, case
label, or abstention reason enters visible wording.

The candidate answers are exactly, in this order:

| option ID | label | canonical value | closed consequence |
|---|---|---|---|
| `correction-scope-incomplete` | `No — it does not cover all declared outcomes` | `{"coverage":"incomplete"}` | `Records an author attestation of incomplete scope as a non-Finding conditional concern.` |
| `correction-scope-complete` | `Yes — it covers all declared outcomes` | `{"coverage":"complete"}` | `Guides a structural recheck; the claim alone cannot establish complete coverage.` |
| `correction-scope-unknown` | `Unknown` | `{"coverage":"unknown"}` | `Leaves the question open.` |

The MaterialQuestion fields are fixed as follows:

- `unknown_semantic_dimension = multiple_testing_correction_scope`;
- `priority = high` because either substantive answer changes the assessment record, but never
  because the tool inferred severity;
- `status = open` absent a validated A answer; B remains open until structural proof succeeds;
- `evidence_searched` contains only closed descriptions of the structural witness and unresolved
  coverage, plus source path/span facts;
- `blocked_detector_ids` contains the 3.1 detector ID;
- `affected_claim_ids` contains only claims already linked by deterministic lineage, otherwise
  the empty list; and
- `linked_conditional_concern_ids` contains exactly the concern in section 5.3.

Required versioned extensions are:

```text
x-question-purpose = multiple_testing_correction_scope
x-question-profile-id
x-question-profile-version
x-check-id
x-check-version
x-detector-id
x-detector-version
x-qualifying-reason
x-authorized-count
x-witness-kind
x-source-span
x-source-span-digest
x-analysis-content-digest
x-authority-binding-digest
x-question-evidence-digest
```

No extension contains quoted source or human free text. A prose tripwire in section 15 mutates all
uninspected text while asserting byte-equal questions.

### 5.3 Linked open ConditionalConcern

Question emission also creates exactly one linked `ConditionalConcern`, because answer A has a
specific consequence. Its closed wording is:

```text
Title:
If the located correction does not cover all {AUTHORIZED_COUNT} declared outcomes, the declared
family may be incompletely corrected.

Conditional statement:
If the correction at {SOURCE_LOCATION} does not cover all {AUTHORIZED_COUNT} declared outcomes,
some family conclusions may be based on incomplete multiple-testing control.
```

It has:

- `issue_class = x-multiple-testing-correction-scope`;
- `condition.premise_state = unknown` before a validated A answer;
- `potential_impact.level = material_if_true`, never a severity;
- `review_priority = high`;
- the question ID and source detector-result ID;
- subject refs only to deterministically linked analysis/contract records;
- no Finding ref and no qualification effect; and
- grouping key equal to a digest of question ID and source detector-result ID.

Its required closed fields also include:

```text
why_material = Complete-family coverage determines whether the declared multiple-testing
               requirement was satisfied.
next_evidence_needed =
  - Select one of the question's three bounded answers.
  - For a complete-scope answer, identify the correction span and closed factor for structural
    recheck.
```

`affected_descendants` and `evidence` contain only already resolved record/source refs; either may
be empty. `subject_refs` always contains the analysis artifact and authorized-family contract.
Question and concern share one logical root, render together, and are never double-counted in
assessment, prioritization, scoring, or coverage totals.

The initial concern is an explicit conditional, not an allegation. It is not counted as a Finding,
detector catch, or author-confirmed misstep. Section 7 defines the A-answer rendering.

### 5.4 Question emission order and no-attestation behavior

The ordered 3.1 pipeline is:

1. snapshot and bind contract exactly as 3.0;
2. run the untouched-tree 3.0 syntactic censuses and 3.0 value/record analysis;
3. freeze the exact source result and first reason;
4. if the reason is one of section 3.2, attempt the bounded section-4 witness proof;
5. emit zero or one canonical question candidate;
6. construct public questions and linked concerns;
7. if an explicit attestation file was supplied, validate it all-or-nothing under section 6;
8. apply A, B, or unknown under sections 7 and 8; and
9. canonicalize, hash, lock, and report all records.

Without attestations, every byte in the frozen 3.0 adapter row is reproduced by the 3.1 analysis
projection under the adapter-row profile: outcome, reason/classification, authorized count,
corrected positions, API-by-position evidence, and scientific evidence payload. A qualifying case
gains only the deterministic question candidate, MaterialQuestion, and linked concern; every
pre-existing source classification, classification reason, scientific evidence projection,
corrected-position set, Finding list, and Disclosure list is equal. A nonqualifying case has equal
assessment arrays as well as an equal source classification.

“Byte-equal” here refers to those canonical adapter rows and historical stored anchors, not to a
3.1 public record falsely labeled as version 3.0. Legitimate no-attestation churn is enumerated and
limited to: the active development registry section; 3.1 implementation/manifest/version/result
identity fields; their downstream development lock/replay bytes; and, on the 24 question rows,
the additive question-result/question/concern records. Historical records are not rewritten. No
GrantPin field, grant, qualification record, threshold policy, metric record, or Finding byte may
derive from that development-inclusive churn.

## 6. Explicit digest-bound attestation input

### 6.1 CLI boundary

The only new input route is explicit:

```text
sc-referee audit /absolute/project \
  --development-lane \
  --attestations /absolute/answers/multiple-testing-attestations.json \
  --output /absolute/audit-output
```

The CLI never prompts, reads an answer from stdin, searches the audited project for an answer,
infers an answer from report/code prose, or accepts environment-variable answers. The file is an
external human-authorized audit input. It is copied into the audit input area, content-addressed,
and included in the semantic lock.

The supplied path must be absolute and lexically normalized. The controller opens it without
following symlinks, verifies matching `lstat`/`fstat` identity and a regular-file mode, reads once
through that descriptor, and rejects a path whose resolved parent is inside the audited project.
This prevents a project-authored file or path race from impersonating human input.

For 3.1 the file must be a regular non-symlink UTF-8 JSON file outside the audited project tree,
at most 1 MiB, containing exactly one entry. YAML, JSONL, comments, duplicate JSON keys,
non-finite numbers, and Unicode decoding replacement are refused. Canonical JSON validation uses
the same duplicate-key and number rules as other public records.

The flag is available only with the development-lane 3.1 binding. A qualified run, historical MT
binding, absent MT contract, or no emitted correction-scope question refuses the file rather than
silently ignoring it.

### 6.2 Closed input schema

The top-level schema is the closed shape:

```text
profile = multiple_testing_correction_scope_attestations_v1
profile_version = 1.0.0
answers = array[1] of AttestationEntry
```

No additional top-level or entry fields are allowed. Each entry is:

```json
{
  "question_id": "material-question:multiple-testing-correction-scope:...",
  "source_snapshot_digest": "sha256:...",
  "analysis_content_digest": "sha256:...",
  "question_evidence_digest": "sha256:...",
  "authority_binding_digest": "sha256:...",
  "answer": "correction-scope-incomplete",
  "respondent": {
    "actor_kind": "human",
    "actor_id": "scientist:...",
    "display_name": "..."
  },
  "certainty": {
    "level": "explicit",
    "basis": "The named human supplied this answer for the bound question."
  },
  "timestamp_status": "available",
  "answered_at": "2026-08-29T00:00:00Z",
  "supersedes_answer_digest": null,
  "claimed_correction": null
}
```

The exact entry invariants are:

1. `answer` is one of `correction-scope-incomplete`, `correction-scope-complete`, or
   `correction-scope-unknown`.
2. The top-level `answers` array contains exactly one entry.
3. `respondent.actor_kind` is exactly `human`; actor ID is required and display name optional.
4. `certainty.level` is exactly `explicit`; `basis` is the closed string shown above. Free-form
   certainty rationales are refused.
5. `timestamp_status` is `available` or `unavailable`; `answered_at` is required exactly for
   `available` and forbidden for `unavailable`.
6. `supersedes_answer_digest` is exactly null in profile v1. Cross-audit answer supersession is
   deferred; the public Answer therefore has `supersedes_answer_refs=[]`. A nonnull value is refused
   rather than following an implicit prior-audit channel.
7. `claimed_correction` is required exactly for `correction-scope-complete` and must be null for A
   or unknown.
8. The entry's question ID equals the one emitted MT correction-scope question.

The `claimed_correction` object is exactly:

```json
{
  "path": "analysis.py",
  "analysis_content_digest": "sha256:...",
  "source_span": {
    "start_line": 1,
    "start_column": 1,
    "end_line": 1,
    "end_column": 2
  },
  "factor": {
    "kind": "contract_family_size",
    "value": 7,
    "source_span": {
      "start_line": 1,
      "start_column": 1,
      "end_line": 1,
      "end_column": 2
    }
  }
}
```

`path` is exactly `analysis.py`. The content digest must equal both the entry and snapshot file
digest. Both spans must be valid AST/token spans within those bytes; the factor span may equal the
correction span. The factor kind is exactly one of:

```text
literal_multiplier
resolved_constant_integer
contract_family_size
correction_input_count
threshold_divisor
```

`value` is a JSON integer in `1..N`. The object does not accept a method name, explanation,
free-text location, code excerpt, variable name, claimed position list, or claimed coverage set.
These fields are pointers only and cannot enlarge the structural grammar.

### 6.3 Digest binding and all-or-nothing validation

Before constructing any public Answer, the controller verifies, in order:

1. raw-file digest and canonical semantic digest;
2. profile/version and closed schema;
3. exact emitted question ID;
4. exact source snapshot digest;
5. exact `analysis.py` content digest;
6. exact question-evidence digest;
7. exact authority-binding digest;
8. exact option/value pairing;
9. null-only supersession conformance; and
10. for B, exact claimed span/factor syntax and bounds.

Validation is all-or-nothing. A stale digest, wrong question ID, duplicate answer, extra field,
bad order, malformed span, mismatched factor, or answer to a nonemitted question causes a
deterministic CLI preflight failure. No partial Answer is admitted and no audit bundle is
published. Exact error categories are:

```text
attestations-file-unavailable
attestations-file-path-unsafe
attestations-file-outside-size-bound
attestations-json-invalid
attestations-schema-invalid
attestations-question-not-open
attestations-answer-cardinality-invalid
attestations-snapshot-binding-mismatch
attestations-analysis-binding-mismatch
attestations-evidence-binding-mismatch
attestations-authority-binding-mismatch
attestations-supersession-invalid
attestations-claimed-correction-invalid
```

The error category, input digest when safely available, and failing JSON pointer are deterministic;
source or answer prose is not copied into errors.

The accepted file's raw digest, canonical semantic digest, entry digests, public Answer digests,
and question evidence digests enter the audit lock. Moving an identical file does not change
semantic output; changing one byte does. Reusing an answer after any source, contract, detector,
witness, or snapshot change fails before classification.

### 6.4 Public Answer projection

A validated A or B entry becomes an existing-schema `Answer` with:

```text
answer_kind = candidate_selection
selected_option_id = the exact option ID
answer_value = the exact option value from section 5.2
response_source = provided_answer_file
authority_scope.authority_kind = reported_intent
authority_scope.semantic_dimensions = ["multiple_testing_correction_scope"]
authority_scope.subject_refs = [the MaterialQuestion ref, the bound analysis artifact ref]
certainty.level = explicit
answer_digest_profile = canonical-json-excluding-answer-digest-v1
provenance.actor = the human respondent
provenance.method = scientist_answer
```

The Answer extensions bind the attestation profile/version, raw/semantic input digests,
question-evidence digest, analysis-content digest, authority-binding digest, and claimed-correction
digest when present. They contain no free text.

`answer_id` is `answer:multiple-testing-correction-scope:<24hex>`, where the suffix is the semantic
digest of question ID, selected option/value, respondent actor ID, timestamp fields,
claimed-correction digest, and all four scope bindings. Audit-run ID and output path are not
identity inputs. The authority kind is `reported_intent` because this is a bound author report about
the audited computation, not detector-observed computation and not authority to change the frozen
scientific contract.

An unknown entry uses `answer_kind=unknown`, selects `correction-scope-unknown`, records the same
bindings, and leaves the question open. Generic answer-entry commands and existing post-hoc
structured-answer routes refuse this question subtype; only the bound file path above may answer it.
Its only report sentence is the closed string `The author selected unknown; correction scope
remains unresolved.` It creates no new concern or Disclosure beyond the initial linked concern.

## 7. Answer A — admission against interest

### 7.1 Classification choice

For `correction-scope-incomplete`, the controller:

1. persists the human `Answer`;
2. marks the MaterialQuestion `answered` and links the Answer ID;
3. replaces the initial open concern with a canonical author-attested ConditionalConcern; and
4. preserves the original source abstention unchanged.

It emits no Finding, detector candidate, no-issue classification, severity, corrected-position
claim, or objective adjudication.

The report label is exactly:

```text
Author attestation — not a tool Finding
```

The closed title and first sentence are:

```text
Title:
Author attests that the located correction does not cover all {AUTHORIZED_COUNT} declared
outcomes.

Conditional statement:
If the bound author attestation accurately describes this source snapshot, the declared family has
incomplete multiple-testing correction.
```

The condition has `premise_state=unknown` and `if_true` equal to the closed conditional statement.
Its potential impact is `material_if_true`, with no severity. Extensions state
`x-basis=author_attestation`, `x-attestation-class=admission-against-interest`,
`x-author-attested-misstep=true`, the Answer digest, and all scope-binding digests. Provenance
uses `actor_kind=controller` and `method=author_attestation_projection`; the human provenance is
carried by the linked Answer. This records author-attestation provenance without pretending that
the human constructed the controller record or that the detector proved its premise.

For this A concern, `next_evidence_needed` is the one-item array `Inspect a corrected source
revision or independently prove the correction-position flow before admitting any tool Finding.`

### 7.2 Why A is not trusted as a Finding

An admission against interest is useful first-party evidence, but the tool has not demonstrated
the code-to-family consequence. The author may misunderstand N, answer the wrong conceptual
question despite digest binding, or describe intent rather than execution. Direct entailment and
finite counterevidence therefore remain incomplete. Only a later source edit or independently
proved detector result can create a Finding under ordinary admission rules.

A malicious or mistaken A can at worst create a visibly author-attributed ConditionalConcern. It
cannot create a Finding byte, evaluation catch, qualification result, severity, or publication
materiality assessment.

### 7.3 Conflict and resubmission

Profile v1 accepts exactly one entry per question and no supersession edge. Duplicate/conflicting
entries are refused before bundle construction. A later audit may carry a different explicit file,
but it creates a separate Answer in that audit; neither bundle rewrites the other, and no prior
Answer is auto-imported. Supporting cross-audit supersession requires its own explicit prior-bundle
input and is deferred.

## 8. Answer B — self-serving pointer and structural recheck

### 8.1 Pointer-only rule

For `correction-scope-complete`, the claimed source span and factor select an already parsed node.
They do not establish that the node is a correction, that its input has N p-values, that each
position is covered, or that conclusions consume its output.

The detector reruns **only** the installed 3.0 structural rules, scoped to the claimed node and its
already existing graph:

- registered correction identity and default method resolution;
- correction-input container reconstruction and position mapping;
- the current manual adjusted-p grammar;
- current record/DataFrame position mapping;
- current threshold grammar and product rules;
- current total forward-consumer accounting; and
- current complete-family coverage equality.

Every whole-module census and every off-pointer counterevidence scan still runs on the untouched
tree. Guidance prioritizes one proof root; it never narrows the module, family, consumer, hierarchy,
correction-terminal, registered-test, statistics-prefix, dynamic-execution, API-rebinding, repeated-
construct, mutation, export, or resampling search surface.

The guided pass may start graph traversal at the claimed span and compare the claimed integer to
already resolved literals or container counts. It may not add an API, terminal, arithmetic form,
factor form, container form, record edge, threshold, helper expansion, or p-value consumer that 3.0
does not already admit. It may not treat the author's claimed factor value as a resolved AST value.
The claimed node must join the same family graph and question witness under existing provenance;
there is no fallback search for a different correction when the claimed node fails.

### 8.2 B proves complete coverage

The B path resolves only when the unchanged checks independently prove:

```text
correction input positions == {0, ..., N-1}
AND every family conclusion uses the corresponding recognized corrected origin/reject result
AND no raw competing conclusion, unresolved consumer, mutation, export, hierarchy, extremum,
    resampling, or correction-shaped sibling remains
```

The source outcome becomes the **existing** `covered/complete` outcome with the same evidence and
wording it would have received without an answer had the proof start been known. The record adds an
`answer-guided` proof receipt containing the Answer digest, claimed span digest, and the unchanged
grammar/result digest. The receipt is provenance, not a scientific premise. Removing the Answer
and invoking the same existing proof at the now-known node in a controlled test must yield the same
corrected-position set.

The pre-attestation abstention digest is retained in the receipt, but it is not emitted as a second
active source assessment. The final attested adapter row is `covered/complete` only because the
rerun produced the independent structural proof. A, unknown, and B-fails retain the original row.

The MaterialQuestion becomes `answered`; no Disclosure or concern remains active. The Answer is
retained. This is not a global “verified correct” classification: it establishes only complete
correction coverage within the detector's existing bounds.

### 8.3 B fails to prove complete coverage

If any required edge remains unresolved or the structurally proved positions are not exactly all
N, the original abstention remains and the MaterialQuestion stays `open` even though its Answer ID
is recorded. Emit one existing-schema Disclosure:

```text
disclosure_kind = detector_gap
title = Author attests complete correction; structural coverage remains unverified
description = The author attests that the correction at {SOURCE_LOCATION} covers all
              {AUTHORIZED_COUNT} declared outcomes, but the bounded structural recheck did not
              prove complete coverage.
importance = important
non_accusatory = true
coverage_status = unknown
interpretive_consequence = Complete-family correction remains unverified; no Finding or clearance
                           follows from the attestation.
next_step = Make the claimed correction and every corrected conclusion structurally inspectable,
            or leave the question open.
```

The only slots are source location and N. `affected_refs` link the question, Answer, analysis
artifact, and detector result. The Disclosure extension records the closed recheck failure code,
all binding digests, and `x-author-attests-complete=true`; it stores no human prose.

The linked ConditionalConcern remains open with `premise_state=conflicted`: the author claims
complete scope while structural evidence cannot establish it. Its wording remains conditional and
has no severity.

The initial concern ID is derived from question ID plus `open`; an A concern ID is derived from
question ID plus Answer digest plus `author-attested`; a B-fails concern ID is derived from question
ID plus Answer/recheck digests plus `conflicted`. A Disclosure ID is derived from question ID,
Answer digest, and recheck digest. These identities prevent one state from overwriting another and
are independent of output path or record order.

### 8.4 Absolute prohibitions for B

A B answer, alone or combined with its claimed factor, can never produce:

- a Finding or Finding candidate;
- `none` or `strict_subset` accusation classification;
- an added corrected position;
- `no_issue_detected_within_coverage`;
- a verified-correct, safe, compliant, publication-ready, or global-pass statement;
- qualification or promotion credit; or
- suppression of an existing Finding from another check.

If the structural recheck cannot prove complete coverage, Disclosure plus open question is the only
permitted result. False clearance is tested at the same zero standard as false accusation.

## 9. Replay, locking, and ordering obligations

### 9.1 Deterministic record order

The single question candidate uses the canonical key:

```text
(analysis_path, start_line, start_column, end_line, end_column,
 witness_kind_rank, association_digest, question_id)
```

Answers sort by question ID; concerns and disclosures sort by their linked question ID. Ordering
never reads visible wording. Duplicate canonical IDs are a hard error. The exact-one-witness rule
is checked before public record construction.

### 9.2 Replay equality

For identical project snapshot, contract/authority inputs, registry bytes, clock fixture,
attestation raw bytes, and CLI options, these must be byte-identical across replay:

- detector source result;
- question candidate and witness;
- MaterialQuestion and linked concern;
- public Answer and answer digest;
- guided-recheck receipt or Disclosure;
- semantic lock and registry digest;
- report JSON, JSONL, and HTML; and
- all storage-manifest entries.

The existing `15/15` replay hard stop extends to attested runs: each of the 15 question/answer
fixture bundles in section 12 is run twice from clean output roots and compared byte-for-byte.
Replay without attestations likewise pins all 140 oracle rows and deterministic question records.

### 9.3 No temporal or answer drift

Question ID and evidence digest do not contain `created_at`. Timestamps are provided or explicitly
unavailable and remain part of the Answer digest. A supplied `answered_at` is data, not wall-clock
state. A new source snapshot, authority binding, witness, question profile, detector version, or
claimed span produces a different binding and rejects the old answer.

An answer file is never copied forward automatically to a later audit. The agent skill may present
an existing answer to the human as prior context, but re-use requires a newly supplied file with
all current digests and explicit human authorization.

## 10. No-attestation oracle over 90 opened and 50 corpus cases

### 10.1 Oracle semantics

The adapter-level 3.1 gate runs the real 3.1 adapter over all 140 projects with no attestation file.
For every row:

1. the frozen adapter-row projection defined in section 5.4 must be canonical-byte-equal to the
   frozen 3.0 row;
2. `candidate`, `covered/complete`, abstention reason, classification, corrected positions,
   registered APIs, and evidence bytes must be equal;
3. the question-ID set must be exactly the set pinned below; and
4. each question case must have exactly one MaterialQuestion and one linked open concern, while
   each other case has zero correction-scope questions and zero such concerns.

Thus the source movement count is `0/140`. The additive question-record census is exactly
`14/90` opened plus `10/50` corpus, or `24/140`. “Unchanged” below means exact frozen 3.0
adapter-row bytes and no new correction-scope question. A question row also keeps exact frozen 3.0
adapter-row bytes.

### 10.2 The 14 opened question rows

| Envelope | Role and case ID | N | Frozen first reason | Required witness |
|---|---|---:|---|---|
| E10 | N2 `9be74afbe9659bd50580` | 5 | `unresolved-decision-threshold` | Sidak expression at `analysis.py:44`, associated through its call and family comparisons |
| E10 | N3 `b787314c170f8f690060` | 4 | `unresolved-manual-correction-present` | `pingouin.multicomp` family-p call at lines 140–142 |
| E11 | N2 `d11a7136d1e91ed8e26f` | 4 | `unresolved-decision-threshold` | Sidak expression at line 44 |
| E11 | N3 `479317f1706d4fb929e5` | 4 | `unresolved-manual-correction-present` | imported `multicomp` family-p call at lines 110–113 |
| E12 | N2 `f256af2f5c5d98f37e65` | 4 | `unresolved-decision-threshold` | Sidak expression at line 54 |
| E12 | N3 `678e94e79226936fd647` | 5 | `unresolved-manual-correction-present` | `pingouin.multicomp` family-p call at lines 114–118 |
| E13 | P6 `d0f9fcd52f47e4d64668` | 5 | `unresolved-manual-correction-present` | `min(p_raw * N_CORRECTED, 1.0)` at line 95 |
| E13 | N1 `b7d38f6e9284abfd3ee6` | 5 | `correction-family-lineage-unresolved` | default-method `multipletests(raw_p_values)` at line 79 |
| E13 | N2 `f65170c644b90c4a893c` | 4 | `unresolved-decision-threshold` | Sidak expression at line 34 |
| E13 | N3 `c15f507ad59999fd9371` | 5 | `unresolved-manual-correction-present` | `pingouin.multicomp` family-p call at lines 95–98 |
| E14 | P6 `94786af7eca95fff6d78` | 8 | `unresolved-manual-correction-present` | `min(p_raw * n_comparisons, 1.0)` record store at line 100 |
| E15 | P5 `3d2f92807b8138de6463` | 7 | `record-family-mutation-unresolved` | Holm `multipletests(primary_p, ...)` at line 144 causally tied to stores at lines 145–146 |
| E15 | P6 `81980e878c1bc8cc216b` | 8 | `unresolved-manual-correction-present` | `min(p_raw * FAMILY_SIZE, 1.0)` at line 122 |
| E15 | N3 `907f9057eb9fc1d88e99` | 4 | `unresolved-manual-correction-present` | `pingouin.multicomp` family-p call at lines 131–133 |

Every row above gets one question with the exact N shown. The design does not infer whether the
correction is complete. Several N rows are known-correct analyses; asking the bounded question is
the intended safe behavior, not an accusation.

### 10.3 Exact opened complement — 76 rows without questions

The following role/case pairs enumerate every opened row not in section 10.2. Each is unchanged and
gets no correction-scope question:

| Envelope | Exact no-question rows |
|---|---|
| E10 | P1 `ebbb8a5dbc2664257144`; P2 `104493a5d99796a002c0`; P3 `3ff45fce2a45e0959fdb`; P4 `7296b0e2cf7faeefca64`; P5 `c51d08801b3d0ba4e532`; P6 `f4cf62caeb8ad68dc5b3`; N1 `cb2e207276a0dc3247bb`; N4 `60f96fabb7129d662b23`; N5 `8d83210468ecde012e4a`; N6 `4907932548f745afe942`; N7 `6d2fdc67ab98bc0e0e6e`; N8 `dfc9f20a94ecefc7f7b5`; N9 `e1bce32a32e3b2df475e` |
| E11 | P1 `8726b87ac4ba4c34c0a3`; P2 `6f08fe90c58e51737a4d`; P3 `69c5d0aec76eefb67148`; P4 `dfd35001c5a99ab1486b`; P5 `114782f595d9c24b923d`; P6 `0249919d05de1abc25fd`; N1 `d1533e4a8bbd10cb727e`; N4 `10e0cfb0c7ba8d03ec52`; N5 `2a712805024597719d32`; N6 `1cce7d6b580caa25f597`; N7 `9bccc428f23dde0d43f0`; N8 `53c4753f38f9e253d541`; N9 `08565c720304eb6fd9d3` |
| E12 | P1 `f9ce4de5e21d9015ecd9`; P2 `e07a6f2a895079b53b8c`; P3 `e28a9537b07c74d21838`; P4 `0ec89f70a9776d1a1931`; P5 `54667dd7c39067c8c2c8`; P6 `68d1a6f5b1ab70f2650a`; N1 `45c4b9a19d0a630f1cb0`; N4 `c37c0fa6e462a22cb6d5`; N5 `6108263527580cd01608`; N6 `db193771248850b81b25`; N7 `190ca375ac7c481c3e08`; N8 `7fd5f9dcd4097c1e5a03`; N9 `62aa3748aa0c7c2607d3` |
| E13 | P1 `686d1432762cd49d9b54`; P2 `c336be2521785ab6a954`; P3 `4f042d10b3f9a43d1099`; P4 `ffbe12246cf8a4227210`; P5 `80091f37c722eba28e18`; N4 `cfbb5edfd1534e7419fd`; N5 `8f37c5176ab3c0a61e4d`; N6 `6a102a97a065f9c8879f`; N7 `aba768f8d0b3f3548683`; N8 `325c686a92196956359a`; N9 `ab70cdb37bb2977d725c` |
| E14 | P1 `9ed744e25f1f1c55f8ca`; P2 `4fc0f5c1ef2d0e2cd5b6`; P3 `502687d9137dab93ff99`; P4 `cccde3c60f936e077f80`; P5 `5e33841b96d85ffe67be`; N1 `aabf005414b9ae164c0b`; N2 `c83b4021527fa98dadf3`; N3 `2327c03c4ddd02a36b97`; N4 `f80bac8b4bd7442917c5`; N5 `e987fc7ceafb6acb7a75`; N6 `1baacbeace56bb5d7b0f`; N7 `470aaf22deaf023aaae6`; N8 `c3191c18f72145cde01c`; N9 `5d5d4e0189d4f2c73f6a` |
| E15 | P1 `e90debfca9efcf70e758`; P2 `f616be91eaedbf23fad2`; P3 `afe47b2a7ea87ed21a69`; P4 `6e0ce2fc6d782f351d96`; N1 `f846b07b1d11131cec4d`; N2 `5fb661f1e846196aa832`; N4 `42f325bec89c5695ea51`; N5 `3583dc8b101822cf15b9`; N6 `d29aecb0a61ab4ebc486`; N7 `9d5848e6aaba7586e0f1`; N8 `0aa1af228c91fde5f909`; N9 `7992deeaaf441345c89e` |

Load-bearing exclusions in this complement are:

- E15 P3: `unresolved-manual-correction-present` but no section-4 witness; its `len(results)`
  summary is not correction arithmetic;
- E15 N9 and the earlier bare-literal threshold cases: the reason may be
  `unresolved-decision-threshold`, but a bare threshold is not the section-4.5 correction shape;
- E15 N2: its earlier `test-operand-lineage-unresolved` reason controls, so a deeper threshold is
  not question-eligible; and
- E14 N9 and all generic p/record/container walls: no positively located correction witness.

### 10.4 The 10 corpus question rows

The frozen corpus source classifications remain byte-identical. Exactly these ten cases gain one
question:

| Case | N | Frozen first reason | Required witness |
|---|---:|---|---|
| `spec-02` | 5 | `correction-family-lineage-unresolved` | default-method `multipletests` family call |
| `spec-04` | 6 | `correction-family-lineage-unresolved` | `multipletests(..., method="holm")` family call |
| `spec-06` | 5 | `unresolved-decision-threshold` | closed Sidak threshold arithmetic |
| `spec-24` | 6 | `correction-family-lineage-unresolved` | default-method `multipletests` family call |
| `spec-26` | 6 | `correction-family-lineage-unresolved` | `multipletests(..., method="fdr_bh")` family call |
| `spec-28` | 4 | `unresolved-decision-threshold` | closed Bonferroni `A/K` threshold arithmetic |
| `spec-29` | 6 | `unresolved-decision-threshold` | closed partial Bonferroni `A/K` threshold arithmetic |
| `spec-46` | 5 | `correction-family-lineage-unresolved` | default-method `multipletests` family call |
| `spec-47` | 6 | `unresolved-decision-threshold` | closed partial Bonferroni `A/K` threshold arithmetic |
| `spec-48` | 5 | `unresolved-decision-threshold` | closed Sidak threshold arithmetic through single-binding Names |

Exactly these 40 corpus cases get no question and remain otherwise byte-identical:

```text
spec-01 spec-03 spec-05 spec-07 spec-08 spec-09 spec-10 spec-11 spec-12 spec-13
spec-14 spec-15 spec-16 spec-17 spec-18 spec-19 spec-20 spec-21 spec-22 spec-23
spec-25 spec-27 spec-30 spec-31 spec-32 spec-33 spec-34 spec-35 spec-36 spec-37
spec-38 spec-39 spec-40 spec-41 spec-42 spec-43 spec-44 spec-45 spec-49 spec-50
```

Notably, `spec-20` and `spec-42` have non-witness threshold/manual shapes, and `spec-50` uses an
off-registry correction surface not matched by the closed callee-terminal rule. They remain
question-free.

### 10.5 Recount and exact question distribution

The exact census is:

| Qualifying first reason | Opened | Corpus | Total |
|---|---:|---:|---:|
| `correction-family-lineage-unresolved` | 1 | 5 | 6 |
| `record-family-lineage-unresolved` | 0 | 0 | 0 |
| `record-family-mutation-unresolved` | 1 | 0 | 1 |
| `unresolved-decision-threshold` | 4 | 5 | 9 |
| `unresolved-manual-correction-present` | 8 | 0 | 8 |
| **Total** | **14/90** | **10/50** | **24/140** |

The zero observed `record-family-lineage-unresolved` rows does not make that path dead: section 12
has isolated positive and negative fixtures, and the reason is included only under the composite
section-4.6 witness.

## 11. False-accusation and false-clearance analysis

### 11.1 Question emission is not an accusation

**Strongest correct-analysis shape:** a correct hand-Sidak analysis compares every family p-value
against `1 - (1 - 0.05) ** (1/N)`, or a correct analysis calls `pingouin.multicomp` over all N and
uses only adjusted results. Both may receive a question because the current grammar cannot prove
coverage.

**Protection:** the visible record is explicitly a question; the linked concern begins with an
`if`; neither has severity; the frozen abstention remains; Findings and scoring adapters exclude
question candidates by type. The question asks scope without asserting incomplete scope.

**Fixture:** `correct-question-complete-hand-sidak` and
`correct-question-complete-off-registry-multicomp` each emit exactly one question, zero candidates,
zero Findings, and one conditional concern.

### 11.2 Reason-name overreach

**Strongest correct-analysis shape:** a summary calls `len(results)` after raw conclusions, causing
the broad 3.0 manual-correction abstention even though no correction exists; or a record is mutated
for presentation only.

**Protection:** reason names are necessary but insufficient. The bounded reason-associated slice
must contain the exact section-4 correction witness. Generic calls, lengths, records, casts,
formatting, and stores do not match.

**Fixtures:** `no-question-e15-p3-summary-len`, `no-question-generic-record-update`, and
`no-question-float-round-presentation` emit no question and preserve exact reasons.

### 11.3 Unrelated or decorative correction names

**Strongest correct-analysis shape:** a module imports `multipletests`, stores a variable named
`bonferroni`, mentions Holm in a report string, or calls an unrelated `sidak` helper on non-p data
while the actual family is already correctly handled elsewhere.

**Protection:** section 4.2 requires resolved API plus a family-p input; section 4.3 reads only the
callee terminal slot and also requires a family-p-derived argument. Non-callee identifiers and all
prose channels are excluded.

**Fixtures:** `no-question-unused-correction-import`, `no-question-noncallee-correction-renames`,
`no-question-report-correction-prose`, and `no-question-sidak-nonp-call` emit no question. A paired
control changes only the callee terminal and must emit a question.

### 11.4 Arithmetic overreach

**Strongest correct-analysis shape:** p-values are scaled for a plot, converted to percentages,
rounded, or multiplied by a unit constant unrelated to a decision; a threshold helper computes an
unrelated power expression.

**Protection:** P must be family-p-derived, K has a closed cardinality grammar, the expression must
feed the reason-associated correction/decision slice, and every other operator/callee abstains
without a question. Literal Decimal construction uses source text.

**Fixtures:** `no-question-p-percent-display`, `no-question-p-unit-conversion`,
`no-question-sidak-shape-off-decision-slice`, and `question-hand-bonferroni-associated-control`.

### 11.5 Record overreach and merge attacks

**Strongest correct-analysis shape:** one record field contains a fully corrected p while another
contains raw p for display; a record is mutated after a consumer; or corrected and raw origins
merge in a conditional field.

**Protection:** section 4.6 requires a closed correction origin causally feeding the exact guarded
store. Existing 3.0 record mutation/lineage refusals remain. No question classifier resolves or
merges a record edge that 3.0 marked unresolved; the question cannot create a corrected-position
claim.

**Fixtures:** `question-record-cross-field-correction`,
`question-record-partial-correction-store`, `no-question-record-display-mutation`, and
`no-question-record-raw-adjusted-merge` pin the distinction.

### 11.6 A-answer false accusation

**Strongest correct-analysis shape:** a human mistakenly answers A for a script whose correction
actually covers all N.

**Protection:** only the human Answer and an explicitly author-attested ConditionalConcern are
created. The detector result remains abstain/covered as structurally determined; there is no
Finding, severity, or evaluation catch. The report label makes provenance unavoidable.

**Fixture:** `answer-a-mistaken-on-complete-correction` asserts zero Findings and exact
`Author attestation — not a tool Finding` rendering.

### 11.7 B-answer false clearance

**Strongest correct-analysis-claim attack:** a partial Holm call over two of seven, an unused
whole-family adjustment beside raw conclusions, a complete-sounding off-registry call, or a claimed
factor N applied only to selected positions is submitted as B.

**Protection:** the answer is only a start pointer. Total forward accounting and exact position
equality rerun under unchanged 3.0 rules. Any raw competing conclusion or unresolved edge yields
Disclosure plus open question. The author's integer cannot be used as AST evidence.

**Fixtures:** `answer-b-fails-partial-holm-e15-p5`, `answer-b-fails-partial-manual-e15-p6`,
`answer-b-fails-unused-complete-call`, `answer-b-fails-off-registry-complete-call`, and
`answer-b-fails-raw-adjusted-merge` all produce zero clearance and zero Findings.

### 11.8 Binding and replay attacks

**Strongest attack:** reuse an old B answer after editing one p-value consumer, changing N,
rebinding the contract, moving the correction, or upgrading detector bytes.

**Protection:** question ID plus four independent scope/evidence digests bind the answer; validation
is all-or-nothing; detector/version/profile changes alter the question evidence. No fuzzy path,
line-only, or prose match exists.

**Fixtures:** every one-field stale mutation in section 12.5 fails with its exact preflight error;
unchanged bytes replay exactly.

### 11.9 Upstream and opaque corrections

**Strongest correct-analysis shape:** adjusted p-values are loaded from a file or returned by an
unresolved imported helper.

**Protection:** there is no local correction span and no closed witness. The existing upstream or
unresolved-consumer abstention remains without a question. The author must supply inspectable code
in a future source revision; an attestation cannot substitute for computational lineage.

**Fixtures:** `no-question-file-loaded-adjusted-p` and
`no-question-unresolved-imported-correction-helper`.

### 11.10 Multiple correction occurrences

**Strongest correct-analysis shape:** two separately coded correction operations cover disjoint
prespecified portions under a valid collective scheme, so neither single operation covers all N.
Asking the singular question twice could turn two truthful “no” answers into a misleading
whole-family concern.

**Protection:** section 4.7 requires exactly one distinct associated correction occurrence after
clone coalescing and dominance. Two occurrences emit no scope question and preserve the original
abstention. This delta does not interpret collective correction schemes.

**Fixture:** `no-question-two-distinct-correction-occurrences` uses two disjoint
`pingouin.multicomp` calls, retains first reason `unresolved-manual-correction-present`, and emits
zero questions and zero Findings.

## 12. Executable fixture matrix

Every fixture is a real project with contract and CSV, run through the real 3.1 adapter/controller;
fixture-shaped AST assertions are insufficient. Expected rows live in an independent design-oracle
JSON with source digests and clause references. No expected outcome is sourced from a test module or
implementation output.

### 12.1 Question-emission and no-question fixtures

| Fixture | Expected source result | Question expectation |
|---|---|---|
| `question-default-multipletests-unresolved` | `correction-family-lineage-unresolved` | one registered-call question |
| `question-off-registry-multicomp` | `unresolved-manual-correction-present` | one terminal-call question |
| `question-hand-sidak-threshold` | `unresolved-decision-threshold` | one threshold question |
| `question-hand-bonferroni-p-multiply` | `unresolved-manual-correction-present` | one adjusted-p question |
| `question-record-partial-correction-store` | `record-family-mutation-unresolved` | one record-store question |
| `question-record-cross-field-correction` | `record-family-lineage-unresolved` | one record-store question |
| `no-question-e15-p3-summary-len` | `unresolved-manual-correction-present` | zero questions |
| `no-question-generic-record-update` | `record-family-mutation-unresolved` | zero questions |
| `no-question-bare-001-threshold` | `unresolved-decision-threshold` | zero questions |
| `no-question-computed-call-threshold` | `unresolved-decision-threshold` | zero questions |
| `no-question-file-loaded-adjusted-p` | `upstream-correction-lineage-unresolved` | zero questions |
| `no-question-unresolved-imported-correction-helper` | existing unresolved reason | zero questions |
| `no-question-unused-correction-import` | frozen source result | zero questions |
| `no-question-noncallee-correction-renames` | frozen source result | zero questions |
| `no-question-report-correction-prose` | frozen source result | zero questions |
| `no-question-two-distinct-correction-occurrences` | `unresolved-manual-correction-present` | zero questions |

Each question fixture also asserts the exact source span, N, witness kind, question ID inputs,
closed wording, zero Findings, and one linked concern.

### 12.2 A-answer fixtures

| Fixture | Expected result |
|---|---|
| `answer-a-partial-holm-e15-p5` | source abstention unchanged; one Answer; question answered; one author-attested ConditionalConcern; zero Findings |
| `answer-a-partial-manual-e15-p6` | same record pattern with N=8 |
| `answer-a-mistaken-on-complete-correction` | author-attributed concern only; structurally complete result is not converted into a Finding |
| `answer-a-extra-nonopen-question-entry` | `attestations-answer-cardinality-invalid`; no bundle |
| `answer-a-duplicate-question-entry` | `attestations-answer-cardinality-invalid`; no bundle |

### 12.3 B-answer-proves fixtures

| Fixture | Required proof and result |
|---|---|
| `answer-b-proves-e13-n1-default-multipletests` | Claimed line 79 guides the existing default-method call/input mapping; unchanged checks prove positions `[0,1,2,3,4]` and adjusted conclusions; existing `covered/complete` plus answer-guided receipt |
| `answer-b-proves-complete-manual-grammar-control` | A synthetic question-triggering wrapper points to an expression already inside the 3.0 manual grammar; unchanged checks prove all N positions; existing `covered/complete` |

The first fixture is load-bearing. If the existing checks cannot prove E13 N1 at the claimed node
without a new grammar, the build stops under section 17; the implementation may not weaken the
proof or silently convert this row into a B-fails fixture.

### 12.4 B-answer-fails fixtures

| Fixture | Expected result |
|---|---|
| `answer-b-fails-partial-holm-e15-p5` | original abstention; open question; one Disclosure; proved subset `[0,1]/7` is not clearance |
| `answer-b-fails-partial-manual-e15-p6` | original abstention; open question; one Disclosure; selected positions are not all 8 |
| `answer-b-fails-unused-complete-call` | raw verdict consumer blocks complete coverage; Disclosure |
| `answer-b-fails-off-registry-complete-call` | existing grammar cannot prove the call; Disclosure |
| `answer-b-fails-raw-adjusted-merge` | unresolved merge; Disclosure |
| `answer-b-fails-factor-n-but-subset-flow` | claimed N is ignored as evidence; structural subset remains; Disclosure |

Every B-fails fixture asserts no candidate, no Finding, no no-issue result, no new corrected
position, question status open, Answer retained, and `non_accusatory=true`.

### 12.5 Attestation-refusal fixtures

The suite mutates one field at a time from a valid A and B file:

| Fixture | Exact category |
|---|---|
| `attestation-stale-snapshot-digest` | `attestations-snapshot-binding-mismatch` |
| `attestation-stale-analysis-digest` | `attestations-analysis-binding-mismatch` |
| `attestation-stale-question-evidence-digest` | `attestations-evidence-binding-mismatch` |
| `attestation-stale-authority-digest` | `attestations-authority-binding-mismatch` |
| `attestation-wrong-question-id` | `attestations-question-not-open` |
| `attestation-zero-answer-entries` | `attestations-answer-cardinality-invalid` |
| `attestation-two-answer-entries` | `attestations-answer-cardinality-invalid` |
| `attestation-nonnull-supersession` | `attestations-supersession-invalid` |
| `attestation-extra-field` | `attestations-schema-invalid` |
| `attestation-b-missing-claim` | `attestations-schema-invalid` |
| `attestation-a-has-claim` | `attestations-schema-invalid` |
| `attestation-claim-span-out-of-range` | `attestations-claimed-correction-invalid` |
| `attestation-factor-source-mismatch` | `attestations-claimed-correction-invalid` |
| `attestation-answer-from-project-tree` | `attestations-file-path-unsafe` |
| `attestation-answer-symlink` | `attestations-file-path-unsafe` |
| `attestation-qualified-lane` | binding refusal before MT execution |

Each asserts nonzero preflight, exact deterministic error category, and absence of a partial audit
bundle or public Answer.

### 12.6 Replay fixture count

The attested replay hard stop comprises exactly 15 bundles:

- 3 A-answer bundles;
- 2 B-proves bundles;
- 6 B-fails bundles;
- 2 separately pinned unknown and omitted-answer bundles; and
- 2 A/B identical-bytes-at-a-different-input-path equivalence bundles.

Each runs twice and compares canonical bundle, lock, report, and manifest bytes. Refusal fixtures are
separately run twice and compare exact exit status and stderr bytes.

## 13. Agent-skill flow addendum

`docs/AGENTIC_SKILL.md`, the authoritative `.agents/skills/scientific-audit` source, and its
test-enforced plugin copy receive the same bounded addendum. It applies to Claude Code and Codex
skill use; the CLI remains provider-independent and authoritative.

The noninteractive two-run flow is:

1. The agent runs the audit without attestations and verifies audit integrity.
2. If open 3.1 correction-scope MaterialQuestions exist, it presents the exact closed question,
   N, and source location. It does not paraphrase the question into an accusation.
3. It states the three exact choices and the asymmetry: A is recorded as author attestation, B is
   only a pointer for structural recheck, and unknown leaves the question open.
4. It asks the human to select A, B, or unknown. It never answers from code, comments, reports,
   likely intent, or its own statistical judgment.
5. For B only, it separately asks the human for the exact correction source span and one closed
   factor kind/value from section 6.2. If the human cannot provide them, the only valid selection is
   unknown; the agent may not infer a line or factor.
6. It requires the audit output root to be outside the audited project, requests a machine template
   from that integrity-verified output, writes the human's explicit values to a separate answer
   file outside the audited project, shows the completed bounded fields to the human, and obtains
   authorization to submit it.
7. It reruns the CLI with `--attestations`, verifies integrity, and reports record types separately:
   Findings, ConditionalConcerns, MaterialQuestions, Answers, and Disclosures.
8. It states whether a B answer was structurally proved or remained unverified. It never calls an
   unverified B “cleared,” and never calls an A concern a Finding.

The CLI may generate an **unanswered request template** in the audit output containing question and
digest bindings, closed options, and null answer fields. That template is not an Answer, is not
automatically consumed, and cannot include a suggested option. The user/agent must create the
explicit input file named on the second run.

Only one MT correction-scope question may exist in one audit under this profile. Other check
families' questions follow their existing workflows; the skill cannot combine them with this
attestation profile, generalize this answer, or reuse it across snapshots.

The expected agent report adds:

```text
Author attestations are reported separately from tool Findings.
A completeness attestation was used only to guide structural verification.
An unverified completeness attestation remains an open MaterialQuestion and Disclosure.
```

The briefing may explain these trust rules. It must not tell an author which option improves an
audit outcome or how to phrase code so structural checks pass.

## 14. Scoring isolation and honest read

### 14.1 Blind-envelope scoring is unchanged

MaterialQuestions, ConditionalConcerns, Answers, and Disclosures are not detector catches. Blind
envelopes have no author and supply no attestation file. Question emission neither increments
first-contact recall nor counts as a negative candidate. The evaluator continues to score only the
frozen candidate/Finding semantics.

Therefore:

- E15 remains `2/6` first-contact recall;
- the E13+E14+E15 class window remains `6/18`;
- the promotion threshold, trailing-window arithmetic, negative hard stops, and Finding replay
  rules are unchanged; and
- question counts are reported only as an auxiliary usability measure, never promotion evidence.

The envelope replay hard stop still requires source outcomes and Findings to be identical. An
additional no-attestation question replay gate checks question determinism without changing the
score.

### 14.2 What 3.1 buys real users

Today, a user sees only an abstention for a positively located partial or opaque correction. Version
3.1 exposes the exact unresolved material question and provides a durable, scope-bound way to
answer it. It distinguishes an admission against interest from a tool demonstration and gives a
self-serving assertion a safe route to independent verification without trusting it.

This can make audits more actionable:

- authors can explicitly disclose that only part of a declared family was corrected;
- a source location can focus an existing structural proof that broad discovery could not select;
- failed verification is visible as an open question and Disclosure instead of disappearing as a
  silent abstention; and
- answers cannot drift across code states.

It does **not** improve blind detector recall. The AP-recognition design—proving adjusted-p
`AP(C,POS)` flows, partial correction position sets, and proper-subset manual factors—remains the
recognizer path for E15 P5/P6 and structurally similar partial corrections. E15 P3 instead needs a
separate false-abstention refinement so its summary `len(results)` no longer masquerades as manual
correction. This delta adds neither change and must not be used as a substitute.

### 14.3 Residuals

The following remain outside 3.1:

- new manual correction forms, including `p < ALPHA/K` coverage recognition;
- AP recognition for cross-field and partial record corrections;
- proper-subset manual factors as verified correction coverage;
- zip write-back dual polarity;
- imported/file-loaded correction implementation;
- author claims about unparsed external tools; and
- any attempt to infer complete correction from report prose.

Those require their own correction-surface or lineage design. An attestation can describe them but
cannot verify them.

## 15. Validation and build gates

### 15.1 Frozen-isolation and identity gates

1. Pin every section-2.4 digest before build and after final edits.
2. Assert all 3.0 and older MT implementation files, qualified pseudoreplication modules,
   GrantPins, grants, qualification records, threshold policies, and wording objects are byte-equal.
3. Run the two-registry differential and prove no qualified record or Finding byte derives from a
   development-inclusive registry digest.
4. Assert the development binding alone advances to 3.1.0 and historical versions remain
   replay-resolvable.
5. Assert contract `1.2.0`, MT evidence v2, and Finding wording v2 bytes are unchanged.

### 15.2 Closed reason and witness gates

1. Assert the copied reason registry has exactly 61 entries and exact equality with 3.0.
2. Assert the qualifying name set equals exactly the five section-3.2 strings.
3. Assert the question fixture emission-reason set equals those five; a documented fixture must
   exercise `record-family-lineage-unresolved` despite its zero corpus count.
4. Parameterize every grammar production and every refused near-neighbor in section 4.
5. Assert reason-only, witness-only, wrong-slice, wrong-N, unresolved-association, and
   multiple-distinct-witness cases emit zero questions.
6. Assert dominance, clone coalescing, exact-one cardinality, and ordering exactly.

### 15.3 Public-record and wording gates

1. Validate every generated DetectorResult, MaterialQuestion, Answer, ConditionalConcern, and
   Disclosure against accepted schema `0.21.0`.
2. Assert question-result `state=material_question_candidate`,
   `candidate.assessment_type=material_question`, and exclusion from Finding admission.
3. Assert A yields Answer plus concern, never Finding; B-fails yields Answer plus Disclosure/open
   concern, never clearance; B-proves requires independent complete coverage.
4. Assert no concern/question/disclosure has severity or publication materiality.
5. Assert every Disclosure has `non_accusatory=true`.
6. Pin wording profile bytes, semantic digest, slot set, option order, and exact visible strings.
7. Assert source text and answer text do not appear in wording, IDs, errors, or reports except the
   closed human actor display name permitted by the public Answer schema.

### 15.4 Prose tripwire

The tripwire executes every new predicate fixture and performs paired mutations:

- add/remove/change comments, docstrings, Markdown/report files, format-string text, ordinary
  string literals, and source encoding trivia;
- rename every non-callee identifier to `bonferroni`, `holm`, `sidak`,
  `benjamini_hochberg`, `multipletests`, and `p_adjust`;
- add correction phrases to report and format strings;
- change human display names and external answer-file location while retaining semantic bindings;
- paired callee-terminal controls that change only the terminal from nonregistry to registry;
- structural positive controls that delete the p-derived correction expression or sever its
  reason association; and
- source-text numeric controls such as `0.050`, `5e-2`, and their float/Decimal traps.

All prose/non-callee mutations must preserve question classification and structural evidence.
Visible question bytes change only when a permitted structured slot changes. Callee/structural
controls must change the witness exactly as specified. The tripwire covers reason selection,
witness matching, association, deduplication, wording, A rendering, B recheck routing, Disclosure,
and errors—not merely the top-level detector.

### 15.5 Attestation-schema and trust gates

1. Execute every section-12.5 refusal through the CLI and compare exact errors.
2. Fuzz duplicate keys, size/entry ceilings, symlinks, project-contained files, JSON numbers,
   span bounds, supersession cycles, option/value mismatches, and extra fields.
3. Prove a human B value never enters AST value resolution, corrected-position computation, or
   evidence except as a pointer/receipt.
4. Differentially run every B fixture with each claimed factor value in `1..N`; structural output
   may change only if the pointed **source node** selected changes, never because the integer claim
   changed.
5. Search every A/B output for Finding IDs and source classifications; assert zero answer-derived
   Finding bytes and zero answer-only clearances.
6. Assert generic interaction Answer routes cannot answer this question subtype.

### 15.6 Corpus and envelope oracle gates

1. Run the 90 opened cases at adapter/controller level; assert exact 3.0 source-result bytes and the
   exact 14-row question set.
2. Run all 50 corpus cases through the same level; assert exact frozen source-result bytes and the
   exact 10-row question set.
3. Assert question distribution `6/0/1/9/8` in section-10.5 reason order and total `24/140`.
4. Assert each question row has exactly one question/concern and all other rows have zero.
5. Assert E15 P3, E15 N9, corpus `spec-20`, `spec-42`, and `spec-50` are explicit no-question
   controls.
6. Re-run all existing E10–E15 source oracles and frozen 2.1/2.2/2.3/3.0 replay anchors unchanged.
7. Run the 15 attested replay bundles twice byte-for-byte.

### 15.7 Regression and suite gates

Required test families include:

- question classifier identity and all constructor guards;
- 61-reason and five-reason set equality;
- witness grammar and adversaries;
- question/concern/answer/disclosure schema goldens;
- attestation input parser and digest binding;
- A/B/unknown state transitions and supersession;
- all 140 no-attestation oracle rows;
- 15 attested replay bundles;
- reporting separation and agent-protocol counts;
- scoring isolation and qualification differential;
- prose tripwire; and
- frozen 3.0 replay anchor.

After the final source change, regenerate scientific registries, capability manifests, maturity
ledger, and repository manifest in that order, then run fresh:

```bash
ruff check .
ruff format --check .
mypy src
pytest
python scripts/validate_starter.py
```

The full suite must be green. Release-identity, registry, ledger, schema-catalog, and source-manifest
tests are hard gates, not post-build cleanup.

## 16. File-by-file implementation plan

### 16.1 New versioned detector files

- `src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3_1.py` — copy v3;
  preserve source analysis and expose bounded reason-associated witness edges without changing
  source outcomes.
- `src/sc_referee/scientific_checks/code_csv_multiple_testing_record_model_v3_1.py` — copy v3;
  expose immutable record provenance needed by section 4.6; no record admission change.
- `src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v3_1.py` — copy v3;
  preserve all source rows and construct question candidates after first-reason freeze.
- `src/sc_referee/scientific_checks/integration_multiple_testing_v3_1.py` — copy v3;
  bind question candidates and answer-guided recheck without changing Finding integration.
- `src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v3_1.py` — versioned detector
  identity, manifest projection, and constructor guards.
- `src/sc_referee/scientific_checks/multiple_testing_scope_questions_v1.py` — closed reason map,
  witness object, canonical identity, wording projection, and question/concern construction.
- `src/sc_referee/multiple_testing_scope_attestations_v1.py` — strict input parsing, digest binding,
  Answer construction, A/B/unknown state transitions, Disclosure construction, and replay receipt.

### 16.2 Narrow shared integration edits

- `src/sc_referee/cli.py` — add explicit `--attestations` option and deterministic preflight errors;
  no prompt/stdin path.
- `src/sc_referee/controller.py` — schedule the development-only question/attestation stage,
  preserve record separation, lock input digests, and emit unanswered templates.
- `src/sc_referee/interaction.py` — add only the closed correction-scope Answer projection and
  prevent generic routes from answering this subtype.
- reporting policy/templates — render Answer provenance, open/answered question state, conditional
  concern, and unverified B Disclosure in separate sections; do not modify Finding wording.
- storage/replay/input-manifest code — include raw and semantic attestation digests and deterministic
  record ordering.

Any shared edit must be covered by a qualified-lane byte differential. If shared integration cannot
avoid changing qualified bytes, the build stops and versions the integration path instead.

### 16.3 Resources and policy records

- `src/sc_referee/resources/input-schemas-v1/multiple-testing-correction-scope-attestations-v1.schema.json`
  — the private closed input schema; accepted public schemas remain untouched;
- `src/sc_referee/resources/multiple-testing-question-profiles-v1/correction-scope-v1.json` — the
  canonical development wording object for
  `material-question:multiple-testing-correction-scope-v1`;
- detector/check development registry records for 3.1 while retaining all historical entries;
- ADR-0080 (or next available number) with section-2.5 content;
- `docs/AGENTIC_SKILL.md`, authoritative scientific-audit skill references, and exact plugin copies
  with the section-13 addendum;
- capability registry, maturity ledger, manifest, and registry-digest regeneration.

### 16.4 Evaluation and tests

- `evaluation/development/multitest-code-slice-v3_1/` — independent fixture sources, oracle JSON,
  attestation files, wording profile, development ledger, and manifest;
- version-scoped unit tests for the question classifier, witness grammar, adapter, detector,
  interaction, reporting, and input parser;
- opened-envelope and corpus controller-level question oracles;
- A/B/unknown, refusal, supersession, replay, prose-tripwire, and scoring-isolation tests; and
- frozen 3.0 source/adapter/controller replay anchor tests.

No 3.0 fixture oracle, frozen corpus record, opened-envelope source, or historical comparison row is
regenerated.

## 17. Stop-and-report rule

Stop and report a design regression instead of adapting this design if any of the following occurs:

1. a no-attestation 3.1 source result differs from 3.0 for any of the 140 pinned cases;
2. the question set differs from exactly the 14 opened and 10 corpus rows in section 10;
3. E15 P3 emits a question without a section-4 witness;
4. a correct question fixture emits a candidate or Finding;
5. an A answer produces a Finding, severity, or detector catch;
6. a B answer changes classification or corrected positions without unchanged structural proof;
7. `answer-b-proves-e13-n1-default-multipletests` cannot prove complete coverage under existing
   grammar;
8. any B-fails fixture closes the question or suppresses the Disclosure;
9. stale/wrong bindings are accepted or partially applied;
10. attested replay is not byte-identical `15/15`;
11. a prose/non-callee mutation changes evidence or question classification;
12. the 61-reason set, five-reason set, or `24/140` census differs;
13. a qualified-lane, GrantPin, grant, qualification, metric, threshold-policy, or Finding byte
    changes; or
14. implementation requires new correction, threshold, record, consumer, or AP grammar.

Conservative refusal is not permission to relabel a pinned row or drop a required question. A
failure in either direction is reported to the supervisor with the exact fixture, source digest,
observed result, expected clause, and minimal structural cause.

## 18. Revision log

### Revision 0 — 2026-08-29

Initial commissioned design. It:

- closes question eligibility to five of 61 reasons plus a reason-associated structural witness;
- requires exactly one distinct correction occurrence, preventing singular questions from
  misdescribing collective schemes;
- defines closed correction-call, manual arithmetic, threshold, and record-store witnesses;
- uses existing MaterialQuestion, Answer, ConditionalConcern, and Disclosure schemas without
  weakening the Finding boundary;
- makes the A/B trust rule explicitly asymmetric;
- specifies a noninteractive, digest-bound attestation input and deterministic replay;
- pins 14/90 opened and 10/50 corpus question cases while preserving every 3.0 source result;
- records E15 P3 as a reason-only no-question control because its trigger is `len(results)`, not a
  correction witness;
- isolates blind scoring and promotion arithmetic; and
- leaves AP/correction recognition to a separate future design.
