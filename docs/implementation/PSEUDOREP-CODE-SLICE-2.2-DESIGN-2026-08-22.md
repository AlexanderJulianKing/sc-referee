# Pseudoreplication code slice 2.2 design — 2026-08-22

- **Status:** Accepted for build
- **Decision provenance:** Fable, under executive authority granted by Alex 2026-08-21
- **Decision date:** 2026-08-22
- **Normative base:** `docs/implementation/PSEUDOREP-CODE-SLICE-2.1-DESIGN-2026-08-22.md`
- **Governing ADR:**
  `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md`
- **Identity:** check, adapter, grammar, and separate code-lane detector `2.2.0`
- **Evidence:** frozen contract, CSV structure, Python AST/dataflow, and established API names only
- **Prose evidence:** forbidden
- **Project-authored-code execution:** forbidden

## 0. BUILD-NOTES

- Ambiguity resolves to abstention. A build observation may narrow this document but may not add an
  admitted form or weaken an R2 guard.
- The requested 44-case development set is exactly the six Envelope-1 cases, eight Envelope-2 cases,
  twelve Envelope-3 cases, twelve Envelope-4 cases, and the six positive Envelope-5 cases. The six
  Envelope-5 negatives remain mandatory safety controls but are not double-counted in 44.
- S3 refreshes six Batch-K method-contract closures against the live `2.2.0`
  check/adapter/detector registry. It changes no project, label, contract answer, authorized unit,
  selected CSV, or expected outcome. The refresh is a closure-version update, not a case edit.
- Detector `2.1.0` source bytes and every earlier versioned detector source remain immutable. A new
  `2.2.0` detector module carries the new identity.
- The existing authority-only compatibility migration admits frozen dependence requirements through
  `2.1.0` against active `2.2.0`; it compares the same candidate, value, role authority, material
  binding, and requirement candidates and does not rewrite a frozen lock.
- The regression-corpus ledger and its execution plan changed only in their active-component record
  and dependent digests, plus the content digest of
  `tests/test_dependence_recognition_scientific_adapter.py`: that retained test source now pins the
  active `2.2.0` shared-integration identity instead of the prior `2.1.0` identity. The 155 retained
  case definitions and all expected outcomes are byte-unchanged; the four direct cases still replay
  as 21 not-applicable observations and two unsupported observations per case, with zero Findings.
- The private capability-maturity ledger now records the installed `2.1.0` dependence grant as stale
  against active `2.2.0`; only complete-domain remains Finding-qualified during this unqualified
  development delta. This is an expected baseline change, not a qualification claim for `2.2.0`.
- `scripts/validate_starter.py` retains the installed Envelope-5 grant at the qualification-resource
  level but now requires its production pin to be stale and omits it from the active capability
  matrix. The complete-domain binding grant remains active at Finding strength.
- The requested full default gate includes the closed release-inventory check, so
  `MANIFEST.sha256` is regenerated from the committed-tree inventory and current proposed bytes. A
  final regeneration after the authorized local commit admits the new 2.2 paths; the commit is
  amended only with that generated manifest and the release-identity test is rerun.
- No report-lane test is restored or retired by this delta. The existing 37 enumerated report-lane
  retirements remain unchanged.
- Entrypoint diagnosis is environment-only: `.venv/lib/python3.11/site-packages/` contains the correct
  absolute `__editable__.sc_referee-0.3.0.pth` path to this checkout's `src`, but `.venv/bin/python`
  does not include that path and `.venv/bin/sc-referee --help` raises `ModuleNotFoundError`. Packaging
  metadata and the generated console script are correct, so `docs/QUICKSTART.md` records the exact
  `PYTHONPATH=src` source-checkout workaround; no environment bytes are changed.
- A conditional reconstruction that yields one raw member and one aggregate is conservatively refused
  first as `two-group-row-selection-unavailable`; 2.2 does not add branch folding merely to reach the
  later aggregation code. A helper that aggregates on every normalized binding is pinned to
  `aggregation-on-test-operand-path`. Both are abstentions, and the narrower precedence adds no
  conviction surface.

## 1. Boundary and unchanged rules

