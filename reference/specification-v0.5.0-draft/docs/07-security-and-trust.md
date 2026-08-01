# 7. Security, trust, and authority

## 7.1 Security posture

sc-referee inspects projects that may contain executable code, large data, external references, generated reports, package definitions, and text capable of influencing a language model. Project content may be malformed, accidentally destructive, or adversarial.

Claude's freedom to investigate is not permission for repository-authored code to execute or access the network. Safe inspection, auditor-owned verification, dependency reconstruction, project-code execution, and external retrieval are separate privilege classes.

## 7.2 Trust boundaries

The principal domains are the scientist or operator, organization-managed policy, user invocation policy, untrusted project content, fallible model-assisted layer, deterministic core, controller network client, audit-owned dependency environment, restricted execution sandbox, external package and information sources, benchmark runner, and generated audit outputs.

The benchmark runner may know answers; the production project and audit agent must not.

## 7.3 Authority model

| Fact type | Primary authority | Notes |
|---|---|---|
| Intended scientific meaning | Scientist or explicit task instruction | May conflict with realized execution |
| Executed source path | Runtime evidence, then static source evidence | Static source may include unexecuted branches |
| Produced artifact value | Verified artifact or runtime observation | Identity strength affects what can be established |
| Report wording | Exact report text | Clarification does not rewrite history |
| Metadata definition | Explicit dictionary or authoritative metadata | Conflicts remain visible |
| Causal assumptions and intended graph | Scientist, protocol, or authoritative source | The auditor evaluates consistency; it does not certify nature |
| Model interpretation | Proposed evidence | Literal extraction may become eligible after non-model verification |
| Detector conclusion | Deterministic detector and admission kernel | Bounded by manifest, evidence, and graph scope |

The system does not use one global authority rank that overwrites every fact type.

## 7.4 Threat model

### Prompt injection in project content

README files, comments, notebook markdown, data values, reports, logs, filenames, package instructions, and retrieved webpages are evidence, never instructions. They cannot change tools, deadlines, network access, execution privilege, answer-key isolation, or Finding admission.

### Accidental or malicious code execution

Static parsing does not import project Python modules, source R files, execute notebook cells, render executable documents, evaluate workflow definitions through unrestricted language execution, load arbitrary pickle or executable workspace objects, or run shell substitutions.

### Path and filesystem escape

The controller defends against symlink escape, path traversal, special files, writes outside audit-owned roots, source modification, and recursive traversal through generated or mounted trees. External roots require policy.

### Network exfiltration and mutable evidence

Claude and the controller may retrieve external information under the accepted network policy. Every material controller retrieval is provenance-recorded and cached when possible. Repository-authored code has no network unless explicitly authorized. No repository instruction may enable it. Credentials are never copied into audit records.

### Dependency installation and supply chain

Standard mode may reconstruct declared dependencies automatically, but only in an isolated audit-owned environment. Installation hooks are untrusted code. The controller does not mutate the user's environment, use `sudo`, install system packages, infer arbitrary packages from failed imports, or install the local project automatically. Sources, versions, lock precision, and approximation are recorded.

### Resource exhaustion and deadline evasion

The controller and sandbox limit elapsed time, CPU, memory, process count, file descriptors, output, disk writes, data reads, and generated-file expansion. Model, network, queue, installation, and sandbox latency all count toward the same user-visible hard deadline.

### Secret exposure

The controller should redact likely secrets from model packets, logs, reports, external requests, and bundles. Project-code execution uses a minimal environment. Authentication use may be recorded as a Boolean or policy class; secret values are never retained.

### HTML and report injection

All project and external text in HTML is escaped. Interactive components do not execute project-provided HTML, JavaScript, SVG scripts, or event handlers.

### Provenance tampering

Record digests, source hashes, external-evidence snapshots, semantic locks, detector digests, and bundle manifests protect against accidental mutation. Content identity does not establish scientific truth.

### Benchmark answer leakage

The evaluation harness provides task text and allowed staged data but excludes answers, graders, adjudication notes, gold workflows, and detector labels. Production packages do not import answer-side resources.

