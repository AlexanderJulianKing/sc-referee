# Custody log, envelope 2 (Fable, custodian under executive authority)
briefing: sha256 9ffc4f7ee7ea9a59677c75455ed25b396814a430c72b050c271404ccf89d40fc 3363 bytes, frozen 2026-08-21 ~23:30 before prompt author commissioned
step4_prompts_frozen: see ENVELOPE_MANIFEST.json prompt_records
step5_data_frozen_utc: 2026-08-22T07:38:37Z
15b07ef7670800ba88e0 pup_masses.csv 8b08dcafee8a67da1ddc5e890faa1a3929942f9f5d17950222ff97b6dbeaf252
15b07ef7670800ba88e0 DATA_DESCRIPTION.md f8e4f9eb6e331218e3ba49f61f905bc4a1df3060e859851d796ef060523499e7
15b07ef7670800ba88e0 make_data.py bbe0e86158fd12f6f1a8bf05663bf02d775ea3d9d6c0a0d4982440e3f5940fc8
2df3396d80adbb63dffb milk_yield.csv ef72d990ccea7884a8b8a33527268610cf90dcb31a6b88c5f4dbea5f0b82f653
2df3396d80adbb63dffb DATA_DESCRIPTION.md 16ba10b3adb9b0ac738b488aa452a987498f626693d2e6d5c4a8a200afa30752
2df3396d80adbb63dffb make_data.py 4386e9c4036f0a8adfbd717433e87e42cb4785fdde9b9b43b28d511e9c6e9d62
5ef43dbf631adcf3daec greenhouse_tomato_yield.csv 5df2ea8930736d0c32e80b5a67d070729b6c31230e476b08985306f46113c2bc
5ef43dbf631adcf3daec DATA_DESCRIPTION.md dd63bfc29e5a819d1c7773d02d4b006e5c20c6ab77ba66106ff5802209b85881
5ef43dbf631adcf3daec make_data.py 7f7ee72a86038d988cc8d487cab6b602c516ffed5598bdf458d6d3a1c9f42823
6090fc1b1b6dbfcd6eee kicknet_samples_raw.csv a579220fe367191caeb08844d3800c3c1abb9751637b7bc0d5ea5266779c94dc
6090fc1b1b6dbfcd6eee reach_summary.csv 9983b6d441f40324f1985571eabab3484ce5a85c6f9a55b01b8ffe48bfe42997
6090fc1b1b6dbfcd6eee DATA_DESCRIPTION.md 3cf9ea65150e88aef122645d91001be4f2458985ad637fe5792c4b8aa9c668f6
6090fc1b1b6dbfcd6eee make_data.py 816c38604eb20e16803fcd41003b7e92c3659cb7084d437ed2281af9406a9439
ca18f96d45dff1b921ad tagged_tree_increment.csv 6458307ed0201ca73bef470b35458abce1e3c015cb14ec326d3c5fab9c6ad6c0
ca18f96d45dff1b921ad DATA_DESCRIPTION.md 6bae4b2ddd3c5f7866af92734a74e5378940601fc4b2515e1f8add0efcd0b24a
ca18f96d45dff1b921ad make_data.py 8326421bf5babc503eab8c53d1637a5010c50e98699db8c5f4e181e55811a907
d4d95cdd4f4e698d675c organoid_teer.csv 71d094db7c3941b14bbf6bde839335d1fdc830cd6d23a8dc0f04897701ef0d4b
d4d95cdd4f4e698d675c DATA_DESCRIPTION.md a7c1182565f1b8c0c7a983b8c3ce8d421bcb2116a9c1015ebe2de217d8150dd7
d4d95cdd4f4e698d675c make_data.py 5da1e633bb280859bed8614d2e05e64d1c0ffeb58a91f13110578f637c5f1670
e60c84d0cda3cc465df7 forager_loads.csv 3a003498f77fa0b8aaccf1eca29bbbd40453b629ef05da25841205c94e4f594d
e60c84d0cda3cc465df7 DATA_DESCRIPTION.md 9435acdd599225b05836d535c2cea1517dbf4625417c65e03aff122aa175d9c9
e60c84d0cda3cc465df7 make_data.py 8f277e4cd2f4849842182828cdc456b908069e0f7f9328e3e032852f816598c1
e8f97fe750189052f726 wing_size.csv 7e7a2424071a7889758f4c3a051e8b02112c143b47a334f113a04a93a7bbc1df
e8f97fe750189052f726 DATA_DESCRIPTION.md 42dca65287c2f99f12a18f0ce6d2151f2874c3ba4ecb1e7426c10ad92c791192
e8f97fe750189052f726 make_data.py fe1385d251e6d4dea3d4b5aecf7ea3ec577d66c0270a24d86aecd1be5a38598f

## step6_contracts

Frozen before any analysis, script, or report bytes exist. Command per case (run from the
envelope directory, repo root `/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext`):

