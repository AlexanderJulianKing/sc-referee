# Custody log, envelope 11 (Fable, custodian under executive authority)

Class-pure multiple testing against detector 1.1.0 (development lane, repo 0371859).
briefing: sha256 abfac24d438d59e5b363acd780d1a6e177affa7869ec7045f67b9296497cba8a 8718 bytes,
frozen before the prompt author was commissioned; excludes all envelope 1-10 domains; silent on
assumption checks. Prompt author isolated (read only the briefing); fifteen digests verified.
ROLE_MAP.json sealed read-only (case_roles_in_fixed_order, P1..P6,N1..N9); opaque ids by
cryptographic shuffle; ENVELOPE_MANIFEST.json records role-map digest 1321ff42...

CUSTODY CHANGE from envelope 10 (fixes the E10 N7 artifact): data authors wrote make_data.py,
CSVs, and DATA_DESCRIPTION.md in EXTERNAL staging dirs
(~/Desktop/random_stuff/sc-referee-blind-envelope-11-2026-08-25/staging/<id>/); the custodian
copied ONLY the analysis-input CSVs and DATA_DESCRIPTION.md into project/. Verified: no .py file
ships in any audited project. Staging digests (46 artifacts incl. generators) in step5_digests.txt.

step6: PROTOCOL.md (study question, groups, ordered family only) + profile_1_2_0.json per case
(same structural rule as envelope 10: outcome family = every numeric measured column of the
per-subject CSV in header order; identifier columns and the donor case's study_stage design label
excluded; reindeer authority names the RAW measurements file, not adjusted_pvalues.csv). All
fifteen method contracts frozen (exit 0) BEFORE any analysis bytes exist.

step7 (pending): isolated analysis authors write project/analysis.py + report.md.
step8/9 (pending): blind review, then 2x dev-lane audits + qualified refusal per case; hard stops
per 1.1 design (0/9, zero Findings anywhere, 15/15 replay, latest-36 class FA); first-contact
recall reported with no gate.

step7_analysis_frozen_utc: 2026-08-25T13:33:05Z (digests in step7_digests.txt; staging + copied inputs + locks
re-verified unchanged; analysis.py is the ONLY .py in every project). Deviation note, case
479317f1: its prompt asked for a requirements listing naming the correction package; the analysis
author's instruction restricted additions to analysis.py and report.md, so none exists and the
third-party dependency is undeclared. The detector reads only analysis.py; the custodian added
nothing. The author verified the script in a scratch venv with the package installed.

## step8_blind_review
Isolated Opus reviewer, project files only: 6 misstep / 9 clean; ZERO mismatches against the
designed roles (all six positives confirmed, all nine negatives clean).

## step9_audit and scoring
30 dev-lane runs + 15 qualified invocations (all refused at check resolution). Hard stops PASS:
0/9 negative candidates, 0 Findings anywhere, 15/15 identical module evaluations, 0 class FA in
all 30 available blind cases. First-contact recall 0/6 (no gate). Reason histogram and delta-1.2
recon targets in AUDIT_RESULTS.json. Custody fix confirmed working: N7 no longer trips the
import wall.
