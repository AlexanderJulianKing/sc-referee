# ADR-0037: Use conservative cross-provider coding-agent adjudication

## Status

Accepted; supersedes the mandatory-human-review portions of ADR-0027.

## Context

Manual expert adjudication is not assumed to be available. Coding agents can inspect repositories at scale, but any one agent can miss evidence, anchor on a result, or produce a plausible false explanation.

## Decision

Qualification uses at least four Stage-1 blind reviews—two independent runs from each of two provider families—and at least two fresh Stage-2 adjudications, one per provider family. The initial reference pair is Claude Code with Claude Opus 5 and Codex with GPT-5.6 Sol. Exact model, agent, prompt, tool, environment, and transcript identities are pinned. Stage 1 hides answers, grades, detector identity, sc-referee output, and other reviews. Stage 2 freezes scientific labels before detector output is visible. Material disagreement is excluded rather than majority-voted. See SA-FR-085 and SA-FR-095 through SA-FR-097.

## Consequences

- Evaluation can scale without pretending agents are infallible.
- Agent-only qualification is disclosed and is not human expert endorsement.
- Conservative exclusion lowers label volume but protects false-accusation precision.
