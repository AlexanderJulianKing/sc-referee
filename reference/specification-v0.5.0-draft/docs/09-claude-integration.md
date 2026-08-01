# 9. Claude Code and Claude Science integration

## 9.1 User invocation

The primary experience is:

```text
/scientific-audit
```

Proposed optional arguments:

```text
/scientific-audit --mode quick
/scientific-audit --mode publication --report manuscript/results.qmd
/scientific-audit --allow-project-execution <target>
/scientific-audit --resume <audit-run-id>
/scientific-audit --diff <previous-run-id>
```

The skill body should remain concise and delegate durable state, validation, scheduling, detection, and reporting to `sc-referee-core`.

The public project and CLI are named `sc-referee`; the Python import namespace is `sc_referee`. The slash command remains `/scientific-audit`.

## 9.2 Distribution model

The recommended distribution has two layers:

1. A Claude Code plugin containing the skill, bounded subagents, local MCP server configuration, optional hooks, and executable package metadata.
2. A standalone `sc-referee` CLI that remains usable without Claude Code.

Current Claude Code documentation describes directory-based `SKILL.md` skills that can be invoked directly as slash commands. Plugins can package skills, agents, hooks, and MCP servers. These implementation-facing claims MUST be rechecked against official documentation before release because the integration surface can change independently of the core architecture.

## 9.3 Proposed plugin layout

```text
scientific-audit-plugin/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── sc-referee/
│       ├── SKILL.md
│       └── references/
├── agents/
│   ├── workflow-mapper.md
│   ├── claim-extractor.md
│   ├── semantic-resolver.md
│   └── source-evidence-verifier.md
├── hooks/
│   └── hooks.json
├── .mcp.json
└── bin/
    └── sc-referee
```

The same core package must remain usable without the plugin.

## 9.4 Skill responsibilities

The skill MUST:

- display the scheduling cutoff, hard deadline, and execution privilege before work begins;

- start or resume an audit run;
- present mode, scope, execution policy, and budget;
- ask the controller for the next bounded work packet;
- route packets to the appropriate subagent or handle them inline;
- submit structured outputs through validation;
- present ranked material questions;
- record answers with authority scope;
- trigger semantic lock, detector execution, and reporting; and
- summarize results without strengthening machine-readable conclusions.

The skill MUST NOT search the project for unspecified scientific mistakes, ask a subagent to perform an open-ended scientific review, or turn a model-generated suspicion into a production assessment item. It MUST NOT manually maintain a second authoritative copy of audit state in conversation text.

## 9.5 Bounded subagents

### Workflow mapper

Resolves workflow relationships that deterministic parsers could not map. It receives bounded source fragments and parser results and returns proposed operation or lineage assertions.

### Claim extractor

Structures report claims, including uncertainty, comparison, population, scale, timing, and causal wording. It returns proposed `Claim` records.

### Semantic resolver

Proposes Scientific Contract dimensions and identifies material unknowns. It returns proposed assertions, conflicts, and candidate questions.

### Source-evidence verifier

Verifies that a structured extraction matches explicit wording in one bounded source span selected by the deterministic controller. It cannot search for new scientific issues, decide counterevidence completion, or admit or dismiss a Finding.

Subagents should receive only required tools and source packets. Scientific correctness must not depend on persistent subagent memory.

## 9.6 Typed tool API

The recommended interface is a local MCP server or equivalently typed subprocess protocol. Proposed tools:

```text
audit_start
audit_status
audit_get_work_queue
audit_get_work_packet
audit_submit_claims
audit_submit_assertions
audit_record_counterevidence_check
audit_record_answers
audit_lock_semantics
audit_run_auditor_verification
audit_record_external_evidence
audit_reconstruct_environment
audit_create_reproduction_request
audit_import_reproduction_evidence
audit_run_detectors
audit_render_report
audit_diff
```

Tools MUST use strict schemas, require an audit-run ID, be idempotent where practical, return record IDs and structured validation errors, reject source references outside the snapshot unless marked external, expose budget status, and keep large payloads in files or resources rather than tool responses.

The tool server MUST prevent the model from assigning observed-computation authority to a record that was not produced by a parser, artifact verifier, or runtime observer.

## 9.7 Standalone CLI

The CLI should expose the same state transitions:

```text
sc-referee init
sc-referee inventory
sc-referee parse
sc-referee claims
sc-referee questions
sc-referee answer
sc-referee lock
sc-referee reproduce
sc-referee detect
sc-referee report
sc-referee diff
sc-referee rerun
```

A single convenience command MAY orchestrate the deterministic portions:

```text
sc-referee audit --mode standard <project-root>
```

Model-assisted steps can be supplied by the plugin or another compatible provider. Locked audits must rerun without one.

## 9.8 Interactive question flow

The controller first searches task text, repository metadata, code, documentation, and existing answers. It then ranks unresolved questions and presents one compact batch, for example:

```text
Three answers could change the scientific assessment:

1. Does sample_id identify a biological donor, a library, or a sequencing lane?
   Affects: repeated-measures detector; claims 4, 7, and 9.

2. Is allele A the effect allele in both the association table and Figure 2?
   Affects: direction claim in the abstract.

3. Was the week-16 complete-case cohort the intended target population?
   Affects: population and missingness findings.
```

The scientist may answer, choose `unknown`, or defer. Deferred questions remain unknown and the audit continues.

## 9.9 Progress and interruption

The skill should report stage-level progress and early material results. It must not promise asynchronous completion. The user can interrupt, change scope, answer questions, or request a report immediately.

On interruption, the controller checkpoints and renders a partial report when requested.

## 9.10 Claude Science and notebook-first workspaces

The same skill and core CLI should work in a notebook or project workspace used through Claude Science. The architecture must not require Git, although Git metadata should be captured when present.

For notebook-first workspaces:

- markdown and code cells are distinct source records;
- cell IDs and execution order are preserved;
- saved outputs are evidence but may be stale;
- hidden state and out-of-order execution are lineage concerns; and
- the selected notebook or rendered export may be the publication surface.

## 9.11 Hooks

Hooks may enforce non-scientific behavior such as validating submitted records, preventing writes outside the audit directory, recording command completion, or reminding the skill to render at terminal states.

No scientific conclusion may depend on a hook firing. Hooks are convenience and policy enforcement, not the audit engine.

## 9.12 Tool permissions

The plugin SHOULD allowlist only the typed audit tools and exact bundled executables required by the skill. Arbitrary shell access should not be granted merely because the deterministic core is implemented in Python.

Selected execution permissions are controlled by the audit policy and sandbox, not by a free-form agent decision.

## 9.13 Version compatibility

The plugin manifest should declare tested Claude Code versions. The core CLI, record schemas, detector APIs, and plugin integration remain independently versioned.

Integration tests should verify skill discovery, direct invocation, MCP startup, tool schema compatibility, subagent restrictions, resume, partial report behavior, and operation without optional hooks.
