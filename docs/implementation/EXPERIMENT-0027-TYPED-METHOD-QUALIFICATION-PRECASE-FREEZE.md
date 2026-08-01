# Experiment 0027: Typed-method qualification pre-case freeze

- **Status:** Pre-case freeze complete; case assignment and authenticated review not started
- **Date:** 2026-07-31
- **Governing decision:** Accepted ADR-0042; active public schema v0.17.0
- **Candidate:** `detector:bounded-analysis-method-conflict` version `0.2.0`
- **Production detector or Finding authority:** None

## Question

Can the final modular v0.2 method-conflict candidate be frozen before case selection under the
typed, independently implemented qualification path, while keeping all labels, reviewer
identities, transcripts, detector outputs, thresholds, and promotion claims absent?

## Frozen boundary

The repository now carries a deterministic pre-case freeze under
`evaluation/qualification/bounded-analysis-method-conflict-v0.2.0-precase/`. It binds:

- detector version `0.2.0`, its exact manifest, and implementation digest;
- the exact founder-orientation method-check binding and its content digest;
- the independent founder-orientation qualification adapter identity, implementation digest, and
  dependency closure;
- the exact Markdown and Python parser manifests plus semantic-profile and version manifests;
- the accepted v0.17.0 `typed_static_method_conflict_v1` profile, closed scalar relation, budgets,
  and generic independent-verifier dependency closure;
- an opaque fixed-order, pre-label, no-replacement selection protocol;
- the positive, verified-good, ambiguous, hard-negative, removal, and counterevidence portfolio
  roles without assigning a case to any role;
- normalized Stage-1, Stage-2, and Stage-3 prompts and their exact digests; and
- the two-provider fresh-context panel shape and actual-invocation-only identity rule.

The frozen profile semantic digest is
`sha256:1978755e1273881dae6e7509b1fdef32f6364e7ca96d5acfebd97d4cfc42cce7`.
The selection protocol content digest is
`sha256:5c660494db8c10fc25961f3cae49e20e2284828a36500a409f101497d46dd3e0`.
The complete pre-manifest inventory digest is
`sha256:c86fc41e643e9094e4ebb9bae5a3674dfa796b2bf03d2534ed1b594299d89fb2`.

## Why cases are not included

Existing Experiment 0026 cases and development workflows are already known to the implementation
team. Reusing them can test transport, but cannot make them independent, held out, or eligible for
promotion metrics. This freeze therefore stops before assignment instead of relabelling known
examples as new qualification evidence.

The next case coordinator must assign each eligible case before its scientific label or detector
output is visible and must not replace an assigned case because of its result. Stage-1 workspaces
must omit the selection protocol, case role, answer-side evidence, other reviews, and detector
identity/output. Reviewer-agent records must be created from the actual provider invocation;
placeholder provider, model, surface, or execution-context identities are prohibited.

## Result

The committed freeze validates against schema v0.17.0 and reproduces byte-for-byte from the
one-time no-replace builder. It contains no case assignment, scientific label, reviewer identity,
transcript, detector output, qualification metric, threshold, promotion decision, or production
Finding permission. The historical v0.1 freeze remains byte-immutable and cannot qualify v0.2.

The isolated evaluation CLI now exposes separate v0.2 commands to freeze a typed profile, create
an opaque no-label assignment, verify a case through the explicitly registered independent
adapter, and replay the proof from the same immutable inputs. The historical v0.1 command names and
behavior remain unchanged. This removes the prior source-API-only transport gap without changing
the production CLI or detector authority.

This completes the local boundary needed before independent review. It does not complete external
qualification.

## Next actions

1. Acquire or construct eligible cases without exposing answer-side labels to Stage 1, then freeze
   exact no-replace assignments and blind-workspace manifests under this protocol.
2. Obtain authenticated two-provider Stage-1 and Stage-2 captures in genuinely fresh contexts.
3. Freeze the scientific labels and exact root-cause records before running v0.2 or showing any
   detector output to Stage 3.
4. Run fresh Stage-3 comparisons and use the readiness evidence only to predeclare a separate
   held-out block and metric threshold.
5. Require an explicit maintainer promotion decision before any Finding permission or public
   qualification claim.

Any material candidate-logic change after a label becomes visible creates a new detector version
and a new freeze. Adding another scientific check also requires its own independent qualification
adapter; the current freeze qualifies no representation beyond founder orientation.

## Test, acceptance criterion, and remaining limitation

- **Tests added:** `tests/test_analysis_method_qualification_freeze.py` validates the committed
  v0.2 profile against schema v0.17.0, verifies exact detector/binding/adapter identities and
  dependency digests, checks the complete file inventory, proves that no case or reviewer evidence
  was inserted, rebuilds the directory byte-for-byte, and proves the builder cannot overwrite an
  existing freeze. It also rebuilds the exact profile and creates a label-free assignment through
  the new CLI. `tests/test_evaluation_control_fixture.py` verifies and byte-replays a complete typed
  proof through that CLI. The handoff verifier requires the typed engine, explicit adapter
  registry, and founder adapter to exist and import from the isolated evaluation wheel. Existing
  tests continue to prove the v0.1 builder rejects v0.2.
- **Acceptance criterion satisfied:** the current v0.2 candidate and independent typed verifier
  are immutably bound before any case assignment or label inspection, with answer blindness,
  no-replacement selection, no project-code execution, and no promotion/Finding authority stated
  explicitly.
- **Remaining limitation:** no new case has been assigned and no authenticated independent review
  has occurred. The freeze is pre-case mechanism evidence only, not a qualification result,
  accuracy estimate, held-out corpus, or public maturity claim.
