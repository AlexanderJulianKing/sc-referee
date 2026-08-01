# 8. Reporting and user experience

## 8.1 Reporting objective

The report must help a scientist decide what to correct, what to clarify, what remains conditional, and what was not inspected without overstating certainty. Record type, section placement, counts, and impact language all enforce epistemic separation.

## 8.2 Output products

Every audit emits:

1. canonical per-record JSON or JSONL;
2. an `AuditBundle` exchange record;
3. a content-addressed semantic lock;
4. a self-contained human-readable HTML report;
5. a concise agent-facing summary generated from canonical records; and
6. coverage and performance records for complete and partial runs.

The HTML is a view. It is never the only durable copy of evidence. It is rendered with Jinja2 using explicit autoescaping and strict undefined-variable handling; all required CSS and assets are embedded or vendored locally.

## 8.3 Run status vocabulary

Run state describes execution, not scientific correctness:

```text
complete_within_plan
partial_budget_exhausted
partial_evidence_unavailable
partial_error
cancelled_with_artifacts
```

The UI must not transform these into pass/fail, valid/invalid, safe/unsafe, publication-ready, or a global risk level.

## 8.4 Human report structure

### A. Audit identity and scope

Repository snapshot, Git state when available, publication-surface state, mode, scheduling cutoff and hard deadline, elapsed and paused time, schema and detector versions, semantic-lock digest, external evidence and environment-reconstruction summary, and partial-run status.

### B. Executive assessment

Counts are reported separately:

- claims needing correction: Findings;
- conditional concerns requiring review;
- material questions blocking interpretation; and
- disclosures about coverage, lineage, opacity, availability, or reproducibility.

No aggregate “total findings” includes uncertain or informational records.

### C. Claims needing correction

Only demonstrated Findings appear here. Each item includes the bounded statement, root cause, exact evidence, all five admission checks, non-inferences, severity, affected descendants, source navigation, detector maturity, coverage boundary, and scientist disposition. Publication materiality is shown only when the final publication surface is resolved; otherwise it is explicitly unassessed and candidate-specific.

### D. Conditional concerns

Each item begins with its condition:

> If `sample_id` identifies biological donors, the fitted model appears to treat repeated donor measurements as independent.

It links to the exact MaterialQuestion, potential impact, affected claims, evidence already searched, and what would resolve it. It has no severity badge.

### E. Questions blocking interpretation

Each question states why it matters, plausible answers including unknown, sources already searched, blocked detectors, linked conditional consequence, priority, and answer controls.

### F. Disclosures

Separate subsections cover incomplete lineage, unsupported operations, opaque dependencies, unavailable data or execution evidence, weak data identity, unresolved publication scope, approximate environment reconstruction, external evidence reproducibility, pending ReproductionRequests, parser and detector gaps, uninspected paths, and reproducibility limitations. Disclosures are not worded as scientific defects.

### G. Claim lineage explorer

For each final claim, show report source, result, operations, decisions, inputs, environment, Scientific Contract, lineage grade, and any assessment descendants.

### H. Coverage, performance, and provenance

Show whole-project inventory, deep-inspection denominator, claims reached, detector-target coverage, parser support, unanswered semantics, deadline use, host-model interruption if any, cache behavior, external retrievals, environment reconstruction, execution privilege, ReproductionRequests, and tool digests.

## 8.5 Wording policy

Permitted examples:

- “The report describes the linked contrast as positive, while the linked coefficient is negative under the established orientation.”
- “If `sample_id` identifies donors, the model appears to treat repeated donor measurements as independent.”
- “The custom binary was treated as an opaque boundary; its internal error model was not inspected.”
- “No issue was detected by detector D within the two model paths it covered.”

Prohibited strengthening includes:

- “The biological conclusion is false” when only report/result direction disagreement is established;
- “The effect is biased upward” without independent evidence for direction;
- “The model is invalid” when only an omitted contract term is demonstrated;
- “No issue found” without coverage qualification; and
- “Critical” on a question, conditional concern, or disclosure.

## 8.6 Clean-audit wording

