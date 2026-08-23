# Pseudoreplication code slice 2.1 design — 2026-08-22

- **Status:** Accepted and frozen for Envelope 5
- **Decision provenance:** Fable, under executive authority granted by Alex 2026-08-21
- **Decision date:** 2026-08-22
- **Normative base:** `docs/implementation/PSEUDOREP-CODE-SLICE-2.0-DESIGN-2026-08-22.md`
- **Governing ADR:**
  `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md`
- **Identity:** check, adapter, grammar, and separate experimental code-lane detector `2.1.0`
- **Evidence:** frozen contract, CSV structure, Python AST/dataflow, and established API names only
- **Prose evidence:** forbidden
- **Project-authored-code execution:** forbidden

## 0. BUILD-NOTES

- Ambiguity resolves to abstention and is recorded here; it never expands the conviction predicate.
- The rejected statement-level R1-a prototype is not part of 2.1. It created a code-lane candidate on
  opened negative `9cd65ce93b9b8f846eb8`; 2.1 retains the member-sensitive directional graph and every
  2.0 R2 guard.
- Advancing the shared integration subject gate to check `2.1.0` changes
  `scientific_checks/integration.py` to exact digest
  `sha256:99cc852d6f7a0f9c1f59d9a05d95136594ad6ccad4ebba3b96f5d474691d22f2` and therefore changes the
  founder adapter's content-addressed integration closure without changing founder core bytes or rules.
- The first complete normal-path trace preserved the required totals but exposed four earlier ordered
  reasons than the preliminary design trace: `0b9b803536c12e3870eb` stops at
  `helper-closure-or-nested-definition-unsupported`, `5bdfa31a22a40d58e20c` at
  `unregistered-component-consumer`, `4f622f87ad3c8a93a2d8` at `admission-call-off-list`, and
  `540f7dfdf1614ceda57d` at `multiple-rowwise-test-candidates`. Each remains an abstention; no
  expectation was changed toward conviction.
- The regression-corpus source update is digest-only: the changed exact-byte assertion in
  `tests/test_dependence_recognition_scientific_adapter.py` advances source digest to
  `sha256:a0dfe0d63ae034e5f7dcb6bc91eef7babd404484503f3791bca397a426b8c244`, ledger digest to
  `sha256:aa244f0a72850eab246ca1f484ca056ad0fef1946f736007df6c96c0987df1eb`, and execution-plan digest to
  `sha256:a12fc56fd627dfa0e067ac19b55f0fa42a34bb437e7ecf7621e2f558ad12cc8c`. The inventory replaces only
  the dependence check's 2.0.0 manifest projection with its 2.1.0 projection. No case expectation or
  eligibility changed.
- No test is newly retired. The existing 37 named report-lane retirements are unchanged.
- Detector 2.0.0 remains byte-identical at
  `sha256:261bfa27092c528cd86fb3905ced2fb1b2f296852f688ab4be3abaa94d57e901`.
- The built 2.1 analyzer is content-addressed at
  `sha256:22b85efb45c41602d45f93855a327bb1d83321f653d5470f6c8946c8003e6c29`; the registered recognition
  grammar digest is `sha256:e135a5182ebba66ffc987f8867c468c54a9a1ab72d34f76dedee9867c4c3b10e`, and the separate 2.1 detector
  source digest is `sha256:9c30154639e1fc013a0f82a5ee3d767202c121f42626b2c6497436e9305f2452`.
- The completed gates are: 5,059 active default-gate tests with the Alex-owned root-manifest inventory
  assertion deselected; 151 regression pytest cases through 110 selectors plus four direct audits for
  all 155 ledger cases; all 108 lifetime-blind cases; the 38 opened and four K normal-path cases;
  replay equality; Ruff check and format check; mypy over 171 source files; and
  `scripts/validate_starter.py`. All runnable gates are green. The separately run root-manifest
  assertion fails only because `MANIFEST.sha256` has not received Alex's release refresh; it was not
  changed.
- The implementation takes no builder discretion beyond the reviewed delta: annotation ASTs are
  excluded from runtime/free-name walks; import, file-parent, builtin, and tracked-name protections are
  retained; pre-test aggregation must still be output-only under R1; and the three A4 methods accept
  only the exact literal/closed-constant arities in section 5. No project-authored analysis code was
  executed.

## 1. Boundary and opened evidence

