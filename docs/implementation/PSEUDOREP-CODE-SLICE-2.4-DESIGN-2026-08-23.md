# Pseudoreplication code slice 2.4: dual qualified/development registry binding

Status: **Accepted for build**
Decision provenance: **Fable, under executive authority granted by Alex 2026-08-21; 2026-08-23**
Companion decision: `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md`

This is a production-authority delta. It changes no 2.1 or 2.3 recognition predicate, no CSV rule,
no dataflow rule, no detector comparison, and no Finding wording. Unchanged behavior remains governed
by the accepted 2.1 through 2.3 designs and ADR-0076.

## 0. BUILD-NOTES

- Envelope 7 is observed to have produced 2/6 positive evaluation candidates, 0/6 negative
  candidates, zero Findings, and replay 12/12 under detector 2.3.0. It is burned. The accepted
  threshold was not met.
- Observed production defect: after development advanced beyond 2.1.0, the single live registry
  binding advanced with it. The installed Envelope-5 pin remained 2.1.0, so
  `installed_pin_matches_live_identity` returned false and the ordinary CLI could no longer promote
  qualified 2.1.0 results.
- This build fixes authority routing only. It does not respond to Envelope-7 recall misses.
- Ambiguity in this design resolves to the qualified lane for ordinary audits and to no promotion in
  every development-lane run.
- The runtime-qualified adapter is a versioned facade over frozen Envelope-5 sources. The facade may
  differ only in import paths needed to keep 2.1 and 2.3 installed concurrently. Its declared adapter
  identity is derived from the byte-frozen Envelope-5 adapter source and the unchanged shared adapter
  helper. Tests compare the facade with the frozen source after that closed import-path normalization
  and exercise all four Envelope-5 candidates through the ordinary CLI. No other source rewrite is
  permitted.
- Narrow interpretation recorded during the required Envelope-6/7 run: qualified authority is exact
  to a contract frozen against the qualified check identity. A contract frozen against a later
  development identity is verified but is not migrated backward into production authority. The
  adapter therefore receives no authority derivation and abstains. Forward migration from an older
  contract to the selected development identity remains permitted because that lane cannot promote.
- Both lane manifests retain the previously frozen scientific-check reducer implementation digest.
  The lane split changes registry orchestration, not either reducer's evidence semantics; rebinding
  that field to the orchestration source would silently change both existing check identities.
- The development-only 155-case regression ledger changes its active dependence-component entry from
  2.3.0 to the qualified 2.1.0 identity and re-digests its execution plan. This is an expected
  component-inventory refresh caused by making production authority explicit; no case, selector,
  expected applicability, or expected outcome changes.
- The generated capability matrix and private maturity ledger now expose two installed binding grants:
  complete-domain and the qualified code-CSV dependence lane. They do not expose the 2.3 development
  binding as qualified, and retain the non-global, per-binding capability wording.
- The retained dependence envelope runner selects `development` explicitly. This implements the R3
  protocol for all future/replayed development envelopes and preserves the executable false-accusation
  halt guard without allowing an envelope evaluation to promote.
- Scientific-check integration treats exactly code-lane versions 2.1.0 and 2.3.0 as static-file
  subjects. This is required for both concurrent adapters to produce resolvable file references; it
  does not admit another check or version.
- Authority-neutral Finding drafting recognizes an exact registered code binding in either lane so
  development candidates can be wording-tested. The controller's development no-promotion ceiling
  runs before drafting in production evaluation and remains the Finding-eligibility boundary.

## 1. Scope and normative terms

### 1.1 Qualified binding

`qualified` means the sole production-eligible dependence binding. It is exactly the installed
Envelope-5 pin surface:

- check `check:authorized-independent-unit-entry-into-row-independent-procedure` version `2.1.0`,
  manifest digest `sha256:8b9ce5f53203c99bd0d24fcf0169e841905cb2aa034e858516bcf48105e4d6c2`;
- adapter
  `adapter:authorized-independent-unit-entry-into-row-independent-procedure:code-csv-rowwise-two-sample-v1`
  version `2.1.0`, implementation digest
  `sha256:986f4862d5bc63cda2a61f5bf1d7df2d46e137b38de753edac5c2208f2705b54`,
  manifest digest `sha256:591a0bf3e7ca93b8166ad6a7a8779e937e48b5295b81ca0f433b02d28fc1c65c`,
  and grammar digest `sha256:e135a5182ebba66ffc987f8867c468c54a9a1ab72d34f76dedee9867c4c3b10e`;
- detector `detector:bounded-code-csv-dependence-conflict` version `2.1.0`, manifest digest
  `sha256:8824f6c48ac7b014383967e03774b9ef227dc265fa4754f5ce79ff1571304b05`;
- binding ID
  `method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1`
  and binding digest
  `sha256:85c270872730d6ce8cf6cc62b79a54140b2a6121d98d7be35764db6d61f5b989`;
