# ADR-0022: Admit a static closed-scope proof basis for detector qualification

- **Status:** Accepted
- **Date:** 2026-07-30
- **Target architecture specification:** `0.6.0`
- **Accepted coordinated public schema release:** `0.15.0`
- **Related decisions:** Accepted ADR-0012 and ADR-0017; deferred ADR-0015 and ADR-0016
- **Related requirements:** SA-FR-031, SA-FR-085, SA-FR-091, SA-FR-102,
  AC-43, AC-55–58, AC-61–62

## Plain-language summary

Some detectors check a fact that is completely visible in immutable files. For example, the first
experimental detector compares one literal report sentence with one exact raw mean difference and
the static source path that writes that value into the report. Rerunning the research workflow does
not make that particular contradiction more or less true.

Schema v0.14.0 nevertheless requires a clean project execution for every complete verified-good or
hard-negative control. That requirement blocks qualification of a non-executing detector even when
all of its material premises and every finite counterevidence check can be replayed from exact
static artifacts. It also pressures the evidence-first MPP toward the optional execution system
that accepted ADR-0017 deliberately deferred.

This ADR proposes one alternative control family: a closed, detector-specific static scope whose
exact raw files, independently derived facts, verifier identity, applicability obligations, and
counterevidence checks are replayable. It does not treat repository prose, reviewer confidence, a
partial scan, production semantic records, or the production detector's own output as proof. It
does not claim that the project ran or that the overall analysis is correct.

## Context

Accepted ADR-0012 correctly rejected unbound proof booleans. Public schema v0.14.0 carries exact
review, snapshot, contract, operation, environment, execution, and sandbox inputs. Its complete
control branches have these fixed meanings:

- `verified_good_fixture` requires `clean_environment_executed`;
- `hard_negative_fixture` requires `clean_environment_executed`; and
- `scope_verified_good` may use bounded `documented_external_execution`.

The accepted schema has no complete non-executing negative-control branch. Setting
`execution_evidence: not_executed` on a complete verified-good or hard-negative fixture fails
schema validation and the evaluator independently rejects it.

Existing independent execution evidence does not close the gap. A bounded imported execution can
support only `scope_verified_good`, while v0.14.0 cannot bind the full authorization, lock,
WorkItem, Artifact, and AssetIdentity closure required for a clean control. Deferred ADR-0015
documents that separate execution-evidence gap. Manufacturing or loosely importing such evidence
would be less conservative than admitting the actual static basis.

The first experimental direction detector is a concrete motivating case. Its applicability is
defined entirely by exact immutable report, Python, and table bytes; an auditor-owned raw
mean-difference calculation; exact static writer lineage; literal label alignment; and a finite
opposite-claim check. The detector explicitly makes no execution, author-intent, biological-truth,
or global-correctness claim.

## Decision

Publish a forward-only public schema v0.15.0 from immutable v0.14.0. Do not change an
earlier schema package. ADR-0015 and ADR-0016 remain deferred; their former unscheduled v0.15.0
target is not a reservation, and any future execution release must use the next available version.

### 1. Preserve existing clean-control kinds and add two explicit static kinds

Do not relabel an existing fixture or add a generic proof-basis switch to every fixture. Keep the
accepted meanings of `verified_good_fixture`, `scope_verified_good`, and
`hard_negative_fixture`, including their current execution requirements. Add exactly two distinct
fixture kinds:

- `static_scope_verified_good`; and
- `static_scope_hard_negative`.

Both new kinds require `execution_evidence: not_executed`. Their fixture proof must contain empty
Environment, Execution, and SandboxCapability inputs and one exact
`StaticQualificationProof` reference. `static_scope_hard_negative` additionally retains
ADR-0012's nonempty suspicious-pattern and decisive-innocent-explanation evidence. Both retain the
complete negative panel, exact ScientificContract and Operation inputs, declared detector,
claim/issue/operation scope, no material dissent, and the global-correctness prohibition.

The new kinds never satisfy a clean-execution claim and are never rendered as “clean controls.”
Reports call them static scope controls and show their counts separately. This ADR therefore adds a
parallel static control family rather than silently weakening ADR-0012.

### 2. Add two typed, replayable static-qualification records

Add `StaticQualificationProfile` and `StaticQualificationProof` to the public record catalog and
AuditBundle.

`StaticQualificationProfile` is frozen before qualification case assignment or case-content
inspection. It binds:

- the exact target DetectorManifest reference, semantic digest, implementation digest, and every
  parser, semantic-profile, and version-manifest digest in its applicability envelope;
- an evaluator-owned verifier entry point plus a sorted content-digest inventory of its complete
  implementation and runtime dependency closure;
- the allowed non-semantic shared utilities, limited to canonical JSON, hashing, schema-shape
  validation, and source-reference resolution;
- deterministic source/surface selection, candidate enumeration, transitive writer/data
  dependency closure, and parser-completeness rules;
- exact file-count, byte, recursion, and elapsed-time budgets;
- closed applicability-obligation, counterevidence-check, and result vocabularies;
- the pre-case corpus-selection protocol-artifact reference and digest; and
- a profile-freeze time and semantic digest that must precede the first assigned case.

`StaticQualificationProof` is the typed verifier result for one frozen case. It binds:

- the exact profile reference and digest;
- the exact case-assignment artifact reference and digest, created under the frozen selection
  protocol before the case workspace or content was inspected;
- the already frozen scientific-label artifact reference and digest;
- one RepositorySnapshot plus every admitted full-digest FileRecord and AssetIdentity reference;
- a closed, sorted dependency graph and exact retained-byte inventory;
- separately typed applicability and finite-counterevidence results;
- the independently derived literal claims, numeric operands, orientations, writer/data paths, and
  scope inventory needed by the frozen profile; and
- exact creation chronology after the scientific-label freeze and before Stage 3.

Every dependency is a typed reference plus semantic digest. A naked digest, prose assertion, or
boolean does not establish a proof premise. The record validator re-resolves the graph and retained
bytes and deterministically recomputes the record identity.

### 3. Derive absence and chronology properties; do not assert them as flags

The controller derives static-proof eligibility from the closed graph. It does not accept fields
such as `scope_complete: true`, `detector_output_observed: false`, or
`project_code_executed: false` as authority.

Eligibility requires all of the following replayed invariants:

- deterministic enumeration reaches every candidate path defined by the frozen profile;
- each required byte is retained under a full AssetIdentity and rehashes exactly;
- every candidate either enters the unique supported closure or has a recorded supported exclusion;
- no unsupported, ambiguous, partial, weak-identity, over-budget, or conflicting candidate remains;
- the proof dependency graph contains no DetectorResult, Finding, Execution,
  ProjectExecutionAuthorization, SandboxCapability, project-execution WorkItem, model proposal, or
  model-derived premise;
- the label-freeze dependency precedes proof construction;
- detector dispatch and output creation occur only after proof freeze through a controller
  chronology edge, while the proof remains outside the detector's semantic inputs;
- every Stage-3 packet and comparison depends on both the already completed proof and the later
  detector output; and
- the exact profile and corpus-selection protocol freeze precede case assignment, and the
  case-assignment artifact precedes workspace construction and review.

This proves only that no detector output or project-execution authority is reachable from the
admitted proof graph. It does not make a global claim about what an external person or system may
have viewed or executed.

Each check records `completion_status` separately from `outcome`. Completion is one of
`completed`, `unavailable`, or `error`; the frozen profile defines a separate closed outcome enum
such as `agreement`, `conflict_present`, `conflict_absent`, `counterevidence_present`, or
`counterevidence_absent`. A complete static control requires every mandatory check to complete and
the result combination to be compatible with the independently frozen panel label.

### 4. Independently rederive every material fact from immutable raw bytes

The static verifier belongs to the isolated answer-side package. It must not import, invoke, copy
from, or accept as an authoritative input any production detector, DetectorResult, production
ParserResult, Claim, ObservedResult, Operation, Artifact lineage, or production helper that derives
a material fact. It independently rereads the immutable raw bytes and rederives every material
literal, numeric value, orientation, candidate set, data dependency, writer path, and
counterevidence outcome.

Production-derived public records may be compared only after label freeze as non-authoritative
cross-check outputs. They cannot satisfy an obligation. The two implementations may share only the
non-semantic utilities enumerated in the frozen profile. The validator rehashes the evaluator
implementation and full dependency lock before accepting its proof.

A model conclusion, confidence score, repository self-description, public answer key, or
production DetectorResult cannot create, complete, or reverse the static proof or scientific
label. The independent 4+2 panel continues to establish the label; the static verifier establishes
only exact closure and independently checkable facts.

### 5. Limit the first profile to the bounded direction detector

The first permitted `StaticQualificationProfile` covers only the exact semantic digest of
`detector:bounded-report-mean-direction` version `0.1.0` and the Experiment 0011 envelope. Before
any case is selected, its closure algorithm fixes these rules:

1. take the selected report path only from the opaque per-case assignment manifest created under
   the pre-frozen selection protocol before workspace construction or case-content inspection;
2. enumerate every snapshot `.md`, `.py`, and `.csv` candidate under the fixed whole-snapshot
   count and byte budgets;
3. require every enumerated candidate to be fully captured, full-digest identified, and strict
   UTF-8;
4. independently inventory every literal directional sentence on the complete selected report;
5. independently enumerate the supported Python raw two-group mean and report-writer grammar and
   reject any unsupported construct on a candidate dependency path;
6. independently resolve one unique transitive table-to-mean-to-writer-to-selected-report path;
7. independently recompute the finite scalar from the complete CSV bytes and exact literal group
   and outcome columns; and
8. complete the opposite-direction sibling-claim search over the entire selected report.

Zero, multiple, dynamic, unsupported, unreadable, weakly identified, or over-budget candidates make
the static proof unavailable. They do not become negative controls.

The profile does not cover transformed effects, regression coefficients, plots, generated reports,
runtime-only dataflow, alternative analyses, or scientific correctness. Additional profiles require
their own pre-case frozen manifest, independent implementation lock, applicability matrix, hard
negatives, mutations, and maintainer review. A generic “statically inspected” claim has no
qualification authority.

### 6. Stratify qualification, metrics, and promotion by control family

The new static kinds may satisfy the verified-good and hard-negative promotion safety gates only
for a detector whose frozen manifest and qualification envelope state that every material Finding
premise is `static_closed_scope`. They cannot qualify a detector premise about runtime behavior,
environment, package dispatch, rendered output, remote data, stochastic behavior, or actual
project execution.

DetectorCaseOutcome, QualificationMetricSet, DetectorQualification, the public qualification
report, and capability generation must retain separate counts and rates for:

- clean-execution controls;
- documented-external-execution scope controls; and
- static-closed-scope controls.

No pooled rate may hide the control family. A qualification with only static controls must say so
prominently and may grant Finding permission only inside the exact frozen static envelope.

The enforced chronology is:

```text
detector + verifier + profile + selection-protocol freeze
  -> opaque per-case assignment and selected-path manifest
  -> blind workspace and Stage 1/2 scientific-label freeze
  -> static proof freeze
  -> production detector dispatch and output
  -> Stage 3 comparison
```

The production detector consumes only its ordinary locked production inputs. The static proof is a
qualification-controller gate and Stage-3 input, never a detector premise.

All other gates remain unchanged: four blind Stage-1 reviews across two provider families, two
fresh falsifying Stage-2 adjudications, label-before-detector chronology, fresh Stage-3 review,
decisive counterevidence, regression cases, disagreement exclusion, problem-cluster-aware metrics,
held-out separation, public reporting, a later pilot-informed numerical-threshold ADR, and explicit
maintainer promotion approval.

No detector is promoted by accepting or implementing this ADR. Experimental outputs remain
Finding-ineligible until that separate evidence and authority exist.

### 7. Migrate fail closed

The v0.14.0 to v0.15.0 migration preserves every existing fixture kind and its accepted execution
meaning. It creates no `StaticQualificationProfile`, `StaticQualificationProof`,
`static_scope_verified_good`, or `static_scope_hard_negative` record. It creates no metric,
qualification, maturity, Finding permission, or promotion authority.

Because `schema_version`, record unions, and proof contracts change, migrated v0.15.0 records
receive newly derived identities and semantic digests where those values are content-derived. The
migration preserves exact v0.14.0 source/evidence references and content digests as historical
inputs; it does not claim byte-identical or semantic-digest-identical v0.15.0 records.

## Alternatives

### Keep execution mandatory for all negative controls

Rejected. It makes the optional post-MPP execution system a qualification prerequisite even when
the detector's entire claim is about exact static artifacts. It is costly for large workflows and
does not strengthen a source-level contradiction that does not claim runtime behavior.

### Treat any imported successful run as sufficient

Rejected. A successful process exit does not establish scientific correctness, exact artifact
identity, detector scope, or the full clean-execution closure. It would also contradict the known
v0.14.0 execution-proof gap.

### Let the production detector certify its own controls

Rejected. A shared defect could validate itself. Qualification remains answer-side,
label-before-detector, and independently reviewed.

### Use review consensus without a deterministic static proof

