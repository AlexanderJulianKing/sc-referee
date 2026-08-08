# Qualification report: complete-domain exposure denominator detector

- **Check:** `check:complete-domain-exposure-denominator`, version 2.0.7
- **Detector:** `detector:bounded-analysis-method-conflict` (question-only output ceiling)
- **Envelope:** first qualified envelope of the ten-findings program (Experiment 0056)
- **Date:** 2026-08-08
- **Result: PASSED the sealed held-out block, seven of seven**, exceeding the accepted
  ADR-0070 threshold (required: zero false accusations of five controls and at least one of
  two planted errors caught; achieved: zero false accusations and both errors caught)

## The error class, in plain terms

A study plans to observe a complete set of units (stations, patients, plots, light curves).
A screening step removes some units. The analysis then computes its headline rate by dividing
event counts by only the retained units, but the report presents that rate as if it covered
the complete planned set. The number is real arithmetic over the wrong denominator, and the
claim silently shrinks the study's stated scope. The corrected form divides by the complete
set; the valid alternative form honestly declares the retained subset as its target.

## How the detector recognizes it

Recognition is operations-based (ADR-0069): variable names, unit nouns, and domain vocabulary
never gate detection. Two fused evidence planes:

1. **Report arithmetic.** The stated counts must form a complete accounting (complete =
   retained + removed, each a distinct stated number), and the stated rate must reconcile,
   within its own stated precision, with exactly one of events/retained or events/complete.
   Standardized notation is respected (percent forms; SI and laboratory unit suffixes,
   compound modifiers, dates, and signed values are excluded from counts).
2. **Source dataflow.** A bounded static trace follows the workflow's own code from the data
   read, through filters, comprehensions, counter and accumulator loops, and helper
   functions, to the division that produces the reported value, and classifies the
   denominator by what it actually counts. Only divisions whose value can reach the written
   report classify. The trace is soundness-audited: every demonstrated wrong-answer path from
   an adversarial review is a permanent unit test, and untraceable code abstains rather than
   guesses.

A conflict is raised only against a frozen, scientist-authorized method contract; the
detector never infers the intended scope, and its output is a question-ceiling evaluation
candidate, never an automatic production finding.

## Development record: sixteen blind pilots

Every pilot was blind: enrolled model authors invented cases (domain, vocabulary, numbers,
and code style all their own) without any access to the detector; a calibrated blind reviewer
labeled cases before any detector output existed; the detector then ran once. Failures were
never repaired in place; every miss was localized and permanently locked as a regression.

| Pilot | Detector | Sensitivity | False accusations | Outcome |
| --- | --- | --- | --- | --- |
| v4 (panel) | 1.1.0 | 0/1 | 0/2 | miss: closed word-list vocabulary |
| v120 (lean) | 1.2.0 | 0/1 | 0/2 | miss: conflict stated only in arithmetic |
| b | 2.0.0 | 0/1 | 0/2 | miss: threshold/retention coincidence; toy-only trace |
| c | 2.0.1 | 0/1 | 0/2 | miss: compound-token phantom; helper division |
| d | 2.0.2 | 1/1 | 0/2 | pass |
| e | 2.0.2 | 1/1 | 0/2 | pass |
| f | 2.0.2 | 0/1 | 0/2 | miss: argument-taking helper return |
| g | 2.0.3 | 0/1 | 0/2 | miss: table-building loop |
| h | 2.0.4 | 1/1 | 0/2 | pass |
| i | 2.0.4 | 0/1 | 0/2 | miss: unit-gap phantom; imperative counters |
| j | 2.0.4 | 0/1 | 0/2 | miss: geometric-chain phantom; loop-built subset |
| k | 2.0.4 | 1/1 | 0/2 | pass |
| l | 2.0.6 | 1/1 | 0/2 | pass |
| m | 2.0.6 | 0/1 | 0/2 | miss: append-assembled report |
| — | 2.0.5 | — | — | soundness pass from an adversarial Codex review |
| — | 2.0.7 | — | — | append-assembly linkage; final pre-exam version |