## 7.5 Automatic safe inspection

Automatic safe inspection permits ordinary text and safe structured reads, syntax parsing, file metadata, schemas, manifests, non-executable workflow declarations, bounded archive listing, permitted digests and fingerprints, and safe serialized-format metadata. It does not imply complete understanding of dynamic behavior.

## 7.6 Auditor-owned verification

Auditor-owned verification uses code shipped and versioned with sc-referee. It may verify existing values or identities, but does not import project modules, execute project callbacks, fit alternatives, select models, or modify analysis source. It runs under resource and write limits.

## 7.7 Project-code execution sandbox

Project-authored code requires explicit user authorization. The sandbox has a read-only project mount, dedicated writable run directory, minimal environment, no project-code network unless separately authorized, process and resource limits, captured output, logged command and environment, and termination on policy or deadline violation.

If the environment cannot enforce the policy, the controller abstains rather than running unsandboxed.

## 7.8 Dependency environment

Dependency reconstruction occurs outside the repository in a content-addressed audit cache. It may use declared lockfiles or dependency metadata. Exactness is recorded separately from successful installation. Unpinned resolution is approximate. Local editable installs, arbitrary Git sources, local path dependencies, and system packages require a stronger explicit authorization path and are not standard automatic behavior.

## 7.9 Network policy

The host controls Claude's actual network tools. sc-referee does not impose a domain allowlist on Claude. Controller retrievals create `ExternalEvidence` records with purpose, requested and resolved URI, time, redirects, authentication use, content identity, cache state, version label when available, and reproducibility effect.

An external scientific statement may inform context or a question. It becomes a material Finding premise only through an accepted evidence channel, such as exact independently verified package semantics, explicit protocol requirements, scientist confirmation, or a validated bounded invariant.

## 7.10 Read and write policy

The core writes audit records, caches, isolated environments, rendered reports, sandbox outputs, and temporary parser artifacts only under configured audit-owned locations unless higher policy permits another path. It never modifies analysis source as part of the audit.

## 7.11 Cache and storage privacy

Source-derived parse trees, strings, formulas, variable names, semantic records, model packets, detector output, and report fragments remain project-local. Global cache entries are limited to public or tool-owned material and isolated dependency environments. SQLite is a local generated index, not an authoritative or shared scientific-information service.

## 7.12 Data handling

The system is not itself a HIPAA, GDPR, or institutional compliance certification. It supports responsible deployment through local or compliant-agent operation, data-minimized packets, configurable exclusion and redaction, source excerpts rather than bulk copies, explicit external retrieval records, and logs of content classes sent to a model.

Raw values are omitted from model packets unless necessary to resolve a material question and permitted by policy. Schemas, summaries, and metadata are preferred.

## 7.13 Opaque trust dimensions

Opaque operations and external artifacts represent trust independently for content identity, producer identity, execution provenance, scientific semantics, numerical correctness, calibration or validation, and reproducibility. A scientist may accept an opaque tool while the auditor still discloses what it did not inspect.

## 7.14 Model trust

Model outputs are fallible evidence proposals. Mitigations include bounded packets, typed schemas, source verification, deterministic extraction of literals, authoritative resolution of ambiguity, no open-ended issue search, and no direct path from model prose or invented causal structure to a Finding.

Hidden model reasoning is never required to understand a final audit result.

## 7.15 Policy precedence

```text
organization-managed policy
  > explicit user invocation policy
  > project configuration explicitly approved by the user
  > package defaults
  > repository-content heuristics
```

Repository content may suggest evidence targets but cannot elevate permissions.

## 7.16 Security acceptance tests

Tests cover prompt injection, symlink escape, path traversal, archive expansion, unsafe serialization, command injection, dependency-install hooks, local-project installation attempts, resource exhaustion, deadline evasion, unauthorized project-code network use, controller retrieval provenance, secret redaction, HTML injection, source mutation, answer-key leakage, and stale or forged source hashes.
