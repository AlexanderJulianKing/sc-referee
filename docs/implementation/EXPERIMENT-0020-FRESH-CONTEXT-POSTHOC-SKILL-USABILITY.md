# Experiment 0020: Fresh-context post-hoc skill usability

- **Status:** Completed evaluation-private experiment and accepted ADR-0020 follow-up; transport,
  scientist interaction, semantic lock, and replay pass
- **Date:** 2026-07-29
- **Governing decision:** Accepted ADR-0019; accepted revised ADR-0020 for the follow-up
- **Public schema change:** None; accepted schema v0.14.0 remains unchanged
- **Production capability change:** None

## Purpose

Test the ordinary `scientific-audit` skill against an existing raw scientific-analysis repository,
without a pre-analysis sc-referee contract, answer-side material, or task-history context. The full
success condition was not merely that the skill could invoke and explain an audit. It had to reach
a controller-derived, closed post-hoc method question from repository evidence, stop for the
scientist's Answer, and preserve that interaction through semantic lock and replay.

The repository owner authorized this fresh-context scientific-audit usability run and granted
standing authorization for later test runs of the same kind. That authorization does not grant
authority to change schemas, Finding meaning, detector maturity, or public capability claims.

## Frozen answer-blind packet

The test copied the nine raw files from the existing `multiparent_qtl_hmm_lmm` workspace into a
new temporary repository. It excluded prior `.scientific-audit` state, Python caches, expected
results, approved scientist Answers, evaluation probes, and public-reference material.

- raw-workspace inventory profile: `sorted-relative-path-shasum-lines-v1`;
- raw-workspace inventory digest:
  `sha256:bc4f51d4139220fc6bed3202cba7a5d987abe49e96510f8e7ba1e11619e103e4`;
- frozen packet digest:
  `sha256:58130fe477c0f438d49dfe05ce0d2ba65e4cdc2dc6d3ea6569e406cceb9de698`;
- ordinary request: “Please use the scientific-audit skill to audit this existing
  scientific-analysis repository. report.md is the final report. Use standard mode. Explain any
  material question in plain language and stop for the scientist's answer if one is needed.”

An independent fresh-context coding agent could read only the copied target, installed
`sc-referee` CLI, and `scientific-audit` skill materials. It was expressly prohibited from running
project-authored code, inspecting this implementation repository, reading answer-side references,
or inventing a scientist Answer.

The copied raw files were rehashed after the run, excluding the generated `.scientific-audit`
directory. Their aggregate digest remained unchanged.

## Initial audit result

The agent used the skill correctly and completed a standard audit:

- audit ID: `audit:c3a270796e8a4ffd8f16be005cd59fe7`;
- terminal state: `complete`;
- overall assessment: `partial_evidence_unavailable`;
- snapshot digest:
  `sha256:d21e86b4d569e8daee390f831beb6d5a899f1b1589b3aedc377cc4c614974e09`;
- declared semantic-lock digest:
  `sha256:f0054e422cdcb8a13ae067e275e64d476e30fc4f0db7e0b239490af1caa842f6`;
- semantic-lock file SHA-256:
  `249255580264810ba051a1d66613910799a92891e0f5f645e80a96c46cbc91d3`;
- report SHA-256:
  `89dece98846b11259feb709c7b98426886ff9da1e3cba44700c6b7660b9e58db`.

The exact typed counts were:

| Record or event | Count |
|---|---:|
| Findings | 0 |
| ConditionalConcerns | 0 |
| MaterialQuestions | 0 |
| Claims | 0 |
| ScientificContracts | 0 |
| SemanticAssertions | 0 |
| Answers | 0 |
| Model calls | 0 |
| Project-code executions | 0 |
| Disclosures | 2 |

All nine files were inventoried. `analysis.py`, `report.md`, and `task.md` were deeply inspected;
the answer, diagnostics, and binary or compressed data remained explicitly uninspected. The audit
recorded 276 opaque Python operations, no eligible detector target, no SelectionEnvelope, and no
Claim bound to a complete ScientificContract. Its termination reason was
`semantic_inputs_unresolved`. Zero Findings was therefore not presented as evidence of scientific
correctness.

The fresh agent did not compensate by performing an open-ended review. It correctly declined to
invent either the intended founder-orientation method or the scientist's Answer.

