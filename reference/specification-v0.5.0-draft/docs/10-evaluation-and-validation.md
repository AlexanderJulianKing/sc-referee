# 10. Evaluation and validation plan

## 10.1 Evaluation objective

Evaluation determines whether sc-referee identifies material root causes, localizes them, avoids false accusations on defensible workflows, asks useful questions, discloses coverage honestly, and completes useful work within budget.

Final-answer correctness is not a sufficient label. A workflow can be accidentally correct after invalid analysis, and a workflow can differ from a canonical implementation while remaining scientifically defensible.

## 10.2 GeneBench-based corpus

The public GeneBench-Pro package can seed stochastic workflow generation. The agent workspace contains only task text, staged data, and the permitted environment. Ground truth, grader code, reference answers, detector labels, and adjudication notes remain runner-side.

For each scientific problem:

1. generate many independent coding-agent workflows without answer access;
2. capture repository, notebook, report, outputs, environment, prompt, transcript, and execution evidence;
3. grade the final result outside the workspace;
4. cluster workflows by behavior and failure signature;
5. submit representative successful and failed workflows to the blind agent-review protocol;
6. preserve multiple defensible implementations and accidental-correct cases; and
7. construct executable, claim-traceable benchmark fixtures with explicit negative, positive, or ambiguous scope.

The production auditor has no dependency on answer-side records.

## 10.3 Agent adjudication is evidence generation, not an oracle

The benchmark labels are produced by coding agents because manual expert review is not assumed to be available. Agent reviewers can make scientific, statistical, and repository-inspection mistakes. Therefore, no individual model, provider, self-reported confidence score, or simple vote is treated as authoritative.

The initial dated reference pair is:

- Claude Code using Claude Opus 5 (`claude-opus-5`); and
- Codex using GPT-5.6 Sol (`gpt-5.6-sol`).

These names are a bootstrap configuration, not permanent normative constants. Every qualification run pins exact model, agent, prompt, tool, environment, and transcript identities. A later reference-model change creates a new protocol version and does not rewrite historical labels.

Agent-only adjudication is always disclosed as agent-only. It is never described as human expert review or human scientific endorsement. Human or mixed review may be added later and is represented separately. Correlated error across provider families remains possible; labels are versioned, challengeable evidence products rather than declarations of scientific truth.

## 10.4 Two-stage independent adjudication protocol

### 10.4.1 Reviewer calibration

Before participating in qualification, each exact agent configuration completes a calibration suite containing demonstrated positives, verified-good negatives, hard negatives, conditional cases, unsupported paths, and decisive counterevidence. Failure on a release-blocking calibration case disqualifies that configuration until the prompt, tools, or model configuration changes and the calibration suite is rerun.

Calibration success does not establish infallibility. It only prevents a known-broken configuration from entering the panel.

### 10.4.2 Stage 1: blind scientific review

A qualification case receives at least four isolated reviews. The minimum panel is four Stage-1 reviews:

```text
2 independent Claude Code / Claude Opus 5 contexts
+
2 independent Codex / GPT-5.6 Sol contexts
```

Each reviewer receives only the scientific task, data description, workflow source, report, generated outputs, and available execution evidence. Stage 1 hides:

- sc-referee output;
- detector identity and implementation;
- benchmark answer and grader result;
- answer-side adjudication evidence;
- other reviewers' outputs; and
- previous labels or discussions.

Each `AgentReview` records candidate root causes, exact source evidence, the narrowest demonstrable statement, plausible innocent explanations, affected claims, unresolved semantics, reviewed scope, and a transcript digest. Model confidence may be recorded for research but is marked ineligible for labeling.

### 10.4.3 Stage 2: fresh scientific adjudication

After Stage-1 records are frozen, the minimum Stage-2 panel consists of two fresh Stage-2 adjudications—one context from each provider family. They receive:

- the frozen Stage-1 rationales;
- reference analysis records;
- answer-side evidence and grader behavior;
- execution comparisons; and
- the structured case record.

