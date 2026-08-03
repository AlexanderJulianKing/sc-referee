# Record interpretation

Use only records present in `audit.bundle.json`.

| Record | Meaning | Never restate as |
|---|---|---|
| `Finding` | A narrowly worded demonstrated issue that passed admission | A global flaw, risk score, or invalid paper |
| `ConditionalConcern` | A consequence that applies only if its linked unknown resolves a stated way | A demonstrated issue |
| `MaterialQuestion` | An unresolved answer that can change applicability, assessment, or materiality | A defect or accusation |
| `WorkItem` | A controller-scheduled bounded packet with exact allowed inputs and outputs | Permission for open-ended review or project execution |
| `Answer` | Human intent within exact subjects and semantic dimensions | Authority over observed computation or unrelated claims |
| `SemanticAssertion` with `proposed` status | A model-authored candidate interpretation awaiting controller/human resolution | An accepted premise or Finding evidence |
| `ObservedResult` | An observed or auditor-recomputed typed value with its own lineage grade | Proof that it produced a report Claim or that its scientific interpretation is correct |
| `Claim.lineage.grades` | Independent report, result, computation, input, execution, and semantic origins with exact evidence and limitations | One aggregate confidence score or authority to fill another grade |
| `Claim.lineage` with `partial` status | A deterministic summary of six grades with at least one incomplete dimension | Complete workflow execution or report-generation provenance |
| A Claim `operation_ref` to a static report writer | Exact source evidence that a literal output path targets the selected report Artifact | Proof that the operation ran, that its argument equals the snapshotted bytes, or that it generated the report wording |
| A report writer `input_ref` to a result Artifact | Exact whitelisted source-expression dataflow, directly or through at most eight ordered uniquely bound module assignments, from a supported computation return into a literal report write | Proof that either operation ran, that the writer produced the snapshotted report, or that the result generated a particular Claim |
| `AnalysisDecision` / `SelectionEnvelope` | An observed bounded source-level decision and the exact known portion of its alternative set | Proof the code path executed, proof of runtime container semantics, the scientific rationale, all alternatives considered, or demonstrated outcome influence |
| `Environment` with `partial`, `unavailable`, or `opaque` identity | Static project declarations (including separately observed nested roots and unresolved conflicts) or bounded auditor-runtime facts with exact limitations | Proof of the environment that executed the project workflow or authority to reconcile conflicting declarations |
| `Execution` with `execution_kind: imported` | An externally supplied execution assertion with its exact source and identity strength | Controller-observed execution, authenticated provenance, clean-control evidence, output correctness, or a Claim/Finding premise unless separate records independently establish those properties |
| `ReproductionRequest` with `proposed` status | A bounded request for externally generated evidence | Approval or authority to execute code, use credentials, access a network, or submit scheduler work |
| `CacheEntry` | A project-local authenticated reuse record whose exact dependency key and output refs validated for this run | Independent scientific evidence, proof that a cached premise is true, or a correctness signal |
| `PerformanceRecord` | A replayable aggregate measurement for the current AuditRun through semantic lock, with exact extension-declared metering scope | Total run duration, post-lock cost, a final AuditRun outcome, or a zero measurement for `null` resources |
| `DetectorResult` with `detector_maturity: experimental` | One deterministic development evaluation, including applicability, premises, finite counterevidence, and exact coverage; `evaluation_finding_candidate` is qualification input only | A Finding, a correction request, detector qualification, or evidence that uncovered Claims are correct |
| `DetectorEvaluationCandidate` | A Finding-shaped experimental output that passed non-maturity admission checks for answer-side evaluation only | A Finding, production detector permission, or proof that its root locator is correct |
| `Stage3ComparisonReview` | One fresh, bounded reviewer judgment about candidate-to-root equivalence | Production Finding admission, scientific-label authority, or an independent metric |
| `DetectorCaseOutcome` | A model-free reconciliation of exact Stage-3 reviews; a complete v0.11 record retains one projection per DetectorResult opportunity | Detector qualification, a correctness class for the entire workflow, or usable metric input when its projection is legacy-incomplete |
| `QualificationMetricSet` | Twelve deterministic ratios and problem-cluster intervals recomputed from its digest-bound case-outcome inputs | Detector promotion, a correctness certificate, or evidence outside its declared envelope and corpus partitions |
| `StaticQualificationProof` with `proof_profile_kind: typed_static_method_conflict_v1` | An independently rederived closed typed comparison over exact retained bytes, method binding, adapter identity, human authority, scope, and finite checks | Detector qualification, execution evidence, an accuracy estimate, promotion, or a Finding |
| `Disclosure` | An unsupported, opaque, unavailable, intentionally uncovered, or routine not-applicable coverage boundary | Evidence that the hidden behavior is wrong; a routine not-applicable record is not a concern |
| `CoverageRecord` | The exact inspected denominator and limitations for this run | A correctness certificate |

## Required checks before summarizing

1. Confirm `coverage_records` contains exactly one record.
2. Copy assessment counts from `coverage_records[0].assessment_counts` and verify that they match
   the corresponding bundle arrays.
3. For every Finding, preserve its bounded statement, evidence links, non-inferences, and
   publication-materiality state.
4. Preserve every open MaterialQuestion and material Disclosure relevant to the selected surface.
   Report routine `not_applicable` scientific-check Disclosures as a separate count unless complete
   coverage bookkeeping is requested; do not silently drop them from the bundle or call them
   concerns.
5. State `overall_status`, `uninspected_paths`, opaque boundaries, and `known_gaps`.
6. If `publication_surfaces[0].status` is `unresolved`, state that publication materiality is
   unassessed and keep candidate surfaces separate.
7. Read all six Claim lineage grades. An auditor `Execution` establishes only auditor verification;
   it does not complete project `execution_origin`. An imported `Execution` retains its stated
   identity strength and does not complete Claim lineage merely because it validates. A scientist
   Answer may change only `semantic_origin` within its exact authority scope.
8. If ReproductionRequests exist, present them as optional external evidence needs and preserve
   their security considerations, resource uncertainty, and nonauthorization boundary.
9. If a PerformanceRecord exists, verify `x-measurement-boundary: semantic_lock` and
   `x-postlock-elapsed-included: false`; state its I/O/cache/model scopes before citing values.
10. If qualification records exist, preserve legacy/comparison exclusions, opportunity rather than
    candidate denominators, zero-denominator nulls, bootstrap limitations, and the metric input
    digest. State both promotion flags exactly and never infer a threshold decision.
11. If experimental DetectorResults exist, report their exact terminal states separately from the
    four assessment arrays. Never count `evaluation_finding_candidate` as a Finding; preserve its
    candidate wording, finite counterevidence outcomes, and declared coverage or abstention gaps.
12. If a typed method StaticQualificationProof exists, preserve its method binding, independent
    adapter, relation and operand type, exact retained observations and authority records,
    applicability/counterevidence results, comparison outcome, limitations, and production-Finding
    permission. Proof completeness is not qualification or promotion.

## Replay interpretation

Replay establishes deterministic regeneration from the semantic lock. It does not establish that
the locked scientific premises are true, that detector coverage is complete, or that the workflow
is correct. Compare semantic records, assessments, coverage, lock digest, and report output.
`AuditRun` history and `StorageManifest` bookkeeping may be regenerated, so aggregate bundle bytes
need not be identical.
