# Accepted decisions in specification 0.5.0

This revision incorporates the scientific-validation review while retaining the accepted epistemic, runtime, security, causal, and implementation-foundation policies from versions 0.2 through 0.4.

## First implementation slices

- The architectural vertical slice is domain-neutral and is exercised first on GeneBench-derived and synthetic fixtures.
- The first named domain pack is a deliberately narrow bulk RNA-seq differential-expression profile.

## Agent adjudication

- Benchmark adjudicators are coding agents rather than assumed manual experts.
- The initial reference pair is Claude Code with Claude Opus 5 and Codex with GPT-5.6 Sol.
- Qualification uses at least four blind Stage-1 reviews across both providers and at least two fresh Stage-2 adjudications.
- Exact model, agent, prompt, tool, environment, and transcript identities are pinned.
- Agent confidence and simple majority vote do not determine labels.
- Material disagreement excludes a case from positive and verified-good sets.
- Scientific labels are frozen before sc-referee output is exposed.
- Agent-only review is disclosed and is not described as human expert endorsement.

## Fixtures and external packaging

- Evaluation distinguishes verified-good, scope-verified-good, hard-negative, positive, and ambiguous fixtures.
- No fixture label permits a global correctness claim.
- RO-Crate 1.3 is the first external research-object export; native records remain canonical.

## Capability and maturity

- Public capability claims use a machine-generated multidimensional matrix.
- Validated and publication-grade detectors may both emit Findings inside their qualified envelope and the same five-part admission rule.
- Experimental detectors cannot emit Findings.
- Non-negotiable promotion safety gates are accepted now; numeric thresholds are deferred until a pilot-corpus ADR.
