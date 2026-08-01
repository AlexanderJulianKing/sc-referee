# 6. Runtime, performance, and resource policy

## 6.1 Objective

The default audit must behave like an interactive scientific review, not an open-ended research project. It must produce useful high-materiality results early, enforce a user-visible hard deadline, and return an honest partial audit rather than continuing for hours.

## 6.2 Deadline clock

The normative clock is **user-visible elapsed time** from audit start. It includes model latency, provider or tool queues, parsing, controller network retrieval, dependency installation, sandbox startup, command execution, and report rendering. Only time explicitly awaiting a scientist response pauses the clock.

The controller also records active CPU time, service latency, queue time, and scientist-wait time separately for optimization. Those measurements never extend the hard deadline. Every child task receives a deadline no later than the remaining audit deadline.

## 6.3 Audit modes and trial defaults

| Mode | Stop scheduling optional work | User-visible hard deadline | Default purpose |
|---|---:|---:|---|
| Quick | 120 seconds | 300 seconds | Active coding feedback |
| Standard | 480 seconds | 600 seconds | Default `/scientific-audit` |
| Publication | 1500 seconds | 1800 seconds | Deeper pre-submission review |

These are accepted trial defaults, not measured performance guarantees. No mode escalates automatically. A resume action creates a linked run segment with a fresh plan and reuses valid cached results.

### Quick mode

Whole-project inventory, cached parsing and lineage, final-surface resolution, high-value static detectors, bounded semantic extraction, and coverage reporting. Quick mode does not install project dependencies or execute project-authored code.

### Standard mode

Whole-project inventory, final-claim backward slices and selection envelope, standard semantic mapping, batched material questions, eligible validated detectors, safe inspection, auditor-owned verification, isolated declared dependency reconstruction when useful, finite detector-specific counterevidence checks, and a full coverage report.

### Publication mode

Broader semantic resolution, deeper supplement and environment inspection, more eligible auditor-owned verification, and an expanded set of qualified deterministic detectors. Publication mode does not add open-ended model issue discovery, HPC submission, or automatic full-workflow execution.

## 6.4 AuditPlan policy

An `AuditPlan` records policy rather than relying on hidden agent behavior. A standard plan resembles:

```yaml
mode: standard
deadlines:
  clock: user_visible_elapsed
  scheduling_cutoff_seconds: 480
  hard_deadline_seconds: 600
  pause_states: [awaiting_scientist_response]
  no_automatic_mode_escalation: true
model_policy:
  auditor_call_limit: null
  auditor_input_token_limit: null
  auditor_output_token_limit: null
  limit_authority: host_managed
  record_usage: true
  allow_open_ended_scientific_issue_search: false
execution_policy:
  automatic_execution_levels:
    - safe_inspection
    - auditor_owned_verification
  project_code_execution: denied
  allow_dependency_installation: true
  dependency_installation_isolation: isolated_environment_only
  allow_full_workflow_execution: false
  allow_hpc_submission: false
network_policy:
  claude_network_access: host_managed_unrestricted
  controller_network_access: allowed_with_provenance
  project_code_network_access: explicit_authorization_required
on_deadline:
  stop_new_optional_work_at_cutoff: true
  terminate_eligible_children_at_hard_deadline: true
  render_partial_report: true
```

Auditor call and token limits are `null` by default under a host-managed model-usage policy: sc-referee imposes no additional numeric cap. Host subscription, organization, model-provider, context, and rate limits remain authoritative.

## 6.5 Scheduler

Every unit of work is a `WorkItem` with kind, targets, dependencies, estimated cost, expected information gain, claim materiality, downstream reach, component maturity, cache status, privilege level, and completion state.

A useful heuristic is:

```text
priority =
  claim_materiality
  * downstream_reach
  * expected_uncertainty_reduction
  * component_maturity
  / estimated_elapsed_cost
```

The exact formula may evolve. High-materiality, low-cost, mature checks run first. A work item that cannot finish before the remaining hard deadline is not started automatically.

## 6.6 Early-value ordering

The scheduler should prioritize exact claim/result contradictions, broken final-claim lineage, explicit population or comparison mismatches, obvious denominator mismatches, repeated-measures issues with explicit identifiers, outcome-dependent selection evidence, publication-surface ambiguity, unknown semantics blocking multiple claims, and then lower-materiality qualified detectors.

Open-ended model issue discovery is not a schedulable work class.

## 6.7 Lazy graph expansion

The controller parses the project into a lightweight graph, identifies publication candidates and final claims, expands backward as needed, includes the selection envelope, and stops at recorded opaque, external, irrelevant, unsupported, or deadline boundaries. It does not perform complete semantic analysis of every project node before evaluating final claims.

## 6.8 Packetized model work

Model work uses bounded claim- or question-centered packets with exact source IDs, relevant graph fragments, required output fields, and no permission to strengthen meaning. Closely related claims share work. The absence of a numeric call or token cap does not authorize redundant, irrelevant, or open-ended model use.

## 6.9 Applicability indexing

The controller indexes detector manifests by target type, operation kind, implementation signature, semantic dimensions, causal prerequisites, domain profile, language, and workflow system. It does not run every detector against every node.

