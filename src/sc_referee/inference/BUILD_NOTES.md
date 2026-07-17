# Inference engine build notes — Increments 0–9

Date: 2026-07-10

## Status

- Increment 0: fully landed.
- Increment 1: fully landed for the requested breadth-first slice.
- Increment 2: fully landed for the requested may-analysis and legacy-projection slice.
- Increment 3: fully landed for the conservative artifact/config slice.
- Increment 4: fully landed for the supported abstract-domain/fixpoint slice.
- Increment 5: fully landed for the typed dependence/read-coverage slice.
- Increment 6: fully landed for the closed-solver, whole-DAG must-slicer slice described below.
- Increment 7: fully landed for refinement inference over supported abstract facts and exact summaries.
- Increment 8: fully landed as a dormant, isolated policy/proof layer; no policy is routed.
- Increment 9: live only as an advisory double-dipping witness. Every engine result is capped at
  `needs_evidence`; unsupported programs delegate to the shipped detector under the same cap.
  Confounding and experimental-unit remain authoritative, and the other policy integrations
  are dormant/abstaining.
- `groupby_provenance`, `bind_sinks`, `evaluate_confounding`, and the shipped experimental-unit
  recompute remain authoritative. The `double_dipping` registry ID is now an inference router whose
  fallback is the unchanged shipped `DoubleDippingCheck`.

## Increment 0 — frozen compatibility oracles

- Recorded the untouched collection count: **586 tests**, including parametrized cases.
- Added a frozen corpus containing:
  - 56 source-input cases covering every current provenance/sink-use test family plus the
    committed `fixtures/ambiguous_group/analysis.py` input.
  - 22 confounding cases covering blocker, needs-evidence, major, informational, and pass
    branches plus the committed `fixtures/confounding_alias` input.
- Serialized complete public object trees, including dataclass type/fields, AST expressions
  with source attributes, contracts, ports, `ValueType`, callsite IDs, spans, diagnostics,
  verdicts, metrics, citations, tuples/sets, and non-finite floats.
- The frozen outputs are `tests/frozen_oracles/legacy_oracles.json`. Normal tests only read it;
  regeneration requires explicitly running `tests.frozen_oracles.generate`.

## Increment 1 — IR and coverage barriers

- Added the §1 package/module skeleton under `sc_referee.inference`.
- The Python frontend delegates normalization and parsing to `source_ast.parse_sources` and
  preserves its `ParsedSource` objects and full-span callsite IDs. It does not import or execute
  analyzed code.
- Added deterministic source-span-derived IDs, evaluation-order lowering, normal and exceptional
  CFG edges, value SSA, merge phi nodes, field-sensitive memory SSA, and IR validation.
- Parse failures, unsupported syntax, dynamic execution, reflection, and unsupported languages
  are explicit barriers with stable IDs and spans.
- Source/frontend coverage is tracked separately from call effects, artifacts, and claim
  inventory. Overall coverage remains incomplete in these increments even for barrier-free code.

## Increment 2 — may effects, havoc, and exact projections

- Added the may/must bilattice invariant and join/refinement operations.
- Added may-points-to abstract values and a literal-field-sensitive heap with singleton/exact
  strong updates, weak updates for dynamic or multi-target writes, and may/must reaching
  definitions.
- Opaque calls may read/write all reachable mutable arguments, clear affected must definitions,
  return all reachable argument origins plus an explicit unknown origin, record unknown egress,
  and make call-effect coverage incomplete.
- Added an exact summary registry keyed by module, symbol, version, package/source digest, and
  summary digest. Any mismatch resolves to `unresolved` and therefore havoc/abstention.
- Added independent `project_legacy_marker_tests` and `project_legacy_sink_uses` projections.
  They consume the snapshot's already-parsed sources and do not call either legacy public
  implementation. A monkeypatch test enforces that separation.
- Both projections are byte-exact against every frozen source case. Internal conservatism is
  discarded only at this compatibility projection seam.

## TDD and verification commands

Baseline collection:

```sh
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest --collect-only -q
```

Red-first/green focused cycles:

```sh
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_frozen_oracles.py -q
PYTHONPATH=src:. UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run python -m tests.frozen_oracles.generate
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_ir_and_barriers.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_effects_and_projections.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference tests/test_source_ast.py tests/test_provenance.py tests/test_sink_use.py tests/test_sink_registry.py tests/test_confounding.py tests/test_confounding_graded.py tests/test_confounding_specificity.py -q
```

Each production slice was preceded by its focused failing test: missing oracle fixture; missing
inference package; missing heap/havoc/projections; missing R/reflection barriers; missing root
projection exports; and prematurely complete global coverage.

Final full suite (Increment 0–2 checkpoint):

```sh
export PYTHONPATH=/tmp/sc-referee-test-bootstrap:src:.
export UV_CACHE_DIR=/tmp/sc-referee-uv-cache
export MPLCONFIGDIR=/tmp/sc-referee-mpl
uv run pytest
```

Result: **603 passed, 4 warnings in 54.17s**. The warnings are the existing duplicate AnnData
feature-name and implicit string-index conversion warnings.

The first untouched full-suite attempt reached 570 passes but the managed macOS sandbox denied
`os.sysconf("SC_SEM_NSEMS_MAX")` inside joblib/loky, producing 10 failures and 6 fixture errors in
pydeseq2 tests. The final command prepended a `/tmp`-only `sitecustomize.py` which converts that one
denied sysconf lookup to `ValueError`, the unsupported-query result joblib already handles. No repo
or shipped implementation was changed for this environment workaround; a focused pydeseq2 test and
the full suite then passed.

## Abstentions and deliberate boundaries

- R is an explicit whole-source `unsupported_language` barrier. A regex/best-effort R subset was
  not claimed as complete without a real parser.
- Async code, classes, lambdas, yields, unsupported compound statements, dynamic execution, and
  reflection are barriers. Dynamic field access is weak/unknown, never silently exact.
- No built-in function summary is registered without exact version and digest evidence. Such calls
  are opaque and havoc reachable mutable state.
- Artifact flow, complete claim inventory, rich dependence/slicing, refinement inference,
  discharge providers, and policy execution are skeleton seams for later increments. Their coverage
  facets remain false and cannot support a clean or violation judgment.
- The frozen confounding implementation is only an Increment-0 oracle here. It was not rerouted or
  reimplemented; its graded legacy branches remain production-active as required.
- No source, config, artifact, notebook, or user analysis was executed by the inference engine.

---

## Increment 3 — artifact and config semantics

