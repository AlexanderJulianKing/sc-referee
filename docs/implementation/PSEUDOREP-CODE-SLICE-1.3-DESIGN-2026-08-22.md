# Pseudoreplication code slice 1.3 delta design — 2026-08-22

- **Status:** Built for maintainer re-check
- **Decision provenance:** Fable, under executive authority granted by Alex 2026-08-21
- **Normative bases:**
  `docs/implementation/PSEUDOREP-CODE-SLICE-DESIGN-2026-08-22.md`,
  `docs/implementation/PSEUDOREP-CODE-SLICE-1.1-DESIGN-2026-08-22.md`, and
  `docs/implementation/PSEUDOREP-CODE-SLICE-1.2-DESIGN-2026-08-22.md`
- **Governing ADR:**
  `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md`
- **Delta identity:** check `1.3.3`, adapter and recognition grammar `1.3.0`, separate experimental
  code-lane detector `1.3.0`
- **Evidence:** Python AST, CSV structure, frozen contract, and established API names only
- **Project-authored-code execution:** forbidden

## 1. Boundary

This is a terminal-description and build-hygiene delta. X7 admits six exact Python idioms only where
X3 straight-line descriptive values or X5 descriptive-helper return elements were already permitted.
It does not add a reader, selection, test API, test-argument path, p-result sink, authority fact,
Finding premise, production pin, prose channel, inter-file analysis, or execution path. A candidate
still requires the unchanged single authorized reader → two raw group-row selections → registered
row-independent two-sample test → p-result sink chain.

Code slice 1.3 uses a new detector module. Detector files 1.0.0, 1.1.0, and 1.2.0 remain untouched.
The capability source set retains separate 1.0.0, 1.1.0, 1.2.0, and 1.3.0 detector records keyed by
`(detector_id, detector_version)`; only the greatest exact semantic version is projected as live.

### 1.1 BUILD-NOTES

- Ambiguity is resolved toward abstention. In particular, tuple/list-target assignment is admitted as
  descriptive only for an exact literal tuple RHS; a tracked groupby pair or test-result tuple is not a
  descriptive assignment.
- X7 wrappers do not compose: `int(float(E))` and `float(int(E))` abstain. `int` and `float` must be
  unshadowed builtins with one positional argument and no keywords.
- `.size` and `.shape[0]` are count-family properties only on a tracked selection or identity value;
  `.shape[1]`, `.shape[-1]`, and `df.size` are not accepted.
- `.var` through a local `Name` return was already structurally possible under X4 when its post-inline
  dataflow passed; 1.3 makes the exact `.var()`/`.var(ddof=1)` form explicit in X3/X5 and adds direct
  expression use.
- X6 constant-only subtrees return an empty parent list, not an unresolved value. The complete outer
  arithmetic must still contain at least one tracked descriptive parent.
- The X5 output graph remains print-only. A structured result containing a registered test result, a
  no-return `report(res)` helper, frame-valued returns, conditional helpers, frame display methods, and
  per-row print loops remain outside the grammar.
- The restored false-accusation halt test installs a test-only root `analysis.py` containing the exact
  pandas/SciPy code-lane reader-selection-test-p-sink chain, an active 1.1 scientific-requirement
  contract over `data/input.csv`, `bird_code`, and `condition`, and a repeated-unit CSV. The harness
  intentionally labels `rq4` as a true negative. The registered detector itself produces the positive,
  the harness records `false_accusation`, writes `FALSE_ACCUSATION_HALT.json`, preserves all four
  detector-produced case outputs, and halts again after the sentinel is removed. No persisted detector
  result is forged or edited.
- The committed complete-domain production demonstration now reaches `_verify_case` for both its error
  and control cases and directly asserts both `project_execution_count == 0` and an empty audit-bundle
  `executions` array. The separately retained whole-demonstration check still stops at the deliberately
  stale dependence grant.
- Capability history now contains the frozen 1.0.0 detector record with implementation digest
  `sha256:e52a367ffb97ca6706d6d2cfd621f0283cb12d99d1483304142d365aad25f86e`,
  alongside 1.1.0, 1.2.0, and live 1.3.0.
- The root `MANIFEST.sha256` is not refreshed. Its dirty-worktree failure remains an expected
  release-time gate owned by Alex.

### 1.2 Complete retired-report-lane inventory

Exactly 37 collected items carry `retired_report_lane`. Every item below constructs, freezes,
qualifies, promotes, or replays the withdrawn report-lane identity; none exercises the active code
adapter. The two non-report guards from the original 31-item exclusion—
`test_task_binding_disclosure_is_digest_bound_only_for_development_loop` and
`test_false_accusation_halts_and_preserves_per_case_outputs`—are active in the default gate.

