# 12. Open decisions

## 12.1 Purpose

This register keeps unresolved product and engineering choices visible. An implementation MUST NOT silently choose a durable default for an open or deferred decision unless the choice is recorded in an ADR or explicitly marked as a temporary experiment.

## 12.2 Decision states

| State | Meaning |
|---|---|
| `open` | No durable choice has been made. |
| `trial` | A reversible default is approved for prototyping. |
| `accepted` | The decision is normative and has an ADR. |
| `deferred` | A policy has been accepted but the final parameter or implementation is intentionally postponed. |
| `superseded` | A later decision replaces this one. |

## 12.3 Resolved scientific validation decisions

OD-026 through OD-030 were resolved in specification 0.5.0:

- the architectural vertical slice is domain-neutral and the first named domain pack is narrow bulk RNA-seq;
- benchmark adjudication uses pinned cross-provider coding-agent panels, initially Claude Code with Claude Opus 5 and Codex with GPT-5.6 Sol;
- qualification requires four Stage-1 blind reviews, two fresh Stage-2 adjudications, deterministic evidence checks, and exclusion of material disagreement;
- verified-good, scope-verified-good, and hard-negative fixtures have distinct proof obligations and never imply global correctness;
- RO-Crate 1.3 is the first external research-packaging export; and
- public capability claims use a machine-generated multidimensional matrix rather than domain-wide checkmarks.

These decisions are recorded in ADR-0036 through ADR-0041. ADR-0037 supersedes the mandatory-human-review portions of ADR-0027 while preserving maintainer approval, public qualification reports, and emergency demotion.

## 12.4 Previously resolved decisions

OD-001 through OD-025 were resolved in specifications 0.2 through 0.4 and are recorded in ADR-0011 through ADR-0035. Their identifiers are not reused.

## 12.5 Deferred scientific threshold decision

### OD-036 — Quantitative detector promotion thresholds

**State:** `deferred`

**Question:** Which minimum precision, false-accusation ceiling, effective sample size, clustered uncertainty interval, and diversity requirements are necessary for `validated` and `publication-grade` promotion?

**Accepted interim policy:** ADR-0042 establishes non-negotiable safety gates now and prohibits promotion before a public qualification report. Universal numeric cutoffs are intentionally deferred until the pilot corpus exists; zero observed false positives alone is insufficient.

**Resolve by:** Before promoting the first detector to `validated`, through a separate threshold ADR informed by the pilot corpus.

## 12.6 Integration and distribution

### OD-031 — Claude command naming

**Question:** Can distribution preserve the exact `/scientific-audit` invocation across standalone skills and namespaced plugins?

**Recommended working default:** Provide a standalone skill alias for `/scientific-audit` and a full plugin command for environments that require namespacing. Keep both as thin adapters over the same local controller.

**Resolve by:** Milestone 5 integration prototype.

### OD-032 — Local tool protocol

**Question:** Should the Claude integration use MCP exclusively, direct CLI calls, or both?

**Recommended working default:** Use a typed local MCP server for structured interactive operations and retain the CLI as the canonical reproducible interface and fallback.

**Resolve by:** Milestone 5.

### OD-033 — Audit bundle signing

**Question:** Should publication-critical audit bundles be cryptographically signed?

**Recommended working default:** Design the bundle manifest so signing can be added without changing record identities. Defer mandatory signing until there is a release and key-management policy.

**Resolve by:** Before regulated or formal publication-review claims.

### OD-034 — Telemetry

**Question:** May the open-source tool collect usage, performance, or detector-feedback telemetry?

**Recommended working default:** No telemetry by default. Any future telemetry must be opt-in, inspectable, and exclude project content and scientific records unless the user deliberately exports them.

**Resolve by:** Before any hosted service or telemetry implementation.

### OD-035 — Feedback export

**Question:** How can users submit false positives or missed issues without leaking sensitive repositories?

**Recommended working default:** Provide a local redaction/export utility that creates a minimal detector fixture only after user review; never upload automatically.

**Resolve by:** Milestone 9.