- Added identity-bearing `ArtifactId`, exact serializer/deserializer contracts, artifact versions,
  workflow ordering, and conservative reaching-writer resolution.
- A must artifact producer is returned only when all of these are exact: literal or manifest path,
  full artifact identity, serializer/deserializer identity, format, one writer version, field map,
  schema digest, content digest, replacing write mode, and absence of any path-colliding later writer,
  append, or possible in-place mutation.
- Every incomplete case returns possible writers plus `UnknownArtifactProducer` and named obligations.
- Added pinned config reads. Dynamic paths, globs, absent schema paths, and missing pinned values return
  `UnknownConfig`; they never become exact config dependencies.
- Red-first artifact fixtures cover overwrite, append, possible mutation, same-path/same-field collisions
  across unrelated artifact identities, dynamic path/glob, missing field, serializer mismatch, and schema
  or content digest mismatch.

## Increment 4 — domains, fixpoint, widening, and narrowing

- Extended `MayMust` with the CFG precision order, evidence meet, widening, and invariant checks.
- Implemented the closed set-expression grammar: `Empty`, `All`, `Exact`, `FieldEquals`, `Union`,
  `Intersection`, `Difference`, `Image`, `Preimage`, and `Unknown`.
- Implemented lower/upper `SetBounds`, row/patient/time/feature `Region`, exact finite overlap proofs,
  explicit dynamic/widening boundaries, and patient projection only through exact or ratified mappings.
- Added identity-bearing units and only the five specified relation kinds. Unit relations enter must only
  from artifact relations, exact constructions, or ratified facts; name-based relations remain unknown.
- Added calibration, selection, fitted-state, scalar, effect, and reduced-value facets. `Naive` requires a
  complete exact summary binding. A method name alone never creates a must selection event.
- Added a worklist solver, delayed widening, one explicit exact-guard narrowing pass, scalar/region/
  points-to widening, and loop-must handling. A loop-body fact is must only with proved execution and
  preservation. Every widened facet is marked for the slicer.

Property-style coverage exhaustively enumerates the small `MayMust` universe and checks:

- join idempotence, commutativity, and associativity;
- consistent evidence-meet idempotence, commutativity, and associativity;
- transfer monotonicity under the CFG precision order;
- lower-bound/upper-bound reduction consistency;
- reduced-value/effect `must ⊆ may` consistency;
- widening termination and may-top movement;
- exact-guard narrowing; and
- loop must-fact preservation rules.

## Increment 5 — complete dependence program

- Added `Derivation` as an OR of guarded `Alternative`s and the closed `DepExpr` forms `Atom`,
  `Unknown`, `AllOf`, and `ChoiceOf`.
- Added the exact edge-class set: `VALUE`, `CONTROL`, `ALIAS`, `MUTATION`, `FIELD`, `FITTED_STATE`,
  `ARTIFACT`, `SERIALIZE`, `CONFIG`, and `FORMAT`.
- Edge evidence separately records exact field, singleton must-alias, overwrite exclusion, artifact,
  serializer, config, format, fitted-state, widening, havoc, and local-certificate premises.
- `DependenceProgram.validate()` fails when a declared abstract read has neither requirements nor an
  explicit `Unknown` boundary. `analyze()` builds this read inventory from its existing parsed AST; it
  does not reparse or execute source.

## Increment 6 — claim inventory and backward must slicer

- Added structured claim manifests, exact report/value bindings, accusation-grade roots, clean-only
  roots from complete egress enumeration, and diagnostic roots for incomplete inventory.
- `analyze()` inventories structured claims and computes internal claim slices but still returns only
  `ABSTAIN`. No slice is connected to a judgment, status, policy, or certificate.
- Added the closed, non-extensible sensitivity-solver set exactly as specified:
  - `affine_linear_q.v1`
  - `sign_monotone.v1`
  - `exact_set_membership.v1`
  - `unit_partition.v1`
  - `exact_rational_rank.v1`
- The solver set has no registration API. Unsupported arithmetic, floating/approximate rank inputs,
  unknown signs or predicates, and unproved unit relations return UNKNOWN.

Whole-sub-DAG canonicalization happens in `claims/slice.py`:

1. `complete_subdag()` first collects the complete relevant reconvergent graph and every feasible
   internal reaching-definition alternative.
2. `_Canonicalizer` recursively expands that graph, universally retaining all pinned-feasible choices.
3. Only then does `apply_transform()` in `claims/sensitivity.py` canonicalize in one closed algebra.
4. `prove_must_consumption()` requires every root and internal feasible alternative's canonical form to
   be sensitive to the candidate producer. One REFUTED or UNKNOWN form prevents must consumption.

A local edge/transform certificate is therefore never used directly as an end-to-end witness.

### Mandatory adversarial fixtures

| Fixture | Result |
|---|---|
| Reconvergent `x + (-x)` | may-only; whole affine form has zero coefficient |
| Sequential `-(-x)` | unavoidable |
| Multiply by possibly-zero quantity | may-only / UNKNOWN |
| Select record then remove it with exact mask | may-only / REFUTED non-membership |
| Combine mask with unknown predicate | may-only / UNKNOWN |
| Sensitive branch plus feasible bypass | may-only |
| Alternative reaching definitions, only some producer-derived | may-only |
| Alternative reaching definitions, every one from same producer | unavoidable |
| Any widened facet | may-only / UNKNOWN |
| Weak alias | may-only / UNKNOWN |
| Possible intervening overwrite | may-only / UNKNOWN |
| Non-closed nonlinear/opaque transform | may-only / UNKNOWN |
| Definite single-path exact-field affine flow | unavoidable |

Additional abstention fixtures cover incomplete `AllOf` consumption, uncertified edges, havoc,
ambiguous fields, unresolved artifact writer/serializer/config/format/fitted state, unresolved or
unpinned guards, mixed solver algebras, unmodeled constraints, resource exhaustion, and inexact claim
roots. UNKNOWN composition adds a boundary and makes slice coverage incomplete; exact cancellation is
REFUTED without inventing another producer.

## Increment 3–6 TDD and verification

Red-first focused commands:

```sh
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_artifact_and_config_semantics.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_domains_and_fixpoint.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_dependence_program.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_claim_inventory_and_solvers.py tests/inference/test_must_slicer_adversarial.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference -q
```

Frozen projection and legacy gate:

```sh
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_frozen_oracles.py tests/inference/test_effects_and_projections.py tests/test_source_ast.py tests/test_provenance.py tests/test_sink_use.py tests/test_sink_registry.py tests/test_confounding.py tests/test_confounding_graded.py tests/test_confounding_specificity.py -q
```

