# ADR-0017: Make the minimum proud product evidence-first and defer project-code execution

- **Status:** Accepted
- **Date:** 2026-07-29
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None
- **Related requirements:** SA-FR-047–049, SA-FR-091, AC-28, AC-31–33, AC-49, AC-58

## Context

The v0.5 architecture is static-first and makes selected reproduction optional for an individual
audit. It nevertheless places a rootless OCI project-execution backend and isolated dependency
reconstruction in the implementation-foundation gate before detector development. In practice,
that sequencing makes an optional and unusually security-sensitive capability a prerequisite for
the useful product.

That is the wrong boundary for the first production-quality release. The primary product is an
evidence compiler: it inspects a scientific workflow and its existing inputs, outputs, reports,
metadata, logs, and provenance; localizes demonstrated inconsistencies; and preserves everything
else as an unknown or coverage limitation. It need not rerun the workflow to do that work.

Full reproduction is also routinely impractical. Scientific data may be remote, controlled, or
many terabytes in size, and a workflow may require a cluster, licensed software, specialized
hardware, or days of computation. Requiring a complete rerun would exclude precisely the projects
for which a bounded evidence audit is most valuable.

Accepted ADR-0013 and ADR-0014 and schemas v0.13.0 and v0.14.0 remain valid historical baselines.
They define how project execution must be represented if it is attempted. Deferred ADR-0015 and
ADR-0016 describe additional closure and trusted-admission work needed before sc-referee itself
could safely offer that capability. None of those records or safety requirements should be
weakened or silently reinterpreted.

## Decision

### 1. Define an evidence-first minimum proud product

The minimum proud product (MPP) MUST perform a useful audit without executing project-authored
code. Its production audit, replay, reporting, detector, and skill paths MUST remain useful when
project execution is unavailable, unaffordable, or inappropriate.

The MPP MAY run sc-referee-owned deterministic operations, including parsers, schema validators,
bounded metadata readers, report rendering, replay, and narrowly specified calculations over
admitted data. Such operations MUST NOT import, evaluate, source, install, or invoke code from the
audited project.

The MPP MUST NOT claim that a workflow ran, that an output was reproduced, or that dynamic
semantics were verified unless those facts are supported by admitted execution evidence. Missing
execution limits only conclusions that depend on execution; it does not invalidate the rest of an
audit.

### 2. Make large-data inspection explicitly bounded

Every operation that may read scientific data MUST obey an explicit byte, record, time, or
resource budget. The controller MUST distinguish:

- a full digest or exact calculation over all required bytes;
- an immutable external identity or manifest supplied by an evidence source;
- a labeled bounded fingerprint, sample, summary, or metadata-only inspection; and
- unavailable or unidentified data.

A bounded fingerprint, sample, declared manifest, or aggregate MUST NOT be represented as a full
content digest or exact verification. When an exact calculation cannot complete within its
declared budget, the dependent premise remains unknown; a partial calculation MUST NOT masquerade
as the requested exact result. Large or unavailable data MUST narrow only dependent lineage,
coverage, and detector conclusions.

No universal size threshold is chosen here. Budgets remain explicit policy inputs so tests can use
small limits and deployments can select appropriate limits without changing evidence meaning.

### 3. Treat existing and imported execution as evidence, not authority

The MPP MAY inspect existing logs, traces, output artifacts, environment manifests, scheduler
records, and externally produced execution records. It MAY emit an inert `ReproductionRequest`
for a human, CI system, HPC operator, or coding agent when additional execution would resolve a
material unknown.

Repository text cannot authorize that execution. A request does not launch anything. Imported
records retain their actual origin and identity grade and do not become controller-observed facts,
clean-control evidence, or Finding premises merely because they validate structurally. Runtime-
dependent qualification or audit conclusions require independently sufficient runtime evidence;
otherwise they remain unqualified or unknown.

### 4. Move the built-in executor beyond the MPP

For the `0.6.0` architecture and implementation sequence:

- a built-in project-code executor is not an MPP feature or detector-foundation gate;
- isolated dependency installation for project execution is likewise post-MPP;
- AC-49 remains a safety invariant: if project execution is ever offered, it is denied without a
  qualifying rootless OCI backend and has no restricted-subprocess fallback;
- accepted v0.14 execution code may remain disabled and synthetic-test-only, but it MUST NOT be
  advertised as a production MPP capability; and
- ADR-0015 and ADR-0016 are deferred with the execution adapter. They must be resolved,
  or explicitly superseded by equally conservative decisions, before any production launch path
  is enabled or execution is admitted as a clean-control premise.