This document is a delta. Every 2.0 rule not replaced below remains normative. In particular, 2.1 does
not change contract profile `1.1.0`, authority fields, byte-exact authorized CSV path resolution, CSV
multiplicity or D1', reader/selection/test/sink allowlists, the single-reader rule, alternate-analysis
scan, operand-path aggregation and mutation guards, dependence-aware and unregistered-consumer sibling
guards, multiple-candidate guard, 50-trip resampling guard, p-result sink requirement, Finding wording,
zero-false-accusation standard, no-prose rule, or no-execution rule.

Envelope 4 is opened development evidence and earns no future blind credit. Its frozen 2.0 result was
2/6 positive candidates (`5c26014c176bf905c121`, `675de846f46beae7d442`), 0/6 negative candidates,
zero Findings, replay 12/12, closure 88/88, and label/role agreement 12/12. The acceptance bar missed by
one and the envelope is burned. Lifetime after scoring is 146 blind cases, zero false accusations, and
three blind catches.

The opened diagnosis found four bounded descriptive-admission blockers. Applying only A1 through A4 to
all 38 opened scripts changes two outcomes: `c07cc7c1a1f9730a3c9f` and
`d92b542e0bb28fa3c950` become candidates. The three shape-blocked negatives remain non-candidates under
their substantive aggregation, dependence-aware-sibling, or tracked-mutation guards. This is observed
development evidence, not qualification credit.

## 2. A1 — annotations are excluded syntax, not dataflow

### 2.1 Helper annotations

For an otherwise X4-eligible module-level synchronous helper:

1. Any `ast.arg.annotation` on a positional-or-keyword parameter is permitted.
2. Any `FunctionDef.returns` annotation is permitted.
3. Annotation subtrees are skipped by helper free-name, helper relevance, call-cycle, body-call,
   suppressor, and data-edge walks. They are never copied into expanded statements.
4. An annotation is never evaluated, resolved as an API, treated as a call, counted as a definition,
   or allowed to create, suppress, corroborate, or complete a candidate.

The existing refusals remain exact: positional-only parameters, keyword-only parameters, `*args`,
`**kwargs`, helper type comments, nonconstant defaults, decorators, async/yield, recursion, closures,
`global`/`nonlocal`, invalid return shape, and depth or call-site limits still abstain under their existing
codes. An annotated helper that aggregates on the test-operand path still abstains
`aggregation-on-test-operand-path` after successful expansion.

### 2.2 `main`

An otherwise valid zero-argument `def main()` may carry any return annotation. The return annotation is
not walked or resolved and adds no data edge. Parameter annotations on `main` remain irrelevant because
`main` still accepts no parameters; main type comments, decorators, async form, defaults, variadics, and
all nonzero-parameter shapes remain `analysis-scope-ambiguous`.

## 3. A2 — close the parameter-shadowing veto to resolution-critical names

Helper parameters are alpha-renamed at every successful inline site before body statements enter the
expanded program. A parameter spelling that equals a closed module string constant, numeric/bool
literal constant, or closed tuple constant therefore cannot shadow that module binding in the expanded
IR and is removed from the `helper-parameter-shape-unsupported` veto.

The veto remains for resolution-critical tracked names: names bound in `resolver.imports`, names in
`resolver.file_parents`, and names in `_UNSHADOWED_BUILTINS`. These bindings determine API, path, or
builtin identity and are not reinterpreted as ordinary constant collisions. The existing parameter and
helper-local alpha-renaming algorithm is unchanged. A parameter spelling that collides with a
caller-local tracked frame/value name is alpha-renamed and does not itself cause abstention or rebind
the caller value. If the expanded helper actually mutates or aggregates a tracked value, the unchanged
mutation and aggregation guards still fire from the resulting dataflow edges.

## 4. A3 — directional descriptive aggregation has no source-order condition

Delete only the source-order comparison in `_post_test_descriptive_aggregation`. An aggregation before
or after the candidate test is R1-admitted only when the existing directional checks prove all of the
following:

`_post_test_descriptive_aggregation` is retained as a historical implementation name only; after A3 it
governs qualifying descriptive aggregation on either side of the test in source order.

1. the aggregation call is absent from every value origin whose name is on either test-argument
   backward slice;
2. the aggregation reaches an accepted output sink through the existing closed assignment/member graph,
   or occurs inside an already valid descriptive loop; and
3. it does not reach the authorized reader call, registered test call, p-result path, or a tracked-frame
   store, and every 2.0 R2 whole-program guard still passes.

