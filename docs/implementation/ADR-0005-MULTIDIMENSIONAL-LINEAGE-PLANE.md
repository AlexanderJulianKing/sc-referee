# ADR-0005: Promote a multidimensional observed-lineage plane

- **Status:** Accepted
- **Date:** 2026-07-28
- **Proposed schema release:** `0.8.0`
- **Related requirements:** SA-FR-012–016, SA-FR-027, SA-FR-040–041, SA-FR-054,
  acceptance criteria AC-02, AC-04, AC-22, AC-25, AC-28, AC-38, AC-47, AC-51

## Context

Accepted schema v0.7.0 can represent Operations, Artifacts, ObservedResults, Claims, and an
aggregate Claim lineage status. Active experiment 0002 proves that sc-referee can independently
recompute one bounded Python/CSV result and link it conservatively to a report Claim. It also
exposes two blocking representation problems:

1. the specification grades report, result, computation, input, execution, and semantic origin
   independently, while the public Claim has only one aggregate status; and
2. normative observed-graph nodes for data structure, analysis choices, selection, execution, and
   environment are absent from the public catalog and AuditBundle.

Using Claim extensions or overloading Artifact and Operation roles for these durable meanings
would make adapters disagree, blur observed computation with scientist intent, and make coverage
denominators impossible to audit. Adding more workflow surfaces before resolving the common graph
would multiply that ambiguity.

## Decision

If accepted, publish one coordinated local schema release `0.8.0`, derived from immutable v0.7.0.
It is an architecture-overhaul release and has no compatibility requirement with the legacy public
GitHub implementation.

### 1. Six independent Claim lineage grades

Replace the v0.7 aggregate-only lineage profile with a required closed `grades` object containing:

- `report_origin`;
- `result_origin`;
- `computational_origin`;
- `input_origin`;
- `execution_origin`; and
- `semantic_origin`.

Each grade records a status (`complete`, `partial`, `missing`, `unavailable`, or `opaque`), exact
record and source references, and bounded limitations. A complete grade has evidence and no
limitation. Every other grade has at least one limitation. The existing aggregate status remains a
deterministic summary only:

- `complete` only when all six grades are complete;
- `missing` when at least one material grade is missing and no positive lineage edge is present;
- `unavailable` when no material grade can be evaluated because evidence is unavailable;
- otherwise `partial`.

An aggregate value cannot override a component grade. Coverage and reporting derive from the six
grades, not from an independently supplied aggregate assertion.

### 2. Public data and decision nodes

Add closed public records for:

- `DataAsset`: a material observed or declared data collection, bound to AssetIdentity and source;
- `Variable`: a named field or feature within one DataAsset, including observed storage type and
  explicit unknown scientific meaning;
- `AnalysisDecision`: one observed, declared, or unresolved choice among alternatives, with exact
  decision inputs, selection statistic when observed, rejected alternatives, outcome-influence
  state, downstream scope, and provenance; and
- `SelectionEnvelope`: the bounded set of AnalysisDecisions and candidate alternatives that could
  have influenced named Claims or results, including an explicit completeness state.

Column names and storage types are observed structure. They do not establish measurement scale,
unit, population, exposure, outcome, or other scientific semantics.

### 3. Public execution and environment nodes

Add closed public records for:

- `Execution`: an observed or imported invocation with command/tool identity, input/output refs,
  timestamps when available, exit state, sandbox/network policy, and evidence source; and
- `Environment`: an observed or imported runtime environment identity, distinct from an attempted
  `EnvironmentReconstruction`.

Static inspection cannot create an Execution. Auditor-owned verification creates an Execution
whose actor and method identify sc-referee, never the project workflow. Project Execution requires
explicit authorization and a qualifying rootless OCI backend; imported logs remain imported
evidence with their actual identity strength.

### 4. Bundle, reference, storage, and coverage integration

Add required arrays for all six new records to AuditBundle, the record union, catalog, SQLite
projection, storage manifest, and replay. Add per-grade Claim coverage counts. Every typed edge must
resolve by record type and identifier. Canonical JSON/JSONL remains authoritative; SQLite remains
generated and disposable.

### 5. Authority separation

- Parser and auditor-verifier evidence may establish observed DataAsset, Variable, Operation,
  Artifact, auditor Execution, and lineage grades within their exact evidence.
- A scientist Answer may establish intended semantics or a declared analysis choice only within
  its authority scope. It cannot establish that project execution occurred.
- A model proposal may suggest bounded lineage or decision links, but they remain proposed and
  Finding-ineligible until independently checked against exact records and snapshot bytes.
- Missing, unavailable, opaque, or conflicted component grades cannot be reversed by confidence,
  uniqueness alone, or an aggregate status.

## Migration from v0.7.0

Migration adds empty arrays for the six new record types and invents no graph history. Existing
Claim result, operation, input, missing, and opaque references are preserved. Because v0.7.0 did
not preserve independent grade states, the migration sets all six grades to `unavailable`, changes
the new aggregate summary to `unavailable`, and preserves the old aggregate value in an
`x-v0-7-aggregate-lineage-status` extension. It does not infer Execution, Environment,
AnalysisDecision, SelectionEnvelope, DataAsset, or Variable records from filenames or roles.

## Acceptance evidence required

1. Positive and negative schema examples for all six record types and every lineage-grade state.
2. Invariant tests proving aggregate Claim lineage is derived from component grades and cannot
   overstate any missing, unavailable, or opaque grade.
3. A fail-closed v0.7→v0.8 migration that preserves existing refs and old aggregate status without
   inventing new observed history.
4. General static runtime promotion of experiment 0002 into DataAsset, Variable, auditor
   Execution, and six Claim grades: report/result/computation/input are evidenced, while project
   execution and unresolved semantics remain explicitly incomplete.
5. A hard negative proving exact comparison/outcome alignment cannot establish an Execution or
   complete Claim lineage.
6. Typed scientist interaction proving resolved intent changes only semantic origin and never
   execution origin.
7. Model-free replay and SQLite rebuild preserving all new records and grade counts byte-for-byte.
8. Report rendering that shows each grade and never presents partial lineage as workflow
   reproduction.

## Consequences

- Public schema version becomes `0.8.0`; accepted v0.7.0, v0.6.0, and v0.5.0 remain immutable.
- Experiment 0002 can be superseded by public records after all acceptance evidence passes.
- Python/Markdown can grow against a stable common graph before R, notebook, Quarto, or workflow
  adapters are added.
- This decision does not qualify any detector, authorize project execution, deploy W3ID schemas,
  install dependencies, or create compatibility work for the legacy public GitHub repository.
- `NotebookCell`, `DocumentChunk`, first-class SemanticUnknown/SemanticConflict, and a generic edge
  record remain separately registered gaps unless implementation evidence proves they are needed
  in this release.

## Acceptance record

- Decision: accept ADR-0005 and schema release `0.8.0`.
- Accepted by: repository owner in the implementation task on 2026-07-28.
- Accepted v0.7.0, v0.6.0, and v0.5.0 packages remain immutable.
- Pre-decision evidence: `derive_aggregate_lineage_status` and `tests/test_lineage.py` exercise the
  proposed six-dimension fail-closed aggregate rule without changing any public v0.7.0 record.
