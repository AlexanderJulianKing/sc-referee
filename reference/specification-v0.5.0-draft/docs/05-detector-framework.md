# 5. Detector framework and finding admission

## 5.1 Purpose

The detector framework converts locked evidence into conservative, reproducible assessment records. It is optimized for precision of demonstrated Findings. It must distinguish a negative result inside declared coverage from abstention, unsupported paths, unresolved semantics, and unavailable execution evidence.

The production framework does not ask an LLM to search for unspecified scientific mistakes.

## 5.2 Detector interface

```python
class Detector(Protocol):
    manifest: DetectorManifest

    def evaluate(self, context: AuditContext, target: NodeId) -> DetectorResult:
        ...
```

The implementation receives canonical records and returns a deterministic result. It does not modify the evidence graph or apply a replacement analysis.

## 5.3 Detector manifest

Every detector version declares:

- stable identifier, version, family, issue classes, and maturity;
- applicable record types, domains, languages, workflow systems, operations, packages, and version constraints;
- required evidence and accepted semantic assertion classes;
- scientific and computational assumptions;
- explicit abstention conditions;
- permitted output record types;
- a finite counterevidence protocol;
- coverage conditions and known limitations;
- wording constraints and prohibited inferences;
- deterministic implementation identity; and
- positive, verified-good negative, ambiguous, unsupported-path, and counterevidence fixtures.

A detector cannot generalize outside this contract because a workflow merely looks similar.

## 5.4 Evaluation states

Every scheduled detector-target pair terminates in exactly one state:

```text
finding_candidate
conditional_concern_candidate
material_question_candidate
disclosure_candidate
no_issue_detected_within_coverage
not_applicable
insufficient_semantics
unsupported_path
execution_evidence_unavailable
detector_error
```

`no_issue_detected_within_coverage` is valid only when the detector applies and actual coverage is covered or partially covered. It is not a statement that the analysis is correct.

## 5.5 Assessment outputs

### Finding

A Finding means a demonstrated issue. It is the only record described as something the auditor established is wrong in the exact bounded sense stated.

### ConditionalConcern

A ConditionalConcern states an explicit unknown or conflict and the consequence that follows if it is true. The condition appears in the title or first sentence. It has potential impact, not severity.

### MaterialQuestion

A MaterialQuestion names unresolved meaning for which plausible answers can change applicability or assessment. It links to a conditional concern when a specific consequence can be stated.

### Disclosure

A Disclosure records a limitation in lineage, operation support, data identity, execution evidence, reproducibility, inspection scope, parser coverage, or detector coverage. It does not allege a scientific defect.

The production vocabulary has no `supported` finding tier, generic LLM hypothesis output, or numerical finding probability.

## 5.6 Five-part Finding admission

A candidate becomes a Finding only when all five conditions hold.

### 5.6.1 Direct entailment

The exact, bounded problem follows from observed computation, artifacts, report text, and eligible authoritative semantics. It is not merely common, plausible, suspicious, or worth checking.

### 5.6.2 No reversing unknown

No material unknown or conflict could reasonably reverse the exact conclusion. Unknown orientation, scale, population, sample identity, timing, denominator, comparison, or another premise forces a question, conditional concern, disclosure, or abstention.

### 5.6.3 Exact detector applicability

The operation, package behavior, version, data type, scientific construct, domain, and evidence form fall inside the manifest. Only validated or publication-grade detector versions may admit Findings.

### 5.6.4 Finite counterevidence complete

Every applicable manifest check has been performed. A decisive unavailable source blocks admission. Counterevidence may suppress the candidate, limit its wording, or change the assessment type.

### 5.6.5 Bounded wording and deterministic replay

The statement says only what was established. It does not infer an unproved bias direction, bias magnitude, biological truth, invalidity of the entire paper, or whether a replacement analysis would change the conclusion. All cited sources resolve, and the decision replays from the semantic lock without Claude.

The operational test is:

> Could a knowledgeable scientist accept every recorded fact and still reasonably deny the exact sentence proposed as a Finding?

If yes, it is not demonstrated.

## 5.7 Model-derived semantic inputs