No aggregation is reclassified on an operand path. A pre-test `groupby().agg(...)` whose result, member,
alias, or derived value reaches either test argument abstains `aggregation-on-test-operand-path`. A
descriptive aggregation that fails the closed output/loop proof remains unadmitted.

## 5. A4 — three read-only pandas methods in R1 descriptive positions

Add exactly `reindex`, `unstack`, and `to_numpy` to `_V2_PANDAS_READONLY_METHODS`. They are R1 read-only
only under these closed call shapes:

| Method | Exact admitted call shape |
| --- | --- |
| `reindex` | Exactly one selector, supplied either as the sole positional argument or as the sole `index=` keyword. The selector is an `ast.List` or `ast.Tuple` of at most 16 literal scalar elements; a `Name` bound in `resolver.tuples`; or exact unshadowed `list(NAME)` where `NAME` is bound in `resolver.tuples`. No other keyword or axis form is accepted. |
| `unstack` | No argument; or exactly one literal level supplied as the sole positional argument or sole `level=` keyword. A literal level is an `ast.Constant` string or non-bool integer. |
| `to_numpy` | No positional arguments and either no keywords or exactly one `dtype=` keyword. `**kwargs` and every keyword other than `dtype` abstain. Nested calls in the dtype value remain independently subject to the closed R1 call registry. |

All three require the existing pandas read-only receiver proof and `inplace` rejection. Their result is a
derived descriptive value governed by the same directional R1 graph; none is a reader, selection,
aggregation waiver, identity alias, or test-operand provenance constructor. In particular, a selection
converted with `to_numpy()` and passed to a registered test remains outside base section 5.4's closed
operand grammar and abstains. These methods are admitted only when they occupy an R1 descriptive
position and do not reach a protected path.

## 6. Ordered predicate and identity delta

The 2.0 predicate changes in this order only:

1. Select the same module/main scope and perform the same E6 and prose-free source checks.
2. Accept any return annotation on otherwise valid `main` and ignore that annotation subtree.
3. During unchanged bounded helper expansion, apply A1's annotation exclusion and A2's narrowed
   shadowing veto; every other X4 refusal and depth/binding rule remains.
4. Build the same complete member-sensitive value graph, reader census, operand backward slices,
   p-result sink path, mutation census, and sibling census.
5. Apply A4's three new call rows only through the existing R1 read-only call branch.
6. Apply A3's source-order-free descriptive-aggregation proof.
7. Apply every unchanged R2 guard to the full expanded program, then the unchanged candidate and Finding
   eligibility path.

The check version, adapter version, grammar version, and separate experimental detector version advance
to `2.1.0`. A new detector module inherits the 2.0 detector and changes only its versioned identity and
own-byte implementation digest. The 2.0 detector file and its versioned manifest record remain unchanged
and content-addressed. No 2.1 qualification or production pin is installed.

## 7. Development check: 38 opened cases and Batch K

“Candidate” means an evaluation candidate only. Every row still produces zero Findings because no 2.1
qualification or production pin exists. First reasons follow the unchanged ordered predicate after A1–A4.

### 7.1 Burned Envelope 1

| Role / case | 2.1 expectation | First reason or complete path |
| --- | --- | --- |
| P1 `45dcad2f6496a0fd5778` | Candidate | Complete authorized reader → two group-row selections → registered test → p-result sink path. |
| P2 `88e59abe85a8eea2b8cd` | Candidate | Complete path. |
| P3 `0f721a41bac71a461dd2` | Candidate | Complete path. |
| N1 `5994e65153b07855b07c` | Abstain | `aggregation-on-test-operand-path`. |
| N2 `e804a86a1e05b781f292` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `11af5bb3f9b7e8e0b293` | Abstain | `tracked-value-mutation`. |

### 7.2 Burned Envelope 2

| Role / case | 2.1 expectation | First reason or complete path |
| --- | --- | --- |
| P1 `e8f97fe750189052f726` | Candidate | Complete path. |
| P2 `2df3396d80adbb63dffb` | Candidate | Complete path. |
| P3 `ca18f96d45dff1b921ad` | Candidate | Complete path. |
| N1 `15b07ef7670800ba88e0` | Abstain | `two-group-row-selection-unavailable`. |
| N2 `5ef43dbf631adcf3daec` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `e60c84d0cda3cc465df7` | Abstain | `tracked-value-mutation`. |
| N4 `6090fc1b1b6dbfcd6eee` | Abstain | `additional-accepted-reader-present`. |
| N5 `d4d95cdd4f4e698d675c` | Abstain | `unregistered-component-consumer`. |