## Replay result

The same agent then performed model-free replay into a new output directory. Integrity verification
passed. The replay preserved the snapshot and declared semantic-lock digests, exact typed counts,
assessment projection, coverage projection, and byte-identical HTML. The semantic-lock file and
HTML were byte-identical; bookkeeping bytes were not required to be identical.

The replay comparison digest was
`sha256:066543d385064bd0d311bc3ba918f84acc443a76b0866d8737e6bbb2bb491c54`.
No model call or project-code execution appeared in either run.

## Adjudication

The skill transport and conservative interpretation behavior **pass**:

- the agent discovered and followed the skill without task-history context;
- the CLI, report selection, status interpretation, integrity verification, and replay worked;
- the agent preserved unsupported science as unknown; and
- repository and answer-side isolation held.

The full ADR-0019 post-hoc interaction usability criterion **fails before the scientist boundary**.
The controller produced zero Claims, zero ScientificContracts, zero method SemanticAssertions, and
zero MaterialQuestions. Consequently the skill had no canonical question to explain and no lawful
Answer, resume, or post-hoc ledger transition to perform.

This is not a failure of `posthoc_method_ledger_v1`: Experiment 0019 already proves the ledger over
fixed typed inputs. The missing link is a reusable production path that can derive a narrowly
scoped method question from exact static repository evidence when no Claim was extracted. The
evaluation-only QTL source probe cannot be copied into production as reported wording, promoted as
a detector, or treated as evidence that the source executed merely to make this test pass.

## Next bounded decision

At the initial experiment boundary, revised proposed ADR-0020 defined a modular scientific-check
registry with separate method-level
checks and language/tool adapters, plus one shared analysis-scoped interaction path over existing
v0.14.0 records. Adding or removing a check must not change the core controller. Experimental
question-only modules may recognize exact evidence and offer finite method alternatives, but they
may create only a pre-lock MaterialQuestion and later a Finding-ineligible compatibility
Disclosure. The QTL case is one marker alongside pulse-admixture and MVMR; no module may key on a
GeneBench identity or expected answer. A module cannot establish the right method, historical
intent, execution, numerical causality, a DetectorResult, or a Finding.

An independent fresh-context broad-design review then tested whether this remedy was itself
overfit. It initially rejected the proposal's implicit adapter boundary, unspecified sibling-
module isolation, and incorrect use of the selected report as the subject of a source-code fact.
Revision 2 now defines a normalized adapter observation and pure check reducer, forbids sibling
reads, attaches static observations to their actual source target, and requires an existing typed
source-to-analysis join or abstention plus a schema-gap decision. The reviewer's follow-up found no
remaining architectural blockers. This is design evidence only; the interface and marker profiles
remain unimplemented.

## Test, acceptance criterion, and remaining limitation

- **Test added:** this answer-blind fresh-context agent run, its independent replay, and the
  separate broad-design review plus follow-up blocker audit of revised ADR-0020; no production
  behavior or automated test changed.
- **Acceptance criterion satisfied:** ordinary skill invocation, answer isolation, no project
  execution, no model authority, honest no-Finding interpretation, immutable raw input, integrity,
  and replay all pass.
- **Acceptance criterion not satisfied:** the raw repository did not produce the bounded method
  question, scientist Answer lifecycle, or ledger result required by ADR-0019.
- **Architecture criterion satisfied:** the follow-up design review found no blocker in the revised
  modular interface; implementation evidence is still absent.
- **Remaining coverage limitation:** this is one local Codex-agent run on one public-development
  QTL repository. It neither validates a scientific detector nor demonstrates the revised modular
  interface across QTL, pulse-admixture, MVMR, additional repositories, languages, or domains.

## Accepted ADR-0020 follow-up

After implementing the accepted revision, a second independent fresh-context agent received the
same answer-blind raw QTL repository and ordinary `scientific-audit` skill request. It did not read
the implementation repository, run project-authored code, inspect answer-side material, or choose
the scientist's requirement. The ordinary audit now reaches the intended boundary:

- audit ID: `audit:f9d17c889a364e988c024a2f267e029a`;
- semantic-lock digest:
  `sha256:a1e000ceef6e97619f4a93c60607af28158f01e43a85b5fdd16c074625a2176b`;