Final collection and full suite:

```sh
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest --collect-only -q
export PYTHONPATH=/tmp/sc-referee-test-bootstrap:src:.
export UV_CACHE_DIR=/tmp/sc-referee-uv-cache
export MPLCONFIGDIR=/tmp/sc-referee-mpl
uv run pytest
```

Final result: **657 passed, 4 warnings in 51.66s**. The 4 warnings are the same pre-existing AnnData
duplicate-name and implicit string-index warnings. The `/tmp` bootstrap is the sandbox-only joblib
`SC_SEM_NSEMS_MAX` compatibility shim documented in the Increment 0–2 checkpoint; it does not modify
the repository or analysis behavior.

## Increment 3–6 abstentions and deviations

- Artifact/config resolvers are explicit engine APIs and dependence edge evidence; automatic recovery
  of a whole external workflow DAG from arbitrary source is not claimed. Any edge without exact
  resolver evidence is may-only.
- Workflow ordering currently consumes explicit integer DAG order supplied by the manifest adapter.
  Branch/append/path ambiguity is retained as possible-only rather than guessed.
- Symbolic region overlap is proved only for the exact finite subset currently implemented. Other
  symbolic predicates remain unknown; this loses proofs but cannot create one.
- The narrowing callback is admissible only for an exact guard supplied by the frontend/manifest TCB.
  Unsupported loop semantics remain widened and may-only.
- No verified cross-algebra bridges exist in this increment. Every mixed-solver proof abstains.
- Nested `AllOf` groupings that would require such a bridge abstain.
- Alternative constraints are not interpreted this run. Any non-empty constraint set forces may-only,
  preventing a nonzero affine coefficient from being asserted over an accidentally constant feasible
  domain.
- Exact rational rank accepts only finite integer/Fraction matrices. Floating, approximate, ragged, or
  unsupported matrices return UNKNOWN.
- Claim inventory accepts structured manifest/egress facts but does not infer claim roots lexically.
  Dynamic formatting or incomplete enumeration stays diagnostic/incomplete.
- The generic AST dependence adapter records every read or an unknown boundary, but it does not infer
  accusation-grade must edges from syntax. Must edges are admitted only through explicitly certified
  dependence formulas and the closed whole-DAG solvers.
- R and the unsupported Python constructs from Increments 1–2 remain barriers.
- The Increment 8 policy, provider, purity, evaluator, and certificate layers described below are
  dormant. Legacy public functions and confounding remain authoritative and byte-exact projection
  tests still pass.

---

## Increment 7 — refinement/effect-type inference

- Added rich immutable `GroupingType`, `TestType`, `PValueType`, and `ReportClaimType` facets plus a
  rich `RefinementIndex`.
- Grouping refinements consume the actual `AbsValue` supplied for a grouping/design port: origin,
  selection events, row/patient/time/feature `Region` bounds, and unit. Missing facets remain explicit
  may-unknown/must-empty values.
- A `TestType` is created only from a complete exact `SummaryBinding`; candidate symbol or method names
  are deliberately ignored. A method name alone cannot create a statistic, null, sampling regime, or
  dependence model.
- `PValueType` calibration comes only from that exact test summary or an exactly bound verified
  safeguard. “No safeguard found” remains `UnknownCalibration`; `Naive` requires an exact summary.
- Exact structured egress roots are paired with the Increment 6 claim slice to populate
  `ReportClaimType`. Inexact roots retain possible producers but lose all unavoidable producers.
- `ValueType` remains the compatibility projection from a rich grouping refinement.
- `analyze()` now populates exact report-claim refinements from its claim inventory and slicer. It does
  not guess grouping/test ports where no exact call summary identifies one, and still returns only
  `ABSTAIN`.

The name-never-fills invariant is directly tested by giving the same abstract value misleading names
(`leiden`, `predefined_design`, `genotype`, and candidate test names) and requiring identical or unknown
results. No syntax/name lookup participates in any refinement transfer.

## Increment 8 — computation-free policies and total evaluation

- Added frozen declarative `FactRef`, `RelationPremise`, `ProviderInvocation`, `ProofRule`,
  `ValidityPolicy`, and `Judgment` schemas. Nested selector/input mappings are read-only; recursive
  validation rejects callable data and canonicalizes declarations to immutable JSON-compatible data.
- Policy premises bind their arguments and claim/producer selectors exactly. An unbound fact or an
  argument-free relation with a coincidentally matching name cannot discharge an argumentful premise.
- `evaluate()` is total across provider failures and implements the required order:
  - simultaneous clean and violation proofs -> `ABSTAIN(INCONSISTENT_EVIDENCE)`;
  - an explicit proved violation rule -> `VIOLATION_WITNESS`;
  - clean only with complete inventory, every possible producer covered, no unknown producer, all
    policy coverage present, and a clean rule for every possible producer;
  - otherwise `ABSTAIN`.
- Refuted/unknown clean evidence is never inverted into an accusation. Provider errors lose the proof
  and abstain.

### Exact discharge-provider registry

The exact registry resolves `(id, version, implementation_digest)` and returns `UNKNOWN` for missing
bindings, unsupported relations, approximate/untyped inputs, or computation boundaries. Each provider
identity binds the complete provider module source digest plus explicit input- and output-schema
digests; requests and typed outputs are separately digest-bound for deterministic replay.

| Provider | One verified computation |
|---|---|
| `exact_rational_rank.v1` | Reuses the closed Increment 6 exact rational Gaussian-elimination/rank solver to prove target estimability or aliasing. |
| `confounding_metrics_q.v1` | Exact rational partial-R2, VIF, and per-term OVB multipliers; comparisons use policy-pinned `1/100` and `10`. |
| `ora_joint_correction.v1` | Exact hypergeometric tail plus joint supported multiplicity recomputation. |
| `sign_parity.v1` | Canonical product of every ratified reversal compared with the applied joint multiplier. |
| `finite_set_relations.v1` | Exact membership, subset/equality, intersection/disjointness, and cardinality. |
| `interval_bounds.v1` | Exact lower/upper legality under a named consumer contract and endpoint inclusivity. |
| `unit_partition.v1` | Exact ratified partition identity/refinement/accounting relation. |

The rank provider reuses the closed sensitivity primitive rather than duplicating it. Exact rationals
accept integers, `Fraction`, and declarative `(numerator, denominator)` literals; floats return
`UNKNOWN`.

### Build-failing policy-purity lint