The one retired pilot item is bound to the withdrawn report detector and its installed historical
Finding path:

- `test_dependence_six_role_fixture_runs_real_pipeline_with_one_installed_finding`

The two retired promotion items rederive or compare the withdrawn report detector's frozen exam/grant
identity:

- `test_exam_time_detector_tuple_is_retained_while_live_binding_identity_drifts_at_v019`
- `test_round2_records_rederive_at_current_pins_and_resolve_test_local_grant`

The following 26 scaffold items consume the withdrawn report-lane briefs, kernels, sealed allocation,
threshold protocol, or held-out configuration and therefore cannot qualify the code identity:

- `test_dependence_precase_reads_complete_live_registry_binding`
- `test_dependence_fourteen_briefs_replay_and_pass_literal_leakage_screen`
- `test_renamed_implementation_drafts_are_distinct_across_blocks`
- `test_all_heldout_briefs_freeze_disjoint_binary_fraction_literals`
- `test_heldout_brief_honest_author_path_is_byte_exact[error_bearing]`
- `test_heldout_brief_honest_author_path_is_byte_exact[corrected_twin]`
- `test_heldout_brief_honest_author_path_is_byte_exact[valid_alternative]`
- `test_heldout_brief_honest_author_path_is_byte_exact[hard_negative]`
- `test_heldout_brief_honest_author_path_is_byte_exact[ambiguous]`
- `test_heldout_brief_honest_author_path_is_byte_exact[unsupported]`
- `test_heldout_brief_honest_author_path_is_byte_exact[renamed_implementation]`
- `test_heldout_brief_real_kernel_outcome_matches_cell[error_bearing]`
- `test_heldout_brief_real_kernel_outcome_matches_cell[corrected_twin]`
- `test_heldout_brief_real_kernel_outcome_matches_cell[valid_alternative]`
- `test_heldout_brief_real_kernel_outcome_matches_cell[hard_negative]`
- `test_heldout_brief_real_kernel_outcome_matches_cell[ambiguous]`
- `test_heldout_brief_real_kernel_outcome_matches_cell[unsupported]`
- `test_heldout_brief_real_kernel_outcome_matches_cell[renamed_implementation]`
- `test_two_block_allocator_accepts_complete_fourteen_case_matrix`
- `test_freeze_uses_sealed_author_slots_not_future_runtime_actors`
- `test_dependence_threshold_refuses_nested_protocol_digest_drift`
- `test_dependence_threshold_refuses_lane_freeze_digest_drift`
- `test_dependence_threshold_selection_cannot_bypass_heldout_seal_refusal`
- `test_dependence_heldout_config_carries_every_envelope_field`
- `test_dependence_threshold_config_selects_rehearsal_and_carries_every_envelope_field`
- `test_dependence_heldout_loader_refuses_six_cases`

The final eight items instantiate `_withdrawn_report_lane_adapter_for_replay`; the five parameterized
routes normalize historical report-only shadow payloads and the three explicitly named historical tests
retain report-parser, paired-procedure, and writer-scope behavior:

- `test_all_shadow_routes_normalize_once_under_question_only_ceiling[shadow_candidate-applicable-multiple_analyzed_rows_per_authorized_independent_unit]`
- `test_all_shadow_routes_normalize_once_under_question_only_ceiling[coverage_note-applicable-one_analyzed_row_per_authorized_independent_unit]`
- `test_all_shadow_routes_normalize_once_under_question_only_ceiling[material_question-ambiguous-None]`
- `test_all_shadow_routes_normalize_once_under_question_only_ceiling[no_lineage-not_applicable-None]`
- `test_all_shadow_routes_normalize_once_under_question_only_ceiling[unsupported-unsupported-None]`
- `test_historical_report_lane_legacy_python_ast_parser_identity_is_unsupported`
- `test_historical_report_lane_paired_procedure_gap_retains_named_abstention`
- `test_historical_report_lane_without_exact_writer_scope_is_unsupported`

## 2. Observed diagnosis and retained miss

The following observations are from Python AST/source bytes. Comments and docstrings are not consumed.

### 2.1 `e8f97fe750189052f726`