Rejected. Reviewer agreement cannot establish that the required bytes were complete, that every
finite counterevidence check ran, or that unsupported inputs were not silently treated as covered.

### Add a generic static-inspection checkbox

Rejected. Static adequacy is detector- and envelope-specific. A generic checkbox would recreate
the unbound boolean problem resolved by ADR-0012.

### Reuse existing verified-good and hard-negative kinds with a proof-basis flag

Rejected. Those accepted kinds currently imply their execution branches. A parallel flag would
create a difficult fixture-kind/proof-basis/execution-evidence cross-product and let careless
reports pool unlike controls. Distinct static kinds preserve the old meaning and make the evidence
basis visible in records, metrics, reports, and capability claims.

## Acceptance evidence required

1. Schema tests preserve every existing fixture branch, accept both distinct static fixture kinds,
   and reject every static/execution cross-branch combination.
2. Migration tests preserve exact v0.14.0 evidence as historical input, derive new v0.15.0
   identities honestly, and create no static record or authority.
3. The first static verifier is dependency-isolated from every production fact-derivation path,
   rederives every material fact from copied immutable raw bytes, and validates against its complete
   implementation/dependency semantic lock.
4. Positive, covered-good, hard-negative, ambiguous, unsupported, weak-identity, over-budget,
   contradictory, and mutation cases exercise every applicability obligation and finite check.
5. Removing, adding, reidentifying, rehashing, relinking, or changing any required record, raw
   source byte, typed verifier input/result, obligation, implementation dependency, or
   counterevidence item invalidates the proof.
6. Chronology tests prove the complete sequence from profile/protocol freeze through opaque case
   assignment, blind label freeze, static proof, later detector dispatch/output, and Stage 3. Stage
   1 and Stage 2 contain no detector identity or output, and the proof is absent from detector
   semantic inputs.
7. Stage 3, metrics, reports, AuditBundle validation, canonical JSONL, disposable SQLite,
   RO-Crate, capability generation, and model-free replay independently revalidate the exact static
   proof and preserve proof-family strata.
8. No test or production path imports or executes project-authored code, calls a model, infers a
   missing premise, or turns a public-development fixture into qualification evidence.
9. The capability matrix remains experimental and Finding-ineligible until a separate real
   cross-provider qualification record and maintainer promotion decision exist.

## Consequences

Positive:

- the evidence-first MPP can qualify a detector whose material claim is genuinely static without
  requiring a scientifically irrelevant rerun;
- large, remote, or computationally expensive workflows can contribute exact bounded controls;
- proof remains replayable and detector-specific rather than becoming a vague static-review claim;
  and
- project execution remains available later for detectors whose premises actually depend on it.

Costs:

- schema v0.15.0, two typed records, two explicit fixture kinds, and a fail-closed migration are
  required;
- the evaluator needs a separately implemented and dependency-locked static verifier plus durable
  profile, case-assignment, label, proof, and comparison chronology; and
- each additional proof profile requires its own narrow evidence and review rather than inheriting
  generic static authority.

## Test, acceptance criterion, and remaining limitation

- **Test added before acceptance:**
  `tests/test_evaluation_control_fixture.py::test_v014_deliberately_rejects_a_complete_static_control`
  freezes the current gap by proving that both schema v0.14.0 and its evaluator reject a complete
  verified-good or hard-negative fixture with no execution evidence.
- **Acceptance criterion satisfied by this proposal:** the gap is localized without changing any
  accepted record, weakening execution evidence, enabling a Finding, or inventing a default.
- **Acceptance record:** accepted by the project owner on 2026-07-30 together with coordinated
  public schema version `0.15.0`. The owner also pre-authorized future narrow, fail-closed ADR and
  schema maintenance decisions, while reserving changes to scientific authority, Finding
  eligibility, execution privilege, or public product scope for explicit consultation.
- **Implementation evidence:** public schema v0.15.0, its fail-closed migration, the isolated
  raw-byte verifier, both static fixture kinds, Stage-3 chronology checks, proof-family-stratified
  metrics, report revalidation, packaging, and model-free proof replay pass locally. The verifier
  rejects unsupported, ambiguous, weak-identity, over-budget, contradictory, counterevidenced,
  chronologically invalid, and byte- or manifest-mutated cases without executing project code.
- **Remaining coverage limitation:** the implemented cases are synthetic mechanism evidence. No
  authenticated real answer-blind corpus panel, numerical-threshold decision, detector
  qualification, maintainer promotion, or production Finding authority is claimed.