Policy declarations live only under `policy/definitions/`. The AST lint permits imports from the policy
schema and immutable engine ID/fact/enum modules, literal constants, and assignments constructing the
five schema objects. It rejects every other import; functions/classes/lambdas; comprehensions;
loops/conditionals; arithmetic/comparisons; and arbitrary calls. Runtime schema validation additionally
rejects callables and requires every provider identity/version/digest to resolve exactly.

`test_purity_lint_demonstrably_rejects_an_impure_fixture_outside_definitions` passes an out-of-directory
sample containing `numpy`, a function, and a list comprehension and asserts the lint failure. A second
sample proves arithmetic, comparison, and `open()` also fail. No impure sample is present in the
definitions directory.

### Dormant declarative policies and specificity fixtures

All definitions have isolated synthetic CLEAN / VIOLATION / ABSTAIN tests. None is imported by
`analyze()`, the shipped audit, or the CLI.

| Policy | Clean fixture | Violation fixture | Required abstention/specificity fixture |
|---|---|---|---|
| `double_dipping.v1` | independently reused selection | exact naive, overlapping, dependent selection reuse must-producing the claim | data-derived grouping name/fact alone |
| `pseudoreplication.v1` | same/accounted replication unit | exact IID-row strict-refinement mismatch with ratified assignment facts | refinement relation alone; a modeled cell-level design is not accused |
| `confounding.v2` | R3 informational near-collinearity and R4 estimable/pass | R1 exact alias/blocker; R2 exact omitted partial-R2 at least `1/100`/major | setup alone; R1/R2/R3/R4 computed premises are exact-provider-bound |
| `allele_harmonization.v1` | joint Wald parity conformant | exact joint signed-sink parity inconsistent and materially consumed | a per-source mismatch alone |
| `enrichment_universe.v1` | complete, internally consistent universe | exact jointly corrected ORA cells prove the reported discovery was made more significant | inflated `K` alone |
| `coordinate_consumption.v1` | coordinate legal for the exact consumer contract, including a legal past-end sentinel | exact consumer interval proves unavoidable/material illegal consumption | bare `v > L`/contig-length comparison |
| `spatial_iid.v1` | section/donor dependence modeled | exact report-bound IID row/assignment-unit mismatch | powered pseudobulk collapse alone |
| `trajectory_circularity.v1` | trajectory structure proved external | exact naive overlapping dependent reuse | same-object evidence alone; violation remains capped `needs_evidence` |

The four necessary-but-not-sufficient math corrections are encoded structurally: GWAS/allele evidence
must use the joint `sign_parity.v1` product; enrichment must use joint `ora_joint_correction.v1` rather
than an inflated-K direction shortcut; reference coordinates must use `interval_bounds.v1` with an
exact consumer contract; and spatial evidence must prove the IID-unit mismatch rather than infer it
from powered collapse. Trajectory is separately and deliberately `needs_evidence`-capped.

### Certificates and replay

- Added immutable certificate/root-binding/grade data, canonical JSON serialization, a certificate
  content digest, and strict schema loading.
- Loading always replays external status. `blocker` requires a blocker-capped violation witness,
  accusation-grade structured root, non-empty root digest, root ratification included among ratified
  external facts, digest-equal report artifact/locator/producing value, all external facts ratified,
  complete closed-world bindings, and complete inventory.
- A blocker-entitled witness with an absent, clean-only, unratified, or changed root becomes
  `needs_evidence`; incomplete inventory becomes `not_audited`. Major/informational policy caps remain
  distinct from blocker entitlement.
- Tests replay an unchanged blocker certificate, replay a newly serialized changed-report certificate
  to `needs_evidence`, and reject payload mutation or unknown schema fields.

## Increment 7–8 TDD and verification

Every production slice began with a focused red test: missing refinement types/inference; empty report
refinements; missing policy schema/evaluator; missing providers; finite-set member failure; missing purity
module/definitions; impure-policy acceptance; missing certificate gate; non-total provider exception;
unbound relation arguments; stale analyzer identity; provider/schema digest mismatch; relation-dependent
input digest; and unpinned confounding thresholds.

Focused commands included:

```sh
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_refinement_inference.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_policy_evaluate.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_discharge_providers.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_policy_purity_and_definitions.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_policy_provider_integration.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_certificate_gate.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference -q
```

Frozen projection and legacy-authority gate:

```sh
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_frozen_oracles.py tests/inference/test_effects_and_projections.py tests/test_source_ast.py tests/test_provenance.py tests/test_sink_use.py tests/test_sink_registry.py tests/test_confounding.py tests/test_confounding_graded.py tests/test_confounding_specificity.py -q
```

This gate passed **101 tests**. The Increment 7–8 work brings `tests/inference` to **138 tests**.

Final commands:

```sh
export PYTHONPATH=/tmp/sc-referee-test-bootstrap:src:.
export UV_CACHE_DIR=/tmp/sc-referee-uv-cache
export MPLCONFIGDIR=/tmp/sc-referee-mpl
uv run pytest --collect-only -q
uv run pytest
```

Final result: **724 passed, 4 warnings in 55.58s**. The 4 warnings are the same pre-existing AnnData
duplicate-name and implicit string-index warnings. The `/tmp` bootstrap is the sandbox-only joblib
`SC_SEM_NSEMS_MAX` compatibility shim documented in the Increment 0–2 checkpoint; it does not modify
the repository or analysis behavior.

## Increment 7–8 abstentions and deviations

- No policy is registered or routed. `analyze()`, shipped checks, audit, CLI, legacy provenance/sink
  binding, and confounding behavior are unchanged; Increment 9 remains the first permitted wiring step.
- Automatic refinement of a grouping/test/p-value requires an exact port/call summary. Where the
  current summary registry has none, the snapshot leaves those maps empty rather than name-filling.
  Exact structured report roots are the only refinement automatically populated by `analyze()` here.
- Provider support is intentionally closed and typed. Approximate matrices, floating rational inputs,
  unsupported ORA tests/corrections, unknown sign parity, dynamic/open sets, missing consumer interval
  contracts, and unratified unit relations return `UNKNOWN`.
- Confounding is exact rational within the supported design subset. It does not claim floating-tolerance
  equivalence or route its result to the production NumPy check; legacy remains authoritative.
- ORA currently supports exact hypergeometric tails with the declared supported multiplicity
  recomputation only. Alternative tests, mappings, or incomplete family inventories abstain.
- Coordinate legality supports exact linear endpoint contracts. Circular topology, unresolved contig
  aliases, and dynamic conventions abstain.
