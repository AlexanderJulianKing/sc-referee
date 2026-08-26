# Custody log, envelope 13 (Fable, custodian under executive authority)

Class-pure multiple testing vs detector 2.2.0 (development lane, repo a3aa829).
briefing sha256 b11fffc16770282e7c8e82aab3ed1cb1173624e1ab09b4e9a7481eed63b0486d (9,531 B),
frozen before the prompt author was commissioned; excludes all envelope 1-12 domains; silent on
assumption checks. Prompt author isolated; fifteen digests verified against manifest.json (PASS).
ROLE_MAP.json sealed read-only (case_roles_in_fixed_order); opaque ids by cryptographic shuffle
(secrets.token_hex); role-map digest 456780e6ab2a5decb7c99d31de9a6e898b7f3936e40bf378932aa51e3cda74cb.

External-staging custody (E11/E12 protocol): data authored in
~/Desktop/random_stuff/sc-referee-blind-envelope-13-2026-08-26/staging/<id>/; only analysis-input
CSVs and DATA_DESCRIPTION.md will be copied into project/; no project-authored .py ships in any
audited project. PROMPT.txt copied verbatim into each staging dir, read-only, before data authors
were commissioned; the custodian did not read prompt contents.

step5 (in progress): isolated data authors, one per case.

step5_data_frozen_utc: 2026-08-26T22:15:19Z. Fifteen isolated Opus data authors, one per
case, each reading only its staging PROMPT.txt. 46 staging artifacts (incl. generators) digested in
step5_digests.txt; only analysis-input CSVs and DATA_DESCRIPTION.md copied into project/; verified
no .py in any project/.

step6: PROTOCOL.md + profile_1_2_0.json per case, same structural rule as envelopes 10-12
(outcome family = every numeric measured column of the per-subject CSV in header order; the
identifier column and the group column excluded; the screen-time case's analysis_half design
label excluded per the E12 ra_baseline stage precedent; the tea-shading case's authority names
the RAW file tea_shading_measurements.csv, not upstream_adjusted_pvalues.csv, per the standing
raw-input rule). All fifteen method contracts frozen (exit 0) at
2026-08-26T22:15:19Z, BEFORE any analysis bytes exist.

step7 (pending): isolated analysis authors.

step7_analysis_frozen_utc: 2026-08-26T22:19:36Z (digests in step7_digests.txt, 91 rows incl.
semantic.lock.json per case; staging + copied inputs + locks re-verified unchanged; analysis.py
the only .py in every project; report.md present in all fifteen). Deviation note, case
325c686a92196956359a: the author's Write tool refused the filename report.md, so the author
staged the content in its scratchpad and copied it into place; content authored solely by that
isolated author, custodian added nothing.

step8 (pending): isolated blind scientific review.

## step8_blind_review
Isolated Opus reviewer: 7 misstep / 8 clean; one mismatch vs design (N6, the gated-screen role,
judged a misstep - the same realization dispute as envelopes 10 and 12; recorded, no FA either way).
All six P roles judged misstep; all other N roles judged clean.

## step9_audit and scoring
30 dev-lane runs + 15 qualified refusals (exit 2, check_id does not resolve on the qualified
surface; partial refusal output dirs removed, refusals recorded in AUDIT_RESULTS.json).
Hard stops PASS: 0/9 negative candidates, 0 Findings in all 30 bundles, 15/15 identical
module_evaluation_digest replays, 0 class FA in all 60 available blind class cases.
FIRST-CONTACT RECALL 3/6 (P1 sequential, P3 collection, P4 helper; all operand
no_recognized_family_correction, classification none). Misses: P2
extra-registered-test-outside-authorized-family, P5+P6 authorized-reader-lineage-unavailable.
Promotion window E12+E13+E14: 5/12 so far; E14 needs >=4/6.
