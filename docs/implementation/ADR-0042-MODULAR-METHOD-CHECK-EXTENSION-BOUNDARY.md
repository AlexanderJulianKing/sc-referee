# ADR-0042: Consolidate the modular method-check extension boundary

- **Status:** Accepted under the repository owner's explicit approval of the reviewed six-step
  consolidation plan
- **Date:** 2026-07-31
- **Coordinated public schema release:** `0.17.0`
- **Related decisions:** Accepted ADR-0018 through ADR-0020 and ADR-0037 through ADR-0041
- **Finding impact:** None; no detector gains qualification, maturity, or Finding permission
- **Execution impact:** None; production inspection and qualification remain non-executing

## Context

The first analysis-scoped report/source conflict proved that the shared snapshot, parser,
lineage, scientist-interaction, method-ledger, storage, reporting, and replay layers are reusable.
It also exposed three remaining coupling points:

1. the controller imports, validates, and dispatches the analysis-method detector explicitly;
2. report, Python, and R Markdown adapters share one implementation-file digest, so an unrelated
   adapter edit changes every adapter identity; and
3. schema v0.16.0 names a generic-looking method-conflict proof but fixes its operands and
   independent verifier to founder orientation.

Repeating those changes for each scientific check would turn extension into a schema-and-
controller rewrite. That is incompatible with the intended modular architecture.

## Decision

### 1. Use an explicit, content-addressed detector binding registry

Each detector-eligible scientific check has one closed binding that names its check identity and
version, detector identity and version, scientific-contract dimension, comparison relation,
required evidence planes and roles, counterevidence profile, maturity ceiling, and manifest
digests. The packaged registry is canonical, allowlisted, version-pinned, and digest-bound.

There is no ambient plugin discovery. A missing, duplicate, drifted, uninstalled, or unsupported
binding fails locally to an unavailable or unsupported result. Merely installing a Python module
cannot change audit coverage or Finding eligibility.

The generalized experimental detector is versioned `0.2.0`. Any external qualification freeze
bound to the founder-specific `0.1.0` implementation remains immutable historical evidence and
cannot qualify or promote `0.2.0`; qualification must restart against the new identity.

The controller calls one registry entry point. Adding another check to an existing detector family
must not require a controller edit.

### 2. Replace the founder-specific evaluator with one typed method-conflict evaluator

The evaluator consumes only a validated binding, one answered analysis-scoped question, the exact
human Answer-derived requirement, normalized report/source observations, the closed scope graph,
and completed finite counterevidence checks. It delegates comparison to the existing closed
method-ledger algebra:

- `value_equals` over canonical scalar operands;
- `set_relation` over unique canonical string sets; and
- `step_precedes` over unique ordered step names.

Each relation keeps its own operand validator and deterministic comparison semantics. There is no
open JSON predicate, executable expression, or model-authored comparison function.

### 3. Give each adapter implementation its own identity boundary

Move the shared selected-report adapter, Python founder-orientation adapter, and R Markdown MVMR
adapter into separate modules. Each adapter manifest binds only the file and grammar that implement
that adapter. Editing one adapter must not change unrelated adapter implementation digests.

Adapters remain incapable of emitting Findings. They produce normalized observations or a bounded
abstention. They do not execute project code or infer historical intent, numerical causality, or
scientific correctness.

### 4. Publish one closed typed static-method proof envelope in schema v0.17.0

Preserve v0.16.0 unchanged. Add `typed_static_method_conflict_v1`, which binds:

- one registered check and detector binding;
- exactly one relation from the closed comparison algebra;
- relation-valid required, report, and source operands;
- exact independently retained declarations and source locations;
- exact human Question, Answer, ScientificContract, and accepted requirement assertion;
- one closed selected-output scope; and
- completed applicability and finite counterevidence results.

The envelope is extensible only by adding a new check whose operands already satisfy one accepted
relation. Adding a new evidence kind, relation, authority source, or counterevidence meaning still
requires an ADR and forward-only schema change.

Migration from v0.16.0 carries the founder-specific proof only as namespaced historical evidence.
It does not infer a generic binding or create qualification, metrics, promotion, or Finding
authority.

### 5. Keep qualification structurally generic and implementation-independent

The qualification controller may share public record schemas, canonical serialization, digest
rules, budgets, and chronology validation with production. It must not import or call the
production adapter, detector, reducer, recognition grammar, or extracted operand.

Each qualification adapter independently derives its operand from retained bytes. A shared generic
qualification engine validates inventory, identity, authority, typed comparison, scope,
counterevidence, chronology, and proof construction. Thus the framework is reusable while a defect
in production semantic extraction cannot corroborate itself.

### 6. Prove the extension standard with three shapes

Tests must exercise:

1. a report-only scalar check that requires configuration and tests only;
2. a report-plus-source check in a second source language using one isolated adapter; and
3. a set-relation or step-order check with explicit ambiguity and counterevidence controls.

For these shapes, no edits are permitted to controller dispatch, storage, reporting, Finding
admission, or the v0.17.0 public schema. Deterministic replay and conservative abstention remain
mandatory.

## Extension standard

- A new report-only check should require one declarative profile plus tests.
- A new recognizable code form should require one isolated adapter plus tests.
- A new method conflict using an accepted relation should require one content-addressed binding,
  independent qualification adapter, and tests, but no detector class or schema change.
- Only a genuinely new evidence type, comparison relation, authority source, or public record
  meaning may trigger an ADR/schema revision.

Failure to meet this standard is an architectural defect to consolidate before adding more
scientific vocabulary; it is not a reason to silently special-case the controller or schema.

## Alternatives rejected

### Infer arbitrary scientific semantics with an LLM

Rejected because model confidence cannot establish a material premise and the same model may have
created the method under review.

### Dynamically discover installed detectors or adapters

Rejected because environment-dependent discovery would make coverage and replay nondeterministic.

### Reuse production extraction in qualification

Rejected because a common implementation defect could certify itself.

### Use one permissive generic proof object

Rejected because untyped operands and open predicates would erase the finite applicability and
counterevidence boundary.

## Test, acceptance criterion, and remaining limitation

- **Tests required:** registry order, duplicate, missing, digest-drift, maturity, and local-failure
  controls; isolated adapter-digest mutation; scalar, set, and step relation validation; all
  existing founder conflict/negative/counterevidence cases; independent-verifier import isolation;
  three-shape extension conformance; migration, packaging, report, storage, replay, and complete
  regression/handoff gates.
- **Acceptance criterion:** all three extension shapes can be added without modifying controller,
  storage, reporting, admission, or schema v0.17.0, while old checks replay byte-for-byte and no
  new production Finding authority exists.
- **Remaining limitation:** a deterministic adapter still must be written for every genuinely new
  scientific representation. The framework cannot recognize arbitrary scientific meaning, runtime
  behavior, or paraphrases without bounded evidence. Existing cross-provider qualification remains
  pending and must restart if the candidate's material logic or identity changes.
