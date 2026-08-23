# Custody log (Fable, custodian)
step4_data_frozen_utc: 2026-08-22T01:24:52Z
0f721a41bac71a461dd2 nestling_mass.csv b1700ac8ce6b905d2620e95899cb014c3ed318c98ac52716a8ff97dd9e2ba1f9
0f721a41bac71a461dd2 DATA_DESCRIPTION.md cf4721bc124a3926e64112a9f195e6f720e1d7029419336caea5fe24f31c7bb5
0f721a41bac71a461dd2 make_data.py b94793da5849e5e9567e25a70217807a791345be6397cdb10c88af90c7632895
11af5bb3f9b7e8e0b293 nubbin_calcification.csv ca637c8ad9d76c85a6518925d0239d2179eea4c1d6fca721488d8541415b7be7
11af5bb3f9b7e8e0b293 DATA_DESCRIPTION.md 1e42269f786edd8cc3aebea908c6a9e929e5cdbbd2109675f2aace80cb4fdf3e
11af5bb3f9b7e8e0b293 make_data.py fe0ce69966cf6252c6c6fe8e4e79865c3febc31a0d236951f3d96d22d2287861
45dcad2f6496a0fd5778 zebrafish_activity.csv e4047494cdab9e5529123ee5af550caa2c32c8e39859a4bfb646bed9d4bf2b2c
45dcad2f6496a0fd5778 DATA_DESCRIPTION.md 2c194af2b9c768ef007b9e435dfa300e29fdcc4042bd1ad2700a2bee49f13d7b
45dcad2f6496a0fd5778 make_data.py 9b91e232e4856d8ac87c942c24134ce27706022472a6d9fe5b0d4e4e35f49579
5994e65153b07855b07c harvest_titer.csv 32bc5e867b39b7a685dc6dc9fd30d9f3aae213a27a66fbbddff661450caff1ac
5994e65153b07855b07c DATA_DESCRIPTION.md c9279acd652ad568bb1b3d0e570296743a960e838749c391936e3be084b1c2d2
5994e65153b07855b07c make_data.py e7db0efef0e962f5f04a67554d9992923f583e0c5f3568f7a060a9acdd6f1f05
88e59abe85a8eea2b8cd soil_respiration.csv d51a55016a0de42f1072b4d1dc21c463959c6ee5c807615bf7e6912d4d177981
88e59abe85a8eea2b8cd DATA_DESCRIPTION.md c0734399121030f657a0576ce19e32fe9b7cb3392c3a86e153599c3f43b740a5
88e59abe85a8eea2b8cd make_data.py 6a0e84a4b78fdd8c427fe5509ef654135266ccac49f192fa85422519f0633f23
e804a86a1e05b781f292 microcolony_growth.csv 7a731f1cb41cd2aec79b8ae34b1100b253deedf997d208bcc3edc103f0adb2be
e804a86a1e05b781f292 DATA_DESCRIPTION.md e7ed88d49da5a2b4a26f5b0148618f384357fa491f2c5f41294f9f6cd8d8b0f9
e804a86a1e05b781f292 make_data.py 0b3c9f0ad1cb928724c8a55d0f421da4864680f9d88fdef23c78ce34c76065b3

## step5_contracts

Frozen before any analysis or report bytes exist. Command per case (run from the envelope directory,
repo root `/Users/alexanderking/Desktop/random_stuff/sc-referee-vnext`):

```
PYTHONPATH=src .venv/bin/python -m sc_referee.cli method-contract cases/<id>/project \
  --task PROTOCOL.md --profile cases/<id>/profile_1_1_0.json \
  --actor-id "custodian:Fable-delegate" -o cases/<id>/method-contract
```

All six exited 0 with resolution status `resolved`, 0 Claims, 0 publication surfaces.
Profile: `scientific_check_requirement_v1` 1.1.0, check
`check:authorized-independent-unit-entry-into-row-independent-procedure` (resolved check version
1.2.0), candidate `one-analyzed-row-per-authorized-independent-unit`.
Lock digest = sha256 of `cases/<id>/method-contract/semantic.lock.json`.
Each lock's `authority_binding_snapshot.material_input_content_digest` equals the step4 CSV digest;
no CSV was modified.