This is a delta. Every 2.1 rule not explicitly replaced below remains normative, including the frozen
`1.1.0` authority contract, byte-exact authorized CSV path, CSV multiplicity and D1', reader and test
allowlists, single-reader rule, direct operand grammar, aggregation/mutation/dependence-aware/sibling/
resampling guards, p-result sink requirement, 16-definition ceiling, no-prose tripwire, no-execution
rule, contract-conflict Finding wording, and zero-false-accusation standard.

The 2.2 delta adds no positive evidence role. It only makes three already-supported code structures
visible to the unchanged R2 predicate: eligible helper bodies at loop call sites, contract-domain loop
bindings, and exact members of one loop-built dictionary.

## 2. S1 — diagnosis of the two Envelope-5 misses

The following is **observed** by parsing the frozen `analysis.py` bytes with the 2.1 analyzer and then
tracing the first node rejected by `_v2_read_reason`. Neither blocking node is an `ast.Call`; the public
reason `admission-call-off-list` also covers unregistered attribute/subscript read shapes.

| Case | Exact blocking expression | Use downstream | Classification |
| --- | --- | --- | --- |
| `e50e676afb2cd3593234` | `data.loc[data[ARM] == label, "fasting_glucose_mmol_l"]` at `analysis.py:137` | The selected series is reduced by `.mean()` and `.std(ddof=1)` and reaches only `print` at line 138; it does not reach either `ttest_ind` operand. | **Benign structural read.** Do not add an API row. Admit only through the closed contract-domain loop rule in section 4. |
| `f1a04b5358a7b9b9d57c` | `df.loc[df[GROUP] == level, "leaf_temp_c"]` at `analysis.py:78` | The selected series is reduced by `.mean()`, `.std(ddof=1)`, `.min()`, and `.max()` and reaches only `print` at lines 79-81; it does not reach either `ttest_ind` operand. | **Benign structural read.** Do not add an API row. Admit only through section 4. |

The first case's full frozen source is at
`evaluation/development/blind-envelope-5-2026-08-22/cases/e50e676afb2cd3593234/project/analysis.py:136-138`;
the second is at
`evaluation/development/blind-envelope-5-2026-08-22/cases/f1a04b5358a7b9b9d57c/project/analysis.py:77-81`.
This diagnosis corrects the shorthand “off-list call”: the emitted code is accurate but the nodes are
subscript selections, not function calls.

## 3. S2(a) — bounded helper expansion at loop sites

### 3.1 Eligible call sites

After the unchanged X1 scope selection and before any Analyzer census, the X4 expander additionally
examines these exact sites in an `ast.For`:

1. a direct helper call used as the RHS of one `Assign` or `AnnAssign` in the loop body;
2. a direct helper call used as one expression statement in the loop body; or
3. one simple-name helper call occurring in the loop iterable, either as the complete iterable or as the
   receiver of one otherwise-admitted attribute/call chain such as `HELPER(...).iterrows()`.

The callee must be a unique module-level synchronous `FunctionDef` already selected by X4 and called by
simple `Name`. All X4 eligibility, argument binding, constant-default, annotation exclusion, recursion,
closure, decorator, global/nonlocal, free-name, return, depth-two, and one-expansion-per-call-site rules
remain byte-for-byte unchanged. A nested call in an argument, two helper calls in one iterable, a helper
call in a loop condition, or any call site not in the three rows above abstains under the existing
narrowest X4 or admission code.

### 3.2 Deterministic expansion algorithm

1. Walk the selected statement list in physical source order, recursively entering `For.body` and
   `For.orelse`; do not enter any other nested scope.
2. For a body site, invoke the existing `_inline_helper_site` once. Insert its fresh parameter/body/
   return statements at the call's position inside that body. The existing prefix is extended by the
   enclosing loop's source position so two loop sites cannot share an alpha name.
3. For an iterable site, allocate one fresh temporary. Invoke `_inline_helper_site` immediately before
   the `For`, targeting that temporary, and replace only the original helper call node in `For.iter`
   with a load of that temporary. The surrounding admitted method chain remains in the iterable.
4. Repeat the existing depth-two expansion pass over newly inserted statements. A physical call site is
   expanded once; seeing it again is `helper-call-site-reentry-unsupported`.
