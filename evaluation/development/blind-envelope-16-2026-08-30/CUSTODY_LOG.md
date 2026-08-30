# Custody log, envelope 16 (Fable, custodian under executive authority)

Class-pure multiple testing vs detector 3.2.0 (development lane, repo 0676ea2).
briefing sha256 6ae8b0940ffa92bc89e4cfccf361fc25a97d4e9e534d74748cf14d14f81f3ba8 (10,662 B),
frozen before the prompt author was commissioned; excludes all envelope 1-15 domains; silent on
assumption checks. Prompt author isolated; fifteen digests verified against manifest.json (PASS).
ROLE_MAP.json sealed read-only (case_roles_in_fixed_order); opaque ids by cryptographic shuffle
(secrets.token_hex); role-map digest 056e2b8ecf1ff0d9a9a2010ea8e4b090e7bd9aeafc943e4e427a1d0b3349826b.

External-staging custody (E11-E15 protocol): data authored in
~/Desktop/random_stuff/sc-referee-blind-envelope-16-2026-08-30/staging/<id>/; only analysis-input
CSVs and DATA_DESCRIPTION.md will be copied into project/; no project-authored .py ships in any
audited project. PROMPT.txt copied verbatim into each staging dir, read-only, before data authors
were commissioned; the custodian did not read prompt contents.

Blind-scoring note: detector 3.2.0 includes the 3.1 question layer; blind runs carry NO
attestation file, questions are not catches, and scoring follows the section-11 lineage unchanged.

step5 (in progress): isolated data authors, one per case.

step5 complete: fifteen isolated data authors delivered CSV + DATA_DESCRIPTION.md per case
(generators remain in external staging; never copied). step5_digests.json sealed read-only.
Only CSVs + DATA_DESCRIPTION.md copied into cases/<id>/project/. Domain-named CSVs kept
(E13 precedent); material_input_path names them.

Profiles + PROTOCOL.md authored by custodian under the structural rule (outcome family =
every numeric measured column in header order; identifier and group columns excluded; the
eel case's `stage` discovery/validation design label excluded per the E12-E15 precedent; the
millet case's authority names the RAW file millet_irrigation.csv, not upstream_inference.csv,
per the standing raw-input rule). All fifteen method contracts frozen (exit 0) at
2026-08-30T05:48:23Z, BEFORE any analysis bytes exist.

step7 (pending): isolated analysis authors.

step7 complete: fifteen isolated analysis authors delivered analysis.py + report.md, each with a
clean exit-0 execution and report numbers taken from the executed run. step7_digests.json sealed
read-only; every step5 data digest re-verified byte-identical (PASS); no unexpected files.
Note: several authors' Write tool refused the report.md filename (a harness guard, not a case
property); those files were written via shell heredoc/copy by the same isolated author - content
provenance unchanged.

Next: isolated blind review, then 30 development-lane audit runs + 15 qualified-lane refusals.

Audit phase complete: 30 development-lane runs (all exit 0), 15 qualified-lane refusals (all
exit 2, check_id does not resolve; qualified-run dirs removed). Replay 15/15 identical
module_evaluation_digest. Blind review completed BEFORE any audit output existed in the tree.
Scoring from semantic.lock.json registry observations against the sealed ROLE_MAP: recall 1/6
(P1 caught), 0/9 negative accusation candidates, 0 Findings in all bundles. N1 resolved
covered/complete 5/5 - a TRUE clearance on a role-map negative (second blind covered/complete).
AUDIT_RESULTS.json sealed read-only. Envelope closed.