- Findings: 0;
- ConditionalConcerns: 0;
- MaterialQuestions: 1;
- Disclosures: 6; and
- model calls after lock and project-code executions: 0.

The question names the selected publication surface, the exact reported founder-orientation
operand, its immutable report span, `value_equals` comparison form, and two finite candidate
requirements. The independent agent correctly explained that the static Python adapter's matching
operand can corroborate or suppress this report-derived question but is not public evidence because
the current records do not establish a typed source-to-selected-analysis join. It then stopped for
the scientist instead of selecting the scientifically intended method.

The follow-up exposed a real usability defect: the typed agent payload and HTML report did not show
the observed operand and finite requirement choices clearly, displayed an empty blocked-detector
field, and retained stale pending-work text. The implementation now exposes the observation,
source, candidates, scope, comparison form, authority limitation, unknown consequence, and exact
downstream effect in both surfaces. A browser rendering check verified the complete question card.
Because that report-template correction intentionally changed deterministic HTML bytes, the
controller rejected resuming the earlier saved report. A new audit over the unchanged raw snapshot
created `audit:c4aa9f71fb0c49e5bbe9704fd689e11b` with semantic-lock digest
`sha256:002ba7eadc78824f63beff771c71cb25ad79249795fc2217bb2e4876f5fcabf9` and the same 0/0/1/6
assessment counts. Its linked interaction segment is
`audit:e1bc9caf56af41ca87831d89c0d3ae83`. The bounded model proposal explicitly retains the
requirement as unknown; it remains proposed, Finding-ineligible, and without scientific authority.

- **Tests added:** registry isolation/arbitration and manifest-drift tests; ordinary-audit marker,
  role-mutation, ambiguity, conformance-removal, lock-mutation, typed-agent, and HTML rendering
  integration tests; and analysis-scoped ledger interaction tests.
- **Acceptance criteria satisfied:** the generic seam is exercised by QTL, pulse-admixture, MVMR,
  and a removable conformance module; the fresh-context skill reaches the scientist boundary;
  zero Findings remains conservative; and integrity and replay inputs are model-free and locked.
- **Scientist boundary reached:** the independent agent stopped without choosing; the completed
  interaction and replay are recorded below.
- **Remaining coverage limitation:** Experiment 0021 later passes the independent non-GeneBench
  false-applicability branch, but no current adapter is applicable to an independently authored
  repository. Useful method portability is still unproved. The static QTL adapter remains a
  non-public corroborator until a typed source-to-selected-analysis join is available. None of this
  evidence qualifies a detector or authorizes a Finding.

## Completed scientist interaction

The repository owner confirmed the exact canonical requirement
`repair_ril_founder_orientation_before_hmm_emission`. The controller recorded structured Answer
`answer-structured:07797c29f361ba9709ed`, bound only to
`publication-surface:c4a0233866298845c3e4` and the `scale_and_orientation` dimension. It then
locked and completed `audit:e1bc9caf56af41ca87831d89c0d3ae83` with semantic-lock digest
`sha256:a7363ec9f6d32a01e755a8868605542ca19cb602ddfaf34540e3620e9d2fb192`.

The deterministic ledger compared the report-derived operand
`use_supplied_founder_alleles_directly_in_hmm_emission` with the scientist's requirement and
emitted one Disclosure titled “One exact review-scoped method incompatibility.” The final bundle
contains zero Findings, zero ConditionalConcerns, one resolved MaterialQuestion, one Answer, and
three Disclosures; `open_question_ids` is empty and `model_access_after_lock` is false. The replay
preserves the audit ID, snapshot digest, semantic-lock digest, assessment counts, and all nine
repository paths with no added, changed, or removed path.

- **Acceptance criterion satisfied:** the answer-blind ordinary skill reached the scientist,
  recorded only the scientist's closed value, produced the bounded compatibility result after
  lock, and replayed without model access.
- **Remaining coverage limitation:** this completes one QTL interaction usability marker, not
  useful independent non-GeneBench applicability, detector qualification, numerical-causality
  proof, or broad scientific-workflow validation. Experiment 0021 separately supplies only the
  independent abstention and false-applicability evidence.
