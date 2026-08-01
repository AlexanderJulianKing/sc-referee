# Experiment 0026: Second static-profile readiness pilot

- **Status:** Superseded historical readiness freeze; no authenticated review was started and the
  detector identity was replaced before qualification
- **Date:** 2026-07-31
- **Governing decisions:** Accepted ADR-0022, ADR-0040, ADR-0041, and ADR-0042; historical public
  schema v0.16.0, superseded candidate detector v0.1.0
- **Production detector or Finding authority:** None

## Question

Can the frozen `detector:bounded-analysis-method-conflict` candidate enter an answer-blind
qualification workflow through an independently implemented, non-executing static proof, without
changing the detector after labels become visible or treating local controls as promotion evidence?

## Frozen pre-case boundary

The repository now carries a deterministic readiness freeze under
`evaluation/qualification/bounded-analysis-method-conflict-v0.1.0-readiness-pilot/`. It binds:

- detector version `0.1.0`, its exact manifest, and implementation digest;
- the exact Markdown and Python parser manifests plus semantic-profile and version manifests;
- evaluator entry point
  `sc_referee_evaluation.analysis_method_qualification:verify_bounded_analysis_method_case` and
  its implementation/dependency closure;
- the accepted v0.16.0 `bounded_analysis_method_conflict_v1` proof vocabulary and budgets;
- a pre-case opaque fixed-order selection protocol with no post-assignment replacement;
- normalized Stage-1, Stage-2, and Stage-3 prompts and their exact digests; and
- the 2x2 Stage-1, 1x2 Stage-2, and 1x2 Stage-3 independent cross-provider panel shape.

The freeze intentionally contains no case assignment, scientific label, reviewer identity,
transcript, detector outcome, threshold, qualification, or promotion decision. The initial block
is explicitly a non-held-out readiness pilot. Its results may validate transport and expose design
defects, but they cannot contribute a promotion metric.

## Assigned readiness workspaces

After the pre-case freeze, four no-replace assignment artifacts and four nine-file blind workspace
manifests were created under `/private/tmp/sc-referee-experiment-0026`:

| Case | Assignment digest | Blind-workspace digest |
|---|---|---|
| `case:readiness:direct` | `sha256:336bdbfbeaf18ad7ccf968d4cd9bf5f51360475efa784156a7c7275ba19db766` | `sha256:16fc687138991d1cb6dd6339730550020b261d3e7142812cea91ac15594a69bf` |
| `case:readiness:repaired` | `sha256:3b2a5836c039bf5639ced5e4c432d94d4aa996bac5966daafe51263a6857d748` | `sha256:3ddaef9d537738bb9c697e9d50c9da64ccd519569bbd23547819cfe88d365964` |
| `case:readiness:counterevidence` | `sha256:a0600d7da7c3c9f854be3211765a888f16eef7bb932f308fb5a1ff3fb7329d39` | `sha256:e6e6125c6f286845933f84a5ed718d2b5e08cd992e4af37346c3a95ff2ab3c10` |
| `case:readiness:removal` | `sha256:48bc5b5c575e6afa675ee6bbd34d2d0416e2dcb3a2a4a6b7d244784b419f07f6` | `sha256:a5c06cb298e80ade6724c48411bd51b53bf1600ec6b194c6a6494648cc53b6fb` |

The direct, counterevidence, and removal cases deliberately reuse the already known development
workflow; the repaired case reuses its already known fixed counterpart. They are suitable only for
readiness transport. They are neither independent nor held out, and their labels and prior detector
behavior are already known to the implementation team. The workspace builder copied only the
allowlisted task, data, source, report, and generated outputs, recorded
`answer_side_content_copied: false`, and executed no project code. Its bounded scanner cannot prove
that no undisclosed or paraphrased answer-side information exists.

Stage-1 packets have not been manufactured with placeholder identities. Each packet must bind the
provider, model, surface, system prompt, tool policy, environment, and fresh execution-context ID
from the actual reviewer invocation.

## Local mechanism result

The new evaluator-owned verifier independently enumerates full-digest `.md` and `.py` candidates,
decodes strict UTF-8, derives the selected-report operand, derives one supported source operand,
proves one unique literal source-parent-relative selected-output writer, and verifies the exact
scope-bound human Question, Answer, ScientificContract, and accepted requirement assertion. It
imports no production parser, adapter, detector, ledger, or semantic-fact helper and executes no
project code.

Local controls now cover the exact conflict, matching requirement, report/source disagreement,
all five counterevidence classes, ambiguous or absent operands, competing or dynamic writers,
unsupported dataflow, nonhuman or drifted authority, weak identity, strict-UTF-8 failure, candidate
inventory drift, byte drift, chronology, and finite budgets. Complete method-profile records pass
static fixture construction and replay, Stage 3, report rendering, canonical JSONL, disposable
SQLite, attached RO-Crate export/validation, public schema migration, and package-resource checks.

## Supersession boundary

No external Stage-1, Stage-2, or Stage-3 capture was obtained under this freeze. Accepted ADR-0042
replaces the founder-specific detector implementation with generic version `0.2.0` and replaces
the proof vocabulary with schema v0.17.0. This committed directory remains immutable historical
evidence of what was frozen before the redesign; it cannot qualify, promote, or supply a metric for
version `0.2.0`. Its one-time builder now fails closed when pointed at the current detector rather
than silently rebuilding a different candidate under the old name.

## Replacement actions

1. **Completed:** local modularity and release gates for detector `0.2.0`, schema v0.17.0, and the
   independently implemented qualification adapter, including current typed fixture, Stage-3,
   reporting, storage, and RO-Crate replay.
2. Freeze a new answer-blind selection protocol, candidate profile, prompts, and exact assignments
   under a new directory and identity before any reviewer sees a case.
3. Obtain authenticated two-provider Stage-1, Stage-2, and fresh Stage-3 captures against that
   unchanged candidate, preserving the readiness-pilot exclusion.
4. Use the pilot only to predeclare a separate held-out block and threshold; Finding permission
   still requires explicit maintainer promotion.

No external provider is represented as authenticated merely because a provider or model name is
written in a packet. Capture provenance and distinct execution contexts must be supplied by the
actual review surfaces.

## Test, acceptance criterion, and remaining limitation

- **Tests added:** `tests/test_analysis_method_qualification.py` covers independent proof and
  mutation behavior; `tests/test_evaluation_control_fixture.py` covers method-profile fixture,
  Stage-3, report, JSONL/SQLite, and RO-Crate paths;
  `tests/test_analysis_method_qualification_freeze.py` proves the committed pre-case freeze's
  internal inventory, validates it against v0.16.0, and proves its builder rejects the current
  detector identity; `tests/test_verify_handoff_configuration.py` keeps the v0.14-to-v0.15 and
  v0.15-to-v0.16 migration checks bound to their respective immutable target schemas.
- **Acceptance criterion satisfied:** the candidate and independent proof protocol are immutable
  before case assignment, every local material premise fails closed, and no local record claims
  qualification, execution, promotion, or Finding authority. The full 1,117-test checkpoint,
  clean-wheel handoff, starter validation, schema validation, demo, replay, Ruff, formatting, and
  strict core/evaluation typing checks pass.
- **Remaining limitation:** this superseded freeze received no authenticated answer-blind panel.
  Detector `0.2.0` requires an entirely new freeze and review portfolio. No pilot metric, held-out
  threshold, qualification, maintainer promotion, or production Finding permission exists.
