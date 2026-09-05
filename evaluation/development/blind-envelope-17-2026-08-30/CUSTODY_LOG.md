# Custody log, envelope 17 (Fable, custodian under executive authority)

Class-pure multiple testing vs detector 3.3.0 (development lane, repo 73eb49b).
briefing sha256 1c2e5f0b058ab0b12550a64c0c25976e38c154369ceaf063a237d0488b13b26f (11,068 B),
frozen before the prompt author was commissioned; excludes all envelope 1-16 domains; silent on
assumption checks. External-staging custody per E11-E16 protocol
(~/Desktop/random_stuff/sc-referee-blind-envelope-17-2026-08-30/).

Promotion window: E17+E18 >= 7/12.

Session note: internet cutoff expected ~3:00 PM PDT 2026-08-30; the chain halts at a clean stage
boundary if the cutoff lands mid-envelope, and each completed stage is sealed before the next
begins, so a resume re-runs only unsealed stages.

Prompt author (isolated) commissioned 2:35 PM.

Prompt author delivered 2:43 PM; fifteen digests verified against manifest.json (PASS).
ROLE_MAP.json sealed read-only (case_roles_in_fixed_order, secrets.token_hex ids); role-map digest
004a87be3448c1736f24ac48d0deb155694ee7da08670d02918ac8e09d4cea9e. PROMPT.txt staged read-only
per case before data authors were commissioned; custodian did not read prompt contents.

step5 complete 2:49 PM: fifteen isolated data authors (generators stay in staging);
step5_digests.json sealed read-only; only CSVs + DATA_DESCRIPTION.md copied to project/.
Profiles + PROTOCOL.md authored under the structural rule (outcome family = every numeric
measured column in header order; identifier and group columns excluded; the cane case's
study_half discovery/validation design label excluded per E12-E16 precedent; the daphnia case's
two-level numeric temperature_c is the group contrast column, excluded from the family; the
vanilla case's authority names the RAW file vanilla_curing_pods.csv, not adjusted_pvalues.csv,
per the standing raw-input rule). All fifteen method contracts frozen (exit 0) at
2026-08-30T21:47:41Z, BEFORE any analysis bytes exist.

step7 (in progress): fifteen isolated analysis authors commissioned 2:48 PM.

step7 complete and sealed 2:50 PM: fifteen analysis.py + report.md, each exit 0; step7_digests.json
read-only; every step5 data digest re-verified byte-identical (PASS). Isolated blind review
completed 2:56 PM (BLIND_REVIEW.md, verdicts MISSTEP 7 / SOUND 8 / UNCERTAIN 0), BEFORE any audit
output existed in the tree. Audit driver (30 development-lane runs + 15 qualified refusals)
launched 2:57 PM as a detached local process logging to audit_driver.log; scoring from
semantic.lock.json registry observations against the sealed ROLE_MAP follows in the next session
(internet cutoff 3:00 PM PDT).

Audit phase completed offline by the detached driver (DRIVER-DONE: 30 development runs exit 0,
15 qualified refusals exit 2 with the resolve message; qualified-run dirs removed). Replay 15/15
identical. Scoring against the sealed ROLE_MAP: recall 4/6 (P1/P2/P4 uncorrected families,
P5 strict_subset [2,3]/8 - first blind strict_subset), 0/9 negative candidates, 0 Findings in all
bundles. AUDIT_RESULTS.json sealed read-only. Envelope closed.