Pilot aggregates: false accusations 0 of 32 blind controls; fresh-test sensitivity roughly 55
percent per case in the v2 architecture, with every repaired evasion staying caught (27
burned pilot cases as permanent regressions, all passing under 2.0.7).

## The sealed held-out examination

Seven case identities and roles were frozen and sealed on 2026-08-04, before any pilot label
or detector outcome existed, with authoring withheld until a maintainer-accepted threshold
(ADR-0070, accepted 2026-08-08). On acceptance the seal opened: the sealed briefs (bound by
digest since sealing) were given to six fresh blind author contexts honoring the sealed
provider assignments — three OpenAI Codex contexts, two Claude Opus contexts, one Claude
Fable context — who produced real executable workflows verified by sandboxed execution at
intake. One calibrated blind reviewer labeled all seven; labels froze; the detector ran once.

| Role | Outcome |
| --- | --- |
| error-bearing (instrument uptime, 21/126 claimed for 168 slots) | **caught (true positive)** |
| independently renamed reimplementation (greenhouse lighting, different author, vocabulary, and numbers) | **caught (true positive)** |
| corrected twin (complete-calendar denominator) | clean (true negative) |
| valid alternative (explicitly conditional target) | clean (true negative) |
| hard negative (secondary quality metric built to look suspicious) | clean (true negative) |
| ambiguous (two equally authoritative scope records; no contract resolvable) | abstained, clean (true negative) |
| unsupported (producer-to-report binding not statically establishable) | abstained, clean (true negative) |

Integrity: blind review clean seven of seven with no escalation; labels frozen before
detector observation; deterministic replay verified; zero production findings; zero project
code executed inside the audit. Ledger digests: opening `sha256:0daf0982…`, authoring
`sha256:6554e881…`, intake `sha256:80a43026…`, review `sha256:a7517978…`, labels
`sha256:913c907e…`, detector run `sha256:679cbc06…` (full values in the delivery-plan log).

## Disclosures

- **Agent-only review.** Case labels were established by calibrated model reviewers under
  ADR-0067 (one blind review with escalation on any non-clean result), not by human experts.
- **Review provider composition.** Reviews came from Anthropic models across two model
  families (ADR-0066); cross-provider review was unavailable. Held-out **authoring** was
  cross-provider (OpenAI and Anthropic).
- **Codex transport verification** for the three Codex authors is banner-level (the model
  flag passed plus the CLI's banner), weaker than the per-call served-model verification used
  for Claude transports.
- **Sealed-brief supersessions**, recorded in the opening record: the unsupported cell's
  mechanism moved from an environment-variable-selected report path to a data-selected path
  (the intake sandbox bans environment access; the cell's tested property is unchanged), and
  the sealed 4+2 reviewer panels were superseded by the accepted lean review ADRs.
- **One shot.** The held-out block ran once. No case was repaired, re-authored after
  admission, or re-run.

## Limitations

- This qualification covers exactly one error class in one check. The other checks in the
  registry remain question-only and unqualified.
- Recognition coverage is bounded: rates stated as bare integers without a percent marker or
  stated fraction, word-form numbers, non-CSV data sources, and non-Python workflows are
  outside the current grammar; unrecognized code shapes abstain.
- Blind fresh-case sensitivity during development was roughly 55 percent per case: new
  authoring idioms can still evade recognition until repaired. The false-accusation record
  (zero in 37 blind controls program-wide) is the load-bearing guarantee.
- The detector's output ceiling is question-only pending the maintainer promotion decision;
  it does not create production findings.

## Replay

Every artifact above is content-addressed and replayable from the repository: the pipeline
(`evaluation/src/sc_referee_evaluation/lean_pipeline.py`, driver `scripts/heldout_run.py`)
revalidates each ledger digest, and `replay()` reproduces the detector results byte-for-byte
from the frozen audit locks.