- Finding profile
  `method-conflict-finding:code-csv-authorized-unit-requirement-conflict-v1`, digest
  `sha256:0440fdb918eb04ff975e7129c4152a2d681f3f4203ae8c7a1f8fc9ebf8916288`.

### 1.2 Development binding

`development` means the newest built dependence identity, 2.3.0 in this slice. It uses the current
2.3 check, adapter, detector, and wording-v2 identities and remains evaluation-only. Its binding ID is
the qualified binding ID plus `:development`; it is not a grant-slot key and cannot match an installed
pin.

### 1.3 Lane

A lane is the closed literal `qualified` or `development`. The ordinary default is `qualified`.
The selected lane determines the dependence module and binding placed in the semantic lock. Other
scientific checks retain their existing module and binding in both lanes.

## 2. Registry contract

`ScientificCheckRegistry` retains `modules` and `method_conflict_bindings` as the qualified production
collections. It adds:

```python
development_modules: tuple[ScientificCheckModule, ...] = ()
development_method_conflict_bindings: tuple[MethodConflictBinding, ...] = ()
```

The registry must expose deterministic `modules_for_lane(lane)` and `bindings_for_lane(lane)` methods.
The development collections are complete lane projections, not patches: exactly one module and at most
one binding per check in each lane. Check IDs and binding IDs must be unique within a lane. A check may
have one qualified binding and one development binding. Each binding is validated only against the
module in its own lane. The existing `MethodConflictBinding` record is unchanged.

`registry_digest` binds both complete lane projections under the keys `qualified` and `development`.
The release-manifest projection carries both collections explicitly. It must not overwrite the
qualified collection with the development collection.

`RegistryEvaluation` records its selected lane. `evaluate(context, lane=...)` evaluates only
`modules_for_lane(lane)`. Scientific-check compilation resolves modules from the same recorded lane.

## 3. Qualified 2.1 implementation closure

The following exact Envelope-5 source bytes are installed as immutable versioned resources:

| Component | Required SHA-256 |
|---|---|
| 2.1 adapter source | `064413da6821c59bf02a8deef4675a9e63ec8699a4146e2854c20792777de0c5` |
| 2.1 dataflow/allowlist source | `22b85efb45c41602d45f93855a327bb1d83321f653d5470f6c8946c8003e6c29` |
| shared report/CSV authority parser used by 2.1 | `e9cfe98905661238865401aba1c4eeb14a431bfae76f12094381eea7ac8516af` |
| 2.1 detector source | `9c30154639e1fc013a0f82a5ee3d767202c121f42626b2c6497436e9305f2452` |
| wording-v1 semantic profile | `sha256:0440fdb918eb04ff975e7129c4152a2d681f3f4203ae8c7a1f8fc9ebf8916288` |

The old source snapshots are auditor-owned package resources; project bytes cannot select or alter
them. The versioned 2.1 runtime facade imports only the frozen 2.1 dataflow and frozen 2.1 CSV parser.
The facade is mechanically equal to the frozen adapter source except for those two import module names
and the source path used by `adapter_implementation_digest`. The test suite must pin that exact
normalization and must fail on any additional difference.

The existing 2.1 detector source and wording-v1 constants remain byte-immutable. Current 2.3 adapter,
dataflow, detector, and wording-v2 bytes remain the development closure and are not called by the
qualified module.

## 4. Audit and CLI routing

`run_audit` adds `scientific_check_lane: Literal["qualified", "development"] = "qualified"`.
The semantic lock records:

```json
{
  "binding_lane": "qualified | development",
  "production_promotion_permitted": true | false
}
```

It locks only the selected lane's enabled modules and method-conflict bindings. It validates only the
selected lane's detector manifests. `production_promotion_permitted` is true exactly for `qualified`
and false exactly for `development`.

The ordinary `sc-referee audit` command selects `qualified`. The explicit boolean CLI option
`--development-lane` selects `development`. A development lock is an evaluation artifact: controller
promotion returns the original evaluation result without consulting a pin whenever
`production_promotion_permitted` is false. Therefore development can emit an evaluation candidate or
an abstention but never a Finding, even if a future development identity accidentally equals a
qualified identity.

The qualified lane consumes authority only from a method contract frozen against the exact qualified
check identity. It never migrates a later development contract backward. The development lane may
apply the existing closed compatibility migration from an older contract to the selected newer
development identity; its no-promotion ceiling remains mandatory.

Replay consumes the frozen lane and promotion-ceiling fields from the lock; it performs no lane
reselection.

## 5. Pin and Finding behavior

`installed_pin_matches_live_identity` and `live_adapter_identity` inspect only the qualified module and
qualified binding collections. A development binding bump cannot alter their answer.

Normal production promotion remains the existing step-10/11 mechanism. It requires the qualified
binding, its exact installed pin, the exact qualification and metric records, the exact detector
manifest, and wording-v1. Development bindings never enter this comparison.

The exact Finding title remains:

> Analysis code contradicts the frozen one-row-per-authorized-unit requirement