A zero-Finding report should begin approximately:

> **No claims needing correction were identified within the inspected evidence and validated detector coverage.** The audit inspected 18 of 20 final-claim paths. Two material questions remain unresolved, one claim depends on an opaque external operation, and three detector coverage gaps are documented below. This is not a determination that the analysis is correct.

There is no green pass badge, global risk rating, or publication-ready state.

## 8.7 Root-cause presentation

One root card contains:

- root operation, decision, claim, or semantic mismatch;
- primary bounded statement;
- affected claims and artifacts;
- relationship paths;
- maximum severity and breadth of publication materiality;
- unaffected claims that bound the scope; and
- dispositions or corrections.

Textually repeated descendants are not independent Findings.

## 8.8 Impact terminology

| Record | Public impact fields |
|---|---|
| Finding | Severity; publication materiality when the final surface is resolved, otherwise `unassessed` |
| ConditionalConcern | Potential impact and review priority |
| MaterialQuestion | Question priority and blocked analyses |
| Disclosure | Importance and interpretive consequence |

User-facing numerical confidence probabilities are prohibited until calibration and a later explicit design decision justify them. Assertion records may retain qualitative certainty with an evidence basis.

## 8.9 Scientist disposition and adjudication

A scientist may mark a Finding or concern `confirmed`, `accepted_risk`, `disputed`, `not_material`, `deferred`, or `corrected_in_later_revision`. The response records rationale, provenance, authority scope, and any new semantic evidence.

Objective `adjudicated_true_positive`, `adjudicated_false_positive`, `detector_defect`, or `insufficient_evidence` labels belong to independent Adjudication records. Neither response deletes the original detector output.

## 8.10 Question interaction

Questions are batched after the initial static and semantic pass, ranked by affected-claim materiality and expected change to the assessment. The scientist may answer, select unknown, or defer. Deferred questions remain explicit and the audit continues.

## 8.11 Progress interaction

Progress is expressed scientifically:

```text
Inventory complete: 426 files classified.
Publication surface selected from declared build target: manuscript/results.qmd.
18 final claims found; 14 have complete static lineage.
3 material questions require resolution.
Running 9 applicable detector families on 22 targets.
```

Low-level model call and parser event streams are not shown unless debugging is requested.

## 8.12 Audit diffs

A diff distinguishes:

- new, resolved, withdrawn, or changed Findings;
- conditional concerns promoted, resolved, or changed;
- answered, superseded, or newly material questions;
- new or resolved Disclosures;
- claim and contract changes;
- detector and coverage changes; and
- code correction versus lost detector coverage.

## 8.13 Accessibility and portability

The report uses semantic headings, keyboard-accessible controls, text alternatives, no color-only meaning, clean printing, escaped project content, core content without JavaScript, and no remote assets. Optional bundled JavaScript may add filtering or graph navigation but cannot be required to read findings, questions, disclosures, lineage, or coverage.

## 8.14 Agent-facing summary

The concise summary contains run state, report path, counts by the four record types, highest-materiality Findings, high-priority questions, material Disclosures, semantic-lock state, and the next deterministic command. It is generated from records rather than a free-form LLM review.

## 8.15 Report integrity tests

The renderer tests:

- zero-Finding non-certification wording;
- no global pass or risk state;
- no severity on uncertain records;
- question–concern linkage;
- exact source-reference presence;
- count reconciliation;
- detector maturity display;
- explicit non-inferences; and
- prevention of wording stronger than the record permits;
- unassessed materiality when publication scope is unresolved;
- deadline and partial-run reconciliation; and
- external-evidence and ReproductionRequest disclosure.


## 8.16 Capability and qualification disclosure

Every report embeds the applicable capability-matrix slice. For each inspected path it shows the exact parser and package coverage, semantic-profile status, detector maturity, review basis, strongest permitted output, tested versions, inferred compatibility, abstention conditions, and known gaps.

A Finding emitted by an agent-qualified detector displays `validated` or `publication-grade` maturity together with `agent-panel qualification`; it does not imply human expert endorsement. Human or mixed review, when present, is shown separately.