5. Expansion is static substitution only. The helper is never imported or executed. Its complete
   expanded body remains present for reader, test, aggregation, mutation, dependence-aware, sibling,
   resampling, unregistered-consumer, R1, and sink scans.

For the contract-domain loop normalization in section 4, each copied iteration receives a distinct
alpha prefix containing the loop line and binding ordinal. For a loop that is not normalized, the
single static loop-body call site receives one fresh prefix and remains inside the loop.

## 4. S2(b) — contract-domain loop-target resolution

### 4.1 Exact eligible loop

A loop is a `contract_domain_loop` only if all conditions hold:

1. it is synchronous `for LEVEL in ITERABLE` with `LEVEL` one `ast.Name`, no `else`, and no `break`,
   `continue`, `yield`, `await`, `global`, or `nonlocal` in its body;
2. `ITERABLE` is an `ast.Tuple` or `ast.List` whose elements are literal strings or names bound to
   closed module string constants, or one `Name` bound in `resolver.tuples` to literal strings;
3. the resolved iterable has length two, its members are distinct, and its ordered members are exactly
   the contract/CSV `group_values` in either order;
4. the loop target is not a reader name, a tracked-frame name, a test-argument backward-slice name, a
   helper name, an import name, a builtin name, or a module constant name; and
5. the body passes helper expansion under section 3 and contains no store to `LEVEL`.

A tuple containing even one value outside the two-value contract domain is not partially resolved. It
remains ordinary control flow and the dynamic mask cannot complete the operand grammar.

### 4.2 Per-binding normalization

Normalize an eligible loop into two ordered copies of its body before Analyzer traversal:

1. substitute every load of `LEVEL` in copy `i` with the exact literal string at iterable position `i`;
2. alpha-rename every ordinary `Name` stored by the body, and every corresponding load in that copy,
   with a prefix containing loop line and binding ordinal;
3. do not rename an import, module constant, helper name, builtin, reader defined outside the loop, or
   the base name of the special reconstruction store in section 5;
4. preserve original source spans on copied evidence nodes and attach a deterministic binding ordinal
   only to synthetic names; and
5. pass each copy through section 3 helper expansion, then splice both copies in iterable order.

After substitution,
`FRAME.loc[FRAME[GROUP_COLUMN] == LEVEL, VALUE_COLUMN]` is evaluated by the unchanged base pandas
selection predicate as the corresponding literal contract group selection. It supplies no evidence
unless it later occupies a registered test operand and all R2 checks pass. A loop target used only for
printing is R1 descriptive; a target or copied value flowing into an operand is governed by R2.

## 5. S2(c) — bounded dictionary reconstruction

### 5.1 Exact construction

One dictionary is reconstructable only in this shape:

```python
SUMMARY = {}
for LEVEL in GROUP_VALUES:
    VALUE = FRAME.loc[FRAME[GROUP_COLUMN] == LEVEL, VALUE_COLUMN]
    SUMMARY[LEVEL] = VALUE
LEFT = SUMMARY[GROUP_VALUE_1]
RIGHT = SUMMARY[GROUP_VALUE_2]
```

The loop must be a section-4 `contract_domain_loop`. `SUMMARY` must be assigned one empty literal dict
exactly once before the loop, may not alias another name, and may have exactly one marked subscript store
per normalized binding. Each normalized key is the literal binding for that copy. The two keys must be
distinct and together equal the exact contract group domain. The RHS may be a tracked selection,
identity, aggregation, unknown derived value, or literal; its complete `_Value` labels and call origins
are retained. The only permitted later reads are literal `SUMMARY[GROUP_VALUE_1]` and
`SUMMARY[GROUP_VALUE_2]` plus R1-descriptive output reads. Dynamic keys, `.get`, update methods,
deletion, reassignment, duplicate keys, a third member, escape through a call, iteration of the whole
dict, or any other store abstains.

### 5.2 Member graph

The empty literal creates a `reconstruction_container` with no members. Each marked normalized store
adds exactly one literal-key member edge. It is construction, not a tracked-frame mutation, only because
section 4 proved the closed two-binding loop and the base name/key/RHS shape above. Every other subscript
store retains `tracked-value-mutation` or the existing unsupported code.

