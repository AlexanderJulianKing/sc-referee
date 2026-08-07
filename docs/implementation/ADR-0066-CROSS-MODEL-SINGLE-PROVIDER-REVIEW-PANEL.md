# ADR-0066: Cross-model single-provider review panel under provider unavailability

- **Status:** Accepted by the maintainer on 2026-08-07, in session, through an explicit
  single-choice confirmation presented by the coordinating agent after the full trade-offs,
  disclosure obligations, and evidence-contract consequences were stated
- **Date:** 2026-08-07
- **Scope:** The active `check:complete-domain-exposure-denominator` pilot and, if still
  necessary, its held-out evaluation, while OpenAI provider access is unavailable
- **Relates to:** Experiment 0056 requirement 7 (four blind Stage-1 reviews across two providers
  and two fresh cross-provider Stage-2 reviews); the v3 evaluation-private evidence contract

## Context

The accepted review requirement assumes two available provider families. On 2026-08-07 the OpenAI
provider is blocked by a usage limit until 20:34 local time, the maintainer has a fixed external
deadline, and the maintainer explicitly directed completion of the active pilot without waiting.

Current state: the replacement clean CLI Stage-1 protocol
(`sha256:b555cee404eb72ddedcb027e35dbb5a4e70351dce181945cccd8c9db8def0d41`) has two admitted
Claude Opus 5 reviews per case and two frozen, unexecuted Codex calls. Claude Fable 5 is a
distinct Anthropic model family from Claude Opus 5 and is available now through the same
authenticated Claude Code CLI surface.

Empirical record to date: across all 24 admitted scientific reviews and every completed
calibration, no reviewer has ever disagreed on a verdict across providers. The one recorded
cross-provider behavioral difference was procedural: the four label-blocking
`unresolved_material_questions` reviews in the first panel were all Anthropic.

The frozen Stage-1 panel and Stage-2 freeze machinery use provider checks that are relative to
the panel's own provider participation. One frozen check is absolute:
`prospective_qualification_v2.py` requires the scientific-panel freeze's two Stage-2 entries to
use two distinct providers. That module is digest-bound by the current v3 precase evidence
tuple and must not be edited in place.

## Decision

1. For the scoped envelope, the Stage-1 panel requirement is four blind reviews from at least two
   distinct **model families**, two reviewers per family, in distinct fresh execution contexts.
   For this pilot the panel is two Claude Opus 5 plus two Claude Fable 5 reviews.
2. The Stage-2 requirement becomes two fresh reviews from two distinct model families (one Opus 5,
   one Fable 5), in fresh contexts, with identities disjoint from the case's authors and Stage-1
   reviewers.
3. The Stage-2 provider-distinctness check in the evidence contract is generalized to
   reviewer-family distinctness, where a reviewer family is the pair (provider, model family).
   This is implemented as a new versioned code path and a prospective v4 evidence-contract tuple
   freeze that supersedes the v3 precase tuple. No scientific label was ever created under the v3
   contract, so nothing is grandfathered. Digest-bound v3 files are not edited.
4. Provider fields keep recording the true provider. No record may describe a panel composed
   under this ADR as cross-provider.
5. Every qualification report, promotion record, and public capability claim covering material
   reviewed under this ADR must disclose: the panel was single-provider and cross-model, and the
   study coordinator shares a model family (Claude Fable 5) with two panel reviewers.
6. The two calibrated Codex reviewer configurations remain enrolled. When provider access
   returns, optional zero-authority Codex cross-check reviews may be retained as Disclosures;
   they cannot change any frozen label. Cross-provider panels remain the default for envelopes
   that have not yet frozen their review protocols.
7. The two unexecuted Codex Stage-1 calls in the clean CLI protocol become obsolete and are
   retained unexecuted; replacing them requires a prospective panel-completion amendment binding
   this ADR, the calibrated Fable configurations, and the two already-admitted Opus call ledgers.

## Consequences

- Independence is weaker than a cross-provider panel: a defect shared by all Claude-family
  models would not be caught by this panel. Partial mitigations: two distinct model families,
  the deterministic model-free selected-result verifier outside any model family, mandatory
  disclosure, and optional later cross-provider cross-checks.
- The Gate 2 evidence-contract freeze reopens until the v4 tuple is frozen and its replay tests
  pass.
- The maintainer accepts that qualification records for this envelope carry a permanent
  single-provider disclosure.

## Maintainer direction

On 2026-08-07 the maintainer directed, in session: complete the panel without waiting the
approximately nine remaining hours of the OpenAI usage limit, using Claude Fable 5 as a
materially different model from Claude Opus 5, with a minimum proud product deadline before an
interview the following Monday. Acceptance of this ADR must be recorded explicitly by the
maintainer; the coordinating agent may not accept it on the maintainer's behalf.
