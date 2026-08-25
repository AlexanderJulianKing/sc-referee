# Custody log, envelope 10 (Fable, custodian under executive authority)

Class-pure multiple testing per design Revision 2.3
(sha256 8adddfaca6729e4cf7e87ba0044c295b848d29eba37ae7003a5a6e4c4888a303), section 11.
briefing: sha256 b62979ccfc22ec8fa43bcf5e3450dc0d3a8f0732ba71cde393e32b396672c62e 8398 bytes,
frozen 2026-08-24 before the prompt author was commissioned; excludes all envelope 1-9 domains and
is silent on assumption checks per design section 11.

Prompt author: isolated Opus subagent, read only the briefing, wrote fifteen prompts plus
manifest.json; all fifteen digests verified against the manifest before sealing. ROLE_MAP.json
(key case_roles_in_fixed_order, order P1..P6,N1..N9) sealed read-only; opaque 20-hex case ids
assigned by cryptographic shuffle. ENVELOPE_MANIFEST.json records the role-map digest.

step4_prompts_frozen: see ENVELOPE_MANIFEST.json prompts_frozen_utc.

## step5_data
One isolated data author per case (two relaunched once after connection drops before any file was written). Each received only its case PROMPT.txt and authored ONLY
make_data.py (deterministic), the CSV(s), and DATA_DESCRIPTION.md. No analysis, no report, no
statistical code. Custodian digests all artifacts before step 6.

## step6_contracts
Custodian writes PROTOCOL.md (study question, groups, ordered outcome family only) and
profile_1_2_0.json per case (check:authorized-complete-family-correction-over-code-test-battery,
candidate complete-correction-over-authorized-outcome-family, authorized_test_family with
material_input_path, group_contrast_column, outcome_columns in the declared order,
family_member_rule one-two-group-test-per-named-outcome-column, correction_scope
complete-authorized-family), then freezes method contracts BEFORE any analysis bytes exist.

## step7_analysis (pending)
One isolated analysis author per case: receives PROMPT.txt plus the project data files, writes
analysis.py and report.md.

## step8_blind_review, step9_audit (pending)
Blind scientific reviewer, then audit runner on the development lane. Hard stops per design
section 11: 0/9 negative candidates, zero Findings anywhere, byte-identical 15/15 replay,
no false accusation in the latest 36 class-specific blind cases. First-contact recall reported
as candidates/6 with no pass gate.

step5_data_frozen_utc: 2026-08-25T05:06:03Z (digests in step5_digests.txt; 46 artifacts, re-verified unchanged after contract runs)
step6_contracts_frozen_utc: 2026-08-25T05:06:03Z

All fifteen exited 0. Profile scientific_check_requirement_v1 1.2.0, check
check:authorized-complete-family-correction-over-code-test-battery, candidate
complete-correction-over-authorized-outcome-family. Outcome family per case = every
numeric measured column of the per-subject CSV in header order (identifier, group, and
the wheat case's stage_split design label excluded); same structural rule for every case,
decided from CSV structure alone. Camel case authority names the RAW per-subject file, not
the upstream adjusted-p file, per the envelope 3-9 raw-input rule.

| Case | Group column | Family size | CSV | Lock digest (sha256) |
| --- | --- | --- | --- | --- |
| 104493a5d99796a002c0 | conche_group | 5 | chocolate_batches.csv | 6e9c7cdf89d6a9cb92cbac2dd59971453af72dc5f8142f1e31818f98c20305fe |
| 3ff45fce2a45e0959fdb | dressing_group | 6 | venous_ulcer_dressings.csv | 3768bbe87c647c756fdd1a2077b7324a9cbfdd54dfa3a2e5c1ed810132411bba |
| 4907932548f745afe942 | site_group | 5 | air_quality_winter.csv | f5963750abad2ef477ccde7fbb5d2a8b1bd7d5880705e1b254973fcb2be25f5a |
| 60f96fabb7129d662b23 | habitat_group | 4 | fox_habitat_measurements.csv | e6a8a10aa277121a7d12b371113668135e6e78a8a36fba42ae82a8b5fb7a3dc4 |
| 6d2fdc67ab98bc0e0e6e | supplement_group | 5 | camel_milk_outcomes.csv | 6b81e151861b34b5960aa8c171525813ba66ad94dc6caa4fb6c819313dc580ad |
| 7296b0e2cf7faeefca64 | feed_group | 3 | calves.csv | 61111c8cdde007a93b75e54ef048202951c126b362ca6204f6586a4e15cba9de |
| 8d83210468ecde012e4a | program_group | 6 | wheat_fungicide_trial.csv | 7f35c3c3aaf81d6fa4508b464282c3eb13214b5be3b6157a25793967483aa4b0 |
| 9be74afbe9659bd50580 | plasma_group | 5 | almond_plasma_lots.csv | 97b6579149e4cfd48a8b13efdbeb07469502fa218b0fafcb7711412df53fbfaf |
| b787314c170f8f690060 | program_group | 4 | pulmonary_rehab_outcomes.csv | 0247fb62193c2b1cb30e53fe9842eae4702df85a98a0ca30605c1e41e71b7648 |
| c51d08801b3d0ba4e532 | pool_system | 7 | lifeguard_airway.csv | 446ee708c9dbc2a9145b86f1b642f275f9e2c332a45af754f09625e0279beba0 |
| cb2e207276a0dc3247bb | n_rate_group | 4 | sorghum_nitrogen_plants.csv | 08c63dcac7a930a5307ce41f622e4149b5510357098da48e64df8d4dd91e928a |
| dfc9f20a94ecefc7f7b5 | harvest_group | 5 | hemp_harvest_timing.csv | bba434dc455a301b74945c94eb8691c34c68a1d9c6c3b75bec247841a74d4b56 |
| e1bce32a32e3b2df475e | exo_group | 5 | exo_picking_trial.csv | 9510252a424daf3ff1a2309d42a8b7e08504cd20fffb4276ef340105cfd6aba2 |
| ebbb8a5dbc2664257144 | liner_group | 4 | heat_strain.csv | 5bd55c6b399f7354bfcf6489d6fc6172d29831906fbcbd59ad0b9e14ab4c1135 |
| f4cf62caeb8ad68dc5b3 | disturbance_group | 5 | marmots.csv | f464171cf9cb61a4c16dcdd236f285a31b7531b847b0efe7eadc65b3d6205a4d |

step7_analysis_frozen_utc: 2026-08-25T05:11:02Z (digests in step7_digests.txt; step5 artifacts and locks re-verified unchanged; one analysis author used a scratchpad venv for a third-party package rather than touching the repo venv)

## step8_blind_review
Isolated Opus reviewer, project files only: 7 misstep / 8 clean. All six designed positives
confirmed missteps; N6's realization contested (descriptive effect-size gate, not level-alpha);
recorded in AUDIT_RESULTS.json role_realization_notes.

## step9_audit and scoring
30 development-lane runs (2 per case) + 15 qualified-lane invocations (all refused at check
resolution, as designed). All hard stops PASS: 0/9 negative candidates, 0 Findings anywhere,
15/15 byte-identical module evaluations across runs, 0 class-specific FA in all 15 available
blind cases. First-contact recall 0/6 (no pass gate). Reason histogram and delta-1.1 recall
diagnosis in AUDIT_RESULTS.json. Note for the record: the initial reason extraction wrongly
grepped the manifest's closed-reason list; the authoritative per-case reasons come from
scientific_check_registry.evaluation in each run's semantic.lock.json.