Literal downstream reads follow only the selected member edge. Reading/passing the whole dict follows
the union of both edges. An aggregate, mutation, test result, unknown call, or different root in either
member therefore remains visible to R2 and can never be laundered by the container.

## 6. False-accusation analysis

The following are mandatory adversarial controls:

| Scenario | Required outcome | Why conviction is blocked |
| --- | --- | --- |
| A helper expanded inside a loop aggregates per iteration and its result reaches a test argument. | Abstain `aggregation-on-test-operand-path`. | Section 3 exposes the complete helper body before R2; expansion never labels it descriptive merely because the call was in a loop. |
| A loop iterable includes a label outside the exact contract/CSV two-group domain. | Abstain; normally `two-group-row-selection-unavailable` or the earlier exact structural code. | Section 4 requires exact set equality and performs no per-member partial resolution. |
| A reconstructed dict contains one raw selection and one aggregate, and both members feed the test. | Abstain `aggregation-on-test-operand-path`. | Section 5 retains the aggregate label on that member and the test sees the member-specific edge. |
| A helper in a loop body calls `MixedLM`, another registered test, or an unregistered component consumer. | Abstain under the unchanged dependence-aware, multiple/sibling, or consumer guard. | Helper expansion precedes every sibling and suppressor scan. |
| A loop target aliases a tracked name and flows into a test. | Abstain `loop-target-aliases-tracked`. | Section 4.1(4) and unchanged 2.0 loop directionality both refuse it. |
| A dict key is dynamic, duplicated, missing one group, or includes a third member. | Abstain. | Section 5 requires a closed complete two-member construction; there is no fallback union that can complete an operand. |

The Finding remains a contract-versus-code record. It does not claim statistical invalidity, execution,
intent, or that the contract author is scientifically correct.

## 7. Ordered predicate delta and codes

The 2.1 predicate changes only in this order:

1. Select the unchanged module/main scope and resolve imports/constants.
2. Normalize only section-4 contract-domain loops, including fresh per-binding names.
3. Expand helpers at top-level and section-3 loop sites under unchanged X4 conditions.
4. Build section-5 reconstruction members while preserving every member label.
5. Build the same complete member-sensitive graph and run every unchanged R2 census/guard.
6. Apply R1 only after protected paths and all component/sibling relationships are known.
7. Require the unchanged p-result sink, CSV/domain checks, admission pin, and Finding profile.

No new outward abstention code is required. Existing exact codes describe every refusal. Predicate-step
precedence from 2.0 section 6.1 dominates source position.

## 8. Development check — 44 requested opened cases

“Candidate” below means the code-lane observation reaches the detector. Because 2.1 is installed, a
candidate would be a Finding only under the installed 2.1 identity; during 2.2 development the 2.1 pin
is stale against the 2.2 live identity and no 2.2 candidate is Finding-eligible before qualification.

### 8.1 Envelope 1 (3/6)

| Role / case | 2.2 outcome | First reason or path |
| --- | --- | --- |
| P1 `45dcad2f6496a0fd5778` | Candidate | Complete path. |
| P2 `88e59abe85a8eea2b8cd` | Candidate | Complete path. |
| P3 `0f721a41bac71a461dd2` | Candidate | Complete path. |
| N1 `5994e65153b07855b07c` | Abstain | `aggregation-on-test-operand-path`. |
| N2 `e804a86a1e05b781f292` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `11af5bb3f9b7e8e0b293` | Abstain | `tracked-value-mutation`. |

### 8.2 Envelope 2 (3/8)

| Role / case | 2.2 outcome | First reason or path |
| --- | --- | --- |
| P1 `e8f97fe750189052f726` | Candidate | Complete path. |
| P2 `2df3396d80adbb63dffb` | Candidate | Complete path. |
| P3 `ca18f96d45dff1b921ad` | Candidate | Complete path. |
| N1 `15b07ef7670800ba88e0` | Abstain | `two-group-row-selection-unavailable`. |
| N2 `5ef43dbf631adcf3daec` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `e60c84d0cda3cc465df7` | Abstain | `tracked-value-mutation`. |
| N4 `6090fc1b1b6dbfcd6eee` | Abstain | `additional-accepted-reader-present`. |
| N5 `d4d95cdd4f4e698d675c` | Abstain | `unregistered-component-consumer`. |