```
PYTHONPATH=<repo>/src <repo>/.venv/bin/python -m sc_referee.cli method-contract cases/<id>/project \
  --task PROTOCOL.md --profile cases/<id>/profile_1_1_0.json \
  --actor-id "custodian:Fable-delegate (executive authority, Alex 2026-08-21)" \
  -o cases/<id>/method-contract
```

All eight exited 0 with resolution status `resolved`, 0 Claims, 0 publication surfaces,
project execution disabled. Profile: `scientific_check_requirement_v1` 1.1.0, check
`check:authorized-independent-unit-entry-into-row-independent-procedure`, candidate
`one-analyzed-row-per-authorized-independent-unit`.
Lock digest = sha256 of `cases/<id>/method-contract/semantic.lock.json`.
Each lock's `authority_binding_snapshot.material_input_content_digest` was verified equal to the
step5 CSV digest for the named raw file; all nine CSVs re-digested after the runs and unchanged.

| Case | Unit column | Group column | CSV path | Lock output path | Lock digest (sha256) | UTC |
| --- | --- | --- | --- | --- | --- | --- |
| 15b07ef7670800ba88e0 | litter_id | diet_group | cases/15b07ef7670800ba88e0/project/pup_masses.csv | cases/15b07ef7670800ba88e0/method-contract/semantic.lock.json | ee5543d36e5fbce3b7f2f085f5a8509907973650689a2cd7b470b8bed3a6c7e8 | 2026-08-22T07:41:50Z |
| 2df3396d80adbb63dffb | cow_tag | ration | cases/2df3396d80adbb63dffb/project/milk_yield.csv | cases/2df3396d80adbb63dffb/method-contract/semantic.lock.json | 41e833f07071672e0802e806a4272280f3395ca92fd4fb3c9fda9418214287c6 | 2026-08-22T07:41:50Z |
| 5ef43dbf631adcf3daec | plant_id | treatment | cases/5ef43dbf631adcf3daec/project/greenhouse_tomato_yield.csv | cases/5ef43dbf631adcf3daec/method-contract/semantic.lock.json | a9d655db528cf9a0a7ba3e4a128671daecc854fd12a241c1bbeddd20afd3ff1c | 2026-08-22T07:41:50Z |
| 6090fc1b1b6dbfcd6eee | reach_id | restoration_group | cases/6090fc1b1b6dbfcd6eee/project/kicknet_samples_raw.csv | cases/6090fc1b1b6dbfcd6eee/method-contract/semantic.lock.json | 4651be9584108595433467418394e1ff65cbd318ef1818118ae57656ea8855dc | 2026-08-22T07:41:50Z |
| ca18f96d45dff1b921ad | stand_code | treatment | cases/ca18f96d45dff1b921ad/project/tagged_tree_increment.csv | cases/ca18f96d45dff1b921ad/method-contract/semantic.lock.json | 37d0fabc2484b7c28a3b443d4e9d3908b75e1cb0bb7ed5736654206a83e57390 | 2026-08-22T07:41:50Z |
| d4d95cdd4f4e698d675c | donor_id | genotype | cases/d4d95cdd4f4e698d675c/project/organoid_teer.csv | cases/d4d95cdd4f4e698d675c/method-contract/semantic.lock.json | 8def6448f043ef4dadae3565bb823c2254b071758c9c04afd7a0b674a4de76df | 2026-08-22T07:41:50Z |
| e60c84d0cda3cc465df7 | colony_id | exposure_group | cases/e60c84d0cda3cc465df7/project/forager_loads.csv | cases/e60c84d0cda3cc465df7/method-contract/semantic.lock.json | 2f4fbcf47cb007f37cb97bb972fca1c988f3d581ead4f9d53f66ab15a762bc7b | 2026-08-22T07:41:50Z |
| e8f97fe750189052f726 | vial_id | diet | cases/e8f97fe750189052f726/project/wing_size.csv | cases/e8f97fe750189052f726/method-contract/semantic.lock.json | 8e0438c6934062a3dc348008676a1a9ce0824f1470d9a57364a318a02201e4d4 | 2026-08-22T07:41:50Z |

step6_contracts_frozen_utc: 2026-08-22T07:41:50Z

step6_note_raw_input: case 6090fc1b1b6dbfcd6eee ships two CSVs. The authority names the raw
per-row file `kicknet_samples_raw.csv` (240 rows, 12 per reach), not `reach_summary.csv`,
because the contract describes the experiment's structure rather than an analyst's file choice.

step6_note_one_row_per_unit: case 5ef43dbf631adcf3daec has exactly one row per plant.
`plant_id` is named as the unit column anyway, per the custody instruction.