- Human ratifications and observed digests are immutable certificate inputs in this increment; there is
  no live trust service, persistence store, renderer, or policy-to-certificate wiring.
- Declarative policy unit tests use synthetic `PolicySnapshot`s. The conversion from a live analysis
  snapshot into each policy's relation/fact vocabulary is intentionally not built or guessed in this
  dormant increment.
- No source, config, artifact, notebook, or user analysis is executed. All engine analysis remains
  parse-only.

---

## Increment 9 blocked checkpoint — historical, non-authoritative

The content in this historical subsection records the implementation that the false-positive review
blocked. It is not a description of current behavior. In particular, its folder-contract evidence,
verdict table, and test counts were removed by the remediation documented in the authoritative
section below.

### What is live

- All eight policy definitions have registered `EnginePolicyVerifier`s:
  `double_dipping.v1`, `confounding.v2`, `pseudoreplication.v1`,
  `allele_harmonization.v1`, `enrichment_universe.v1`,
  `coordinate_consumption.v1`, `spatial_iid.v1`, and
  `trajectory_circularity.v1`.
- The audit discovers an optional static `sc-referee.inference.json`, validates exact source and
  report digests, constructs an `AnalysisRequest`, runs parse-only `analyze()`, slices the exact
  structured claim root, evaluates the declarative policy with the exact provider registry, replays
  the certificate gate, and maps the result to a shipped `Finding`.
- The analyzer identity is now `sc-referee.inference.increment-9.live.v1`.
- A small closed live dependence subset certifies only straight-line identity assignments such as
  `reported = source`. Calls, branches, mutation, non-identity expressions, and opaque behavior add
  unknown boundaries and cannot support an adverse entitlement.
- Policy summary identities are code-owned and bind the analyzer digest plus the canonical policy JSON.
  A merely well-formed but unregistered/lookalike summary identity loses blocker entitlement.

### Live adverse-entitlement conjunction

A live `blocker` requires every one of the following:

1. a `VIOLATION_WITNESS` from the declarative policy and exact provider identities;
2. a code-owned exact policy-summary binding;
3. an accusation-grade structured claim root;
4. root ratification included in the human-ratified fact set;
5. the shipped design/manifest confirmation gate;
6. exact source digests and the actual on-disk report digest;
7. digest-equal report locator and producing-value binding;
8. an exact artifact path/format/schema/content/writer/serializer contract, unique writer, exact field
   correspondence, and no later mutation;
9. complete source/frontend/call/artifact/claim coverage;
10. a coverage-complete claim slice with at least one unavoidable producer and no unknown boundary;
11. closed-world producer coverage and all external facts ratified.

Removing any single gate is parameterized across all eight policies. Every case becomes
`needs_evidence` or `not_audited`, never `blocker`. The same full gate is required before a live
confounding `major`; a partial contract cannot introduce a new major on a previously green analysis.
Trajectory remains capped at `needs_evidence`, even when its internal policy produces a violation
witness.

### Overlapping policies: migration deliberately deferred

The required replacement equivalence is not yet established, so none of the three shipped checks was
replaced:

| Engine policy | Authoritative shipped check | Why replacement is deferred |
|---|---|---|
| `double_dipping.v1` | `checks/double_dipping.py` | Existing reports include descriptive and unverified-safeguard branches not yet rendered byte-exact by the policy layer; existing analyses also lack accusation-grade report roots. |
| `confounding.v2` | `checks/confounding.py` | Exact rational provider status branches are covered, but the shipped floating metrics, precedence, prose/verdict structure, and existing root entitlement are not byte-exact. Replacing it would incorrectly downgrade existing confirmed blockers or alter metrics. |
| `pseudoreplication.v1` | `checks/experimental_unit.py` | The policy proves a structural IID-unit mismatch, while the shipped public verdict is earned by a report-bound pseudobulk recompute. They are not observationally equivalent. |

Their engine verifiers are live only when an explicit exact contract names them. With no such contract,
the original classes remain the only findings for their analysis types. The differential tests assert
that `build_checks()` contains the original `DoubleDippingCheck`, `ConfoundingCheck`, and
`ExperimentalUnitCheck` under their shipped IDs and never duplicates those IDs.

The 22 frozen confounding findings remain byte-exact, including complete object serialization,
metrics, precedence, and verdict text. The frozen provenance/sink projections and all existing
double-dipping/experimental-unit fixtures remain unchanged.

### pbmc_dex guardrail

The requested pbmc_dex xfail was already retired on the authoritative Increment 0–8 baseline: no
`pytest.mark.xfail` remained, and the GMM/custom-clustering -> `obs` column -> marker-test cases were
already green and returned `needs_evidence`. Increment 9 therefore has no honest `silent ->
needs_evidence` flip to claim. `tests/frozen_oracles/live_audit_oracles.json` freezes the current
`needs_evidence -> needs_evidence` result and the full suite preserves the anti-crack guardrail. No
liver-fibrosis verdict changes.

### Enumerated public audit changes

These are the complete accepted differences from the 724-test Increment 8 baseline. They are frozen in
`tests/frozen_oracles/live_audit_oracles.json` and checked by running the same folder once with engine
verifiers removed and once with them registered.

| Fixture | Old public result | New public result | Reason |
|---|---|---|---|
| Existing confirmed eQTL fixture without joint contract | historical blocked behavior | removed | Bare eQTL no longer routes the joint policy; the shipped pass is preserved. |
| Existing trajectory fixture without contract | `coverage=not_audited` | `inference.trajectory_circularity=not_audited` | Replace generic coverage text with the exact policy abstention. |
| Existing differential-abundance fixture without contract | `coverage=not_audited` | `inference.enrichment_universe=not_audited` | Replace generic coverage text with the exact joint-ORA policy abstention. |
| Existing `other` fixture without contract | `coverage=not_audited` | `inference.coordinate_consumption=not_audited` | Replace generic coverage text with the consumer-contract policy abstention. |
| Synthetic self-ratified coordinate fixture | historical false blocker | removed; `not_audited` | Folder-provided scientific facts and authority are inadmissible. |

Spatial IID is additive only after an explicit spatial live contract declares its applicability; no
column/method name can route a generic condition contrast into it. Thus existing condition-contrast
audits have no new finding or verdict change.

### New-capability conservatism and specificity

- Allele harmonization: a per-source mismatch alone abstains; only exact joint `sign_parity.v1`
  inconsistency plus material must-consumption can witness a violation.
- Enrichment universe: inflated `K` alone abstains; only joint exact ORA-cell/multiplicity recomputation
  can witness a violation.