### 8.3 Envelope 3 (6/12)

| Role / case | 2.2 outcome | First reason or path |
| --- | --- | --- |
| P1 `a28f42e4bd1fe1c5e048` | Candidate | Complete path. |
| P2 `29893ac47ebe4ca60cce` | Candidate | Complete path. |
| P3 `df67e751158d62c4cbf4` | Candidate | Complete path. |
| P4 `045708a55a9f3e2ec449` | Candidate | Complete path. |
| P5 `2d47b05c996177f2afd7` | Candidate | Complete path. |
| P6 `d92b542e0bb28fa3c950` | Candidate | Complete path. |
| N1 `0b9b803536c12e3870eb` | Abstain | `helper-closure-or-nested-definition-unsupported`. |
| N2 `5b80f0787b1b6c47048b` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `245226f0f9f97f6acda2` | Abstain | `tracked-value-mutation`. |
| N4 `f4e4d89ac44385a18261` | Abstain | `helper-closure-or-nested-definition-unsupported`; S2(a) reaches the helper refusal before the unchanged additional-reader guard. |
| N5 `19824e3f6b1e3980872f` | Abstain | `unregistered-component-consumer`. |
| N6 `3c650ec217b884e5f35e` | Abstain | `aggregation-on-test-operand-path`. |

### 8.4 Envelope 4 (3/12 expected)

| Role / case | 2.2 outcome | First reason or path |
| --- | --- | --- |
| P1 `5c26014c176bf905c121` | Candidate | Complete path. |
| P2 `5bdfa31a22a40d58e20c` | Abstain | `admission-call-off-list`; S2(a) expands `describe_arm` and `means_by_timepoint`, then exposes the unchanged unsupported two-column return projection `table[[ARM_LIGHT, ARM_DEEP]]`. |
| P3 `4f622f87ad3c8a93a2d8` | Abstain | `admission-call-off-list`; named `GroupBy.agg(...)` output lineage through the separate summary helper is outside S2. |
| P4 `c07cc7c1a1f9730a3c9f` | Candidate | Complete path. |
| P5 `34b1ade6d028cfda2a75` | Abstain | `two-group-row-selection-unavailable`; `treatments = sorted(df["rabbit_exclusion"].unique())` is data-derived, not a literal/closed module tuple, so S2(b/c) does not apply. |
| P6 `675de846f46beae7d442` | Candidate | Complete path. |
| N1 `540f7dfdf1614ceda57d` | Abstain | `multiple-rowwise-test-candidates`. |
| N2 `9cd65ce93b9b8f846eb8` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `23cc44d49100a68655c5` | Abstain | `two-group-row-selection-unavailable`. |
| N4 `c69bb7590d57d2057ee0` | Abstain | `additional-accepted-reader-present`. |
| N5 `0e06da6bdb3963daae4e` | Abstain | `helper-closure-or-nested-definition-unsupported`. |
| N6 `e303f93351acf5df0457` | Abstain | `aggregation-on-test-operand-path`. |

### 8.5 Envelope 5 positives (6/6 expected)

| Role / case | 2.2 outcome | First reason or path |
| --- | --- | --- |
| P1 `0b4876ceca6b0a9aede7` | Candidate | Complete path. |
| P2 `e50e676afb2cd3593234` | **Candidate gained by S2(b)** | Breakfast-arm loop's background selection becomes a literal-group print-only read. |
| P3 `1975f22bc0022b19331f` | Candidate | Complete path. |
| P4 `2448bea72701b75fce2a` | Candidate | Complete path. |
| P5 `a1541d5c671f3d6d58ce` | Candidate | Complete path. |
| P6 `f1a04b5358a7b9b9d57c` | **Candidate gained by S2(b)** | Canopy-treatment loop's temperature selection becomes a literal-group print-only read. |

Expected requested total: **21/44 candidates**, comprising **21/24 positives and 0/20 negatives**.
The remaining positive misses are `5bdfa31a22a40d58e20c`, `4f622f87ad3c8a93a2d8`, and
`34b1ade6d028cfda2a75`.