step6_note_actor: actor_id on all eight locks is
`custodian:Fable-delegate (executive authority, Alex 2026-08-21)`. Unit and group columns were
chosen by the custodian delegate from `DATA_DESCRIPTION.md` alone; `PROMPT.txt` and
`ROLE_MAP.json` were not read. Alex to ratify post-scoring. Disclosed deviation from design 10.1
wording, as in envelope 1 step5.
step7_analysis_authors_released_utc: 2026-08-22T07:42:35Z (authors told: /usr/local/bin/python3 only, install nothing)

step7_projects_frozen_utc: 2026-08-22T07:50:18Z
15b07ef7670800ba88e0 analysis.py faa8f42e4f4b48e5f631eeaa1a72334240567fd51cf5baada296125f95a1b531
15b07ef7670800ba88e0 report.md ec55fc33a1ae1cd26faef6d5e5bb71e90722b4279ec7c1d669086264f5745f70
15b07ef7670800ba88e0 pup_masses.csv 8b08dcafee8a67da1ddc5e890faa1a3929942f9f5d17950222ff97b6dbeaf252
2df3396d80adbb63dffb analysis.py c847d0011aa0048076093ff70436b399dc4df429d43a2d51034b7879426d664d
2df3396d80adbb63dffb report.md a28082dfe3a4e932fa9692bc85003ff69bd9083174103fa1fe13c4634c5e0324
2df3396d80adbb63dffb milk_yield.csv ef72d990ccea7884a8b8a33527268610cf90dcb31a6b88c5f4dbea5f0b82f653
5ef43dbf631adcf3daec analysis.py d7ebed71cda71d807a19d202fa2e3b8fb96c5e07b523e89fe4d7a3aa42f117ae
5ef43dbf631adcf3daec report.md 5f756b5dc19193a71d7d470b30cffccfdfbb1854e66dabd8fb192083cd6cda80
5ef43dbf631adcf3daec greenhouse_tomato_yield.csv 5df2ea8930736d0c32e80b5a67d070729b6c31230e476b08985306f46113c2bc
6090fc1b1b6dbfcd6eee analysis.py 173ba770803d6eb8a22952c980a87bc089ddea514e28838bb383b32bb430831e
6090fc1b1b6dbfcd6eee report.md a13393026f8f9a489f6b1c494c66063c65d5c329c979626632b6ce106e58416c
6090fc1b1b6dbfcd6eee kicknet_samples_raw.csv a579220fe367191caeb08844d3800c3c1abb9751637b7bc0d5ea5266779c94dc
6090fc1b1b6dbfcd6eee reach_summary.csv 9983b6d441f40324f1985571eabab3484ce5a85c6f9a55b01b8ffe48bfe42997
ca18f96d45dff1b921ad analysis.py 146395acd2ec9696439c70a841c5a6a9d177480d73b710a5c5e0365efdc3ced2
ca18f96d45dff1b921ad report.md d605ad82d469a0617c738e89a31ba4c1c995e53a245786da603b9035c4ab3b12
ca18f96d45dff1b921ad tagged_tree_increment.csv 6458307ed0201ca73bef470b35458abce1e3c015cb14ec326d3c5fab9c6ad6c0
d4d95cdd4f4e698d675c analysis.py 857083f9cee5aeb76886c6bf0d1363506f2ef0ca2baa2f834318431a786a9552
d4d95cdd4f4e698d675c report.md 96ed857c45dc67ecce50312a75807f235f2729f24ed078d725456c4b18f59d4f
d4d95cdd4f4e698d675c organoid_teer.csv 71d094db7c3941b14bbf6bde839335d1fdc830cd6d23a8dc0f04897701ef0d4b
e60c84d0cda3cc465df7 analysis.py e28401c11067f22d99642c7ca8751bc13be6bd24cefdc791e5f59c50c886ad4b
e60c84d0cda3cc465df7 report.md 7098079f4361f152a095d8ebf9f04de42288ffbbb95274666779cba1039f4c02
e60c84d0cda3cc465df7 forager_loads.csv 3a003498f77fa0b8aaccf1eca29bbbd40453b629ef05da25841205c94e4f594d
e8f97fe750189052f726 analysis.py 6a8e5aa92a6fcfb2cdbdcd9d60903239a33e4fb1dd0f2e360c1a1e4b4916c6bc
e8f97fe750189052f726 report.md 2cdcc680f46ae02f54297995863b6e88b8dc329a40d6a998ff547e71ba3857f5
e8f97fe750189052f726 wing_size.csv 7e7a2424071a7889758f4c3a051e8b02112c143b47a334f113a04a93a7bbc1df

step9_scored_utc: 2026-08-22T07:56:52Z
RESULT: positives recognized 0/3 (e8f97f, 2df339: interprocedural-call-unresolved; ca18f9: analysis-scope-ambiguous); negatives convicted 0/5; Findings 0; replay 8/8; closure 64/64 verified; blind labels matched ROLE_MAP 8/8. ENVELOPE 2 BURNED against the 3/3 bar. Runner note: its summary line "all eight: pup_masses.csv" was a reporting slip; each run used its own lock-bound CSV (verified by custodian).