Stage 2 still hides sc-referee output and detector identity. Its purpose is to adjudicate the workflow label, not to judge the detector. Each adjudicator must actively test the proposed root cause against innocent explanations and must identify any material dissent. Each must produce a falsification record naming the strongest innocent explanation, every premise that could reverse the label, and the evidence used to reject or retain those alternatives.

### 10.4.4 Stage 3: detector comparison

Only after the scientific label is frozen may fresh comparison agents or deterministic tools inspect sc-referee output. This separates benchmark truth construction from detector evaluation and reduces anchoring on the auditor's wording.

## 10.5 Conservative label admission

A demonstrated positive label requires all of the following; linked review records and per-provider participation counts must independently reconcile:

1. at least one matching Stage-1 root-cause review from each provider family;
2. Stage-2 cross-provider agreement on the same bounded root cause;
3. exact source references that resolve against the fixture snapshot;
4. deterministic checks of claim/output relationship, bounded entailment, and decisive counterevidence;
5. no unresolved material dissent; and
6. explicit exclusion of claims stronger than the established issue.

A majority vote is never sufficient. If one material interpretation could reverse the label and remains unresolved, the case is excluded from positive and verified-good sets.

## 10.6 Fixture taxonomy

### `verified_good_fixture`

A release-blocking false-accusation fixture requires:

- an immutable repository and data snapshot;
- clean-environment execution for GeneBench-sized fixtures;
- exact claim-to-output agreement;
- resolved Scientific Contracts for the declared scope;
- identified operations evaluated by the named detectors;
- completion of the full agent panel protocol;
- no material disagreement; and
- no known issue inside the declared claim, detector, operation, and issue-class scope.

It does not mean the entire workflow or scientific conclusion is globally correct.

### `scope_verified_good`

A real-world or HPC workflow may be verified only for named claims, paths, issue classes, operations, data identities, or execution boundaries. It supports targeted testing but cannot be presented as globally verified-good.

### `hard_negative_fixture`

A hard negative satisfies verified-good obligations while deliberately containing a pattern that superficially resembles an issue, such as an adjustment encoded through another term, repeated observations handled by upstream aggregation, a legitimate complete-case estimand, correct reference reversal, or an unconventional but valid denominator.

### Positive and ambiguous fixtures

A `positive_issue_fixture` contains an adjudicated bounded root cause. An `ambiguous_fixture` preserves unresolved scientific meaning, material reviewer disagreement, or insufficient evidence and must not be used as a positive or verified-good control.

When feasible, each scientific problem should have multiple materially different defensible implementations across packages, formulas, parameterizations, preprocessing orders, or estimators.

## 10.7 Root-cause labels

Each adjudicated positive records:

- first material divergence from a defensible analysis;
- issue class and exact source locations;
- required scientific premise;
- bounded demonstrable statement;
- affected artifacts and final claims;
- plausible innocent explanations examined;
- whether the final answer passed or failed;
- whether numerical insensitivity masked the error; and
- every independent review and material disagreement.

The evaluation unit is the root cause, not every downstream symptom.

## 10.8 Split and leakage strategy

Split by scientific problem or data-generating structure, not randomly by stochastic workflow. Public cases are development-only. Held-out problems support detector tuning; hidden or newly generated problems support final evaluation. Stochastic siblings from one problem are clustered for uncertainty estimation.

Core and production packages cannot import answer-side evaluation code. Workspaces omit ground truth and graders. Audit and evaluation caches are separated. Prompts and generated repositories are scanned for answer leakage. Agent-review prompts and transcript hashes are retained.

## 10.9 Primary metrics

### Safety

- workflow-level probability of any false Finding;
- detector-opportunity-level false-positive rate;
- Finding precision;
- false root-cause localization rate;
- conditional or unresolved cases incorrectly promoted to Findings;
- Findings whose wording exceeds the adjudicated bounded defect; and
- severity-stratified false accusations.

### Scientific utility

- recall of adjudicated material root causes;
- root-cause localization accuracy;
- affected-claim precision and recall;
- ConditionalConcern precision;
- MaterialQuestion resolution value; and
- counterevidence suppression and wording-bounding accuracy.

### Coverage honesty

- unsupported paths correctly disclosed;
- abstention distinguished from negative result;
- parser and detector gap accuracy;
- unknown-semantic propagation accuracy;
- final claims reached before budget exhaustion; and
- count consistency across assessment types.