No report text, Markdown, comments, docstrings, string labels, or other prose is read as evidence in
either lane.

## 6. Envelope protocol amendment

Every future dependence envelope freezes the full dual registry and selects the `development` lane.
Its audit locks must record `binding_lane = development` and
`production_promotion_permitted = false`. Candidate scoring uses the development results.

A passing envelope does not mutate the qualified lane. It authorizes step 10 to derive qualification,
metric, threshold, Finding-profile, and replacement-pin artifacts. Step 11 then runs the candidate
cases through an explicitly proposed qualified projection. Only explicit installation of the
replacement pin and corresponding qualified registry projection promotes development to qualified.
That installation is the only allowed transition of the qualified binding.

## 7. Acceptance tests

### 7.1 Registry and authority

1. Both lane projections validate; duplicate IDs within either lane fail.
2. One check may occur in both lanes, but a binding drifting from its same-lane module fails.
3. The registry and packaged release manifest expose both lanes deterministically.
4. The qualified dependence binding equals the installed pin on every bound field and
   `installed_pin_matches_live_identity` is true.
5. Replacing only the development identity with a synthetic later version leaves the qualified
   registry digest projection, pin match, and production result unchanged.
6. Complete-domain remains qualified and its installed pin continues to match.

### 7.2 Frozen bytes

1. Pin all five §3 identities.
2. Assert the 2.1 facade differs from the frozen adapter source only by the closed import/path
   normalization.
3. Assert qualified observations on the four Envelope-5 candidates are replay-identical to their
   frozen 2.1 observations before promotion.
4. Assert current 2.3 sources and detector bytes are unchanged.

### 7.3 Routing and no-promotion ceiling

1. Default API and CLI lock `qualified`; explicit flag locks `development`.
2. Qualified locks include only the 2.1 dependence module/binding; development locks include only the
   2.3 dependence module/binding.
3. A development evaluation candidate remains evaluation-only and produces zero Findings even if its
   binding is synthetically made pin-equal.
4. Replay preserves the selected lane and the complete canonical result/Finding/coverage projection.

### 7.4 Required ordinary-path runs

- Envelope-5 candidates `0b4876ce`, `1975f22b`, `2448bea7`, and `a1541d5c`: exactly one Finding each
  through the normal CLI without `--development-lane`.
- Envelope-5 positive misses: zero Findings.
- Every Envelope-5 negative and every Envelope-6/7 case: zero Findings.
- Existing 108 blind cases: zero Findings.
- Existing 155 regression cases: zero Findings.
- Replay equality for all required locked cases.

Run the focused dual-registry, qualified-adapter, grant, detector, Finding, Envelope-5/6/7, and replay
suites; then the full default gate, Ruff format/check, and mypy gates required by `AGENTS.md`.

## 8. File-by-file build list

| File | Change |
|---|---|
| `src/sc_referee/scientific_checks/registry.py` | Add complete qualified/development projections, lane validation/evaluation, and digest binding. |
| `src/sc_referee/scientific_checks/profiles.py` | Build exact 2.1 qualified dependence module/binding and current 2.3 development projection; serialize both. |
| `src/sc_referee/scientific_checks/integration.py` | Compile against the evaluation's recorded lane. |
| `src/sc_referee/scientific_checks/code_csv_dependence_adapter_v2_1.py` | Add the narrow 2.1 runtime facade. |
| `src/sc_referee/scientific_checks/code_csv_dependence_dataflow_v2_1.py` | Install frozen 2.1 dataflow bytes. |
| `src/sc_referee/scientific_checks/report_csv_dependence_adapter_v2_1.py` | Install frozen 2.1 CSV authority/parser bytes. |
| `src/sc_referee/resources/frozen-code-csv-dependence-v2.1.0/` | Install exact Envelope-5 adapter/dataflow/report-adapter source snapshots and digest manifest. |
| `src/sc_referee/controller.py` | Select and lock one lane; enforce the development no-promotion ceiling. |
| `src/sc_referee/cli.py` | Add explicit `--development-lane`. |
| `src/sc_referee/detectors/method_conflict_registry.py` | Validate and dispatch the selected lane, including detector 2.1. |
| `src/sc_referee/detectors/method_conflict_grant_pins.py` | Resolve live adapter identity only from qualified modules. |
| `src/sc_referee/resources/scientific-check-manifests-v1/registry.json` | Regenerate the dual-lane release projection. |
| `tests/test_scientific_check_registry.py` | Lane validation and digest tests. |
| `tests/test_code_csv_dependence_dual_registry.py` | Frozen-byte, routing, no-promotion, four-candidate, corpus, and replay tests. |
| existing integration/grant/manifest tests | Replace stale-single-binding expectations with exact lane expectations. |
| this design and ADR-0076 | Record the accepted architecture and BUILD-NOTES. |

## 9. Open questions

None. Recall work after 2.3 is explicitly out of scope for this slice.