| Case | Unit column | Group column | CSV path | Lock output path | Lock digest (sha256) | UTC |
| --- | --- | --- | --- | --- | --- | --- |
| 0f721a41bac71a461dd2 | nest_tag | food_treatment | cases/0f721a41bac71a461dd2/project/nestling_mass.csv | cases/0f721a41bac71a461dd2/method-contract/semantic.lock.json | 9219c5fa39b815a15f125c0c2ab7dbf39efd4bd071567b177fb4101a4fbf6fd7 | 2026-08-22T01:28:02Z |
| 11af5bb3f9b7e8e0b293 | parent_colony | thermal_regime | cases/11af5bb3f9b7e8e0b293/project/nubbin_calcification.csv | cases/11af5bb3f9b7e8e0b293/method-contract/semantic.lock.json | 70e8ebc8ad1ad7e1a7eb562b2ca3ae2f0eca42c37aa7d2f58a066e9fde449301 | 2026-08-22T01:28:02Z |
| 45dcad2f6496a0fd5778 | aquarium_ref | exposure | cases/45dcad2f6496a0fd5778/project/zebrafish_activity.csv | cases/45dcad2f6496a0fd5778/method-contract/semantic.lock.json | bcfe4701b2c78347867fb9fa28ec47ba360fbf958642b8026b15dd7438886c0d | 2026-08-22T01:28:02Z |
| 5994e65153b07855b07c | fermenter_run | feed_strategy | cases/5994e65153b07855b07c/project/harvest_titer.csv | cases/5994e65153b07855b07c/method-contract/semantic.lock.json | 0854cc6c4a16cd821f57c2ebccc6dc99d612aab100b620963318a7f87886737d | 2026-08-22T01:28:02Z |
| 88e59abe85a8eea2b8cd | plot_code | warming_status | cases/88e59abe85a8eea2b8cd/project/soil_respiration.csv | cases/88e59abe85a8eea2b8cd/method-contract/semantic.lock.json | 1f4f4477bec627c3cc30ab0ec162571ab755fd9f9055d8d6c31435264997dde7 | 2026-08-22T01:28:02Z |
| e804a86a1e05b781f292 | hive_label | pollen_diet | cases/e804a86a1e05b781f292/project/microcolony_growth.csv | cases/e804a86a1e05b781f292/method-contract/semantic.lock.json | a16349dc3cb19d115c4f1422dc8b2e0afbdc54e736c68905fc255184ebee842e | 2026-08-22T01:28:02Z |

step5_contracts_frozen_utc: 2026-08-22T01:28:02Z

step5_note: actor_id on all six locks is custodian:Fable-delegate (Alex delegated authority in chat 2026-08-21; unit/group columns chosen by custodian delegate from DATA_DESCRIPTION.md only; Alex to ratify post-scoring). Disclosed deviation from design 10.1 wording.
step6_analysis_authors_released_utc: 2026-08-22T01:28:36Z
step6_deviation: analysis author for 88e59a installed pandas 3.0.5 + scipy 1.17.1 into repo .venv via uv (venv previously lacked both); author for 45dcad used /usr/local/bin/python3 instead. Closure digests to be re-verified before audit runs.

step6_projects_frozen_utc: 2026-08-22T01:32:33Z
0f721a41bac71a461dd2 analysis.py 368958cea973aa2b51e7ca2acb0dc5d85cf9a9c921e5776c37c0f5e4852dd26a
0f721a41bac71a461dd2 report.md c1859597911f2d7e0bf31553aa06f14b5c81fe1de633483ffa7de32693525bb3
0f721a41bac71a461dd2 nestling_mass.csv b1700ac8ce6b905d2620e95899cb014c3ed318c98ac52716a8ff97dd9e2ba1f9
11af5bb3f9b7e8e0b293 analysis.py 77eff44ce1b4afe685f3c845f6195fba4e8cc04fef1c54ec10e9445551b67b84
11af5bb3f9b7e8e0b293 report.md e832accdfeb34d0cc5badec1a22701d8f7c85ec57a80ac346bbd861bf8aae8e1
11af5bb3f9b7e8e0b293 nubbin_calcification.csv ca637c8ad9d76c85a6518925d0239d2179eea4c1d6fca721488d8541415b7be7
45dcad2f6496a0fd5778 analysis.py 324497f1b415712d4fba0477fdb84f7ea94d1f4dba5e2c3f3eceb992341ef2c9
45dcad2f6496a0fd5778 report.md 817901c232a7a3e4e53ef7f311b3a80bbc6fa85018a4bc9ac640c64f1df3fcec
45dcad2f6496a0fd5778 zebrafish_activity.csv e4047494cdab9e5529123ee5af550caa2c32c8e39859a4bfb646bed9d4bf2b2c
5994e65153b07855b07c analysis.py a3421a7e10cb57fe723056ce82c690ef6d93e8b2e35ae6a0dac6dc61205ccb18
5994e65153b07855b07c report.md 2819840ac27a831868a9192f228ae73cfc043b7b6ee86d7691eeed576779edb7
5994e65153b07855b07c harvest_titer.csv 32bc5e867b39b7a685dc6dc9fd30d9f3aae213a27a66fbbddff661450caff1ac
88e59abe85a8eea2b8cd analysis.py f0a6a3fee2a30c467b73232245a2b88962641548a9de1b3f2df1fff8e6fc613a
88e59abe85a8eea2b8cd report.md 56eeaf954c930c199cc5c9751febc41c33a16a2f6c452263152c6d5c121f6d38
88e59abe85a8eea2b8cd soil_respiration.csv d51a55016a0de42f1072b4d1dc21c463959c6ee5c807615bf7e6912d4d177981
e804a86a1e05b781f292 analysis.py 6f3ad4d50db531cf020c4cb40a228a74ada3697dae79e0a4d988164dbc3cb94c
e804a86a1e05b781f292 report.md 75b089c7005e99c45ca78b94d28dc44552356cb6b8d2b74ef19e38ba27c8e874
e804a86a1e05b781f292 microcolony_growth.csv 7a731f1cb41cd2aec79b8ae34b1100b253deedf997d208bcc3edc103f0adb2be

step8_scored_utc: 2026-08-22T01:44:51Z
RESULT: positives recognized 0/3 (45dcad, 88e59a: suppressor-present; 0f721a: admission-unavailable); negatives convicted 0/3; Findings 0; replay identical 6/6; closure verified 31/31. Blind reviewer labels agreed with ROLE_MAP 6/6. ENVELOPE BURNED against the 3/3 bar per design 10.1. No case bytes may be edited or reused as positives in a future envelope.