### 8.6 Additional Envelope-5 negative controls

| Role / case | 2.2 outcome | First reason |
| --- | --- | --- |
| N1 `0d274a0eccdb84966940` | Abstain | `aggregation-on-test-operand-path`. |
| N2 `4afe430c936bbe560a5e` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `4d64fa6416ee8406f678` | Abstain | `tracked-value-mutation`. |
| N4 `4e24fb76c83774381e41` | Abstain | `additional-accepted-reader-present`. |
| N5 `be94cec09f73d4a3036a` | Abstain | `unregistered-component-consumer`. |
| N6 `094fcb05ef85e4f7f406` | Abstain | `aggregation-on-test-operand-path`. |

Expected safety total: **0/6 candidates**.

## 9. Batch-K refreshed method contracts

Refresh the method-contract closures for all six planted Batch-K positives at live check `2.2.0`:

| Case | Procedure family | Expected scored outcome after refresh | First reason |
| --- | --- | --- | --- |
| `0de3a6061d3bb4056306` | `ttest_ind` | Abstain | `analysis-source-envelope-unavailable`. |
| `6b2da0c7167dbba3738f` | `ttest_ind` | Abstain | `analysis-source-envelope-unavailable`. |
| `e9e2718573bb47f7d17b` | `ttest_ind` | Abstain | `analysis-source-envelope-unavailable`. |
| `3ae92d0bb421d6eee99e` | `ttest_ind` | Abstain | `analysis-source-envelope-unavailable`. |
| `2c458d2b523ea8c1bd90` | binomial control | Abstain | `authorized-group-domain-not-exactly-two`. |
| `556f3545bebb45a3b005` | binomial control | Abstain | `authorized-group-domain-not-exactly-two`. |

The four t-test projects have only `workflow/analysis.py`, never root `analysis.py`; S2 does not alter
the filename admission gate. The two binomial controls stop earlier because the authorized contrast
column is not an exact two-value domain. The refreshed method contracts make these outcomes scored under
the live check instead of refusing them for registry drift.

## 10. Test-plan delta

1. S1 probes pin both exact Envelope-5 expressions and prove both become candidates only when the loop
   iterable equals the contract group domain.
2. S2(a) positives: a helper call as direct loop-body assignment, loop-body expression, complete loop
   iterable, and receiver of `.iterrows()`; nested depth-two helper; distinct fresh names for two
   contract bindings.
3. S2(a) refusals: duplicate/nonunique helper, method callee, nested argument call, two iterable helper
   calls, recursion, closure, decorator, global/nonlocal, dynamic default, depth three, call-site reentry,
   unresolved free name, and unsupported return.
4. S2(b) positives: literal tuple in both orders and a closed module tuple, with each mask resolved to
   its own literal group.
5. S2(b) refusals: non-domain label, duplicate label, one/three labels, list/tuple with a dynamic item,
   loop `else`, target reassignment, tracked-name target, and a loop target that flows into a test under
   an unsupported mask.
6. S2(c) positive: exact empty-dict/two-member reconstruction feeding the two raw test operands.
7. S2(c) adversarial: helper aggregation per iteration; mixed raw/aggregate members; dynamic, duplicate,
   missing, or extra key; `.get`; whole-dict escape; alias; update/delete/reassignment; selection from a
   second reader; test-result member; and unregistered consumer.
8. Normal CLI path and replay for all 44 requested cases, six Envelope-5 negative controls, and six
   refreshed K method-contract closures. Expected totals are sections 8 and 9.
9. Zero Findings across the 108 blind corpus and 155 regression corpus; old findings are not silently
   emitted under a stale 2.1 production pin while 2.2 is unqualified.
10. Prose tripwire instruments adapter inspection, helper/loop normalization, per-binding substitution,
    reconstruction member propagation, backward/forward slices, and admission. Comments, docstrings,
    string literals, printed labels, and report presence/content mutations yield byte-identical
    observations.
11. Replay compares the complete canonical projection; Ruff check/format, mypy, starter validation,
    false-accusation halt, detector-manifest immutability, default gate, and every existing code-lane
    adversarial suite must pass.