This changes implementation sequencing, not the meaning of an accepted record. It supersedes the
v0.5 implementation-foundation requirement that rootless OCI capability and isolated dependency
reconstruction exist before detector implementation. It does not supersede the conditional
security rule in ADR-0033: any future project-authored execution still requires a qualifying
rootless OCI backend.

### 5. Keep qualification fail closed

This ADR does not weaken the current BenchmarkFixture schema or manufacture clean execution
evidence. Existing qualification rules continue to apply to existing fixture kinds. Small
qualification fixtures may use independently produced and verified execution evidence without
requiring sc-referee to execute the audited project itself. A later schema ADR is required if
experience shows that a distinct, fully static proof basis should qualify a fixture currently
defined to require clean execution.

Detector work may proceed before the built-in executor, but no detector is promoted and no
Finding is emitted until its actual schema-valid qualification obligations are satisfied.

## Alternatives

### Keep the rootless executor as a detector-foundation gate

Rejected because it delays the central audit capability behind a hard security problem and makes
large, remote, proprietary, and HPC workflows appear less auditable than they are.

### Remove project execution permanently

Rejected because selected reproduction can later resolve dynamic lineage, environment, and
runtime premises that static evidence cannot establish.

### Treat samples or successful process exit as reproduction

Rejected because a sample does not establish an exact whole-data result and successful execution
does not establish scientific correctness.

### Relax execution safety to obtain an earlier demo

Rejected because a subprocess, container availability flag, copied capability record, or user
consent cannot establish the isolation and evidence premises required for untrusted code.

## Acceptance evidence required

1. Production audit, replay, report, detector, and skill tests prove that project-authored code is
   never imported or invoked.
2. An audit with a deliberately tiny data-read budget completes with useful independent evidence,
   labels the limited identity or inspection precisely, and localizes the resulting unknown.
3. Tests prove that a bounded fingerprint or incomplete calculation cannot be promoted to a full
   digest, exact result, Finding premise, or global correctness claim.
4. Existing logs, outputs, manifests, and external execution evidence can be inspected without
   being upgraded to controller-observed execution or launch authority.
5. A `ReproductionRequest` remains inert, carries no scheduler or authorization authority, and is
   optional rather than a prerequisite for completing the audit.
6. The public MPP capability matrix and documentation do not claim built-in project execution,
   clean reproduction, or unrestricted large-data verification.
7. The task board prioritizes bounded evidence acquisition, domain-neutral detectors, analysis
   surfaces, qualification, and real-corpus validation ahead of the optional execution adapter.

## Consequences

- The next implementation work returns to the core auditor rather than schema v0.15.0 execution
  closure.
- Projects with enormous or unavailable datasets can still receive a useful, explicitly partial
  audit of inspectable claims, code, metadata, inputs, outputs, and lineage.
- Some dynamic behavior, environment effects, and exact numerical reproduction remain unknown.
- A future execution adapter remains possible, but it is a separately gated capability rather
  than a hidden prerequisite for the product.
- No public schema changes on acceptance. Accepted schema packages through v0.14.0 remain
  immutable.

## Acceptance record

Accepted by the project owner on 2026-07-29 as recommended, with no coordinated schema release.
This acceptance changes the `0.6.0` architecture and implementation sequence. It does not grant
project-execution authority, reinterpret an accepted v0.14.0 record, or add compatibility work for
an earlier public repository.

## Implementation record

| Change | Test evidence | Acceptance criterion |
|---|---|---|
| Hide the four post-MPP execution commands from ordinary product help while preserving direct synthetic entry points and fail-closed launch denial | `tests/test_execution_request.py::test_post_mpp_execution_commands_are_hidden_from_product_help`; `tests/test_execution_request.py::test_execute_authorized_cli_rejects_standalone_capability_before_runtime` | 1, 6 |
| Audit and replay a project containing a 10-billion-byte sparse data asset after only a 12,288-byte weak-fingerprint read; do not materialize or fully digest it; preserve independent parsing/Claim evidence; do not execute embedded project code | `tests/test_general_audit.py::test_enormous_data_asset_is_bounded_without_making_the_audit_useless` | 1, 2, 3 |
| Move executor work behind bounded evidence acquisition, the first real detector, and real-corpus validation while keeping clean-control admission fail closed | implementation plan, task board, completion matrix, schema-gap register, and release-gate audit | 4, 5, 6, 7 |

Remaining coverage is explicit. The sparse-file regression proves bounded I/O and evidence behavior,
not parsing of a real H5AD object or performance on a physical 10-billion-byte allocation. Existing
log/trace/output import is not yet broad, no production detector is qualified, and no real
answer-blind corpus has completed. The v0.14 execution closure and trusted-origin gaps remain
deferred rather than solved.