- Coordinate consumption: bare `v > L` abstains; a legal past-end sentinel under its exact consumer
  contract is never accused.
- Spatial IID: powered pseudobulk collapse alone abstains; the exact IID-unit mismatch and ratified
  assignment facts are all required.
- Trajectory circularity: same-object evidence alone abstains; the policy stays
  `needs_evidence`-capped even under the full synthetic conjunction.

Each policy has a positive full-conjunction fixture and every gate is removed independently. Source
mutation, non-human ratification, possible later artifact mutation, opaque calls, clean-only roots,
missing summaries, lookalike summaries, incomplete coverage, and digest changes all lose adverse
entitlement.

### Shipped seam files touched

Exactly two non-`inference/**` source files were changed:

- `src/sc_referee/audit.py`: one local import/call attaches the optional static live contract to the
  already-ingested bundle before normal `_safe_run` routing. Existing validation order,
  `max_status` clamp, exception degradation, and `FAIL_ON_DEFAULT` behavior are unchanged.
- `src/sc_referee/registry.py`: `build_checks()` appends the eight engine verifiers and `checks_for()`
  uses that live list. The compatibility `CHECKS` inventory remains legacy-only so existing citation,
  audit-dimension, and proof-report contracts are not silently redefined during partial migration.

No shipped check implementation, citation map, status semantics, CLI, config loader, schema, or public
legacy provenance/sink function was changed.

### Increment 9 TDD and verification

Production changes followed focused red tests for: missing live module/verifiers; absent identity
dependence; incomplete artifact coverage; missing audit contract discovery; non-human/source-changed
contract downgrade; stale analyzer identity; registry additions; frozen migration fixture absence;
unconfirmed-design blocker leakage; possible later artifact mutation; missing/lookalike summary
bindings; and a partial-contract confounding major.

Focused commands:

```sh
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_live_dependence.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_live_policy_gate.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_live_audit_seam.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_live_differential_gate.py -q
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference -q
```

Frozen/differential gate:

```sh
UV_CACHE_DIR=/tmp/sc-referee-uv-cache uv run pytest tests/inference/test_frozen_oracles.py tests/inference/test_effects_and_projections.py tests/inference/test_live_differential_gate.py tests/test_source_ast.py tests/test_provenance.py tests/test_sink_use.py tests/test_sink_registry.py tests/test_confounding.py tests/test_confounding_graded.py tests/test_confounding_specificity.py tests/test_double_dipping.py tests/test_experimental_unit.py -q
```

This gate passed **127 tests** before the final full-suite run.

Final verification:

```sh
export PYTHONPATH=/tmp/sc-referee-test-bootstrap:src:.
export UV_CACHE_DIR=/tmp/sc-referee-uv-cache
export MPLCONFIGDIR=/tmp/sc-referee-mpl
uv run pytest --collect-only -q
uv run pytest
```

The historical checkpoint count is intentionally omitted because its positive self-ratification tests
encoded behavior that is now forbidden. Current verification counts appear below.

### Increment 9 abstentions and deviations

- No overlapping shipped check was replaced. This is the principal deliberate partial migration and
  is required by the no-regression rail until complete public outputs are exact.
- Live automatic must-certification is intentionally limited to straight-line identity flow. It does
  not certify calls (including GMM/custom clustering), branches, loops, mutation, artifacts inferred
  from paths alone, or nonlinear transforms. Those cases remain may-only/unknown unless a future
  reviewed exact summary extends the TCB.
- Historical note: folder contracts were once allowed to supply relations and facts. That channel is
  now deleted; contracts are inert routing/proposal metadata and cannot affect an adverse proof.
- Spatial applicability is not inferred from names. Without an explicit spatial contract the spatial
  verifier does not apply, because treating every cell-level condition contrast as spatial would be a
  false routing assertion.
- The optional live JSON contract is parsed statically and strictly enough to fail closed; malformed,
  source-mismatched, report-mismatched, or unsupported-version contracts attach no evidence and yield
  an abstention where the policy is otherwise known to apply.
- No analyzed source, notebook, artifact code, or config expression is executed.

---

## Increment 9 — current authoritative live state

This is the authoritative real-facts implementation after both false-positive reviews. Folder
contracts cannot provide proved relations, accusation-grade roots, ratification IDs, observed
digests, or live adverse evidence.

### Advisory-only safety decision

A sound static `double_dipping` blocker is not achievable in the supported subset: program dataflow
cannot decide every scientific premise required for a never-false-accuse verdict (for example,
whether an installed split is statistically independent or whether preprocessing couples nominally
held-out features). Pattern-specific precision fixes only separate some colliding abstract states.

The honest live ceiling is therefore `needs_evidence`:

- the declarative violation rule has `max_external_status="needs_evidence"`;
- `EnginePolicyVerifier.max_status` is `needs_evidence` for double dipping;
- direct verifier results are defensively capped before return; and
- the audit spine independently clamps any forced adverse result to the verifier entitlement.

Consequently the inference engine cannot emit `blocker` or `major` for double dipping. Combined with
the seven non-adverse engine policies, the engine live surface is structurally limited to
`needs_evidence`/`not_audited`; adverse statuses come only from unchanged shipped checks. A future
round may re-earn blocking through witness-specific ratification: engine proposes exact, digest-bound
circularity propositions; a human explicitly ratifies those propositions; certificate replay then
decides entitlement. General `design.confirmed_by_human` is not sufficient for that future blocker.

### Safety core: folder trust removed

`sc-referee.inference.json` now deserializes only:

- policy/routing identity and source-digest route narrowing; and
- inert `proposed_facts` intended for future non-accusatory design facts.

It cannot deserialize or represent, in `LivePolicyContract`, any scientific relation status,
`claim_root_grade`, accusation authority, ratification IDs, external-ratification completeness,
observed/bound report or producing-value digests, artifact exactness, assumptions, provider facts, or
summary proof. Legacy keys are ignored rather than grandfathered. The 51-case adversarial matrix in
`test_live_trust_boundary_redteam.py` freezes this boundary across all eight policies and the six
previous authority vectors.

The verifier independently measures the bound report bytes and absolute report locator, obtains the
data/report paths from ingest provenance, and computes the sliced producing-value digest from the
source dependence path. `design.confirmed_by_human` ratifies the real marker-design fact; no folder
string can ratify a violation.

### Flagship double-dipping premise paths

`inference/double_dipping.py` uses `source_ast.parse_sources`, `source_env`, `resolve_callee`, and the
shared stable callsite IDs. It never imports or executes analyzed code. For the supported pbmc_dex
path, the six policy premises come from:

| Premise | Exact engine computation |
|---|---|
| `ClaimMustProducedByTest` | An exact `rank_genes_groups` result with matching result key and group selector is extracted through `scanpy.get.rank_genes_groups_df`, remains mutation-free, and is serialized once by exact `DataFrame.to_csv` to the verifier-discovered literal report path. The resulting report root is sliced through `claims.slice.slice_claim`; the test producer must be unavoidable. |
| `GroupingMustProducedBySelection` | A strong reaching definition from exact `GaussianMixture`/`KMeans.fit_predict` or exact Scanpy graph selection flows through one receiver-qualified literal `obs[(object_id, field)]` write; a second whole-DAG slice must make the selection producer unavoidable for that same receiver. |
| `TestDefinitelyNaive` | `domains.calibration.infer_calibration` receives `handling="naive"` only when the exact Scanpy sink has literal method `t-test`, `t-test_overestim_var`, or `wilcoxon`. `logreg`, a missing method, a dynamic method, or an unrecognized method is Unknown. Absence of a safeguard never supplies Naive. |
| `RelevantRegionOverlapDefinite` | The exact claim-feature lower bounds intersect on the same artifact receiver and a compatible data partition. Literal disjoint features refute overlap; distinct layers, receivers, external regions, or dynamic partitions are unknown. For `use_raw=True`, reported feature IDs are compared against the selection set because `.raw` may strictly contain the current subset. |
| `SelectionReuseDependentUnderNull` | The exact selection and marker summaries jointly establish shared-expression reuse under the marker null, only after the same-object and definite-overlap proof. |
| `PinnedReachable` | The exact marker call is an unconditional module-level statement in the parsed CFG subset. Branch/loop/nested calls do not earn this premise. |

Whole-sub-DAG canonicalization remains in `claims/slice.py`; the live adapter consumes its
`unavoidable_producers`, never a local occurrence or edge certificate.

The positive path additionally requires a literal `scanpy.read_h5ad` path equal to the
verifier-discovered data artifact. A variable named `adata` supplies no type or artifact facet.
Strong overwrites kill constructor, selection-label, marker-result, obs-field, embedding, and report
facts. Monkey-patched summaries, possible report overwrites, dynamic CSV paths, multiple marker tests,
or multiple writers abstain.

### Trusted double-dipping summaries

The code-owned summary registry binds exact canonical module/symbol identity, reviewed version range,
summary-source digest, and semantic-summary digest for:

- `scanpy.read_h5ad`;
- `sklearn.mixture.GaussianMixture.fit_predict`;
- `sklearn.cluster.KMeans.fit_predict`;
- `scanpy.pp.neighbors`;
- `scanpy.tl.leiden` and `scanpy.tl.louvain`;
- `scanpy.tl.rank_genes_groups`;
- `scanpy.get.rank_genes_groups_df`; and
- `pandas.core.generic.DataFrame.to_csv`.

`leiden`/`louvain` require an exact preceding expression-neighbor summary; a method name or externally
written adjacency graph is unknown. `fit_predict` requires the exact imported constructor identity
and rejects monkey-patching. No custom clustering name creates a must selection event.

### pbmc_dex result and specificity

The frozen real-code fixture is:

`read_h5ad` -> `GaussianMixture.fit_predict(X_pca)` -> `obs['gmm']` ->
`rank_genes_groups(groupby='gmm', method='wilcoxon')` -> matching-key
`rank_genes_groups_df` -> mutation-free literal measured report egress.

It produces a computed `VIOLATION_WITNESS`. An unconfirmed bundle/design maps to
`needs_evidence`, and a confirmed audit remains `needs_evidence`. The finding preserves proved
relations, claim/grouping slices, exact summary bindings, and selection/test producer IDs, but its
message states that the engine-computed structure needs human review and is not an adverse verdict.

Specificity/adversarial fixtures never accuse:

- opaque count-split/held-out flow: abstain;
- exact disjoint feature sets: abstain/refuted overlap;
- clustering on `obsm['spatial']`: abstain;
- data-independent metadata relabel: abstain;
- selection-aware/tradeSeq-style call outside the exact registry: abstain;
- conditional selection versus predefined grouping: abstain;
- missing report egress, competing report writer, or dynamic writer: abstain;
- overwritten selector/labels/marker result/`X_pca`: abstain;
- bare `adata` name without exact artifact read: abstain; and
- monkey-patched `fit_predict` or Leiden without an exact expression-neighbor producer: abstain.

### Second specificity review: five false-positive paths closed

1. **Count-split / held-out data.** `FeatureRegion` now carries a data-partition identity. Selection
   from one literal layer and testing from another do not collapse to one `all` region. Until an exact
   split summary proves independence, both overlap and dependence remain Unknown; they never become
   Proved. The fixture clusters `selection_split` and tests `heldout_split`.
2. **Scanpy method calibration.** The marker summary no longer declares Naive unconditionally. Only
   literal `t-test`, `t-test_overestim_var`, and `wilcoxon` enter the exact naive subset. `logreg`,
   absent/dynamic/unrecognized methods, empty/all-NaN p-value columns, or reports without exact
   `feature_id` values abstain. Merely naming a column `pvals` is insufficient.
3. **HVG selection versus `.raw` claims.** The tested region is reduced to the exact reported feature
   IDs, while `use_raw=True` preserves the raw partition's possible superset relationship. The
   fixture selects on `HVG_ONLY` and reports disjoint raw genes; overlap and reuse are Refuted.
4. **Result-key/group and mutation binding.** `_MarkerTest`, `_MarkerResultValue`, and `_ReportEgress`
   retain exact `key_added`/`key`, tested/extracted groups, method, and mutation-free value version.
   Key or group mismatch, direct/nested/aliased DataFrame writes, alias-risk calls, or possible mutation before
   egress removes the claim link. The producing-value digest includes receiver, grouping, method,
   result key, group selector, report features, and egress callsite.
5. **Receiver-qualified grouping memory.** `obs` facts are keyed by `(object_id, field)`, and grouping
   slice roots include both. `adata_A.obs['g']` cannot satisfy a test on `adata_B` merely because the
   field strings match.

These are abstention refinements, not new adverse verdicts. The exact pbmc_dex GMM and Leiden fixtures
still prove all six premises. Analyzer identity is
`sc-referee.inference.increment-9.live.advisory-v4`, and scientific summary identities remain
to `double-dipping-summary-v2`.

### Known open precision paths, made safe by the cap

This round deliberately does not attempt further evidence fixes for four still-imprecise patterns:

- held-out/count-split data installed in `.X` and `.raw` rather than literal layers;
- HVG/PCA selection followed by claims on disjoint raw genes whose PCA lineage is unavailable;
- in-place or opaque replacement of selected labels with predefined metadata; and
- same-spelled locals in different source files entering the shared evidence state.

Each has an empirical fixture that may still compute an over-strong witness, but every finding is
`needs_evidence`, never `major` or `blocker`. Precision belongs to the future witness-ratification
build; the severity cap makes these collisions non-accusatory now.

### Provider corrections

- `ora_joint_correction.v1` no longer substitutes Bonferroni. It requires a complete exact raw
  p-value family, target index, bound alpha, reported adjusted value and decision, and the analyst's
  declared supported procedure (`bh` or `bonferroni`). It first replays the reported adjustment,
  replaces the target raw p-value with the exact corrected hypergeometric tail, reapplies the same
  procedure to the whole family, and proves a violation only for significant-before and
  non-significant-after materiality. Unsupported procedures, incomplete families, or a report that
  does not replay are `UNKNOWN`. The correct-BH fixture is `REFUTED`, never blocked.
- `interval_bounds.v1` accepts only a code-owned registry ID, exact coordinate role, contig length,
  convention, and topology. Registered contracts are zero-based half-open linear coordinates,
  one-based closed linear coordinates, and a past-end slice-boundary sentinel. Free-form labels or
  caller-supplied inclusivity are impossible inputs and resolve `UNKNOWN`.

Provider definitions were rebound to the new implementation digest
`sha256:13d26eddc19def337b6a34c8c09f3552f829fdf9fbae1358745505188614eef4`.

### Live routing, intended verdict changes, and abstentions

- `double_dipping`: the registry now exposes one `double_dipping` router. Exact supported programs
  use computed engine facts and retain the rich witness at `needs_evidence`; every unsupported
  program delegates to the unchanged shipped check and is still capped by the engine verifier.
- `confounding` and `pseudoreplication`: shipped checks remain authoritative; engine policies abstain.
- `allele_harmonization`: a bare `analysis_type="eqtl"` no longer routes the joint policy. The
  single-source eQTL fixture reverts from `pass + inference.not_audited` to its shipped
  `allele_orientation=pass` only.
- `enrichment_universe`, `coordinate_consumption`, `spatial_iid`, and
  `trajectory_circularity`: no real fact integration exists in this round, so they abstain
  (`not_audited`/`needs_evidence`) and cannot emit `major` or `blocker`.

Frozen enumerated changes in `tests/frozen_oracles/live_audit_oracles.json`:

| Fixture | Old -> new | Reason |
|---|---|---|
| Confirmed exact pbmc_dex | previous engine `blocker` -> `double_dipping=needs_evidence` (legacy was also `needs_evidence`) | The complete witness is preserved, but static scientific premises cannot earn a never-false-accuse blocker. Blocking is deferred to future witness-specific human ratification. |
| Single-source eQTL | `allele_orientation=pass + inference.allele_harmonization=not_audited` -> `allele_orientation=pass` | Bare eQTL is not a multi-source harmonization context. |
| Former synthetic self-ratified coordinate contract | `inference.coordinate_consumption=blocker` -> `not_audited` | Folder relations/authority/digests are inadmissible; no live coordinate facts exist. |

The previously frozen generic-coverage to policy-specific `not_audited` changes for trajectory,
enrichment, and coordinate-without-contract remain non-adverse. No liver-fibrosis or other silent
verdict change is introduced.

### Differential proof and shipped seam

Frozen legacy `groupby_provenance`, `bind_sinks`, and confounding outputs remain byte-exact. The
focused safety/differential command below passes **198 tests**. Confounding and experimental-unit are
unchanged. The double-dipping router is differential-exact by delegation outside its enumerated exact
surface.

The only shipped source file modified in this remediation is:

- `src/sc_referee/registry.py`: replace the duplicate legacy/live double-dipping registrations with
  one inference router under the shipped `double_dipping` ID. Its unsupported-path fallback is the
  unchanged `DoubleDippingCheck`.

`src/sc_referee/audit.py` remains the previously approved minimal Increment-9 seam and was not changed
in this remediation. `_safe_run`, `max_status`, and `FAIL_ON_DEFAULT` semantics are unchanged.
This advisory-cap round changed no shipped source file; it only exercises the existing audit-spine
clamp in the structural invariant test.

### Red-first and verification commands

Red failures were observed before each production correction for: forged folder relation/authority
proofs; missing computed double-dipping module; absent report egress binding; possible later writer;
stale constructor/label/report reaching definitions; method monkey-patching; name-derived `adata`
binding; external `X_pca` overwrite; Leiden method-name selection; count-split layer conflation;
`logreg` calibration; raw/HVG feature conflation; result-key/group mismatch; direct and nested
DataFrame mutation (direct, nested, and aliased); cross-receiver grouping-name conflation; the
canonical/adversarial severity cap; `.X`/`.raw` held-out installation; PCA/raw disjoint lineage;
in-place label replacement; cross-file same-name collision; hard-coded Bonferroni; unsupported or
incomplete ORA families; and free-form interval contracts.

```sh
export PYTHONPATH=/tmp/sc-referee-test-bootstrap:src:.
export UV_CACHE_DIR=/tmp/sc-referee-uv-cache
export MPLCONFIGDIR=/tmp/sc-referee-mpl

uv run pytest -q tests/inference/test_live_trust_boundary_redteam.py
uv run pytest -q tests/inference/test_computed_double_dipping_live.py
uv run pytest -q tests/inference/test_discharge_providers.py tests/inference/test_policy_provider_integration.py
uv run pytest -q tests/inference
uv run pytest -q tests/inference/test_frozen_oracles.py tests/inference/test_effects_and_projections.py tests/inference/test_live_differential_gate.py tests/inference/test_live_audit_seam.py tests/inference/test_live_trust_boundary_redteam.py tests/inference/test_computed_double_dipping_live.py tests/inference/test_discharge_providers.py tests/inference/test_policy_provider_integration.py tests/test_source_ast.py tests/test_provenance.py tests/test_sink_use.py tests/test_double_dipping.py tests/test_audit.py
uv run pytest
```

Final full-suite result: **828 passed, 4 warnings in 56.58s**. The warnings are the existing AnnData
duplicate-feature-name and implicit string-index warnings. No analyzed code was executed at any point;
all source handling was normalization, AST parsing, abstract interpretation, and digesting of real
on-disk artifacts.