### Reproducibility and performance

- normalized deterministic rerun equivalence;
- stable root grouping;
- correct incremental invalidation;
- source-reference resolution;
- active and user-visible elapsed time;
- model and agent usage;
- CPU, memory, bytes read, commands, and cache hits; and
- claims completed before the budget ceiling.

Uncertainty intervals must account for clustering by scientific problem or data-generating structure. Workflow-level and detector-target-level metrics are reported separately.

## 10.10 Detector maturity and Finding permission

Experimental detectors cannot emit Findings.

Validated and publication-grade detectors may both emit narrowly bounded Findings inside their qualification envelope, subject to the identical five-part admission rule. Publication-grade indicates broader implementation diversity, independently assembled or externally replicated evaluation, package-version maintenance, rollback policy, and continued regression evidence. It does not permit stronger Finding language.

Every maturity record discloses whether qualification was agent-only, mixed, or human. The capability matrix displays that basis alongside maturity.

## 10.11 Qualification safety gates

Before promotion beyond experimental:

1. no known high- or critical-severity false accusation may remain in release-blocking fixtures;
2. every discovered false accusation is fixed and added as a regression fixture;
3. no conditional, disputed, or insufficient-evidence case is admitted as a Finding;
4. verified-good, hard-negative, positive, unsupported, ambiguous, and decisive-counterevidence fixtures are included;
5. uncertainty is problem-cluster aware;
6. workflow-level and detector-target-level false-accusation metrics are reported;
7. public development cases do not qualify a detector;
8. unresolved agent disagreement is excluded rather than majority-voted;
9. publication-grade qualification includes an independently assembled corpus or external replication; and
10. the public qualification report includes sample counts, exclusions, agent configurations, disagreements, intervals, and review-basis disclosure.

Universal numeric cutoffs are deferred until the pilot corpus exists. A later ADR must set them before the first validated promotion. Zero observed false positives alone is not proof of zero residual risk.

## 10.12 Capability claims

A release publishes a machine-generated multidimensional capability matrix. Each entry names the domain, language, package, tested and inferred versions, operation forms, syntax coverage, operation extraction, semantic coverage, detectors, maturity, review basis, strongest permitted output, gaps, and abstention conditions.

The project does not publish a generic checked list of “supported domains.” One validated detector for one DESeq2 operation does not validate bulk RNA-seq as a whole.

The human audit report embeds the exact applicable capability-matrix slice so the scientist can interpret negative results and coverage without consulting a separate website.

## 10.13 Provenance export

Version one exports RO-Crate 1.3 containing the native audit bundle, HTML report, identity manifests, environments, detector manifests and qualification references, execution evidence, licensing, and authorship. Native records remain unchanged and canonical.

W3C PROV remains a planned mapping. It is added only when a concrete interoperability consumer justifies the additional maintenance and semantic mapping burden.

## 10.14 Continuous integration

CI runs schema validation, controller invariants, parser and detector fixtures, deterministic replay, security fixtures, verified-good and hard-negative workflows, report wording snapshots, capability-matrix generation, RO-Crate export validation, agent-adjudication protocol checks, and fixed-budget performance smoke tests. Larger scientific suites run on a schedule.

## 10.15 Runtime and policy evaluation

Every benchmark run records user-visible elapsed duration, active CPU time, queue and service latency when available, scientist-wait time, model usage, host-limit interruption, controller network retrievals, dependency reconstruction, sandbox commands, data reads, questions, final-claim coverage, cache hits, and whether cutoff and hard-deadline behavior produced a useful partial report.

The suite evaluates the accepted 120/300, 480/600, and 1500/1800 cutoff/deadline pairs without treating them as proven service guarantees.

## 10.16 Causal-contract evaluation

Causal detector fixtures separate claim intent, estimand mismatch, identification assumptions, covariate roles, implementation, and report wording. They include partial-open-world graphs, complete-for-query graphs, missing causal structure, explicit mediators and post-treatment variables, and multiple defensible causal specifications. Model-invented roles or edges must never create Findings.
