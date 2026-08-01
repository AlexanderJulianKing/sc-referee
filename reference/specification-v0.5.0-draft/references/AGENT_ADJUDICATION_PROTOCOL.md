# Agent adjudication protocol reference

**Protocol version:** 1.0.0-draft  
**Dated reference configuration:** 2026-07-27

## Reference provider pair

- Anthropic Claude Code with Claude Opus 5, model ID `claude-opus-5`.
- OpenAI Codex with GPT-5.6 Sol, model ID `gpt-5.6-sol`.

The protocol pins exact agent and model identities per review. These are initial reference configurations rather than permanent product requirements.

## Minimum qualification panel

- Four Stage-1 blind reviews: two independent execution contexts per provider family.
- Two Stage-2 scientific adjudications: one fresh context per provider family.
- Scientific label frozen before Stage-3 detector comparison.
- Material disagreement excludes the case.
- Self-reported confidence and simple majority vote are ineligible.
- Every review retains prompt, tools, environment, transcript, blindness, scope, and evidence identities.

## Disclosure

Labels produced only by this protocol are described as agent-adjudicated or agent-panel-qualified. They are never represented as human expert review, and correlated error remains a known limitation.


## Mandatory anti-correlation safeguards

- The two runs from one provider family use fresh contexts and independently randomized review identifiers; they do not share scratch state or prior outputs.
- Stage-2 adjudicators receive an explicit falsification assignment: state the strongest innocent explanation, identify any premise that could reverse the label, and attempt to disprove the proposed root cause before accepting it.
- Cross-provider textual agreement is not sufficient. Every material source reference must resolve against the frozen snapshot, and every bounded label must pass deterministic entailment, scope, lineage, and decisive-counterevidence checks.
- A materially dissenting review, unresolved semantic premise, failed source reference, or non-reproducible deterministic check makes the case ineligible for positive, verified-good, or hard-negative status.
- Correlated model error remains possible. Agent-panel labels are versioned, challengeable, and subject to immediate demotion when contrary evidence appears.