### 7.3 Burned Envelope 3

| Role / case | 2.1 expectation | First reason or complete path |
| --- | --- | --- |
| P1 `a28f42e4bd1fe1c5e048` | Candidate | Complete path. |
| P2 `29893ac47ebe4ca60cce` | Candidate | Complete path. |
| P3 `df67e751158d62c4cbf4` | Candidate | Complete path. |
| P4 `045708a55a9f3e2ec449` | Candidate | Complete path. |
| P5 `2d47b05c996177f2afd7` | Candidate | Complete path. |
| P6 `d92b542e0bb28fa3c950` | **Candidate (gained by A3)** | Pre-test weekly/ration aggregations reach print-only sinks and never a test-argument slice; the raw group selections still reach `ttest_ind`. |
| N1 `0b9b803536c12e3870eb` | Abstain | After A1 removes the annotation wall, `helper-closure-or-nested-definition-unsupported` is first; the later per-volunteer aggregation remains unavailable as an operand path. |
| N2 `5b80f0787b1b6c47048b` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `245226f0f9f97f6acda2` | Abstain | `tracked-value-mutation`. |
| N4 `f4e4d89ac44385a18261` | Abstain | `additional-accepted-reader-present`. |
| N5 `19824e3f6b1e3980872f` | Abstain | `unregistered-component-consumer`. |
| N6 `3c650ec217b884e5f35e` | Abstain | `aggregation-on-test-operand-path`. |

### 7.4 Burned Envelope 4

| Role / case | 2.1 expectation | First reason or complete path |
| --- | --- | --- |
| P1 `5c26014c176bf905c121` | Candidate | Complete path. |
| P2 `5bdfa31a22a40d58e20c` | Abstain | `unregistered-component-consumer` remains on the unresolved tracked helper path. |
| P3 `4f622f87ad3c8a93a2d8` | Abstain | A4 admits `reindex`, then the next closed-grammar wall is `admission-call-off-list`. |
| P4 `c07cc7c1a1f9730a3c9f` | **Candidate (gained by A1)** | Annotated reader helper expands; complete raw group-selection/test/p-result path. |
| P5 `34b1ade6d028cfda2a75` | Abstain | `two-group-row-selection-unavailable`. |
| P6 `675de846f46beae7d442` | Candidate | Complete path. |
| N1 `540f7dfdf1614ceda57d` | Abstain | After A1/A2 expansion, `multiple-rowwise-test-candidates`; the unit-level aggregation remains visible. |
| N2 `9cd65ce93b9b8f846eb8` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `23cc44d49100a68655c5` | Abstain | `two-group-row-selection-unavailable`; the dependence-aware sibling remains visible. |
| N4 `c69bb7590d57d2057ee0` | Abstain | `additional-accepted-reader-present`. |
| N5 `0e06da6bdb3963daae4e` | Abstain | `helper-closure-or-nested-definition-unsupported`; mixed-model and cluster-bootstrap guards are not waived. |
| N6 `e303f93351acf5df0457` | Abstain | `aggregation-on-test-operand-path`. |

Expected opened total: **15/38 candidates**, comprising 15/18 positives and **0/20 negatives**. The
only changes from 2.0 are the two named gains above.

### 7.5 Batch K

| Case | 2.1 expectation | First reason |
| --- | --- | --- |
| `0de3a6061d3bb4056306` | Abstain | `analysis-source-envelope-unavailable`. |
| `6b2da0c7167dbba3738f` | Abstain | `analysis-source-envelope-unavailable`. |
| `e9e2718573bb47f7d17b` | Abstain | `analysis-source-envelope-unavailable`. |
| `3ae92d0bb421d6eee99e` | Abstain | `analysis-source-envelope-unavailable`. |

Expected K total: **0/4 candidates**, zero Findings, replay equality.

## 8. Test-plan delta

1. A1 positive probes: arbitrary parameter and return annotations on eligible helpers; arbitrary return
   annotation on zero-argument `main`; annotation names/calls absent from the runtime graph and free-name
   scan.
2. A1 adversarial probes: annotated helper whose expanded body aggregates on the operand path; annotated
   helper with pos-only, kw-only, variadic, nonconstant-default, type-comment, decorator, or closure
   shape retains the existing refusal.