## 11. Envelope 6 protocol

Envelope 6 is not created by this build. After 2.2 is reviewed and explicitly frozen:

1. freeze the complete 2.2 implementation closure and threshold policy before prompt bytes are visible;
2. use a new independent prompt-author session with a newly frozen briefing; the author receives no
   detector grammar, prior case bytes, prior prose, diagnosis, or outputs;
3. assign twelve opaque IDs in fixed role order P1-P6,N1-N6, seal the role map, and freeze prompt/case
   bytes before either maintainer reads them;
4. retain the same six negative shapes as Envelope 5, including a helper-defined pseudobulk returning
   the aggregate; author at least one positive using a helper in a loop and one using a loop-built dict,
   without disclosing detector syntax;
5. run the normal reportless CLI and model-free replay from the frozen bytes; and
6. pass only with at least 3/6 positive evaluation candidates, exactly 0/6 negative candidates, zero
   Findings across 108 blind + 155 regression + all 12 envelope cases, and replay equality 12/12.

Recall is reported as measured. There is no retry and no qualification credit from any opened/burned
case.

## 12. File-by-file build list

| File or family | Change | Rough delta |
| --- | --- | ---: |
| `docs/implementation/PSEUDOREP-CODE-SLICE-2.2-DESIGN-2026-08-22.md` | This accepted delta and BUILD-NOTES. | +420 |
| `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md` | Append 2.2 code-lane eligibility amendment and provenance. | +20 |
| `src/sc_referee/scientific_checks/code_csv_dependence_dataflow.py` | Closed loop-site expansion, contract-domain normalization, and reconstruction members. | +220/-20 |
| `src/sc_referee/scientific_checks/code_csv_dependence_adapter.py` | Advance check/adapter/grammar identity to 2.2.0; no evidence-role change. | +2/-2 |
| `src/sc_referee/detectors/bounded_code_csv_dependence_conflict_v2_2.py` | New versioned detector identity inheriting frozen 2.1 behavior surface. | +20 |
| `src/sc_referee/detectors/method_conflict_registry.py`, `src/sc_referee/scientific_checks/profiles.py`, `src/sc_referee/scientific_checks/integration.py` | Register and route 2.2.0. | +8/-8 |
| `src/sc_referee/scientific_requirement_contract.py` | Extend the authority-only compatibility migration through frozen 2.1.0 to active 2.2.0. | +3/-3 |
| capability/scientific manifest resources and source-manifest records | Deterministically regenerate 2.2 digests while retaining 1.0-2.1 detector records. | mechanical |
| `evaluation/development/pseudorep-code-slice-v2_2/DEVELOPMENT_LEDGER.json` | Canonical 44-case, six-negative, and six-K expectations. | +1 canonical JSON line |
| `evaluation/development/pseudorep-code-slice-v2_2/k-method-contracts/` | Six live-2.2 Batch-K method-contract closures; normal-path audit/replay outputs stay test-local. No case bytes or answers change. | generated |
| `tests/test_code_csv_dependence_dataflow.py` and focused 2.2 test module | Positive and adversarial S2 matrix. | +500 |
| `tests/test_dependence_code_slice_development.py` and manifest/registry tests | 44-case/K normal path, replay, tripwire, and 2.2 identity. | +180/-40 |
| `docs/QUICKSTART.md` | Document `PYTHONPATH=src` because the `.venv` failure is environment-only. | +4 |

## 13. Entry-point decision rule

Run `.venv/bin/sc-referee --help` and a read-only version command without `PYTHONPATH`. If the installed
entry point resolves a stale/non-repository package because repository packaging metadata or generated
entry-point configuration is wrong, fix that repo-side cause and test it. If `uv`'s editable `.pth` is
present but this local interpreter does not honor it, do not mutate or vendor the environment; add the
exact `PYTHONPATH=src .venv/bin/sc-referee ...` workaround to `QUICKSTART.md` and record the observed
environment evidence in BUILD-NOTES.

## 14. Open build-changing questions

None. The named `GroupBy.agg` apple case remains outside scope, 44 has the exact composition stated in
section 0, Envelope 6 is not created, and no 2.2 production pin is installed by this build.
