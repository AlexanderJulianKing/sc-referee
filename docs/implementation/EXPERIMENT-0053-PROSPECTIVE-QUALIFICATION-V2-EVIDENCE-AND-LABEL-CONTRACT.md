# Experiment 0053: Prospective qualification v2 evidence and label contract

- **Status:** Evaluation-private contract and first finite verifier profile implemented; verifier
  not qualified or frozen; no v2 cases assigned
- **Date:** 2026-08-04
- **Policy effect:** None; this is a temporary evaluation experiment, not an accepted public
  schema or production authority source
- **Held-out impact:** The v1 held-out block remains sealed and is not reused
- **Finding impact:** None
- **Execution impact:** None

## Pilot diagnosis

The v1 pilot froze 2 `issue_present`, 30 `issue_absent`, 35 `indeterminate`, and 3 `unsupported`
labels. Eighteen of the indeterminate cases had two providers agree on a demonstrated issue and
root but used synonymous free-text issue classes. Ten more cases exposed both a conforming and a
conflicting path without binding the reported result to either producer. Another ten lacked enough
public provenance; only three satisfied the v1 exact unsupported branch.

The v1 freezer behaved as implemented, but its inputs were not shaped well enough for the intended
study. Loosening demonstrated-issue criteria after seeing labels would be invalid. V2 instead fixes
the authoring and review contracts before any new cases exist.

## V2 design

1. Each relation envelope freezes one canonical `issue-class:*` identifier. Stage-2 reviewers
   select that exact enum or `issue_absent`; their bounded descriptions remain retained evidence but
   do not enter deterministic label resolution.
2. Each author freezes an exact selected-result declaration containing the selected report span,
   one static producer span, required source operands, and every alternative producer span. Dynamic
   selection is explicitly unsupported.
3. The author declaration has `authority: none`. A fresh independent verifier must rederive the
   selected result, producer, and operand path from immutable bytes. Failed, ambiguous, incomplete,
   and unsupported verification cannot yield `issue_present`.
   The first temporary verifier profile is limited to a closed Python/static-report grammar. Its
   retained case inventory includes whether each regular file was executable because that bit is
   an input to the profile's exclusive report/producer/operand role decision. It rejects
   executable or shebang-bearing reports and operands, unclassified files, and unsupported source
   artifacts. These evaluation-private records have no qualification or Finding authority.
   The implemented v1 profile supports only strict, straight-line Python with a literal
   `pathlib.Path` report writer, exact retained-output byte equality, and statically rederived
   `.csv`/`.tsv` operands. Text-mode operands and reports are restricted to ASCII bytes with LF
   line endings, and the runtime encoding, platform, and line separator are implementation-locked;
   this prevents locale encoding and universal-newline translation from being mistaken for exact
   byte reproduction. Python source must use the default UTF-8 byte interpretation; byte-order
   marks and PEP 263 encoding cookies are unsupported so source parsing cannot diverge from Python's
   executable-byte semantics. Arbitrary Python, other languages, dynamic paths, executable inputs,
   extra files, and unclassified roles are unsupported rather than guessed.
4. Label resolution requires two distinct Stage-2 reviewers from two providers, with author,
   reviewer, and independent-verifier identities and providers mutually disjoint. It also requires
   exact review and validation digests, one exact selected-result binding digest, and complete
   finite counterevidence status.
5. Verified cross-provider `issue_present` reviews resolve through the canonical enum even when
   their prose differs. Present/absent disagreement is retained as `review_disagreement`.
   Ambiguous, insufficient, and unsupported evidence receive distinct labels rather than being
   collapsed.
6. The new ten-envelope template requires 140 wholly new assignments. The complete-domain
   denominator envelope uses `check:complete-domain-exposure-denominator`; it does not retrofit the
   label-visible v1 positives.

## Implemented artifacts

- `evaluation/src/sc_referee_evaluation/prospective_qualification_v2.py`
- `evaluation/src/sc_referee_evaluation/prospective_selected_result_verifier.py`
- `evaluation/prospective-qualification-v2/ten-envelope-study.template.json`
- `scripts/build_prospective_qualification_v2_template.py`
- `tests/test_prospective_qualification_v2.py`
- `tests/test_prospective_selected_result_verifier.py`

The tests cover exact byte replay, fresh-location replay, missing operands, dynamic paths,
result/report drift and span containment, duplicate and non-Python alternative producers, closed
file roles, executable/shebang rejection, import and statement order, forward references, caller
forgery, tree and evaluator ceilings, symlinks, participant independence and chronology, canonical
issue-class resolution, ambiguity, insufficiency, unsupported structure, provider disagreement,
and post-review mutation. Stage-2 label freezing now replays the validation from case bytes; a
handwritten validation summary cannot substitute for the verifier artifact.

## Remaining external gate

No v2 authors, reviewers, authenticators, cases, labels, thresholds, held-out outcomes, metrics, or
promotion decisions exist. The first verifier implementation exists, but it has not undergone its
required independent qualification or freeze. It therefore cannot yet supply qualification
evidence, and opaque assignments must not be created. This experiment cannot be cited as verifier
qualification, detector qualification, or a production Finding capability.