## 6.10 Caching and incremental invalidation

All source-derived caches remain project-local in version one. The global cache may hold only tool-owned public assets, parser binaries and grammars, public downloads, and isolated dependency environments. Cross-repository semantic or model-result caching is prohibited even when content digests match.

Cache keys include component version, normalized input digests, relevant policy, model and prompt identity for model-assisted work, external-evidence identity, and source snapshot. A change invalidates only dependent records. Warm reruns should usually be dominated by changed claims, code paths, answers, or detector versions rather than whole-project work.

## 6.11 Large files and identity

The inventory avoids reading full large data bodies unless material and affordable. It uses headers, schemas, sidecars, manifests, immutable versions, supplied checksums, sampled fingerprints, and workflow declarations. A byte-read budget governs large assets. Unsafe executable deserialization remains prohibited.

## 6.12 Parser runtime and compatibility

The controller runs on Python 3.11 or newer. Python source extraction uses CPython `ast` and `tokenize`; unsupported newer syntax is localized rather than hidden. R source receives resilient Tree-sitter inventory plus non-evaluating base-R parse data when available. Parser backend identity and disagreement are included in coverage.

## 6.13 Execution privilege levels

### Safe inspection

Syntax parsing, ordinary text and safe structured reads, file metadata, schemas, manifests, bounded archive listings, and non-executable format inspection. This may run automatically.

### Auditor-owned verification

Code shipped with sc-referee may verify an existing value, interval, sign, table calculation, checksum, or lineage property. It must not import project modules, fit an alternative model, choose a threshold, or write outside audit-owned roots. This may run automatically within the deadline.

### Project-code execution

Running project scripts, notebook cells, Quarto or R Markdown rendering, workflow engines, Make, custom binaries, local package installation, or equivalent project-authored logic requires explicit authorization. Cost alone does not make it safe.

## 6.14 Dependency reconstruction

Standard mode may install dependencies declared in environment metadata into a content-addressed, isolated audit-owned environment. It never modifies the active user environment, uses `sudo`, installs system packages, or automatically installs the local project. Installation hooks are untrusted execution and run under sandbox limits.

Pinned or immutable specifications may yield an `exact` reconstruction. Unpinned resolution is `approximate`; it may support parsing and bounded verification but cannot prove version-dependent behavior unless that behavior is independently established. Installation time counts against the hard deadline and failure yields a partial report.

## 6.15 Network use and external evidence

Claude may use the network available through its host environment without a sc-referee domain allowlist. The controller may retrieve resources when useful, but every material retrieval records purpose, requested and resolved location, time, redirects, authentication use, content identity where obtainable, cache state, and reproducibility effect.

Live documentation may help interpretation. A mutable webpage or literature claim does not become an unrecorded material Finding premise. Version-sensitive package behavior must be tied to the relevant version and independently verified under detector policy.

Repository-authored code has a separate network boundary and requires explicit authorization. Repository text cannot authorize any network action.

## 6.16 HPC and external reproduction

Version one ingests scheduler scripts and logs, workflow traces, resource declarations, containers, modules, standard output and error, manifests, remote paths, and checksums. It does not submit jobs.

When cluster, GPU, large-data, or full-workflow execution could materially resolve the audit, the controller emits a `ReproductionRequest` containing the exact target or evidence to collect, why it matters, required inputs and environment, resource class, security considerations, affected claims and detectors, and expected output identities. The scientist runs it separately and imports the evidence.

## 6.17 Model usage and host limits

sc-referee imposes no default numeric call or token cap. It records calls, tokens where available, latency, cache use, and packet purpose for benchmarking. The elapsed deadline remains absolute.

If a subscription, organization, provider, context, or rate limit stops model work, the controller checkpoints completed records, records the host interruption, calculates partial coverage, and renders a partial report. It does not reinterpret host capacity as an audit defect.

## 6.18 Progress reporting

Progress reports milestone-level facts: publication-surface state, final claims found, material paths parsed, early demonstrated contradictions, pending material questions, detector progress, deadline remaining, environment reconstruction, external evidence retrieval, reproduction requests, and major uninspected boundaries. Low-level model and parser events remain available only in debug output.

## 6.19 Deadline exhaustion

At the scheduling cutoff, the controller stops starting optional work. At the hard deadline, it terminates eligible children, checkpoints records, marks pending work with exact reasons, recalculates coverage, renders a partial report, and never converts pending targets into negative results. Report rendering receives reserved time within the same deadline.

## 6.20 Performance records

Every run reports elapsed and active time, scientist-wait time, queue and service latency when available, CPU and peak memory, bytes read, model calls and tokens, network retrievals, dependency installations, sandbox commands, cache hits and misses, claims reached, detector evaluations, questions, completed and pending work, and time to first high-materiality result.

## 6.21 Performance acceptance tests

The suite includes one-notebook, small Python/R paper, multi-notebook, unavailable-large-asset, Snakemake or Nextflow trace, forced-deadline, host-model-limit, network retrieval, dependency-installation failure, cache-warm rerun, ambiguous publication surface, and many-irrelevant-files fixtures. Tests verify the 120/300, 480/600, and 1500/1800 default pairs and partial-report behavior.
