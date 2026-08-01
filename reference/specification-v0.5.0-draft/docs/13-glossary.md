# 13. Glossary

## Adjudication

An independent judgment that an assessment is a true positive, false positive, detector defect, or insufficiently supported. It is distinct from scientist disposition.

## Analysis decision

A threshold, filter, model, subgroup, contrast, tuning, exclusion, or stopping choice that can shape a reported result.

## Analysis population

The units actually included after eligibility, availability, exclusion, missingness, and quality-control operations.

## Artifact

A data file, model object, scalar, table, figure, serialized result, report, log, or other computational output.

## Assertion

A provenance-bearing statement about scientific meaning, report wording, metadata, or realized computation. Assertions can be proposed, accepted, rejected, superseded, unknown, or conflicted as appropriate.

## Authority scope

The domain in which an actor or evidence source can establish meaning, such as scientific intent, executed computation, reported wording, or metadata definition.

## Claim

A structured proposition tied to exact report text and linked to its computational and semantic lineage.

## Claim-centric inspection

Whole-project inventory followed by deep inspection of final-claim backward slices and the selection envelope.

## Computational lineage

The chain from report text to result, operation, decisions, inputs, environment, and execution evidence.

## ConditionalConcern

A possible material issue that follows only if an explicit unresolved or conflicted premise is true. It is not a Finding and has no severity rating.

## Conflict

Two or more relevant assertions that cannot all be accepted in the same authority scope without resolution.

## Counterevidence protocol

A detector-specific finite checklist of innocent or limiting explanations that must be inspected before a candidate can become a Finding.

## Coverage

A structured account of what files, operations, claims, semantics, detectors, and execution paths were covered, partially covered, unsupported, unavailable, opaque, or uninspected.

## Disclosure

A record of incomplete lineage, unsupported or opaque operations, unavailable evidence, weak data identity, uninspected paths, reproducibility limits, or parser and detector gaps. It is not a scientific accusation.

## Evidence compiler

The architecture that transforms source material through validated stages into observed facts, proposed semantics, resolved semantics and unknowns, detector results, assessment records, and coverage.

## Finding

A narrowly worded demonstrated issue that satisfies all five admission conditions. The term is not used for conditional, unresolved, hypothetical, or informational items.

## MaterialQuestion

An unresolved scientific meaning for which plausible answers can change detector applicability or assessment outcome.

## Publication materiality

The breadth and directness with which a demonstrated Finding affects final claims or publication conclusions. It is separate from severity.

## Scientific Contract

A typed record of population, unit, treatment or exposure, outcome, estimand, comparison, time, scale and orientation, adjustment, denominator, control set, dependence, measurement, missingness and transport, uncertainty, and selection semantics.

## Semantic lock

A content-addressed snapshot of accepted semantics, unknowns, conflicts, claims, contracts, publication scope, and detector inputs from which deterministic detection and reporting replay.

## Scientist disposition

A scientist response: confirmed, accepted risk, disputed, not material, deferred, or corrected in a later revision. It does not objectively adjudicate detector correctness.

## Selection envelope

Operations and decisions capable of selecting, rejecting, filtering, tuning, comparing, or shaping the final reported result.

## Severity

The scientific consequence of a demonstrated Finding. Severity is not assigned to ConditionalConcerns, MaterialQuestions, or Disclosures.

## Source reference

An exact, media-appropriate pointer to code, notebook cells, document chunks, workflow nodes, commands, artifacts, or external evidence.

## Audit deadline

The user-visible elapsed hard limit for one run segment. Model latency, queues, network retrieval, installation, sandbox startup, execution, and rendering count; only scientist-response wait pauses it.

## Auditor-owned verification

Versioned code shipped with sc-referee that verifies an existing result or identity without importing project modules, fitting alternatives, or selecting an analysis.

## Causal Contract

A typed record separating claim intent, target estimand, identification assumptions, covariate roles and timing, optional causal structure, implemented estimator, and reported claim.

## Environment reconstruction

Creation of an isolated audit-owned dependency environment. It is exact only when the resolved environment is sufficiently fixed; unpinned resolution is approximate.

## ExternalEvidence

A durable record of an external retrieval used by the audit, including purpose, location, retrieval time, content identity, cache state, and reproducibility effect.

## Publication surface

The report, notebook, manuscript, table set, figure set, or rendered artifact treated as the final source of claims. Unresolved candidate surfaces remain separate.

## ReproductionRequest

A structured request for evidence-producing work outside the interactive auditor, such as an HPC run, trace capture, checksum, environment capture, or export of an existing artifact.

## Safe inspection

Automatic non-project-code operations such as syntax parsing, safe structured reads, metadata inspection, manifests, hashes, and non-executable format inspection.

## Unsupported operation

An operation outside a parser or detector's declared semantics. It remains in the graph and propagates to dependent coverage disclosures.

## Verified explicit extraction

A model-assisted structured extraction of literal source meaning that cites an exact span, can be checked independently, and has passed a non-model verification.


## Detector qualification

A durable record supporting a detector maturity state, including maintainers, agent-only, mixed, or human review basis, pinned adjudication references, optional human approvals, domain expertise, evaluation and independent-corpus references, disagreement, safety gates, threshold policy, metrics, and the public qualification report.

## Parser result

The source-specific output of a named parser backend, including coverage state, emitted graph records, syntax issues, opaque constructs, and any disagreement with a secondary parser.

## Rootless OCI sandbox

A capability-reported container execution backend running without a privileged daemon or root-equivalent host authority and enforcing the project-execution controls required by sc-referee.

## Workspace diverged

A run state indicating that the live project changed after snapshot creation. The current audit remains bound to the original immutable snapshot.

## W3ID schema identifier

An immutable canonical HTTPS identifier under `https://w3id.org/sc-referee/schema/` used for published schema `$id` and `$ref` values.


**AgentReview**  
One isolated, version-pinned coding-agent review with explicit blindness, scope, evidence, verdict, and transcript identity.

**BenchmarkAdjudication**  
A conservative cross-provider synthesis of blind reviews and fresh adjudications. Material disagreement excludes a case rather than being overridden by majority vote.

**VerifiedGoodFixture**  
A release-blocking negative fixture proven only within a declared claim, detector, operation, issue-class, semantic, and execution scope. It is not a global correctness certificate.

**ScopeVerifiedGood**  
A workflow verified only for explicitly named paths or detector scopes, often used when full execution or evidence is unavailable.

**HardNegativeFixture**  
A verified-good fixture containing a superficially suspicious pattern and a documented decisive innocent explanation.

**CapabilityMatrix**  
A machine-generated, versioned set of narrow capability envelopes across syntax, operation extraction, semantics, detectors, maturity, review basis, versions, gaps, and abstention conditions.

**Agent-panel qualification**  
Detector qualification based on pinned independent coding-agent panels from multiple provider families. It must be disclosed and is not represented as human expert endorsement.

**ROCrateExport**  
An RO-Crate 1.3 package containing the native audit bundle and publication metadata while leaving sc-referee records canonical.