A model-derived assertion may be a material Finding premise only when it extracts explicit source meaning, cites an exact source span, is independently checkable, passes a non-model verification, and uses the correct authority scope.

Implicit model interpretations require corroboration from task text, metadata, runtime evidence, or the scientist. Self-reported confidence never changes eligibility.

## 5.8 Finite counterevidence protocol

“Complete” means every detector-declared finite check was performed for available evidence. It does not mean no conceivable objection exists.

Each check specifies:

- when it applies;
- sources to inspect;
- whether unavailability blocks a Finding; and
- whether discovered counterevidence suppresses, bounds, or changes the assessment type.

Examples include formula expansion, upstream encoding, package defaults for the recorded version, reverse orientation, report qualification, prior filtering, and authoritative scientist answers.

The controller owns completion. A model may only extract explicit meaning from a bounded source already selected by the check, and that extraction requires independent verification.

## 5.9 Root-cause grouping

One root assessment item should contain all graph-reachable manifestations. The canonical grouping key combines detector identity, causal root, and violated semantic dimension. Text similarity is insufficient.

The root lists affected claims, artifacts, models, and decisions with relationship paths. Reports may collapse descendants but cannot repeat them as independent Findings.

## 5.10 Future issue classes

The known detector families are not exhaustive. Version-one open-world behavior consists of preserving:

- unsupported operations;
- unknown and conflicted semantics;
- opaque or unavailable evidence;
- parser and detector coverage gaps; and
- uninspected paths.

New issue classes arise from benchmark failures, scientist reports, or methodological review, then receive explicit logic, applicability, counterevidence, fixtures, evaluation, and maturity. A production open-ended LLM “find anything suspicious” pass is prohibited.

Research experiments may use clearly isolated `x-*` records outside production reports and counts. They cannot self-promote into Findings.

## 5.11 Coverage contracts

Each detector defines covered, partially covered, not covered, and not applicable conditions. Actual coverage is calculated from operations, package versions, semantic availability, data identity, and execution evidence.

A result exposes unsupported constructs, absent prerequisites, decisive unavailable evidence, and wording limitations. Absence of a Finding is meaningful only within this envelope.

## 5.12 Maturity model

### Experimental

Maintainer review and the required positive, verified-good, hard-negative, ambiguity, unsupported-path, and counterevidence fixtures are required. Experimental detectors cannot emit Findings.

They may emit questions, conditional concerns, disclosures, and development diagnostics.

### Validated

Promotion requires a software-maintainer decision, a qualifying cross-provider agent adjudication panel, all non-negotiable safety gates, held-out problem-level evaluation, and a public qualification report. The initial reference panel uses Claude Code with Claude Opus 5 and Codex with GPT-5.6 Sol, with exact identities pinned per review.

Validated detectors may admit narrowly bounded Findings inside the evaluated applicability envelope.

### Publication-grade

Publication-grade promotion adds broader implementation and package-version evidence, an independently assembled corpus or external replication, repeated qualifying adjudication, maintenance and rollback obligations, and continuing regression monitoring.

Publication-grade detectors follow the same Finding admission rule and wording ceiling as validated detectors.

### Review-basis disclosure

Every maturity record identifies `agent_panel`, `mixed_panel`, or `human_panel`. Agent-only qualification is not described as human expert review. Optional human review is retained separately rather than implied by maturity.

Maturity belongs to one detector version and applicability envelope, not an entire parser, package, scientific method, or domain. Emergency demotion is immediate after a false accusation or qualification defect.

## 5.13 Detector testing

Every detector includes:

- positive fixtures;
- independently verified-good negative fixtures;
- ambiguous fixtures requiring a question or conditional concern;
- unsupported-path fixtures;
- counterevidence fixtures that suppress or bound a candidate;
- deterministic replay tests;
- source-location tests;
- root-grouping tests; and
- wording snapshots that reject conclusions stronger than the evidence.

## 5.14 Initial detector families

Initial families cover:

- claim/result and uncertainty agreement;
- outcome-guided model, threshold, filter, or subgroup selection;
- population, estimand, comparison, or adjustment mismatch;
- measurement or error-model non-identification;
- denominator, background, or control-set mismatch;
- omitted batch, nuisance, repeated-measures, kinship, site, or dependence structure;
- group-specific residual patterns hidden by aggregate fit;
- unsupported orientation, scale, timing rule, or scientific invariant;
- ignored missingness, transport, calibration, measurement, or uncertainty; and
- incomplete computational lineage.

A detector may demonstrate a narrow implementation fact without establishing downstream bias. For example, it may establish that a contract-required batch term is absent without claiming that batch confounding changed an estimate.

## 5.15 Causal reasoning

Causal review is layered rather than reduced to one regression formula or one DAG.

### 5.15.1 Claim intent

Every material claim is classified as `descriptive`, `associational`, `predictive`, `causal`, or `ambiguous` from explicit wording and context. A statistical method does not establish causal intent. Material ambiguity becomes a scientist question rather than the more accusatory interpretation.

### 5.15.2 Target estimand

Every explicitly causal claim has a typed estimand contract covering target population, unit of analysis, treatment or exposure, treatment strategies or versions, outcome, counterfactual comparison, effect measure and scale, time zero, outcome horizon, total/direct/indirect or other effect type, censoring and competing events, interference, and transport relationship as applicable.

The target estimand is separate from the implemented model. This allows a detector to establish a narrow mismatch such as five-year risk difference versus one-year odds ratio without declaring the entire paper invalid.

### 5.15.3 Identification contract

The identification layer records randomization or another strategy, adjustment set, estimand-scoped covariate roles, temporal ordering, exchangeability, positivity, consistency and treatment versions, measurement or calibration assumptions, selection, censoring, and transport assumptions. Roles include confounder, mediator, collider, post-treatment variable, precision variable, instrument, proxy, selection variable, and unknown.

A role is never global. The same variable may be a confounder for one estimand and a mediator, precision variable, or irrelevant variable for another.

### 5.15.4 Optional causal structure

A graph or equivalent relational assertions may be absent, partial, or complete. It declares one scope:

- `partial_open_world`: omitted edges are unknown;
- `complete_for_named_query`: the structure is asserted sufficient for one named treatment-outcome-estimand query; or
- `closed_world`: omitted relevant edges are asserted absent.

`partial_open_world` is the default. A graph-dependent detector cannot treat missing edges as evidence of absence.

### 5.15.5 Permitted conclusions without a full graph

A validated detector may establish a bounded issue without a full graph when authoritative records directly support it, for example:

- a causal claim is inconsistent with an explicitly associational contract;
- the implemented population, contrast, scale, time zero, or horizon differs from the target estimand;
- the model conditions on a variable explicitly declared as a mediator while the target is the total effect;
- a required adjustment variable in the authoritative contract is absent;
- an explicitly post-outcome variable is used for baseline selection; or
- an explicit path in a supplied graph is open under the implemented adjustment set.

The detector may not infer bias direction, magnitude, or biological truth unless separately established.

### 5.15.6 Required abstention

Without authoritative structure, a detector may not demonstrate adjustment-set sufficiency, all backdoor paths blocked, confounder or collider status based on biological intuition, existence of an unmeasured confounder, noncausality of an association, or bias direction. It asks a MaterialQuestion, creates a ConditionalConcern, discloses the coverage limit, or abstains.

Claude may extract explicitly stated causal relations from exact source spans. Model-invented causal structure, including Claude-generated causal structure, conventional domain knowledge, or model confidence cannot become a material Finding premise without scientist or authoritative-source corroboration or a validated narrowly bounded invariant.


## 5.16 Capability matrix

Public support claims are generated from parser, profile, detector, qualification, and version manifests. Each capability entry identifies exact language, package, operation, tested version, inferred compatibility, semantic coverage, detector maturity, qualification basis, strongest permitted output, gaps, and abstention conditions. Domain-wide support or validation is never inferred from a component entry.

## 5.17 Domain profiles


A domain profile packages operation signatures, semantic roles, scientific invariants, detector implementations, fixtures, and validation evidence. Capability is reported independently for syntax support, operation extraction, semantic coverage, detector availability, held-out validation, and publication-grade maturity.