`describe_group(values)` returns a dict whose elements are exactly
`int(values.count())`, `float(values.mean())`, and `float(values.std(ddof=1))`; the two returned dicts
feed arithmetic and literal formatting under `print`, not either `ttest_ind` argument
(`evaluation/development/blind-envelope-2-2026-08-22/cases/e8f97fe750189052f726/project/analysis.py:28-34,49-57,67-92`).
`welch_degrees_of_freedom(a, b)` assigns `va, vb` from an exact tuple of `.var(ddof=1)`/`.count()`
arithmetic and returns one `float(...)` scalar used only by `print`
(`:37-40,55,91`). X7 rules 1, 2, 4, and 5 admit both descriptive helpers; the raw selections at lines
46-47, `ttest_ind` at line 54, and p-result sink at line 92 therefore form a candidate.

### 2.2 `2df3396d80adbb63dffb`

The only former 1.1 blocker was `print("  df = {:d}".format(n_total - 2))`; `n_total` is derived from
`len(control)` and `len(treated)` and is print-only
(`evaluation/development/blind-envelope-2-2026-08-22/cases/2df3396d80adbb63dffb/project/analysis.py:32-34,63`).
X6 already admitted it in 1.2. X7 does not alter this case; it remains a candidate.

### 2.3 `ca18f96d45dff1b921ad`

`compare_groups(df)` performs the registered `ttest_ind` and returns a dict that carries
`result.statistic` and `result.pvalue` alongside descriptive values; `main` passes that dict to the
no-return `report(res)` helper
(`evaluation/development/blind-envelope-2-2026-08-22/cases/ca18f96d45dff1b921ad/project/analysis.py:29-48,51-77`).
The returned value is print-only downstream, but it is a structured test-result payload and its output
helper violates the exact one-return X4 grammar. X7 deliberately does not lift either construct, so the
first reason remains `descriptive-helper-return-contract-unsupported`. This is the sixth opened positive
and remains an honest miss.

## 3. X7 normative grammar

“Descriptive position” below means only an X3 one-name straight-line descriptive assignment, an X7
literal-tuple destructuring assignment, or one independently checked element/scalar of an X5 helper
return. No X7 form may occur on either test-argument backward slice. Any violated signature, shadowed
builtin, unsupported receiver, unsupported use edge, or unresolved origin abstains.

### 3.1 Transparent numeric wrapper

Accept `int(E)` and `float(E)` iff all are true:

1. the builtin is not shadowed by import, assignment, function, async function, or class definition;
2. the call has exactly one positional argument and no keywords;
3. `E` independently satisfies the X3/X5 descriptive-element grammar; and
4. `E` is not itself an `int(...)` or `float(...)` call.

The wrapper adds no tracked parent and no conversion semantics; it preserves the parents of `E`.

### 3.2 Variance reduction

Add method `var` to the X3/X5 reduction set with exactly two accepted signatures: `.var()` and
`.var(ddof=1)`. Positional arguments, any other `ddof`, additional keywords, and all other signatures
abstain. The receiver must be a tracked selection or identity value and must not be aggregated or
unknown. The descriptive-loop reduction table is unchanged.

### 3.3 Count-family forms

Accept exactly these additional X3/X5 elements on a tracked selection or identity `NAME`:

- `NAME.size`;
- `NAME.shape[0]`, where the subscript is the literal integer zero; and
- `NAME.nunique()` with no arguments or keywords.

No corresponding form on the reader frame, grouped value, aggregation, unknown value, attribute chain,
or different subscript is accepted.

### 3.4 Literal-tuple destructuring

Accept `TARGET = RHS` as a descriptive assignment iff:

1. `TARGET` is a tuple or list of 1 through 16 distinct simple names;
2. `RHS` is an AST `Tuple` literal of identical length with no starred element; and
3. every RHS element independently satisfies the X5 element rule: an accepted descriptive reduction,
   count-family form, depth-one numeric wrapper, arithmetic descriptive descendant, literal, or exact
   group-label module constant.

Each target name is bound only to its corresponding element. A nonliteral tracked RHS, unequal length,
star, nested target, duplicate/rebinding target, groupby pair, or tuple containing test-result members
abstains with `descriptive-target-assignment-unsupported`. The separate exact two-name destructuring of
a registered positive test call remains the result-binding grammar and is not X7.

### 3.5 Direct reduction in descriptive arithmetic

An exact X3 reduction or count-family form may occur directly as a leaf of X5 arithmetic rather than
first being assigned to a name. The receiver and signature checks in sections 3.2-3.3 apply at every
leaf. Every constant-only subtree is valid and contributes zero parents; the complete expression must
still contain at least one descriptive parent. An aggregation or unknown receiver abstains.

