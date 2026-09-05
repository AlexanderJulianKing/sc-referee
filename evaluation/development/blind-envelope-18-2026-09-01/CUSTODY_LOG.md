# Custody log, envelope 18 (Fable, custodian under executive authority)

Class-pure multiple testing. Detector under test: code_csv_multiple_testing 3.4.0 (development
lane); the exact repo commit is recorded below at audit time, because the authoring stages
(briefing, prompts, data, contracts, analyses, blind review) are detector-independent and were run
in parallel with the 3.4 merge gate.
briefing sha256 f3f6e47b91f69a511db5120d8a14a713ac82dbb0d719034349338e3cf8d40aa6 (11,435 B),
frozen before the prompt author was commissioned; excludes all envelope 1-17 domains; silent on
assumption checks. External-staging custody per E11-E17 protocol
(~/Desktop/random_stuff/sc-referee-blind-envelope-18-2026-09-01/).

Promotion window: E17 (4/6) + E18 >= 7/12, so E18 needs >= 3/6.

Prompt author (isolated) commissioned 2026-09-01.

Prompt author delivered; fifteen digests verified against manifest.json (PASS). ROLE_MAP.json
sealed read-only (case_roles_in_fixed_order, secrets.token_hex ids); role-map digest
cd830c2a79ea80f4fe310d8db09893b29c74fdf25d33975c713d9161feff3d92. PROMPT.txt staged read-only
per case before data authors were commissioned; custodian did not read prompt contents.

step5 (in progress): fifteen isolated data authors commissioned.

step5 complete: fifteen isolated data authors (generators stay in staging); step5_digests.json
sealed read-only; only CSVs + DATA_DESCRIPTION.md copied into cases/<id>/project/ (authors named
their files data.csv, E15 style). Profiles + PROTOCOL.md authored under the structural rule
(outcome family = every numeric measured column in header order; identifier and group columns
excluded; the coeliac case's study_half discovery/validation design label excluded per E12-E17
precedent; the salt-fermentation case's two-level numeric salt_pct is the group contrast column;
the rapeseed case's authority names the RAW data.csv, not adjusted_pvalues.csv, per the standing
raw-input rule). All fifteen method contracts frozen (exit 0) at 2026-09-01T20:20:02Z,
BEFORE any analysis bytes exist.

step7 (pending): isolated analysis authors.

step7 complete: fifteen isolated analysis authors delivered analysis.py + report.md, each with a
clean exit-0 execution and report numbers taken from the executed run. One author (case
0ebcfa6ddcba137a394a) also delivered requirements.txt because its prompt required a dependency
listing; it is an author deliverable (not a script), recorded in step7_digests.json. step7 sealed
read-only; every step5 data digest re-verified byte-identical (PASS).

Next: isolated blind review (before any audit output exists), then audits once 3.4 merges.

Isolated blind review completed (BLIND_REVIEW.md, verdicts MISSTEP 7 / SOUND 8 / UNCERTAIN 0),
BEFORE any audit output existed in the tree. The envelope now holds at the audit gate: audits run
against detector 3.4.0 once dev/mt-34 merges into dev/dependence-growth; the merge commit is
recorded here at that time.

Audit gate opened 2026-09-02: dev/mt-34 merged into dev/dependence-growth at
f85d4f45fafb924089262e817c24425ae2cec7e2 (detector code_csv_multiple_testing 3.4.0 development
lane after MT 3.4 audit-fix rounds 1-7). The round-7 Codex re-audit returned FIX-REQUIRED; its
residual routes and read-only losses were measured through the real pipeline, recorded in ADR-0079
(custodian post-audit note), and queued as MT 3.5; the custodian (Alex, 2026-09-02) chose to merge
and audit this envelope on that lane. Full gate on the merged tree: 9702 + 422 passed, 1 skipped
(pinned Claude CLI build absent), one manifest-consistency failure caused solely by this uncommitted
custody log.

Contract re-freeze (deviation, recorded): the fifteen method contracts frozen 2026-09-01T20:20Z
were bound to the round-4 check manifest (implementation digest fb441237...), and the merged lane
refuses a multiple-testing contract whose resolved profile differs from the active lane's
(method_contract_run: "scientific requirement is incompatible with the active check lane"). The
only differing field is the check implementation digest (now bb1e2b96...); check version 3.4.0,
profile 1.2.0, and the human-authored semantic role authority are identical in every case. Each
contract was therefore re-frozen on the merged detector into cases/<id>/method-contract-r7/ from
the same sealed inputs (PROTOCOL.md, profile_1_2_0.json, same actor id), with the original sealed
method-contract/ directories left untouched. The re-freeze reads the project directory as it now
stands, so its snapshot includes the sealed step-7 analysis bytes; the contract content is
determined by the protocol and profile alone. Digests: refreeze_r7.log and each
method-contract-r7/semantic.lock.json. Audits run against the r7 locks.

Audit driver launched 2026-09-02T17:18:26Z as a detached local process (E17 pattern: two
development-lane runs plus one qualified-lane refusal per case, --material-input data.csv, no
--report), logging to audit_driver.log and ending with DRIVER-DONE. ROLE_MAP.json stays sealed
until scoring.

Audit phase completed 2026-09-02T17:21:13Z (DRIVER-DONE: 30 development runs exit 0, 15 qualified
refusals exit 2 with the resolve message; qualified-run dirs removed). Replay 15/15 identical.
Scoring against the sealed ROLE_MAP (opened only after DRIVER-DONE): recall 2/6 (P1, P4 uncorrected
families), 0/9 negative candidates, 0 Findings in all bundles, one true clearance (N1
covered/complete 5/5 on a role-map negative). Window E17+E18 = 6/12; promotion threshold 7/12 not
reached. AUDIT_RESULTS.json sealed. Envelope closed.
