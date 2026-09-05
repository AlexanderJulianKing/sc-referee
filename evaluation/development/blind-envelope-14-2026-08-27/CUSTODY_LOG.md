# Custody log, envelope 14 (Fable, custodian under executive authority)

Class-pure multiple testing vs detector 2.3.0 (development lane, repo 15e8525).
briefing sha256 2a4fe3cd48a2966dbe4d2b9d070dc98ea06cff45b1ceec0f7bd636a4adb01932 (9,894 B),
frozen before the prompt author was commissioned; excludes all envelope 1-13 domains; silent on
assumption checks. Prompt author isolated; fifteen digests verified against manifest.json (PASS).
ROLE_MAP.json sealed read-only (case_roles_in_fixed_order); opaque ids by cryptographic shuffle
(secrets.token_hex); role-map digest b9f56f863be69882b07d98423d55691bd4f1bafec1bfa41a83edd080a951e69e.

External-staging custody (E11-E13 protocol): data authored in
~/Desktop/random_stuff/sc-referee-blind-envelope-14-2026-08-27/staging/<id>/; only analysis-input
CSVs and DATA_DESCRIPTION.md will be copied into project/; no project-authored .py ships in any
audited project. PROMPT.txt copied verbatim into each staging dir, read-only, before data authors
were commissioned; the custodian did not read prompt contents.

step5 (in progress): isolated data authors, one per case.

step5_data_frozen_utc: 2026-08-27T05:51:28Z. Fifteen isolated Opus data authors, one per
case. 46 staging artifacts digested in step5_digests.txt; only analysis-input CSVs and
DATA_DESCRIPTION.md copied into project/; verified no .py in any project/.

step6: PROTOCOL.md + profile_1_2_0.json per case, same structural rule as envelopes 10-13
(outcome family = every numeric measured column in header order; identifier and group columns
excluded; the honey case's analysis_set design label excluded per the E12 stage / E13
analysis_half precedent; the malaria-trial case's authority names the RAW file
trial_participants.csv, not upstream_adjusted_pvalues.csv, per the standing raw-input rule).
All fifteen method contracts frozen (exit 0) at 2026-08-27T05:51:28Z, BEFORE any
analysis bytes exist.

step7 (pending): isolated analysis authors.

step7_analysis_frozen_utc: 2026-08-27T05:56:10Z (digests in step7_digests.txt, 91 rows incl.
semantic.lock.json per case; staging + copied inputs + locks re-verified unchanged; analysis.py
the only .py in every project; report.md present in all fifteen). Deviation notes: case
2327c03c (specialist-package role) - its prompt asked for a requirements list, the author's
instruction restricted additions to analysis.py and report.md, so dependencies are named in the
report and the analysis.py docstring (docstrings stripped before analysis; no detector impact;
same as the E12 678e94e7 precedent); the same case's prompt asked for a marginal-p outcome the
frozen data does not contain - the author correctly reported actual values without touching data.
Case cccde3c6's author noted the PROTOCOL.md-vs-prompt tension (that tension is the designed
misstep for a positive role; nothing modified). The custodian added nothing.

step8 (pending): isolated blind scientific review.

## step8_blind_review
Isolated Opus reviewer: 7 misstep / 8 clean; ZERO mismatches vs design (first envelope in the
class with a perfect blind review; even the N6-style gated role read clean).

## step9_audit and scoring
30 dev-lane runs + 15 qualified refusals (exit 2; partial refusal output dirs removed).
Hard stops PASS: 0/9 negative candidates, 0 Findings in all 30 bundles, 15/15 identical
replays, 0 class FA in all 75 available blind class cases. FIRST-CONTACT RECALL 1/6 (P1
sequential, candidate/none). Misses: P2 pvalue-family-collection-unresolved, P3
test-battery-cardinality-unresolved, P4+P5 authorized-family-test-census-incomplete, P6
unresolved-manual-correction-present. The 2.3 reader-path admission held on arrival (zero
reader-lineage abstentions envelope-wide); the dominant new wall is the earlier
census-incomplete wall (also 6 of 9 negatives). Promotion window E12+E13+E14 = 6/18: NOT
reached; window slides.