### 3.6 Closed print formatting

For an X5 returned root or its already-accepted arithmetic/subscript descendant:

- an f-string `format_spec` is accepted only when it is an AST `JoinedStr` containing `Constant` nodes
  only; a nested replacement field or conversion remains unsupported; and
- `%` formatting is accepted only as a string-literal left operand with either one right operand or an
  AST tuple of operands, every one of which is an X5 descriptive name/closed descendant, a literal, or
  an exact group-label module constant.

Both forms must flow directly to unshadowed `print` under the existing X5 graph. Stored formatted
strings, file sinks, keywords to `print`, or any other dynamic operand abstain.

## 4. Hygiene closure

1. **H1 — retirement audit.** Of the original 31 excluded collected items, 29 are report-identity
   qualification/promotion items and remain retired. The task-binding disclosure test and
   `test_false_accusation_halts_and_preserves_per_case_outputs` are restored to the default gate. The
   explicitly historical report-adapter tests are marked as such and remain retired.
2. **H2 — drift guard.** The test constructs a test-scope pin from the live binding and live adapter
   identity, asserts `installed_pin_matches_live_identity(...) is True`, then changes only the grammar
   digest and asserts `False` and no grant resolution.
3. **H3 — `rq1`/`rq2`/`rq3`.** The three fixtures use the same flat script: a
   `csv.DictReader` materialization followed by separate `signal` and `reference` column lists and
   `st.ttest_ind(observed, reference)` (`tests/test_dependence_free_envelope.py:84-103`). Their CSV has
   `bird_code,session,signal,reference` and no contract group/contrast column
   (`tests/test_dependence_free_envelope.py:69-81`). They are honest
   `two-group-row-selection-unavailable` misses in the code lane, so `missed_unsupported` is retained and
   documented rather than presented as a catch.
4. **H4 — grant reproducibility.** The grant builder reprojects both frozen installed pin records from
   their qualification/metric bytes, and the active test compares every generated byte with
   `default_qualification_grant_root()` while retaining the live complete-domain binding check.
5. **H5 — adapter identity.** Withdrawn report-adapter tests are named and marked historical. Active
   equivalents assert the registered dependence module contains exactly `CodeCsvDependenceAdapter`,
   static Python evidence, no report/shadow lane, question-only output, and a closed prose-free
   counterevidence profile.
6. **H6 — version gates.** Finding and grant eligibility derive the active dependence check/detector
   tuple from `scientific_check_release_registry()` rather than comparing a version literal.
7. **H7 — detector history.** Capability detector records are uniquely keyed and sorted by
   `(detector_id, detector_version)`. The installed 1.0.0, 1.1.0, and 1.2.0 records retain implementation
   digests `sha256:e52a367ffb97ca6706d6d2cfd621f0283cb12d99d1483304142d365aad25f86e`,
   `sha256:3b136e2dcb33023c3f9abc0eb962b8120cda836e74bf715fd8c7c5383799da57`, and
   `sha256:ab6e90b5496996f769cb4af0b5ab60082778f0adf4378b1bb127c63ffb81da14`;
   live projection selects 1.3.0 without deleting any historical record.
8. **H8 — starter validator.** The validator retains an explicit lower-level dependence grant
   projection and asserts that the stale installed dependence pin does not grant live Finding strength;
   the public capability matrix still exposes only the live complete-domain Finding grant.

## 5. Development re-trace

All cases below are opened, label-visible development evidence and confer no blind credit.

| Envelope / case | 1.3 expectation | First reason or complete path |
| --- | --- | --- |
| 1 P1 `45dcad2f6496a0fd5778` | Candidate | Raw reader-selection-test-p-sink path. |
| 1 P2 `88e59abe85a8eea2b8cd` | Candidate | Raw reader-selection-test-p-sink path. |
| 1 P3 `0f721a41bac71a461dd2` | Candidate | Raw reader-selection-test-p-sink path. |
| 1 N1 `5994e65153b07855b07c` | Abstain | `aggregation-on-test-operand-path`. |
| 1 N2 `e804a86a1e05b781f292` | Not applicable | `no-repeated-authorized-unit`. |
| 1 N3 `11af5bb3f9b7e8e0b293` | Abstain | `tracked-value-mutation`. |
| 2 P1 `e8f97fe750189052f726` | **Candidate** | X7 closes both print-only descriptive helpers; raw chain remains complete. |
| 2 P2 `2df3396d80adbb63dffb` | Candidate | Existing X6 print-only arithmetic. |
| 2 P3 `ca18f96d45dff1b921ad` | Abstain; honest miss | `descriptive-helper-return-contract-unsupported`. |
| 2 N1 `15b07ef7670800ba88e0` | Abstain | `two-group-row-selection-unavailable`. |
| 2 N2 `5ef43dbf631adcf3daec` | Not applicable | `no-repeated-authorized-unit`. |
| 2 N3 `e60c84d0cda3cc465df7` | Abstain | `helper-body-statement-unsupported`. |
| 2 N4 `6090fc1b1b6dbfcd6eee` | Abstain | `additional-accepted-reader-present`. |
| 2 N5 `d4d95cdd4f4e698d675c` | Abstain | `descriptive-helper-return-contract-unsupported`. |

