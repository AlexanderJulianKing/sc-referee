# Experiment 0028: Fresh Hi-C scientific-audit skill portability

- **Status:** Local fresh-context portability check complete; not qualification evidence
- **Date:** 2026-07-31
- **Target:** Answer-isolated Hi-C workflow from Experiment 0025
- **Mode:** `standard` (480-second scheduling cutoff; 600-second hard deadline)
- **Project execution:** Disabled
- **Production detector or Finding authority:** None

## Question

Can a fresh-context agent use the repository-scoped `scientific-audit` skill on a non-QTL
workflow, select the explicitly named report, recover the existing bounded expected-count
question, stop at the scientist boundary, and replay the result without open-ended scientific
interpretation?

## Procedure

The fresh agent received the skill and the isolated target
`/private/tmp/sc-referee-experiment-0025/hic-v2/workspace`. It was instructed to audit in standard
mode with `report.md` as the explicit publication surface, not execute project-authored code, not
inspect answer-side files semantically, not select an answer, and replay the resulting semantic
lock.

The globally installed `sc-referee` executable was absent from that agent's shell path. Following
the skill's stated fallback, it used the checkout's `.venv/bin/sc-referee`; it did not install a
dependency or run project setup code.

Primary output:

`/private/tmp/sc-referee-experiment-0025/hic-v2/workspace/.scientific-audit/runs/fresh-portability-standard-20260731T190041Z`

Replay output:

`/private/tmp/sc-referee-experiment-0025/hic-v2/workspace/.scientific-audit/runs/fresh-portability-replay-20260731T190253Z`

## Result

The primary run completed with verified integrity and overall status
`partial_evidence_unavailable`. It produced:

- zero Findings;
- zero ConditionalConcerns;
- one MaterialQuestion; and
- 18 Disclosures.

The exact question was `question-analysis-expected-count-obligation:5c7bb3e4b91942cedbf1`:
“Which expected-count/background profile governs the requested values?” Its only choices were to
provide the bounded structured expected-count recipe or retain the unknown. The agent presented
the question and left it unresolved. The six unresolved contract dimensions were
`adjustment_set`, `control_set`, `dependence_structure`, `measurement_model`,
`scale_and_orientation`, and `selection_process`.

The run deeply inspected only `analysis.py`, `report.md`, and `task.md`. The major limitations were
that no production detector target was eligible and 100 statically inventoried Python operations
remained opaque. The semantic-lock digest was
`sha256:98547fde1f3a7681dcdeb6ef582225fba120e6f4f939376c54d948b293a93209`.

Replay preserved the semantic lock, assessment counts, question, coverage, and rendered report.
The audit diff reported no assessment or path changes and had digest
`sha256:7fbb5c8bb0617aca8f92dc906bebe9debb963b1473d28275e71c2715b62a86d1`.
The measured interval through semantic lock was 0.2798939999192953 seconds, with 32,919 source
bytes read for identity, zero cache hits, three cache misses, and zero controller-recorded model
calls. This timing excludes post-lock work and is not total runtime.

This result demonstrates that a fresh skill user can operate the existing bounded question path
on this non-QTL workflow. It does not demonstrate that the workflow is correct, that the question
has a scientifically correct answer, that other Hi-C methods are covered, or that any detector is
qualified.

## Answer-key-informed development follow-up

The expert answer key was then used only on the evaluation side to construct and check a golden
workflow. That workflow implemented the specified masked negative-binomial estimator, excluded
the focal target from fitting, and reproduced the three released values within approximately
`1e-9`, well inside the `0.02` tolerance. An independent static reviewer accepted its method and
found no material answer leakage. The preserved candidate instead reported a same-distance
arithmetic mean that included the focal target and missed all three released values: case by
`-0.8120861770`, control by `-0.2311593286`, and delta by `-0.5809268480`.

Accepted ADR-0043 therefore adds two domain-neutral, question-only checks for those explicit
method axes: expected-count construction and focal-target handling. A new ordinary static audit
of the unchanged candidate report produced three questions: the two atomic questions plus the
unchanged complete-profile question. It produced zero Findings and zero ConditionalConcerns.

The repository owner's answer-key-backed review decisions were recorded in two separately linked
segments because the interaction command accepts one answer per segment:

- `answer-key-loop-20260731-03` records the requirement to exclude the focal target and reports an
  exact incompatibility with the report's target-inclusive background. Its semantic-lock digest
  is `sha256:1bedca763b75762b0e122b6848727b30e6f632a4a6f9b363ab41fd0871f3e498`.
- `answer-key-loop-20260731-04` records the requirement to use negative-binomial-model predicted
  expected counts and reports an exact incompatibility with the report's arithmetic mean. Its
  semantic-lock digest is `sha256:1815db5116fd9804fbc82854b9fba86b331bed05c7fe8fce3144d1de04b0925f`.

Both replays reproduced their semantic locks and rendered reports byte-for-byte. These are
review-scoped material incompatibility Disclosures, not Findings: the selected report demonstrates
what it says, but static report text does not prove which code ran or that either choice caused the
numeric misses. The answer key is evaluation evidence and is not production authority for another
study.

## Snapshot-access clarification

The target root also contained `answer.json`, `diagnostics.json`, and four compressed data files.
The agent did not open or interpret those files for scientific meaning, and no assessment,
question, Claim, contract, or result premise was derived from their contents. The auditor did,
however, open every eligible file to compute immutable snapshot identity, so those files acquired
path, size, and digest records.

Therefore `uninspected` means “not semantically or deeply inspected”; it does not mean “no byte
access.” An audit cannot honestly promise byte-blindness for an eligible file inside its target
root. If a case protocol forbids even hashing an answer-side file, the coordinator must first
provide an allowlisted workspace that omits it. The authoritative and packaged skill copies now
state that boundary before audit execution.

## Test, acceptance criterion, and remaining limitation

- **Test added:** `tests/test_agent_skill.py` now requires the authoritative skill to distinguish
  semantic noninspection from snapshot byte access and to require an allowlisted workspace when
  byte access is prohibited. `tests/test_codex_plugin.py` continues to require byte-identical
  authoritative and packaged skill copies. The skill and plugin validators pass.
- **Acceptance criterion satisfied:** a fresh-context user followed the installed workflow on a
  non-QTL repository, reached exactly the existing bounded scientist question, preserved the
  unknown, emitted zero Findings, executed no project code, recorded no model calls, verified
  integrity, and reproduced the locked result.
- **Remaining limitation:** this is one local Codex fresh-context usability run over a known
  development case. It is not an authenticated two-provider review, an answer-blind detector
  qualification case, a false-positive estimate, broad Hi-C support, or public Finding authority.
  Because the supplied root retained answer-side artifacts, the run also proves semantic
  noninspection rather than byte exclusion. The follow-up recognizes only explicit selected-
  Markdown declarations; it does not parse arbitrary paraphrases, prove executed code, validate
  masks or covariates, attribute numerical causality, or resolve the complete expected-count
  profile.