3. A2 probes: parameter spelling equal to a module string constant, numeric literal constant, and tuple
   constant expands with fresh names; import/path/builtin and tracked-frame shadow controls abstain.
4. A3 probes: pre-test output-only `groupby().agg` is admitted; pre-test aggregation assigned through an
   alias/member into a test operand abstains `aggregation-on-test-operand-path`; post-test behavior is
   unchanged.
5. A4 positive/negative arity probes for every admitted method form and every refused extra argument,
   keyword, dynamic selector, nested call, or inplace form.
6. A4 adversarial probe: `to_numpy()` on either registered-test operand does not satisfy operand
   provenance and cannot create a candidate.
7. Extend the no-prose tripwire and byte-identical prose-mutation matrix across annotation exclusion,
   helper expansion, `_post_test_descriptive_aggregation`, and the three A4 call rows.
8. Run all 38 opened scripts and four K cases through normal `sc-referee audit`, asserting the exact
   section-7 outcomes, zero Findings, and replay equality.
9. Run all 108 existing blind and 155 regression cases with zero Findings from this adapter, the full
   default gate, Ruff check and format check, mypy, and `scripts/validate_starter.py`.
10. Assert detector 2.0.0 bytes and digest are unchanged and its versioned manifest record remains; add
    and pin the 2.1.0 detector record without installing a qualification or production pin.

## 9. File-by-file build delta

Files omitted here do not change for 2.1.

| File | Responsibility |
| --- | --- |
| `src/sc_referee/scientific_checks/code_csv_dependence_dataflow.py` | Implement A1–A4 only. |
| `src/sc_referee/scientific_checks/code_csv_dependence_adapter.py` | Advance check/adapter/grammar identity to 2.1.0. |
| `src/sc_referee/scientific_checks/profiles.py` | Register the 2.1.0 live code lane and exact coverage limits. |
| `src/sc_referee/scientific_checks/integration.py` | Bind the 2.1.0 code-lane observation surface. |
| `src/sc_referee/scientific_requirement_contract.py` | Permit frozen 2.0.0 authority migration to active 2.1.0; profile remains 1.1.0. |
| `src/sc_referee/detectors/bounded_code_csv_dependence_conflict_v2_1.py` | Add the separate 2.1.0 detector identity; 2.0.0 file untouched. |
| `src/sc_referee/detectors/method_conflict_registry.py` | Register the 2.1.0 detector. |
| `scripts/build_capability_source_manifests.py` and generated capability/scientific resources | Add versioned 2.1.0 records while retaining 1.0.0–2.0.0. |
| `evaluation/development/pseudorep-code-slice-v2_1/DEVELOPMENT_LEDGER.json` | Record all 38 opened and four K expectations with no qualification credit. |
| `tests/test_code_csv_dependence_dataflow.py` | A1–A4 unit/adversarial matrix. |
| `tests/test_code_csv_dependence_adapter.py` | Identity and tripwire assertions. |
| `tests/test_dependence_code_slice_development.py` | Normal-path 38+4 expectations and replay. |
| Existing identity, integration, registry, regression, and manifest tests | Advance only the live 2.1 projection and preserve historical-byte assertions. |
| `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md` | Record the accepted executive-authority 2.1 amendment. |
| Generated maturity/public-interface/growth-loop and regression ledgers | Record the exact live identity and mechanically refreshed source digests only. |

## 10. Deferred 2.2 surface

The following are decisions deferred to a separately reviewed 2.2 delta and are not builder options in
2.1:

1. helper expansion at loop-body call sites;
2. helper expansion at loop-iterable call sites;
3. loop-target label resolution in selection masks; and
4. dict-container reconstruction beyond the existing member graph.

Unsupported occurrences retain their current abstention or coverage-limit outcomes.

## 11. Observed and inferred

**Observed:** Envelope 4's frozen result and closure; exact opened ASTs; the annotation veto, constant/
tuple shadowing veto, source-order comparison, and current pandas R1 list in the 2.0 analyzer; and the
substantive guards reached by opened negatives after diagnosis.

**Inferred and requiring build verification:** A1–A4 produce exactly the two named positive gains,
15/38 opened candidates, no negative candidates, unchanged K outcomes, and no regression/blind Finding.
No open question authorizes a wider implementation; any unresolved AST form abstains.