Honest opened expectation: **5/6 positives become evaluation candidates; 0/8 negatives become
candidates; all fourteen produce zero pre-qualification Findings and replay identically.**

The four K t-test cases remain 0/4 because none has one root `analysis.py`; each first reason is
`analysis-source-envelope-unavailable`. The two binomial K controls remain
`authorized-group-domain-not-exactly-two`.

## 6. Test-plan delta

Add or retain executable tests for:

- every X7 positive signature and a near miss for every parameter/receiver boundary;
- shadowed `int`/`float`, nested wrappers, wrong arity, and keywords;
- `.var()`/`.var(ddof=1)` and every refused argument shape;
- `.size`, `.shape[0]`, `.nunique()` and wrong receiver/index/arguments;
- tuple/list targets with exact tuple RHS, plus adversarial groupby-pair and test-result-tuple RHS;
- direct reductions in arithmetic, including an aggregated receiver that must abstain;
- constant-only X6 subtrees, constant-only f-string format specs, nested replacement refusal, and
  closed/refused `%` operands;
- a descriptive helper that secretly aggregates under a fresh name, a dict return reaching a test
  argument, and a helper mixing reductions with a registered test;
- all eight hygiene items, including exact historical detector digests and byte-reproducible grant
  resources;
- prose tripwire coverage through helper expansion and prose-byte mutation invariance;
- all fourteen opened cases plus four K t-test cases and two K binomial controls through normal audit;
- 108 blind and 155 regression cases with zero Findings, replay equality, ruff, mypy, and the starter
  validator. The root release-manifest digest check remains the one expected failure.

## 7. File-by-file build delta

- `src/sc_referee/scientific_checks/code_csv_dependence_dataflow.py`: X7 AST grammar and closed
  abstentions.
- `src/sc_referee/scientific_checks/code_csv_dependence_adapter.py`: adapter/check identity bump only.
- `src/sc_referee/detectors/bounded_code_csv_dependence_conflict_v1_3.py`: new detector identity.
- `src/sc_referee/detectors/method_conflict_registry.py`, `scientific_checks/profiles.py`,
  `scientific_checks/integration.py`, and `scientific_requirement_contract.py`: live 1.3 binding and
  frozen-contract migration.
- `src/sc_referee/capability_matrix.py`, `scripts/build_capability_source_manifests.py`, and packaged
  capability/scientific-check manifests: versioned detector history and live projection.
- `src/sc_referee/detectors/method_conflict_finding.py`,
  `method_conflict_grant_pins.py`, `scripts/build_method_conflict_grant_resources.py`, and
  `scripts/validate_starter.py`: H2/H4/H6/H8 hygiene closure.
- `tests/test_code_csv_dependence_dataflow.py`, `test_code_csv_dependence_adapter.py`,
  `test_dependence_code_slice_development.py`, `test_capability_matrix.py`,
  `test_dependence_free_envelope.py`, `test_dependence_recognition_scientific_adapter.py`, and
  `test_installed_method_conflict_grants.py`: X7, identity, history, and restored safety gates.
- `evaluation/development/pseudorep-code-slice-v1_3/DEVELOPMENT_LEDGER.json`: evaluation-only expected
  outcomes; no qualification credit.
- this delta, the 1.2 BUILD-NOTES correction, ADR-0076 amendment, public interface, maturity ledger, and
  growth-loop state: documentation and current identity only.

## 8. Observed versus inferred

Observed: the exact AST/source constructs and downstream uses in section 2; the old detector file
digests; the 31-item retirement audit; and normal-path outcomes after the build. Inferred and still
requiring future blind verification: that these bounded idioms cover enough independent author behavior
to achieve Envelope 3's 3/3 bar without adding false accusations. No opened case is blind evidence.

No build-changing question remains open. Envelope 3 is not created or frozen by this build.
